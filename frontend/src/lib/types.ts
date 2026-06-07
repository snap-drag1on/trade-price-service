export interface QueryRequest {
  product: string;
  language: "uz" | "ru" | "en";
  destination?: string;
  max_results?: number;
  use_cache?: boolean;
}

export interface DiscoverySource {
  source: string;
  product_name: string;
  price: number;
  currency: string;
  marketplace: string;
  source_url: string;
  confidence: number;
}

export interface DiscoveryPhase {
  sources: DiscoverySource[];
  average_price_usd: number;
  total_sources: number;
}

export interface TradeAnalystPhase {
  hs_code: string;
  hs_description: string;
  duty_rate: number;
  vat_rate: number;
  certifications: Array<{
    type: string;
    cost_usd: number;
    duration_days: number;
  }>;
  freight: {
    origin: string;
    destination: string;
    cost_usd: number;
    days: number;
  };
  notes: string;
}

export interface DecisionPhase {
  total_landed_cost_usd: number;
  total_landed_cost_uzs: number;
  breakdown: {
    product: number;
    duty: number;
    vat: number;
    freight: number;
    certifications: number;
  };
  recommendations: Array<{
    source: string;
    reason: string;
    total_with_import: number;
  }>;
  summary: string;
}

export interface QueryResponse {
  success: boolean;
  task_id: string;
  status: "processing" | "completed" | "error";
  phases?: {
    router?: any;
    discovery?: DiscoveryPhase;
    analyst?: TradeAnalystPhase;
    decision?: DecisionPhase;
  };
  result?: any;
  error?: string;
  timestamp: string;
}
