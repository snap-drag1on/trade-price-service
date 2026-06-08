# Trade AI V40.1 - Agent Knowledge Base

## Architecture
- **Backend**: Python FastAPI (Render)
- **Frontend**: Next.js 14 (Vercel)
- **Database**: Supabase (Postgres)
- **Task Store**: SQLite at `/tmp/trade_tasks/tasks.db` (multi-worker safe)

## Key Directories
```
app/
  agent/          # AI agent logic (engine, prompts, models)
  api.py          # FastAPI routes (query, health, price-check, compare)
  task_store.py   # SQLite task persistence
  supabase_client.py
  cache.py        # Query caching via Supabase RPC
  config.py       # Pydantic Settings from .env
main.py           # FastAPI app entry point
frontend/
  src/
    components/   # ChatView, AgentTimeline, OpportunityCard, SourcesBadge
    hooks/        # useChat (polling logic)
    lib/          # api.ts, types.ts
    app/          # page.tsx, layout.tsx
```

## Commands (Backend)
```bash
# Run locally
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
# Run with .venv
source .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
# Lint (ruff)
ruff check app/
# Type check
mypy app/
```

## Commands (Frontend)
```bash
cd frontend
npm install
npm run dev    # dev server on :3000
npm run build  # production build
```

## Key Endpoints (Render)
- `GET /api/v1/health` - Server health + Supabase status + task list
- `POST /api/v1/query` - Start agent query (returns task_id)
- `GET /api/v1/query/{task_id}` - Poll task status + phases + result

## Architecture Decisions
1. **3 AI Agents + 3 Services**: Router, Opportunity (optional), Decision are LLM-based; Market, Logistics, Trade Engine are pure data functions
2. **Parallel Services**: Market, Logistics, Trade Engine run via `asyncio.gather` (not sequential)
3. **7 Backend Phases → 4 UI Phases**: router, market_research, logistics, trade_engine, profit, decision (7) → mapped to 4 UI phases via UI_PHASE_MAP
4. **SQLite Task Store**: Multi-worker safe (Render uses gunicorn -w 4), file-level WAL locking
5. **Decision Agent has zero tools**: Receives pre-computed profit + confidence data, pure reasoning

## Important Notes
- Render free tier sleeps after 15min idle; first request takes ~30s cold start
- Supabase service key on Render may be outdated; set in Render dashboard env vars
- No Apify (free tier expired); web_search (DDGS) is primary data source
- Agent never guesses prices — only returns tool results
- 3 languages: uz (primary), ru, en
- When adding marketplaces, add to `app/agent/tools/` and parallel service list in engine.py

## URLS
- Backend: https://trade-price-service.onrender.com
- Supabase: https://npwojqqeerenbvgkvnyd.supabase.co
- GitHub: https://github.com/snap-drag1on/trade-price-service
