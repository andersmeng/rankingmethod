# data_utils.py
import os, json
import pandas as pd
import yfinance as yf
from config import *

CACHE_DIR = '.data_cache'
_STALE_DAYS = 2

def _cache_path(name):
    return os.path.join(CACHE_DIR, f'{name}.parquet')

def _meta_path():
    return os.path.join(CACHE_DIR, 'meta.json')

def _read_meta():
    if not os.path.exists(_meta_path()):
        return {}
    with open(_meta_path()) as f:
        return json.load(f)

def _is_cache_fresh(name):
    meta = _read_meta()
    last = pd.Timestamp(meta.get(name, '2000-01-01'))
    return (pd.Timestamp.today().normalize() - last).days <= _STALE_DAYS

def _write_cache(df, name):
    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_parquet(_cache_path(name))
    meta = _read_meta()
    meta[name] = str(df.index[-1].date())
    with open(_meta_path(), 'w') as f:
        json.dump(meta, f)

def _read_cache(name):
    return pd.read_parquet(_cache_path(name))

def download_data(tickers, start, end, force=False):
    """Download daily adjusted close and volume for given tickers (cached)."""
    if not force and _is_cache_fresh('adj_close') and _is_cache_fresh('volume'):
        try:
            adj_close = _read_cache('adj_close')
            volume = _read_cache('volume')
            if not adj_close.empty and adj_close.index[-1] >= pd.Timestamp(end) - pd.Timedelta(days=5):
                print("Using cached stock data.")
                return adj_close, volume
        except (FileNotFoundError, Exception):
            pass
    print("Downloading stock data...")
    data = yf.download(tickers, start=start, end=end, group_by='ticker', auto_adjust=False)
    adj_close = data.xs('Adj Close', axis=1, level=1).ffill()
    volume = data.xs('Volume', axis=1, level=1).ffill()
    adj_close = adj_close.dropna(axis=1, thresh=int(0.7*len(adj_close)))
    volume = volume[adj_close.columns]
    _write_cache(adj_close, 'adj_close')
    _write_cache(volume, 'volume')
    return adj_close, volume

def download_fx_rates(start, end, force=False):
    """Return DataFrame with columns DKK, SEK, NOK giving USD per foreign unit (cached)."""
    if not force and _is_cache_fresh('fx_rates'):
        try:
            fx = _read_cache('fx_rates')
            if not fx.empty and fx.index[-1] >= pd.Timestamp(end) - pd.Timedelta(days=5):
                print("Using cached FX data.")
                return fx
        except (FileNotFoundError, Exception):
            pass
    print("Downloading FX data...")
    fx_tickers = [v for v in FX_TICKERS.values() if v is not None]
    fx_data = yf.download(fx_tickers, start=start, end=end, group_by='ticker', auto_adjust=True)
    fx_rates = pd.DataFrame()
    for currency, ticker in FX_TICKERS.items():
        if ticker is None:
            fx_rates[currency] = 1.0
            continue
        try:
            series = fx_data.xs('Close', axis=1, level=1)[ticker]
        except KeyError:
            series = fx_data.xs('Adj Close', axis=1, level=1).get(ticker, pd.Series(dtype=float))
        fx_rates[currency] = series.ffill()
    _write_cache(fx_rates, 'fx_rates')
    return fx_rates

def convert_to_usd(adj_close, fx_rates):
    """Multiply each stock's close by its currency's USD rate."""
    fx_rates = fx_rates.reindex(adj_close.index, method='ffill')
    cols = {}
    for ticker in adj_close.columns:
        currency = CURRENCY_MAP.get(ticker, 'USD')
        rate = fx_rates.get(currency, 1.0)
        cols[ticker] = adj_close[ticker] * rate
    return pd.concat(cols, axis=1)
