-- V49: Complete freight corridors seed
-- Real logistics routes from all major import origins to Uzbekistan
-- Sources: Tonlexing, CargoFromChina, ColliCare, RailFreight, KTZ, CBU

-- Drop if exists with incompatible schema
DROP TABLE IF EXISTS freight_corridors CASCADE;

CREATE TABLE freight_corridors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    origin_country_code CHAR(2) NOT NULL,
    destination_country_code CHAR(2) NOT NULL DEFAULT 'UZ',
    transport_mode VARCHAR(10) NOT NULL CHECK (transport_mode IN ('rail', 'road', 'air', 'sea')),
    transit_days_min INTEGER NOT NULL,
    transit_days_max INTEGER NOT NULL,
    cost_per_kg_usd NUMERIC NOT NULL DEFAULT 0,
    cost_per_container_usd NUMERIC DEFAULT 0,
    cost_per_cbm_usd NUMERIC DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_freight_origin ON freight_corridors(origin_country_code);
CREATE INDEX IF NOT EXISTS idx_freight_mode ON freight_corridors(transport_mode);

GRANT SELECT ON freight_corridors TO anon, authenticated, service_role;

-- Seed freight_corridors for 15 major origins
-- China: rail $1.2/kg, road $1.5/kg, air $5.5/kg | Route: Xi'an→Alashankou→Almaty→Tashkent, 4486km
-- Russia: rail $1.0/kg, road $1.3/kg, air $4.5/kg | Route: Moscow→Kazakhstan→Tashkent
-- Kazakhstan: rail $0.5/kg, road $0.8/kg | Direct border at Saryagash
-- South Korea: sea $1.5/kg, air $6.0/kg | Busan→Vladivostok→Trans-Siberian rail
-- Turkey: road $1.8/kg, rail $1.5/kg, air $5.0/kg | Istanbul→Tehran→Ashgabat→Bukhara
-- Turkmenistan: road $0.5/kg, rail $0.4/kg | Direct border FTA since 2025
-- Germany: rail $2.5/kg, air $6.5/kg | Hamburg→Warsaw→Brest→Moscow→Kazakhstan
-- India: road $2.5/kg, sea $1.8/kg, air $5.5/kg | Delhi→Iran→Turkmenistan→Termez
-- Belarus: rail $1.2/kg, road $1.5/kg | Minsk→Moscow→Kazakhstan→UZ (EAEU zero duty)
-- USA: sea $2.5/kg, air $8.0/kg | US West Coast→Vladivostok→Trans-Siberian rail
-- Kyrgyzstan: road $0.4/kg, rail $0.3/kg | Direct border, transit for CN→UZ road
-- Latvia: rail $2.0/kg | Riga→Russia→Kazakhstan→Uzbekistan (EU goods transit)
-- Iran: road $1.2/kg, rail $1.0/kg | Tehran→Mashhad→Sarahs→Turkmenistan
-- Japan: sea $2.2/kg, air $7.0/kg | Tokyo→Vladivostok→Trans-Siberian rail
-- UAE: road $1.8/kg, air $4.5/kg | Dubai→Iran→Turkmenistan (re-export hub)
-- Italy: rail $2.8/kg, air $7.0/kg | Milan→Verona→Munich→Poland→Belarus→Russia
-- France: rail $2.8/kg, air $6.5/kg | Paris→Germany→Poland→Belarus→Russia
-- Poland: road $2.0/kg, rail $1.8/kg | Warsaw→Belarus→Russia→Kazakhstan (EU hub)
-- Czech Republic: road $2.2/kg, rail $2.0/kg | Prague→Poland→Belarus→Russia→Kazakhstan
INSERT INTO freight_corridors (origin_country_code, destination_country_code, transport_mode, transit_days_min, transit_days_max, cost_per_kg_usd, cost_per_container_usd, cost_per_cbm_usd)
VALUES
    ('CN', 'UZ', 'rail', 10, 16, 1.2, 3200, 180),
    ('CN', 'UZ', 'road', 7, 14, 1.5, 4200, 220),
    ('CN', 'UZ', 'air', 1, 4, 5.5, 0, 0),
    ('RU', 'UZ', 'rail', 7, 12, 1.0, 2800, 150),
    ('RU', 'UZ', 'road', 5, 8, 1.3, 3500, 180),
    ('RU', 'UZ', 'air', 1, 3, 4.5, 0, 0),
    ('KZ', 'UZ', 'rail', 2, 4, 0.5, 1500, 80),
    ('KZ', 'UZ', 'road', 1, 3, 0.8, 2000, 100),
    ('KR', 'UZ', 'air', 2, 5, 6.0, 0, 0),
    ('KR', 'UZ', 'rail', 20, 28, 2.0, 5000, 280),
    ('KR', 'UZ', 'sea', 25, 35, 1.5, 3500, 200),
    ('TR', 'UZ', 'road', 10, 15, 1.8, 4500, 250),
    ('TR', 'UZ', 'air', 2, 4, 5.0, 0, 0),
    ('TR', 'UZ', 'rail', 12, 18, 1.5, 3800, 200),
    ('TM', 'UZ', 'road', 1, 2, 0.5, 1200, 60),
    ('TM', 'UZ', 'rail', 2, 3, 0.4, 1000, 50),
    ('DE', 'UZ', 'rail', 14, 21, 2.5, 6000, 350),
    ('DE', 'UZ', 'air', 2, 3, 6.5, 0, 0),
    ('IN', 'UZ', 'air', 2, 5, 5.5, 0, 0),
    ('IN', 'UZ', 'road', 15, 25, 2.5, 5500, 300),
    ('IN', 'UZ', 'sea', 25, 35, 1.8, 4000, 220),
    ('BY', 'UZ', 'rail', 8, 14, 1.2, 3000, 160),
    ('BY', 'UZ', 'road', 6, 10, 1.5, 3800, 190),
    ('US', 'UZ', 'air', 3, 7, 8.0, 0, 0),
    ('US', 'UZ', 'sea', 30, 45, 2.5, 5500, 320),
    ('KG', 'UZ', 'road', 1, 2, 0.4, 1000, 50),
    ('KG', 'UZ', 'rail', 1, 3, 0.3, 800, 40),
    ('LV', 'UZ', 'rail', 12, 18, 2.0, 4800, 260),
    ('IR', 'UZ', 'road', 4, 8, 1.2, 3000, 160),
    ('IR', 'UZ', 'rail', 6, 10, 1.0, 2500, 140),
    ('JP', 'UZ', 'air', 2, 5, 7.0, 0, 0),
    ('JP', 'UZ', 'sea', 25, 35, 2.2, 5200, 300),
    ('AE', 'UZ', 'air', 2, 3, 4.5, 0, 0),
    ('AE', 'UZ', 'road', 7, 12, 1.8, 4200, 240),
    ('IT', 'UZ', 'rail', 15, 22, 2.8, 6500, 380),
    ('IT', 'UZ', 'air', 2, 4, 7.0, 0, 0),
    ('FR', 'UZ', 'air', 2, 3, 6.5, 0, 0),
    ('FR', 'UZ', 'rail', 15, 22, 2.8, 6500, 380),
    ('PL', 'UZ', 'road', 8, 14, 2.0, 4800, 260),
    ('PL', 'UZ', 'rail', 10, 16, 1.8, 4200, 230),
    ('CZ', 'UZ', 'road', 10, 15, 2.2, 5000, 280),
    ('CZ', 'UZ', 'rail', 12, 18, 2.0, 4800, 260)
ON CONFLICT DO NOTHING;
