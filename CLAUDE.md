# CLAUDE.md

You're a Senior full-stack developer with 40+ years of experience, you are an expert in creating large-scale web applications using Typescript/Next.js , Python and other popular libraries. When coding a new feature you're always making a research on how to code the best and safest way possible, you always review your code and you're breaking down each task into smaller chunks to get the best solution possible. You're using the ask the user questions tool effectively to make sure you have all details possible to develop and create a good working feature/app/website and etc.

## Project

AlexDrive — car dealer website for a Korean used-car market. Scrapes carmanager.co.kr listings, translates Korean UI to Russian, and presents them with a dark-themed frontend.

## Architecture

```
Browser → alexdriveapp (Next.js :3000) → alexdrivebackend (FastAPI :3001) → carmanager.co.kr (via proxy)
```

**alexdrivebackend/** — FastAPI (Python) server handling all scraping, authentication, HTML parsing, and caching. Uses httpx for HTTP requests, beautifulsoup4 for parsing, pydantic-settings for config. Persistent process keeps module-level session/filter caches alive.

**alexdriveapp/** — Next.js 16 (App Router) frontend. Pure presentation layer: fetches JSON from backend, renders UI, translates Korean→Russian client-side.

**Root package.json** — Uses `concurrently` to orchestrate both packages. No formal monorepo tooling.

## Commands

### Run both (from root)

```bash
npm run dev          # starts backend (:3001) + frontend (:3000) via concurrently
npm run install:all  # installs frontend deps
```

### Backend (from alexdrivebackend/)

```bash
python -m uvicorn app.main:app --reload          # dev with hot-reload
python app/main.py                                # run directly
```

Python venv lives at `alexdrivebackend/.venv/`. Install deps: `pip install -r requirements.txt` or `pip install -e .`

### Frontend (from alexdriveapp/)

```bash
npm run dev    # next dev
npm run build  # next build
npm start      # next start
npm run lint   # eslint (no auto-fix)
```

Backend tests: `cd alexdrivebackend && pytest -v` (57 tests, pytest + pytest-asyncio + respx).

## Environment Variables

### Backend (.env)

- `CARMANAGER_USERNAME` / `CARMANAGER_PASSWORD` — required, carmanager.co.kr credentials
- `PROXY_URL` — optional HTTP proxy for outbound requests
- `PORT` — default 3001
- `CORS_ORIGINS` — comma-separated, default "http://localhost:3000"

### Frontend (.env.local)

- `BACKEND_URL` — server-side backend URL (default http://localhost:3001)
- `NEXT_PUBLIC_BACKEND_URL` — client-side backend URL

## Key Conventions

- **Car IDs contain `/` and `=`** (base64-encoded). The detail endpoint uses query params (`GET /api/cars/detail?id=xxx`), not path params, to avoid routing issues.
- **Filter JS files are fetched sequentially** in the backend to avoid proxy connection limits. Do not parallelize them.
- **Session cookies have ~10-min TTL** (server EndDate). Smart validation before re-login, 4-min keepalive, disk persistence, 3-retry login logic. Auto re-login is transparent — no user-visible errors.
- **Filter cache has 24h TTL** with thundering-herd protection (shared in-flight Promise).
- **Translations** live in `alexdriveapp/src/lib/translations.ts` (~1830 lines). The `translateSmartly()` function converts Korean text to Russian with brand/model name awareness.
- **Dark theme** with Classic Gold (#D4AF37) accent. Colors defined as CSS custom properties in `globals.css`.
- **Fonts:** Jost (headings), Inter (body), both with cyrillic subset.
- **Russian UI** — all user-facing text is in Russian.
- **Client-side debouncing** — 500ms delay on filter param changes before fetching car listings.
- **ISR on detail pages** — 10-minute revalidation (`revalidate=600`).

## Backend Request Flow

1. `routes/` receive HTTP request via FastAPI router, extract params
2. `services/carmanager.py` orchestrates business logic (filter fetch, listing search, detail fetch)
3. `services/client.py` makes authenticated HTTP requests with auto-retry on 302/401
4. `services/session.py` manages login, cookie caching, httpx client
5. `parsers/` extract structured data from HTML/JS responses using beautifulsoup4

## Frontend Data Flow

- Catalog page (`page.tsx`): client component, fetches `/api/filters` once + `/api/cars` on filter changes
- Detail page (`car/[id]/page.tsx`): server component with ISR, fetches `/api/cars/detail?id=<encoded_id>`
- `lib/api.ts`: `backendFetch()` helper — constructs URL, adds `/api` prefix, 30s timeout
- No state management library — React hooks only (useState, useEffect, useCallback)
