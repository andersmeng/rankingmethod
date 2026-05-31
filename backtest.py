import numpy as np
import pandas as pd
from config import *
from data_utils import download_data, download_fx_rates, convert_to_usd
from selection import get_correlation, select_picks, composite_score
from features import compute_features


def _metrics(returns, name):
    cum = (1 + returns).cumprod()
    total_ret = cum.iloc[-1] - 1
    n_years = len(returns) / 12
    ann_ret = (1 + total_ret) ** (1 / n_years) - 1
    ann_vol = returns.std() * np.sqrt(12)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
    running_max = cum.cummax()
    drawdown = (cum - running_max) / running_max
    max_dd = drawdown.min()
    win_rate = (returns > 0).mean()
    avg_win = returns[returns > 0].mean() if (returns > 0).any() else 0
    avg_loss = returns[returns < 0].mean() if (returns < 0).any() else 0

    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    print(f"  Total Return:        {total_ret:>8.2%}")
    print(f"  Annualized Return:   {ann_ret:>8.2%}")
    print(f"  Annualized Vol:      {ann_vol:>8.2%}")
    print(f"  Sharpe Ratio:        {sharpe:>8.2f}")
    print(f"  Max Drawdown:        {max_dd:>8.2%}")
    print(f"  Win Rate:            {win_rate:>8.2%}")
    print(f"  Avg Win:             {avg_win:>8.2%}")
    print(f"  Avg Loss:            {avg_loss:>8.2%}")
    print(f"  Months:              {len(returns):>8d}")
    return {'returns': returns, 'cumulative': cum, 'drawdown': drawdown}


def run_backtest(force_download=False, composite=False):
    print("=== BACKTEST ===")

    print("Loading price data...")
    adj_close_raw, volume_raw = download_data(ALL_TICKERS, TRAIN_START_DATE, TRAIN_END_DATE, force=force_download)
    fx_rates = download_fx_rates(TRAIN_START_DATE, TRAIN_END_DATE, force=force_download)
    adj_close = convert_to_usd(adj_close_raw, fx_rates)
    volume = volume_raw[adj_close.columns]

    if composite:
        print("Using composite scoring (no ML model)")
        monthly_dates = pd.date_range(start=PANEL_START_DATE, end=TRAIN_END_DATE, freq='BME')
        dates = [d for d in monthly_dates if d in adj_close.index]
        score_map = {}
        for dt in dates:
            feat = compute_features(adj_close, volume, dt)
            if feat.empty:
                continue
            feat = composite_score(feat)
            for t in feat.index:
                score_map.setdefault(dt, {})[t] = feat.loc[t, 'score']
    else:
        oos_path = 'oos_predictions.csv'
        try:
            oos_df = pd.read_csv(oos_path)
            oos_df['date'] = pd.to_datetime(oos_df['date'])
        except FileNotFoundError:
            print(f"Error: {oos_path} not found. Run 'python main.py train' first.")
            return
        dates = sorted(oos_df['date'].unique())
    strat_rets, bench_rets = [], []
    trade_log = []
    prev_selected = set()

    for dt in dates:
        if dt not in adj_close.index:
            continue
        loc = adj_close.index.get_loc(dt)
        if loc + 22 >= len(adj_close):
            continue
        future = adj_close.index[loc + 22]

        entry = adj_close.loc[dt]
        exit_ = adj_close.loc[future]

        if composite:
            scores_at_dt = score_map.get(dt, {})
            if len(scores_at_dt) < 3:
                continue
            day_scores = pd.Series(scores_at_dt).sort_values(ascending=False)
            feat_for_select = day_scores.to_frame('score')
        else:
            day_scores = oos_df[oos_df['date'] == dt].sort_values('score', ascending=False)
            feat_for_select = day_scores.set_index('ticker')

        selected = select_picks(feat_for_select, adj_close, n_stocks=STOP_N,
                                persist_tickers=prev_selected, persist_bonus=PERSIST_BONUS)
        if len(selected) < 1:
            continue
        prev_selected = set(selected)

        # Score-weighted return with stop-loss simulation
        scores = np.array([feat_for_select.loc[t, 'score'] for t in selected])
        scores = scores - scores.min() + 1e-8
        weights = scores / scores.sum()
        tc = COMMISSION + SLIPPAGE
        rets = []
        for t in selected:
            entry_price = entry[t]

            # Compute stop level (same logic as train.py)
            if STOP_LOSS_TYPE == 'fixed':
                stop = entry_price * (1 - STOP_LOSS_PCT)
            else:
                series_before = adj_close[t].loc[:dt].dropna()
                if len(series_before) >= 20:
                    vol = series_before.pct_change().dropna().iloc[-20:].std()
                    stop = entry_price * (1 - STOP_N_SIGMA * vol)
                else:
                    stop = entry_price * 0.9

            # Daily check for stop trigger in holding period
            daily_prices = adj_close[t].loc[dt:future]
            exit_price = exit_[t]
            for day in daily_prices.index[1:]:
                if daily_prices[day] <= stop:
                    exit_price = daily_prices[day]
                    break

            rets.append(exit_price / entry_price - 1)

        strat_ret = (np.array(rets) - tc).dot(weights)
        strat_rets.append(strat_ret)

        for t, w, r in zip(selected, weights, rets):
            trade_log.append({
                'date': dt, 'ticker': t, 'weight': round(w, 4),
                'return': r,
                'return_net': r - tc,
            })

        all_ = [c for c in adj_close.columns if c in entry.index and c in exit_.index]
        bench_ret = (exit_[all_] / entry[all_]).mean() - 1 if all_ else 0
        bench_rets.append(bench_ret)

    strat = pd.Series(strat_rets, index=dates[:len(strat_rets)])
    bench = pd.Series(bench_rets, index=dates[:len(bench_rets)])

    _metrics(strat, 'STRATEGY (sector-div., score-weighted, top 6)')
    _metrics(bench, 'BENCHMARK (equal-weight universe)')

    # Excess returns
    excess = strat - bench
    print(f"\n  EXCESS RETURN (Strategy - Benchmark)")
    print(f"  Mean Excess:          {excess.mean():>8.2%}")
    print(f"  Positive Months:      {(excess > 0).mean():>8.2%}")
    hit_rate = (excess > 0).mean()
    print(f"  Hit Rate vs Benchmark:{hit_rate:>8.2%}")

    print(f"\n  TRANSACTION COSTS: {COMMISSION:.1%} commission + {SLIPPAGE:.1%} slippage per trade")
    if STOP_LOSS_TYPE == 'fixed':
        print(f"  STOP-LOSS: {STOP_LOSS_PCT:.0%} fixed below entry")
    else:
        print(f"  STOP-LOSS: {STOP_N_SIGMA}-sigma volatility-based (trailing)")

    # Best/worst picks (net of costs, weighted)
    trades = pd.DataFrame(trade_log)
    trades['weighted_net'] = trades['return_net'] * trades['weight']
    best = trades.groupby('ticker')['weighted_net'].sum().sort_values(ascending=False)
    print(f"\n  TOP 5 TICKERS BY AVG NET RETURN:")
    for t, r in best.head(5).items():
        print(f"    {t:15s}  {r:.2%}")
    print(f"\n  WORST 5 TICKERS BY AVG NET RETURN:")
    for t, r in best.tail(5).items():
        print(f"    {t:15s}  {r:.2%}")

    # Save trade log
    trades.to_csv('backtest_trades.csv', index=False)
    print(f"\nTrade log saved to backtest_trades.csv")

    # Summary
    outperformance = (excess > 0).sum()
    total_months = len(excess)
    print(f"\n{'='*50}")
    print(f"  Strategy outperformed benchmark in {outperformance}/{total_months} months")
    print(f"{'='*50}")
