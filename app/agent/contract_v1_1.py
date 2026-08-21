"""Typed, migration-free primitives for the approved Tradix Agent Contract v1.1.

This module deliberately contains no provider calls, no database writes and no
hidden reasoning. It is the validation boundary used before a task is allowed
to execute tools or emit user-facing Activity Trace events.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Iterable, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CONTRACT_VERSION = "1.1"


class FieldState(str, Enum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


class TradeIntent(str, Enum):
    DISCOVERY = "discovery"
    ROUTE_CHECK = "route_check"
    LANDED_COST = "landed_cost"


class ResearchTaskStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    PARTIAL = "partial"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DecisionBriefStatus(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    NEEDS_INPUT = "needs_input"
    FAILED = "failed"


class EvidenceConfidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    STALE = "STALE"
    CONFLICTING = "CONFLICTING"
    UNAVAILABLE = "UNAVAILABLE"


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    CONFLICTING = "conflicting"
    UNAVAILABLE = "unavailable"


class TradeIntakeField(BaseModel):
    """One normalized user input with explicit provenance/state."""

    value: Optional[Any] = None
    state: FieldState = FieldState.UNKNOWN
    source: Literal["user", "parser", "resume"] = "user"

    @model_validator(mode="after")
    def state_matches_value(self) -> "TradeIntakeField":
        if self.state == FieldState.CONFIRMED and self.value in (None, ""):
            raise ValueError("confirmed intake fields require a value")
        if self.state == FieldState.UNKNOWN and self.value not in (None, ""):
            raise ValueError("unknown intake fields cannot carry a value")
        return self


class TradeIntake(BaseModel):
    """Immutable normalized user state; this is not a conversation transcript."""

    model_config = ConfigDict(frozen=True)

    intake_id: str = Field(default_factory=lambda: str(uuid4()))
    session_id: str
    sequence: int = Field(ge=1)
    contract_version: Literal["1.1"] = CONTRACT_VERSION
    raw_user_message: str = Field(min_length=1, max_length=10_000)
    intent: TradeIntent
    fields: dict[str, TradeIntakeField]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("raw_user_message")
    @classmethod
    def non_blank_message(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("raw_user_message cannot be blank")
        return trimmed


class ClarificationQuestion(BaseModel):
    field: str
    question: str = Field(min_length=2, max_length=400)
    reason: str = Field(min_length=2, max_length=400)


class ClarificationResponse(BaseModel):
    kind: Literal["clarification"] = "clarification"
    contract_version: Literal["1.1"] = CONTRACT_VERSION
    intake_id: str
    intent: TradeIntent
    questions: tuple[ClarificationQuestion, ...]
    missing_fields: tuple[str, ...]
    status: Literal["needs_input"] = "needs_input"

    @model_validator(mode="after")
    def dynamic_question_limit(self) -> "ClarificationResponse":
        if not 1 <= len(self.questions) <= 3:
            raise ValueError("clarification must ask between one and three questions")
        return self


class ExecutionLayer(BaseModel):
    """One backend-selected layer, never a frontend default or fake placeholder."""

    layer_id: Literal[
        "image_analysis",
        "research",
        "analyze",
        "classify",
        "requirements",
        "calculate",
        "compare",
        "verify",
        "brief",
    ]
    label: str = Field(min_length=2, max_length=120)
    depends_on: tuple[str, ...] = ()


class ExecutionPlan(BaseModel):
    """Exactly one immutable v1 plan belongs to an executable research task."""

    model_config = ConfigDict(frozen=True)

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    research_task_id: str
    intake_id: str
    contract_version: Literal["1.1"] = CONTRACT_VERSION
    layers: tuple[ExecutionLayer, ...]
    blocked_claims: tuple[str, ...] = ()
    plan_hash: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def valid_layers(self) -> "ExecutionPlan":
        ids = [layer.layer_id for layer in self.layers]
        if not ids or ids[-1] != "brief":
            raise ValueError("an execution plan must finish with the brief layer")
        if len(ids) != len(set(ids)):
            raise ValueError("execution plan layers must be unique")
        for layer in self.layers:
            unknown_dependencies = set(layer.depends_on) - set(ids)
            if unknown_dependencies:
                raise ValueError(f"unknown layer dependencies: {sorted(unknown_dependencies)}")
        return self


class LayerEvent(BaseModel):
    """Polling-friendly, safe projection of an authoritative backend event."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    task_id: str
    sequence: int = Field(ge=1)
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    event_type: Literal["plan.created", "stage.updated", "source.discovered", "task.completed"]
    layer_id: Optional[str] = None
    state: Literal["queued", "running", "complete", "failed", "cancelled"]
    message: str = Field(min_length=2, max_length=500)
    tool_run_id: Optional[str] = None
    evidence_ids: tuple[str, ...] = ()
    detail: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, int] = Field(default_factory=dict)


class EvidenceRecord(BaseModel):
    """A claim-supporting source or deterministic calculation, never model opinion."""

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    research_task_id: str
    tool_run_id: Optional[str] = None
    evidence_class: Literal[
        "official_tariff",
        "agreement",
        "market",
        "logistics",
        "user_document",
        "deterministic_calculation",
    ]
    issuer: str = Field(min_length=2, max_length=300)
    source_ref: str = Field(min_length=2, max_length=2_000)
    claim: str = Field(min_length=2, max_length=1_000)
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: EvidenceConfidence
    confidence_ruleset_version: str = Field(min_length=1, max_length=80)
    status: EvidenceStatus


class DecisionBrief(BaseModel):
    """Immutable result built only from validated values, evidence and unknowns."""

    model_config = ConfigDict(frozen=True)

    brief_id: str = Field(default_factory=lambda: str(uuid4()))
    research_task_id: str
    contract_version: Literal["1.1"] = CONTRACT_VERSION
    status: DecisionBriefStatus
    scope: dict[str, Any]
    known_values: tuple[dict[str, Any], ...] = ()
    unknowns: tuple[dict[str, str], ...] = ()
    assumptions: tuple[dict[str, str], ...] = ()
    candidate_hs: Optional[dict[str, Any]] = None
    risks: tuple[dict[str, str], ...] = ()
    verify_next: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="after")
    def unknowns_are_explicit(self) -> "DecisionBrief":
        for unknown in self.unknowns:
            if unknown.get("status") != "UNKNOWN" or not unknown.get("reason"):
                raise ValueError("every unknown must be UNKNOWN with a reason")
        if self.status == DecisionBriefStatus.COMPLETE and not self.evidence_ids:
            raise ValueError("a complete brief requires evidence references")
        return self


REQUIRED_FIELDS: dict[TradeIntent, tuple[str, ...]] = {
    TradeIntent.DISCOVERY: ("destination", "budget_or_constraints"),
    TradeIntent.ROUTE_CHECK: ("product", "origin", "destination"),
    TradeIntent.LANDED_COST: (
        "product",
        "origin",
        "destination",
        "quantity",
        "declared_value",
        "currency",
        "valuation_basis",
    ),
}

QUESTION_COPY: dict[str, tuple[str, str]] = {
    "product": ("Which product should Tradix assess?", "Product details are required to classify the item and select checks."),
    "origin": ("Which country will the goods come from?", "Origin is required for route-specific customs and sourcing checks."),
    "destination": ("Which country do you plan to sell or import into?", "Destination determines market and import requirements."),
    "budget_or_constraints": ("What budget or sourcing constraint should guide the scan?", "A discovery scan needs a commercial constraint before selecting a useful market scope."),
    "quantity": ("What quantity are you planning to import?", "Quantity is required before an indicative landed-cost calculation can be checked."),
    "declared_value": ("What supplier or declared shipment value should be used?", "A landed-cost calculation cannot be produced without a value basis."),
    "currency": ("Which currency is the stated value in?", "Currency is required to keep the calculation reproducible."),
    "valuation_basis": ("Is the stated value EXW, FOB, CIF, or another Incoterm basis?", "The valuation basis determines which cost components are already included."),
}

COUNTRY_ALIASES: dict[str, tuple[str, ...]] = {
    "UZ": ("uzbekistan", "uzbekiston", "o'zbekiston", "ozbekiston"),
    "TR": ("turkey", "turkiye", "türkiye", "turkiya"),
    "CN": ("china", "xitoy"),
    "RU": ("russia", "rossiya"),
    "KZ": ("kazakhstan", "qozog'iston", "qozogiston"),
    "AE": ("uae", "emirates", "dubai", "baa"),
    "DE": ("germany", "germaniya"),
    "US": ("usa", "united states", "america", "aqsh"),
    "JP": ("japan", "yaponiya"),
    "KR": ("south korea", "korea", "koreya"),
}


def required_fields(intent: TradeIntent) -> tuple[str, ...]:
    return REQUIRED_FIELDS[intent]


def missing_required_fields(intake: TradeIntake) -> tuple[str, ...]:
    """Only explicitly confirmed user fields unlock execution."""

    missing: list[str] = []
    for name in required_fields(intake.intent):
        field = intake.fields.get(name)
        if not field or field.state != FieldState.CONFIRMED or field.value in (None, ""):
            missing.append(name)
    return tuple(missing)


def create_clarification(intake: TradeIntake) -> Optional[ClarificationResponse]:
    missing = missing_required_fields(intake)
    if not missing:
        return None
    questions = tuple(
        ClarificationQuestion(field=name, question=QUESTION_COPY[name][0], reason=QUESTION_COPY[name][1])
        for name in missing[:3]
    )
    return ClarificationResponse(
        intake_id=intake.intake_id,
        intent=intake.intent,
        questions=questions,
        missing_fields=missing,
    )


def is_executable(intake: TradeIntake) -> bool:
    return not missing_required_fields(intake)


def normalize_legacy_message(message: str, session_id: str, sequence: int = 1) -> TradeIntake:
    """Conservative parser for the legacy one-field Composer request.

    This only promotes text that the user explicitly typed. Route defaults from
    legacy callers are intentionally ignored so destination/origin never become
    hidden facts.
    """

    normalized = message.strip()
    lower = normalized.lower()
    if any(token in lower for token in ("landed cost", "boj", "duty", "vat", "cif", "fob", "exw")):
        intent = TradeIntent.LANDED_COST
    elif any(token in lower for token in ("from ", " to ", "turkey", "turkiya", "china", "xitoy", "route")):
        intent = TradeIntent.ROUTE_CHECK
    else:
        intent = TradeIntent.DISCOVERY

    def confirmed(value: Any) -> TradeIntakeField:
        return TradeIntakeField(value=value, state=FieldState.CONFIRMED, source="user")

    def unknown() -> TradeIntakeField:
        return TradeIntakeField(value=None, state=FieldState.UNKNOWN, source="parser")

    origin: Optional[str] = None
    destination: Optional[str] = None
    for code, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            if f"from {alias}" in lower or f"{alias}dan" in lower:
                origin = code
            if f"to {alias}" in lower or f"in {alias}" in lower or f"{alias}ga" in lower:
                destination = code
    if intent == TradeIntent.DISCOVERY and destination is None:
        for code, aliases in COUNTRY_ALIASES.items():
            if any(alias in lower for alias in aliases):
                destination = code
                break

    product = normalized
    for separator in (" from ", " to ", " import ", " check ", " with ", " for "):
        index = lower.find(separator)
        if index > 0:
            product = normalized[:index].strip(" .,:;-")
            break
    if product.lower().startswith("import "):
        product = product[7:].strip()
    has_product = bool(product) and product.lower() not in {"what", "what should i", "nima", "nima olib kelsam"}

    budget_match = re.search(r"(?:budget|under|up to|below|byudjet)[^\d$]*(\$?\s*[\d][\d,\s.]*)", lower)
    quantity_match = re.search(r"(?:quantity|qty|units?|pieces?|dona)[^\d]*(\d[\d,\s.]*)", lower)
    money_matches = re.findall(r"\$\s*(\d[\d,\s.]*)", normalized)
    valuation_basis = next((basis for basis in ("EXW", "FOB", "CIF") if basis.lower() in lower), None)

    fields: dict[str, TradeIntakeField] = {
        "product": confirmed(product) if has_product else unknown(),
        "origin": confirmed(origin) if origin else unknown(),
        "destination": confirmed(destination) if destination else unknown(),
        "budget_or_constraints": confirmed(budget_match.group(0).strip()) if budget_match else unknown(),
        "quantity": confirmed(int(re.sub(r"\D", "", quantity_match.group(1)))) if quantity_match else unknown(),
        "declared_value": confirmed(float(re.sub(r"[^0-9.]", "", money_matches[-1]))) if money_matches and intent == TradeIntent.LANDED_COST else unknown(),
        "currency": confirmed("USD") if money_matches and intent == TradeIntent.LANDED_COST else unknown(),
        "valuation_basis": confirmed(valuation_basis) if valuation_basis else unknown(),
    }
    return TradeIntake(
        session_id=session_id,
        sequence=sequence,
        raw_user_message=normalized,
        intent=intent,
        fields=fields,
    )


def _plan_payload(intake: TradeIntake, task_id: str, layers: Iterable[ExecutionLayer]) -> str:
    return json.dumps(
        {
            "contract_version": CONTRACT_VERSION,
            "intake_id": intake.intake_id,
            "research_task_id": task_id,
            "layers": [layer.model_dump(mode="json") for layer in layers],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def create_execution_plan(
    intake: TradeIntake,
    research_task_id: str,
    *,
    has_image: bool = False,
    comparison_requested: bool = False,
) -> ExecutionPlan:
    """Create the smallest contract-compliant plan; raise before any tool work if blocked."""

    missing = missing_required_fields(intake)
    if missing:
        raise ValueError(f"cannot create execution plan while input is missing: {', '.join(missing)}")

    layers: list[ExecutionLayer] = []
    if has_image:
        layers.append(ExecutionLayer(layer_id="image_analysis", label="Analyzing the supplied image"))

    if intake.intent == TradeIntent.DISCOVERY:
        layers.extend(
            [
                ExecutionLayer(layer_id="research", label="Searching trade data", depends_on=tuple(layer.layer_id for layer in layers)),
                ExecutionLayer(layer_id="verify", label="Checking evidence", depends_on=("research",)),
            ]
        )
    elif intake.intent == TradeIntent.ROUTE_CHECK:
        layers.extend(
            [
                ExecutionLayer(layer_id="classify", label="Checking candidate HS classification", depends_on=tuple(layer.layer_id for layer in layers)),
                ExecutionLayer(layer_id="requirements", label="Checking import requirements", depends_on=("classify",)),
                ExecutionLayer(layer_id="verify", label="Checking evidence", depends_on=("requirements",)),
            ]
        )
    else:
        layers.extend(
            [
                ExecutionLayer(layer_id="classify", label="Checking candidate HS classification", depends_on=tuple(layer.layer_id for layer in layers)),
                ExecutionLayer(layer_id="requirements", label="Checking import requirements", depends_on=("classify",)),
                ExecutionLayer(layer_id="calculate", label="Calculating landed cost", depends_on=("requirements",)),
                ExecutionLayer(layer_id="verify", label="Checking evidence", depends_on=("calculate",)),
            ]
        )

    if comparison_requested:
        prerequisite = layers[-1].layer_id
        layers.append(ExecutionLayer(layer_id="compare", label="Comparing trade routes", depends_on=(prerequisite,)))

    brief_dependency = layers[-1].layer_id if layers else None
    layers.append(
        ExecutionLayer(
            layer_id="brief",
            label="Building trade brief",
            depends_on=(brief_dependency,) if brief_dependency else (),
        )
    )
    payload = _plan_payload(intake, research_task_id, layers)
    return ExecutionPlan(
        research_task_id=research_task_id,
        intake_id=intake.intake_id,
        layers=tuple(layers),
        plan_hash=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )
