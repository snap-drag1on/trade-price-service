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
