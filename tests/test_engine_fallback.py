import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.agent.engine import _build_deterministic_decision, _deterministic_route, run_agent


class DeterministicFallbackTests(unittest.TestCase):
    def test_extracts_origin_and_product_without_an_llm(self):
        route = _deterministic_route("Cotton t-shirts from Turkey to Uzbekistan. Check import duties.")

        self.assertEqual(route["origin_country"], "TR")
        self.assertEqual(route["product"], "Cotton t-shirts")
        self.assertEqual(route["pipeline"], ["parallel", "profit", "decision"])

    def test_builds_a_data_backed_brief_without_margin_claims(self):
        decision = _build_deterministic_decision({
            "product_target": "Cotton t-shirts",
            "origin_country": "TR",
            "market": {"origin_price_usd": 4.5, "origin_source": "Origin market"},
            "logistics": {"cost_per_kg_usd": 1.2, "transport_mode": "rail", "transit_days": 12},
            "trade": {"hs_code": "610910", "duty_pct": 10, "vat_pct": 12},
            "profit": {"total_landed_usd": 6.6, "margin_pct": 42},
            "confidence": {"overall": 0.7},
        })

        self.assertEqual(decision["decision"]["mode"], "data_backed")
        self.assertIn("Candidate HS classification: 610910", decision["answer"])
        self.assertIn("Commercial inputs still needed", decision["answer"])
        self.assertNotIn("margin", decision["answer"].lower())
        self.assertNotIn("selling price", decision["answer"].lower())

    def test_continues_with_data_backed_brief_when_router_provider_is_unavailable(self):
        async def exercise():
            phases = []
            market = {"origin_price_usd": 4.5, "origin_source": "Origin market", "confidence": 0.5}
            logistics = {"cost_per_kg_usd": 1.2, "transport_mode": "rail", "transit_days": 12, "confidence": 0.8}
            trade = {"hs_code": "610910", "duty_pct": 10, "vat_pct": 12, "confidence": 1.0}

            with patch("app.agent.engine._get_client", return_value=object()), patch(
                "app.agent.engine._route_intent", new=AsyncMock(side_effect=RuntimeError("provider quota exhausted"))
            ), patch(
                "app.agent.engine._run_parallel_services", new=AsyncMock(return_value=(market, logistics, trade))
            ):
                return await run_agent(
                    "Cotton t-shirts from Turkey to Uzbekistan",
                    progress_callback=lambda phase, _data: phases.append(phase),
                ), phases

        result, phases = asyncio.run(exercise())

        self.assertEqual(result["analysis_mode"], "deterministic")
        self.assertEqual(result["origin_country"], "TR")
        self.assertEqual(result["router"]["mode"], "deterministic")
        self.assertIn("Commercial inputs still needed", result["answer"])
        self.assertEqual(phases[-1], "decision")
