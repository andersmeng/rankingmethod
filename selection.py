import pandas as pd
from config import SECTOR_MAP, SECTOR_LIMIT, CORR_THRESH, N_STOCKS, FEATURE_COLS, COMPOSITE_WEIGHTS


def get_correlation(t1, t2, close_df, lookback=60):
    ret1 = close_df[t1].pct_change().dropna()
    ret2 = close_df[t2].pct_change().dropna()
    common = ret1.index.intersection(ret2.index)
    if len(common) < 30:
        return 0.0
    return ret1.loc[common[-lookback:]].corr(ret2.loc[common[-lookback:]])


def composite_score(feat_df):
    """Score stocks using a fixed composite formula (no ML needed)."""
    if 'score' in feat_df.columns:
        return feat_df
    score = pd.Series(0.0, index=feat_df.index)
    for col, w in COMPOSITE_WEIGHTS.items():
        if col in feat_df.columns:
            score += feat_df[col].fillna(0) * w
    result = feat_df.copy()
    result['score'] = score
    return result.sort_values('score', ascending=False)


def select_picks(feat_df, adj_close, n_stocks=None, corr_thresh=None,
                 sector_map=None, sector_limit=None,
                 persist_tickers=None, persist_bonus=None):
    if n_stocks is None:
        n_stocks = N_STOCKS
    if corr_thresh is None:
        corr_thresh = CORR_THRESH
    if sector_map is None:
        sector_map = SECTOR_MAP
    if sector_limit is None:
        sector_limit = SECTOR_LIMIT

    df = feat_df.copy()
    if persist_tickers and 'score' in df.columns and persist_bonus is not None:
        for t in persist_tickers:
            if t in df.index:
                df.loc[t, 'score'] += persist_bonus
        df = df.sort_values('score', ascending=False)

    selected = []
    sector_count = {}

    for ticker in df.index:
        if ticker not in adj_close.columns:
            continue
        sector = sector_map.get(ticker, 'OTHER')
        if sector_count.get(sector, 0) >= sector_limit:
            continue
        include = True
        for s in selected:
            if abs(get_correlation(ticker, s, adj_close)) > corr_thresh:
                include = False
                break
        if include:
            selected.append(ticker)
            sector_count[sector] = sector_count.get(sector, 0) + 1
        if len(selected) >= n_stocks:
            break

    return selected
