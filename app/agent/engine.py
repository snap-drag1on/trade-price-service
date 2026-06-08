from __future__ import annotations

import asyncio
import json
import re
from typing import Any, Callable, Optional

from openai import OpenAI

from app.agent.tools import TOOL_DEFINITIONS, TOOL_MAP
from app.agent.prompts import (
    ROUTER_SYSTEM_PROMPT,
    OPPORTUNITY_SYSTEM_PROMPT,
    DECISION_SYSTEM_PROMPT,
)
from app.config import settings
from app.landed_cost import calculate_landed_cost
from app.supabase_client import get_service_client, get_supabase
from app.log import get_logger

logger = get_logger("agent.engine")

CEREBRAS_BASE_URL = "https://api.cerebras.ai/v1"
GITHUB_BASE_URL = "https://models.inference.ai.azure.com"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

ROUTER_MODEL = "zai-glm-4.7"
RESEARCH_MODEL = "zai-glm-4.7"
DECISION_MODEL = "gpt-oss-120b"

API_DELAY_SECONDS = 3

PhaseCallback = Callable[[str, Any], None]


def _get_client() -> OpenAI:
    if settings.csk_key:
        return OpenAI(base_url=CEREBRAS_BASE_URL, api_key=settings.csk_key)
    if settings.nvbuild_api_key:
        return OpenAI(base_url=NVIDIA_BASE_URL, api_key=settings.nvbuild_api_key)
    api_key = settings.github_pat or ""
    return OpenAI(base_url=GITHUB_BASE_URL, api_key=api_key)


def _llm_call(client: OpenAI, loop: asyncio.AbstractEventLoop, model: str, messages: list[dict], tools: Optional[list[dict]] = None) -> Any:
    kwargs: dict = dict(model=model, messages=messages, temperature=0.1)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    return loop.run_in_executor(None, lambda: client.chat.completions.create(**kwargs))


async def run_agent(
    user_message: str,
    max_tool_rounds: int = 10,
    progress_callback: Optional[PhaseCallback] = None,
) -> dict:
    client = _get_client()
    loop = asyncio.get_event_loop()

    _emit(progress_callback, "router", {"status": "running", "progress": 0.0})

    route = await _route_intent(client, loop, user_message)
    intent = route.get("intent", "trade_check")
    pipeline = route.get("pipeline", ["parallel", "profit", "decision"])
    product_target = route.get("product", "")
    origin_country = route.get("origin_country", "CN")

    logger.info("Router → intent=%s origin=%s product=%s", intent, origin_country, product_target)

    _emit(progress_callback, "router", {"status": "completed", "progress": 1.0, "details": route})

    context: dict = {
        "user_message": user_message,
        "intent": intent,
        "product_target": product_target,
        "opportunity": None,
        "market": None,
        "logistics": None,
        "trade": None,
        "profit": None,
        "confidence": None,
    }

    for phase in pipeline:
        if phase == "opportunity":
            _emit(progress_callback, "opportunity", {"status": "running", "progress": 0.0})
            context["opportunity"] = await _run_opportunity_phase(client, loop, user_message, max_tool_rounds)
            _emit(progress_callback, "opportunity", {"status": "completed", "progress": 1.0, "details": context["opportunity"]})
            await asyncio.sleep(API_DELAY_SECONDS)

        elif phase == "parallel":
            _emit(progress_callback, "market_research", {"status": "running", "progress": 0.0})
            _emit(progress_callback, "logistics", {"status": "running", "progress": 0.0})
            _emit(progress_callback, "trade_engine", {"status": "running", "progress": 0.0})

            market_data, logistics_data, trade_data = await _run_parallel_services(product_target or user_message, origin_country)

            context["market"] = market_data
            context["logistics"] = logistics_data
            context["trade"] = trade_data

            _emit(progress_callback, "market_research", {"status": "completed" if market_data else "error", "progress": 1.0, "details": market_data})
            _emit(progress_callback, "logistics", {"status": "completed" if logistics_data else "error", "progress": 1.0, "details": logistics_data})
            _emit(progress_callback, "trade_engine", {"status": "completed" if trade_data else "error", "progress": 1.0, "details": trade_data})

        elif phase == "profit":
            _emit(progress_callback, "profit", {"status": "running", "progress": 0.0})
            profit_data = _calculate_profit(context["market"], context["logistics"], context["trade"])
            context["profit"] = profit_data

            confidence = _compute_confidence(context["market"], context["logistics"], context["trade"], profit_data)
            context["confidence"] = confidence

            _emit(progress_callback, "profit", {"status": "completed", "progress": 1.0, "details": profit_data})

        elif phase == "decision":
            _emit(progress_callback, "decision", {"status": "running", "progress": 0.0})
            result = await _run_decision_phase(client, loop, context)
            _emit(progress_callback, "decision", {"status": "completed", "progress": 1.0})
            return result

    return context


def _emit(callback: Optional[PhaseCallback], phase: str, data: dict):
    if callback:
        try:
            callback(phase, data)
        except Exception as e:
            logger.warning("Progress callback failed: %s", e)


# ====================================================================
# ROUTER (AI Agent)
# ====================================================================

async def _route_intent(client: OpenAI, loop: asyncio.AbstractEventLoop, user_message: str) -> dict:
    messages: list[dict] = [
        {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    response = await _llm_call(client, loop, ROUTER_MODEL, messages)
    content = response.choices[0].message.content or ""

    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and "intent" in parsed:
            return parsed
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*"intent".*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return {"intent": "trade_check", "pipeline": ["parallel", "profit", "decision"], "product": user_message, "origin_country": "CN"}


# ====================================================================
# OPPORTUNITY (AI Agent) — optional, only for discovery intent
# ====================================================================

async def _run_opportunity_phase(
    client: OpenAI, loop: asyncio.AbstractEventLoop, user_message: str, max_tool_rounds: int
) -> dict:
    discovery_tools = [
        td for td in TOOL_DEFINITIONS
        if td["function"]["name"] in ("web_search", "discover_opportunities")
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": t["function"]["name"],
                "description": t["function"].get("description", ""),
                "parameters": t["function"].get("parameters", {}),
            },
        }
        for t in discovery_tools
    ]
    tool_map = {name: fn for name, fn in TOOL_MAP.items() if name in ("web_search", "discover_opportunities")}

    messages: list[dict] = [
        {"role": "system", "content": OPPORTUNITY_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    for _ in range(max_tool_rounds):
        response = await _llm_call(client, loop, RESEARCH_MODEL, messages, tools)
        await asyncio.sleep(API_DELAY_SECONDS)
        choice = response.choices[0]
        msg = choice.message

        if not msg.tool_calls:
            if msg.content:
                messages.append({"role": "assistant", "content": msg.content})
            break

        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": msg.tool_calls})

        for tc in msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            fn = tool_map.get(fn_name)
            if fn is None:
                result_text = json.dumps({"success": False, "error": f"Unknown tool: {fn_name}"})
            else:
                logger.info("Opportunity calling: %s(%s)", fn_name, fn_args)
                result = await fn(**fn_args)
                result_text = json.dumps({"success": result.success, "data": result.data, "error": result.error}, ensure_ascii=False)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result_text})

    last_content = ""
    for m in reversed(messages):
        if m.get("role") == "assistant" and m.get("content"):
            last_content = m["content"]
            break

    opportunities = _extract_opportunities(last_content)
    return {"opportunities": opportunities, "raw": last_content}


def _extract_opportunities(text: str) -> list[dict]:
    try:
        match = re.search(r'\{.*"opportunities".*\}', text, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed.get("opportunities"), list):
                return parsed["opportunities"]
    except (json.JSONDecodeError, AttributeError):
        pass
    return []


# ====================================================================
# PARALLEL SERVICES (Market + Logistics + Trade Engine)
# No AI — pure data retrieval
# ====================================================================

async def _run_parallel_services(product: str, origin: str = "CN") -> tuple[dict, dict, dict]:
    market_task = _market_service(product, origin)
    logistics_task = _logistics_service(product, origin)
    trade_task = _trade_engine(product, origin)

    done, _ = await asyncio.wait(
        {market_task, logistics_task, trade_task},
        timeout=25,
    )
    results = [{} for _ in range(3)]
    task_list = [market_task, logistics_task, trade_task]
    for i, t in enumerate(task_list):
        if t in done:
            try:
                r = t.result()
                results[i] = r if not isinstance(r, Exception) else {}
            except Exception:
                results[i] = {}
    logger.info("Parallel services: market=%s logistics=%s trade=%s (%d/%d done)",
        "ok" if results[0].get("origin_price_usd") else "empty",
        "ok" if results[1] else "empty",
        "ok" if results[2] else "empty",
        len(done), len(task_list))

    market = results[0] if not isinstance(results[0], Exception) else {}
    logistics = results[1] if not isinstance(results[1], Exception) else {}
    trade = results[2] if not isinstance(results[2], Exception) else {}

    if isinstance(results[0], Exception):
        logger.warning("Market service error: %s", results[0])
    if isinstance(results[1], Exception):
        logger.warning("Logistics service error: %s", results[1])
    if isinstance(results[2], Exception):
        logger.warning("Trade engine error: %s", results[2])

    return market, logistics, trade


async def _market_service(product: str, origin: str = "CN") -> dict:
    """Find prices from origin country and Uzbekistan marketplaces."""
    result = {"product_name": product, "origin_price_usd": None, "origin_source": None, "uz_price_usd": None, "confidence": 0.0, "origin_country": origin}

    if origin == "CN":
        origin_task = _search_china_prices(product)
    else:
        origin_task = _search_country_prices(product, origin)
    uz_task = _search_uz_prices(product)

    origin_result, uz_result = await asyncio.gather(origin_task, uz_task, return_exceptions=True)

    if not isinstance(origin_result, Exception) and origin_result:
        result["origin_price_usd"] = origin_result.get("price_usd")
        result["origin_source"] = origin_result.get("source")
        result["weight_kg"] = origin_result.get("weight_kg")

    if not isinstance(uz_result, Exception) and uz_result:
        result["uz_price_usd"] = uz_result.get("price_usd")
        result["uz_price_uzs"] = uz_result.get("price_uzs")
        result["uz_source"] = uz_result.get("source")

    confidence = 0.0
    if result["origin_price_usd"] is not None:
        confidence += 0.5
    if result["uz_price_usd"] is not None:
        confidence += 0.5
    result["confidence"] = round(confidence, 2)

    return result


async def _search_china_prices(product: str) -> Optional[dict]:
    """Search Chinese wholesale sources for prices."""
    try:
        result = await TOOL_MAP["search_cn_sources"](product, max_results=5)
        if result.success and result.data:
            data = result.data
            prices = []
            for item in data:
                snippet = item.get("snippet", "") or item.get("title", "")
                price_match = re.search(r'\$?(\d+\.?\d*)', snippet)
                if price_match:
                    try:
                        prices.append(float(price_match.group(1)))
                    except ValueError:
                        pass
            avg_price = round(sum(prices) / len(prices), 2) if prices else None
            return {"price_usd": avg_price, "source": data[0].get("source", "Alibaba") if data else "Unknown", "weight_kg": None}
    except Exception as e:
        logger.debug("China price search failed: %s", e)

    try:
        result = await TOOL_MAP["web_search"](f"alibaba {product} price USD wholesale", max_results=5)
        if result.success and result.data:
            prices = []
            for item in result.data:
                body = item.get("body", "") or item.get("title", "")
                price_match = re.search(r'\$?(\d+\.?\d*)', body)
                if price_match:
                    try:
                        prices.append(float(price_match.group(1)))
                    except ValueError:
                        pass
            avg_price = round(sum(prices) / len(prices), 2) if prices else None
            return {"price_usd": avg_price, "source": "Alibaba (web)", "weight_kg": None}
    except Exception as e:
        logger.debug("China web search failed: %s", e)

    return None


async def _search_uz_prices(product: str) -> Optional[dict]:
    """Search Uzbekistan marketplaces for prices."""
    try:
        result = await TOOL_MAP["search_uz_marketplaces"](product, max_results=3)
        if result.success and result.data:
            data = result.data
            prices_uzs = []
            for item in data:
                price = item.get("price_uzs") or item.get("price_usd")
                if price and price > 0:
                    prices_uzs.append(float(price))
            if prices_uzs:
                avg_uzs = round(sum(prices_uzs) / len(prices_uzs), 2)
                return {"price_uzs": avg_uzs, "price_usd": round(avg_uzs / 12700, 2), "source": data[0].get("marketplace", "Uzum")}
    except Exception as e:
        logger.debug("UZ price search failed: %s", e)

    try:
        result = await TOOL_MAP["search_uzum"](product, max_results=3)
        if result.success and result.data:
            data = result.data
            prices_uzs = []
            for item in data:
                price = item.get("price_uzs") or item.get("price_usd")
                if price and price > 0:
                    prices_uzs.append(float(price))
            if prices_uzs:
                avg_uzs = round(sum(prices_uzs) / len(prices_uzs), 2)
                return {"price_uzs": avg_uzs, "price_usd": round(avg_uzs / 12700, 2), "source": "Uzum"}
    except Exception as e:
        logger.debug("Uzum search failed: %s", e)

    return None


async def _search_country_prices(product: str, origin: str) -> Optional[dict]:
    """Search marketplaces of a specific origin country for prices."""
    try:
        from app.agent.tools import COUNTRY_MARKETPLACES
        info = COUNTRY_MARKETPLACES.get(origin)
        if info:
            marketplaces = info.get("marketplaces", [])[:3]
            for mp in marketplaces:
                result = await TOOL_MAP["web_search"](f"site:{mp} {product}", max_results=2)
                if result.success and result.data:
                    prices = []
                    for item in result.data:
                        snippet = item.get("body", "") or item.get("title", "")
                        price_match = re.search(r'\$?(\d+\.?\d*)', snippet)
                        if price_match:
                            try:
                                prices.append(float(price_match.group(1)))
                            except ValueError:
                                pass
                    if prices:
                        avg = round(sum(prices) / len(prices), 2)
                        return {"price_usd": avg, "source": mp, "weight_kg": None}
    except Exception as e:
        logger.debug("Country price search failed for %s: %s", origin, e)

    try:
        result = await TOOL_MAP["web_search"](f"{product} price {origin} USD", max_results=5)
        if result.success and result.data:
            prices = []
            for item in result.data:
                body = item.get("body", "") or item.get("title", "")
                price_match = re.search(r'\$?(\d+\.?\d*)', body)
                if price_match:
                    try:
                        prices.append(float(price_match.group(1)))
                    except ValueError:
                        pass
            if prices:
                avg = round(sum(prices) / len(prices), 2)
                return {"price_usd": avg, "source": f"{origin} (web)", "weight_kg": None}
    except Exception as e:
        logger.debug("Country web search failed: %s", e)

    return None


async def _logistics_service(product: str, origin: str = "CN") -> dict:
    """Get freight info from DB. Uses origin→UZ corridor."""
    result = {
        "origin": origin,
        "destination": "UZ",
        "cost_per_kg_usd": None,
        "transit_days": None,
        "transport_mode": "rail",
        "confidence": 0.0,
    }

    try:
        freight = await TOOL_MAP["get_freight_corridor"](origin, "UZ", "rail")
        if freight.success and freight.data:
            result["cost_per_kg_usd"] = freight.data.get("cost_per_kg_usd")
            result["transit_days"] = freight.data.get("transit_days_min") or freight.data.get("transit_days_max")
            result["confidence"] = 0.8
            return result
    except Exception as e:
        logger.debug("Rail freight failed: %s", e)

    try:
        multi = await TOOL_MAP["get_logistics_multi_route"](origin, "UZ", weight_kg=1)
        if multi.success and multi.data:
            routes = multi.data.get("routes", [])
            if routes:
                best = routes[0]
                result["cost_per_kg_usd"] = best.get("cost_per_kg_usd") or best.get("total_cost_usd")
                result["transit_days"] = best.get("transit_days_min") or best.get("transit_days_max")
                result["transport_mode"] = best.get("transport_mode", "rail")
                result["confidence"] = 0.6
                return result
    except Exception as e:
        logger.debug("Multi-route failed: %s", e)

    result["confidence"] = 0.3
    return result


async def _trade_engine(product: str, origin: str = "CN") -> dict:
    """Get duty/VAT from DB. Try to find HS code by product name."""
    result = {"hs_code": None, "hs_description": None, "duty_pct": None, "vat_pct": None, "freight_pct": None, "confidence": 0.0, "origin_country": origin}

    hs_code = await _find_hs_code(product)

    if hs_code:
        result["hs_code"] = hs_code
        try:
            trade = await TOOL_MAP["get_trade_costs"](origin, "UZ", hs_code, "rail")
            if trade.success and trade.data:
                result["duty_pct"] = trade.data.get("duty_pct")
                result["vat_pct"] = trade.data.get("vat_pct")
                result["freight_pct"] = trade.data.get("freight_pct")
                result["confidence"] = 1.0 if (result["duty_pct"] is not None and result["vat_pct"] is not None) else 0.5
                return result
        except Exception as e:
            logger.debug("Trade costs failed: %s", e)

    result["confidence"] = 0.2
    return result


async def _find_hs_code(product: str) -> Optional[str]:
    """Try to find HS code from Supabase or via web search."""
    try:
        supabase = get_service_client() or get_supabase()
        if supabase:
            data = supabase.table("hs_codes").select("hs_code,description").ilike("description", f"%{product[:30]}%").limit(3).execute()
            if data.data and len(data.data) > 0:
                return data.data[0].get("hs_code")
    except Exception as e:
        logger.debug("HS code DB lookup failed: %s", e)

    category_map = {
        "laptop": "847130", "computer": "847130", "notebook": "847130",
        "phone": "851713", "smartphone": "851713", "iphone": "851713",
        "printer": "844332", "mini printer": "844332",
        "led": "853952", "lamp": "853952", "light": "853952",
        "power bank": "850760", "battery": "850760",
        "solar": "854143", "inverter": "850440",
        "fan": "841451", "cooler": "841451",
        "cable": "854442", "charger": "850440",
        "speaker": "851822", "headphone": "851830",
        "camera": "852589", "dash camera": "852589",
        "blanket": "630110", "towel": "630260",
        "toy": "950300", "drone": "852581",
    }

    lower = product.lower()
    for keyword, code in category_map.items():
        if keyword in lower:
            return code

    return None


# ====================================================================
# PROFIT (formula-based, no AI)
# ====================================================================

def _calculate_profit(market: Optional[dict], logistics: Optional[dict], trade: Optional[dict]) -> dict:
    market = market or {}
    logistics = logistics or {}
    trade = trade or {}

    price_usd = market.get("origin_price_usd") or market.get("china_price_usd") or 0
    uz_price_usd = market.get("uz_price_usd") or 0

    if price_usd <= 0:
        return {"price_usd": 0, "total_landed_usd": 0, "profit_usd": 0, "margin_pct": 0}

    duty_pct = trade.get("duty_pct") or 0
    vat_pct = trade.get("vat_pct") or 0
    freight_cost = logistics.get("cost_per_kg_usd") or 0
    freight_rate = trade.get("freight_pct") or 15

    weight = (market.get("weight_kg") or 1)
    total_freight = freight_cost * weight if freight_cost > 0 else (price_usd * freight_rate / 100)

    lc = calculate_landed_cost(
        price_usd=price_usd,
        duty_pct=float(duty_pct),
        vat_pct=float(vat_pct),
        freight_pct=(total_freight / price_usd * 100) if price_usd > 0 else freight_rate,
    )

    landed = lc.total_landed
    profit = uz_price_usd - landed if uz_price_usd > 0 else 0
    margin = (profit / landed * 100) if landed > 0 and profit > 0 else 0

    return {
        "price_usd": price_usd,
        "duty_amount": lc.duty_amount,
        "vat_amount": lc.vat_amount,
        "freight_amount": lc.freight_amount,
        "total_landed_usd": landed,
        "total_landed_uzs": round(landed * 12700, 2),
        "market_price_usd": uz_price_usd,
        "profit_usd": round(profit, 2),
        "margin_pct": round(margin, 1),
    }


# ====================================================================
# CONFIDENCE AGGREGATOR
# ====================================================================

def _compute_confidence(market: Optional[dict], logistics: Optional[dict], trade: Optional[dict], profit: Optional[dict]) -> dict:
    market_conf = (market or {}).get("confidence", 0)
    logistics_conf = (logistics or {}).get("confidence", 0)
    trade_conf = (trade or {}).get("confidence", 0)

    profit_data = profit or {}
    profit_conf = 1.0 if profit_data.get("total_landed_usd", 0) > 0 and profit_data.get("market_price_usd", 0) > 0 else 0.3

    scores = [market_conf, logistics_conf, trade_conf, profit_conf]
    overall = round(sum(scores) / len(scores), 2) if scores else 0.0

    return {
        "market_score": round(market_conf, 2),
        "logistics_score": round(logistics_conf, 2),
        "trade_score": round(trade_conf, 2),
        "profit_score": round(profit_conf, 2),
        "overall": overall,
    }


# ====================================================================
# DECISION (AI Agent) — final reasoning, no tools
# ====================================================================

async def _run_decision_phase(client: OpenAI, loop: asyncio.AbstractEventLoop, context: dict) -> dict:
    product_target = context.get("product_target") or context.get("user_message", "")
    market = context.get("market") or {}
    logistics = context.get("logistics") or {}
    trade = context.get("trade") or {}
    profit_data = context.get("profit") or {}
    confidence = context.get("confidence") or {}
    opp_data = context.get("opportunity") or {}
    opportunities = opp_data.get("opportunities", [])

    prompt_parts = [f"=== USER SAVOLI ===\n{context['user_message']}\n"]

    if opportunities:
        prompt_parts.append("=== TOPILGAN IMKONIYATLAR ===\n" + json.dumps(opportunities, ensure_ascii=False, indent=2) + "\n")

    NA = "ma'lum emas"
    origin_country = market.get("origin_country", "CN")
    prompt_parts.append(
        "=== MARKET MA'LUMOTLARI ===\n"
        f"Mahsulot: {market.get('product_name', product_target)}\n"
        f"Origin: {origin_country}\n"
        f"Origin narxi: ${market.get('origin_price_usd', market.get('china_price_usd', NA))}\n"
        f"O'zbekiston narxi: ${market.get('uz_price_usd', NA)}\n"
        f"Manba: {market.get('origin_source', market.get('china_source', 'noma_lum'))} / {market.get('uz_source', 'noma_lum')}\n"
        f"Ishonchlilik: {market.get('confidence', 0)}\n"
        "\n"
        "=== LOGISTIKA ===\n"
        f"Transport: {logistics.get('transport_mode', 'rail')}\n"
        f"Narxi/kg: ${logistics.get('cost_per_kg_usd', NA)}\n"
        f"Kun: {logistics.get('transit_days', NA)}\n"
        f"Ishonchlilik: {logistics.get('confidence', 0)}\n"
        "\n"
        "=== BOJ / VAT ===\n"
        f"HS kod: {trade.get('hs_code', NA)}\n"
        f"Boj: {trade.get('duty_pct', NA)}%\n"
        f"VAT: {trade.get('vat_pct', NA)}%\n"
        f"Ishonchlilik: {trade.get('confidence', 0)}\n"
        "\n"
        "=== FOYDA HISOBLARI ===\n"
        f"Landed cost (USD): ${profit_data.get('total_landed_usd', 0)}\n"
        f"Landed cost (UZS): {profit_data.get('total_landed_uzs', 0)} som\n"
        f"Bozor narxi: ${profit_data.get('market_price_usd', 0)}\n"
        f"Foyda: ${profit_data.get('profit_usd', 0)}\n"
        f"Marja: {profit_data.get('margin_pct', 0)}%\n"
        "\n"
        "=== ISHONCHLILIK METRIKALARI ===\n"
        + json.dumps(confidence, indent=2, ensure_ascii=False)
    )

    messages = [
        {"role": "system", "content": DECISION_SYSTEM_PROMPT},
        {"role": "user", "content": "\n".join(prompt_parts)},
    ]

    try:
        response = await _llm_call(client, loop, DECISION_MODEL, messages)
        if response is None or not response.choices:
            answer = "Kechirasiz, AI javob bera olmadi. Iltimos qayta urinib ko'ring."
        else:
            answer = response.choices[0].message.content or "Kechirasiz, javob topilmadi."
    except Exception as e:
        logger.error("Decision LLM call failed: %s", e)
        answer = _generate_fallback_answer(context)

    return {
        "answer": answer,
        "market": market,
        "logistics": logistics,
        "trade": trade,
        "profit": profit_data,
        "confidence": confidence,
        "opportunities": opportunities,
    }


def _generate_fallback_answer(context: dict) -> str:
    """Generate a simple text answer when LLM is unavailable."""
    market = context.get("market") or {}
    profit_data = context.get("profit") or {}
    confidence = context.get("confidence") or {}

    lines = ["📊 Tahlil natijalari:\n"]
    if profit_data.get("total_landed_usd"):
        lines.append(f"💰 Landed cost: ${profit_data['total_landed_usd']}")
        lines.append(f"   UZS: {profit_data['total_landed_uzs']:,} so'm")
    if profit_data.get("margin_pct"):
        lines.append(f"📈 Marja: {profit_data['margin_pct']}%")
    if profit_data.get("profit_usd"):
        lines.append(f"💵 Foyda: ${profit_data['profit_usd']}")
    origin_price = market.get("origin_price_usd") or market.get("china_price_usd")
    uz_price = market.get("uz_price_usd")
    origin_name = market.get("origin_country", "CN")
    if origin_price:
        lines.append(f"\n🏷️ {origin_name} narxi: ${origin_price}")
    if uz_price:
        lines.append(f"🏷️ O'zbekiston narxi: ${uz_price}")
    lines.append(f"\n📊 Ishonchlilik: {confidence.get('overall', 0)*100:.0f}%")
    lines.append("\n💡 Batafsil tahlil uchun qayta urinib ko'ring.")
    return "\n".join(lines)
