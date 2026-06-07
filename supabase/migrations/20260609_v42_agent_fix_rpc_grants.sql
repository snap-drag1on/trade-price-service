BEGIN;

-- Grant service_role access to the tables used by api_search_sourcing RPC
GRANT SELECT ON ALL TABLES IN SCHEMA public TO service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO service_role;

-- Also ensure RPC execution grants
GRANT EXECUTE ON FUNCTION api_search_sourcing TO service_role;

SELECT 'V42: fixed service_role permissions for RPC queries' AS status;

COMMIT;
