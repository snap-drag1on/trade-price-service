import asyncio
import unittest
from unittest.mock import patch

from app.agent.tools import get_trade_costs


class _FailingClient:
    def __init__(self):
        self.called = False

    def rpc(self, *_args, **_kwargs):
        self.called = True
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
    def test_prefers_anon_rpc_before_a_stale_service_client(self):
        async def exercise():
            service_client = _FailingClient()
            with patch("app.agent.tools.get_service_client", return_value=service_client), patch(
                "app.agent.tools.get_supabase", return_value=_SuccessfulClient()
            ):
                result = await get_trade_costs("CN", "UZ", "610910")
            return result, service_client

        result, service_client = asyncio.run(exercise())
        self.assertTrue(result.success)
        self.assertEqual(result.data["duty_pct"], 20.0)
        self.assertEqual(result.data["vat_pct"], 12.0)
        self.assertFalse(service_client.called)
