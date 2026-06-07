-- V55: CBU exchange rate API integration
-- Creates a function to fetch and store daily rates from cbu.uz

CREATE EXTENSION IF NOT EXISTS pg_net;

-- Function to call CBU API and store exchange rates
CREATE OR REPLACE FUNCTION sync_cbu_exchange_rates()
RETURNS TABLE(currency_code CHAR(3), rate_to_uzs NUMERIC, success BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    resp JSON;
    rate_record JSON;
BEGIN
    -- Fetch from Central Bank of Uzbekistan API
    SELECT content::json INTO resp
    FROM http_get('https://cbu.uz/uz/arkhiv-kursov-valyut/json/');

    IF resp IS NULL THEN
        RETURN QUERY SELECT 'USD'::CHAR(3), 0::NUMERIC, false;
        RETURN;
    END IF;

    FOR rate_record IN SELECT json_array_elements(resp)
    LOOP
        INSERT INTO uzs_exchange_rates (currency_code, rate_to_uzs, source, valid_from, valid_until)
        VALUES (
            (rate_record->>'Ccy')::CHAR(3),
            REPLACE(rate_record->>'Rate', ',', '.')::NUMERIC,
            'CBU',
            NOW()::DATE,
            (NOW() + INTERVAL '7 days')::DATE
        )
        ON CONFLICT DO NOTHING;
    END LOOP;

    RETURN QUERY SELECT e.currency_code, e.rate_to_uzs, true
    FROM uzs_exchange_rates e
    WHERE e.valid_from = NOW()::DATE;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION sync_cbu_exchange_rates TO service_role;

-- Trigger function to auto-clean old rates
CREATE OR REPLACE FUNCTION cleanup_old_exchange_rates()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    DELETE FROM uzs_exchange_rates
    WHERE valid_until < NOW() - INTERVAL '90 days';
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_cleanup_old_rates ON uzs_exchange_rates;
CREATE TRIGGER trg_cleanup_old_rates
    AFTER INSERT ON uzs_exchange_rates
    FOR EACH STATEMENT
    EXECUTE FUNCTION cleanup_old_exchange_rates();

COMMENT ON FUNCTION sync_cbu_exchange_rates IS 'Fetches daily exchange rates from cbu.uz API and stores them in uzs_exchange_rates';
