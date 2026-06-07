-- V43: Create cn_product_catalog table for Chinese product master data
-- Stores comprehensive product info from Alibaba/Aliexpress research
-- Each row = one product type with price range, variants, specs

CREATE TABLE IF NOT EXISTS cn_product_catalog (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hs_code         VARCHAR(20) NOT NULL,
    category        VARCHAR(100) NOT NULL,
    subcategory     VARCHAR(100),
    product_name    TEXT NOT NULL,
    product_type    VARCHAR(100),
    specs           JSONB DEFAULT '{}',
    price_min_usd   NUMERIC,
    price_max_usd   NUMERIC,
    price_avg_usd   NUMERIC,
    moq_min         INTEGER,
    variants        TEXT[] DEFAULT '{}',
    source_url      TEXT,
    marketplace     VARCHAR(50) DEFAULT 'Alibaba',
    confidence      NUMERIC DEFAULT 0.5,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_cn_catalog_hs ON cn_product_catalog(hs_code);
CREATE INDEX IF NOT EXISTS idx_cn_catalog_category ON cn_product_catalog(category);

-- Grant access
GRANT SELECT, INSERT, UPDATE ON cn_product_catalog TO anon, authenticated, service_role;
