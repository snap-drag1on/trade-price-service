-- V40: Fix missing rail freight data for AE, GB, US → UZ
-- Test found: AE and GB had no rail entry → freight=0 → ranked #1 incorrectly

GRANT INSERT ON country_logistics TO anon, authenticated, service_role;

INSERT INTO country_logistics (origin_country, destination_country, transport_mode, freight_rate_pct, insurance_pct, transit_days, valid_from, notes)
VALUES
    ('AE', 'UZ', 'rail', 12.0, 0.5, 18, '2026-01-01', 'AE → UZ multimodal (sea+rail via Iran) estimated 12%'),
    ('GB', 'UZ', 'rail', 10.0, 0.5, 20, '2026-01-01', 'GB → UZ multimodal (sea+rail via EU) estimated 10%'),
    ('US', 'UZ', 'rail', 18.0, 0.5, 30, '2026-01-01', 'US → UZ multimodal (sea+rail via EU) estimated 18%')
ON CONFLICT DO NOTHING;

SELECT 'V40: rail freight data added for AE, GB, US → UZ' AS status;
