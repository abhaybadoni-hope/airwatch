# AirWatch — Real-Time Air Quality Tracking & Alert System

AirWatch polls live air-quality data for subscribed cities, stores the history, charts it on a dashboard, and pushes a Telegram alert the moment pollution crosses a threshold — sending exactly one alert per crossing instead of spamming while the air stays bad.

**Live demo:** https://airwatch-production-58cb.up.railway.app
**Dashboard:** https://airwatch-production-58cb.up.railway.app/dashboard/
**API docs:** https://airwatch-production-58cb.up.railway.app/docs

> Replace the URLs above if your Railway domain changes. Add a dashboard screenshot here — see the "Screenshot" note near the bottom.

---

## What it does

- Polls the OpenWeatherMap Air Pollution API on a schedule for each subscribed city
- Stores every reading (AQI, PM2.5, PM10, timestamp) in PostgreSQL as time-series data
- Serves current readings, historical data, and city subscriptions over a REST API
- Renders a live dashboard charting the last 24 hours of PM2.5
- Sends Telegram alerts on threshold crossings, and a recovery message when air improves
- Caches readings in Redis so multiple subscribers to the same city share one API call
- Recovers automatically from transient API failures with retry + exponential backoff

---

## Architecture

Two independent services run from a single repository:

```
                          ┌─────────────────────┐
                          │  Scheduler service  │
                          │     (main.py)       │
                          │  polls every 15 min │
                          └──────────┬──────────┘
                                     │
                fetch_aqi()          │
                                     ▼
   OpenWeatherMap  ◄──────►  ┌───────────────┐        ┌──────────────┐
   Air Pollution API        │   fetcher.py  │◄──────►│    Redis     │
                            │ (cache-aware, │  cache  │  (15-min TTL)│
                            │  retry/backoff)│        └──────────────┘
                             └───────┬───────┘
                                     │ save_reading()
                                     ▼
                            ┌──────────────────┐
                            │    PostgreSQL    │
                            │ readings /       │
                            │ alert_state /    │
                            │ subscriptions    │
                            └────────┬─────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    │                                  │
                    ▼                                  ▼
          ┌───────────────────┐            ┌──────────────────────┐
          │   API service     │            │  Telegram (notifier) │
          │    (api.py)       │            │  threshold alerts    │
          │  FastAPI + docs   │            └──────────────────────┘
          │  serves dashboard │
          └─────────┬─────────┘
                    │
                    ▼
              Web dashboard
             (Chart.js, /dashboard)
```

**Why two services?** The web server (serves requests) and the background poller (runs a schedule) are different workloads with different failure modes. Splitting them means the scheduler can crash and restart without taking the API — and the live dashboard — down with it. They share the same PostgreSQL and Redis instances.

---

## Tech stack

| Layer            | Choice                     | Why                                                        |
|------------------|----------------------------|------------------------------------------------------------|
| Language         | Python 3.12                | Fast iteration; strong ecosystem for APIs and scheduling   |
| API framework    | FastAPI                    | Auto-generated interactive docs, built-in validation       |
| Scheduler        | APScheduler                | Simple in-process interval scheduling                      |
| Database         | PostgreSQL                 | Real time-series storage with proper date types            |
| Cache            | Redis                      | Shared cache across subscribers; TTL-based expiry          |
| Retries          | tenacity                   | Declarative retry with exponential backoff                 |
| Notifications    | Telegram Bot API           | Free, instant push to phone                                |
| Frontend         | Chart.js                   | Lightweight charting, no build step                        |
| Containerization | Docker                     | Reproducible builds; one image runs anywhere               |
| Hosting          | Railway                    | Multi-service deploys, managed Postgres and Redis          |

---

## Key engineering decisions

**Deduplicated alerts (state transitions, not levels).** A naive threshold check fires an alert on every poll while pollution stays high — 20+ identical messages over a few hours. AirWatch tracks each city's alert state in the database and only notifies on a *transition*: crossing from safe into unhealthy (one alert), then staying silent until it drops back and crosses again. A recovery message fires on the downward crossing.

**Redis caching to cut redundant API calls.** Multiple subscribers to the same city previously meant multiple identical calls to the external API each cycle. Readings are now cached in Redis keyed by coordinates with a 15-minute TTL, so all subscribers to a city share a single upstream call — cutting redundant external API calls by roughly **[FILL IN — e.g. 75%]** in the multi-subscriber case.

> Update that percentage to whatever you can defend. Reasoning template: N cities × M subscribers polling every cycle = N×M calls without cache vs N calls with cache. Example: 5 cities × 4 subscribers = 20 calls → 5 calls = 75% reduction.

**Resilience to upstream failure.** The external API and network are treated as unreliable. Fetches retry up to 3 times with exponential backoff (2s → 4s → up to 10s) on network errors only, and a request timeout prevents a hung connection from freezing the scheduler. If all retries fail, the scheduler's own error handling logs it and moves on — one failed city never kills the polling loop. (Verified in production: a transient Redis outage was logged and the scheduler kept running.)

**Environment-driven config.** Database and Redis connection details come from environment variables, with sensible localhost fallbacks. The identical codebase runs locally against local services and in the cloud against managed ones, with no code changes — only configuration differs.

---

## API reference

| Method | Endpoint                         | Description                                    |
|--------|----------------------------------|------------------------------------------------|
| GET    | `/`                              | Health check                                   |
| GET    | `/cities/{city}/current`         | Latest reading for a city                      |
| GET    | `/cities/{city}/history?hours=N` | Readings from the last N hours (default 24)    |
| POST   | `/subscriptions`                 | Subscribe a city (name, lat, lon, threshold)   |
| GET    | `/subscriptions`                 | List all subscriptions                         |
| GET    | `/docs`                          | Interactive API documentation                  |

---

## Running locally

**Prerequisites:** Python 3.12+, PostgreSQL, Redis (or a Redis-compatible server such as Memurai on Windows).

1. Clone and set up a virtual environment:
   ```bash
   git clone https://github.com/abhaybadoni-hope/airwatch.git
   cd airwatch
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Create a `.env` file (see `.env.example` for the full list of keys):
   ```
   OPENWEATHER_API_KEY=your_key
   TELEGRAM_BOT_TOKEN=your_token
   TELEGRAM_CHAT_ID=your_chat_id
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=airwatch
   DB_USER=postgres
   DB_PASSWORD=your_password
   ```

3. Create the database (in `psql`):
   ```sql
   CREATE DATABASE airwatch;
   ```

4. Initialise the tables:
   ```bash
   python -c "from database import init_db, init_alert_state, init_subscriptions; init_db(); init_alert_state(); init_subscriptions()"
   ```

5. Run the two processes in separate terminals:
   ```bash
   # Terminal 1 — the API + dashboard
   uvicorn api:app --reload

   # Terminal 2 — the poller
   python main.py
   ```

6. Open the dashboard at `http://127.0.0.1:8000/dashboard/`.

---

## Deployment (Railway)

Deployed as two services from one repository, plus managed Postgres and Redis:

- **API service** — start command `uvicorn api:app --host 0.0.0.0 --port 8000`, public domain generated
- **Scheduler service** — start command `python main.py`, no public domain (background worker)
- Both reference the managed database URLs via Railway's variable references (`${{Postgres.DATABASE_URL}}`, `${{Redis.REDIS_URL}}`)
- The `Dockerfile` builds the image; `railway.json` pins the Dockerfile builder, while each service sets its own start command

---

## Project structure

```
airwatch/
├── api.py              # FastAPI app: endpoints + dashboard mount + startup table init
├── main.py             # Scheduler: polls all cities, runs alert logic
├── fetcher.py          # Cache-aware, retrying AQI fetch
├── database.py         # PostgreSQL access layer (connection, tables, queries)
├── notifier.py         # Telegram alert sender
├── static/
│   └── index.html      # Chart.js dashboard
├── Dockerfile
├── docker-compose.yml  # Local full-stack (app + Postgres + Redis)
├── railway.json        # Railway build config
├── requirements.txt
└── .env.example
```

---

## Screenshot

Add a screenshot of the live dashboard here so reviewers see it without running anything:

```markdown
![AirWatch dashboard](docs/dashboard.png)
```

Save your dashboard screenshot into a `docs/` folder in the repo as `dashboard.png`, then commit it.

---

## Possible extensions

- Multiple cities on the dashboard with a selector
- Configurable alert thresholds per subscription (schema already supports it)
- Historical trends beyond 24 hours (daily/weekly rollups)
- Email alerts alongside Telegram
- A proper lifespan handler in place of the deprecated `on_event("startup")`
