-- ============================================================
-- V39: price_cached_results + currency_rates
-- Real-time price cache layer for Trade Price Service
-- ============================================================

CREATE TABLE IF NOT EXISTS price_cached_results (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash      TEXT NOT NULL,
    product_name    TEXT NOT NULL,
    hs_code         TEXT,
    destination     CHAR(2),
    origin          CHAR(2) NOT NULL,
    price_usd       NUMERIC NOT NULL,
    currency        CHAR(3) DEFAULT 'USD',
    source_url      TEXT,
    marketplace     TEXT,
    confidence      NUMERIC DEFAULT 0.5,
    total_landed    NUMERIC,
    duty_pct        NUMERIC,
    vat_pct         NUMERIC,
    freight_pct     NUMERIC,
    scraped_at      TIMESTAMPTZ DEFAULT now(),
    ttl_hours       INT DEFAULT 24,
    expires_at      TIMESTAMPTZ GENERATED ALWAYS AS (scraped_at + (ttl_hours || ' hours')::INTERVAL) STORED
);

CREATE INDEX IF NOT EXISTS idx_cache_query_hash ON price_cached_results(query_hash);
CREATE INDEX IF NOT EXISTS idx_cache_expires ON price_cached_results(expires_at);

GRANT SELECT, INSERT ON price_cached_results TO anon, authenticated;


CREATE TABLE IF NOT EXISTS currency_rates (
    base        CHAR(3) DEFAULT 'USD',
    target      CHAR(3) NOT NULL,
    rate        NUMERIC NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (base, target)
);

GRANT SELECT, INSERT, UPDATE ON currency_rates TO anon, authenticated;


SELECT 'V39: price_cached_results + currency_rates deployed' AS status;
