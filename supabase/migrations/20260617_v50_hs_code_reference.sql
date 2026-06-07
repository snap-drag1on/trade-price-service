-- V50: HS Code Reference Table
-- Top imported HS chapters in Uzbekistan with descriptions
-- Source: UN COMTRADE, OEC World, Trading Economics, TradeInt

DROP TABLE IF EXISTS hs_code_reference CASCADE;

CREATE TABLE hs_code_reference (
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
