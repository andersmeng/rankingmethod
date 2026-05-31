# monitor.py
import numpy as np
import pandas as pd
import joblib
from datetime import datetime, timedelta
from config import *
from data_utils import download_data, download_fx_rates, convert_to_usd
from features import compute_features
import json, os
from selection import get_correlation, select_picks

def compute_stop_level(price_series, entry_price):
    if STOP_LOSS_TYPE == 'fixed':
        return entry_price * (1 - STOP_LOSS_PCT)
    if len(price_series) < 20:
        return entry_price * 0.9
    rets = price_series.pct_change().dropna().iloc[-20:]
    vol = rets.std()
    return price_series.iloc[-1] * (1 - STOP_N_SIGMA * vol)

def run_monitor(force_download=False):
    print("=== MONITORING ===")
    # 1. Load ensemble models & scaler
    ensemble_data = joblib.load(MODEL_PATH)
    models = ensemble_data['models']
    scaler = joblib.load(SCALER_PATH)

    # 2. Download recent data
    end_date = pd.Timestamp.today().normalize()
    start_date = end_date - pd.DateOffset(years=MONITOR_LOOKBACK_YEARS)
    print(f"Fetching data from {start_date.date()} to {end_date.date()}...")
    adj_close_raw, volume_raw = download_data(ALL_TICKERS, start_date, end_date)
    fx_rates = download_fx_rates(start_date, end_date)
    adj_close = convert_to_usd(adj_close_raw, fx_rates)
    volume = volume_raw[adj_close.columns]

    # 3. Determine reference date (last full month-end for official signal)
    month_ends = pd.date_range(start=PANEL_START_DATE, end=end_date, freq='BME')
    last_month_end = month_ends[-1]
    if last_month_end not in adj_close.index:
        last_month_end = adj_close.index.asof(last_month_end)
    print(f"Reference date for signal: {last_month_end.date()}")

    # 4. Compute features and score (ensemble average)
    feat_df = compute_features(adj_close, volume, last_month_end)
    if feat_df.empty:
        raise ValueError("Insufficient data to compute features.")
    X = feat_df[FEATURE_COLS].dropna()
    X_scaled = scaler.transform(X)
    scores = np.mean([m.predict(X_scaled) for m in models], axis=0)
    feat_df = feat_df.loc[X.index].copy()
    feat_df['score'] = scores
    feat_df = feat_df.sort_values('score', ascending=False)

    persist = set()
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE) as f:
            persist = {p['ticker'] for p in json.load(f)}
    selected = select_picks(feat_df, adj_close, persist_tickers=persist,
                            persist_bonus=PERSIST_BONUS)

    # Score-weighted sizing (shift to non-negative)
    weights = np.array([feat_df.loc[t, 'score'] for t in selected])
    weights = weights - weights.min() + 1e-8
    weights = weights / weights.sum()

    print("\n--- CURRENT TOP PICKS ---")
    print(f"{'#':>2} {'Ticker':15s} {'Score':>8s} {'Weight':>7s} {'Price':>10s} {'Sector':>12s}")
    print('-' * 56)
    for i, (t, w) in enumerate(zip(selected, weights), 1):
        price = adj_close[t].iloc[-1]
        score = feat_df.loc[t, 'score']
        sec = SECTOR_MAP.get(t, 'OTHER')
        print(f"{i:2d}. {t:15s} {score:8.4f} {w:6.1%} ${price:>7.2f} {sec:>12s}")

    # 6. Save/update portfolio with current picks
    total_capital = CAPITAL_PER_POSITION * N_STOCKS
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
            'entry_date': str(last_month_end.date()),
            'stop_loss': stop,
            'stop_type': STOP_LOSS_TYPE,
        })
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(positions, f, indent=2)
    print(f"\nPortfolio saved to {PORTFOLIO_FILE}")

    # 7. If a portfolio file exists, check stops and correlation breaches
    if os.path.exists(PORTFOLIO_FILE):
        with open(PORTFOLIO_FILE, 'r') as f:
            portfolio = json.load(f)
        if portfolio:
            print("\n--- PORTFOLIO CHECK ---")
            for pos in portfolio:
                ticker = pos['ticker']
                entry_price = pos['entry_price']
                shares = pos['shares']
                # current price
                if ticker not in adj_close.columns:
                    continue
                price_series = adj_close[ticker]
                current_price = price_series.iloc[-1]
                # stop level
                stop = compute_stop_level(price_series, entry_price)
                triggered = current_price <= stop
                print(f"{ticker}: entry {entry_price:.2f}  current {current_price:.2f}  stop {stop:.2f}  {'⚠️ TRIGGERED' if triggered else 'OK'}")
            # correlation check
            if len(portfolio) >= 2:
                print("\nCorrelation check:")
                for i in range(len(portfolio)):
                    for j in range(i+1, len(portfolio)):
                        t1, t2 = portfolio[i]['ticker'], portfolio[j]['ticker']
                        corr = get_correlation(t1, t2, adj_close)
                        alert = "⚠️ HIGH" if abs(corr) > CORR_THRESH else "OK"
                        print(f"{t1} vs {t2}: corr={corr:.3f} {alert}")

    else:
        print("\nNo portfolio file found. Create a 'current_portfolio.json' to track positions.")
