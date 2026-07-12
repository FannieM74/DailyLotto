# DailyLotto Prediction Platform

Multi-game SA lottery prediction platform supporting **5 games** with **8 prediction methods** each. Built with FastAPI, Next.js 14, SQLite, Docker.

## Supported Games

| Game | Numbers | Range | Bonus/PB | Draw Days |
|------|---------|-------|----------|-----------|
| Daily Lotto | 5 | 1-36 | — | Daily |
| Lotto | 6 | 1-58 | Bonus 1-58 | Wed, Sat |
| Lotto Plus | 6 | 1-58 | Bonus 1-58 | Wed, Sat |
| PowerBall | 5 | 1-50 | PB 1-20 | Tue, Fri |
| PowerBall XTRA | 5 | 1-50 | PB 1-20 | Tue, Fri |

## Prediction Methods

| Method | Type | Varies per draw? | Description |
|--------|------|-------------------|-------------|
| Frequency | Statistical | Yes (rolling 200) | Most frequent numbers in recent draws |
| Weighted | Recency | Yes | Recent draws weighted more heavily |
| Pair Freq | Co-occurrence | Yes (rolling 200) | Most common number pairs |
| Delta | Gap analysis | Yes | Most common gaps between consecutive numbers |
| Ensemble | Consensus | Yes | Votes across multiple methods |
| Markov | Transition | Yes | Probability matrix from last draw |
| Hot/Cold | Extreme | Partially | Hottest + coldest numbers |
| AI (LSTM) | Neural net | Yes | Sequence prediction model |

## Prediction Schedule (SAST)

| Game | Predict Time | After Draw Backfill |
|------|-------------|-------------------|
| Daily Lotto | Daily 05:00 | Daily 06:00 |
| Lotto | Wed/Sat 04:00 | Thu/Sun 06:00 |
| Lotto Plus | Wed/Sat 04:05 | Thu/Sun 06:05 |
| PowerBall | Tue/Fri 05:00 | Wed/Sat 06:00 |
| PowerBall XTRA | Tue/Fri 05:05 | Wed/Sat 06:05 |

Predictions are generated for the **next draw day**, not today. On non-draw days, the dashboard shows predictions for the upcoming draw.

## Key Features

- **Game selector** — switch between 5 games, all data (predictions, win rates, history) filters per game
- **Method filter** — custom dropdown shows each method's last 3 match counts for quick comparison
- **Consensus row** — shows most-agreed numbers across all 8 methods with vote counts
- **Draw-day aware** — predictions only generated on draw days; dashboard adapts automatically
- **Rolling window** — stable methods use last 200 draws instead of all history, so predictions vary per date
- **Win rates** — per-method stats: total predictions, avg matches, win rate (2+), best streak
- **Recent predictions** — color-coded match history showing predicted vs actual numbers
- **Ticket checker** — check your numbers against historical draws for any game

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, SQLite (WAL mode), APScheduler, NumPy
- **Frontend:** Next.js 14 (App Router), TypeScript, CSS
- **Deployment:** Docker Compose (API + Frontend)

## Project Structure

```
DailyLotto/
├── backend/
│   ├── main.py           # FastAPI routes, scheduler, game-aware endpoints
│   ├── database.py       # SQLAlchemy models, WAL mode, migration
│   ├── games.py          # Game config (5 games + next_draw_date helper)
│   ├── scraper.py        # CSV + web scraping per game
│   ├── seed.py           # Game-aware data import
│   ├── predictor.py      # Store predictions + backfill matches
│   ├── backtest.py       # Walk-forward backtest (rolling window 200)
│   ├── models/
│   │   ├── frequency.py  # Frequency analysis
│   │   ├── markov.py     # Markov chain transitions
│   │   ├── lstm.py       # LSTM neural network (pure NumPy)
│   │   └── alternative.py # Pair freq, delta, ensemble, weighted, hot/cold
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── page.tsx       # Dashboard — predictions, win rates, tracker, consensus
│   │   ├── checker/page.tsx # Ticket checker
│   │   ├── layout.tsx     # Root layout with GameProvider
│   │   └── globals.css    # All styles
│   ├── components/
│   │   ├── Header.tsx     # Logo + nav
│   │   ├── SelectorBar.tsx # Game + Method selectors on own line
│   │   ├── GameSelector.tsx # Game dropdown
│   │   ├── MethodSelector.tsx # Custom method dropdown with last-3 matches
│   │   ├── NumberBall.tsx # Number display ball
│   │   ├── PredictionCard.tsx # Prediction + result comparison cards
│   │   └── DrawHistory.tsx # Recent draw list
│   ├── context/
│   │   └── GameContext.tsx # Game + method state provider
│   ├── lib/
│   │   └── api.ts         # API fetch functions with game param
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| GET / | Health check |
| GET /games | List all games with config |
| GET /draws/latest?game= | Latest draw for a game |
| GET /draws/recent?game=&days= | Recent draws |
| GET /predict/today?game= | All 8 methods' predictions for next draw |
| GET /predict/frequency?game= | Frequency analysis |
| GET /predict/markov?game= | Markov chain prediction |
| GET /predict/lstm?game= | LSTM prediction |
| GET /predict/pair-freq?game= | Pair frequency |
| GET /predict/delta?game= | Delta analysis |
| GET /predict/ensemble?game= | Ensemble voting |
| GET /predict/weighted-freq?game= | Weighted frequency |
| GET /predict/hot-cold?game= | Hot/cold numbers |
| GET /tracker?game= | Past predictions vs actuals |
| GET /tracker/win-rates?game= | Win rate stats per method |
| GET /tracker/recent-matches?game= | Last 3 match counts per method |
| POST /checker | Check ticket numbers vs history |
| POST /seed?game= | Import historical data for a game |
| POST /train?game= | Train LSTM model for a game |
| POST /retrain?game= | Seed + store predictions |
| POST /backfill | Backfill match counts |
| POST /backtest?game=&limit= | Run walk-forward backtest |

## Configuration

All game settings in `backend/games.py`:
- Number ranges, pick counts, draw days
- CSV/HTML scrape URLs
- Scheduler times (predict, backfill)
- Bonus/powerball flags

## Deployment

```bash
docker compose build
docker compose up -d
```

Frontend on `:3000`, API on `:8000`. API URL set via `NEXT_PUBLIC_API_URL` build arg.
