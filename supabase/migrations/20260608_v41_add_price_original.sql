BEGIN;

ALTER TABLE price_cached_results
ADD COLUMN IF NOT EXISTS price_original NUMERIC;

GRANT SELECT, INSERT ON price_cached_results TO anon, authenticated;
GRANT SELECT, INSERT ON price_cached_results TO service_role;

SELECT 'V41: added price_original column to price_cached_results' AS status;

COMMIT;
