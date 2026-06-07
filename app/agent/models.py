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
    phases: Optional[dict] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    timestamp: datetime


class RouterPhase(BaseModel):
    detected_language: str
    product_category: str
    search_intent: str
    confidence: float


class DiscoverySource(BaseModel):
    source: str
    product_name: str
    price: float
    currency: str
    marketplace: str
    source_url: str
    confidence: float


class DiscoveryPhase(BaseModel):
    sources: List[DiscoverySource]
    average_price_usd: float
    total_sources: int


class TradeAnalystPhase(BaseModel):
    hs_code: str
    hs_description: str
    duty_rate: float
    vat_rate: float
    certifications: List[dict]
    freight: dict
    notes: str


class DecisionPhase(BaseModel):
    total_landed_cost_usd: float
    total_landed_cost_uzs: float
    breakdown: dict
    recommendations: List[dict]
    summary: str


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
