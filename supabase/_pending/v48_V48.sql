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
