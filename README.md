# Ranking Method

A machine learning-driven stock ranking and portfolio system using LightGBM LambdaRank. Scores a 180+ ticker multi-country equity universe (US + Nordic) on momentum, volatility, and technical features, then selects a sector-diversified, low-correlation portfolio with volatility-based stops.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

| Command | What it does |
|---|---|
| `python main.py train` | Downloads data, trains model ensemble, scores latest market, saves portfolio |
| `python main.py monitor` | Checks current positions against stop-losses and correlation limits |
| `python main.py backtest` | Evaluates strategy on walk-forward OOS predictions |
| `python main.py backtest --composite` | Backtest using fixed-formula composite scoring (no ML) |
| `python main.py daily` | Full daily report with sell signals, rebalance alerts, correlation check |
| `python main.py daily --mail user@example.com` | Same, emailed |
| `{cmd} --force` | Force re-download all data (bypass cache) |

Data is cached in `.data_cache/` after first download. Each cache (stock prices, volume, FX rates) tracks its own timestamp independently and expires after 2 days. Non-USD prices are converted via FX rates, with forward-fill to handle mismatched trading calendars (e.g. FX markets closed when stocks trade).

## Pipeline

1. **Data**: yfinance downloads 180+ US/Nordic tickers, converts non-USD prices via FX rates.
2. **Features** (per stock, monthly): 12-1 month momentum, 5-day reversal, 20-day volatility, log dollar volume, PPO histogram. Cross-sectionally z-scored.
3. **Model**: LightGBM LambdaRank ensemble (3 models, different seeds) via walk-forward validation (36-month initial train, 6-month test windows, 3-month purge gap).
4. **Selection**: Score all tickers → pick top N with sector limit (1/sector) + correlation filter (<0.85). Held stocks get a persistence bonus (+0.10 score) to reduce churn.
5. **Portfolio**: Score-weighted position sizing, saved to `current_portfolio.json` with entry prices, share counts, and stop-loss levels.
6. **Risk**: Volatility-based trailing stop (2.5 sigma of 20-day returns) or fixed percentage stop.

### Composite scoring (fallback)

When run with `--composite`, the system uses a fixed-formula score:

```
score = 0.50 * mom_12_1 + 0.20 * rev_5 - 0.15 * vol_20 + 0.10 * log_dollar_vol + 0.05 * ppo_hist
```

No training required — useful as a baseline or when ML predictions are unavailable.

## Configuration (`config.py`)

| Setting | Default | Notes |
|---|---|---|
| `STOP_N` | 6 | Number of positions to hold |
| `ENSEMBLE_SIZE` | 3 | Number of LGBM models per window (different seeds) |
| `SECTOR_LIMIT` | 1 | Max positions per sector |
| `PERSIST_BONUS` | 0.10 | Score boost for held stocks at rebalance |
| `STOP_LOSS_TYPE` | `'volatility'` | `'volatility'` or `'fixed'` |
| `STOP_N_SIGMA` | 2.5 | Sigma multiplier for vol stops |
| `STOP_LOSS_PCT` | 0.05 | Fixed % stop |
| `CORR_THRESH` | 0.85 | Max pairwise return correlation |
| `INITIAL_TRAIN_MONTHS` | 36 | Months of initial training data |
| `TEST_MONTHS` | 6 | Months per test window |
| `PURGE_MONTHS` | 3 | Gap between train/test |
| `COMMISSION` | 0.001 | Per-trade commission (10 bps) |
| `SLIPPAGE` | 0.001 | Per-trade slippage (10 bps) |
| `COMPOSITE_WEIGHTS` | dict | Fixed coefficients for composite scoring |

## Project structure

```
main.py              CLI entry point (train | monitor | backtest | daily)
config.py            Universe, parameters, stop-loss settings
data_utils.py        yfinance download, FX conversion, caching
features.py          Feature computation & label creation
train.py             Walk-forward ensemble training + portfolio saving
selection.py         Shared pick logic: select_picks(), get_correlation(), composite_score()
monitor.py           Daily portfolio check (stops, correlations)
daily_check.py       Full daily report with email
backtest.py          Performance evaluation with stop-loss simulation
viz.py               Holdings chart + turnover reporting
```

## Key decisions

- **Ensemble of 3** LGBM rankers smooths noisy predictions vs single model (Sharpe 1.22 vs 1.18)
- **Sector limit** (1/sector) and **persistence bonus** (0.10) reduced turnover from 9.7 to 2.4 trades/month
- **5 core features** used — 3 additional candidates tested all hurt Sharpe
- **Regularized params** (num_leaves=15, lr=0.03) — deeper trees overfit
- **LambdaRank converges in 1-8 iterations** — features are the bottleneck, not model capacity
