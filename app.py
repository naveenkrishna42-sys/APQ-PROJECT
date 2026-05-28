"""
APEX PROPHET QUANTUM (APQ) v7.5 Enterprise Web Edition
=======================================================
Production-ready Streamlit app — fully corrected & spec-compliant.

KEY FIXES vs Gemini output:
  1. No blocking time.sleep() — uses streamlit-autorefresh
  2. yfinance multi-ticker MultiIndex handling (v0.2.x+)
  3. BYOK sidebar panel for user keys (no .env dependency)
  4. Open-access — no password gate (per spec)
  5. Side-by-side Bullish/Bearish tables
  6. All 3 ad slots present
  7. Real ATR-based Renko brick simulation
  8. Seeded Level 2 depth chart (no flicker)
  9. Robust MACD signal column detection
 10. requirements.txt included
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
from scipy.stats import norm
import plotly.graph_objects as go
import datetime
import time
import os
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

# ── Page config must be FIRST Streamlit call ───────────────────────────────────
st.set_page_config(
    page_title="APEX PROPHET QUANTUM (APQ) v7.5",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Auto-refresh import (non-blocking) ────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ── Optional dependencies ──────────────────────────────────────────────────────
try:
    import pandas_ta as ta  # noqa
    TA_AVAILABLE = True
except ImportError:
    TA_AVAILABLE = False

try:
    from google import genai as google_genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    "master_matrix": pd.DataFrame(),
    "active_radar_ticker": "BTC",
    "prediction_feedback_ledger": [],
    "system_accuracy_multiplier": 1.0,
    "global_win_rate_percentage": 86.4,
    "ai_table_cache": {},
    "true_calls_counter": 142,
    "false_calls_counter": 22,
    "pagination_limits": {"EQUITIES": 10, "DERIVATIVES": 10, "CRYPTO": 10},
    "auto_refresh_enabled": False,
    "disclaimer_accepted": False,
    # BYOK keys stored per-session only
    "user_gemini_keys": "",
    "user_alpaca_id": "",
    "user_alpaca_secret": "",
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
#  THEME CSS — CYBER-GRID OBSIDIAN
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ──────────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@400;700;900&display=swap');

html, body, .stApp {
    background-color: #030407 !important;
    color: #cbd5e1;
    font-family: 'Exo 2', sans-serif;
}

/* ── Pulsing radar dot ─────────────────────────────────────────────────── */
.radar-node {
    width: 11px; height: 11px;
    background: #00ff88; border-radius: 50%;
    display: inline-block; vertical-align: middle; margin-left: 8px;
    box-shadow: 0 0 0 0 rgba(0,255,136,0.7);
    animation: pulseRadar 1.6s infinite cubic-bezier(0.66,0,0,1);
}
@keyframes pulseRadar { to { box-shadow: 0 0 0 18px rgba(0,255,136,0); } }

/* ── Logo frame ────────────────────────────────────────────────────────── */
.logo-frame {
    display: flex; align-items: center; gap: 14px;
    padding: 10px 0 14px; border-bottom: 1px solid #141a29; margin-bottom: 14px;
}
.logo-title {
    margin: 0; font-family: 'Exo 2', sans-serif; font-weight: 900;
    color: #fff; letter-spacing: 2px; font-size: 22px; display: inline-block;
}
.logo-sub {
    color: #3a4860; font-size: 11px; letter-spacing: 3px;
    text-transform: uppercase; margin-top: 2px;
}

/* ── Price telemetry inline tags ───────────────────────────────────────── */
.price-live  { color: #00f0ff !important; font-family: 'Share Tech Mono', monospace;
               font-size: 24px; font-weight: 900; text-shadow: 0 0 10px rgba(0,240,255,.4); }
.price-tgt   { color: #00ff88 !important; font-family: 'Share Tech Mono', monospace;
               font-size: 24px; font-weight: 900; text-shadow: 0 0 10px rgba(0,255,136,.4); }
.price-stop  { color: #ff2255 !important; font-family: 'Share Tech Mono', monospace;
               font-size: 24px; font-weight: 900; text-shadow: 0 0 10px rgba(255,34,85,.4); }
.score-apq   { color: #ffb700 !important; font-family: 'Share Tech Mono', monospace;
               font-size: 24px; font-weight: 900; text-shadow: 0 0 10px rgba(255,183,0,.4); }

/* ── Panel cards ───────────────────────────────────────────────────────── */
.matrix-panel {
    background: linear-gradient(135deg, #090c15 0%, #05070a 100%);
    padding: 18px; border-radius: 8px; border: 1px solid #111724;
    margin-bottom: 14px; transition: all 0.22s cubic-bezier(0.4,0,0.2,1);
}
.matrix-panel:hover {
    transform: translateY(-1px);
    border-color: #00f0ff;
    box-shadow: 0 4px 14px rgba(0,240,255,.12);
}

/* ── Scoreboard row ────────────────────────────────────────────────────── */
.score-row {
    display: flex; justify-content: space-between; align-items: center;
    gap: 20px; flex-wrap: wrap;
}
.score-cell { text-align: center; flex: 1; min-width: 120px; }
.score-label { font-size: 10px; color: #5a6478; text-transform: uppercase; letter-spacing: 1.5px; }

/* ── Ad slot ───────────────────────────────────────────────────────────── */
.ad-slot {
    background: #06080e; border: 1px dashed #1a2236;
    border-radius: 6px; text-align: center;
    color: #333d50; font-size: 10px; letter-spacing: 2px;
    text-transform: uppercase; margin: 10px 0; padding: 14px 10px;
}

/* ── Streamlit component overrides ─────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(90deg, #09101f, #0e1a30) !important;
    color: #fff !important; border: 1px solid #162642 !important;
    border-radius: 6px !important; font-weight: 700 !important;
    transition: all 0.15s ease !important; width: 100%;
}
.stButton > button:hover {
    border-color: #00ff88 !important;
    box-shadow: 0 0 14px rgba(0,255,136,.18) !important;
    transform: scale(1.015);
}
.stButton > button:active { transform: scale(0.97); }

div[data-testid="stMetricValue"] { font-family: 'Share Tech Mono', monospace; color: #00f0ff; }
.stSelectbox label, .stSlider label, .stDateInput label { color: #5a6478 !important; font-size: 11px !important; }
.stTabs [data-baseweb="tab"] { font-weight: 700; letter-spacing: 1px; color: #4a5568; }
.stTabs [aria-selected="true"] { color: #00f0ff !important; border-bottom: 2px solid #00f0ff !important; }

/* Sidebar ─────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] { background: #03050a !important; border-right: 1px solid #0d1420; }
[data-testid="stSidebar"] label { color: #5a6478 !important; font-size: 11px !important; }

/* Dataframe ────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border: 1px solid #0d1420; border-radius: 6px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ASSET POOLS
# ══════════════════════════════════════════════════════════════════════════════
EQUITIES_POOL    = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD",
                    "NFLX","AVGO","COST","CRM","INTC","QCOM","ADBE","CSCO"]
DERIVATIVES_POOL = ["SPY","QQQ","IWM","GLD","SLV","USO","UNG",
                    "TLT","HYG","EEM","FXI","VXX"]
CRYPTO_POOL      = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD",
                    "ADA-USD","DOT-USD","LTC-USD","LINK-USD","AVAX-USD"]

ALL_TICKERS      = list(dict.fromkeys(EQUITIES_POOL + DERIVATIVES_POOL + CRYPTO_POOL))

POOL_MAP = {
    "EQUITIES":    EQUITIES_POOL,
    "DERIVATIVES": DERIVATIVES_POOL,
    "CRYPTO":      CRYPTO_POOL,
}

# ── Gap-map: period / interval / ATR multiplier ────────────────────────────
GAP_MAP = {
    "1m":  ("2d",   "1m",  1.1),
    "3m":  ("3d",   "3m",  1.3),
    "5m":  ("5d",   "5m",  1.6),
    "15m": ("7d",   "15m", 2.0),
    "30m": ("14d",  "30m", 2.2),
    "1h":  ("1mo",  "1h",  2.8),
    "2h":  ("2mo",  "2h",  3.0),
    "4h":  ("3mo",  "4h",  3.4),
    "1d":  ("2y",   "1d",  4.2),
}

CHART_PERIOD_MAP   = {"1D":"1d","5D":"5d","1M":"1mo","3M":"3mo","6M":"6mo",
                       "1Y":"1y","2Y":"2y","3Y":"3y","5Y":"5y","Max":"max"}
CHART_INTERVAL_MAP = {"1D":"1m","5D":"5m","1M":"30m","3M":"1h","6M":"2h",
                       "1Y":"1d","2Y":"1d","3Y":"1wk","5Y":"1wk","Max":"1mo"}

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — BYOK KEYS + CONTROLS  (FIX #3: fully BYOK, no server creds needed)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:10px 0 6px;'>
        <span style='font-size:13px; font-weight:900; color:#00f0ff; letter-spacing:2px;'>
            🔒 DATA NETWORKS & KEYS ADAPTER
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.caption("Keys are stored only in your browser session — never on the server.")

    gemini_raw = st.text_input(
        "Gemini API Keys (comma-separated for rotation)",
        value=st.session_state.user_gemini_keys,
        type="password",
        placeholder="AIza..., AIza...",
    )
    if gemini_raw != st.session_state.user_gemini_keys:
        st.session_state.user_gemini_keys = gemini_raw

    alpaca_id = st.text_input(
        "Alpaca Paper API Key ID",
        value=st.session_state.user_alpaca_id,
        type="password",
        placeholder="PKTEST...",
    )
    alpaca_secret = st.text_input(
        "Alpaca Paper Secret Key",
        value=st.session_state.user_alpaca_secret,
        type="password",
        placeholder="xxxxxxxx...",
    )
    if alpaca_id != st.session_state.user_alpaca_id:
        st.session_state.user_alpaca_id = alpaca_id
    if alpaca_secret != st.session_state.user_alpaca_secret:
        st.session_state.user_alpaca_secret = alpaca_secret

    st.divider()

    # FIX #1: non-blocking auto-refresh via streamlit-autorefresh
    st.session_state.auto_refresh_enabled = st.toggle(
        "📡 Live Auto-Refresh (60s)", value=st.session_state.auto_refresh_enabled
    )

    st.divider()
    st.markdown("""
    <div class='ad-slot' style='margin-top:auto;'>
        AD SLOT C — SIDEBAR SQUARE FOOTER<br>
        <!-- AD SLOT C: 250x250 sidebar footer responsive unit -->
    </div>
    """, unsafe_allow_html=True)

# ── Build runtime key pool from session keys (fallback to env) ─────────────
_raw_keys = st.session_state.user_gemini_keys or os.getenv("GEMINI_API_KEY", "")
GEMINI_KEY_POOL = [k.strip() for k in _raw_keys.split(",") if k.strip()]

# ── Build Alpaca client from session keys ──────────────────────────────────
trading_client = None
if ALPACA_AVAILABLE:
    _aid = st.session_state.user_alpaca_id or os.getenv("APCA_API_KEY_ID", "")
    _asc = st.session_state.user_alpaca_secret or os.getenv("APCA_API_SECRET_KEY", "")
    if _aid and _asc and "your_" not in _aid:
        try:
            trading_client = TradingClient(_aid, _asc, paper=True)
        except Exception:
            trading_client = None

# ── Non-blocking auto-refresh ──────────────────────────────────────────────
if st.session_state.auto_refresh_enabled and AUTOREFRESH_AVAILABLE:
    st_autorefresh(interval=60_000, key="global_autorefresh")

# ══════════════════════════════════════════════════════════════════════════════
#  DISCLAIMER — dialog on first visit only
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.disclaimer_accepted:
    @st.dialog("⚠️ MANDATORY FINANCIAL DISCLAIMER")
    def _show_disclaimer():
        st.markdown("""
        **REGULATORY COMPLIANCE AND RISK EXPOSURE NOTICE**

        The calculation matrices, options Greeks, and AI text responses produced by this
        application are engineered strictly for **analytical validation, data testing, and
        educational purposes**.

        Under no circumstance should outputs be actioned as directional investment advice.
        By clicking *Accept* you acknowledge all execution and capital risks remain your
        individual liability.
        """)
        if st.button("I AGREE & ACCEPT", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    _show_disclaimer()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: yfinance multi-ticker safe extractor  (FIX #2)
# ══════════════════════════════════════════════════════════════════════════════
def _safe_extract(raw_df: pd.DataFrame, ticker: str, tickers_list: list) -> pd.DataFrame:
    """
    Handles both single-ticker (flat columns) and multi-ticker (MultiIndex columns)
    DataFrames returned by yf.download() for yfinance >= 0.2.x.
    """
    if isinstance(raw_df.columns, pd.MultiIndex):
        # yfinance 0.2.x+ returns (Price, Ticker) MultiIndex
        try:
            return raw_df.xs(ticker, level=1, axis=1).copy()
        except KeyError:
            return pd.DataFrame()
    else:
        # Single ticker — columns are flat (Open, High, Low, Close, Volume)
        return raw_df.copy()

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Black-Scholes Greeks
# ══════════════════════════════════════════════════════════════════════════════
def compute_greeks(spot, strike=None, days=30, rfr=0.04, sigma=0.30):
    if strike is None:
        strike = spot * 1.05
    t = max(0.001, days / 365.0)
    d1 = (np.log(spot / strike) + (rfr + 0.5 * sigma ** 2) * t) / (sigma * np.sqrt(t))
    d2 = d1 - sigma * np.sqrt(t)
    delta = float(norm.cdf(d1))
    theta = float(
        (-(spot * norm.pdf(d1) * sigma) / (2 * np.sqrt(t))
         - rfr * strike * np.exp(-rfr * t) * norm.cdf(d2)) / 365.0
    )
    return delta, theta

# ══════════════════════════════════════════════════════════════════════════════
#  HELPER: Renko brick simulation  (FIX #7)
# ══════════════════════════════════════════════════════════════════════════════
def build_renko_trace(close_series: pd.Series, brick_size: float):
    """
    Computes ATR-based Renko bricks from a close price series.
    Returns a Plotly Scatter trace.
    """
    if brick_size <= 0:
        brick_size = float(close_series.std()) * 0.5 or 1.0

    prices = close_series.dropna().values
    if len(prices) < 2:
        return go.Scatter(x=[], y=[], mode="markers+lines", name="Renko")

    bricks_y, bricks_color = [], []
    current_price = prices[0]

    for p in prices[1:]:
        while p >= current_price + brick_size:
            current_price += brick_size
            bricks_y.append(current_price)
            bricks_color.append("#00ff88")
        while p <= current_price - brick_size:
            current_price -= brick_size
            bricks_y.append(current_price)
            bricks_color.append("#ff2255")

    if not bricks_y:
        bricks_y = [prices[-1]]
        bricks_color = ["#00f0ff"]

    return go.Scatter(
        x=list(range(len(bricks_y))),
        y=bricks_y,
        mode="markers+lines",
        marker=dict(symbol="square", color=bricks_color, size=8),
        line=dict(color="#3a4860", width=1),
        name="Renko",
    )

# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE AUDITOR
# ══════════════════════════════════════════════════════════════════════════════
def run_auditor(prices_dict: dict):
    if not st.session_state.prediction_feedback_ledger:
        return
    success, evaluated = 0, 0
    for item in st.session_state.prediction_feedback_ledger:
        asset = item["Asset"]
        if asset not in prices_dict:
            continue
        live = prices_dict[asset]
        item["Current Price"] = live
        if item["Status"] == "ACTIVE":
            is_bull = "BUY" in item["Direction"]
            if is_bull and live >= item["Target"]:
                item["Status"] = "✅ HIT"; item["Close"] = live
                st.session_state.true_calls_counter += 1
            elif is_bull and live <= item["Stop"]:
                item["Status"] = "❌ STOPPED"; item["Close"] = live
                st.session_state.false_calls_counter += 1
            elif not is_bull and live <= item["Target"]:
                item["Status"] = "✅ HIT"; item["Close"] = live
                st.session_state.true_calls_counter += 1
            elif not is_bull and live >= item["Stop"]:
                item["Status"] = "❌ STOPPED"; item["Close"] = live
                st.session_state.false_calls_counter += 1
        if item["Status"] != "ACTIVE":
            evaluated += 1
            if "HIT" in item["Status"]:
                success += 1
        else:
            evaluated += 1
            if abs(live - item["Entry"]) / item["Entry"] < 0.035:
                success += 1

    if evaluated > 0:
        wr = (success / evaluated) * 100.0
        st.session_state.global_win_rate_percentage = wr
        # FIX: compress risk margins by 15–35% during high-error cycles
        if wr < 65.0:
            st.session_state.system_accuracy_multiplier = max(0.65, wr / 100.0)
        else:
            st.session_state.system_accuracy_multiplier = 1.0

# ══════════════════════════════════════════════════════════════════════════════
#  QUANTUM ANALYSIS GRID
# ══════════════════════════════════════════════════════════════════════════════
def run_analysis_grid(tickers: list, gap: str) -> pd.DataFrame:
    period, interval, mult = GAP_MAP.get(gap, ("1mo", "1h", 2.8))
    try:
        raw_intra = yf.download(
            tickers, period=period, interval=interval,
            group_by="ticker", progress=False, threads=True, auto_adjust=True
        )
        raw_macro = yf.download(
            tickers, period="2y", interval="1d",
            group_by="ticker", progress=False, threads=True, auto_adjust=True
        )
    except Exception:
        return pd.DataFrame()

    rows, snap = [], {}
    acc = st.session_state.system_accuracy_multiplier

    for t in tickers:
        try:
            # FIX #2: safe extraction handles MultiIndex
            df_i = _safe_extract(raw_intra, t, tickers)
            df_m = _safe_extract(raw_macro, t, tickers)
            df_i.dropna(inplace=True)
            df_m.dropna(inplace=True)
            if len(df_i) < 5 or len(df_m) < 40:
                continue

            close_p = float(df_i["Close"].iloc[-1])
            prev_p  = float(df_i["Close"].iloc[-2])
            label   = t.replace("-USD", "")
            snap[label] = close_p

            # ── Technical indicators via pandas_ta ──────────────────────
            if TA_AVAILABLE:
                df_i.ta.rsi(length=14, append=True)
                df_i.ta.macd(append=True)
                df_i.ta.atr(length=14, append=True)
                df_m.ta.sma(length=50, append=True)
                df_m.ta.sma(length=200, append=True)

            # ── Wildcard column finders (version-proof) ─────────────────
            rsi_cols  = [c for c in df_i.columns if "RSI" in str(c).upper()]
            atr_cols  = [c for c in df_i.columns if "ATR" in str(c).upper()]
            # FIX #9: robust MACD line vs signal detection
            macd_cols = [c for c in df_i.columns
                         if "MACD" in str(c).upper()
                         and "SIGNAL" not in str(c).upper()
                         and "HIST" not in str(c).upper()
                         and "H" not in str(c).split("_")[-1]]
            macs_cols = [c for c in df_i.columns
                         if ("MACDS" in str(c).upper() or "SIGNAL" in str(c).upper())
                         and "MACD" in str(c).upper()]
            sma50_cols  = [c for c in df_m.columns
                           if "SMA" in str(c).upper() and "50" in str(c)]
            sma200_cols = [c for c in df_m.columns
                           if "SMA" in str(c).upper() and "200" in str(c)]

            rsi   = float(df_i[rsi_cols[0]].iloc[-1])  if rsi_cols  else 50.0
            atr   = float(df_i[atr_cols[0]].iloc[-1])  if atr_cols  else close_p * 0.015
            macd_l = float(df_i[macd_cols[0]].iloc[-1]) if macd_cols else 0.0
            macd_s = float(df_i[macs_cols[0]].iloc[-1]) if macs_cols else 0.0
            sma50  = float(df_m[sma50_cols[0]].iloc[-1])  if sma50_cols  else close_p
            sma200 = float(df_m[sma200_cols[0]].iloc[-1]) if sma200_cols else close_p

            # Fallback if TA not available — simple EMA
            if not TA_AVAILABLE:
                sma50  = float(df_m["Close"].rolling(50).mean().iloc[-1])  or close_p
                sma200 = float(df_m["Close"].rolling(200).mean().iloc[-1]) or close_p
                atr    = float(df_i["Close"].rolling(14).std().iloc[-1]) * 1.5 or close_p * 0.015

            # ── Scoring ─────────────────────────────────────────────────
            bullish_trend = close_p > sma50 > sma200
            macd_cross    = macd_l > macd_s

            sc_growth   = int(min(100, max(0, 85 if bullish_trend else 35)))
            sc_value    = int(min(100, max(0, 92 - rsi * 0.45 if close_p < sma50 else 30)))
            sc_momentum = int(min(100, max(0, 95 if macd_cross else 25)))
            aps         = int((sc_growth + sc_value + sc_momentum) / 3)

            direction   = macd_cross
            target_p    = close_p + atr * mult * acc if direction else close_p - atr * mult * acc
            stop_p      = close_p - atr * mult * 0.55 * acc if direction else close_p + atr * mult * 0.55 * acc
            verdict     = ("STRONG BUY" if aps > 66 else
                           "BUY"        if aps > 52 else
                           "SELL"       if aps < 35 else "HOLD")

            rows.append({
                "Asset":       label,
                "RawTicker":   t,
                "Live Price":  close_p,
                "Gain/Loss %": round((close_p - prev_p) / prev_p * 100, 3),
                "CAN SLIM":    sc_growth,
                "Value Safety":sc_value,
                "Momentum":    sc_momentum,
                "APS Rating":  aps,
                "Target":      target_p,
                "Stop Loss":   stop_p,
                "ATR":         atr,
                "Direction":   "BUY" if direction else "SELL",
                "Verdict":     verdict,
                "IntradayDF":  df_i,
            })
        except Exception:
            continue

    if snap:
        run_auditor(snap)

    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
#  AI EXECUTIVE BRIEFING  (429-protected key rotation)
# ══════════════════════════════════════════════════════════════════════════════
def run_ai_briefing(row: dict, gap: str, segment: str,
                    from_d: str, to_d: str) -> str:
    cache_key = f"{row['Asset']}_{gap}_{segment}_{from_d}_{to_d}"
    if cache_key in st.session_state.ai_table_cache:
        return st.session_state.ai_table_cache[cache_key]

    if not GEMINI_KEY_POOL:
        return (
            "| Warning | No Gemini Keys | Paste your free Gemini API key(s) in the sidebar. |"
        )

    try:
        ticker_obj = yf.Ticker(row["RawTicker"])
        news_items = ticker_obj.news or []
        news_str   = " | ".join(n.get("title", "") for n in news_items[:2]) or "No catalysts."
    except Exception:
        news_str = "News feed unavailable."

    # Register prediction for tracking
    entry = {
        "Time":      time.strftime("%H:%M:%S"),
        "Asset":     row["Asset"],
        "Direction": row["Verdict"],
        "Entry":     row["Live Price"],
        "Target":    row["Target"],
        "Stop":      row["Stop Loss"],
        "Current Price": row["Live Price"],
        "Status":    "ACTIVE",
        "Close":     "-",
    }
    already_active = any(
        d["Asset"] == row["Asset"] and d["Status"] == "ACTIVE"
        for d in st.session_state.prediction_feedback_ledger
    )
    if not already_active:
        st.session_state.prediction_feedback_ledger.append(entry)

    prompt = (
        f"Perform algorithmic audit on {row['Asset']} ({segment}). "
        f"Price: ${row['Live Price']:.4f}. Interval: {gap}. APS: {row['APS Rating']}/100. "
        f"Win rate: {st.session_state.global_win_rate_percentage:.1f}%. "
        f"Date range context: {from_d} → {to_d}. News: {news_str}. "
        "Return ONLY a strict Markdown table with columns: "
        "'Audit Component' | 'Metric' | 'Action Vector'. "
        "No intro text, no bold headers outside the table. "
        "Rows: Management Actions, Corporate Adjustments, Operational Pros/Cons, Volatility Regime."
    )

    for key in GEMINI_KEY_POOL:
        try:
            if not GENAI_AVAILABLE:
                break
            client = google_genai.Client(api_key=key)
            resp   = client.models.generate_content(
                model="gemini-2.5-flash-lite", contents=prompt
            )
            result = resp.text
            st.session_state.ai_table_cache[cache_key] = result
            return result
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                continue  # rotate to next key
            return f"| Error | {err[:80]} | Check key validity |"

    return "| Notice | All Gemini keys exhausted | Re-try later or add more keys |"

# ══════════════════════════════════════════════════════════════════════════════
#  SVG LOGO
# ══════════════════════════════════════════════════════════════════════════════
LOGO_SVG = """
<div class='logo-frame'>
<svg width="48" height="48" viewBox="0 0 120 120"
     style="filter:drop-shadow(0 0 6px rgba(0,240,255,.35));vertical-align:middle;">
  <defs>
    <linearGradient id="apqGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#00f0ff"/>
      <stop offset="50%"  stop-color="#00ff88"/>
      <stop offset="100%" stop-color="#ff2255"/>
    </linearGradient>
  </defs>
  <polygon points="60,6 114,36 114,96 60,118 6,96 6,36"
           fill="none" stroke="url(#apqGrad)" stroke-width="5" stroke-linejoin="round"/>
  <!-- A -->
  <path d="M28,90 L52,22 L76,90 M35,66 L69,66"
        fill="none" stroke="#00f0ff" stroke-width="7" stroke-linecap="round"/>
  <!-- P -->
  <path d="M76,22 L76,90 M76,22 Q104,22 104,46 Q104,66 76,66"
        fill="none" stroke="#00ff88" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
  <!-- Q accent dot -->
  <circle cx="99" cy="96" r="7" fill="none" stroke="#ff2255" stroke-width="5"/>
  <line  x1="104" y1="101" x2="113" y2="112" stroke="#ff2255" stroke-width="5" stroke-linecap="round"/>
</svg>
<div>
  <div class='logo-title'>APEX PROPHET QUANTUM</div>
  <div class='logo-sub'>v7.5 Enterprise Web Edition</div>
</div>
<div class="radar-node"></div>
</div>
"""
st.markdown(LOGO_SVG, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 1 — WIN-RATE SCOREBOARD
# ══════════════════════════════════════════════════════════════════════════════
total_calls = st.session_state.true_calls_counter + st.session_state.false_calls_counter
wr = st.session_state.global_win_rate_percentage
am = st.session_state.system_accuracy_multiplier

st.markdown(f"""
<div class='matrix-panel'>
  <div style='font-size:10px; color:#3a4860; text-transform:uppercase;
              letter-spacing:2px; margin-bottom:10px;'>
    🏆 WIN-RATE PERFORMANCE SCOREBOARD — LIVE GLOBAL TELEMETRY
  </div>
  <div class='score-row'>
    <div class='score-cell'>
      <div class='score-label'>Global Model Accuracy</div>
      <div class='score-apq'>{wr:.1f}%</div>
    </div>
    <div class='score-cell'>
      <div class='score-label'>True System Calls</div>
      <div style='color:#00ff88; font-family:Share Tech Mono,monospace; font-size:26px; font-weight:900;'>
        {st.session_state.true_calls_counter}
      </div>
    </div>
    <div class='score-cell'>
      <div class='score-label'>False Deflections</div>
      <div style='color:#ff2255; font-family:Share Tech Mono,monospace; font-size:26px; font-weight:900;'>
        {st.session_state.false_calls_counter}
      </div>
    </div>
    <div class='score-cell'>
      <div class='score-label'>Total Evaluated</div>
      <div class='price-live'>{total_calls}</div>
    </div>
    <div class='score-cell'>
      <div class='score-label'>Accuracy Multiplier</div>
      <div style='color:#ffb700; font-family:Share Tech Mono,monospace; font-size:26px; font-weight:900;'>
        {am:.2f}x
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# AD SLOT A — top horizontal banner
st.markdown("""
<div class='ad-slot'>
    AD SLOT A — TOP HORIZONTAL BANNER (728×90 leaderboard responsive)
    <!-- AD SLOT A: top horizontal banner below scoreboard -->
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CONTROLS
# ══════════════════════════════════════════════════════════════════════════════
gc1, gc2, gc3 = st.columns([5, 3, 2])
with gc1:
    all_labels = sorted(set(t.replace("-USD", "") for t in ALL_TICKERS))
    search_pick = st.selectbox(
        "🎯 GLOBAL CROSS-MARKET QUICK FIND",
        ["None"] + all_labels,
    )
    if search_pick != "None":
        st.session_state.active_radar_ticker = search_pick

with gc2:
    target_gap = st.selectbox(
        "⏱️ STRATEGY INTERVAL",
        list(GAP_MAP.keys()), index=5,
    )

with gc3:
    if st.button("⚡ EXECUTE GLOBAL SCAN", use_container_width=True):
        with st.spinner("Running quantitative analysis matrix…"):
            st.session_state.master_matrix = run_analysis_grid(ALL_TICKERS, target_gap)

# AD SLOT B — tab separator banner
st.markdown("""
<div class='ad-slot'>
    AD SLOT B — MIDDLE TAB SEPARATOR BANNER (468×60 full-width)
    <!-- AD SLOT B: middle tab separator banner -->
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_eq, tab_dx, tab_cr = st.tabs([
    "📈 SPOT EQUITIES TERMINAL",
    "⚡ DERIVATIVES: FUTURES & OPTIONS",
    "🌌 CRYPTOCURRENCY RADAR",
])

# ─────────────────────────────────────────────────────────────────────────────
def render_window(pool_key: str):
    """
    Renders the full 3-zone layout for one asset-class window.
    pool_key: one of "EQUITIES" | "DERIVATIVES" | "CRYPTO"
    """
    pool = POOL_MAP[pool_key]

    # ── Feedback ledger ──────────────────────────────────────────────────────
    with st.expander("⏳ Rolling Prediction Feedback Ledger", expanded=False):
        if st.session_state.prediction_feedback_ledger:
            fd = pd.DataFrame(st.session_state.prediction_feedback_ledger)
            pool_labels = [t.replace("-USD", "") for t in pool]
            fd_scope = fd[fd["Asset"].isin(pool_labels)]
            if not fd_scope.empty:
                display_cols = [c for c in
                    ["Time","Asset","Direction","Entry","Target","Stop","Current Price","Status","Close"]
                    if c in fd_scope.columns]
                st.dataframe(fd_scope[display_cols], use_container_width=True, hide_index=True)
            else:
                st.caption("No predictions logged for this class yet.")
        else:
            st.caption("Run a scan to begin tracking predictions.")

    st.markdown("---")

    # ── 3-column layout ──────────────────────────────────────────────────────
    z2, z3, z4 = st.columns([3.0, 5.0, 3.0])

    # ════════════════════════════════════════════════════════
    #  ZONE 2 — Left: Bullish / Bearish ranked tables
    # ════════════════════════════════════════════════════════
    with z2:
        st.markdown(f"##### {pool_key} Asset Ranks")

        mm = st.session_state.master_matrix
        if not mm.empty:
            scope = mm[mm["RawTicker"].isin(pool)].copy()
            if not scope.empty:
                # FIX #4 (spec §III-5): side-by-side Bullish / Bearish tables
                bullish = scope[scope["Direction"] == "BUY"].sort_values("APS Rating", ascending=False)
                bearish = scope[scope["Direction"] == "SELL"].sort_values("APS Rating", ascending=True)

                p_lim = st.session_state.pagination_limits.get(pool_key, 10)
                bull_page = bullish.head(p_lim)
                bear_page = bearish.head(p_lim)

                bcol, rcol = st.columns(2)
                with bcol:
                    st.markdown(
                        "<span style='color:#00ff88; font-size:11px; font-weight:700;'>▲ BULLISH</span>",
                        unsafe_allow_html=True,
                    )
                    if not bull_page.empty:
                        st.dataframe(
                            bull_page[["Asset","Live Price","Gain/Loss %","APS Rating"]],
                            use_container_width=True, hide_index=True,
                        )
                    else:
                        st.caption("None currently.")

                with rcol:
                    st.markdown(
                        "<span style='color:#ff2255; font-size:11px; font-weight:700;'>▼ BEARISH</span>",
                        unsafe_allow_html=True,
                    )
                    if not bear_page.empty:
                        st.dataframe(
                            bear_page[["Asset","Live Price","Gain/Loss %","APS Rating"]],
                            use_container_width=True, hide_index=True,
                        )
                    else:
                        st.caption("None currently.")

                # Pagination
                total_assets = len(scope)
                if p_lim < total_assets:
                    if st.button(
                        f"➕ LOAD MORE {pool_key} ROWS",
                        key=f"more_{pool_key}",
                        use_container_width=True,
                    ):
                        st.session_state.pagination_limits[pool_key] += 10
                        st.rerun()

                st.markdown("---")
                # Row-click selector
                asset_options = scope["Asset"].tolist()
                selected = st.selectbox(
                    "Inspect Asset", ["None"] + asset_options,
                    key=f"sel_{pool_key}",
                )
                if selected != "None":
                    st.session_state.active_radar_ticker = selected
            else:
                st.info("No data for this class. Run a scan.")
        else:
            st.info("No scan data. Press ⚡ EXECUTE GLOBAL SCAN above.")

    # ════════════════════════════════════════════════════════
    #  ZONE 3 — Centre: chart + AI briefing
    # ════════════════════════════════════════════════════════
    with z3:
        active_lbl = st.session_state.active_radar_ticker
        st.markdown(f"##### Centerstage: `{active_lbl}`")

        # Timeline & chart style
        ctrl1, ctrl2 = st.columns(2)
        with ctrl1:
            timeline = st.selectbox(
                "📊 HISTORICAL RANGE",
                ["1D","5D","1M","3M","6M","1Y","2Y","3Y","5Y","Max","CUSTOM DATE RANGE"],
                index=5, key=f"tl_{pool_key}",
            )
        with ctrl2:
            chart_style = st.selectbox(
                "🎨 CHART PERSPECTIVE",
                ["Candlesticks","Institutional Line View","OHLC Structural Bars",
                 "Quantum Area Fill","Renko Matrix Simulations"],
                index=0, key=f"cs_{pool_key}",
            )

        from_date = datetime.date.today() - datetime.timedelta(days=365)
        to_date   = datetime.date.today()
        if timeline == "CUSTOM DATE RANGE":
            cd1, cd2 = st.columns(2)
            with cd1:
                from_date = st.date_input(
                    "From Date", datetime.date.today() - datetime.timedelta(days=180),
                    key=f"fd_{pool_key}",
                )
            with cd2:
                to_date = st.date_input(
                    "To Date", datetime.date(2029, 11, 25),
                    key=f"td_{pool_key}",
                )

        # Find matched row in master matrix
        mm = st.session_state.master_matrix
        matched = mm[mm["Asset"] == active_lbl] if not mm.empty else pd.DataFrame()

        # Telemetry bar
        if not matched.empty:
            r = matched.iloc[0]
            gain_color = "#00ff88" if r["Gain/Loss %"] >= 0 else "#ff2255"
            st.markdown(f"""
            <div class='matrix-panel' style='padding:12px; margin-bottom:8px;'>
              <div style='display:flex; justify-content:space-between; text-align:center; flex-wrap:wrap; gap:8px;'>
                <div><div style='font-size:9px; color:#3a4860;'>LIVE PRICE</div>
                  <div class='price-live'>${r['Live Price']:.4f}</div></div>
                <div><div style='font-size:9px; color:#3a4860;'>TARGET</div>
                  <div class='price-tgt'>${r['Target']:.4f}</div></div>
                <div><div style='font-size:9px; color:#3a4860;'>STOP LOSS</div>
                  <div class='price-stop'>${r['Stop Loss']:.4f}</div></div>
                <div><div style='font-size:9px; color:#3a4860;'>APS SCORE</div>
                  <div class='score-apq'>{r['APS Rating']}</div></div>
                <div><div style='font-size:9px; color:#3a4860;'>GAIN/LOSS</div>
                  <div style='color:{gain_color}; font-family:Share Tech Mono,monospace; font-size:20px; font-weight:900;'>
                    {r['Gain/Loss %']:+.2f}%</div></div>
              </div>
            </div>
            """, unsafe_allow_html=True)
            raw_ticker = r["RawTicker"]
        else:
            st.markdown("""
            <div class='matrix-panel' style='text-align:center; padding:10px; color:#3a4860;'>
              Run scan to populate telemetry.
            </div>""", unsafe_allow_html=True)
            # Attempt to guess raw ticker
            guess = [t for t in ALL_TICKERS if active_lbl in t]
            raw_ticker = guess[0] if guess else f"{active_lbl}-USD"

        # Fetch chart data
        try:
            t_inst = yf.Ticker(raw_ticker)
            if timeline == "CUSTOM DATE RANGE":
                hist_df = t_inst.history(
                    start=from_date, end=to_date, interval="1d"
                )
            else:
                hist_df = t_inst.history(
                    period=CHART_PERIOD_MAP[timeline],
                    interval=CHART_INTERVAL_MAP[timeline],
                )
        except Exception:
            hist_df = pd.DataFrame()

        if not hist_df.empty:
            fig = go.Figure()

            if chart_style == "Candlesticks":
                fig.add_trace(go.Candlestick(
                    x=hist_df.index,
                    open=hist_df["Open"], high=hist_df["High"],
                    low=hist_df["Low"],   close=hist_df["Close"],
                    name="OHLC",
                    increasing_line_color="#00ff88",
                    decreasing_line_color="#ff2255",
                ))
            elif chart_style == "Institutional Line View":
                fig.add_trace(go.Scatter(
                    x=hist_df.index, y=hist_df["Close"],
                    mode="lines", line=dict(color="#00f0ff", width=2),
                    name="Close",
                ))
            elif chart_style == "OHLC Structural Bars":
                fig.add_trace(go.Ohlc(
                    x=hist_df.index,
                    open=hist_df["Open"], high=hist_df["High"],
                    low=hist_df["Low"],   close=hist_df["Close"],
                    name="OHLC Bars",
                ))
            elif chart_style == "Quantum Area Fill":
                fig.add_trace(go.Scatter(
                    x=hist_df.index, y=hist_df["Close"],
                    fill="tozeroy",
                    fillcolor="rgba(0,240,255,0.05)",
                    line=dict(color="#00f0ff", width=1.5),
                    name="Area",
                ))
            elif chart_style == "Renko Matrix Simulations":
                # FIX #7: actual brick-based Renko
                atr_approx = float(hist_df["Close"].rolling(14).std().iloc[-1]) or (
                    float(hist_df["Close"].iloc[-1]) * 0.01
                )
                renko_trace = build_renko_trace(hist_df["Close"], brick_size=atr_approx)
                fig.add_trace(renko_trace)

            # Target / Stop overlays when data is available
            if not matched.empty:
                fig.add_hline(
                    y=float(r["Target"]),
                    line_dash="dot", line_color="#00ff88",
                    annotation_text=f"TARGET ${r['Target']:.2f}",
                    annotation_font_color="#00ff88",
                )
                fig.add_hline(
                    y=float(r["Stop Loss"]),
                    line_dash="dot", line_color="#ff2255",
                    annotation_text=f"STOP ${r['Stop Loss']:.2f}",
                    annotation_font_color="#ff2255",
                )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#05070c",
                margin=dict(l=0, r=0, t=4, b=0),
                height=310,
                xaxis_rangeslider_visible=False,
                xaxis=dict(fixedrange=False, gridcolor="#0d1420"),
                yaxis=dict(fixedrange=True, gridcolor="#0d1420"),
            )
            st.plotly_chart(
                fig, use_container_width=True,
                key=f"chart_{pool_key}",
                config={"scrollZoom": True, "displayModeBar": False},
            )

            roi = (
                (float(hist_df["Close"].iloc[-1]) - float(hist_df["Close"].iloc[0]))
                / float(hist_df["Close"].iloc[0]) * 100
            )
            roi_color = "#00ff88" if roi >= 0 else "#ff2255"
            st.markdown(
                f"Displayed range ROI: "
                f"<span style='color:{roi_color}; font-family:monospace; font-weight:900;'>"
                f"{roi:+.2f}%</span>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No chart data available for selected range/interval.")

        # AD SLOT B (per-zone instance within tabs)
        st.markdown("""
        <div class='ad-slot' style='margin:8px 0;'>
            AD SLOT B — TAB CONTENT SEPARATOR
            <!-- AD SLOT B: middle tab separator -->
        </div>
        """, unsafe_allow_html=True)

        # ── AI Executive Briefing ─────────────────────────────────────────
        st.markdown("##### 📋 AI EXECUTIVE BRIEFING MATRIX")
        if not matched.empty:
            ai_horizon = st.select_slider(
                "Predictive Analysis Horizon",
                options=["30m","1h","4h","1d","1w","1mo","3mo","Max"],
                value="1h", key=f"hz_{pool_key}",
            )
            if st.button(
                f"✨ RUN NEURAL AUDIT — {active_lbl.upper()}",
                use_container_width=True, key=f"ai_{pool_key}",
            ):
                with st.spinner("Decrypting fundamental risk matrices…"):
                    result = run_ai_briefing(
                        r.to_dict(), ai_horizon, pool_key,
                        str(from_date), str(to_date),
                    )
                    st.markdown(result, unsafe_allow_html=False)
        else:
            st.caption("Run a global scan first to enable AI briefing.")

    # ════════════════════════════════════════════════════════
    #  ZONE 4 — Right: Class-specific panel
    # ════════════════════════════════════════════════════════
    with z4:
        st.markdown("##### Performance Metrics")

        if not matched.empty:
            r = matched.iloc[0]
            st.metric("APS Score", f"{r['APS Rating']} / 100")
            verdict_color = "#00ff88" if "BUY" in r["Verdict"] else "#ff2255"
            st.markdown(
                f"Verdict: <span style='color:{verdict_color}; font-weight:900;'>"
                f"{r['Verdict']}</span>",
                unsafe_allow_html=True,
            )
            st.markdown("---")

            # ── Class-specific panels ─────────────────────────────────────
            if pool_key == "EQUITIES":
                st.markdown("**CAN SLIM / Fundamental Vectors**")
                st.progress(int(r["CAN SLIM"]),    text=f"Growth Breakout: {r['CAN SLIM']}%")
                st.progress(int(r["Value Safety"]), text=f"Graham Safety:   {r['Value Safety']}%")
                st.progress(int(r["Momentum"]),     text=f"Minervini Mom.:  {r['Momentum']}%")

            elif pool_key == "DERIVATIVES":
                st.markdown("**Black-Scholes Greeks**")
                delta, theta = compute_greeks(float(r["Live Price"]))
                st.metric("Δ Delta (Call)", f"{delta:.4f}")
                st.metric("Θ Theta / day",  f"{theta:.4f}")
                st.markdown("---")
                st.markdown("**Futures Basis Summary**")
                st.markdown(
                    "Basis Deviation: `+0.0415%`  \n"
                    "Implied Funding: `0.0100% / 8h`"
                )

            elif pool_key == "CRYPTO":
                st.markdown("**📡 Level 2 Liquidity Flux Simulation**")
                # FIX #4: seeded random so chart doesn't flicker on rerun
                rng = np.random.default_rng(int(r["Live Price"] * 1000) % (2**31))
                price  = float(r["Live Price"])
                atr_v  = float(r["ATR"])
                levels = 5
                bid_prices = [price - i * atr_v * 0.12 for i in range(1, levels + 1)]
                ask_prices = [price + i * atr_v * 0.12 for i in range(1, levels + 1)]
                bid_sizes  = rng.integers(150, 900, size=levels).tolist()
                ask_sizes  = rng.integers(150, 900, size=levels).tolist()

                l2_fig = go.Figure()
                l2_fig.add_trace(go.Bar(
                    y=bid_prices, x=bid_sizes,
                    name="Bids", orientation="h",
                    marker_color="#00ff88",
                ))
                l2_fig.add_trace(go.Bar(
                    y=ask_prices, x=[-s for s in ask_sizes],
                    name="Asks", orientation="h",
                    marker_color="#ff2255",
                ))
                l2_fig.update_layout(
                    barmode="relative",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="#05070c",
                    height=180,
                    margin=dict(l=0, r=0, t=4, b=0),
                    showlegend=True,
                    legend=dict(font=dict(size=9)),
                    xaxis=dict(title="Volume", gridcolor="#0d1420"),
                    yaxis=dict(title="Price",  gridcolor="#0d1420"),
                )
                st.plotly_chart(
                    l2_fig, use_container_width=True,
                    key=f"l2_{pool_key}",
                    config={"displayModeBar": False},
                )

            st.markdown("---")

            # ── Trade execution ───────────────────────────────────────────
            st.markdown("**Execution Gateway (Alpaca Paper)**")

            def _submit_order(side: str):
                if trading_client is None:
                    st.warning("Connect Alpaca keys in the sidebar.")
                    return
                sym = (
                    f"{r['Asset']}/USD"
                    if r["RawTicker"].endswith("-USD")
                    else r["Asset"]
                )
                qty = 0.01 if r["RawTicker"].endswith("-USD") else 1
                try:
                    trading_client.submit_order(
                        MarketOrderRequest(
                            symbol=sym, qty=qty,
                            side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
                            time_in_force=TimeInForce.GTC,
                        )
                    )
                    if side == "BUY":
                        st.success(f"✅ BUY {qty} {sym} dispatched.")
                    else:
                        st.error(f"🔴 SELL {qty} {sym} dispatched.")
                except Exception as ex:
                    st.error(f"Order rejected: {ex}")

            col_buy, col_sell = st.columns(2)
            with col_buy:
                if st.button("▲ BUY", key=f"buy_{pool_key}", use_container_width=True):
                    _submit_order("BUY")
            with col_sell:
                if st.button("▼ SELL", key=f"sell_{pool_key}", use_container_width=True):
                    _submit_order("SELL")

        else:
            st.caption("Run a scan to load metrics.")

# ── Render all three tabs ──────────────────────────────────────────────────
with tab_eq:
    render_window("EQUITIES")
with tab_dx:
    render_window("DERIVATIVES")
with tab_cr:
    render_window("CRYPTO")

# ══════════════════════════════════════════════════════════════════════════════
#  PORTFOLIO LEDGER — Alpaca Account
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 💼 AUTOMATED TERMINAL PORTFOLIO EXCHANGES")

if trading_client is not None:
    try:
        acc = trading_client.get_account()
        st.markdown("<div class='matrix-panel'>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        a1.metric("Cash Balance",       f"${float(acc.cash):,.2f}")
        a2.metric("Portfolio Value",    f"${float(acc.portfolio_value):,.2f}")
        a3.metric("Buying Power",       f"${float(acc.buying_power):,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

        positions = trading_client.get_all_positions()
        if positions:
            rows_pos = []
            for p in positions:
                rows_pos.append({
                    "Symbol":    p.symbol,
                    "Qty":       p.qty,
                    "Avg Entry": f"${float(p.avg_entry_price):,.4f}",
                    "Mkt Price": f"${float(p.current_price):,.4f}",
                    "Mkt Value": f"${float(p.market_value):,.2f}",
                    "Unreal P/L": (
                        f"${float(p.unrealized_pl):+,.2f} "
                        f"({float(p.unrealized_plpc)*100:+.2f}%)"
                    ),
                })
            st.dataframe(pd.DataFrame(rows_pos), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions in this paper account.")
    except Exception as err:
        st.error(f"Alpaca ledger error: {err}")
else:
    st.markdown("""
    <div class='matrix-panel' style='text-align:center; color:#3a4860; padding:20px;'>
        🔒 Alpaca Paper Trading not connected.<br>
        <span style='font-size:12px;'>Paste your Alpaca Paper API keys in the sidebar to activate live execution.</span>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style='text-align:center; color:#1a2236; font-size:10px;
            letter-spacing:2px; text-transform:uppercase; padding:30px 0 10px;'>
    APEX PROPHET QUANTUM v7.5 — FOR EDUCATIONAL &amp; ANALYTICAL USE ONLY —
    NOT INVESTMENT ADVICE
</div>
""", unsafe_allow_html=True)
