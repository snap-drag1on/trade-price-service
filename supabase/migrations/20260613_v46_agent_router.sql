-- V46: Agent Router + Opportunity Signals
-- These tables control the AI agent's routing behavior and cache discovery results

-- ========== 1. AGENT ROUTER ==========
-- Maps user intents to agent pipeline sequences

CREATE TABLE IF NOT EXISTS agent_router (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    intent VARCHAR(50) UNIQUE NOT NULL,
    pipeline TEXT[] NOT NULL,
    keywords TEXT[] NOT NULL DEFAULT '{}',
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Seed router configs
INSERT INTO agent_router (intent, pipeline, keywords, description) VALUES
('discovery', ARRAY['discovery','trade_analyst','decision'], ARRAY['nima','qanday mahsulot','trend','imkoniyat','foydali','kerakli','top','tavsiya','goya','trade idea','opportunity'], 'Yangi mahsulot imkoniyatlarini topish. Discovery → Trade Analyst → Decision'),
('trade_check', ARRAY['trade_analyst','decision'], ARRAY['narxi','qancha tushadi','landed','import','olib kirish','keltirish','landed cost','qiymati','bahosi','sotib olish'], 'Aniq mahsulotni olib kirish hisobi. Trade Analyst → Decision'),
('comparison', ARRAY['trade_analyst','decision'], ARRAY['solishtirish','farqi','qaysi','china yoki','turkiya yoki','taqqoslash','variant'], 'Ikki yoki undan ortiq variantni solishtirish. Trade Analyst → Decision'),
('simple', ARRAY['trade_analyst'], ARRAY['HS code','boj','tarif','logistika','yuk','kod','duty','vat','stavka'], 'Oddiy ma''lumot so''rovi. Faqat Trade Analyst')
ON CONFLICT (intent) DO NOTHING;

-- ========== 2. OPPORTUNITY SIGNALS ==========
-- Cached discovery results for trending/underserved products

CREATE TABLE IF NOT EXISTS opportunity_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_name TEXT NOT NULL,
    category VARCHAR(100),
    demand_score INTEGER CHECK (demand_score BETWEEN 0 AND 100),
    competition_score INTEGER CHECK (competition_score BETWEEN 0 AND 100),
    sources TEXT[],
    signal_text TEXT,
    confidence NUMERIC DEFAULT 0.5,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_os_category ON opportunity_signals(category);
CREATE INDEX IF NOT EXISTS idx_os_demand ON opportunity_signals(demand_score DESC);

-- ========== 3. PERMISSIONS ==========

GRANT SELECT, INSERT, UPDATE ON agent_router TO anon, authenticated, service_role;
GRANT SELECT, INSERT, UPDATE ON opportunity_signals TO anon, authenticated, service_role;

-- ========== 4. SEED OPPORTUNITY SIGNALS ==========
-- Common known opportunities for Uzbekistan market

INSERT INTO opportunity_signals (product_name, category, demand_score, competition_score, sources, signal_text, confidence)
SELECT * FROM (VALUES
    ('Power station (katta quvvatli)', 'Elektronika', 85, 30, ARRAY['Uzum analysis', 'Web search'], 'O''zbekistonda katta quvvatli power stationlar yetishmaydi, faqat 2-3 seller bor', 0.7),
    ('Mini printer (termal)', 'Elektronika', 70, 40, ARRAY['Uzum analysis'], 'Kichik biznes uchun termal printerlar talab yuqori, lekin sifatli variantlar kam', 0.6),
    ('Elektro velosiped', 'Transport', 80, 35, ARRAY['Web search', 'Telegram groups'], 'Elektro velosiped importi o''sib bormoqda, lekin narxlar juda yuqori', 0.65),
    ('LED grow light (o''simlik chirog''i)', 'Qishloq xojaligi', 75, 20, ARRAY['Web search'], 'Issiqxonalar uchun LED grow light kerak, hali hech kim olib kelmayapti', 0.55),
    ('Power bank 50000mAh', 'Elektronika', 65, 50, ARRAY['Uzum analysis'], 'Katta power banklar bor lekin sifatsiz, sifatli variantlar yetishmaydi', 0.6),
    ('Smart watch (byudjet)', 'Elektronika', 90, 70, ARRAY['Uzum analysis'], 'Arzon smart watchlar juda ko''p, raqobat yuqori', 0.5),
    ('Solar panel (katta)', 'Energiya', 80, 25, ARRAY['Web search', 'Telegram groups'], 'Quyosh panellari talabi o''smoqda, lekin faqat 1-2 importyor bor', 0.7)
) AS seed_data
WHERE NOT EXISTS (SELECT 1 FROM opportunity_signals WHERE product_name = seed_data.column1);
