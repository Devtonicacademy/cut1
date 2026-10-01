# LivelyBorg AI: Honest Football Predictions (Lagos, Nigeria)

> Win/draw/loss predictions trained on 70,000+ real matches, tested against the bookmakers, explained in plain English, and recorded in a public, tamper-evident track record before every kickoff. 18+ only; predictions are probabilities, not guarantees.

## What it does
- **Real data, no key needed**: results, shots and odds for 22 leagues from football-data.co.uk (10 seasons), plus fixtures up to 14 days ahead from football-data.org (free key).
- **Trained model**: Elo, opponent-adjusted team ratings (Dixon-Coles), form, shots, rest, league table and head-to-head features feed a logistic model. When bookmaker odds exist, their consensus is an extra input. On 8,920 unseen matches it matches the bookmakers (50.3% correct, log loss 1.0034 vs 1.0042) and its percentages are well calibrated.
- **Reasons for every pick**: e.g. "Arsenal in better recent form (2.3 vs 1.6 points per game)".
- **Verified track record**: predictions lock within 36 hours of kickoff into a hash-chained ledger and are graded automatically; nothing can be edited unnoticed.
- **Honest slips**: accumulators built from predicted winners at real market prices, showing the true chance every pick wins; capped at 10 games.
- **Value bets only if proven**: shown only when a backtest found them profitable on two separate seasons (currently switched off).
- **Champions League (lower confidence)**: fixtures come from football-data.org (needs its free key). Clubs from different leagues are compared with domestic Elo plus hand-set league-strength offsets (`data/leagues.py`). This is not backtested, so these picks are labelled lower confidence and kept out of the track record and the accumulator builder. Clubs from leagues we hold no history for are skipped.
- **National teams** (Nations League, AFCON and its qualifiers, Asian Cup, friendlies): rated by Elo from 49,000 international results (free open dataset). Walk-forward tested on 4,671 matches since 2022: log loss 0.879 vs 1.051 for base rates, 60% correct, well calibrated. There are no bookmaker odds to compare against, and no squad or injury data. Fixtures need a free API-Football key (`API_FOOTBALL_KEY`); like the Champions League picks they stay out of the track record and the accumulator builder.
- **Responsible gambling**: 18+ confirmation, no booking-code or "guaranteed win" claims, support link in the footer.

## Repository structure
```
apps/api/app/
  data/        downloaders (football_data_uk.py, football_data_org.py), SQLite (db.py), team ratings (ratings.py), ingest.py
  ml/          features.py (pre-kickoff features), train.py (training + backtest), predictor.py (serving + reasons)
  tracking/    ledger.py (locked predictions, hash chain, grading)
  services/    fixture_service.py, accas_optimizer.py, ev_engine.py, kelly_engine.py, gemini_analyzer.py, tracker_service.py
  jobs.py      scheduler: refresh -> predict -> lock -> grade, weekly retrain
  main.py      FastAPI endpoints
apps/web/      Next.js app (match cards, slip builder, track record, accuracy page)
apps/bot/      Telegram message formatter
tests/         pytest suite on a synthetic database (no network)
```

## Configuration (`.env`)
| Variable | Purpose |
|---|---|
| `FOOTBALL_DATA_KEY` | football-data.org key: fixtures up to 14 days ahead (optional) |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | plain-English match explanations (optional; a template is used otherwise) |
| `ADMIN_TOKEN` | enables `POST /api/v1/jobs/run` and `/fixtures/refresh` (send it as the `X-Admin-Token` header); unset = disabled |
| `ALLOWED_ORIGINS` | comma-separated web origins allowed to call the API (default `http://localhost:3000,http://127.0.0.1:3000`) |
| `LIVELYBORG_AUTO_REFRESH`, `LIVELYBORG_CYCLE_HOURS` | scheduler on/off and interval (default on, every 3 hours) |
| `SITE_ADDRESS` | public domain for the Docker/Caddy deployment |

**Deploying:** see [DEPLOY.md](DEPLOY.md). It's one server with Docker Compose: Caddy (HTTPS), the web app, and the API with its database on a persistent volume. It can run for ₦0 on Oracle Cloud Always Free.

---
## 🛠️ Quickstart Instructions

### 1. Run Automated Test Suite
```bash
# Activate virtual environment
.\.venv\Scripts\python -m pytest -v tests
```

### 2. Load Real Football Data (free, no API key)
```bash
# Downloads 5 seasons of results (22 leagues) + upcoming fixtures from football-data.co.uk into data/livelyborg.db
.\.venv\Scripts\python -m apps.api.app.data.ingest --seasons 5
```
- Completed seasons are cached in `data/raw/`; later runs only re-download the current season.
- The API refreshes the current season and fixtures automatically on startup when data is older than 6 hours (`LIVELYBORG_AUTO_REFRESH=0` disables this), and on `POST /api/v1/fixtures/refresh`.
- Data status: `http://127.0.0.1:8000/api/v1/data/status`
- Team ratings are learned from these results (`apps/api/app/data/ratings.py`); tests use a synthetic database (`tests/conftest.py`) and never touch the network.

#### Train the prediction model
```bash
# Builds pre-kickoff features (Elo, team ratings, form, shots, rest, table, H2H), trains on past seasons,
# tests on the last 1.5 seasons against bookmaker odds, then saves data/models/match_model.joblib
.\.venv\Scripts\python -m apps.api.app.ml.train
```
- Backtest report: `data/models/report.json`, or `http://127.0.0.1:8000/api/v1/model/report` while the API runs.
- Value bets are only shown if a threshold was profitable on both the validation and test seasons (`value_policy` in the report).
- Without a trained model the API falls back to Dixon-Coles ratings.
- Two models are trained: **with_market** (football features + bookmaker consensus, used when a fixture has odds) and **football_only** (fixtures listed before bookmakers price them).

#### Automation & verified track record
While the API runs, a scheduler repeats every 3 hours (`LIVELYBORG_CYCLE_HOURS`): refresh results and fixtures → predict → **lock** predictions for matches kicking off within 36 hours → **grade** finished matches. The model retrains itself when it is more than 7 days old. Set `LIVELYBORG_AUTO_REFRESH=0` to disable.
```bash
# Run one cycle without the API (e.g. from Windows Task Scheduler); add --retrain to also retrain
.\.venv\Scripts\python -m apps.api.app.jobs
```
- Locked predictions live in the `predictions` table: append-only, each row hash-chained to the previous one. Results are graded from the official results feed; there is no manual result entry.
- `GET /api/v1/track-record` shows accuracy and what a flat ₦1,000 on every priced pick would have returned; `GET /api/v1/track-record/verify` recomputes the hash chain.
- With `FOOTBALL_DATA_KEY` set, fixtures up to 14 days ahead are added from football-data.org for 8 top leagues (team names are mapped automatically; unmatched names appear in `/api/v1/data/status`).

### 3. Start the FastAPI Predictive Backend
```bash
.\.venv\Scripts\python -m uvicorn apps.api.app.main:app --reload --port 8000
```
- API Docs: `http://127.0.0.1:8000/docs`
- Healthcheck: `http://127.0.0.1:8000/api/v1/health`

### 4. Start the Next.js Mobile-First Web PWA
```bash
cd apps/web
npm run dev
```
Open `http://localhost:3000` to interact with the full dashboard.

### 5. Test the Telegram VIP Bot
```bash
.\.venv\Scripts\python apps/bot/telegram_bot.py
```
