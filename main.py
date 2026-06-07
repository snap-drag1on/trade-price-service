from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings, validate_config
from app.log import get_logger, setup_logging
from app.routers.search import router as search_router
from app.routers.prices import router as prices_router
from app.routers.agent import router as agent_router
from app.supabase_client import get_supabase, get_service_client

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(debug=settings.debug)
    warnings = validate_config()
    for w in warnings:
        logger.warning("Startup: %s", w)
    if not warnings:
        logger.info("All configuration OK")
    yield


app = FastAPI(
    title="Trade Price Service",
    description="Real-time market intelligence layer for multi-country import sourcing",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router, prefix="/api", tags=["search"])
app.include_router(prices_router, prefix="/api", tags=["prices"])
app.include_router(agent_router, prefix="/api", tags=["agent"])


@app.get("/health")
async def health():
    deps = {"app": "ok"}
    supabase = get_service_client()
    deps["supabase"] = "ok" if supabase else "missing_key"
    if supabase:
        try:
            supabase.table("price_cached_results").select("query_hash").limit(1).execute()
        except Exception as e:
            deps["supabase"] = f"error: {e}"
    deps["apify"] = "configured" if settings.apify_token else "not_configured"
    deps["rakuten"] = "configured" if settings.rakuten_app_id else "not_configured"
    deps["ebay"] = "configured" if settings.ebay_app_id else "not_configured"
    all_ok = all(v == "ok" or v == "configured" for v in deps.values())
    status = "ok" if all_ok else "degraded"
    return {"status": status, "dependencies": deps}
