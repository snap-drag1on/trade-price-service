from __future__ import annotations

import asyncio
import json
from typing import Any

from openai import OpenAI

from app.agent.tools import TOOL_DEFINITIONS, TOOL_MAP
from app.agent.prompts import (
    ROUTER_SYSTEM_PROMPT,
    DISCOVERY_SYSTEM_PROMPT,
    TRADE_ANALYST_SYSTEM_PROMPT,
    DECISION_SYSTEM_PROMPT,
)
from app.config import settings
from app.log import get_logger

logger = get_logger("agent.engine")

CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
GITHUB_BASE_URL = "https://models.inference.ai.azure.com"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

ROUTER_MODEL = "zai-glm-4.7"
RESEARCH_MODEL = "zai-glm-4.7"
DECISION_MODEL = "gpt-oss-120b"

API_DELAY_SECONDS = 3  # Rate limit between API calls

# ========== Tool assignments per agent ==========

ROUTER_TOOLS = []  # Router faqat text classification

DISCOVERY_TOOLS = [
    td for td in TOOL_DEFINITIONS
    if td["function"]["name"] in (
        "web_search",
        "discover_opportunities",
    )
]

TRADE_ANALYST_TOOLS = [
    td for td in TOOL_DEFINITIONS
    if td["function"]["name"] not in (
        "calculate_landed_cost",     # faqat Decision
        "discover_opportunities",    # faqat Discovery
    )
]

DECISION_TOOLS = [
    td for td in TOOL_DEFINITIONS
    if td["function"]["name"] in ("calculate_landed_cost", "get_exchange_rate")
]


def _convert_tools(tools: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "parameters": t["function"].get("parameters", {}),
            },
        }
        for t in tools
    ]


def _get_client() -> OpenAI:
    if settings.csk_key:
        return OpenAI(base_url=CEREBRAS_BASE_URL, api_key=settings.csk_key)
    if settings.nvbuild_api_key:
        return OpenAI(base_url=NVIDIA_BASE_URL, api_key=settings.nvbuild_api_key)
    api_key = settings.github_pat or ""
    return OpenAI(base_url=GITHUB_BASE_URL, api_key=api_key)


async def run_agent(user_message: str, max_tool_rounds: int = 10) -> str:
    client = _get_client()
    loop = asyncio.get_event_loop()

    # === PHASE 0: ROUTER ===
    route = await _route_intent(client, loop, user_message)
    intent = route.get("intent", "trade_check")
    pipeline = route.get("pipeline", ["trade_analyst", "decision"])
    product_target = route.get("product", "")

    logger.info("Router → intent=%s pipeline=%s product=%s", intent, pipeline, product_target)

    context = {
        "user_message": user_message,
        "intent": intent,
        "product_target": product_target,
        "discovery_results": None,
        "analyst_results": None,
    }

    # === PHASE 1: DISCOVERY ===
    if "discovery" in pipeline:
        logger.info("Starting DISCOVERY phase")
        discovery_out = await _run_discovery_phase(client, loop, user_message)
        context["discovery_results"] = discovery_out
        await asyncio.sleep(API_DELAY_SECONDS)

    # === PHASE 2: TRADE ANALYST ===
    if "trade_analyst" in pipeline:
        logger.info("Starting TRADE ANALYST phase")
        analyst_out = await _run_trade_analyst_phase(client, loop, context)
        context["analyst_results"] = analyst_out
        await asyncio.sleep(API_DELAY_SECONDS)

    # === PHASE 3: DECISION ===
    if "decision" in pipeline:
        logger.info("Starting DECISION phase")
        result = await _run_decision_phase(client, loop, context)
        return result

    # Agar faqat trade_analyst bo'lsa (simple intent)
    return context.get("analyst_results", "Hech qanday ma'lumot topilmadi.")


# ====================================================================
# ROUTER
# ====================================================================

async def _route_intent(
    client: OpenAI, loop: asyncio.AbstractEventLoop, user_message: str
) -> dict:
    messages: list[dict] = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = await loop.run_in_executor(
        None,
        lambda: client.chat.completions.create(
            model=ROUTER_MODEL,
            messages=messages,
            temperature=0.1,  # Past temperature = aniq klassifikatsiya
        ),
    )

    content = response.choices[0].message.content or ""
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "intent" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    # JSON topishga urinish
    import re
    match = re.search(r'\{.*"intent".*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Default
    return {"intent": "trade_check", "pipeline": ["trade_analyst", "decision"], "product": user_message}


# ====================================================================
# DISCOVERY
# ====================================================================

async def _run_discovery_phase(
    client: OpenAI, loop: asyncio.AbstractEventLoop, user_message: str
) -> str:
    messages: list[dict] = [
        {"role": "system", "content": DISCOVERY_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    tools = _convert_tools(DISCOVERY_TOOLS)
    tool_map = {name: fn for name, fn in TOOL_MAP.items() if name in ("web_search", "discover_opportunities")}

    for turn in range(5):
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=RESEARCH_MODEL,
                messages=messages,
                tools=tools or None,
                tool_choice="auto",
            ),
        )
        await asyncio.sleep(API_DELAY_SECONDS)
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            if msg.content:
                messages.append({"role": "assistant", "content": msg.content})
            break

        tool_calls_data = msg.tool_calls
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": tool_calls_data})

        for tc in tool_calls_data:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            fn = tool_map.get(fn_name)
            if fn is None:
                result_text = json.dumps({"success": False, "error": f"Unknown tool: {fn_name}"})
            else:
                logger.info("Discovery calling: %s(%s)", fn_name, fn_args)
                result = await fn(**fn_args)
                result_text = json.dumps(
                    {"success": result.success, "data": result.data, "error": result.error},
                    ensure_ascii=False,
                )
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    summary = []
    for m in messages:
        role = m.get("role", "")
        if role == "assistant" and m.get("content"):
            summary.append(f"[DISCOVERY_AI]: {m['content']}")
        if role == "tool":
            summary.append(f"[TOOL_RESULT]: {m['content']}")

    return "\n".join(summary)


# ====================================================================
# TRADE ANALYST
# ====================================================================

async def _run_trade_analyst_phase(
    client: OpenAI, loop: asyncio.AbstractEventLoop, context: dict
) -> str:
    user_message = context["user_message"]
    discovery_context = context.get("discovery_results")

    # Agar discovery dan natija bo'lsa, shu mahsulotlarni tekshir
    if discovery_context:
        prompt = f"""=== ASL SAVOL ===
{user_message}

=== DISCOVERY NATIJALARI ===
{discovery_context}

Yuqoridagi discovery agent topgan mahsulotlarni tekshir.
Har bir mahsulot uchun Xitoy narxi, UZB narxi, boj/VAT, yuk narxini top.
Agar discovery natijasi bo'lmasa, user bergan mahsulotni tekshir."""
    else:
        prompt = user_message

    messages: list[dict] = [
        {"role": "system", "content": TRADE_ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    tools = _convert_tools(TRADE_ANALYST_TOOLS)
    tool_map = {name: fn for name, fn in TOOL_MAP.items() if name != "calculate_landed_cost" and name != "discover_opportunities"}

    for turn in range(8):
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=RESEARCH_MODEL,
                messages=messages,
                tools=tools or None,
                tool_choice="auto",
            ),
        )
        await asyncio.sleep(API_DELAY_SECONDS)
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            if msg.content:
                messages.append({"role": "assistant", "content": msg.content})
            break

        tool_calls_data = msg.tool_calls
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": tool_calls_data})

        for tc in tool_calls_data:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            fn = tool_map.get(fn_name)
            if fn is None:
                result_text = json.dumps({"success": False, "error": f"Unknown tool: {fn_name}"})
            else:
                logger.info("Trade Analyst calling: %s(%s)", fn_name, fn_args)
                result = await fn(**fn_args)
                result_text = json.dumps(
                    {"success": result.success, "data": result.data, "error": result.error},
                    ensure_ascii=False,
                )
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })
    else:
        pass

    summary = []
    for m in messages:
        role = m.get("role", "")
        if role == "assistant" and m.get("content"):
            summary.append(f"[TRADE_ANALYST]: {m['content']}")
        if role == "tool":
            summary.append(f"[TOOL_RESULT]: {m['content']}")

    return "\n".join(summary)


# ====================================================================
# DECISION
# ====================================================================

async def _run_decision_phase(
    client: OpenAI, loop: asyncio.AbstractEventLoop, context: dict
) -> str:
    user_message = context["user_message"]
    analyst_context = context.get("analyst_results", "")
    discovery_context = context.get("discovery_results")

    extra_context = ""
    if discovery_context:
        extra_context += f"\n=== DISCOVERY NATIJALARI ===\n{discovery_context}\n\n"

    prompt = f"""=== ASL SAVOL ===
{user_message}
{extra_context}
=== TRADE ANALYST NATIJALARI ===
{analyst_context}

Yuqoridagi trade analyst natijalarini tahlil qil.
calculate_landed_cost tool'ini ishlatib har bir variantni hisobla.
Eng yaxshi variantni tanla va jadval ko'rinishida chiroyli qilib tushuntir.
Agar discovery natijalari bo'lsa, barcha mahsulotlar ichidan eng yaxshi import imkoniyatini tanla."""

    messages: list[dict] = [
        {"role": "system", "content": DECISION_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    tools = _convert_tools(DECISION_TOOLS)

    for turn in range(5):
        response = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=DECISION_MODEL,
                messages=messages,
                tools=tools or None,
                tool_choice="auto",
            ),
        )
        await asyncio.sleep(API_DELAY_SECONDS)
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            return msg.content or "Hech qanday natija topilmadi."

        tool_calls_data = msg.tool_calls
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": tool_calls_data})

        for tc in tool_calls_data:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            fn = TOOL_MAP.get(fn_name)
            if fn is None:
                result_text = json.dumps({"success": False, "error": f"Unknown tool: {fn_name}"})
            else:
                logger.info("Decision calling: %s(%s)", fn_name, fn_args)
                result = await fn(**fn_args)
                result_text = json.dumps(
                    {"success": result.success, "data": result.data, "error": result.error},
                    ensure_ascii=False,
                )
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    if messages and messages[-1].get("content"):
        return messages[-1]["content"]
    return "Kechirasiz, javob topilmadi."
