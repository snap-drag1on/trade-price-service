-- V44: Create uz_product_catalog table for Uzum Market product research
-- Each row = one product type with current UZS selling prices
-- Used for comparing CN landed costs vs. local selling prices

CREATE TABLE IF NOT EXISTS uz_product_catalog (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category            VARCHAR(100) NOT NULL,
    subcategory         VARCHAR(100),
    product_name        TEXT NOT NULL,
    brand               VARCHAR(100),
    price_uzs           NUMERIC NOT NULL,
    price_uzs_original  NUMERIC,
    specs               JSONB DEFAULT '{}',
    rating              NUMERIC DEFAULT 0,
    reviews_count       INTEGER DEFAULT 0,
    url                 TEXT,
    category_url        TEXT,
    confidence          NUMERIC DEFAULT 0.5,
    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uz_catalog_category ON uz_product_catalog(category);
CREATE INDEX IF NOT EXISTS idx_uz_catalog_brand ON uz_product_catalog(brand);

GRANT SELECT, INSERT, UPDATE ON uz_product_catalog TO anon, authenticated, service_role;
