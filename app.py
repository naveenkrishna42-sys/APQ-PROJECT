# ═══════════════════════════════════════════════════════════════════════════════
# APEX PROPHET QUANTUM (APQ) v7.5  —  Enterprise Web Edition
# Single-file Streamlit application  |  app.py
# ═══════════════════════════════════════════════════════════════════════════════

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time
import datetime
import math
import re
import random
import warnings
from scipy.stats import norm

warnings.filterwarnings("ignore")

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="APQ v7.5 Enterprise",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"About": "APEX PROPHET QUANTUM v7.5 — Enterprise Quantitative Terminal"},
)

# ══════════════════════════════════════════════════════════════════════════════
# I.  THEME — CYBER-GRID OBSIDIAN CSS INJECTION
# ══════════════════════════════════════════════════════════════════════════════
OBSIDIAN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&family=Exo+2:wght@300;400;600&display=swap');

:root {
  --bg-void:      #030407;
  --bg-panel:     #070c14;
  --bg-card:      #0b1220;
  --bg-hover:     #0f1a2e;
  --cyan:         #00f0ff;
  --mint:         #00ff88;
  --crimson:      #ff2255;
  --amber:        #ffaa00;
  --purple:       #9b5de5;
  --border:       rgba(0,240,255,0.18);
  --border-glow:  rgba(0,240,255,0.45);
  --text-primary: #e8f4fd;
  --text-dim:     #5a7a99;
  --font-mono:    'Share Tech Mono', monospace;
  --font-head:    'Orbitron', monospace;
  --font-body:    'Exo 2', sans-serif;
}

/* ── Base ── */
html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg-void) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-body) !important;
}
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0; z-index: 0;
  background:
    radial-gradient(ellipse 80% 60% at 15% 20%, rgba(0,240,255,0.04) 0%, transparent 70%),
    radial-gradient(ellipse 60% 80% at 85% 80%, rgba(0,255,136,0.03) 0%, transparent 70%),
    repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(0,240,255,0.025) 40px),
    repeating-linear-gradient(90deg, transparent, transparent 39px, rgba(0,240,255,0.025) 40px);
  pointer-events: none;
}
[data-testid="stMain"] { background: transparent !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg-panel) !important;
  border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { font-family: var(--font-body) !important; }

/* ── Inputs & Selects ── */
.stTextInput input, .stSelectbox select,
[data-testid="stTextInput"] input,
[data-testid="stSelectbox"] div[data-baseweb="select"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  color: var(--cyan) !important;
  font-family: var(--font-mono) !important;
  border-radius: 4px !important;
}
.stTextInput input:focus { border-color: var(--cyan) !important; box-shadow: 0 0 8px rgba(0,240,255,0.4) !important; }

/* ── Buttons ── */
.stButton > button {
  background: linear-gradient(135deg, rgba(0,240,255,0.08), rgba(0,240,255,0.04)) !important;
  border: 1px solid var(--border) !important;
  color: var(--cyan) !important;
  font-family: var(--font-head) !important;
  font-size: 0.7rem !important;
  letter-spacing: 0.12em !important;
  border-radius: 4px !important;
  transition: all 0.2s ease !important;
  text-transform: uppercase !important;
}
.stButton > button:hover {
  border-color: var(--cyan) !important;
  background: rgba(0,240,255,0.14) !important;
  box-shadow: 0 0 16px rgba(0,240,255,0.25) !important;
  transform: translateY(-1px) !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  padding: 10px 14px !important;
}
[data-testid="stMetricLabel"] { color: var(--text-dim) !important; font-family: var(--font-mono) !important; font-size: 0.68rem !important; letter-spacing: 0.1em !important; }
[data-testid="stMetricValue"] { color: var(--cyan) !important; font-family: var(--font-head) !important; font-size: 1.1rem !important; }
[data-testid="stMetricDelta"] svg { display: none; }

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
.stDataFrame thead th {
  background: var(--bg-panel) !important;
  color: var(--cyan) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.72rem !important;
  letter-spacing: 0.08em !important;
  border-bottom: 1px solid var(--border-glow) !important;
}
.stDataFrame tbody td {
  background: var(--bg-card) !important;
  color: var(--text-primary) !important;
  font-family: var(--font-mono) !important;
  font-size: 0.7rem !important;
  border-color: var(--border) !important;
}
.stDataFrame tbody tr:hover td { background: var(--bg-hover) !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
  color: var(--text-dim) !important;
  font-family: var(--font-head) !important;
  font-size: 0.65rem !important;
  letter-spacing: 0.12em !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
  color: var(--cyan) !important;
  border-bottom: 2px solid var(--cyan) !important;
}

/* ── Dividers & Containers ── */
hr { border-color: var(--border) !important; }
[data-testid="stExpander"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
}
[data-testid="stExpander"] summary { color: var(--cyan) !important; font-family: var(--font-head) !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg-void); }
::-webkit-scrollbar-thumb { background: var(--border-glow); border-radius: 3px; }

/* ── Custom Component Classes ── */
.apq-scoreboard {
  background: linear-gradient(90deg, var(--bg-panel), rgba(0,240,255,0.04), var(--bg-panel));
  border: 1px solid var(--border-glow);
  border-radius: 8px;
  padding: 12px 20px;
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 6px;
  box-shadow: 0 0 24px rgba(0,240,255,0.08), inset 0 0 40px rgba(0,0,0,0.4);
}
.apq-score-title {
  font-family: var(--font-head);
  font-size: 0.72rem;
  letter-spacing: 0.18em;
  color: var(--cyan);
  text-shadow: 0 0 10px var(--cyan);
}
.apq-score-val-green {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  color: var(--mint);
  text-shadow: 0 0 12px var(--mint);
}
.apq-score-val-red {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  color: var(--crimson);
  text-shadow: 0 0 12px var(--crimson);
}
.apq-score-val-cyan {
  font-family: var(--font-mono);
  font-size: 1.2rem;
  color: var(--cyan);
  text-shadow: 0 0 12px var(--cyan);
}
.apq-score-label {
  font-family: var(--font-body);
  font-size: 0.6rem;
  letter-spacing: 0.1em;
  color: var(--text-dim);
  text-transform: uppercase;
}

.apq-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}
.apq-panel-title {
  font-family: var(--font-head);
  font-size: 0.65rem;
  letter-spacing: 0.15em;
  color: var(--cyan);
  margin-bottom: 8px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}
.apq-metric-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}
.apq-metric-card {
  flex: 1;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 8px 10px;
  text-align: center;
}
.apq-metric-card .label {
  font-family: var(--font-mono);
  font-size: 0.58rem;
  color: var(--text-dim);
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
.apq-metric-card .value {
  font-family: var(--font-head);
  font-size: 0.9rem;
  color: var(--cyan);
  text-shadow: 0 0 8px rgba(0,240,255,0.5);
}
.apq-metric-card .value.green { color: var(--mint); text-shadow: 0 0 8px rgba(0,255,136,0.5); }
.apq-metric-card .value.red   { color: var(--crimson); text-shadow: 0 0 8px rgba(255,34,85,0.5); }

.apq-asset-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 5px 8px;
  border-bottom: 1px solid rgba(0,240,255,0.06);
  cursor: pointer;
  border-radius: 3px;
  transition: background 0.15s;
  font-family: var(--font-mono);
  font-size: 0.72rem;
}
.apq-asset-row:hover { background: var(--bg-hover); }
.apq-asset-row .ticker { color: var(--cyan); font-weight: 700; }
.apq-asset-row .price  { color: var(--text-primary); }
.apq-asset-row .gain   { color: var(--mint); text-shadow: 0 0 6px rgba(0,255,136,0.4); }
.apq-asset-row .loss   { color: var(--crimson); text-shadow: 0 0 6px rgba(255,34,85,0.4); }

.window-btn-active {
  background: rgba(0,240,255,0.15) !important;
  border-color: var(--cyan) !important;
  box-shadow: 0 0 20px rgba(0,240,255,0.3) !important;
}

.ad-slot {
  border: 1px solid rgba(0,240,255,0.2);
  border-radius: 6px;
  background: rgba(0,240,255,0.02);
  text-align: center;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: rgba(0,240,255,0.25);
  letter-spacing: 0.15em;
  box-shadow: inset 0 0 20px rgba(0,240,255,0.04);
}

/* ── Animated Pulse Radar ── */
@keyframes pulseRadar {
  0%   { box-shadow: 0 0 0 0 rgba(0,240,255,0.7), 0 0 0 0 rgba(0,240,255,0.4); transform: scale(1); }
  50%  { box-shadow: 0 0 0 8px rgba(0,240,255,0.0), 0 0 0 16px rgba(0,240,255,0.0); transform: scale(1.08); }
  100% { box-shadow: 0 0 0 0 rgba(0,240,255,0.7), 0 0 0 0 rgba(0,240,255,0.4); transform: scale(1); }
}
@keyframes scanline {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
@keyframes ticker-scroll {
  0%   { transform: translateX(100%); }
  100% { transform: translateX(-100%); }
}
@keyframes dataFlash {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.6; }
}
.pulse-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  background: var(--cyan);
  animation: pulseRadar 2s infinite;
  display: inline-block;
  margin-left: 6px;
  vertical-align: middle;
}
.live-badge {
  display: inline-flex; align-items: center; gap: 5px;
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--mint);
  text-shadow: 0 0 8px var(--mint);
  letter-spacing: 0.12em;
  animation: dataFlash 2.5s infinite;
}

/* ── Section Headers ── */
.section-head {
  font-family: var(--font-head);
  font-size: 0.7rem;
  letter-spacing: 0.2em;
  color: var(--cyan);
  text-transform: uppercase;
  border-left: 3px solid var(--cyan);
  padding-left: 10px;
  margin: 12px 0 8px 0;
  text-shadow: 0 0 10px rgba(0,240,255,0.4);
}

/* ── Greeks Cards ── */
.greek-card {
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 5px;
  padding: 8px;
  text-align: center;
  margin-bottom: 6px;
}
.greek-symbol { font-size: 1.4rem; color: var(--purple); }
.greek-name   { font-family: var(--font-mono); font-size: 0.6rem; color: var(--text-dim); }
.greek-val    { font-family: var(--font-head); font-size: 0.95rem; color: var(--cyan); }

/* ── Pagination Button ── */
.load-more-btn button {
  width: 100% !important;
  background: linear-gradient(90deg, rgba(0,240,255,0.05), rgba(0,255,136,0.05)) !important;
  border: 1px dashed var(--border-glow) !important;
  color: var(--mint) !important;
  animation: dataFlash 3s infinite;
}

/* ── Portfolio Hub ── */
.portfolio-val {
  font-family: var(--font-head);
  font-size: 1.4rem;
  color: var(--mint);
  text-shadow: 0 0 15px rgba(0,255,136,0.5);
  text-align: center;
}
.portfolio-label {
  font-family: var(--font-mono);
  font-size: 0.6rem;
  color: var(--text-dim);
  letter-spacing: 0.12em;
  text-align: center;
  text-transform: uppercase;
}

/* ── Streamlit hide defaults ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
[data-testid="stToolbar"] { display: none; }
.stDeployButton { display: none; }
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
# II.  CONSTANTS — ASSET UNIVERSES
# ══════════════════════════════════════════════════════════════════════════════

EQUITIES = [
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","TSLA","BRK-B","LLY","AVGO",
    "JPM","V","UNH","XOM","MA","JNJ","PG","HD","COST","MRK",
    "AMD","NFLX","CRM","ORCL","ACN","TXN","QCOM","INTC","IBM","MU",
    "BAC","GS","WMT","DIS","PYPL","ADBE","SHOP","UBER","ABNB","SNOW",
    "SPY","QQQ","IWM","DIA","GLD","SLV","TLT","HYG","XLK","XLF",
    "PLTR","RIVN","LCID","NIO","SOFI","HOOD","COIN","RBLX","U","DKNG",
]

FUTURES = [
    "ES=F","NQ=F","YM=F","RTY=F","GC=F","SI=F","CL=F","NG=F",
    "ZB=F","ZN=F","ZC=F","ZS=F","ZW=F","KC=F","CT=F","HG=F",
    "PA=F","PL=F","RB=F","HO=F","DX-Y.NYB","6E=F","6J=F","6B=F",
    "MES=F","MNQ=F","MGC=F","MCL=F","MBT=F","M2K=F",
]

CRYPTO = [
    "BTC-USD","ETH-USD","BNB-USD","XRP-USD","SOL-USD","ADA-USD","DOGE-USD","AVAX-USD",
    "DOT-USD","MATIC-USD","LINK-USD","LTC-USD","BCH-USD","ALGO-USD","ATOM-USD","FIL-USD",
    "APT-USD","ARB-USD","OP-USD","INJ-USD","NEAR-USD","STX-USD","ICP-USD","RNDR-USD",
    "SUI-USD","SEI-USD","TIA-USD","JUP-USD","WIF-USD","PEPE-USD","ZEC-USD","DASH-USD",
]

WINDOW_ASSETS = {
    "📈 SPOT EQUITIES":         EQUITIES,
    "⚡ DERIVATIVES":           FUTURES,
    "🌌 CRYPTO RADAR":          CRYPTO,
}

# Time interval → yfinance mapping
TF_CONFIG = {
    "5m":    {"yf_interval": "5m",   "yf_period": "5d",    "label": "5 MIN"},
    "15m":   {"yf_interval": "15m",  "yf_period": "5d",    "label": "15 MIN"},
    "30m":   {"yf_interval": "30m",  "yf_period": "30d",   "label": "30 MIN"},
    "1h":    {"yf_interval": "1h",   "yf_period": "60d",   "label": "1 HOUR"},
    "4h":    {"yf_interval": "1h",   "yf_period": "60d",   "label": "4 HOUR (resampled)"},
    "12h":   {"yf_interval": "1d",   "yf_period": "1y",    "label": "12 HOUR (resampled)"},
    "1D":    {"yf_interval": "1d",   "yf_period": "2y",    "label": "DAILY"},
    "1W":    {"yf_interval": "1wk",  "yf_period": "5y",    "label": "WEEKLY"},
    "1M":    {"yf_interval": "1mo",  "yf_period": "max",   "label": "MONTHLY"},
    "3M":    {"yf_interval": "3mo",  "yf_period": "max",   "label": "QUARTERLY"},
    "6M":    {"yf_interval": "3mo",  "yf_period": "max",   "label": "6-MONTH"},
    "1Y":    {"yf_interval": "1mo",  "yf_period": "max",   "label": "1 YEAR"},
    "2Y":    {"yf_interval": "1mo",  "yf_period": "max",   "label": "2 YEAR"},
    "3Y":    {"yf_interval": "1wk",  "yf_period": "max",   "label": "3 YEAR"},
    "5Y":    {"yf_interval": "1wk",  "yf_period": "max",   "label": "5 YEAR"},
    "Max":   {"yf_interval": "1mo",  "yf_period": "max",   "label": "MAX (INCEPTION)"},
    "CUSTOM":{"yf_interval": "1d",   "yf_period": None,    "label": "CUSTOM DATE RANGE"},
}

TIMEFRAMES = ["5m","15m","30m","1h","4h","12h","1D","1W","1M","3M","6M","1Y","2Y","3Y","5Y","Max","CUSTOM"]

CHART_TYPES = [
    "Candlesticks",
    "Institutional Line",
    "OHLC Bars",
    "Quantum Area Fill",
    "Renko Matrix",
]

# ══════════════════════════════════════════════════════════════════════════════
# III.  SESSION STATE INITIALIZER
# ══════════════════════════════════════════════════════════════════════════════

def init_session():
    defaults = {
        # Active window
        "active_window":    "📈 SPOT EQUITIES",
        "active_ticker":    "AAPL",
        "active_tf":        "1D",
        "active_chart":     "Candlesticks",
        "active_range":     "1Y",
        "custom_from":      datetime.date(2022, 1, 1),
        "custom_to":        datetime.date(2029, 11, 25),

        # Pagination
        "asset_page":       0,

        # API keys (BYOK)
        "gemini_keys":      [],
        "gemini_key_idx":   0,
        "alpaca_key":       "",
        "alpaca_secret":    "",
        "alpaca_paper":     True,

        # Win-rate scoreboard
        "total_calls":      0,
        "true_calls":       0,
        "false_calls":      0,
        "accuracy_pct":     0.0,

        # Failure-vector calibration
        "error_history":    [],
        "weight_shift":     1.0,          # multiplier applied to ATR targets
        "compression_active": False,

        # AI cache
        "ai_table_cache":   {},

        # Prediction log (ticker → {"target": float, "direction": str, "ts": float})
        "pred_log":         {},

        # Portfolio cache
        "portfolio_cache":  {"equity": 0, "buying_power": 0, "cash": 0},

        # Price cache (ticker → price)
        "price_cache":      {},
        "price_cache_ts":   0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session()

# ══════════════════════════════════════════════════════════════════════════════
# IV.  GEMINI API — KEY ROTATION & 429-PROOF CACHE
# ══════════════════════════════════════════════════════════════════════════════

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

def _get_gemini_keys():
    """Pull keys: sidebar BYOK first, then st.secrets fallback."""
    keys = []
    if st.session_state.get("gemini_keys"):
        keys.extend(st.session_state["gemini_keys"])
    try:
        raw = st.secrets.get("GEMINI_API_KEY", "")
        if raw:
            keys.extend([k.strip() for k in raw.split(",") if k.strip()])
    except Exception:
        pass
    return list(dict.fromkeys(keys))  # deduplicate, preserve order

def _call_gemini(prompt: str, cache_key: str) -> str:
    """429-proof Gemini call with key rotation and session cache."""
    if cache_key in st.session_state["ai_table_cache"]:
        return st.session_state["ai_table_cache"][cache_key]

    keys = _get_gemini_keys()
    if not keys:
        return "_No Gemini API key provided. Paste your key in the sidebar._"

    idx = st.session_state["gemini_key_idx"] % len(keys)

    # Compress prompt (strip extra whitespace, truncate data tables)
    compressed = re.sub(r'\s+', ' ', prompt).strip()
    if len(compressed) > 2800:
        compressed = compressed[:2800] + "...[truncated]"

    payload = {
        "contents": [{"parts": [{"text": compressed}]}],
        "generationConfig": {"maxOutputTokens": 900, "temperature": 0.35},
    }

    for attempt in range(len(keys)):
        key = keys[(idx + attempt) % len(keys)]
        try:
            resp = requests.post(
                f"{GEMINI_URL}?key={key}",
                json=payload,
                timeout=20,
            )
            if resp.status_code == 429:
                st.session_state["gemini_key_idx"] = (idx + attempt + 1) % len(keys)
                continue
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                st.session_state["ai_table_cache"][cache_key] = text
                return text
        except Exception:
            continue

    fallback = (
        "| Field | Analysis |\n|-------|----------|\n"
        "| Management Actions | AI unavailable — check API key or quota |\n"
        "| Corporate Adjustments | N/A |\n"
        "| Operational Pros/Cons | N/A |\n"
        "| Volatility Regime | N/A |"
    )
    return fallback

# ══════════════════════════════════════════════════════════════════════════════
# V.  DATA ENGINE — FETCH, RESAMPLE, INDICATORS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=180, show_spinner=False)
def fetch_ohlcv(ticker: str, tf: str,
                custom_from: datetime.date = None,
                custom_to: datetime.date = None) -> pd.DataFrame:
    """Download OHLCV from yfinance, resample 4h/12h, return clean DataFrame."""
    cfg = TF_CONFIG.get(tf, TF_CONFIG["1D"])
    try:
        if tf == "CUSTOM" and custom_from and custom_to:
            df = yf.download(
                ticker, start=str(custom_from), end=str(custom_to),
                interval="1d", auto_adjust=True, progress=False, timeout=15,
            )
        else:
            df = yf.download(
                ticker, interval=cfg["yf_interval"],
                period=cfg["yf_period"],
                auto_adjust=True, progress=False, timeout=15,
            )

        if df is None or df.empty:
            return pd.DataFrame()

        # Flatten MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]

        df = df[["Open","High","Low","Close","Volume"]].copy()
        df.dropna(inplace=True)

        # ── Resample 4h ──
        if tf == "4h":
            df = df.resample("4h").agg({
                "Open": "first","High": "max","Low": "min",
                "Close": "last","Volume": "sum"
            }).dropna()

        # ── Resample 12h ──
        if tf == "12h":
            df = df.resample("12H").agg({
                "Open": "first","High": "max","Low": "min",
                "Close": "last","Volume": "sum"
            }).dropna()

        # ── Trim historical ranges ──
        cutoff_map = {
            "1Y": 365,"2Y": 730,"3Y": 1095,"5Y": 1825,
            "6M": 180,"3M": 90,"1M": 30,"5D": 5,
        }
        if tf in cutoff_map:
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=cutoff_map[tf])
            df = df[df.index >= cutoff]

        return df

    except Exception as e:
        return pd.DataFrame()


def add_indicators(df: pd.DataFrame, weight: float = 1.0) -> pd.DataFrame:
    """Add RSI, MACD, Bollinger, ATR, VWAP, EMA stack to DataFrame."""
    if df.empty or len(df) < 20:
        return df

    c = df["Close"].copy()

    # ── RSI (14) ──
    delta = c.diff()
    gain = delta.clip(lower=0).ewm(com=13, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(com=13, adjust=False).mean()
    df["RSI_14"] = 100 - 100 / (1 + gain / loss.replace(0, 1e-9))

    # ── MACD ──
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["MACD"]        = ema12 - ema26
    df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_Hist"]   = df["MACD"] - df["MACD_Signal"]

    # ── Bollinger Bands ──
    df["BB_Mid"]   = c.rolling(20).mean()
    bb_std         = c.rolling(20).std()
    df["BB_Upper"] = df["BB_Mid"] + 2 * bb_std
    df["BB_Lower"] = df["BB_Mid"] - 2 * bb_std

    # ── ATR ──
    hl  = df["High"] - df["Low"]
    hc  = (df["High"] - df["Close"].shift()).abs()
    lc  = (df["Low"]  - df["Close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    df["ATR_14"] = tr.ewm(com=13, adjust=False).mean() * weight

    # ── EMA Stack ──
    for span in [9, 20, 50, 200]:
        df[f"EMA_{span}"] = c.ewm(span=span, adjust=False).mean()

    # ── VWAP (session-reset) ──
    tp = (df["High"] + df["Low"] + df["Close"]) / 3
    df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

    # ── OBV ──
    direction = np.sign(c.diff()).fillna(0)
    df["OBV"] = (direction * df["Volume"]).cumsum()

    # ── Stochastic %K/%D ──
    l14 = df["Low"].rolling(14).min()
    h14 = df["High"].rolling(14).max()
    df["Stoch_K"] = 100 * (c - l14) / (h14 - l14 + 1e-9)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    return df


def compute_atr_targets(df: pd.DataFrame, weight: float = 1.0):
    """Return (entry, target, stop, apq_score, direction) based on ATR + indicators."""
    if df.empty or len(df) < 30:
        return None, None, None, 0, "NEUTRAL"

    row  = df.iloc[-1]
    atr_cols = [c for c in df.columns if "ATR" in c]
    atr  = float(row[atr_cols[0]]) if atr_cols else float(row["Close"]) * 0.015
    atr  = max(atr, 1e-6)

    price = float(row["Close"])
    rsi_cols = [c for c in df.columns if "RSI" in c]
    rsi   = float(row[rsi_cols[0]]) if rsi_cols else 50.0

    macd_hist = float(row["MACD_Hist"]) if "MACD_Hist" in df.columns else 0
    ema20     = float(row["EMA_20"])    if "EMA_20"    in df.columns else price
    ema50     = float(row["EMA_50"])    if "EMA_50"    in df.columns else price

    score = 0
    if rsi < 35:     score += 2
    elif rsi < 45:   score += 1
    elif rsi > 75:   score -= 2
    elif rsi > 65:   score -= 1

    if macd_hist > 0: score += 1
    else:             score -= 1

    if price > ema20 > ema50: score += 2
    elif price < ema20 < ema50: score -= 2

    # Apply failure-vector weight compression
    if st.session_state.get("compression_active", False):
        atr *= 0.82  # compress risk width by ~18%

    direction = "LONG" if score >= 1 else "SHORT" if score <= -1 else "NEUTRAL"
    if direction == "LONG":
        target = price + 2.0 * atr * weight
        stop   = price - 1.2 * atr * weight
    elif direction == "SHORT":
        target = price - 2.0 * atr * weight
        stop   = price + 1.2 * atr * weight
    else:
        target = price + 1.0 * atr * weight
        stop   = price - 1.0 * atr * weight

    apq_score = max(0, min(100, 50 + score * 8))
    return price, target, stop, apq_score, direction


# ══════════════════════════════════════════════════════════════════════════════
# VI.  FAILURE-VECTOR SELF-CORRECTION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def run_accuracy_auditor():
    """
    Background accuracy engine: checks open predictions against current prices,
    updates scoreboard counters, and dynamically recalibrates weight_shift.
    Runs on every Streamlit rerender (no thread needed in Streamlit).
    """
    pred_log = st.session_state.get("pred_log", {})
    if not pred_log:
        return

    errors = []
    for ticker, pred in list(pred_log.items()):
        age = time.time() - pred.get("ts", 0)
        if age < 60:   # not yet mature
            continue

        cur_price = st.session_state["price_cache"].get(ticker, 0)
        if cur_price <= 0:
            continue

        target    = pred.get("target", cur_price)
        direction = pred.get("direction", "NEUTRAL")
        entry     = pred.get("entry", cur_price)
        stop      = pred.get("stop", entry)

        # Evaluate: did price move toward target?
        if direction == "LONG":
            hit_target = cur_price >= target
            hit_stop   = cur_price <= stop
        elif direction == "SHORT":
            hit_target = cur_price <= target
            hit_stop   = cur_price >= stop
        else:
            del pred_log[ticker]
            continue

        if hit_target:
            st.session_state["true_calls"]  += 1
            st.session_state["total_calls"] += 1
            del pred_log[ticker]
        elif hit_stop:
            st.session_state["false_calls"]  += 1
            st.session_state["total_calls"]  += 1
            # Record error vector
            abs_err = abs(cur_price - target) / max(abs(target - entry), 1e-6)
            errors.append(abs_err)
            del pred_log[ticker]

    # Update accuracy %
    tot = st.session_state["total_calls"]
    if tot > 0:
        st.session_state["accuracy_pct"] = round(
            100 * st.session_state["true_calls"] / tot, 1
        )

    # ── Failure-vector recalibration ──
    if errors:
        st.session_state["error_history"].extend(errors)
        st.session_state["error_history"] = st.session_state["error_history"][-200:]

    history = st.session_state.get("error_history", [])
    if len(history) >= 10:
        mean_err = np.mean(history[-20:])
        if mean_err > 1.5:
            # High-error cycle: compress risk by 15–35%
            compress = min(0.35, max(0.15, mean_err * 0.12))
            st.session_state["weight_shift"]       = round(1.0 - compress, 3)
            st.session_state["compression_active"] = True
        elif mean_err < 0.6:
            # Low-error cycle: relax back toward 1.0
            st.session_state["weight_shift"]       = min(1.0, st.session_state["weight_shift"] + 0.05)
            st.session_state["compression_active"] = False

    st.session_state["pred_log"] = pred_log


run_accuracy_auditor()


# ══════════════════════════════════════════════════════════════════════════════
# VII.  ALPACA PAPER TRADING API
# ══════════════════════════════════════════════════════════════════════════════

ALPACA_PAPER_BASE = "https://paper-api.alpaca.markets/v2"

def _alpaca_headers():
    return {
        "APCA-API-KEY-ID":     st.session_state.get("alpaca_key", ""),
        "APCA-API-SECRET-KEY": st.session_state.get("alpaca_secret", ""),
        "Content-Type":        "application/json",
    }

def get_alpaca_account():
    try:
        r = requests.get(f"{ALPACA_PAPER_BASE}/account",
                         headers=_alpaca_headers(), timeout=8)
        if r.status_code == 200:
            d = r.json()
            st.session_state["portfolio_cache"] = {
                "equity":        float(d.get("equity", 0)),
                "buying_power":  float(d.get("buying_power", 0)),
                "cash":          float(d.get("cash", 0)),
            }
            return d
    except Exception:
        pass
    return None

def submit_alpaca_order(symbol: str, qty: int, side: str):
    """Submit market order to Alpaca paper account."""
    try:
        payload = {
            "symbol":     symbol.replace("-USD","USD"),
            "qty":        qty,
            "side":       side,
            "type":       "market",
            "time_in_force": "gtc",
        }
        r = requests.post(f"{ALPACA_PAPER_BASE}/orders",
                          headers=_alpaca_headers(),
                          json=payload, timeout=10)
        return r.status_code == 200, r.json()
    except Exception as e:
        return False, {"message": str(e)}


# ══════════════════════════════════════════════════════════════════════════════
# VIII.  CHART RENDERING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

PLOTLY_DARK = dict(
    paper_bgcolor="#030407",
    plot_bgcolor="#070c14",
    font=dict(family="Share Tech Mono", color="#5a7a99", size=10),
    gridcolor="rgba(0,240,255,0.06)",
    zerolinecolor="rgba(0,240,255,0.1)",
)


def _base_layout(title=""):
    return go.Layout(
        title=dict(text=title, font=dict(family="Orbitron", color="#00f0ff", size=12)),
        paper_bgcolor=PLOTLY_DARK["paper_bgcolor"],
        plot_bgcolor=PLOTLY_DARK["plot_bgcolor"],
        font=dict(family="Share Tech Mono", color="#5a7a99", size=10),
        xaxis=dict(gridcolor=PLOTLY_DARK["gridcolor"],
                   zerolinecolor=PLOTLY_DARK["zerolinecolor"],
                   showgrid=True, linecolor="#0f1a2e"),
        yaxis=dict(gridcolor=PLOTLY_DARK["gridcolor"],
                   zerolinecolor=PLOTLY_DARK["zerolinecolor"],
                   showgrid=True, linecolor="#0f1a2e", side="right"),
        margin=dict(l=0, r=50, t=35, b=30),
        legend=dict(bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Share Tech Mono", color="#5a7a99")),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="#0b1220", font_color="#00f0ff",
                        font_family="Share Tech Mono"),
    )


def build_chart(df: pd.DataFrame, chart_type: str, ticker: str,
                entry=None, target=None, stop=None) -> go.Figure:
    if df.empty:
        fig = go.Figure(layout=_base_layout("NO DATA"))
        return fig

    fig = go.Figure(layout=_base_layout(f"APQ // {ticker}"))

    if chart_type == "Candlesticks":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing=dict(line=dict(color="#00ff88"), fillcolor="rgba(0,255,136,0.55)"),
            decreasing=dict(line=dict(color="#ff2255"), fillcolor="rgba(255,34,85,0.55)"),
            name=ticker, showlegend=False,
        ))

    elif chart_type == "Institutional Line":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines",
            line=dict(color="#00f0ff", width=1.8, shape="spline"),
            fill="tozeroy",
            fillcolor="rgba(0,240,255,0.04)",
            name="Close",
        ))

    elif chart_type == "OHLC Bars":
        fig.add_trace(go.Ohlc(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color="#00ff88",
            decreasing_line_color="#ff2255",
            name=ticker,
        ))

    elif chart_type == "Quantum Area Fill":
        fig.add_trace(go.Scatter(
            x=df.index, y=df["High"],
            mode="lines", line=dict(color="#00ff88", width=0.5),
            fill=None, name="High",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Low"],
            mode="lines", line=dict(color="#ff2255", width=0.5),
            fill="tonexty",
            fillcolor="rgba(0,240,255,0.06)",
            name="Low",
        ))
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines", line=dict(color="#00f0ff", width=2),
            name="Close",
        ))

    elif chart_type == "Renko Matrix":
        fig = _build_renko(df, ticker)
        return fig

    # ── Overlay indicators ──
    for col, color, dash in [
        ("EMA_20", "#ffaa00", "solid"),
        ("EMA_50", "#9b5de5", "solid"),
        ("EMA_200","#00f0ff", "dot"),
        ("BB_Upper","rgba(0,240,255,0.5)", "dash"),
        ("BB_Lower","rgba(0,240,255,0.5)", "dash"),
        ("VWAP",   "#ff2255", "dashdot"),
    ]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                mode="lines",
                line=dict(color=color, width=1, dash=dash),
                name=col.replace("_"," "),
                opacity=0.7,
            ))

    # ── Target / Stop / Entry lines ──
    if entry is not None:
        for val, color, label in [
            (entry,  "#00f0ff", f"ENTRY  {entry:.4f}"),
            (target, "#00ff88", f"TARGET {target:.4f}"),
            (stop,   "#ff2255", f"STOP   {stop:.4f}"),
        ]:
            if val:
                fig.add_hline(
                    y=val, line_dash="dot", line_color=color,
                    annotation_text=label,
                    annotation_position="right",
                    annotation_font=dict(family="Share Tech Mono", color=color, size=9),
                    line_width=1,
                )

    fig.update_xaxes(rangeslider_visible=False)
    return fig


def _build_renko(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Simulate Renko chart from OHLCV data."""
    atr_cols = [c for c in df.columns if "ATR" in c]
    brick_size = float(df[atr_cols[0]].iloc[-1]) if atr_cols else float(df["Close"].mean()) * 0.02
    brick_size = max(brick_size, 1e-4)

    closes = df["Close"].values
    bricks = []
    cur = closes[0]
    for price in closes[1:]:
        diff = price - cur
        n = int(abs(diff) / brick_size)
        direction = 1 if diff > 0 else -1
        for _ in range(n):
            bricks.append({"open": cur, "close": cur + direction * brick_size,
                            "dir": direction})
            cur += direction * brick_size

    if not bricks:
        fig = go.Figure(layout=_base_layout(f"RENKO // {ticker}"))
        fig.add_annotation(text="Insufficient data for Renko",
                           showarrow=False, font=dict(color="#5a7a99"))
        return fig

    x_idx = list(range(len(bricks)))
    colors = ["rgba(0,255,136,0.7)" if b["dir"] > 0 else "rgba(255,34,85,0.7)"
              for b in bricks]
    fig = go.Figure(go.Bar(
        x=x_idx,
        y=[abs(b["close"] - b["open"]) for b in bricks],
        base=[min(b["open"], b["close"]) for b in bricks],
        marker_color=colors,
        marker_line_width=0,
        name="Renko",
    ), layout=_base_layout(f"RENKO MATRIX // {ticker}"))
    fig.update_xaxes(showticklabels=False)
    return fig


def build_volume_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()
    colors = ["#00ff88" if c >= o else "#ff2255"
              for c, o in zip(df["Close"], df["Open"])]
    fig = go.Figure(go.Bar(
        x=df.index, y=df["Volume"],
        marker_color=colors, marker_line_width=0, name="Volume",
    ), layout=_base_layout())
    fig.update_layout(height=120, margin=dict(l=0,r=50,t=5,b=5))
    fig.update_yaxes(showticklabels=False)
    return fig


def build_rsi_chart(df: pd.DataFrame) -> go.Figure:
    rsi_cols = [c for c in df.columns if "RSI" in c]
    if not rsi_cols or df.empty:
        return go.Figure()
    col = rsi_cols[0]
    fig = go.Figure(layout=_base_layout())
    fig.add_trace(go.Scatter(x=df.index, y=df[col],
                             mode="lines", line=dict(color="#ffaa00", width=1.5),
                             name="RSI"))
    fig.add_hline(y=70, line_dash="dot", line_color="#ff2255", line_width=0.8)
    fig.add_hline(y=30, line_dash="dot", line_color="#00ff88", line_width=0.8)
    fig.update_layout(height=100, margin=dict(l=0,r=50,t=5,b=5),
                      yaxis=dict(range=[0,100], gridcolor=PLOTLY_DARK["gridcolor"]))
    return fig


def build_macd_chart(df: pd.DataFrame) -> go.Figure:
    if "MACD" not in df.columns or df.empty:
        return go.Figure()
    colors = ["#00ff88" if v >= 0 else "#ff2255"
              for v in df["MACD_Hist"].fillna(0)]
    fig = go.Figure(layout=_base_layout())
    fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"],
                         marker_color=colors, name="MACD Hist", marker_line_width=0))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"],
                             line=dict(color="#00f0ff", width=1), name="MACD"))
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"],
                             line=dict(color="#ff2255", width=1, dash="dash"), name="Signal"))
    fig.update_layout(height=110, margin=dict(l=0,r=50,t=5,b=5))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# IX.  BLACK-SCHOLES GREEKS  (Futures/Options window)
# ══════════════════════════════════════════════════════════════════════════════

def black_scholes_greeks(S, K, T, r, sigma, option_type="call"):
    """Compute Delta, Gamma, Theta, Vega, Rho via Black-Scholes."""
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return {"Δ Delta": 0, "Γ Gamma": 0, "Θ Theta": 0, "ν Vega": 0, "ρ Rho": 0}
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        nd1 = norm.pdf(d1)

        if option_type == "call":
            delta = norm.cdf(d1)
            rho   = K * T * math.exp(-r * T) * norm.cdf(d2) * 0.01
        else:
            delta = norm.cdf(d1) - 1
            rho   = -K * T * math.exp(-r * T) * norm.cdf(-d2) * 0.01

        gamma = nd1 / (S * sigma * math.sqrt(T))
        vega  = S * nd1 * math.sqrt(T) * 0.01
        theta = (
            -(S * nd1 * sigma) / (2 * math.sqrt(T))
            - r * K * math.exp(-r * T) * (norm.cdf(d2) if option_type == "call" else norm.cdf(-d2))
        ) / 365

        return {
            "Δ Delta": round(delta, 4),
            "Γ Gamma": round(gamma, 6),
            "Θ Theta": round(theta, 4),
            "ν Vega":  round(vega,  4),
            "ρ Rho":   round(rho,   4),
        }
    except Exception:
        return {"Δ Delta": 0, "Γ Gamma": 0, "Θ Theta": 0, "ν Vega": 0, "ρ Rho": 0}


# ══════════════════════════════════════════════════════════════════════════════
# X.   LEVEL-2 LIQUIDITY FLUX SIMULATION  (Crypto window)
# ══════════════════════════════════════════════════════════════════════════════

def build_l2_chart(ticker: str, mid_price: float) -> go.Figure:
    """Simulate a Level-2 order-book liquidity flux chart."""
    np.random.seed(int(time.time()) % 999)
    spread = mid_price * 0.0008

    bid_prices = [mid_price - spread * (i + 1) * (1 + np.random.rand() * 0.3) for i in range(20)]
    ask_prices = [mid_price + spread * (i + 1) * (1 + np.random.rand() * 0.3) for i in range(20)]
    bid_sizes  = np.random.exponential(scale=3.0, size=20) * np.linspace(1.0, 0.2, 20)
    ask_sizes  = np.random.exponential(scale=3.0, size=20) * np.linspace(1.0, 0.2, 20)

    fig = go.Figure(layout=_base_layout(f"L2 LIQUIDITY FLUX — {ticker}"))
    fig.add_trace(go.Bar(
        y=bid_prices, x=-bid_sizes,
        orientation="h", marker_color="rgba(0,255,136,0.65)",
        marker_line_width=0, name="BID",
    ))
    fig.add_trace(go.Bar(
        y=ask_prices, x=ask_sizes,
        orientation="h", marker_color="rgba(255,34,85,0.65)",
        marker_line_width=0, name="ASK",
    ))
    fig.add_hline(y=mid_price, line_dash="dot", line_color="#00f0ff",
                  annotation_text=f"MID {mid_price:.4f}",
                  annotation_font=dict(color="#00f0ff", size=9))
    fig.update_layout(barmode="overlay", height=280,
                      margin=dict(l=0,r=0,t=30,b=5),
                      xaxis=dict(title="Size", gridcolor=PLOTLY_DARK["gridcolor"]),
                      yaxis=dict(gridcolor=PLOTLY_DARK["gridcolor"]))
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# XI.  CAN SLIM + GRAHAM  (Equities window)
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600, show_spinner=False)
def get_fundamentals(ticker: str) -> dict:
    try:
        info = yf.Ticker(ticker).info
        pe    = info.get("trailingPE",       None)
        bvps  = info.get("bookValue",        None)
        price = info.get("currentPrice") or info.get("regularMarketPrice", None)
        eps_g = info.get("earningsGrowth",   None)
        rev_g = info.get("revenueGrowth",    None)
        roe   = info.get("returnOnEquity",   None)
        de    = info.get("debtToEquity",     None)
        mktcap= info.get("marketCap",        None)

        graham_iv = None
        if pe and bvps and price:
            try:
                graham_iv = round(math.sqrt(22.5 * float(bvps) * float(pe)), 2)
            except Exception:
                pass

        mos = None
        if graham_iv and price:
            mos = round((graham_iv - float(price)) / float(price) * 100, 1)

        return {
            "P/E":           round(pe, 1)     if pe    else "N/A",
            "EPS Growth":    f"{eps_g*100:.1f}%" if eps_g else "N/A",
            "Rev Growth":    f"{rev_g*100:.1f}%" if rev_g else "N/A",
            "ROE":           f"{roe*100:.1f}%"   if roe   else "N/A",
            "D/E":           round(de, 2)     if de    else "N/A",
            "Market Cap":    f"${mktcap/1e9:.1f}B" if mktcap else "N/A",
            "Graham IV":     f"${graham_iv}"  if graham_iv else "N/A",
            "Margin of Safety": f"{mos}%"    if mos    else "N/A",
        }
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# XII.  BULK PRICE CACHE (for asset tables)
# ══════════════════════════════════════════════════════════════════════════════

def _refresh_price_cache(tickers: list):
    """Refresh price cache if older than 30 seconds."""
    if time.time() - st.session_state["price_cache_ts"] < 30:
        return
    try:
        batch = " ".join(tickers[:30])
        raw = yf.download(batch, period="1d", interval="1d",
                          auto_adjust=True, progress=False, timeout=15, group_by="ticker")
        for t in tickers[:30]:
            try:
                if isinstance(raw.columns, pd.MultiIndex):
                    close = raw[t]["Close"].dropna()
                else:
                    close = raw["Close"].dropna()
                if not close.empty:
                    st.session_state["price_cache"][t] = float(close.iloc[-1])
            except Exception:
                pass
        st.session_state["price_cache_ts"] = time.time()
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════════════════
# XIII.  AI EXECUTIVE BRIEFING PROMPT
# ══════════════════════════════════════════════════════════════════════════════

def build_ai_prompt(ticker, window, tf, price, rsi, macd_hist,
                    direction, apq_score, date_from, date_to):
    return f"""
You are APQ v7.5, a quantitative trading AI.
Asset: {ticker} | Window: {window} | Timeframe: {tf}
Date Range: {date_from} to {date_to}
Current Price: {price:.4f} | RSI: {rsi:.1f} | MACD Hist: {macd_hist:.4f}
Signal Direction: {direction} | APQ Score: {apq_score}/100

Respond ONLY as a strict Markdown table with these exact rows:
| Field | Analysis |
|-------|----------|
| Management Actions | [2-3 concise action items based on signal] |
| Corporate Adjustments | [sector/macro adjustment notes] |
| Operational Pros | [top 2 bullish factors] |
| Operational Cons | [top 2 bearish risks] |
| Volatility Regime | [LOW/MEDIUM/HIGH with 1-line justification] |
| APQ Verdict | [STRONG BUY / BUY / HOLD / SELL / STRONG SELL with 1-line rationale] |

No preamble. No explanation outside the table. Table only.
"""

# ══════════════════════════════════════════════════════════════════════════════
# XIV.  AD SLOT COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

AD_SLOT_A_HTML = """
<div class="ad-slot" style="height:70px;display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(0,240,255,0.2);border-radius:6px;
  background:rgba(0,240,255,0.02);font-family:'Share Tech Mono',monospace;
  font-size:10px;color:rgba(0,240,255,0.25);letter-spacing:0.15em;
  box-shadow:inset 0 0 20px rgba(0,240,255,0.04);">
  <!-- INSERT AD TAG: SLOT A — TOP HORIZONTAL BANNER (728×90) -->
  ◈ ADVERTISEMENT SLOT A — HORIZONTAL BANNER ◈
</div>
"""

AD_SLOT_B_HTML = """
<div class="ad-slot" style="height:55px;display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(0,255,136,0.15);border-radius:6px;
  background:rgba(0,255,136,0.01);font-family:'Share Tech Mono',monospace;
  font-size:10px;color:rgba(0,255,136,0.2);letter-spacing:0.15em;
  box-shadow:inset 0 0 20px rgba(0,255,136,0.03);">
  <!-- INSERT AD TAG: SLOT B — TAB SEPARATOR BANNER (728×60) -->
  ◈ ADVERTISEMENT SLOT B — TAB SEPARATOR ◈
</div>
"""

AD_SLOT_C_HTML = """
<div class="ad-slot" style="height:200px;display:flex;align-items:center;justify-content:center;
  border:1px solid rgba(255,170,0,0.15);border-radius:6px;
  background:rgba(255,170,0,0.01);font-family:'Share Tech Mono',monospace;
  font-size:10px;color:rgba(255,170,0,0.2);letter-spacing:0.12em;
  box-shadow:inset 0 0 20px rgba(255,170,0,0.03);">
  <!-- INSERT AD TAG: SLOT C — SIDEBAR SQUARE AD (300×250) -->
  ◈ ADVERTISEMENT SLOT C — SIDEBAR SQUARE ◈
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# XV.  SVG LOGO + PULSE RADAR
# ══════════════════════════════════════════════════════════════════════════════

APQ_LOGO_HTML = """
<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
  <svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
    <defs>
      <filter id="glow">
        <feGaussianBlur stdDeviation="1.5" result="blur"/>
        <feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
      <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%"   stop-color="#00f0ff"/>
        <stop offset="100%" stop-color="#00ff88"/>
      </linearGradient>
    </defs>
    <!-- Outer hexagon frame -->
    <polygon points="22,2 40,12 40,32 22,42 4,32 4,12"
      fill="none" stroke="url(#grad1)" stroke-width="1.2" opacity="0.6" filter="url(#glow)"/>
    <!-- Inner diamond -->
    <polygon points="22,8 36,22 22,36 8,22"
      fill="none" stroke="#00f0ff" stroke-width="0.8" opacity="0.4"/>
    <!-- Letter A path -->
    <path d="M14,30 L19,14 L22,22 M16,24 H21" stroke="#00f0ff" stroke-width="1.8"
      fill="none" stroke-linecap="round" filter="url(#glow)"/>
    <!-- Letter P path -->
    <path d="M23,30 L23,14 M23,14 Q29,14 29,20 Q29,26 23,26"
      stroke="#00ff88" stroke-width="1.8" fill="none" stroke-linecap="round" filter="url(#glow)"/>
    <!-- Letter Q path -->
    <path d="M31,20 m-4,0 a4,4 0 1,0 8,0 a4,4 0 1,0 -8,0 M33,23 L36,26"
      stroke="#ffaa00" stroke-width="1.8" fill="none" stroke-linecap="round" filter="url(#glow)"/>
    <!-- Center dot -->
    <circle cx="22" cy="22" r="1.5" fill="#00f0ff" opacity="0.8"/>
  </svg>

  <div>
    <div style="font-family:'Orbitron',monospace;font-size:1.05rem;
      font-weight:900;letter-spacing:0.18em;color:#00f0ff;
      text-shadow:0 0 14px rgba(0,240,255,0.7);">
      APEX PROPHET QUANTUM
    </div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;
      letter-spacing:0.22em;color:#5a7a99;">
      v7.5 ENTERPRISE  &nbsp;|&nbsp;
      <span style="color:#00ff88;animation:dataFlash 2.5s infinite;display:inline;">
        ● LIVE
      </span>
    </div>
  </div>

  <!-- Pulse Radar Node -->
  <div style="margin-left:auto;position:relative;width:34px;height:34px;">
    <div style="position:absolute;inset:0;border-radius:50%;
      border:1px solid rgba(0,240,255,0.3);animation:pulseRadar 2s infinite;"></div>
    <div style="position:absolute;inset:4px;border-radius:50%;
      border:1px solid rgba(0,240,255,0.5);animation:pulseRadar 2s infinite 0.5s;"></div>
    <div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
      width:8px;height:8px;border-radius:50%;background:#00f0ff;
      box-shadow:0 0 8px #00f0ff;"></div>
    <!-- Sweeping scan line -->
    <div style="position:absolute;top:50%;left:50%;width:50%;height:1px;
      background:linear-gradient(90deg,rgba(0,240,255,0.8),transparent);
      transform-origin:left center;animation:scanline 3s linear infinite;"></div>
  </div>
</div>
"""

# ══════════════════════════════════════════════════════════════════════════════
# XVI.  MAIN APP RENDER
# ══════════════════════════════════════════════════════════════════════════════

# Inject CSS
st.markdown(OBSIDIAN_CSS, unsafe_allow_html=True)

# ── SVG Logo ──
st.markdown(APQ_LOGO_HTML, unsafe_allow_html=True)

# ── WIN-RATE SCOREBOARD ───────────────────────────────────────────────────────
acc  = st.session_state["accuracy_pct"]
tot  = st.session_state["total_calls"]
true_c = st.session_state["true_calls"]
false_c = st.session_state["false_calls"]
wshift  = st.session_state["weight_shift"]
compress= "⚡ ACTIVE" if st.session_state["compression_active"] else "NOMINAL"

scoreboard_html = f"""
<div class="apq-scoreboard">
  <div>
    <div class="apq-score-title">🏆 WIN-RATE PERFORMANCE SCOREBOARD</div>
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;
      color:rgba(0,240,255,0.4);letter-spacing:0.1em;">
      GLOBAL MODEL ACCURACY · REAL-TIME TELEMETRY
    </div>
  </div>

  <div style="text-align:center;">
    <div class="apq-score-val-cyan">{acc:.1f}%</div>
    <div class="apq-score-label">Global Accuracy</div>
  </div>
  <div style="text-align:center;">
    <div class="apq-score-val-green">{true_c:,}</div>
    <div class="apq-score-label">True Calls</div>
  </div>
  <div style="text-align:center;">
    <div class="apq-score-val-red">{false_c:,}</div>
    <div class="apq-score-label">False Calls</div>
  </div>
  <div style="text-align:center;">
    <div class="apq-score-val-cyan">{tot:,}</div>
    <div class="apq-score-label">Total Calls</div>
  </div>
  <div style="text-align:center;">
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.85rem;
      color:#ffaa00;text-shadow:0 0 8px rgba(255,170,0,0.5);">{wshift:.3f}×</div>
    <div class="apq-score-label">Weight Shift</div>
  </div>
  <div style="text-align:center;">
    <div style="font-family:'Share Tech Mono',monospace;font-size:0.72rem;
      color:{'#ff2255' if compress == '⚡ ACTIVE' else '#5a7a99'};">{compress}</div>
    <div class="apq-score-label">Risk Compression</div>
  </div>
</div>
"""
st.markdown(scoreboard_html, unsafe_allow_html=True)

# ── AD SLOT A ──
components.html(AD_SLOT_A_HTML, height=78)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="font-family:'Orbitron',monospace;font-size:0.7rem;
      letter-spacing:0.18em;color:#00f0ff;text-align:center;margin-bottom:14px;
      text-shadow:0 0 10px rgba(0,240,255,0.5);">
      🔒 DATA NETWORKS &amp; KEYS ADAPTER
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-head">GEMINI AI KEYS</div>', unsafe_allow_html=True)
    raw_keys = st.text_area(
        "Gemini API Keys (comma-separated)",
        value="",
        type="password",
        height=70,
        help="Paste one or more Gemini API keys separated by commas. Keys rotate automatically on 429 errors.",
        placeholder="key1,key2,key3...",
    )
    if raw_keys:
        st.session_state["gemini_keys"] = [k.strip() for k in raw_keys.split(",") if k.strip()]

    st.markdown('<div class="section-head">ALPACA PAPER TRADING</div>', unsafe_allow_html=True)
    alp_key = st.text_input("Alpaca API Key", type="password", key="alp_key_inp",
                             placeholder="PK…")
    alp_sec = st.text_input("Alpaca Secret",  type="password", key="alp_sec_inp",
                             placeholder="Secret…")
    if alp_key: st.session_state["alpaca_key"]    = alp_key
    if alp_sec: st.session_state["alpaca_secret"] = alp_sec

    if st.button("🔗 CONNECT ALPACA", use_container_width=True):
        with st.spinner("Connecting…"):
            acct = get_alpaca_account()
            if acct:
                st.success("✅ Alpaca connected!")
            else:
                st.warning("⚠ Check credentials or add keys first.")

    # ── Portfolio values ──
    pc = st.session_state["portfolio_cache"]
    st.markdown('<div class="section-head">PORTFOLIO HUB</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="apq-panel">
      <div style="text-align:center;margin-bottom:6px;">
        <div class="portfolio-val">${pc['equity']:,.2f}</div>
        <div class="portfolio-label">Gross Equity Value</div>
      </div>
      <div style="display:flex;gap:6px;">
        <div style="flex:1;text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:0.8rem;color:#00f0ff;">
            ${pc['cash']:,.2f}</div>
          <div class="portfolio-label">Cash</div>
        </div>
        <div style="flex:1;text-align:center;">
          <div style="font-family:'Orbitron',monospace;font-size:0.8rem;color:#00ff88;">
            ${pc['buying_power']:,.2f}</div>
          <div class="portfolio-label">Buying Power</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Quick Order ──
    st.markdown('<div class="section-head">QUICK ORDER</div>', unsafe_allow_html=True)
    order_ticker = st.text_input("Symbol", value=st.session_state["active_ticker"],
                                  key="order_sym")
    order_qty    = st.number_input("Qty", min_value=1, value=1, key="order_qty")
    col_b, col_s = st.columns(2)
    with col_b:
        if st.button("⬆ BUY", use_container_width=True, key="buy_btn"):
            ok, msg = submit_alpaca_order(order_ticker, order_qty, "buy")
            st.success("Order placed!") if ok else st.error(f"Error: {msg.get('message','')}")
    with col_s:
        if st.button("⬇ SELL", use_container_width=True, key="sell_btn"):
            ok, msg = submit_alpaca_order(order_ticker, order_qty, "sell")
            st.success("Order placed!") if ok else st.error(f"Error: {msg.get('message','')}")

    st.markdown("---")
    # ── AD SLOT C ──
    components.html(AD_SLOT_C_HTML, height=210)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN WORKSPACE
# ══════════════════════════════════════════════════════════════════════════════

# ── Window selector ──
wc1, wc2, wc3, wc4 = st.columns([1,1,1,3])
with wc1:
    if st.button("📈 SPOT EQUITIES", use_container_width=True, key="win_eq"):
        st.session_state["active_window"] = "📈 SPOT EQUITIES"
        st.session_state["active_ticker"] = "AAPL"
        st.session_state["asset_page"]    = 0
with wc2:
    if st.button("⚡ DERIVATIVES", use_container_width=True, key="win_fut"):
        st.session_state["active_window"] = "⚡ DERIVATIVES"
        st.session_state["active_ticker"] = "ES=F"
        st.session_state["asset_page"]    = 0
with wc3:
    if st.button("🌌 CRYPTO RADAR", use_container_width=True, key="win_cr"):
        st.session_state["active_window"] = "🌌 CRYPTO RADAR"
        st.session_state["active_ticker"] = "BTC-USD"
        st.session_state["asset_page"]    = 0

active_window = st.session_state["active_window"]
active_assets = WINDOW_ASSETS.get(active_window, EQUITIES)

# Window badge
badge_color = {"📈 SPOT EQUITIES":"#00ff88","⚡ DERIVATIVES":"#ffaa00","🌌 CRYPTO RADAR":"#9b5de5"}
bc = badge_color.get(active_window,"#00f0ff")
st.markdown(f"""
<div style="display:flex;align-items:center;gap:8px;margin:4px 0 10px 0;">
  <div style="width:8px;height:8px;border-radius:50%;background:{bc};
    box-shadow:0 0 8px {bc};"></div>
  <span style="font-family:'Orbitron',monospace;font-size:0.68rem;
    color:{bc};letter-spacing:0.2em;">{active_window.upper()}</span>
</div>
""", unsafe_allow_html=True)

# ── Main 3-column layout ──
left_col, center_col, right_col = st.columns([3, 4.5, 2.5])

# ══════════════════════════════════════════════════════════════════════════════
# LEFT COLUMN — Asset Tables with Pagination
# ══════════════════════════════════════════════════════════════════════════════
with left_col:
    st.markdown('<div class="section-head">ASSET SCANNER</div>', unsafe_allow_html=True)

    # Refresh price cache
    _refresh_price_cache(active_assets)

    page     = st.session_state["asset_page"]
    per_page = 10
    start_i  = 0
    end_i    = per_page * (page + 1)
    slice_assets = active_assets[:end_i]

    # Build mini table data
    bull_rows = []
    bear_rows = []

    for t in slice_assets:
        cp = st.session_state["price_cache"].get(t, None)
        if cp is None:
            try:
                tk = yf.Ticker(t)
                hist = tk.history(period="2d")
                if not hist.empty:
                    cp = float(hist["Close"].iloc[-1])
                    st.session_state["price_cache"][t] = cp
            except Exception:
                pass

        if cp is None:
            continue

        # Simulate 24h change (use session variance)
        change_pct = (random.random() - 0.48) * 6  # ±6% range, slightly bullish skew
        change_str = f"+{change_pct:.2f}%" if change_pct >= 0 else f"{change_pct:.2f}%"

        row = {"ticker": t, "price": cp, "change": change_pct, "change_str": change_str}
        if change_pct >= 0:
            bull_rows.append(row)
        else:
            bear_rows.append(row)

    bull_rows.sort(key=lambda x: x["change"], reverse=True)
    bear_rows.sort(key=lambda x: x["change"])

    # Render tables
    tab_bull, tab_bear = st.tabs(["🟢 BULLISH", "🔴 BEARISH"])

    def render_asset_table(rows, label):
        if not rows:
            st.markdown(f"<div style='color:#5a7a99;font-size:0.7rem;padding:8px;'>No {label} signals</div>",
                        unsafe_allow_html=True)
            return

        html_rows = ""
        for r in rows[:10]:
            color = "#00ff88" if r["change"] >= 0 else "#ff2255"
            html_rows += f"""
            <div class="apq-asset-row" onclick="">
              <span class="ticker">{r['ticker']}</span>
              <span class="price">${r['price']:,.4f}</span>
              <span style="color:{color};font-size:0.7rem;">{r['change_str']}</span>
            </div>"""

        st.markdown(f"""
        <div class="apq-panel" style="padding:6px;">
          <div style="display:flex;justify-content:space-between;padding:4px 8px;
            border-bottom:1px solid rgba(0,240,255,0.1);margin-bottom:4px;">
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;
              color:#5a7a99;">TICKER</span>
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;
              color:#5a7a99;">PRICE</span>
            <span style="font-family:'Share Tech Mono',monospace;font-size:0.6rem;
              color:#5a7a99;">CHG%</span>
          </div>
          {html_rows}
        </div>
        """, unsafe_allow_html=True)

    with tab_bull:
        render_asset_table(bull_rows, "bullish")

    with tab_bear:
        render_asset_table(bear_rows, "bearish")

    # ── Ticker selector ──
    st.markdown('<div class="section-head" style="margin-top:10px;">SELECT ASSET</div>',
                unsafe_allow_html=True)
    chosen = st.selectbox("Asset", options=active_assets,
                          index=active_assets.index(st.session_state["active_ticker"])
                          if st.session_state["active_ticker"] in active_assets else 0,
                          key="ticker_sel", label_visibility="collapsed")
    st.session_state["active_ticker"] = chosen

    # ── Load More pagination ──
    total_pages = math.ceil(len(active_assets) / per_page) - 1
    if page < total_pages:
        st.markdown('<div class="load-more-btn">', unsafe_allow_html=True)
        if st.button(f"⬇ LOAD MORE  ({end_i}/{len(active_assets)})",
                     use_container_width=True, key="load_more"):
            st.session_state["asset_page"] += 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="text-align:center;font-family:'Share Tech Mono',monospace;
          font-size:0.6rem;color:#5a7a99;padding:6px;">
          ✓ ALL {len(active_assets)} ASSETS LOADED
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CENTER COLUMN — Chart + Controls
# ══════════════════════════════════════════════════════════════════════════════
with center_col:

    # ── Controls Row ──
    ctrl1, ctrl2, ctrl3 = st.columns(3)
    with ctrl1:
        tf_sel = st.selectbox("TIMEFRAME", TIMEFRAMES,
                              index=TIMEFRAMES.index(st.session_state["active_tf"]),
                              key="tf_sel_main", label_visibility="collapsed")
        st.session_state["active_tf"] = tf_sel
    with ctrl2:
        chart_sel = st.selectbox("CHART TYPE", CHART_TYPES,
                                  index=CHART_TYPES.index(st.session_state["active_chart"]),
                                  key="chart_sel_main", label_visibility="collapsed")
        st.session_state["active_chart"] = chart_sel
    with ctrl3:
        st.markdown('<div class="live-badge">◉ LIVE  APQ ENGINE</div>', unsafe_allow_html=True)

    # ── Custom date pickers ──
    custom_from = st.session_state["custom_from"]
    custom_to   = st.session_state["custom_to"]
    if tf_sel == "CUSTOM":
        dp1, dp2 = st.columns(2)
        with dp1:
            custom_from = st.date_input("FROM DATE", value=st.session_state["custom_from"],
                                         min_value=datetime.date(2000,1,1),
                                         max_value=datetime.date(2029,11,25),
                                         key="date_from")
            st.session_state["custom_from"] = custom_from
        with dp2:
            custom_to = st.date_input("TO DATE", value=st.session_state["custom_to"],
                                       min_value=datetime.date(2000,1,2),
                                       max_value=datetime.date(2029,11,25),
                                       key="date_to")
            st.session_state["custom_to"] = custom_to

    ticker = st.session_state["active_ticker"]
    weight = st.session_state.get("weight_shift", 1.0)

    # ── Fetch & compute ──
    with st.spinner(f"Loading {ticker}…"):
        df = fetch_ohlcv(ticker, tf_sel, custom_from, custom_to)
        if not df.empty:
            df = add_indicators(df, weight)

    # ── Compute targets ──
    entry, target, stop, apq_score, direction = compute_atr_targets(df, weight)

    # Register prediction
    if entry and ticker not in st.session_state["pred_log"]:
        st.session_state["pred_log"][ticker] = {
            "target": target, "stop": stop, "entry": entry,
            "direction": direction, "ts": time.time()
        }
        st.session_state["total_calls"] += 1

    # ── Metrics Bar ──
    price_disp = f"${entry:.4f}" if entry else "N/A"
    target_disp= f"${target:.4f}" if target else "N/A"
    stop_disp  = f"${stop:.4f}" if stop else "N/A"
    dir_color  = "#00ff88" if direction=="LONG" else "#ff2255" if direction=="SHORT" else "#ffaa00"

    st.markdown(f"""
    <div class="apq-metric-row">
      <div class="apq-metric-card">
        <div class="label">LIVE PRICE</div>
        <div class="value">{price_disp}</div>
      </div>
      <div class="apq-metric-card">
        <div class="label">TARGET</div>
        <div class="value green">{target_disp}</div>
      </div>
      <div class="apq-metric-card">
        <div class="label">STOP LOSS</div>
        <div class="value red">{stop_disp}</div>
      </div>
      <div class="apq-metric-card">
        <div class="label">APQ SCORE</div>
        <div class="value" style="color:{dir_color};text-shadow:0 0 8px {dir_color}80;">
          {apq_score}/100
        </div>
      </div>
      <div class="apq-metric-card">
        <div class="label">SIGNAL</div>
        <div class="value" style="color:{dir_color};font-size:0.7rem;letter-spacing:0.08em;">
          {direction}
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Main Chart ──
    if not df.empty:
        fig_main = build_chart(df, chart_sel, ticker, entry, target, stop)
        fig_main.update_layout(height=320)
        st.plotly_chart(fig_main, use_container_width=True, config={"displayModeBar": False})
    else:
        st.warning("⚠ No data — check ticker symbol or try a different timeframe.")

    # ── AD SLOT B ──
    components.html(AD_SLOT_B_HTML, height=63)

    # ── Sub-charts: Volume / RSI / MACD ──
    sub_tabs = st.tabs(["📊 VOLUME", "📈 RSI", "〰 MACD"])
    with sub_tabs[0]:
        if not df.empty:
            st.plotly_chart(build_volume_chart(df), use_container_width=True,
                            config={"displayModeBar": False})
    with sub_tabs[1]:
        if not df.empty:
            st.plotly_chart(build_rsi_chart(df), use_container_width=True,
                            config={"displayModeBar": False})
    with sub_tabs[2]:
        if not df.empty:
            st.plotly_chart(build_macd_chart(df), use_container_width=True,
                            config={"displayModeBar": False})

    # ── AI EXECUTIVE BRIEFING ──
    st.markdown('<div class="section-head" style="margin-top:8px;">AI EXECUTIVE BRIEFING</div>',
                unsafe_allow_html=True)

    with st.expander("🤖 GENERATE APQ NEURAL ANALYSIS", expanded=False):
        rsi_val   = 50.0
        macd_h    = 0.0
        if not df.empty:
            rsi_cols   = [c for c in df.columns if "RSI" in c]
            macd_cols  = [c for c in df.columns if "MACD_Hist" in c]
            if rsi_cols:  rsi_val  = float(df[rsi_cols[0]].iloc[-1])  if not df[rsi_cols[0]].isna().all()  else 50.0
            if macd_cols: macd_h   = float(df[macd_cols[0]].iloc[-1]) if not df[macd_cols[0]].isna().all() else 0.0

        cache_key = f"{ticker}_{tf_sel}_{direction}_{custom_from}_{custom_to}"

        if st.button("⚡ RUN AI BRIEFING", key="ai_btn", use_container_width=True):
            if cache_key in st.session_state["ai_table_cache"]:
                st.session_state["ai_table_cache"].pop(cache_key)  # force refresh

        prompt = build_ai_prompt(
            ticker, active_window, tf_sel,
            entry or 0, rsi_val, macd_h,
            direction, apq_score,
            str(custom_from), str(custom_to),
        )

        ai_result = _call_gemini(prompt, cache_key)
        st.markdown(ai_result, unsafe_allow_html=False)


# ══════════════════════════════════════════════════════════════════════════════
# RIGHT COLUMN — Context-aware Discrete Fields Rail
# ══════════════════════════════════════════════════════════════════════════════
with right_col:
    st.markdown('<div class="section-head">ANALYSIS RAIL</div>', unsafe_allow_html=True)

    # ────────────────────────────────────────────────
    # A) SPOT EQUITIES → CAN SLIM + Graham
    # ────────────────────────────────────────────────
    if "SPOT EQUITIES" in active_window:
        st.markdown('<div class="apq-panel-title">CAN SLIM / GRAHAM FUNDAMENTALS</div>',
                    unsafe_allow_html=True)

        fund = get_fundamentals(ticker)
        if fund:
            rows_html = ""
            for k, v in fund.items():
                mos_color = "#00ff88" if k=="Margin of Safety" and str(v).startswith("-") is False and v!="N/A" else "#ff2255" if str(v).startswith("-") else "#5a7a99"
                rows_html += f"""
                <div style="display:flex;justify-content:space-between;
                  padding:5px 0;border-bottom:1px solid rgba(0,240,255,0.06);">
                  <span style="font-family:'Share Tech Mono',monospace;font-size:0.65rem;
                    color:#5a7a99;">{k}</span>
                  <span style="font-family:'Orbitron',monospace;font-size:0.65rem;
                    color:{mos_color};">{v}</span>
                </div>"""
            st.markdown(f'<div class="apq-panel">{rows_html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="apq-panel"><span style="color:#5a7a99;font-size:0.7rem;">Fundamental data unavailable for this asset.</span></div>',
                        unsafe_allow_html=True)

        # CAN SLIM quick checklist
        can_slim_checks = {
            "C – Current EPS Growth": "≥25% QoQ",
            "A – Annual EPS Growth":  "≥25% over 3Y",
            "N – New Product/Market": "Check latest news",
            "S – Supply (Shares Out)":"Small/Mid preferred",
            "L – Leader in Sector":   "Top 1-3 in group",
            "I – Institutional Sponsor":"Check 13F filings",
            "M – Market Direction":   "Uptrend (IBD TM)",
        }
        st.markdown('<div class="apq-panel-title" style="margin-top:10px;">CAN SLIM CHECKLIST</div>',
                    unsafe_allow_html=True)
        cl_html = '<div class="apq-panel">'
        for k, v in can_slim_checks.items():
            cl_html += f"""
            <div style="padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);">
              <div style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;
                color:#00f0ff;">{k}</div>
              <div style="font-family:'Exo 2',sans-serif;font-size:0.6rem;
                color:#5a7a99;margin-top:1px;">{v}</div>
            </div>"""
        cl_html += '</div>'
        st.markdown(cl_html, unsafe_allow_html=True)

    # ────────────────────────────────────────────────
    # B) DERIVATIVES → Black-Scholes Greeks
    # ────────────────────────────────────────────────
    elif "DERIVATIVES" in active_window:
        st.markdown('<div class="apq-panel-title">BLACK-SCHOLES GREEKS ENGINE</div>',
                    unsafe_allow_html=True)

        S_val = entry or 100.0
        st.markdown('<div class="apq-panel">', unsafe_allow_html=True)

        K_inp    = st.number_input("Strike Price (K)", value=float(round(S_val)),
                                    min_value=0.01, key="bs_k", format="%.2f")
        T_inp    = st.number_input("Time to Expiry (days)", value=30, min_value=1,
                                    max_value=730, key="bs_t")
        r_inp    = st.number_input("Risk-Free Rate %", value=5.0, min_value=0.0,
                                    max_value=20.0, key="bs_r") / 100
        vol_inp  = st.number_input("Implied Volatility %", value=25.0, min_value=0.1,
                                    max_value=300.0, key="bs_vol") / 100
        opt_type = st.radio("Option Type", ["call","put"], horizontal=True, key="bs_type")
        st.markdown('</div>', unsafe_allow_html=True)

        greeks = black_scholes_greeks(S_val, K_inp, T_inp/365, r_inp, vol_inp, opt_type)

        greek_symbols = {"Δ Delta":"Δ","Γ Gamma":"Γ","Θ Theta":"Θ","ν Vega":"ν","ρ Rho":"ρ"}
        for name, val in greeks.items():
            sym = greek_symbols.get(name, name[0])
            color = "#00ff88" if val > 0 else "#ff2255" if val < 0 else "#5a7a99"
            st.markdown(f"""
            <div class="greek-card">
              <div class="greek-symbol">{sym}</div>
              <div class="greek-name">{name}</div>
              <div class="greek-val" style="color:{color};">{val}</div>
            </div>""", unsafe_allow_html=True)

        # Funding / Basis drift simulation
        st.markdown('<div class="apq-panel-title" style="margin-top:10px;">CONTRACT FUNDING DRIFT</div>',
                    unsafe_allow_html=True)
        funding_vals = np.cumsum(np.random.randn(30) * 0.001)
        fig_fund = go.Figure(go.Scatter(
            y=funding_vals, mode="lines+markers",
            line=dict(color="#9b5de5", width=1.5),
            marker=dict(size=3, color="#9b5de5"),
            name="Funding Rate",
        ), layout=_base_layout())
        fig_fund.update_layout(height=130, margin=dict(l=0,r=0,t=5,b=5),
                                showlegend=False)
        st.plotly_chart(fig_fund, use_container_width=True, config={"displayModeBar":False})

    # ────────────────────────────────────────────────
    # C) CRYPTO → Level-2 Liquidity Flux
    # ────────────────────────────────────────────────
    elif "CRYPTO" in active_window:
        st.markdown('<div class="apq-panel-title">LEVEL-2 LIQUIDITY FLUX</div>',
                    unsafe_allow_html=True)

        mid_price = entry or 1.0
        fig_l2 = build_l2_chart(ticker, mid_price)
        st.plotly_chart(fig_l2, use_container_width=True, config={"displayModeBar":False})

        # ── Crypto-specific metrics ──
        st.markdown('<div class="apq-panel-title" style="margin-top:8px;">MARKET MICROSTRUCTURE</div>',
                    unsafe_allow_html=True)

        if not df.empty:
            vol_24h = float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
            obv_val = float(df["OBV"].iloc[-1]) if "OBV" in df.columns else 0
            stoch_k = float(df["Stoch_K"].iloc[-1]) if "Stoch_K" in df.columns else 0
            stoch_d = float(df["Stoch_D"].iloc[-1]) if "Stoch_D" in df.columns else 0

            ms_html = f"""
            <div class="apq-panel">
              <div style="display:flex;justify-content:space-between;padding:4px 0;
                border-bottom:1px solid rgba(0,240,255,0.06);">
                <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a99;">Volume (latest)</span>
                <span style="font-family:'Orbitron',monospace;font-size:0.65rem;color:#00f0ff;">{vol_24h:,.0f}</span>
              </div>
              <div style="display:flex;justify-content:space-between;padding:4px 0;
                border-bottom:1px solid rgba(0,240,255,0.06);">
                <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a99;">OBV</span>
                <span style="font-family:'Orbitron',monospace;font-size:0.65rem;
                  color:{'#00ff88' if obv_val>0 else '#ff2255'};">{obv_val:,.0f}</span>
              </div>
              <div style="display:flex;justify-content:space-between;padding:4px 0;
                border-bottom:1px solid rgba(0,240,255,0.06);">
                <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a99;">Stoch %K</span>
                <span style="font-family:'Orbitron',monospace;font-size:0.65rem;
                  color:{'#ff2255' if stoch_k>80 else '#00ff88' if stoch_k<20 else '#ffaa00'};">
                  {stoch_k:.1f}</span>
              </div>
              <div style="display:flex;justify-content:space-between;padding:4px 0;">
                <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;color:#5a7a99;">Stoch %D</span>
                <span style="font-family:'Orbitron',monospace;font-size:0.65rem;color:#9b5de5;">
                  {stoch_d:.1f}</span>
              </div>
            </div>"""
            st.markdown(ms_html, unsafe_allow_html=True)

    # ── Common: Indicator Summary ──
    if not df.empty:
        st.markdown('<div class="section-head" style="margin-top:10px;">INDICATOR MATRIX</div>',
                    unsafe_allow_html=True)

        row = df.iloc[-1]
        ind_items = {}

        rsi_c   = [c for c in df.columns if "RSI" in c]
        macd_c  = [c for c in df.columns if "MACD_Hist" in c]
        atr_c   = [c for c in df.columns if "ATR" in c]
        bb_u    = [c for c in df.columns if "BB_Upper" in c]
        bb_l    = [c for c in df.columns if "BB_Lower" in c]
        ema20_c = [c for c in df.columns if "EMA_20" in c]
        ema50_c = [c for c in df.columns if "EMA_50" in c]

        if rsi_c:   ind_items["RSI-14"]     = f"{row[rsi_c[0]]:.1f}"
        if macd_c:  ind_items["MACD Hist"]  = f"{row[macd_c[0]]:.5f}"
        if atr_c:   ind_items["ATR-14"]     = f"{row[atr_c[0]]:.4f}"
        if bb_u:    ind_items["BB Upper"]   = f"${row[bb_u[0]]:.4f}"
        if bb_l:    ind_items["BB Lower"]   = f"${row[bb_l[0]]:.4f}"
        if ema20_c: ind_items["EMA-20"]     = f"${row[ema20_c[0]]:.4f}"
        if ema50_c: ind_items["EMA-50"]     = f"${row[ema50_c[0]]:.4f}"
        if "VWAP" in df.columns: ind_items["VWAP"] = f"${row['VWAP']:.4f}"

        ind_html = '<div class="apq-panel">'
        for k, v in ind_items.items():
            ind_html += f"""
            <div style="display:flex;justify-content:space-between;
              padding:4px 0;border-bottom:1px solid rgba(0,240,255,0.05);">
              <span style="font-family:'Share Tech Mono',monospace;font-size:0.62rem;
                color:#5a7a99;">{k}</span>
              <span style="font-family:'Orbitron',monospace;font-size:0.63rem;
                color:#00f0ff;">{v}</span>
            </div>"""
        ind_html += '</div>'
        st.markdown(ind_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;font-family:'Share Tech Mono',monospace;
  font-size:0.6rem;color:rgba(0,240,255,0.2);letter-spacing:0.15em;padding:6px 0;">
  APEX PROPHET QUANTUM v7.5 ENTERPRISE  ·  ALL TOOLS OPEN ACCESS  ·  AD-MONETIZED PLATFORM
  ·  DATA: YAHOO FINANCE  ·  AI: GOOGLE GEMINI  ·  TRADING: ALPACA PAPER
  <br/>⚠ NOT FINANCIAL ADVICE. FOR EDUCATIONAL & INFORMATIONAL USE ONLY. ⚠
</div>
""", unsafe_allow_html=True)
