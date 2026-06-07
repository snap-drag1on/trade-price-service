from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.log import setup_logging, get_logger
from app.config import settings, validate_config
from app.api import router as api_router
from app.routers import agent, prices, search

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Trade Price Service starting...")

    warnings = validate_config()
    for warning in warnings:
        logger.warning("%s", warning)

    try:
        from app.supabase_client import get_service_client
        supabase = get_service_client()
        if supabase:
            logger.info("Supabase service client connected")
    except Exception as e:
        logger.warning("Supabase connection optional: %s", e)

    logger.info("Service ready!")
    yield
    logger.info("Trade Price Service shutting down...")


app = FastAPI(
    title="Trade Price Service",
    description="AI-powered import cost calculator for Uzbekistan",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={
                "success": False,
                "error": e.detail,
                "path": request.url.path,
            },
        )
    except Exception as e:
        logger.error("Unhandled error: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Internal server error",
                "path": request.url.path,
            },
        )


app.include_router(api_router)

app.include_router(agent.router, prefix="/routers")
app.include_router(prices.router, prefix="/routers")
app.include_router(search.router, prefix="/routers")


@app.get("/")
async def root():
    return {
        "service": "Trade Price Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


@app.get("/docs-custom")
async def custom_docs():
    return {
        "endpoints": {
            "POST /api/v1/query": {
                "description": "Start agent query (async)",
                "returns": "task_id for polling",
            },
            "GET /api/v1/query/{task_id}": {
                "description": "Get query status and results",
                "returns": "QueryResponse with phases",
            },
            "POST /api/v1/price-check": {
                "description": "Manual price calculation",
                "returns": "PriceCheckResponse with landing cost",
            },
            "POST /api/v1/compare": {
                "description": "Compare 2 offers",
                "returns": "ComparisonResponse",
            },
            "GET /api/v1/health": {
                "description": "Server health check",
                "returns": "Status info",
            },
            "POST /api/v1/admin/sync-cbu": {
                "description": "Manually trigger CBU rate sync",
                "returns": "Sync result",
            },
        }
    }


if __name__ == "__main__":
    setup_logging(debug=settings.debug)
    logger.info("Trade Price Service initialized")

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
