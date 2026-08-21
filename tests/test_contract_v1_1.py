import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.agent.contract_v1_1 import (
    DecisionBrief,
    DecisionBriefStatus,
    FieldState,
    TradeIntake,
    TradeIntakeField,
    TradeIntent,
    create_clarification,
    create_execution_plan,
    is_executable,
    normalize_legacy_message,
)
from app.agent.contract_runner_v1_1 import run_contract_v1_1
from app.agent.models import QueryRequest


class ContractV11Tests(unittest.TestCase):
    @staticmethod
    def _field(value, state=FieldState.CONFIRMED):
        return TradeIntakeField(value=value, state=state)

    def test_route_check_asks_at_most_three_dynamic_questions_before_execution(self):
        intake = TradeIntake(
            session_id="session-1",
            sequence=1,
            raw_user_message="I want to import shirts",
            intent=TradeIntent.ROUTE_CHECK,
            fields={"product": self._field("shirts"), "origin": self._field(None, FieldState.UNKNOWN)},
        )

        clarification = create_clarification(intake)

        self.assertIsNotNone(clarification)
        assert clarification is not None
        self.assertEqual(clarification.status, "needs_input")
        self.assertEqual(clarification.missing_fields, ("origin", "destination"))
        self.assertEqual([question.field for question in clarification.questions], ["origin", "destination"])
        self.assertFalse(is_executable(intake))

    def test_landed_cost_plan_requires_all_commercial_inputs(self):
        intake = TradeIntake(
            session_id="session-2",
            sequence=1,
            raw_user_message="Calculate landed cost",
            intent=TradeIntent.LANDED_COST,
            fields={
                "product": self._field("cotton t-shirts"),
                "origin": self._field("TR"),
                "destination": self._field("UZ"),
                "quantity": self._field(1000),
                "declared_value": self._field(5000),
                "currency": self._field("USD"),
                "valuation_basis": self._field("FOB"),
            },
        )

        plan = create_execution_plan(intake, "task-1")

        self.assertTrue(is_executable(intake))
        self.assertEqual(
            [layer.layer_id for layer in plan.layers],
            ["classify", "requirements", "calculate", "verify", "brief"],
        )
        self.assertEqual(len(plan.plan_hash), 64)

    def test_image_analysis_layer_is_optional_and_trace_is_not_fixed_seven_steps(self):
        intake = TradeIntake(
            session_id="session-3",
            sequence=1,
            raw_user_message="Find sourcing ideas for Uzbekistan under $10,000",
            intent=TradeIntent.DISCOVERY,
            fields={"destination": self._field("UZ"), "budget_or_constraints": self._field("under $10,000")},
        )

        plan = create_execution_plan(intake, "task-2", has_image=True)

        self.assertEqual([layer.layer_id for layer in plan.layers], ["image_analysis", "research", "verify", "brief"])
        self.assertEqual(len(plan.layers), 4)

    def test_complete_brief_requires_evidence_and_unknowns_have_a_reason(self):
        brief = DecisionBrief(
            research_task_id="task-3",
            status=DecisionBriefStatus.PARTIAL,
            scope={"destination": "UZ"},
            unknowns=({"field": "duty", "status": "UNKNOWN", "reason": "insufficient_evidence"},),
        )

        self.assertEqual(brief.status, DecisionBriefStatus.PARTIAL)
        with self.assertRaises(ValueError) as raised:
            DecisionBrief(
                research_task_id="task-3",
                status=DecisionBriefStatus.COMPLETE,
                scope={"destination": "UZ"},
            )
        self.assertIn("evidence", str(raised.exception))

    def test_query_endpoint_returns_clarification_without_scheduling_research(self):
        class BackgroundTaskSpy:
            def __init__(self):
                self.calls = []

            def add_task(self, *args, **kwargs):
                self.calls.append((args, kwargs))

        async def exercise():
            from app.api import create_query

            tasks = BackgroundTaskSpy()
            request = QueryRequest(product="I want to import shirts", destination=None)
            with patch("app.api.save_task", new=AsyncMock()) as save_task:
                response = await create_query(request, tasks)
            return response, tasks, save_task

        response, tasks, save_task = asyncio.run(exercise())

        self.assertEqual(response.status, "needs_input")
        self.assertIsNotNone(response.clarification)
        self.assertEqual(tasks.calls, [])
        self.assertEqual(save_task.await_count, 1)

    def test_route_runner_emits_dynamic_source_events_and_builds_no_margin_brief(self):
        async def exercise():
            intake = normalize_legacy_message(
                "Cotton t-shirts from Turkey to Uzbekistan",
                "session-route",
            )
            events = []

            async def capture(event):
                events.append(event)

            with patch("app.agent.contract_runner_v1_1._find_hs_code", new=AsyncMock(return_value="610910")), patch(
                "app.agent.contract_runner_v1_1._trade_engine",
                new=AsyncMock(return_value={"hs_code": "610910", "duty_pct": 17.5, "vat_pct": 12, "freight_pct": 15}),
            ):
                result = await run_contract_v1_1(intake, "task-route", event_callback=capture)
            return result, events

        result, events = asyncio.run(exercise())

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["decision_brief"]["status"], "complete")
        self.assertEqual(
            [layer["layer_id"] for layer in result["execution_plan"]["layers"]],
            ["classify", "requirements", "verify", "brief"],
        )
        self.assertTrue(any(event.event_type == "source.discovered" for event in events))
        source_event = next(event for event in events if event.event_type == "source.discovered")
        self.assertEqual(source_event.detail["source_ref"], "supabase:get_trade_costs")
        self.assertNotIn("margin", str(result).lower())


if __name__ == "__main__":
    unittest.main()
