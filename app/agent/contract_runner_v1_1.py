"""Contract v1.1 execution runner using existing tools through typed gates.

The runner is intentionally deterministic. It never asks an LLM to create a
confidence score, invent evidence, calculate margin, or alter an immutable
Decision Brief.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from app.agent.contract_v1_1 import (
    ClarificationResponse,
    DecisionBrief,
    DecisionBriefStatus,
    EvidenceConfidence,
    EvidenceRecord,
    EvidenceStatus,
    ExecutionPlan,
    LayerEvent,
    TradeIntake,
    TradeIntent,
    create_clarification,
    create_execution_plan,
)
from app.agent.engine import _find_hs_code, _trade_engine
from app.agent.tools import discover_opportunities
from app.landed_cost import calculate_landed_cost


EventCallback = Callable[[LayerEvent], Awaitable[None] | None]
CONFIDENCE_RULESET_VERSION = "evidence-rules-1"


async def _emit(callback: Optional[EventCallback], event: LayerEvent) -> None:
    if callback is None:
        return
    result = callback(event)
    if inspect.isawaitable(result):
        await result


def derive_confidence(*, evidence_class: str, source_ref: str, status: EvidenceStatus) -> EvidenceConfidence:
    """Deterministic and testable source → validation → confidence mapping."""

    if status == EvidenceStatus.CONFLICTING:
        return EvidenceConfidence.CONFLICTING
    if status == EvidenceStatus.UNAVAILABLE or not source_ref:
        return EvidenceConfidence.UNAVAILABLE
    if status == EvidenceStatus.PARTIAL:
        return EvidenceConfidence.LOW
    if evidence_class in {"official_tariff", "agreement", "deterministic_calculation"}:
        return EvidenceConfidence.HIGH
    if evidence_class in {"market", "logistics", "user_document"}:
        return EvidenceConfidence.MEDIUM
    return EvidenceConfidence.LOW


def _safe_event(
    task_id: str,
    sequence: int,
    event_type: str,
    state: str,
    message: str,
    layer_id: Optional[str] = None,
    evidence_ids: tuple[str, ...] = (),
    detail: Optional[dict[str, str]] = None,
) -> LayerEvent:
    return LayerEvent(
        task_id=task_id,
        sequence=sequence,
        event_type=event_type,  # type: ignore[arg-type]
        state=state,  # type: ignore[arg-type]
        message=message,
        layer_id=layer_id,
        evidence_ids=evidence_ids,
        detail=detail or {},
    )


def _unknown(field: str, reason: str) -> dict[str, str]:
    return {"field": field, "status": "UNKNOWN", "reason": reason}


def _source_evidence(
    *,
    task_id: str,
    evidence_class: str,
    issuer: str,
    source_ref: str,
    claim: str,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
) -> EvidenceRecord:
    confidence = derive_confidence(evidence_class=evidence_class, source_ref=source_ref, status=status)
    return EvidenceRecord(
        research_task_id=task_id,
        evidence_class=evidence_class,  # type: ignore[arg-type]
        issuer=issuer,
        source_ref=source_ref,
        claim=claim,
        confidence=confidence,
        confidence_ruleset_version=CONFIDENCE_RULESET_VERSION,
        status=status,
    )


def _summary_from_brief(brief: DecisionBrief) -> str:
    known = len(brief.known_values)
    unknown = len(brief.unknowns)
    if brief.status == DecisionBriefStatus.COMPLETE:
        return f"Trade brief prepared from {known} validated inputs."
    return f"Partial trade brief prepared from {known} validated inputs; {unknown} item(s) still require verification."


async def run_contract_v1_1(
    intake: TradeIntake,
    research_task_id: str,
    *,
    event_callback: Optional[EventCallback] = None,
    has_image: bool = False,
) -> dict[str, Any]:
    """Run selected backend work only after Contract v1.1 input validation."""

    clarification: Optional[ClarificationResponse] = create_clarification(intake)
    if clarification is not None:
        return {
            "kind": "clarification",
            "status": "needs_input",
            "intent": intake.intent.value,
            "clarification": clarification.model_dump(mode="json"),
            "contract_version": "1.1",
        }

    plan: ExecutionPlan = create_execution_plan(intake, research_task_id, has_image=has_image)
    sequence = 1
    await _emit(
        event_callback,
        _safe_event(research_task_id, sequence, "plan.created", "queued", "Preparing the required trade checks", evidence_ids=()),
    )
    sequence += 1
    for layer in plan.layers:
        await _emit(
            event_callback,
            _safe_event(research_task_id, sequence, "stage.updated", "queued", layer.label, layer.layer_id),
        )
        sequence += 1

    fields = intake.fields
    product = str(fields.get("product").value)
    origin = str(fields.get("origin").value)
    destination = str(fields.get("destination").value)
    evidence: list[EvidenceRecord] = []
    known_values: list[dict[str, Any]] = []
    unknowns: list[dict[str, str]] = []
    assumptions: list[dict[str, str]] = []
    risks: list[dict[str, str]] = []
    candidate_hs: Optional[dict[str, Any]] = None
    market: dict[str, Any] = {}
    logistics: dict[str, Any] = {}
    trade: dict[str, Any] = {}
    landed_cost: dict[str, Any] = {}

    async def run_layer(layer_id: str, label: str) -> None:
        nonlocal sequence
        await _emit(event_callback, _safe_event(research_task_id, sequence, "stage.updated", "running", label, layer_id))
        sequence += 1

    async def complete_layer(layer_id: str, message: str, evidence_ids: tuple[str, ...] = ()) -> None:
        nonlocal sequence
        await _emit(event_callback, _safe_event(research_task_id, sequence, "stage.updated", "complete", message, layer_id, evidence_ids))
        sequence += 1

    for layer in plan.layers:
        if layer.layer_id == "research":
            await run_layer("research", "Searching trade data")
            discovered = await discover_opportunities(max_results=5)
            opportunities = discovered.data.get("opportunities", []) if discovered.success and isinstance(discovered.data, dict) else []
            if opportunities:
                source = _source_evidence(
                    task_id=research_task_id,
                    evidence_class="market",
                    issuer="Tradix market signal database",
                    source_ref="supabase:opportunity_signals",
                    claim="Opportunity signals used to narrow the discovery scan",
                    status=EvidenceStatus.PARTIAL,
                )
                evidence.append(source)
                known_values.append({"field": "opportunity_signals", "value": opportunities, "evidence_id": source.evidence_id})
                await _emit(
                    event_callback,
                    _safe_event(
                        research_task_id,
                        sequence,
                        "source.discovered",
                        "running",
                        "Found connected market signals",
                        "research",
                        (source.evidence_id,),
                        {"issuer": source.issuer, "source_ref": source.source_ref, "claim": source.claim},
                    ),
                )
                sequence += 1
                await complete_layer("research", "Market signal search completed", (source.evidence_id,))
            else:
                unknowns.append(_unknown("opportunity_signals", "insufficient_evidence"))
                await complete_layer("research", "No verified opportunity signal was returned")

        elif layer.layer_id == "classify":
            await run_layer("classify", "Checking candidate HS classification")
            hs_code = await _find_hs_code(product)
            if hs_code:
                candidate_hs = {
                    "status": "candidate",
                    "hs_code": hs_code,
                    "reason": "Deterministic taxonomy/keyword lookup; customs validation is still required.",
                }
                known_values.append({"field": "candidate_hs", "value": hs_code, "status": "candidate"})
                await complete_layer("classify", "Candidate HS classification prepared")
            else:
                unknowns.append(_unknown("candidate_hs", "insufficient_evidence"))
                await complete_layer("classify", "No candidate HS classification was returned")

        elif layer.layer_id == "requirements":
            await run_layer("requirements", "Checking import requirements")
            if not candidate_hs:
                unknowns.append(_unknown("import_requirements", "candidate_hs_unavailable"))
                await complete_layer("requirements", "Requirements check blocked until a candidate HS is available")
                continue
            if destination != "UZ":
                unknowns.append(_unknown("customs_inputs", "destination_not_supported_by_connected_customs_service"))
                risks.append({"kind": "coverage", "detail": f"Connected customs validation is currently limited to Uzbekistan; {destination} was not queried."})
                await complete_layer("requirements", "Connected customs coverage is unavailable for this destination")
                continue
            trade = await _trade_engine(product, origin)
            if trade.get("duty_pct") is not None or trade.get("vat_pct") is not None:
                source = _source_evidence(
                    task_id=research_task_id,
                    evidence_class="official_tariff",
                    issuer="Tradix customs rule database",
                    source_ref="supabase:get_trade_costs",
                    claim=f"Customs inputs for candidate HS {candidate_hs['hs_code']} into {destination}",
                    status=EvidenceStatus.PARTIAL,
                )
                evidence.append(source)
                known_values.append(
                    {
                        "field": "customs_inputs",
                        "value": {"duty_pct": trade.get("duty_pct"), "vat_pct": trade.get("vat_pct")},
                        "evidence_id": source.evidence_id,
                        "status": "conditional_on_hs_validation",
                    }
                )
                await _emit(
                    event_callback,
                    _safe_event(
                        research_task_id,
                        sequence,
                        "source.discovered",
                        "running",
                        "Checked connected customs rules",
                        "requirements",
                        (source.evidence_id,),
                        {"issuer": source.issuer, "source_ref": source.source_ref, "claim": source.claim},
                    ),
                )
                sequence += 1
                await complete_layer("requirements", "Import requirements check completed", (source.evidence_id,))
            else:
                unknowns.append(_unknown("customs_inputs", "insufficient_evidence"))
                await complete_layer("requirements", "No verified customs input was returned")

        elif layer.layer_id == "calculate":
            await run_layer("calculate", "Calculating landed cost")
            declared_value = float(fields["declared_value"].value)
            quantity = float(fields["quantity"].value)
            duty_pct = trade.get("duty_pct")
            vat_pct = trade.get("vat_pct")
            freight_pct = trade.get("freight_pct")
            if duty_pct is None or vat_pct is None or freight_pct is None:
                unknowns.append(_unknown("landed_cost", "insufficient_evidence"))
                await complete_layer("calculate", "Landed-cost calculation blocked by missing customs or freight evidence")
                continue
            computed = calculate_landed_cost(
                price_usd=declared_value,
                duty_pct=float(duty_pct),
                vat_pct=float(vat_pct),
                freight_pct=float(freight_pct),
            )
            source = _source_evidence(
                task_id=research_task_id,
                evidence_class="deterministic_calculation",
                issuer="Tradix landed-cost calculation service",
                source_ref="function:calculate_landed_cost",
                claim="Illustrative landed-cost calculation from confirmed declared value and connected customs inputs",
            )
            evidence.append(source)
            landed_cost = {
                "status": "illustrative",
                "currency": fields["currency"].value,
                "valuation_basis": fields["valuation_basis"].value,
                "shipment_total": round(computed.total_landed, 2),
                "per_unit": round(computed.total_landed / quantity, 4) if quantity else None,
                "duty_amount": round(computed.duty_amount, 2),
                "vat_amount": round(computed.vat_amount, 2),
                "freight_amount": round(computed.freight_amount, 2),
            }
            known_values.append({"field": "landed_cost", "value": landed_cost, "evidence_id": source.evidence_id})
            await complete_layer("calculate", "Illustrative landed cost calculated", (source.evidence_id,))

        elif layer.layer_id == "verify":
            await run_layer("verify", "Checking evidence")
            if not evidence:
                unknowns.append(_unknown("evidence", "insufficient_evidence"))
            if candidate_hs and not any(item.get("field") == "customs_inputs" for item in known_values):
                risks.append({"kind": "classification", "detail": "Candidate HS is not validated by a customs requirements result."})
            if candidate_hs:
                assumptions.append({"field": "hs_classification", "detail": "Candidate HS remains subject to product composition and use confirmation."})
            await complete_layer("verify", "Evidence validation completed", tuple(item.evidence_id for item in evidence))

        elif layer.layer_id == "brief":
            await run_layer("brief", "Building trade brief")
            brief_status = DecisionBriefStatus.COMPLETE if evidence and not unknowns else DecisionBriefStatus.PARTIAL
            brief = DecisionBrief(
                research_task_id=research_task_id,
                status=brief_status,
                scope={
                    "intent": intake.intent.value,
                    "product": product,
                    "origin": origin,
                    "destination": destination,
                },
                known_values=tuple(known_values),
                unknowns=tuple(unknowns),
                assumptions=tuple(assumptions),
                candidate_hs=candidate_hs,
                risks=tuple(risks),
                verify_next=(
                    "Confirm product composition and intended use before treating the candidate HS as validated.",
                    "Confirm supplier quote, Incoterm and shipment details before placing an order.",
                ),
                evidence_ids=tuple(item.evidence_id for item in evidence),
            )
            await complete_layer("brief", "Trade brief prepared", brief.evidence_ids)
            await _emit(
                event_callback,
                _safe_event(research_task_id, sequence, "task.completed", "complete", "Trade brief ready", "brief", brief.evidence_ids),
            )
            return {
                "kind": "decision_brief",
                "status": "completed",
                "intent": intake.intent.value,
                "contract_version": "1.1",
                "execution_plan": plan.model_dump(mode="json"),
                "decision_brief": brief.model_dump(mode="json"),
                "evidence": [item.model_dump(mode="json") for item in evidence],
                "answer": _summary_from_brief(brief),
                "decision": {"recommendation": _summary_from_brief(brief), "mode": "data_backed"},
                "market": market,
                "logistics": logistics,
                "trade": trade,
                "landed_cost": landed_cost,
                "analysis_mode": "deterministic",
            }

    raise RuntimeError("execution plan completed without a brief layer")
