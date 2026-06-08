from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class QueryRequest(BaseModel):
    product: str = Field(..., min_length=1, description="Mahsulot nomi")
    language: str = Field("uz", pattern="^(uz|ru|en)$")
    destination: str = Field("UZ", min_length=2, max_length=2)
    max_results: int = Field(5, ge=1, le=20)
    use_cache: bool = Field(True)


class QueryResponse(BaseModel):
    success: bool
    task_id: str
    status: str
    flow: Optional[str] = None
    phases: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    timestamp: datetime


class PhaseProgress(BaseModel):
    status: str = "pending"  # pending | running | completed | skipped | error
    progress: float = 0.0    # 0.0 - 1.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    details: Optional[dict] = None


class RouterPhase(BaseModel):
    intent: str
    pipeline: List[str]
    product: str
    detected_language: Optional[str] = None
    confidence: float = 1.0


class OpportunityItem(BaseModel):
    product_name: str
    category: Optional[str] = None
    demand_score: float = 0
    competition_score: float = 0
    signal: Optional[str] = None
    source: str = "web"


class OpportunityPhase(BaseModel):
    opportunities: List[OpportunityItem] = []
    sources_used: List[str] = []


class MarketData(BaseModel):
    product_name: str = ""
    china_price_usd: Optional[float] = None
    china_source: Optional[str] = None
    uz_price_usd: Optional[float] = None
    uz_price_uzs: Optional[float] = None
    uz_source: Optional[str] = None
    weight_kg: Optional[float] = None
    currency: str = "USD"
    confidence: float = 0.0


class LogisticsData(BaseModel):
    origin: str = "CN"
    destination: str = "UZ"
    transport_mode: str = "rail"
    distance_km: Optional[int] = None
    transit_days: Optional[int] = None
    cost_per_kg_usd: Optional[float] = None
    total_freight_usd: Optional[float] = None
    confidence: float = 0.0


class TradeData(BaseModel):
    hs_code: Optional[str] = None
    hs_description: Optional[str] = None
    duty_pct: Optional[float] = None
    vat_pct: Optional[float] = None
    freight_pct: Optional[float] = None
    certifications: List[dict] = []
    confidence: float = 0.0


class ProfitData(BaseModel):
    price_usd: Optional[float] = None
    duty_amount: Optional[float] = None
    vat_amount: Optional[float] = None
    freight_amount: Optional[float] = None
    total_landed_usd: Optional[float] = None
    total_landed_uzs: Optional[float] = None
    market_price_usd: Optional[float] = None
    profit_usd: Optional[float] = None
    margin_pct: Optional[float] = None


class ConfidenceMetrics(BaseModel):
    market_score: float = 0.0
    logistics_score: float = 0.0
    trade_score: float = 0.0
    profit_score: float = 0.0
    overall: float = 0.0


class PriceCheckRequest(BaseModel):
    product_query: str
    origin: str
    destination: str
    price_original: float
    currency: str = "USD"
    hs_code: Optional[str] = None
    transport_mode: str = "rail"
    marketplace: str = "Manual"


class PriceCheckResponse(BaseModel):
    total_landed_usd: float
    total_landed_uzs: float
    breakdown: dict
    saved: bool


class ComparisonRequest(BaseModel):
    offer_1: dict
    offer_2: dict
    destination: str = "UZ"


class ComparisonResponse(BaseModel):
    offer_1_landed: float
    offer_2_landed: float
    savings_usd: float
    savings_percent: float
    recommendation: str
