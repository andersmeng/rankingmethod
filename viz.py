import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict


def plot_holdings(csv_path='backtest_trades.csv', fig_path='holdings.png'):
    trades = pd.read_csv(csv_path)
    trades['date'] = pd.to_datetime(trades['date'])

    all_tickers = sorted(trades['ticker'].unique())
    dates = sorted(trades['date'].unique())

    ticker_colors = plt.colormaps.get_cmap('tab20')
    color_map = {t: ticker_colors(i % 20) for i, t in enumerate(all_tickers)}

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), height_ratios=[2, 1])
    fig.suptitle('Portfolio Holdings Over Time', fontsize=14, fontweight='bold')

    holdings = trades.pivot_table(index='date', columns='ticker', values='weight', aggfunc='first')
    holdings = holdings.reindex(dates).fillna(0)
    holdings = holdings[all_tickers]

    bottom = np.zeros(len(dates))
    for ticker in all_tickers:
        vals = holdings[ticker].values
        ax1.bar(dates, vals, bottom=bottom, color=color_map[ticker],
                width=20, edgecolor='white', linewidth=0.3)
        bottom += vals

    ax1.set_ylabel('Portfolio Weight')
    ax1.set_title('Monthly Portfolio Composition (stacked by weight)')
    ax1.legend(handles=[mpatches.Patch(color=color_map[t], label=t) for t in all_tickers],
               loc='upper left', bbox_to_anchor=(1, 1), ncol=1, fontsize=8)
    ax1.set_ylim(0, 1.05)
    ax1.grid(axis='y', alpha=0.3)

    returns = trades.pivot_table(index='date', columns='ticker', values='return', aggfunc='first')
    cum_rets = {}
    for t in all_tickers:
        if t in returns.columns:
            s = returns[t].dropna().add(1).cumprod().sub(1)
            cum_rets[t] = s

    for t, s in cum_rets.items():
        ax2.plot(s.index, s.values, color=color_map[t], linewidth=1.5, alpha=0.8)

    eq_bench = trades.groupby('date')['return'].apply(lambda x: x.mean())
    eq_cum = eq_bench.add(1).cumprod().sub(1)
    ax2.plot(eq_cum.index, eq_cum.values, 'k--', linewidth=2, alpha=0.7, label='Benchmark')

    ax2.set_ylabel('Cumulative Return')
    ax2.set_title('Cumulative Return by Ticker (dashed = equal-weight benchmark)')
    ax2.axhline(y=0, color='grey', linestyle='-', linewidth=0.5)
    ax2.legend(fontsize=8)
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(fig_path, dpi=150, bbox_inches='tight')
    print(f"Chart saved to {fig_path}")
    plt.close()


def print_turnover(csv_path='backtest_trades.csv'):
    trades = pd.read_csv(csv_path)
    trades['date'] = pd.to_datetime(trades['date'])

    dates = sorted(trades['date'].unique())
    total_trades = 0
    prev_holdings = set()
    print(f"\n── TRADES PER MONTH ──")
    for dt in dates:
        month = trades[trades['date'] == dt]
        current = set(month['ticker'])
        turnover_buys = current - prev_holdings
        turnover_sells = prev_holdings - current
        n_trades = len(turnover_buys) + len(turnover_sells)
        total_trades += n_trades
        if n_trades > 0:
            print(f"  {dt.date()}: {n_trades} trades  "
                  f"+{','.join(sorted(turnover_buys)) if turnover_buys else '—'}  "
                  f"-{','.join(sorted(turnover_sells)) if turnover_sells else '—'}")
        prev_holdings = current

    n_months = len(dates)
    print(f"\n  Total: {total_trades} trades over {n_months} months")
    print(f"  Avg turnover: {total_trades / n_months:.1f} trades/month")


if __name__ == '__main__':
    plot_holdings()
    print_turnover()
