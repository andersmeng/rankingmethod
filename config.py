

# ---- Universe ----
# United States (large-cap, high liquidity)
US_TICKERS = [
    'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'TSLA', 'NVDA', 'JPM', 'V',
    'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 'DIS', 'ADBE', 'NFLX', 'CRM',
    'AMD', 'BAC', 'KO', 'PEP', 'TMO', 'ABT', 'DHR', 'NKE', 'ORCL', 'CSCO',
    'INTC', 'QCOM', 'TXN', 'AMGN', 'INTU', 'AMAT', 'LOW', 'SBUX', 'MDT',
    'BMY', 'GILD', 'ADP', 'ISRG', 'BKNG', 'VRTX', 'REGN', 'MDLZ', 'ADSK',
    'NOW', 'LRCX', 'MU', 'CSX', 'CHTR', 'PYPL', 'ASML', 'SNPS', 'CDNS',
    'MRNA', 'FTNT', 'KLAC', 'MAR', 'CRWD', 'MRVL', 'DXCM', 'IDXX', 'CTAS',
    'KDP', 'A', 'ALGN', 'ANET', 'APH', 'AZO', 'BIIB', 'BSX', 'CAT', 'CI',
    'CMCSA', 'COST', 'CPRT', 'CTSH', 'DE', 'DLTR', 'EA', 'EBAY', 'F', 'FAST',
    'FDX', 'GD', 'GE', 'GM', 'GOOG', 'HON', 'HSY', 'IBM', 'ILMN', 'ITW',
    'KMB', 'LMT', 'MCHP', 'MMM', 'MNST', 'MS', 'MSI', 'NSC', 'OXY', 'PANW',
    'PCAR', 'PLD', 'PSA', 'ROST', 'SCHW', 'SO', 'SPGI', 'T', 'TGT', 'TJX',
    'TMUS', 'TSCO', 'TT', 'UBER', 'UNP', 'UPS', 'USB', 'VLO', 'VZ', 'WFC',
    'XEL', 'ZTS'
]

# Denmark (OMXC25 constituents, .CO suffix)
DK_TICKERS = [
    'NOVO-B.CO',   # Novo Nordisk B
    'DSV.CO',      # DSV Panalpina
    'DANSKE.CO',   # Danske Bank
    'VWS.CO',      # Vestas Wind Systems
    'ORSTED.CO',   # Ørsted
    'GMAB.CO',     # Genmab
    'COLO-B.CO',   # Coloplast B
    'TRYG.CO',     # Tryg
    'ISS.CO',      # ISS
    'CARL-B.CO',   # Carlsberg B
    'MAERSK-B.CO', # A.P. Moller-Maersk B
    'PNDORA.CO',   # Pandora
    'ROCK-B.CO',   # Rockwool B
    'DEMANT.CO',   # Demant
    'AMBU-B.CO',   # Ambu B
    'FLS.CO',      # FLSmidth
    'GN.CO',       # GN Store Nord
    'HLUN-A.CO'    # H. Lundbeck A
]

# Sweden (OMXS30 constituents, .ST suffix)
SE_TICKERS = [
    'ATCO-A.ST',   # Atlas Copco A
    'VOLV-B.ST',   # Volvo B
    'ERIC-B.ST',   # Ericsson B
    'SAND.ST',     # Sandvik
    'HM-B.ST',     # H&M B
    'INVE-B.ST',   # Investor B
    'SEB-A.ST',    # SEB A
    'SWED-A.ST',   # Swedbank A
    'SHB-A.ST',    # Handelsbanken A
    'TEL2-B.ST',   # Tele2 B
    'ESSITY-B.ST', # Essity B
    'SCA-B.ST',    # SCA B
    'ELUX-B.ST',   # Electrolux B
    'SKF-B.ST',    # SKF B
    'ALFA.ST',     # Alfa Laval
    'ASSA-B.ST',   # Assa Abloy B
    'HEXA-B.ST',   # Hexagon B
    'NIBE-B.ST',   # Nibe Industrier B
    'TELIA.ST',    # Telia Company
]

# Norway (OBX25 constituents, .OL suffix)
NO_TICKERS = [
    'EQNR.OL',     # Equinor
    'DNB.OL',      # DNB
    'TEL.OL',      # Telenor
    'YAR.OL',      # Yara International
    'NHY.OL',      # Norsk Hydro
    'MOWI.OL',     # Mowi
    'ORK.OL',      # Orkla
    'SALM.OL',     # SalMar
    'BAKKA.OL',    # Bakkafrost
    'SUBC.OL',     # Subsea 7
    'STB.OL',      # Storebrand
    'KOG.OL',      # Kongsberg Gruppen
    'RECSI.OL',    # REC Silicon (less liquid, use with caution)
    'TGS.OL',      # TGS
    'PGS.OL',      # PGS (Petroleum Geo-Services)
    'AUSS.OL',     # Austevoll Seafood
    'WWI.OL',      # Wilh. Wilhelmsen
    'BWO.OL'       # BW Offshore
]

# Combine
ALL_TICKERS = US_TICKERS + DK_TICKERS + SE_TICKERS + NO_TICKERS

# ---- Sector map (broad categories for diversification) ----
SECTOR_MAP = {
    # US - Technology
    'AAPL': 'TECH', 'MSFT': 'TECH', 'ADBE': 'TECH', 'CRM': 'TECH',
    'NOW': 'TECH', 'INTU': 'TECH', 'ADSK': 'TECH', 'CTSH': 'TECH',
    'FTNT': 'TECH', 'PANW': 'TECH', 'CRWD': 'TECH', 'MSI': 'TECH',
    # US - Semiconductors
    'NVDA': 'SEMI', 'AMD': 'SEMI', 'INTC': 'SEMI', 'QCOM': 'SEMI',
    'TXN': 'SEMI', 'AMAT': 'SEMI', 'LRCX': 'SEMI', 'MU': 'SEMI',
    'KLAC': 'SEMI', 'MRVL': 'SEMI', 'ASML': 'SEMI', 'SNPS': 'SEMI',
    'CDNS': 'SEMI', 'MCHP': 'SEMI',
    # US - Consumer Cyclical
    'AMZN': 'CONS_CYCL', 'TSLA': 'CONS_CYCL', 'HD': 'CONS_CYCL',
    'NKE': 'CONS_CYCL', 'SBUX': 'CONS_CYCL', 'BKNG': 'CONS_CYCL',
    'MAR': 'CONS_CYCL', 'LOW': 'CONS_CYCL', 'ROST': 'CONS_CYCL',
    'TJX': 'CONS_CYCL', 'TGT': 'CONS_CYCL', 'DLTR': 'CONS_CYCL',
    'EBAY': 'CONS_CYCL', 'EA': 'CONS_CYCL', 'TSCO': 'CONS_CYCL',
    'F': 'CONS_CYCL', 'GM': 'CONS_CYCL', 'AZO': 'CONS_CYCL',
    # US - Consumer Defensive
    'PG': 'CONS_DEF', 'KO': 'CONS_DEF', 'PEP': 'CONS_DEF',
    'WMT': 'CONS_DEF', 'COST': 'CONS_DEF', 'HSY': 'CONS_DEF',
    'KDP': 'CONS_DEF', 'KMB': 'CONS_DEF', 'MDLZ': 'CONS_DEF',
    'MNST': 'CONS_DEF',
    # US - Financial
    'JPM': 'FIN', 'V': 'FIN', 'MA': 'FIN', 'BAC': 'FIN',
    'MS': 'FIN', 'SCHW': 'FIN', 'USB': 'FIN', 'WFC': 'FIN',
    'SPGI': 'FIN', 'PYPL': 'FIN',
    # US - Healthcare
    'JNJ': 'HC', 'UNH': 'HC', 'ABT': 'HC', 'TMO': 'HC',
    'DHR': 'HC', 'AMGN': 'HC', 'BMY': 'HC', 'GILD': 'HC',
    'VRTX': 'HC', 'REGN': 'HC', 'MRNA': 'HC', 'BIIB': 'HC',
    'ISRG': 'HC', 'ZTS': 'HC', 'IDXX': 'HC', 'DXCM': 'HC',
    'ILMN': 'HC', 'BSX': 'HC', 'MDT': 'HC', 'CI': 'HC',
    'ALGN': 'HC', 'A': 'HC',
    # US - Communication
    'META': 'COMMS', 'GOOGL': 'COMMS', 'GOOG': 'COMMS',
    'DIS': 'COMMS', 'NFLX': 'COMMS', 'CMCSA': 'COMMS',
    'CHTR': 'COMMS', 'T': 'COMMS', 'VZ': 'COMMS', 'TMUS': 'COMMS',
    # US - Industrial
    'CAT': 'IND', 'DE': 'IND', 'GE': 'IND', 'HON': 'IND',
    'UPS': 'IND', 'UNP': 'IND', 'FDX': 'IND', 'LMT': 'IND',
    'GD': 'IND', 'MMM': 'IND', 'ITW': 'IND', 'CSX': 'IND',
    'NSC': 'IND', 'CPRT': 'IND', 'FAST': 'IND', 'PCAR': 'IND',
    'TT': 'IND', 'CTAS': 'IND',
    # US - Energy
    'OXY': 'ENERGY', 'VLO': 'ENERGY',
    # US - Utilities
    'SO': 'UTIL', 'XEL': 'UTIL',
    # US - Real Estate
    'PLD': 'RE', 'PSA': 'RE',
    # Denmark
    'NOVO-B.CO': 'HC', 'DSV.CO': 'IND', 'DANSKE.CO': 'FIN',
    'VWS.CO': 'ENERGY', 'ORSTED.CO': 'UTIL', 'GMAB.CO': 'HC',
    'COLO-B.CO': 'HC', 'TRYG.CO': 'FIN', 'ISS.CO': 'IND',
    'CARL-B.CO': 'CONS_DEF', 'MAERSK-B.CO': 'IND',
    'PNDORA.CO': 'CONS_CYCL', 'ROCK-B.CO': 'IND',
    'DEMANT.CO': 'HC', 'AMBU-B.CO': 'HC', 'FLS.CO': 'IND',
    'GN.CO': 'HC', 'HLUN-A.CO': 'HC',
    # Sweden
    'ATCO-A.ST': 'IND', 'VOLV-B.ST': 'IND', 'ERIC-B.ST': 'TECH',
    'SAND.ST': 'IND', 'HM-B.ST': 'CONS_CYCL', 'INVE-B.ST': 'FIN',
    'SEB-A.ST': 'FIN', 'SWED-A.ST': 'FIN', 'SHB-A.ST': 'FIN',
    'TEL2-B.ST': 'COMMS', 'ESSITY-B.ST': 'CONS_DEF',
    'SCA-B.ST': 'BASIC', 'ELUX-B.ST': 'CONS_CYCL',
    'SKF-B.ST': 'IND', 'ALFA.ST': 'IND', 'ASSA-B.ST': 'IND',
    'HEXA-B.ST': 'TECH', 'NIBE-B.ST': 'IND', 'TELIA.ST': 'COMMS',
    # Norway
    'EQNR.OL': 'ENERGY', 'DNB.OL': 'FIN', 'TEL.OL': 'COMMS',
    'YAR.OL': 'BASIC', 'NHY.OL': 'BASIC', 'MOWI.OL': 'CONS_DEF',
    'ORK.OL': 'CONS_DEF', 'SALM.OL': 'CONS_DEF',
    'BAKKA.OL': 'CONS_DEF', 'SUBC.OL': 'ENERGY',
    'STB.OL': 'FIN', 'KOG.OL': 'IND', 'RECSI.OL': 'SEMI',
    'TGS.OL': 'ENERGY', 'PGS.OL': 'ENERGY', 'AUSS.OL': 'CONS_DEF',
    'WWI.OL': 'IND', 'BWO.OL': 'ENERGY',
}

SECTOR_LIMIT = 1  # max positions per sector

# ---- Timeframe (computed dynamically) ----
import pandas as pd
from pandas.tseries.offsets import BDay, Week

_today = pd.Timestamp.today().normalize()
_last_trading_day = _today - BDay(1)
_next_monday = _today + Week(weekday=0)

TRAIN_START_DATE = '2018-01-01'
TRAIN_END_DATE   = str(_today.date())                # exclusive for yfinance, so data up to last trading day
TRADE_START_DATE = str(_next_monday.date())           # next Monday
END_DATE         = str(_last_trading_day.date())      # last trading day

# ---- Strategy parameters ----
MOMENTUM_WINDOW    = 252
RANKING_METHOD     = 'momentum'
STOP_N             = 6
REBALANCE_FREQUENCY = 'M'
LONG_ONLY          = True

# ---- Filters & risk constraints ----
MIN_DAILY_VOLUME   = 100_000
MIN_MARKET_CAP     = 1e9
MAX_POSITION_WEIGHT = 1.0 / STOP_N
COMMISSION         = 0.001
SLIPPAGE           = 0.001

# ---- Currency mapping ----
# (generated automatically as before)
# Currency mapping (auto‑generated)
CURRENCY_MAP = {}
for t in US_TICKERS: CURRENCY_MAP[t] = 'USD'
for t in DK_TICKERS: CURRENCY_MAP[t] = 'DKK'
for t in SE_TICKERS: CURRENCY_MAP[t] = 'SEK'
for t in NO_TICKERS: CURRENCY_MAP[t] = 'NOK'


# Forex tickers for currency conversion (all to USD)
FX_TICKERS = {
    'DKK': 'DKKUSD=X',
    'SEK': 'SEKUSD=X',
    'NOK': 'NOKUSD=X',
    'USD': None        # base currency, no conversion needed
}

# ---- Walk-forward training ----
PANEL_START_DATE  = str((pd.Timestamp(TRAIN_START_DATE) + pd.DateOffset(years=1)).date())  # 2019-01-01, needs 1yr lookback
INITIAL_TRAIN_MONTHS = 36   # 3 years of initial training
TEST_MONTHS          = 6    # 6-month test window
PURGE_MONTHS         = 3    # gap to avoid look-ahead bias
FEATURE_COLS = ['mom_12_1', 'rev_5', 'vol_20', 'log_dollar_vol', 'ppo_hist']

# Fixed composite weights (used when scoring with RANKING_METHOD='composite')
COMPOSITE_WEIGHTS = {
    'mom_12_1': 0.50,
    'rev_5': 0.20,
    'vol_20': -0.15,
    'log_dollar_vol': 0.10,
    'ppo_hist': 0.05,
}

# ---- LightGBM parameters ----
LGB_PARAMS = {
    'objective': 'lambdarank',
    'metric': 'ndcg',
    'boosting_type': 'gbdt',
    'num_leaves': 15,
    'learning_rate': 0.03,
    'n_estimators': 500,
    'min_child_samples': 30,
    'reg_alpha': 0.01,
    'reg_lambda': 0.01,
    'subsample': 0.8,
    'feature_fraction': 0.8,
    'label_gain': list(range(101)),
}

ENSEMBLE_SIZE = 3   # number of LGBM models trained per window with different seeds
SEED_BASE = 42      # seeds are SEED_BASE, SEED_BASE+1, ..., SEED_BASE+ENSEMBLE_SIZE-1

# ---- Model paths ----
MODEL_PATH  = 'model.joblib'
SCALER_PATH = 'scaler.joblib'

# ---- Monitor settings ----
MONITOR_LOOKBACK_YEARS = 3
CORR_THRESH = 0.85
N_STOCKS    = 6
PORTFOLIO_FILE = 'current_portfolio.json'
PERSIST_BONUS = 0.10  # score boost for currently held stocks at rebalance

# ---- Stop-loss settings ----
# 'volatility': dynamic stop based on recent vol (n * sigma)
# 'fixed': fixed percentage stop
STOP_LOSS_TYPE = 'volatility'
STOP_LOSS_PCT  = 0.05
STOP_N_SIGMA   = 2.5
CAPITAL_PER_POSITION = 10000    # hypothetical capital per position for share calc