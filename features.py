# features.py
import numpy as np
import pandas as pd

def ppo_histogram(series):
    """PPO histogram value (12,26,9)."""
    ema12 = series.ewm(span=12, adjust=False).mean()
    ema26 = series.ewm(span=26, adjust=False).mean()
    ppo = (ema12 - ema26) / ema26 * 100
    signal = ppo.ewm(span=9, adjust=False).mean()
    return ppo - signal


def rsi(series, period=14):
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def sma_ratio(series, fast=50, slow=200):
    """SMA crossover ratio: fast/slow - 1."""
    sma_fast = series.rolling(fast).mean()
    sma_slow = series.rolling(slow).mean()
    return sma_fast / sma_slow - 1


def compute_features(close_usd, volume, date):
    """
    Compute normalized features (cross-sectional z-score) for all tickers
    using data up to and including `date`.
    """
    close_hist = close_usd.loc[:date]
    vol_hist = volume.loc[:date]
    if len(close_hist) < 252:
        return pd.DataFrame()

    returns = close_hist.pct_change().dropna()

    # Momentum 12-1
    if len(close_hist) >= 273:  # 252 + 21
        mom_12_1 = close_hist.iloc[-22] / close_hist.iloc[-252] - 1
    else:
        mom_12_1 = np.nan
    # 5-day reversal
    rev_5 = close_hist.iloc[-1] / close_hist.iloc[-5] - 1 if len(close_hist) >= 5 else np.nan
    # 20-day volatility
    vol_20 = returns.iloc[-20:].std() * np.sqrt(252) if len(returns) >= 20 else np.nan
    # Dollar volume (log)
    dollar_vol = (close_hist.iloc[-20:] * vol_hist.iloc[-20:]).mean()
    log_dollar_vol = np.log(dollar_vol.clip(lower=1e-9))
    # PPO histogram
    ppo = {}
    for ticker in close_hist.columns:
        prices = close_hist[ticker].dropna()
        if len(prices) >= 26:
            ppo[ticker] = ppo_histogram(prices).iloc[-1]
        else:
            ppo[ticker] = np.nan

    # RSI (14-day)
    rsi_val = {}
    for ticker in close_hist.columns:
        prices = close_hist[ticker].dropna()
        if len(prices) >= 14:
            rsi_val[ticker] = rsi(prices).iloc[-1]
        else:
            rsi_val[ticker] = np.nan

    # SMA crossover (50/200)
    sma = {}
    for ticker in close_hist.columns:
        prices = close_hist[ticker].dropna()
        if len(prices) >= 200:
            sma[ticker] = sma_ratio(prices).iloc[-1]
        else:
            sma[ticker] = np.nan

    # Volume trend (20d avg / 60d avg - 1)
    eps = 1e-12
    vol_trend = {}
    for ticker in vol_hist.columns:
        v = vol_hist[ticker].dropna()
        if len(v) >= 60:
            vol_trend[ticker] = v.iloc[-20:].mean() / (v.iloc[-60:].mean() + eps) - 1
        else:
            vol_trend[ticker] = np.nan

    feat_df = pd.DataFrame({
        'mom_12_1': mom_12_1,
        'rev_5': rev_5,
        'vol_20': vol_20,
        'log_dollar_vol': log_dollar_vol,
        'ppo_hist': pd.Series(ppo),
        'rsi_14': pd.Series(rsi_val),
        'sma_50_200': pd.Series(sma),
        'vol_trend': pd.Series(vol_trend),
    }, index=close_hist.columns)

    # Cross-sectional z-score
    feat_z = (feat_df - feat_df.mean()) / feat_df.std()
    feat_z = feat_z.clip(-3, 3)
    return feat_z.dropna()

def create_labels(close_usd, date, holding_period=21):
    """Forward 1-month return percentile (0–1) as relevance label."""
    if date not in close_usd.index:
        return pd.Series(dtype=float)
    loc = close_usd.index.get_loc(date)
    if loc + holding_period >= len(close_usd.index):
        return pd.Series(dtype=float)
    future_date = close_usd.index[loc + holding_period]
    entry = close_usd.loc[date]
    exit_ = close_usd.loc[future_date]
    fwd_ret = exit_ / entry - 1
    fwd_ret = fwd_ret.dropna()
    if fwd_ret.empty:
        return pd.Series(dtype=float)
    return fwd_ret.rank(pct=True)
