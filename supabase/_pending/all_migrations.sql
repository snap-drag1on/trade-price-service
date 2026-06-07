-- ===== v47_V47.sql =====
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


-- ===== v48_V48.sql =====
-- V48: Trade agreements + Certification requirements
-- Uzbekistan's preferential trade agreements and product certification rules

-- ========== 1. TRADE AGREEMENTS ==========

CREATE TABLE IF NOT EXISTS trade_agreements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    partner_country CHAR(2) NOT NULL REFERENCES countries(code),
    agreement_type VARCHAR(50) NOT NULL,
    full_name_uz TEXT,
    full_name_en TEXT,
    duty_reduction_pct NUMERIC DEFAULT 0,
    rules_of_origin TEXT,
    valid_from DATE NOT NULL,
    valid_until DATE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE trade_agreements IS 'Uzbekistan''s preferential trade agreements and their duty reduction impacts';

-- Real trade agreements (source: ADB ARIC, CBU, government portal)
INSERT INTO trade_agreements (partner_country, agreement_type, full_name_uz, full_name_en, duty_reduction_pct, rules_of_origin, valid_from, valid_until, notes)
SELECT * FROM (VALUES
    -- EAEU observer members: significant tariff preferences
    ('RU', 'EAEU', 'Yevrosiyo Iqtisodiy Ittifoqi doirasida erkin savdo', 'EAEU Free Trade Regime (Observer)', 100,
     'Goods must originate from EAEU member state. Certificate of Origin CT-1 required. At least 50% local content.',
     '2015-01-01', null, 'EAEU: Russia, Kazakhstan, Belarus, Kyrgyzstan, Armenia. Uzbekistan joined as observer in 2020. Zero duty on most industrial goods.'),
    ('KZ', 'EAEU', 'Yevrosiyo Iqtisodiy Ittifoqi doirasida erkin savdo', 'EAEU Free Trade Regime (Observer)', 100,
     'Goods must originate from EAEU member state. Certificate of Origin CT-1 required. At least 50% local content.',
     '2015-01-01', null, 'Same EAEU regime as Russia. Kazakhstan is also the main transit country for CN→UZ rail.'),
    ('BY', 'EAEU', 'Yevrosiyo Iqtisodiy Ittifoqi doirasida erkin savdo', 'EAEU Free Trade Regime (Observer)', 100,
     'Goods must originate from EAEU member state. Certificate of Origin CT-1 required. At least 50% local content.',
     '2015-01-01', null, 'EAEU member. Industrial machinery and food products from Belarus enter duty-free.'),
    ('KG', 'EAEU', 'Yevrosiyo Iqtisodiy Ittifoqi doirasida erkin savdo', 'EAEU Free Trade Regime (Observer)', 100,
     'Goods must originate from EAEU member state. Certificate of Origin CT-1 required. At least 50% local content.',
     '2015-01-01', null, 'EAEU member. Kyrgyzstan is also a transit country for CN→UZ road freight.'),
    ('AM', 'EAEU', 'Yevrosiyo Iqtisodiy Ittifoqi doirasida erkin savdo', 'EAEU Free Trade Regime (Observer)', 100,
     'Goods must originate from EAEU member state. Certificate of Origin CT-1 required. At least 50% local content.',
     '2015-01-01', null, 'EAEU member. Limited trade volume but full duty preference.'),
    -- CIS FTA (Commonwealth of Independent States FTA)
    ('RU', 'CIS_FTA', 'MDH Erkin Savdo Hududi', 'CIS Free Trade Area', 100,
     'Certificate of Origin CT-1 required. Goods must have at least 50% local content from CIS member.',
     '2012-01-01', null, 'CIS FTA: Uzbekistan, Russia, Kazakhstan, Belarus, Kyrgyzstan, Armenia, Moldova, Tajikistan. Overlaps with EAEU for most members.'),
    ('KZ', 'CIS_FTA', 'MDH Erkin Savdo Hududi', 'CIS Free Trade Area', 100,
     'Certificate of Origin CT-1 required. Goods must have at least 50% local content from CIS member.',
     '2012-01-01', null, 'Same as CIS FTA.'),
    ('BY', 'CIS_FTA', 'MDH Erkin Savdo Hududi', 'CIS Free Trade Area', 100,
     'Certificate of Origin CT-1 required. Goods must have at least 50% local content from CIS member.',
     '2012-01-01', null, 'Same as CIS FTA.'),
    ('KG', 'CIS_FTA', 'MDH Erkin Savdo Hududi', 'CIS Free Trade Area', 100,
     'Certificate of Origin CT-1 required. Goods must have at least 50% local content from CIS member.',
     '2012-01-01', null, 'Same as CIS FTA.'),
    ('AM', 'CIS_FTA', 'MDH Erkin Savdo Hududi', 'CIS Free Trade Area', 100,
     'Certificate of Origin CT-1 required. Goods must have at least 50% local content from CIS member.',
     '2012-01-01', null, 'Same as CIS FTA.'),
    -- Bilateral agreements
    ('TM', 'FTA', 'O''zbekiston-Turkmaniston Erkin Savdo Kelishuvi', 'Uzbekistan-Turkmenistan Free Trade Agreement', 100,
     'Goods produced in either country. Exceptions list applies (cement, textiles, furniture, etc. excluded from zero duty).',
     '2025-02-25', null, 'Signed July 2024, entered into force Feb 2025. Zero duty on most goods except certain categories.'),
    ('TR', 'PTA', 'O''zbekiston-Turkiya Preferensial Savdo Kelishuvi', 'Uzbekistan-Turkey Preferential Trade Agreement', 50,
     'Certificate of Origin A.TR required. Only applies to goods listed in the preference schedule. At least 40% local content.',
     '2023-01-01', null, 'Signed 2023. Covers ~200 product categories with reduced duties (average 50% reduction). Currently being expanded to full FTA.')
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM trade_agreements WHERE partner_country = seed_data.column1 AND agreement_type = seed_data.column2);

CREATE INDEX IF NOT EXISTS idx_ta_country ON trade_agreements(partner_country);
CREATE INDEX IF NOT EXISTS idx_ta_type ON trade_agreements(agreement_type);

GRANT SELECT ON trade_agreements TO anon, authenticated, service_role;

-- ========== 2. CERTIFICATION REQUIREMENTS ==========

CREATE TABLE IF NOT EXISTS certification_requirements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hs_chapter VARCHAR(2) NOT NULL,
    hs_description VARCHAR(200),
    cert_type VARCHAR(50) NOT NULL,
    cert_name_uz VARCHAR(200),
    cert_name_en VARCHAR(200),
    is_mandatory BOOLEAN DEFAULT true,
    estimated_cost_usd NUMERIC DEFAULT 300,
    validity_days INTEGER DEFAULT 365,
    testing_days INTEGER DEFAULT 14,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE certification_requirements IS 'Product certification requirements per HS chapter for Uzbekistan import';

-- Certification requirements (source: UzStandard Agency, USDA FAIRS report, Delta Global Solutions)
INSERT INTO certification_requirements (hs_chapter, hs_description, cert_type, cert_name_uz, cert_name_en, is_mandatory, estimated_cost_usd, validity_days, testing_days, notes)
SELECT * FROM (VALUES
    ('02', 'Go''sht va go''sht mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 400, 180, 21, 'Veterinary certificate also required. Testing at accredited lab in Tashkent.'),
    ('03', 'Baliq va dengiz mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 400, 180, 21, 'Veterinary certificate required. Origin country must be approved by Uzbek veterinary service.'),
    ('04', 'Sut va sut mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 500, 180, 21, 'Veterinary certificate required. Strict testing for bacterial content.'),
    ('07', 'Sabzavotlar', 'SanEpid', 'Fitosanitar sertifikat', 'Phytosanitary Certificate', true, 250, 180, 14, 'Required for all plant products. Testing for pesticides and GMO.'),
    ('08', 'Mevalar', 'SanEpid', 'Fitosanitar sertifikat', 'Phytosanitary Certificate', true, 250, 180, 14, 'Same as vegetables. Additional testing for tropical fruits.'),
    ('15', 'Yog''lar va moylar', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 400, 365, 14, 'O''simlik va hayvon yog''lari uchun majburiy.'),
    ('16', 'Qayta ishlangan go''sht', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 500, 180, 21, 'Konserva va kolbasa mahsulotlari uchun qo''shimcha tekshiruv.'),
    ('17', 'Shakar va qandolat', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 350, 365, 14, 'Standard food certification.'),
    ('18', 'Kakao va kakao mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 350, 365, 14, 'Standard food certification.'),
    ('19', 'Don mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 300, 365, 14, 'Nonlar, makaron, pechenye uchun.'),
    ('20', 'Sabzavot va meva konservalari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 350, 365, 14, 'Konserva mahsulotlari uchun standart sertifikat.'),
    ('21', 'Turli oziq-ovqat mahsulotlari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 350, 365, 14, 'Souslar, ziravorlar, qo''shimchalar.'),
    ('22', 'Ichimliklar, alkogol', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 500, 365, 21, 'Alcohol requires additional excise license. Testing for methanol content mandatory.'),
    ('24', 'Tamaki mahsulotlari', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 600, 365, 14, 'Excise stamp required. Special labeling requirements.'),
    ('25', 'Tuz, oltingugurt, tuproq', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Standard industrial certification.'),
    ('27', 'Mineral yoqilg''ilar, neft', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 800, 365, 21, 'Neft mahsulotlari uchun maxsus ruxsatnoma talab qilinadi.'),
    ('28', 'Noorganik kimyoviy moddalar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 500, 365, 21, 'Xavfli kimyoviy moddalar uchun qo''shimcha litsenziya.'),
    ('29', 'Organik kimyoviy moddalar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 500, 365, 21, 'Xavfli moddalar uchun maxsus talablar.'),
    ('30', 'Farmatsevtika mahsulotlari', 'SanEpid', 'Farmatsevtik litsenziya', 'Pharmaceutical License + SanEpid', true, 1500, 365, 60, 'O''zbekiston Sog''liqni Saqlash Vazirligidan ro''yxatdan o''tish talab qilinadi. 6-12 oy.'),
    ('31', 'O''g''itlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 400, 365, 14, 'Kimyoviy o''g''itlar uchun ekologik sertifikat ham talab qilinadi.'),
    ('33', 'Parfyumeriya va kosmetika', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 400, 365, 14, 'Kosmetika uchun majburiy sertifikat. Har bir mahsulot nomi uchun alohida.'),
    ('34', 'Sovun va yuvish vositalari', 'SanEpid', 'Sanitariya-epidemiologik xulosa', 'Sanitary-Epidemiological Certificate', true, 350, 365, 14, 'Standard chemical certification.'),
    ('38', 'Turli kimyoviy mahsulotlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 400, 365, 14, 'Xavflilik darajasiga qarab qo''shimcha talablar.'),
    ('39', 'Plastmassa va undan mahsulotlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Oziq-ovqat bilan kontaktda bo''ladigan plastmassa uchun SanEpid ham talab qilinadi.'),
    ('40', 'Kauchuk va rezina', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Transport vositalari uchun rezina qismlar qo''shimcha sertifikat talab qiladi.'),
    ('42', 'Teri mahsulotlari', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas, lekin bojxonada tekshiruvni tezlashtiradi.'),
    ('44', 'Yog''och va yog''och mahsulotlari', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Yog''ochning kelib chiqishi to''g''risidagi hujjat talab qilinadi.'),
    ('47', 'Qog''oz massasi', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', false, 200, 365, 7, 'Ixtiyoriy.'),
    ('48', 'Qog''oz va karton', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 250, 365, 7, 'Oziq-ovqat uchun mo''ljallangan qog''oz SanEpid talab qiladi.'),
    ('49', 'Kitob va bosma mahsulotlar', null, 'Talab qilinmaydi', 'Not Required', false, 0, 0, 0, 'Sertifikat talab qilinmaydi.'),
    ('50', 'Ipak', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('51', 'Jun', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('52', 'Paxta tolasi', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'O''zbekiston paxta tolasi asosiy eksport mahsuloti.'),
    ('54', 'Kimyoviy tolalar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'To''qimachilik sanoati uchun majburiy.'),
    ('55', 'Kimyoviy shtapel tolalar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Same as chemical fibers.'),
    ('56', 'Vatka va mato', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('57', 'Gilamlar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('58', 'Maxsus matolar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('59', 'Emdirilgan matolar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('60', 'Trikotaj matolar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('61', 'Trikotaj kiyimlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Bolalar kiyimlari uchun qattiqroq talablar (O''zDSt 1134).'),
    ('62', 'To''qimachilik kiyimlari', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Kattalar kiyimi uchun standart sertifikat.'),
    ('63', 'Tayyor to''qimachilik', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Choyshab, sochiq va shu kabi mahsulotlar.'),
    ('64', 'Oyog'' kiyimlari', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Bola oyoq kiyimi uchun qattiq talablar.'),
    ('68', 'Tosh, gips, sement', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Qurilish materiallari uchun ixtiyoriy.'),
    ('69', 'Keramika mahsulotlari', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Majburiy emas.'),
    ('70', 'Shisha va shisha mahsulotlari', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Oziq-ovqat bilan kontaktda bo''ladigan shisha uchun SanEpid talab qilinadi.'),
    ('71', 'Qimmatbaho metallar', 'CoC', 'Maxsus ruxsatnoma', 'Special Permit', true, 1000, 365, 30, 'Oltin, kumush, qimmatbaho toshlar uchun maxsus ruxsatnoma talab qilinadi.'),
    ('72', 'Cho''yan va po''lat', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 400, 365, 14, 'Metallurgiya sanoati uchun standart sertifikat.'),
    ('73', 'Po''latdan buyumlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Qurilish konstruksiyalari uchun qo''shimcha talablar.'),
    ('74', 'Mis va mis buyumlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Elektr kabel uchun mis qo''shimcha sertifikat talab qilmaydi.'),
    ('76', 'Alyuminiy', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Standard metal certification.'),
    ('82', 'Asboblar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 300, 365, 14, 'Elektr asboblar uchun qo''shimcha xavfsizlik testi.'),
    ('83', 'Turli metall buyumlar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 200, 365, 7, 'Qulflar, armatura va shu kabi.'),
    ('84', 'Mashina va mexanizmlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 800, 365, 21, 'Sanoat uskunalari uchun majburiy. Xavfsizlik talablari tekshiriladi.'),
    ('85', 'Elektr mashina va jihozlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 600, 365, 21, 'Elektronika va elektr jihozlar uchun majburiy. O''zDSt IEC standartlari asosida.'),
    ('86', 'Temir yo''l transporti', 'CoC', 'Maxsus texnik sertifikat', 'Technical Certificate', true, 1200, 365, 30, 'Temir yo''l transporti uchun maxsus texnik talablar.'),
    ('87', 'Transport vositalari', 'CoC', 'Transport vositasi sertifikati', 'Vehicle Type Certificate', true, 1500, 365, 45, 'Har bir model uchun alohida sertifikat. Yevro-5 standarti talab qilinadi.'),
    ('90', 'Tibbiy asboblar', 'SanEpid', 'Tibbiy ro''yxatdan o''tkazish', 'Medical Device Registration', true, 2000, 365, 90, 'O''zbekiston Sog''liqni Saqlash Vazirligida ro''yxatdan o''tish talab qilinadi. 3-6 oy.'),
    ('91', 'Soatlar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 150, 365, 7, 'Majburiy emas.'),
    ('94', 'Mebel', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 400, 365, 14, 'Yong''in xavfsizligi standartlariga muvofiqlik tekshiriladi.'),
    ('95', 'O''yinchoqlar', 'CoC', 'Muvofiqlik sertifikati', 'Certificate of Conformity', true, 350, 365, 14, 'Bolalar xavfsizligi standartlari talab qilinadi.'),
    ('96', 'Turli tayyor mahsulotlar', 'CoC', 'Ixtiyoriy sertifikat', 'Voluntary Certificate', false, 150, 365, 7, 'Majburiy emas.'),
    ('97', 'San''at asarlari', null, 'Talab qilinmaydi', 'Not Required', false, 0, 0, 0, 'Maxsus bojxona tartibi.'),
    ('99', 'Boshqa', null, 'Talab qilinmaydi', 'Not Required', false, 0, 0, 0, 'Yuqoridagi ro''yxatga kirmagan mahsulotlar. Majburiy sertifikat talab qilinmaydi.')
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM certification_requirements WHERE hs_chapter = seed_data.column1 AND cert_type = seed_data.column3);

CREATE INDEX IF NOT EXISTS idx_cert_hs ON certification_requirements(hs_chapter);
CREATE INDEX IF NOT EXISTS idx_cert_mandatory ON certification_requirements(is_mandatory);

GRANT SELECT ON certification_requirements TO anon, authenticated, service_role;


-- ===== v49_V49.sql =====
-- V49: Complete freight corridors seed
-- Real logistics routes from all major import origins to Uzbekistan
-- Sources: Tonlexing, CargoFromChina, ColliCare, RailFreight, KTZ, CBU

-- Seed freight_corridors for 15 major origins
INSERT INTO freight_corridors (origin_country_code, destination_country_code, transport_mode, transit_days_min, transit_days_max, cost_per_kg_usd, cost_per_container_usd, cost_per_cbm_usd)
SELECT * FROM (VALUES
    -- ===== CHINA → UZBEKISTAN (Uzbekistan's #1 import partner, 29.2% share) =====
    ('CN', 'UZ', 'rail', 10, 16, 1.2, 3200, 180),
    ('CN', 'UZ', 'road', 7, 14, 1.5, 4200, 220),
    ('CN', 'UZ', 'air', 1, 4, 5.5, 0, 0),
    -- Express train Xi'an→Tashkent via Khorgos (record: 5 days, normal: 10-12 days)
    -- Rail: $0.8-$1.5/kg, Road: $1.2-$1.8/kg, Air: $4.0-$7.0/kg
    -- Route: Xi'an → Alashankou/Khorgos → Almaty → Saryagash → Tashkent, 4486km

    -- ===== RUSSIA → UZBEKISTAN (21.8% share, EAEU observer) =====
    ('RU', 'UZ', 'rail', 7, 12, 1.0, 2800, 150),
    ('RU', 'UZ', 'road', 5, 8, 1.3, 3500, 180),
    ('RU', 'UZ', 'air', 1, 3, 4.5, 0, 0),
    -- Route: Moscow/Samara → Kazakhstan → Tashkent. Rail via Orenburg - Beyneu - Kungrad.
    -- Zero duty under EAEU/CIS FTA.

    -- ===== KAZAKHSTAN → UZBEKISTAN (7.8% share, EAEU observer) =====
    ('KZ', 'UZ', 'rail', 2, 4, 0.5, 1500, 80),
    ('KZ', 'UZ', 'road', 1, 3, 0.8, 2000, 100),
    -- Direct border crossing at Saryagash / Gishtkuprik. Major transit country for CN→UZ.
    -- Zero duty under EAEU/CIS FTA.

    -- ===== SOUTH KOREA → UZBEKISTAN (5.3% share) =====
    ('KR', 'UZ', 'air', 2, 5, 6.0, 0, 0),
    ('KR', 'UZ', 'rail', 20, 28, 2.0, 5000, 280),
    ('KR', 'UZ', 'sea', 25, 35, 1.5, 3500, 200),
    -- Sea: Busan → Vladivostok → Trans-Siberian rail → Kazakhstan → Uzbekistan (35 days)
    -- Air: Incheon → Tashkent (direct flights by Korean Air, Uzbekistan Airways)

    -- ===== TURKEY → UZBEKISTAN (4.8% share, PTA 50% duty reduction) =====
    ('TR', 'UZ', 'road', 10, 15, 1.8, 4500, 250),
    ('TR', 'UZ', 'air', 2, 4, 5.0, 0, 0),
    ('TR', 'UZ', 'rail', 12, 18, 1.5, 3800, 200),
    -- Road: Istanbul → Tehran → Ashgabat → Bukhara → Tashkent (or via Baku→Caspian→Turkmenbashi)
    -- Rail: Istanbul → Baku → Caspian ferry → Turkmenbashi → Tashkent
    -- PTA signed 2023, ~50% duty reduction on 200 product categories

    -- ===== TURKMENISTAN → UZBEKISTAN (2.9% share, FTA 2025) =====
    ('TM', 'UZ', 'road', 1, 2, 0.5, 1200, 60),
    ('TM', 'UZ', 'rail', 2, 3, 0.4, 1000, 50),
    -- Direct border. FTA signed Feb 2025 - zero duty on most goods.
    -- Route: Ashgabat → Bukhara → Tashkent or Turkmenabat → Karshi

    -- ===== GERMANY → UZBEKISTAN (2.8% share) =====
    ('DE', 'UZ', 'rail', 14, 21, 2.5, 6000, 350),
    ('DE', 'UZ', 'air', 2, 3, 6.5, 0, 0),
    -- Rail: Hamburg → Warsaw → Brest → Moscow → Kazakhstan → Uzbekistan (China Express route)
    -- Air: Frankfurt → Tashkent (Uzbekistan Airways, Lufthansa)
    -- Most common for industrial machinery and vehicles

    -- ===== INDIA → UZBEKISTAN (2.4% share) =====
    ('IN', 'UZ', 'air', 2, 5, 5.5, 0, 0),
    ('IN', 'UZ', 'road', 15, 25, 2.5, 5500, 300),
    ('IN', 'UZ', 'sea', 25, 35, 1.8, 4000, 220),
    -- Road: Delhi → Pakistan/Afghanistan → Termez or via Iran → Turkmenistan → Uzbekistan
    -- Sea: Nhava Sheva → Bandar Abbas (Iran) → road/rail → Uzbekistan
    -- Air: Delhi → Tashkent (direct flights)

    -- ===== BELARUS → UZBEKISTAN (1.5% share, EAEU) =====
    ('BY', 'UZ', 'rail', 8, 14, 1.2, 3000, 160),
    ('BY', 'UZ', 'road', 6, 10, 1.5, 3800, 190),
    -- Rail: Minsk → Moscow → Kazakhstan → Uzbekistan. Zero duty under EAEU.
    -- Route same as Russia rail via Kazakhstan.

    -- ===== USA → UZBEKISTAN (1.3% share) =====
    ('US', 'UZ', 'air', 3, 7, 8.0, 0, 0),
    ('US', 'UZ', 'sea', 30, 45, 2.5, 5500, 320),
    -- Air: JFK/Chicago/LAX → Tashkent (via Istanbul or Frankfurt)
    -- Sea/rail: US West Coast → Vladivostok → Trans-Siberian rail → Uzbekistan (35-45 days)
    -- Increasing trade: aircraft, machinery, medical equipment

    -- ===== KYRGYZSTAN → UZBEKISTAN (0.9% share, EAEU) =====
    ('KG', 'UZ', 'road', 1, 2, 0.4, 1000, 50),
    ('KG', 'UZ', 'rail', 1, 3, 0.3, 800, 40),
    -- Direct border crossing. Also transit for CN→UZ road via Irkeshtam pass.
    -- Zero duty under EAEU.

    -- ===== LATVIA → UZBEKISTAN (1.2% share) =====
    ('LV', 'UZ', 'rail', 12, 18, 2.0, 4800, 260),
    -- Key transit point for EU goods. Riga → Russia → Kazakhstan → Uzbekistan.
    -- Used for EU-made machinery, chemicals, food products.

    -- ===== IRAN → UZBEKISTAN (0.9% share) =====
    ('IR', 'UZ', 'road', 4, 8, 1.2, 3000, 160),
    ('IR', 'UZ', 'rail', 6, 10, 1.0, 2500, 140),
    -- Road: Tehran → Mashhad → Sarahs → Turkmenistan → Uzbekistan
    -- Rail: Tehran → Mashhad → Serakhs → Turkmenabad → Tashkent
    -- Key transit route for Turkey→UZ, also direct trade (building materials, food)

    -- ===== JAPAN → UZBEKISTAN (0.9% share) =====
    ('JP', 'UZ', 'air', 2, 5, 7.0, 0, 0),
    ('JP', 'UZ', 'sea', 25, 35, 2.2, 5200, 300),
    -- Air: Tokyo/Narita → Tashkent (via Incheon or Istanbul)
    -- Sea: Tokyo → Vladivostok → Trans-Siberian rail → Uzbekistan
    -- Main imports: auto parts, electronics, machinery

    -- ===== UAE → UZBEKISTAN (0.8% share) =====
    ('AE', 'UZ', 'air', 2, 3, 4.5, 0, 0),
    ('AE', 'UZ', 'road', 7, 12, 1.8, 4200, 240),
    -- Air: Dubai → Tashkent (multiple daily flights)
    -- Road: Dubai → Iran → Turkmenistan → Uzbekistan (re-export hub)
    -- Dubai is a major re-export hub; goods from China/India/Europe transit here

    -- ===== ITALY → UZBEKISTAN (1.0% share) =====
    ('IT', 'UZ', 'rail', 15, 22, 2.8, 6500, 380),
    ('IT', 'UZ', 'air', 2, 4, 7.0, 0, 0),
    -- Rail: Milan → Verona → Munich → Poland → Belarus → Russia → Kazakhstan → Uzbekistan
    -- Main imports: machinery, textiles, leather goods, furniture

    -- ===== FRANCE → UZBEKISTAN (0.9% share) =====
    ('FR', 'UZ', 'air', 2, 3, 6.5, 0, 0),
    ('FR', 'UZ', 'rail', 15, 22, 2.8, 6500, 380),
    -- Air: Paris → Tashkent (Uzbekistan Airways direct)
    -- Rail: Paris → Germany → Poland → Belarus → Russia → Kazakhstan → Uzbekistan
    -- Perfume, cosmetics, pharmaceuticals, machinery

    -- ===== POLAND → UZBEKISTAN (0.8% share) =====
    ('PL', 'UZ', 'road', 8, 14, 2.0, 4800, 260),
    ('PL', 'UZ', 'rail', 10, 16, 1.8, 4200, 230),
    -- Key EU distribution hub. Warsaw is a major rail terminal for China→Europe traffic.
    -- Goods from Poland to Uzbekistan via Belarus → Russia → Kazakhstan.

    -- ===== CZECH REPUBLIC → UZBEKISTAN (0.8% share) =====
    ('CZ', 'UZ', 'road', 10, 15, 2.2, 5000, 280),
    ('CZ', 'UZ', 'rail', 12, 18, 2.0, 4800, 260),
    -- Machinery, glass, beer, industrial equipment.
    -- Route: Prague → Poland → Belarus → Russia → Kazakhstan → Uzbekistan
) AS seed_data
ON CONFLICT DO NOTHING;


-- ===== v50_V50.sql =====
-- V50: HS Code Reference Table
-- Top imported HS chapters in Uzbekistan with descriptions
-- Source: UN COMTRADE, OEC World, Trading Economics, TradeInt

CREATE TABLE IF NOT EXISTS hs_code_reference (
    hs_chapter VARCHAR(2) PRIMARY KEY,
    hs_section VARCHAR(10),
    description_uz TEXT NOT NULL,
    description_en TEXT NOT NULL,
    description_ru TEXT NOT NULL,
    uzb_import_value_usd_b NUMERIC DEFAULT 0,
    uzb_import_rank INTEGER,
    typical_vat_pct NUMERIC DEFAULT 12,
    typical_freight_factor_pct NUMERIC DEFAULT 15,
    uzb_local_production BOOLEAN DEFAULT false,
    has_import_substitution BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE hs_code_reference IS 'HS code chapters with descriptions, import statistics, and trade parameters for Uzbekistan';

-- Top traded HS chapters in Uzbekistan (by 2024 import value, source: UN COMTRADE, OEC)
INSERT INTO hs_code_reference (hs_chapter, hs_section, description_uz, description_en, description_ru, uzb_import_value_usd_b, uzb_import_rank, typical_vat_pct, typical_freight_factor_pct, uzb_local_production, has_import_substitution, notes)
SELECT * FROM (VALUES
    -- Section IV - Food, Beverages, Tobacco
    ('10', 'II', 'Donli oʻsimliklar', 'Cereals', 'Злаки', 0.45, 25, 12, 30, true, false, 'Wheat imports from Kazakhstan. Uzbekistan is a major wheat consumer.'),
    ('15', 'III', 'Yogʻlar va moylar', 'Fats and oils', 'Жиры и масла', 0.32, 30, 12, 25, true, false, 'Vegetable oil imports. Sunflower and cottonseed oil produced locally.'),
    ('17', 'IV', 'Shakar va qandolat', 'Sugars and confectionery', 'Сахар и кондитерские изделия', 0.28, 35, 12, 25, true, false, 'Sugar imports despite local production capacity.'),
    ('22', 'IV', 'Ichimliklar, alkogol va sirka', 'Beverages, spirits and vinegar', 'Напитки, спирт и уксус', 0.18, 40, 20, 20, true, false, 'Higher VAT on alcohol (20%).') ,

    -- Section V - Mineral Products
    ('25', 'V', 'Tuz, oltingugurt, tuproq', 'Salt, sulphur, earths', 'Соль, сера, земля', 0.15, 45, 12, 20, true, false, 'Cement and construction minerals.'),
    ('27', 'V', 'Mineral yoqilgʻilar, neft', 'Mineral fuels, oils', 'Минеральное топливо, нефть', 2.10, 5, 12, 10, true, false, 'Major import category. Petroleum products from Russia and Kazakhstan. Local gas production.'),
    
    -- Section VI - Chemical Products
    ('28', 'VI', 'Noorganik kimyoviy moddalar', 'Inorganic chemicals', 'Неорганические химикаты', 0.22, 38, 12, 20, false, false, 'Industrial chemicals.'),
    ('29', 'VI', 'Organik kimyoviy moddalar', 'Organic chemicals', 'Органические химикаты', 0.35, 28, 12, 20, false, false, 'Dyes, pigments, industrial intermediates.'),
    ('30', 'VI', 'Farmatsevtika mahsulotlari', 'Pharmaceutical products', 'Фармацевтическая продукция', 1.20, 7, 12, 15, true, false, 'Large import category. Local production growing but insufficient.'),
    ('31', 'VI', 'Oʻgʻitlar', 'Fertilisers', 'Удобрения', 0.40, 26, 12, 20, true, true, 'Uzbekistan is a fertilizer exporter (potash). Some NPK types imported.'),
    ('32', 'VI', 'Ekvstraktlar, boʻyoqlar', 'Tanning extracts, dyes', 'Экстракты, красители', 0.25, 36, 12, 20, false, false, 'Industrial dyes, pigments for textile industry.'),
    ('33', 'VI', 'Parfyumeriya va kosmetika', 'Essential oils, cosmetics', 'Парфюмерия и косметика', 0.30, 32, 12, 20, true, false, 'Growing market. Local brands but significant imports.'),
    ('34', 'VI', 'Sovun va yuvish vositalari', 'Soap, washing preparations', 'Мыло и моющие средства', 0.20, 39, 12, 22, true, false, 'Local production covers basic needs. Premium imported.'),
    ('38', 'VI', 'Turli kimyoviy mahsulotlar', 'Miscellaneous chemical products', 'Прочие химические продукты', 0.45, 24, 12, 20, false, false, 'Adhesives, catalysts, industrial chemicals.'),

    -- Section VII - Plastics and Rubber
    ('39', 'VII', 'Plastmassa va undan mahsulotlar', 'Plastics and articles thereof', 'Пластмассы и изделия из них', 1.50, 6, 12, 18, true, false, 'Large import. Packaging materials, construction plastics.'),
    ('40', 'VII', 'Kauchuk va rezina', 'Rubber and articles thereof', 'Каучук и резина', 0.50, 22, 12, 18, false, false, 'Tires for vehicles are a major subcategory.'),

    -- Section X - Wood and Paper
    ('44', 'IX', 'Yogʻoch va yogʻoch mahsulotlari', 'Wood and articles of wood', 'Древесина и изделия из нее', 0.28, 34, 12, 25, false, false, 'Construction timber, furniture blanks.'),
    ('48', 'X', 'Qogʻoz va karton', 'Paper and paperboard', 'Бумага и картон', 0.35, 29, 12, 20, false, false, 'Packaging paper, printing paper.'),
    
    -- Section XI - Textiles and Textile Articles
    ('52', 'XI', 'Paxta tolasi', 'Cotton', 'Хлопок', 0.12, 48, 12, 20, true, true, 'Uzbekistan is a major cotton exporter. Import primarily synthetic fibers.'),
    ('54', 'XI', 'Kimyoviy tolalar', 'Man-made filaments', 'Химические нити', 0.55, 21, 12, 18, true, false, 'Synthetic fibers for textile industry.'),
    ('55', 'XI', 'Kimyoviy shtapel tolalar', 'Man-made staple fibres', 'Химические штапельные волокна', 0.40, 27, 12, 18, true, false, 'Raw material for local textile production.'),
    ('60', 'XI', 'Trikotaj matolar', 'Knitted fabrics', 'Трикотажные полотна', 0.25, 37, 12, 18, true, false, 'Intermediate textile products.'),
    ('61', 'XI', 'Trikotaj kiyimlar', 'Articles of apparel, knitted', 'Предметы одежды трикотажные', 0.65, 19, 12, 20, true, true, 'Growing local production but significant imports from China, Turkey.'),
    ('62', 'XI', 'Toʻqimachilik kiyimlari', 'Articles of apparel, not knitted', 'Предметы одежды нетрикотажные', 0.70, 17, 12, 20, true, true, 'Largest textile import category. Strong competition from Turkish brands.'),
    ('63', 'XI', 'Tayyor toʻqimachilik buyumlari', 'Made-up textile articles', 'Прочие текстильные изделия', 0.30, 31, 12, 20, true, false, 'Home textiles, bedding, curtains.'),

    -- Section XIII - Stone, Plaster, Glass
    ('69', 'XIII', 'Keramika mahsulotlari', 'Ceramic products', 'Керамические изделия', 0.45, 23, 12, 22, false, false, 'Tiles, sanitary ware. Major import from China, Turkey, Spain.'),
    ('70', 'XIII', 'Shisha va shisha mahsulotlari', 'Glass and glassware', 'Стекло и изделия из него', 0.18, 41, 12, 22, false, false, 'Glass bottles, architectural glass.'),

    -- Section XV - Base Metals
    ('72', 'XV', 'Choʻyan va poʻlat', 'Iron and steel', 'Чугун и сталь', 1.80, 4, 12, 18, true, false, 'Major import for construction and manufacturing.'),
    ('73', 'XV', 'Poʻlatdan buyumlar', 'Articles of iron or steel', 'Изделия из черных металлов', 0.80, 13, 12, 18, true, false, 'Steel structures, pipes, tanks.'),
    ('74', 'XV', 'Mis va mis buyumlar', 'Copper and articles thereof', 'Медь и изделия из нее', 0.22, 38, 12, 18, true, true, 'Uzbekistan exports copper but also imports certain products.'),
    ('76', 'XV', 'Alyuminiy va undan buyumlar', 'Aluminium and articles thereof', 'Алюминий и изделия из него', 0.30, 33, 12, 18, false, false, 'Aluminum profiles for construction.'),

    -- Section XVI - Machinery and Electrical
    ('84', 'XVI', 'Mashina va mexanizmlar, qozonlar', 'Nuclear reactors, boilers, machinery', 'Реакторы, котлы, оборудование', 4.20, 2, 12, 18, false, false, '2nd largest import category. Industrial machinery, pumps, compressors, construction equipment.'),
    ('85', 'XVI', 'Elektr mashina va jihozlar', 'Electrical machinery and equipment', 'Электрические машины и оборудование', 3.73, 1, 12, 18, false, false, 'LARGEST import category. Phones, computers, electronics, cables.'),
    
    -- Section XVII - Vehicles
    ('87', 'XVII', 'Transport vositalari', 'Vehicles other than railway', 'Средства наземного транспорта', 3.50, 3, 12, 15, true, false, '3rd largest. Cars, trucks, buses, auto parts. Chinese EVs growing rapidly.'),
    ('86', 'XVII', 'Temir yoʻl transporti', 'Railway vehicles', 'Железнодорожный транспорт', 0.15, 46, 12, 15, false, false, 'Locomotives, rolling stock for railway modernization.'),
    ('88', 'XVII', 'Havo transporti', 'Aircraft, spacecraft', 'Воздушный транспорт', 0.50, 20, 12, 5, false, false, 'Aircraft parts and maintenance. Uzbekistan Airways fleet modernization.'),
    
    -- Section XVIII - Precision Instruments
    ('90', 'XVIII', 'Tibbiy va optik asboblar', 'Optical, medical instruments', 'Оптические, медицинские приборы', 0.75, 16, 12, 10, false, false, 'Medical devices, measuring instruments, dental equipment.'),
    ('91', 'XVIII', 'Soatlar', 'Clocks and watches', 'Часы', 0.10, 50, 12, 15, false, false, 'Small but steady import.'),

    -- Section XX - Miscellaneous
    ('94', 'XX', 'Mebel va yotoq jihozlari', 'Furniture, bedding', 'Мебель, постельные принадлежности', 0.80, 14, 12, 22, true, false, 'Growing import. Local production exists but premium foreign brands dominate.'),
    ('95', 'XX', 'Oʻyinchoqlar va sport jihozlari', 'Toys, games, sports', 'Игрушки, игры, спорт', 0.35, 30, 12, 22, true, false, 'Chinese imports dominate this category.'),
    
    -- Top chapters summary for "other" HS codes
    ('99', 'XXI', 'Boshqa mahsulotlar', 'Other products', 'Прочие товары', 1.50, 8, 12, 15, false, false, 'Miscellaneous goods not elsewhere classified.')
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM hs_code_reference WHERE hs_chapter = seed_data.column1);

CREATE INDEX IF NOT EXISTS idx_hs_import_rank ON hs_code_reference(uzb_import_rank);

GRANT SELECT ON hs_code_reference TO anon, authenticated, service_role;


