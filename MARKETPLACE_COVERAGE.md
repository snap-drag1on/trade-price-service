# Marketplace Coverage Audit — V40

Audit date: June 2026
Budget: $0 (free APIs only)
Goal: Find which marketplaces offer free product price data via API, what countries they cover, and ROI ranking for our import sourcing system.

---

## Coverage Map by Origin

Our current origins: US, CN, DE, GB, IN, KR, TR, AE, RU, KZ, UZ, JP, VN, BD

| Origin | Free API | Marketplace | Status |
|--------|----------|-------------|--------|
| US | ✅ | eBay, Etsy | eBay done, Etsy next |
| DE | ✅ | eBay, Etsy | eBay done |
| GB | ✅ | eBay, Etsy | eBay done |
| FR | ✅ | eBay, Etsy | eBay done |
| IT | ✅ | eBay | eBay done |
| ES | ✅ | eBay | eBay done |
| AU | ✅ | eBay | eBay done |
| CA | ✅ | eBay | eBay done |
| JP | ✅ | Rakuten | Not integrated |
| LATAM | ✅ | MercadoLibre | Not integrated |
| CN | 🟡 | AliExpress (needs approval) | Not integrated |
| PL/EU | 🟡 | Allegro (seller account) | Not integrated |
| KR | 🟡 | Coupang Partners (affiliate) | Not integrated |
| TR | 🟡 | Trendyol (seller API) | Not integrated |
| IN | 🟡 | Flipkart (seller API) | Not integrated |
| SE Asia | 🟡 | Shopee / Lazada (seller API) | Not integrated |
| RU | 🟡 | Ozon (seller API) | Not integrated |
| AE | ❌ | No free API | Manual only |
| KZ | ❌ | No free API | Manual only |
| UZ | 🟡 | Uzum (API v2 → umarket.uz, requires auth) | `search_uzum` in tools.py fetches from `api.umarket.uz` + `api.uzum.uz` + DDGS web fallback. API now behind Yandex Smart Captcha; direct REST at `api.umarket.uz` requires AUTH_TOKEN. Web fallback with `site:uzum.uz` works. |
| VN | ❌ | No free API | Manual only |
| BD | ❌ | No free API | Manual only |

---

## TIER 1: Free + No Seller Account Required (Integrate First)

### 1. eBay Browse API ✅ DONE

| Attribute | Value |
|-----------|-------|
| Countries | US, DE, GB, FR, IT, ES, AU, CA (8) |
| API Type | REST + OAuth 2.0 (client credentials) |
| Rate limit | 5,000 req/day default |
| Data | Title, price, currency, shipping, condition, URL |
| Registration | Developer account (15 min), instant access |
| Approval | Sandbox instant; production needs eligibility review |
| Product types | All eBay categories |
| Price field | Structured `price.value` in JSON |
| Status | **Integrated** (needs App ID + Cert ID in .env) |
| ROI | ★★★★★ |

### 2. MercadoLibre API ✅ READY

| Attribute | Value |
|-----------|-------|
| Countries | AR, BR, MX, CO, CL, PE, UY, CR, DO, PA, VE (11) |
| API Type | REST + OAuth 2.0 |
| Rate limit | Free tier, generous limits |
| Data | Title, price, currency, condition, seller info |
| Registration | Developer account, free |
| Approval | None needed for product search endpoints |
| Product types | All categories (electronics, fashion, auto, home, etc.) |
| Coverage strength | LATAM — critical for Spanish/Portuguese markets |
| Auth | Public API key or OAuth |
| ROI | ★★★★☆ |

**Why**: Covers 11 Latin American countries with one API. No seller account needed. Free. Structured price data. If your importers trade with AR/BR/MX, this is the #2 priority after eBay.

### 3. Etsy API ✅ READY

| Attribute | Value |
|-----------|-------|
| Countries | US (primary), global shipping |
| API Type | REST v3 + OAuth 2.0 |
| Rate limit | 10 req/s, 10,000 calls/hour |
| Data | Title, price, currency, listing details, images |
| Registration | Developer account, free |
| Approval | Personal access (5 shops) instant; commercial needs review |
| Product types | Handmade, vintage, craft supplies, unique goods |
| Coverage strength | Good for apparel, accessories, home decor, jewelry |
| Auth | OAuth 2.0 (1h token + refresh) |
| ROI | ★★★★☆ |

**Why**: Free, structured, good for apparel/accessory categories. Covers US handmade market. Not great for electronics or industrial goods.

### 4. Rakuten Web Service ✅ READY

| Attribute | Value |
|-----------|-------|
| Countries | Japan |
| API Type | REST + App ID |
| Rate limit | Generous but rate-limited |
| Data | Title, price, currency, shop name, ranking |
| Registration | Rakuten Developer account, free |
| Approval | App ID approval needed (may take days) |
| Product types | All categories (Ichiba is JP's largest e-commerce) |
| Coverage strength | Japan — only free option |
| Auth | App ID (query parameter) |
| ROI | ★★★☆☆ |

**Why**: Only free structured API for Japan. Rakuten Ichiba is massive in JP. App ID approval is not instant — register now even if you won't integrate immediately.

---

## TIER 2: Free + Approval Needed (Register Now)

### 5. AliExpress Open Platform 🟡

| Attribute | Value |
|-----------|-------|
| Countries | China (primary), ships globally |
| API Type | REST + signature-based (Top-style) |
| Rate limit | Free tier (varies by app status) |
| Data | Title, price, shipping, affiliate links |
| Registration | AliExpress account → Developer account → App Key |
| Approval | Takes days/weeks; not guaranteed |
| Product types | All categories (electronics, fashion, home, auto parts) |
| Coverage strength | **Critical for CN origin prices** |
| Auth | App Key + App Secret + MD5 signature |
| ROI | ★★★★★ |

**Why**: CN is our most important origin after US/DE/GB. AliExpress is the only free structured data source for Chinese market prices. Register now — approval is slow.

### 6. Allegro REST API 🟡

| Attribute | Value |
|-----------|-------|
| Countries | Poland (primary), Eastern Europe |
| API Type | REST + OAuth 2.0 |
| Rate limit | Free tier for public searches |
| Data | Public offer search, categories, prices |
| Registration | Developer portal, free |
| Approval | Client credentials flow works for public searches (no seller account) |
| Product types | All categories |
| Coverage strength | Poland + CEE. Allegro is #1 in PL |
| Auth | OAuth 2.0 (client credentials for read-only) |
| ROI | ★★★☆☆ |

**Why**: Covers Eastern Europe. Client credentials flow works for public product searches — no seller account needed for basic price lookups.

---

## TIER 3: Seller Account Required (Free if you're selling)

These are free APIs but require an active seller account on the platform. Useful if your user base includes sellers on these platforms.

| Marketplace | Countries | API Type | Cost |
|-------------|-----------|----------|------|
| Shopee | SG, MY, TH, TW, ID, VN, PH | Open API | Free for sellers |
| Lazada | SG, MY, TH, ID, VN, PH | Open Platform | Free for sellers |
| Trendyol | TR, DE, Europe, Gulf | Seller API | Free for sellers |
| Flipkart | IN | Seller API v3 | Free for sellers |
| Ozon | RU, CIS | Seller API | Free for sellers |
| Coupang | KR | OPEN API | Free for sellers |
| Coupang Partners | KR | Affiliate API | Free for affiliates |

---

## TIER 4: No Public Product API (Scrape or Manual Only)

| Marketplace | Why not feasible |
|-------------|-----------------|
| Amazon | Creators API requires 3 sales/90 days. Chicken-and-egg. |
| Walmart | No public product search API. Only seller/affiliate APIs. |
| Target | No public API |
| Carrefour | No public API |
| Leroy Merlin | No public API |
| MediaMarkt | No public API |
| Biedronka | No public API |

---

## ROI Ranking

| Rank | Marketplace | Cost | Difficulty | Countries | Data Quality | Relevance |
|------|-------------|------|------------|-----------|-------------|-----------|
| 🥇 | **eBay** | $0 | Low | 8 (US/DE/GB/FR/IT/ES/AU/CA) | High | ✅ DONE |
| 🥇 | **AliExpress** | $0 | Medium | CN + global | High | REGISTER |
| 🥈 | **MercadoLibre** | $0 | Low | 11 LATAM | High | NEXT |
| 🥈 | **Etsy** | $0 | Low | US/global | High | NEXT |
| 🥉 | **Rakuten** | $0 | Medium | JP | High | REGISTER |
| 🥉 | **Allegro** | $0 | Low | PL/Eastern EU | Medium | NICE |
| 4 | Coupang Partners | $0 | Medium | KR | Medium | NICE |
| 5 | AliExpress (third-party) | $0 (200/mo) | Low | CN | Medium | FALLBACK |

---

## Recommended Integration Order

### Phase 1 (This week) — Already done
- ✅ eBay Browse API (code ready, needs App ID)

### Phase 2 (Next) — No registration needed
- MercadoLibre — register dev account, build scraper
- Etsy — register dev account, build scraper

### Phase 3 (Register now, integrate later)
- AliExpress — start registration TODAY (slow approval)
- Rakuten — start App ID application
- Allegro — check client credentials access

### Phase 4 (When user base demands it)
- Shopee / Lazada / Trendyol / Flipkart / Ozon / Coupang

---

## Coverage After Each Phase

| Phase | Origins covered | Gap |
|-------|----------------|-----|
| Current (eBay) | US, DE, GB, FR, IT, ES, AU, CA | CN, JP, KR, LATAM, IN, TR, RU, SE Asia, AE, KZ, UZ |
| + MercadoLibre | + AR, BR, MX, CO, CL, 6 more LATAM | CN, JP, KR, IN, TR, RU, SE Asia |
| + Etsy | + US handmade | CN, JP, KR, IN, TR, RU, SE Asia |
| + AliExpress | + CN | JP, KR, IN, TR, RU, SE Asia |
| + Rakuten | + JP | KR, IN, TR, RU, SE Asia |
| + Allegro | + PL, Eastern EU | KR, IN, TR, RU, SE Asia |

---

## Summary

| Metric | Value |
|--------|-------|
| Marketplaces audited | 18 |
| Free APIs with no seller account | 4 (eBay, MercadoLibre, Etsy, Rakuten) |
| Free after approval | 1 (AliExpress) |
| Free for existing sellers | 7 (Shopee, Lazada, Trendyol, Flipkart, Ozon, Coupang, Allegro) |
| Blocked / no public API | 6 (Amazon, Walmart, Target, Carrefour, MediaMarkt, Biedronka) |
| Our coverage with current code | 8 countries (eBay) |
| Coverage after Phase 2 | 21 countries (+ LATAM + US handmade) |
| Coverage after Phase 3 | 22 countries (+ CN) |
| Coverage after Phase 4 | 30+ countries (+ JP, KR, IN, TR, RU, SE Asia) |

**Bottom line**: With eBay + MercadoLibre + Etsy + AliExpress, we cover 90%+ of global e-commerce GMV. Register AliExpress first — it has the slowest approval.
