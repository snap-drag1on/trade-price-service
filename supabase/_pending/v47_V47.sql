-- V47: Countries reference + UZS exchange rates
-- Reference data for all trade-related country information

-- ========== 1. COUNTRIES ==========

CREATE TABLE IF NOT EXISTS countries (
    code CHAR(2) PRIMARY KEY,
    name_uz VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_ru VARCHAR(100) NOT NULL,
    currency CHAR(3) NOT NULL,
    currency_name VARCHAR(50),
    region VARCHAR(50) NOT NULL,
    trade_bloc VARCHAR(50),
    is_uzbekistan BOOLEAN DEFAULT false,
    has_preferential_trade BOOLEAN DEFAULT false,
    import_share_pct NUMERIC DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE countries IS 'All countries referenced in trade calculations, with trade bloc and preference info';
COMMENT ON COLUMN countries.trade_bloc IS 'EAEU, CIS_FTA, EU, GSP, or null';
COMMENT ON COLUMN countries.import_share_pct IS '% of Uzbekistan total imports (source: CBU, 2024 data)';

-- Seed Uzbekistan
INSERT INTO countries (code, name_uz, name_en, name_ru, currency, currency_name, region, trade_bloc, is_uzbekistan, import_share_pct)
VALUES ('UZ', 'O''zbekiston', 'Uzbekistan', 'Узбекистан', 'UZS', 'Uzbek Soum', 'Central Asia', null, true, 0)
ON CONFLICT (code) DO NOTHING;

-- Seed top 25 trade partners (by 2024 import value, source: Trading Economics / CBU)
INSERT INTO countries (code, name_uz, name_en, name_ru, currency, currency_name, region, trade_bloc, has_preferential_trade, import_share_pct)
SELECT * FROM (VALUES
    ('CN', 'Xitoy', 'China', 'Китай', 'CNY', 'Yuan Renminbi', 'East Asia', null, false, 29.2),
    ('RU', 'Rossiya', 'Russia', 'Россия', 'RUB', 'Russian Ruble', 'Europe/East', 'EAEU', true, 21.8),
    ('KZ', 'Qozog''iston', 'Kazakhstan', 'Казахстан', 'KZT', 'Kazakh Tenge', 'Central Asia', 'EAEU', true, 7.8),
    ('KR', 'Janubiy Koreya', 'South Korea', 'Южная Корея', 'KRW', 'South Korean Won', 'East Asia', null, false, 5.3),
    ('TR', 'Turkiya', 'Turkey', 'Турция', 'TRY', 'Turkish Lira', 'Middle East', null, true, 4.8),
    ('TM', 'Turkmaniston', 'Turkmenistan', 'Туркменистан', 'TMT', 'Turkmen Manat', 'Central Asia', null, true, 2.9),
    ('DE', 'Germaniya', 'Germany', 'Германия', 'EUR', 'Euro', 'Europe', 'EU', false, 2.8),
    ('IN', 'Hindiston', 'India', 'Индия', 'INR', 'Indian Rupee', 'South Asia', null, false, 2.4),
    ('BY', 'Belarus', 'Belarus', 'Беларусь', 'BYN', 'Belarusian Ruble', 'Europe/East', 'EAEU', true, 1.5),
    ('US', 'Amerika Qo''shma Shtatlari', 'United States', 'США', 'USD', 'US Dollar', 'North America', null, false, 1.3),
    ('KG', 'Qirg''iziston', 'Kyrgyzstan', 'Киргизия', 'KGS', 'Kyrgyz Som', 'Central Asia', 'EAEU', true, 0.9),
    ('LV', 'Latviya', 'Latvia', 'Латвия', 'EUR', 'Euro', 'Europe', 'EU', false, 1.2),
    ('IT', 'Italiya', 'Italy', 'Италия', 'EUR', 'Euro', 'Europe', 'EU', false, 1.0),
    ('IR', 'Eron', 'Iran', 'Иран', 'IRR', 'Iranian Rial', 'Middle East', null, false, 0.9),
    ('FR', 'Fransiya', 'France', 'Франция', 'EUR', 'Euro', 'Europe', 'EU', false, 0.9),
    ('JP', 'Yaponiya', 'Japan', 'Япония', 'JPY', 'Japanese Yen', 'East Asia', null, false, 0.9),
    ('AE', 'Birlashgan Arab Amirliklari', 'United Arab Emirates', 'ОАЭ', 'AED', 'UAE Dirham', 'Middle East', null, false, 0.8),
    ('PL', 'Polsha', 'Poland', 'Польша', 'PLN', 'Polish Zloty', 'Europe', 'EU', false, 0.8),
    ('CZ', 'Chexiya', 'Czech Republic', 'Чехия', 'CZK', 'Czech Koruna', 'Europe', 'EU', false, 0.8),
    ('NL', 'Niderlandiya', 'Netherlands', 'Нидерланды', 'EUR', 'Euro', 'Europe', 'EU', false, 0.7),
    ('GB', 'Buyuk Britaniya', 'United Kingdom', 'Великобритания', 'GBP', 'Pound Sterling', 'Europe', null, false, 0.5),
    ('CH', 'Shveytsariya', 'Switzerland', 'Швейцария', 'CHF', 'Swiss Franc', 'Europe', null, false, 0.6),
    ('GE', 'Gruziya', 'Georgia', 'Грузия', 'GEL', 'Georgian Lari', 'Caucasus', null, false, 0.6),
    ('AT', 'Avstriya', 'Austria', 'Австрия', 'EUR', 'Euro', 'Europe', 'EU', false, 0.5),
    ('AM', 'Armaniston', 'Armenia', 'Армения', 'AMD', 'Armenian Dram', 'Caucasus', 'EAEU', true, 0.3)
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM countries WHERE code = seed_data.column1);

CREATE INDEX IF NOT EXISTS idx_countries_region ON countries(region);
CREATE INDEX IF NOT EXISTS idx_countries_bloc ON countries(trade_bloc);

GRANT SELECT ON countries TO anon, authenticated, service_role;

-- ========== 2. UZS EXCHANGE RATES ==========
-- Official Central Bank of Uzbekistan rates

CREATE TABLE IF NOT EXISTS uzs_exchange_rates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    currency_code CHAR(3) NOT NULL,
    rate_to_uzs NUMERIC NOT NULL,
    source VARCHAR(50) DEFAULT 'CBU',
    valid_from DATE NOT NULL,
    valid_until DATE,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uzs_rates_currency ON uzs_exchange_rates(currency_code, valid_from DESC);

COMMENT ON TABLE uzs_exchange_rates IS 'Official UZS exchange rates from Central Bank of Uzbekistan (cbu.uz)';

-- Historical CBU rates (source: cbu.uz, goldenpages.uz, nbu.uz, valutafx)
INSERT INTO uzs_exchange_rates (currency_code, rate_to_uzs, source, valid_from, valid_until)
SELECT * FROM (VALUES
    ('USD', 12938.01, 'CBU', '2025-05-06', '2025-05-12'),
    ('EUR', 14673.00, 'CBU', '2025-05-06', '2025-05-12'),
    ('RUB', 158.73,   'CBU', '2025-05-06', '2025-05-12'),
    ('CNY', 1779.30,  'CBU', '2025-05-06', '2025-05-12'),
    ('JPY', 89.93,    'CBU', '2025-05-06', '2025-05-12'),
    ('KZT', 24.98,    'CBU', '2025-05-06', '2025-05-12'),
    ('GBP', 17211.43, 'CBU', '2025-05-06', '2025-05-12'),
    ('CHF', 15100.00, 'CBU', '2025-05-06', '2025-05-12'),
    -- June 2025
    ('USD', 12655.00, 'CBU', '2025-06-30', '2025-07-06'),
    ('EUR', 14200.00, 'CBU', '2025-06-30', '2025-07-06'),
    ('RUB', 155.00,   'CBU', '2025-06-30', '2025-07-06'),
    ('CNY', 1740.00,  'CBU', '2025-06-30', '2025-07-06'),
    -- November 2025 (lowest point)
    ('USD', 11869.00, 'CBU', '2025-11-28', '2025-12-04'),
    ('EUR', 13200.00, 'CBU', '2025-11-28', '2025-12-04'),
    ('RUB', 142.00,   'CBU', '2025-11-28', '2025-12-04'),
    ('CNY', 1620.00,  'CBU', '2025-11-28', '2025-12-04'),
    -- June 2026 (current, source: nbu.uz 05.06.2026)
    ('USD', 12000.00, 'CBU', '2026-06-05', null),
    ('EUR', 13800.00, 'CBU', '2026-06-05', null),
    ('RUB', 165.00,   'CBU', '2026-06-05', null),
    ('CNY', 1700.00,  'CBU', '2026-06-05', null),
    ('JPY', 76.00,    'CBU', '2026-06-05', null),
    ('KZT', 25.00,    'CBU', '2026-06-05', null),
    ('GBP', 16000.00, 'CBU', '2026-06-05', null),
    ('CHF', 15200.00, 'CBU', '2026-06-05', null),
    ('KRW', 8.50,     'CBU', '2026-06-05', null),
    ('TRY', 370.00,   'CBU', '2026-06-05', null),
    ('AED', 3270.00,  'CBU', '2026-06-05', null),
    ('INR', 144.00,   'CBU', '2026-06-05', null)
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM uzs_exchange_rates WHERE currency_code = seed_data.column1 AND valid_from = seed_data.column3);

GRANT SELECT ON uzs_exchange_rates TO anon, authenticated, service_role;
