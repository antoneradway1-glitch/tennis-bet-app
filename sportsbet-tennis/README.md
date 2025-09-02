# SportsBet Tennis — Plug & Play Best-Bet Finder

A modular, end-to-end application that ingests historical tennis matches, builds features (incl. Elo),
trains a predictive model, estimates fair odds, and flags +EV bets versus bookmaker prices.
Includes a FastAPI service and a simple Streamlit UI.

## Features
- **Data layer**: DuckDB with clean schemas for matches, players, odds, and model artifacts.
- **Feature engineering**: surface-aware Elo, rolling stats, player form.
- **Modeling**: baseline Logistic Regression (sklearn) + pluggable XGBoost/LightGBM.
- **Odds math**: implied probabilities, vig removal (proportional), fair odds.
- **Decisioning**: expected value, Kelly fraction, stake sizing with bankroll guardrails.
- **Backtesting**: walk-forward split with leakage-avoidant feature generation.
- **Serving**: FastAPI endpoints for probabilities and bet suggestions.
- **UI**: Streamlit dashboard to explore edges and simulate staking.

## Quickstart
```bash
# (Recommended) create virtualenv
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Initialize DB and load sample data
python -m app.utils.db --init
python -m app.ingest.parse_atp_results --load-sample

# Build features and train the model
python -m app.features.feature_builder --rebuild
python -m app.models.train --train

# Run a quick backtest on the sample
python -m app.backtest.backtest --run

# Start API
uvicorn app.api.main:app --reload

# Start Streamlit (optional)
streamlit run app/ui/app.py
```

## Folder structure
```
app/
  data/               # sample data + schema
  ingest/             # parsers for historical datasets
  features/           # Elo + feature builder
  models/             # train + predict
  odds/               # odds and vig utilities
  ev/                 # decision engine (EV, Kelly)
  backtest/           # walk-forward backtester
  api/                # FastAPI app
  ui/                 # Streamlit app
  utils/              # db + paths
```

## Responsible Betting
This code is for educational purposes. Betting carries risk. Use limits, and never wager more than you can afford to lose.
