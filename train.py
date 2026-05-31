# train.py
import json, os
import numpy as np
import pandas as pd
import joblib
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from config import *
from data_utils import download_data, download_fx_rates, convert_to_usd
from features import compute_features, create_labels
from selection import select_picks

def build_panel(adj_close, volume):
    """Create monthly panel with features and labels."""
    monthly_dates = pd.date_range(PANEL_START_DATE, TRAIN_END_DATE, freq='BME')
    panel = []
    for dt in monthly_dates:
        if dt not in adj_close.index:
            dt_actual = adj_close.index.asof(dt)
        else:
            dt_actual = dt
        X = compute_features(adj_close, volume, dt_actual)
        if X.empty:
            continue
        y = create_labels(adj_close, dt_actual, holding_period=21)
        common = X.index.intersection(y.index)
        if len(common) < 10:
            continue
        temp = X.loc[common].copy()
        temp['relevance'] = (y.loc[common] * 100).astype(int)
        temp['date'] = dt_actual
        panel.append(temp)
    panel_df = pd.concat(panel).reset_index().rename(columns={'index': 'ticker'})
    return panel_df

def train_walkforward(force_download=False):
    print("=== TRAINING STARTED ===")
    # 1. Download data
    adj_close_raw, volume_raw = download_data(ALL_TICKERS, TRAIN_START_DATE, TRAIN_END_DATE, force=force_download)
    fx_rates = download_fx_rates(TRAIN_START_DATE, TRAIN_END_DATE, force=force_download)
    adj_close = convert_to_usd(adj_close_raw, fx_rates)
    volume = volume_raw[adj_close.columns]  # align

    # 2. Build panel
    print("Building feature panel...")
    panel_df = build_panel(adj_close, volume)
    print(f"Panel shape: {panel_df.shape}")

    # 3. Walk-forward training (ensemble)
    all_dates = sorted(panel_df['date'].unique())
    oos_predictions = []
    start_test_idx = INITIAL_TRAIN_MONTHS
    last_models = []
    last_scaler = None

    while start_test_idx + TEST_MONTHS <= len(all_dates):
        train_end_idx = start_test_idx - PURGE_MONTHS
        if train_end_idx <= 0:
            start_test_idx += TEST_MONTHS
            continue
        train_dates = all_dates[:train_end_idx]
        test_dates = all_dates[start_test_idx:start_test_idx+TEST_MONTHS]

        train_mask = panel_df['date'].isin(train_dates)
        test_mask = panel_df['date'].isin(test_dates)

        X_train = panel_df.loc[train_mask, FEATURE_COLS]
        y_train = panel_df.loc[train_mask, 'relevance']
        X_test = panel_df.loc[test_mask, FEATURE_COLS]
        if X_train.empty or X_test.empty:
            start_test_idx += TEST_MONTHS
            continue

        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        train_groups = panel_df.loc[train_mask].groupby('date').size().values
        test_groups = panel_df.loc[test_mask].groupby('date').size().values

        # Ensemble: train ENSEMBLE_SIZE models with different seeds
        ensemble_scores = np.zeros(X_test_s.shape[0])
        window_models = []
        for i in range(ENSEMBLE_SIZE):
            params = {**LGB_PARAMS, 'random_state': SEED_BASE + i}
            model = lgb.LGBMRanker(**params)
            model.fit(
                X_train_s, y_train,
                group=train_groups,
                eval_set=[(X_test_s, panel_df.loc[test_mask, 'relevance'])],
                eval_group=[test_groups],
                callbacks=[lgb.early_stopping(20), lgb.log_evaluation(0)],
            )
            ensemble_scores += model.predict(X_test_s)
            window_models.append(model)

        ensemble_scores /= ENSEMBLE_SIZE
        temp = panel_df.loc[test_mask, ['date', 'ticker']].copy()
        temp['score'] = ensemble_scores
        oos_predictions.append(temp)

        last_models = window_models
        last_scaler = scaler
        start_test_idx += TEST_MONTHS

    # 4. Save artifacts (ensemble)
    ensemble_data = {'models': last_models, 'ensemble_size': ENSEMBLE_SIZE}
    joblib.dump(ensemble_data, MODEL_PATH)
    joblib.dump(last_scaler, SCALER_PATH)
    print(f"Ensemble of {ENSEMBLE_SIZE} models saved to {MODEL_PATH}, scaler to {SCALER_PATH}")

    # 5. Save OOS predictions for later analysis (optional)
    oos_df = pd.concat(oos_predictions)
    oos_df.to_csv('oos_predictions.csv', index=False)

    # 6. Score latest data with final ensemble and show top picks
    print("\nScoring latest market data...")
    last_bme = pd.date_range(PANEL_START_DATE, TRAIN_END_DATE, freq='BME')[-1]
    if last_bme in adj_close.index:
        latest_ref = last_bme
    else:
        latest_ref = adj_close.index.asof(last_bme)
    X_latest = compute_features(adj_close, volume, latest_ref)
    if not X_latest.empty:
        X_latest_s = last_scaler.transform(X_latest[FEATURE_COLS].dropna())
        scores = np.mean([m.predict(X_latest_s) for m in last_models], axis=0)
        latest_df = X_latest.loc[X_latest[FEATURE_COLS].dropna().index].copy()
        latest_df['score'] = scores
        latest_df = latest_df.sort_values('score', ascending=False)

        persist = set()
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE) as f:
                persist = {p['ticker'] for p in json.load(f)}
        selected = select_picks(latest_df, adj_close, n_stocks=STOP_N,
                                persist_tickers=persist, persist_bonus=PERSIST_BONUS)

        # Score-weighted position sizing
        scores = np.array([latest_df.loc[t, 'score'] for t in selected])
        scores = scores - scores.min() + 1e-8
        weights = scores / scores.sum()

        print(f"\n=== TOP {STOP_N} DIVERSIFIED PICKS ({latest_ref.date()}) ===")
        print(f"{'#':>2} {'Ticker':15s} {'Score':>8s} {'Weight':>8s} {'Price':>10s} {'Sector':>12s}")
        print('-' * 57)
        for i, (ticker, w) in enumerate(zip(selected, weights), 1):
            s = latest_df.loc[ticker, 'score']
            p = adj_close[ticker].iloc[-1]
            sec = SECTOR_MAP.get(ticker, 'OTHER')
            print(f"{i:2d}. {ticker:15s} {s:8.4f} {w:7.1%} ${p:>7.2f} {sec:>12s}")
        print(f"\nNext rebalance: {TRADE_START_DATE}")

        # Save as portfolio with stop-loss levels and score weights
        total_capital = CAPITAL_PER_POSITION * STOP_N
        positions = []
        for ticker, w in zip(selected, weights):
            price = float(adj_close[ticker].iloc[-1])
            alloc = total_capital * w
            if STOP_LOSS_TYPE == 'fixed':
                stop = round(price * (1 - STOP_LOSS_PCT), 2)
            else:
                series = adj_close[ticker].dropna()
                if len(series) >= 20:
                    vol = series.pct_change().dropna().iloc[-20:].std()
                    stop = round(price * (1 - STOP_N_SIGMA * vol), 2)
                else:
                    stop = round(price * 0.9, 2)
            positions.append({
                'ticker': ticker,
                'entry_price': price,
                'shares': int(alloc / price),
                'weight': round(w, 4),
                'entry_date': str(latest_ref.date()),
                'stop_loss': stop,
                'stop_type': STOP_LOSS_TYPE,
            })
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(positions, f, indent=2)
        print(f"\nPortfolio saved to {PORTFOLIO_FILE}")
        if STOP_LOSS_TYPE == 'fixed':
            print(f"Stop-loss: {STOP_LOSS_PCT:.0%} below entry for each position")
        else:
            print(f"Stop-loss: {STOP_N_SIGMA}-sigma volatility-based for each position")
    print("Training complete.")