# daily_check.py
# Run daily (e.g., via cron after market close) to get portfolio status and sell alerts.
#
# Usage:
#   .venv/bin/python daily_check.py                          # print report to stdout
#   .venv/bin/python daily_check.py --mail user@example.com   # email report
#   .venv/bin/python daily_check.py --force                   # bypass cache
#
# Cron example (every weekday at 6 PM):
#   0 18 * * 1-5 cd /path/to/project && .venv/bin/python daily_check.py --mail you@email.com

import argparse, json, os, subprocess, sys, textwrap
from datetime import datetime

import numpy as np
import pandas as pd
import joblib

from config import *
from data_utils import download_data, download_fx_rates, convert_to_usd
from features import compute_features


# ── helpers ──────────────────────────────────────────────────────────
from selection import get_correlation, select_picks


def _stop_level(price_series, entry_price):
    if STOP_LOSS_TYPE == 'fixed':
        return entry_price * (1 - STOP_LOSS_PCT)
    if len(price_series) < 20:
        return entry_price * 0.9
    vol = price_series.pct_change().dropna().iloc[-20:].std()
    return price_series.iloc[-1] * (1 - STOP_N_SIGMA * vol)


def _fmt(val):
    if isinstance(val, float):
        return f"{val:.2f}"
    return str(val)


# ── main ─────────────────────────────────────────────────────────────

def run_daily_check(mail_to=None, force=False):
    today = pd.Timestamp.today().normalize()
    lines = []
    def out(msg=""):
        lines.append(msg)
        print(msg)

    out(f"{'='*60}")
    out(f"  DAILY PORTFOLIO CHECK  —  {today.date()}")
    out(f"{'='*60}")

    # 1. Load model & data
    if not os.path.exists(MODEL_PATH) or not os.path.exists(PORTFOLIO_FILE):
        out("ERROR: model or portfolio file missing. Run 'python main.py train' first.")
        return _finish(lines, mail_to)

    ensemble_data = joblib.load(MODEL_PATH)
    models = ensemble_data['models']
    scaler = joblib.load(SCALER_PATH)

    end_date = today
    start_date = end_date - pd.DateOffset(years=MONITOR_LOOKBACK_YEARS)
    out(f"Data: {start_date.date()} → {end_date.date()}")

    adj_close_raw, volume_raw = download_data(ALL_TICKERS, start_date, end_date, force=force)
    fx_rates = download_fx_rates(start_date, end_date, force=force)
    adj_close = convert_to_usd(adj_close_raw, fx_rates)
    volume = volume_raw[adj_close.columns]

    # 2. Score universe with latest model
    last_bme = pd.date_range(start=PANEL_START_DATE, end=end_date, freq='BME')[-1]
    if last_bme not in adj_close.index:
        last_bme = adj_close.index.asof(last_bme)

    feat_df = compute_features(adj_close, volume, last_bme)
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
    picks = select_picks(feat_df, adj_close, persist_tickers=persist,
                         persist_bonus=PERSIST_BONUS)
    pick_scores = {t: feat_df.loc[t, 'score'] for t in picks}

    # 3. Load current portfolio
    with open(PORTFOLIO_FILE) as f:
        portfolio = json.load(f)

    portfolio_map = {p['ticker']: p for p in portfolio}
    current_prices = {}
    for p in portfolio:
        t = p['ticker']
        if t in adj_close.columns:
            current_prices[t] = float(adj_close[t].iloc[-1])

    # 4. SELL signals — stop-loss triggered
    out()
    out("── STOP-LOSS CHECK ──")
    sell_signals = []
    for p in portfolio:
        t = p['ticker']
        if t not in current_prices:
            out(f"  {t:15s}  NO DATA")
            continue
        entry = p['entry_price']
        current = current_prices[t]
        pnl = (current - entry) / entry
        series = adj_close[t]
        stop = _stop_level(series, p['entry_price'])
        triggered = current <= stop

        status = "SELL" if triggered else "OK"
        if triggered:
            sell_signals.append(t)
        out(f"  {t:15s}  entry={entry:<8.2f}  curr={current:<8.2f}  "
            f"P&L={pnl:>+7.2%}  stop={stop:<8.2f}  [{status}]")

    # 5. WATCH signals — dropped from top N picks
    out()
    out("── REBALANCE CHECK ──")
    pick_set = set(picks)
    for p in portfolio:
        t = p['ticker']
        if t not in pick_set:
            rank = list(feat_df.index).index(t) + 1 if t in feat_df.index else "N/A"
            out(f"  {t:15s}  NOT IN TOP {N_STOCKS}  (rank={rank})  → consider selling at next rebalance")

    out(f"\n  Current top picks: {', '.join(f'{t}({pick_scores[t]:.3f})' for t in picks)}")

    # 6. Correlation check
    out()
    out("── CORRELATION CHECK ──")
    high_corr = False
    for i in range(len(portfolio)):
        for j in range(i + 1, len(portfolio)):
            t1, t2 = portfolio[i]['ticker'], portfolio[j]['ticker']
            if t1 not in adj_close.columns or t2 not in adj_close.columns:
                continue
            c = get_correlation(t1, t2, adj_close)
            if abs(c) > CORR_THRESH:
                high_corr = True
                out(f"  {t1} ↔ {t2}: corr={c:.3f}  HIGH  → consider diversifying")
    if not high_corr:
        out("  All pairs OK (below {:.0%})".format(CORR_THRESH))

    # 7. Summary
    out()
    out(f"{'='*60}")
    if sell_signals:
        out(f"  ACTION REQUIRED: SELL {', '.join(sell_signals)} (stop-loss triggered)")
    elif any(t not in pick_set for t in [p['ticker'] for p in portfolio]):
        out("  ACTION: Positions dropped from top picks — prepare for next rebalance")
    else:
        out("  ALL CLEAR — portfolio is healthy")

    # Portfolio P&L
    total_pnl = 0
    count = 0
    for p in portfolio:
        t = p['ticker']
        if t in current_prices:
            total_pnl += (current_prices[t] - p['entry_price']) / p['entry_price'] * p.get('weight', 1/N_STOCKS)
            count += 1
    if count:
        out(f"  Weighted P&L: {total_pnl:>+7.2%}")
    out(f"{'='*60}")

    # Save report
    report_path = f"daily_report_{today.date()}.txt"
    with open(report_path, 'w') as f:
        f.write('\n'.join(lines))
    out(f"\nReport saved to {report_path}")

    if mail_to:
        _send_mail(lines, mail_to)

    return sell_signals


def _send_mail(lines, mail_to):
    body = '\n'.join(lines)
    try:
        subprocess.run(
            ["sendmail", mail_to],
            input=f"Subject: Daily Portfolio Report\n\n{body}".encode(),
            check=True, timeout=30,
        )
        print(f"Email sent to {mail_to}")
    except Exception as e:
        print(f"Email failed: {e}")
        print("Install sendmail or pipe output manually:\n"
              f"  .venv/bin/python daily_check.py | mail -s 'Report' {mail_to}")


def _finish(lines, mail_to):
    if mail_to:
        _send_mail(lines, mail_to)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Daily portfolio check")
    parser.add_argument('--mail', '-m', type=str, help='email address to send report to')
    parser.add_argument('--force', '-f', action='store_true', help='bypass cache')
    args = parser.parse_args()
    run_daily_check(mail_to=args.mail, force=args.force)
