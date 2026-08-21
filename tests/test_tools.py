import asyncio
import unittest
from unittest.mock import patch

from app.agent.tools import get_trade_costs


class _FailingClient:
    def rpc(self, *_args, **_kwargs):
        raise RuntimeError("stale service credential")


class _SuccessfulQuery:
    def execute(self):
        return type(
            "Response",
            (),
            {
                "data": {
                    "results": [
                        {
                            "origin": "CN",
                            "trade_costs": {
                                "duty_rate_pct": 20,
                                "vat_rate_pct": 12,
                                "freight_rate_pct": 15,
                            },
                        }
                    ]
                }
            },
        )()


class _SuccessfulClient:
    def rpc(self, *_args, **_kwargs):
        return _SuccessfulQuery()


class TradeCostToolTests(unittest.TestCase):
    def test_uses_anon_rpc_when_service_client_is_stale(self):
        async def exercise():
            with patch("app.agent.tools.get_service_client", return_value=_FailingClient()), patch(
                "app.agent.tools.get_supabase", return_value=_SuccessfulClient()
            ):
                return await get_trade_costs("CN", "UZ", "610910")

        result = asyncio.run(exercise())
        self.assertTrue(result.success)
        self.assertEqual(result.data["duty_pct"], 20.0)
        self.assertEqual(result.data["vat_pct"], 12.0)
