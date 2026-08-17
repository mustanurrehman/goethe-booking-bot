# AGENTS.md — Goethe Booking Bot

## Project Overview
Selenium bot that auto-books Goethe Institut exam slots for Pakistan region. Web control panel (Flask) + dashboard frontend. Students loaded from Google Sheets or SQLite DB.

## Quick Commands
```bash
# Deploy backend to Railway (auto-deploys from GitHub main; manual)
railway up -d C:\Users\brosp\Downloads\goethe-bot

# Deploy frontend to Netlify
npx netlify deploy --prod --dir=frontend --site 0d638a6c-008a-402b-b8a9-7f6a4541980e
# or from project dir:
npx netlify deploy --prod --dir=frontend

# Set Railway env var
railway variable set KEY=VALUE

# Check Railway logs
railway logs --service goethe-booking-bot -n 100

# Trigger Railway redeploy
railway service redeploy --yes
# or: git commit --allow-empty -m "redeploy" && git push origin main
```

## URLs
| Service | URL |
|---------|-----|
| Frontend | https://snazzy-kleicha-1d59fd.netlify.app |
| Backend | https://goethe-booking-bot-production-21af.up.railway.app |
| GitHub | https://github.com/abeermeer/goethe-booking-bot (public, new home) |
| Old GitHub (fork) | https://github.com/hamzabot655/goethe-booking-bot (private fork, may be stale) |

## Credentials
- **Auth login**: AUTH_EMAIL=`hamzarafiq655@gmail.com` / AUTH_PASSWORD=`Hamza@123` (Railway env vars)
- **ScrapingBee API**: RQS2P8K2SVGO15HH5X9C17P006KS9RCULD3M3X4URWZ7XEPVFU4GMG5B3U6DK2470PUG0XREZKVKSN3P (set via `SCRAPINGBEE_API_KEY` env var)
- **Google Sheet ID**: `1C7VD_52VnGmJqYSQGtdNzBZGekvCRHWUrdZCgTvvhAY` (`GOOGLE_SHEET_ID` env var)
- **Google Service Account**: Base64 in `GOOGLE_SERVICE_ACCOUNT_B64` env var

## Railway Project
- **Project**: hospitable-heart (ID: 520adb72-b1f4-4021-8c4b-21ca81f8a901)
- **Service**: goethe-booking-bot (ID: f568e242-4d2a-4b44-8205-07899abfbd26)
- **Environment**: production (ID: 20945f76-1cfa-4e38-b50b-a5cb8d5f47cd)
- **Region**: sfo
- **Databases**: Postgres-ZHgW, Postgres, Postgres-3Fwo (unused by the main app; uses SQLite)

## File Map
| File | Purpose |
|------|---------|
| `webapp.py` | Flask backend — API endpoints, CORS, auth, bot control |
| `booking_helper.py` | Core Selenium bot — login, 5-step wizard, smart_retry, polling |
| `goethe_scraper.py` | Pakistan exam schedule scraper — ScrapingBee → curl_cffi → Playwright → fallback |
| `google_sheets.py` | Google Sheets integration — read/write students, auto-fill dates, update schedule tab |
| `db.py` | SQLite DB — students, logs, settings tables |
| `frontend/index.html` | Single-page dashboard — 6 sections (Dashboard, Controls, Schedule, Students, Logs, Settings) |
| `Dockerfile` | Railway deployment — Python + Chrome + Playwright |
| `pk_fallback.json` | Offline exam schedule data (10 entries, Jul-Oct 2026) |
| `netlify.toml` | Netlify config — publishes `frontend/` directory |

## Architecture

### API Endpoints (all prefixed with `/api`)
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/login` | POST | No | Returns JWT token |
| `/students` | GET | Yes | List all students (DB + sheet + config merged) |
| `/students` | POST | Yes | Add student to DB + Google Sheet |
| `/students/<id>` | DELETE | Yes | Delete DB student (negative id = sheet-only, returns 400) |
| `/goethe-schedule` | GET | Yes | Pakistan exam schedule (`?refresh=1` for live, `?level=A1` to filter) |
| `/sheets/update-schedule` | POST | Yes | Update Google Sheets Schedule tab from Goethe data |
| `/sheets/auto-fill` | POST | Yes | Auto-fill booking_datetime for empty students |
| `/schedule` | GET | Yes | Load students from Google Sheet |
| `/start` | POST | Yes | Start bot on all students |
| `/stop` | POST | Yes | Stop bot |
| `/config` | GET/POST | Yes | Bot configuration |
| `/live-status` | GET | Yes | Live booking status per student |
| `/heartbeat` | GET | Yes | Dead man switch heartbeat |

### Student ID System
- **DB students**: positive `id` (SQLite auto-increment)
- **Sheet/config students**: negative `id` (e.g., -1, -2) assigned in `_get_loaded_students()`
- Delete button visible for all, but sheet-only delete returns error msg

### Bot Flow
1. Load students (DB + Sheet merged via `_get_loaded_students()`)
2. Each student gets own `threading.Thread` + own Chrome browser (parallel)
3. For each student: navigate to level URL → wait/poll for booking button → CAS login → 5-step wizard
4. Wizard steps: Personal Data 1 → Personal Data 2 → Payment (Invoice) → Promo Code → Review & Confirm
5. Status pushed via WebSocket to frontend live dashboard

### Schedule Fetch Chain
1. **ScrapingBee** (premium_proxy=true) — primary, ~15s per 3 levels parallel
2. **curl_cffi** (chrome131 impersonate) — fallback if ScrapingBee fails
3. **Playwright** (headless Chromium) — fallback if curl_cffi unavailable
4. **pk_fallback.json** — last resort offline data

### Google Sheets 429 Handling
- `_retry_gsheet()`: 5s → 10s → 20s → 40s exponential backoff
- 15s TTL in-memory cache on `load_sheet_data()` to reduce read frequency
- `strict=False` on data validation dropdown to avoid red dot on existing values

## Common Issues

### "Delete failed: Unexpected token '<'"
**Cause**: Student missing `id` field → URL `/api/students/undefined` → HTML 404
**Fix**: All students now get an id (positive for DB, negative for sheet/config). Already fixed.

### "Quota exceeded for quota metric 'Read requests'"
**Cause**: Google Sheets 60 reads/min/user limit exceeded
**Fix**: Retry with backoff + 15s cache. If persistent, wait 1 min.

### Schedule returns 0 entries
**Cause**: ScrapingBee monthly limit, Playwright browsers not installed, or Goethe API blocking
**Fix**: Fallback to `pk_fallback.json`. If ScrapingBee exhausted, replace API key.

### "cannot connect to chrome" / "ChromeDriver only supports Chrome version 152" (local + uc)
**Cause**: `create_driver()` now pins both the undetected-chromedriver and standard-selenium paths to a locally cached chromedriver that matches the installed Chrome build (`_find_local_driver()`). Older code let uc download the latest driver, which only supports newer Chrome, and reused a mutated ChromeOptions object across retries (uc bug "you cannot reuse the ChromeOptions object").
**Fix (already applied)**: `booking_helper.create_driver()` → `uc.Chrome(..., driver_executable_path=<cached driver>, version_main=int)` with a fresh `_build_options()` per attempt. The full-version cache lives under `~/.wdm/drivers/chromedriver/win64/<full_version>/`. If uc still fails, it falls back to standard Selenium with the same pinned driver. Verify with `python -c "import booking_helper as b; d=b.create_driver(True, __import__('logging').getLogger('x')); d.quit()"`.

### Bot timing — "5-10 min per student?"
**Reality**: ~1.5-2 min per student when booking open. Parallel for multiple students (same total time).

## Deployment Notes
- Railway auto-deploys from GitHub `main` branch pushes
- Railway env vars are picked up on next deploy (not hot-reloaded)
- Netlify deploys are manual via CLI (`npx netlify deploy --prod --dir=frontend`)
- Frontend is pure HTML/CSS/JS — no build step needed
- Backend SQLite DB resets on each Railway deploy (data persists only in Google Sheet or GitHub config)

## Todo / Known Gaps
- [ ] India adaptation: change `/ins/pk/` to `/ins/in/`, add `undetected-chromedriver`, Indian proxies
- [ ] Google Sheets append_student doesn't retry on 429
- [ ] Config file students lack DB ids (can't be deleted via API)
- [ ] No automated tests for the booking flow (only scrapers and helpers tested)
