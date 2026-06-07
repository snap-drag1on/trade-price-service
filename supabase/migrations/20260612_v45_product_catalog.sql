-- V45: New product catalog architecture
-- product_catalog = product identity (brand+model, specs, HS code)
-- marketplace_listings = URL references per marketplace (price=ephemeral, 24h cache)
-- Archive old flat tables

-- ========== 1. NEW TABLES ==========

CREATE TABLE IF NOT EXISTS product_catalog (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name    TEXT NOT NULL,
    brand           VARCHAR(100),
    model           VARCHAR(200),
    category        VARCHAR(100) NOT NULL,
    subcategory     VARCHAR(100),
    specs           JSONB DEFAULT '{}',
    hs_code         VARCHAR(20),
    confidence      NUMERIC DEFAULT 0.5,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pc_brand ON product_catalog(brand);
CREATE INDEX IF NOT EXISTS idx_pc_category ON product_catalog(category);
CREATE INDEX IF NOT EXISTS idx_pc_hs ON product_catalog(hs_code);

CREATE TABLE IF NOT EXISTS marketplace_listings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id      UUID NOT NULL REFERENCES product_catalog(id) ON DELETE CASCADE,
    marketplace     VARCHAR(50) NOT NULL CHECK (marketplace IN ('uzum','aliexpress','rakuten','ebay','olcha','asaxiy','mediapark','texnomart')),
    url             TEXT NOT NULL,
    listing_title   TEXT,
    last_price      NUMERIC,
    currency        VARCHAR(3),
    last_checked    TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ml_product ON marketplace_listings(product_id);
CREATE INDEX IF NOT EXISTS idx_ml_marketplace ON marketplace_listings(marketplace);
CREATE INDEX IF NOT EXISTS idx_ml_active ON marketplace_listings(is_active) WHERE is_active = true;

GRANT SELECT, INSERT, UPDATE ON product_catalog TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON marketplace_listings TO anon, authenticated, service_role;

-- ========== 2. ARCHIVE OLD TABLES ==========

ALTER TABLE IF EXISTS cn_product_catalog RENAME TO cn_product_catalog_archive;
ALTER TABLE IF EXISTS uz_product_catalog RENAME TO uz_product_catalog_archive;

-- ========== 3. MIGRATE EXISTING DATA ==========

-- Migrate cn_product_catalog_archive → product_catalog + marketplace_listings
INSERT INTO product_catalog (product_name, brand, model, category, subcategory, specs, hs_code, confidence, notes)
SELECT
    product_name,
    split_part(product_name, ' ', 1) AS brand,
    product_name AS model,
    category,
    subcategory,
    specs || jsonb_build_object(
        'price_min_usd', price_min_usd,
        'price_max_usd', price_max_usd,
        'price_avg_usd', price_avg_usd,
        'moq_min', moq_min,
        'variants', variants,
        'product_type', product_type
    ),
    hs_code,
    confidence,
    notes || ' [migrated from cn_product_catalog_archive]'
FROM cn_product_catalog_archive
ON CONFLICT DO NOTHING;

INSERT INTO marketplace_listings (product_id, marketplace, url, listing_title, last_checked)
SELECT
    pc.id,
    'aliexpress',
    COALESCE(ca.source_url, 'https://www.alibaba.com/'),
    ca.product_name,
    now()
FROM cn_product_catalog_archive ca
JOIN product_catalog pc ON pc.product_name = ca.product_name AND pc.hs_code = ca.hs_code
ON CONFLICT DO NOTHING;

-- Migrate uz_product_catalog_archive → product_catalog + marketplace_listings
INSERT INTO product_catalog (product_name, brand, model, category, subcategory, specs, confidence, notes)
SELECT
    product_name,
    brand,
    product_name AS model,
    category,
    subcategory,
    specs || jsonb_build_object(
        'rating', rating,
        'reviews_count', reviews_count
    ),
    confidence,
    notes || ' [migrated from uz_product_catalog_archive]'
FROM uz_product_catalog_archive
ON CONFLICT DO NOTHING;

INSERT INTO marketplace_listings (product_id, marketplace, url, listing_title, last_price, currency, last_checked)
SELECT
    pc.id,
    'uzum',
    COALESCE(ua.url, 'https://uzum.uz/'),
    ua.product_name,
    ua.price_uzs,
    'UZS',
    now()
FROM uz_product_catalog_archive ua
JOIN product_catalog pc ON pc.product_name = ua.product_name AND pc.brand = ua.brand
ON CONFLICT DO NOTHING;
