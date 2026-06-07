# Trade Price Service — To'liq Loyiha Holati

## 1. LOYIHA HAQIDA

**Trade Price Service** — O'zbekistonga import qilinadigan mahsulotlarning to'liq narxini hisoblab beruvchi AI-agent tizimi.

Agent foydalanuvchining savoliga qarab:
- Mahsulot narxini topadi (AliExpress, Alibaba, eBay, Rakuten)
- Import bojini hisoblaydi (HS kod bo'yicha)
- Yuk tashish narxini qo'shadi (freight corridors)
- Sertifikat va soliqlarni hisobga oladi
- Yakuniy "to'liq yetkazib berish" narxini chiqaradi

---

## 2. BOSHLANG'ICH HOLAT (Nimadan boshladik)

Loyiha quyidagi holatda edi:
- **Baza**: V39-V42 migrations yuklangan (price cache, freight fix, RPC grants)
- **Agent**: 1 faza — faqat bitta agent barcha ishni qilardi (ko'p xatolar bilan)
- **Frontend**: Streamlit ilova bor
- **API**: Ba'zi endpointlar bor

### Mavjud jadvallar:
- `price_cached_results` — narx kesh jadvali
- `currency_rates` — valyuta kurslari
- Boshqa V39-V42 dagi jadvallar

### Muammolar:
- Agent import qoidalarini bilmas edi
- Freight ma'lumotlari to'liq emas edi
- Davlatlar ma'lumotnomasi yo'q edi
- HS kod tahlili yo'q edi
- Sertifikat talablari yo'q edi

---

## 3. QILGAN ISHLARIMIZ (To'liq ro'yxat)

### 3.1. Agent Arxitekturasi (V46)

**Fayllar:**
- `app/agent/prompts.py` — barcha 4 agent promptlari
- `app/agent/engine.py` — 3-fazali flow
- `app/agent/tools.py` — 11 ta tool

**Agent Tuzilishi:**
```
Router (savolni tahlil qiladi)
  │
  ├── Discovery (ma'lumot qidiradi — web search, web fetch, Apify, eBay)
  │
  ├── Trade Analyst (import hisob-kitobi — HS kod, boj, freight, sertifikat)
  │
  └── Decision (yakuniy narx va tavsiya)
```

**Router Agent:**
- Savolni tahlil qiladi
- Tilni aniqlaydi (uz/ru/en)
- Mahsulot turini aniqlaydi
- Discovery agentga yo'naltiradi

**Discovery Agent:**
- Web search orqali mahsulot narxlarini qidiradi
- Apify (AliExpress) orqali narxlarni oladi
- eBay orqali narxlarni tekshiradi
- Web fetch orqali ma'lumotlarni yig'adi

**Trade Analyst Agent:**
- HS kodni aniqlaydi
- Import bojini hisoblaydi
- VAT (QQS) hisoblaydi
- Freight narxini qo'shadi
- Sertifikat talablarini tekshiradi

**Decision Agent:**
- Barcha ma'lumotlarni jamlaydi
- Yakuniy narxni chiqaradi
- Tavsiya beradi

**11 ta Tool:**
1. `web_search` — internet qidirish
2. `web_fetch` — URL dan ma'lumot olish
3. `apify_get_aliexpress_prices` — AliExpress narxlari
4. `ebay_search` — eBay narxlari
5. `get_hs_code_info` — HS kod ma'lumoti
6. `get_duty_rate` — boj stavkasi
7. `get_freight_cost` — yuk tashish narxi
8. `get_certification_requirements` — sertifikat talablari
9. `get_exchange_rate` — valyuta kursi
10. `calculate_total_landed_cost` — to'liq narx hisobi
11. `get_trade_agreement` — savdo kelishuvi

### 3.2. V43 — CN Product Catalog

**Fayl:** `20260610_v43_cn_product_catalog.sql`

**Yangilangan:** Xitoy mahsulot katalogi
- 6 ta elektronika kategoriyasi (LED lampalar, solar panellar, kabellar, transformatorlar, batareyalar)
- 50+ mahsulot
- To'liq specifikatsiyalar bilan
- Narx diapazonlari (FOB Shenzhen)

### 3.3. V44 — UZ Product Catalog

**Fayl:** `20260611_v44_uz_product_catalog.sql`

**Yangilangan:** O'zbekiston mahsulot katalogi
- Sanoat uskunalari, qurilish materiallari, oziq-ovqat, to'qimachilik
- 80+ mahsulot
- O'zbekiston bozor narxlari

### 3.4. V45 — Product Catalog

**Fayl:** `20260612_v45_product_catalog.sql`

**Yangilangan:** Laptop katalogi
- `lap_product_catalog` jadvali
- 30+ laptop modeli
- To'liq texnik xususiyatlar

### 3.5. V46 — Agent Router

**Fayl:** `20260613_v46_agent_router.sql`

**Yangi jadvallar:**
- `agent_router` — agent routing logikasi
- `opportunity_signals` — imkoniyat signallari

### 3.6. V47 — Countries + Exchange Rates

**Fayl:** `20260614_v47_countries.sql`

**Yangi jadvallar:**
- `countries` — davlatlar ma'lumotnomasi (25 ta asosiy)
- `uzs_exchange_rates` — UZS valyuta kurslari

**Ma'lumotlar:**
- O'zbekiston + 25 ta asosiy savdo hamkor
- 3 davr uchun valyuta kurslari (2025 may, 2025 noyabr, 2026 iyun)

### 3.7. V48 — Trade Rules

**Fayl:** `20260615_v48_trade_rules.sql`

**Yangi jadvallar:**
- `trade_agreements` — savdo kelishuvlari
- `certification_requirements` — sertifikat talablari

**Ma'lumotlar:**
- 12 ta savdo kelishuvi (EAEU, CIS_FTA, Turkiya PTA, Turkmaniston FTA)
- 78 ta sertifikat talabi (asosiy HS boblar uchun)

### 3.8. V49 — Freight Corridors

**Fayl:** `20260616_v49_freight_corridors.sql`

**Yangi jadval:** `freight_corridors`

**Ma'lumotlar:**
- 15 ta asosiy davlatdan UZ ga yo'nalishlar
- 3 transport turi (rail, road, air, sea)
- Narxlar: kg, container, CBM bo'yicha
- Yetkazish muddatlari

### 3.9. V50 — HS Code Reference

**Fayl:** `20260617_v50_hs_code_reference.sql`

**Yangi jadval:** `hs_code_reference`

**Ma'lumotlar:**
- 41 ta asosiy HS bob
- O'zbekiston import statistikasi
- VAT stavkalari
- Freight faktorlari
- Mahalliy ishlab chiqarish ma'lumoti

### 3.10. V51 — Complete Countries (EXPANSION)

**Fayl:** `20260618_v51_all_countries.sql`

**O'zgarish:** `countries` jadvali kengaytirildi
- **168 davlat** (barcha UN a'zolari + hududlar)
- 7 region: Central Asia, East Asia, Southeast Asia, South Asia, Middle East, Caucasus, Europe, North America, South America, Africa, Oceania
- Savdo bloklari: EAEU, EU, CIS_FTA
- Import ulushi (%)
- Valyuta nomlari

### 3.11. V52 — Complete HS Codes (EXPANSION)

**Fayl:** `20260619_v52_all_hs_codes.sql`

**O'zgarish:** `hs_code_reference` kengaytirildi
- **Barcha 97 HS bob** to'liq
- Barcha 21 seksiya
- O'zbek, ingliz, rus tillarida nomlar
- VAT stavkalari (12% / 20%)
- Freight faktorlari
- Mahalliy ishlab chiqarish ma'lumoti

### 3.12. V53 — Complete Freight Corridors (EXPANSION)

**Fayl:** `20260620_v53_all_freight_corridors.sql`

**O'zgarish:** `freight_corridors` kengaytirildi
- **119 ta yo'nalish**
- Barcha muhim savdo hamkorlar:
  - EU: ES, NL, BE, AT, SE, DK, FI, NO, HU, RO, BG, GR
  - Caucasus: AZ, GE
  - Middle East: SA, IQ, JO, IL, KW, QA
  - South Asia: PK, BD
  - Southeast Asia: TH, VN, MY, SG, ID, PH
  - East Asia: TW, HK
  - Americas: CA, BR, AR, MX
  - Africa: ZA, EG, NG, MA, KE
  - Oceania: AU, NZ

### 3.13. V54 — Complete Certifications (EXPANSION)

**Fayl:** `20260621_v54_all_certifications.sql`

**O'zgarish:** `certification_requirements` kengaytirildi
- **118 ta sertifikat talabi**
- Barcha HS boblar uchun:
  - SanEpid — sanitariya sertifikati
  - CoC — muvofiqlik sertifikati
  - Veterinary — veterinariya sertifikati
  - Phytosanitary — fitosanitar sertifikati
  - Special Permit — maxsus ruxsatnoma
- Narxlar (0-3000 USD)
- Muddati kunlarda
- Test kunlari

### 3.14. V55 — CBU API Integration (EXPANSION)

**Fayl:** `20260622_v55_cbu_api.sql`

**Funksiyalar:**
- `sync_cbu_exchange_rates()` — CBU API dan valyuta kurslarini yuklaydi
- `cleanup_old_exchange_rates()` — eski kurslarni tozalaydi (90 kundan eski)
- `http_get` — pg_net extension orqali HTTP so'rov

---

## 4. HOZIRGI BAZA HOLATI

```
V39  ✅ price_cached_results
V40  ✅ rail_freight fix
V41  ✅ price_original
V42  ✅ agent_fix_rpc_grants
V43  ✅ cn_product_catalog
V44  ✅ uz_product_catalog  
V45  ✅ lap_product_catalog
V46  ✅ agent_router + opportunity_signals
V47  ✅ countries + uzs_exchange_rates
V48  ✅ trade_agreements + certification_requirements
V49  ✅ freight_corridors
V50  ✅ hs_code_reference
V51  ✅ ALL countries (168)
V52  ✅ ALL HS codes (97)
V53  ✅ ALL freight corridors (119)
V54  ✅ ALL certifications (118)
V55  ✅ CBU API functions
```

**Jami: 17 ta migratsiya (V39-V55)**

---

## 5. MUHIM FAKT VA RAQAMLAR

| Ko'rsatkich | Qiymat |
|---|---|
| Migratsiyalar soni | 17 ta (V39-V55) |
| Davlatlar | 168 ta |
| HS kod boblar | 97 ta (to'liq) |
| Freight yo'nalishlar | 119 ta |
| Sertifikat talablari | 118 ta |
| Savdo kelishuvlari | 12 ta |
| Valyuta kurslari | 28 ta |
| Agentlar | 4 ta (Router, Discovery, Trade Analyst, Decision) |
| Tool'lar | 11 ta |
| Python fayllar | `engine.py`, `prompts.py`, `tools.py` |

---

## 6. SUPABASE CLOUD MA'LUMOTLARI

- **Project Ref:** `npwojqqeerenbvgkvnyd`
- **Region:** Seoul (ap-northeast-2)
- **URL:** `https://npwojqqeerenbvgkvnyd.supabase.co`
- **Pooler:** `aws-1-ap-northeast-2.pooler.supabase.com:5432`
- **Status:** Active, barcha migrations yuklangan

---

## 7. .ENV FAYLI TUZILISHI

```
SUPABASE_URL=https://npwojqqeerenbvgkvnyd.supabase.co
SUPABASE_SERVICE_KEY=<service_role_key>
SUPABASE_ANON_KEY=<anon_key>
APIFY_TOKEN=<apify_token>          # AliExpress ma'lumotlari uchun
OPENROUTER_API_KEY=<or_key>         # AI agent uchun
RAKUTEN_APP_ID=<rakuten_id>         # Yaponiya narxlari uchun
RAKUTEN_ACCESS_KEY=<rakuten_key>    # Yaponiya narxlari uchun
CSK_KEY=<csk_key>                   # Cohere/embedding
GOOGLE_API_KEY=<google_key>         # Google search
GITHUB_PAT=<github_pat>             # GitHub access
DEBUG=true
```

---

## 8. MUHIM KOD STRUKTURASI

```
app/
├── agent/
│   ├── __init__.py
│   ├── engine.py          # 3-fazali agent flow (asosiy)
│   ├── prompts.py         # 4 agent promptlari
│   └── tools.py           # 11 ta tool
├── api.py                 # FastAPI endpointlar
├── supabase_client.py     # Supabase ulanish
├── config.py              # Sozlamalar
├── log.py                 # Logging
└── utils.py               # Yordamchi funksiyalar

supabase/
├── migrations/            # V39-V55 SQL fayllar
├── seed_cn_catalog.sql    # Xitoy katalogi
├── seed_uz_catalog.sql    # O'zbek katalogi
├── seed_laptops.sql       # Laptop katalogi
├── _pending/              # Qo'lda yuklanmagan SQL lar
└── .temp/                 # Supabase CLI temp

scripts/
├── seed_catalog.py        # Migration + seed yuklash skripti
└── train.py               # Training skripti

streamlit_app.py           # Frontend
```

---

## 9. KEYINGI IMLAR (AI NIMA QILISHI KERAK)

### 9.1. Mavjud vazifalar:

1. **Agentni test qilish**
   ```python
   from app.agent.engine import run_agent
   import asyncio
   result = asyncio.run(run_agent("laptop narxi qancha?", "uz"))
   print(result)
   ```

2. **Agar xatolik bo'lsa**, tekshirish:
   - `.env` da OPENROUTER_API_KEY to'g'ri yozilganmi?
   - `.env` da SUPABASE_SERVICE_KEY to'g'ri yozilganmi?
   - `supabase/v55_cbu_api.sql` da `http_get` funksiyasi ishlaydimi?

3. **Yangi HS kodlar qo'shish** kerak bo'lsa:
   - `hs_code_reference` jadvaliga INSERT
   - HS kod bo'yicha boj stavkalarini qo'shish

### 9.2. Rivojlantirish yo'nalishlari:

1. **CBU valyuta kurslarini avtomatik yangilash**
   - `sync_cbu_exchange_rates()` funksiyasini chaqirish uchun cron/Edge Function
   - Har kuni ertalab cbu.uz dan kurslarni yuklash

2. **Agent tool'larini kengaytirish**
   - Yangi marketplace'lar qo'shish (Amazon, Wildberries, Uzum)
   - Mahalliy bozor ma'lumotlari (Uzum, Olx)

3. **To'liq product catalog** (agar kerak bo'lsa)
   - Apify/AliExpress orqali real mahsulotlarni yuklash
   - `.env` da APIFY_TOKEN mavjud

4. **Import boj stavkalari ma'lumotnomasi**
   - Hozir agent HS kod orqali bojni hisoblaydi
   - To'liq boj ma'lumotnomasi qo'shish mumkin

5. **Frontendni yaxshilash**
   - Streamlit ilova UI/UX
   - Agent natijalarini vizuallashtirish

6. **Edge Functions**
   - CBU kurslarini yangilash uchun Supabase Edge Function
   - Webhook'lar

### 9.3. Diagnostika:

Agar agent ishlamasa:
1. `supabase migration list` — barcha migrations yuklanganmi?
2. `.env` da OPENROUTER_API_KEY bormi?
3. `python3 -c "from app.agent.engine import run_agent; import asyncio; print(asyncio.run(run_agent('test', 'uz')))"` — agent ishlaydimi?
4. `.env` da SUPABASE_SERVICE_KEY to'g'rimi?

---

## 10. MUHIM ESLATMALAR

- **Product catalog** (V43-V45) agent tomonidan emas, balki `supabase db push` orqali yuklandi
- **V51-V55** kengaytmalar qo'lda yaratildi va yuklandi
- **Agent** mahsulot narxlarini real vaqtda web search orqali topadi (pre-seed kerak emas)
- **Barcha ma'lumotnomalar** (davlatlar, HS, freight, sertifikat) to'liq
- **Seed_catalog.py** orqali SQL yuklash ishlamaydi (REST API /api/sql yo'q). Faqat `supabase db push` orqali ishlaydi.

---

*Hujjat oxiri. 2026-06-07.*
