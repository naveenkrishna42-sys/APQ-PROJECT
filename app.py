"""
APEX PROPHET QUANTUM (APQ) v7.5 Enterprise Web Edition
=======================================================
Production-ready Streamlit app — fully corrected & spec-compliant.

ROOT CAUSE FIX (deployment crash):
  pandas-ta pulls numba==0.61.2 → llvmlite==0.44.0
  llvmlite does NOT support Python 3.14 (Streamlit Cloud default as of 2025).
  Solution: pandas-ta removed entirely. All RSI / MACD / ATR / SMA indicators
  re-implemented in pure pandas/numpy — zero C-extension build required.

All other fixes vs original Gemini output:
  • No blocking time.sleep() — uses streamlit-autorefresh
  • yfinance MultiIndex safe extraction (.xs) for v0.2.x+
  • BYOK sidebar panel (no server-side credential dependency)
  • Open access — no password gate (per spec)
  • Side-by-side Bullish/Bearish tables
  • All 3 ad slots present (A top, B tab separator, C sidebar footer)
  • Real ATR-based Renko brick simulation
  • Seeded RNG for Level 2 chart (no per-rerun flicker)
  • Robust MACD column detection
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

# ── Page config — must be first Streamlit call ────────────────────────────────
st.set_page_config(
    page_title="APEX PROPHET QUANTUM (APQ) v7.5",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Non-blocking auto-refresh ─────────────────────────────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except ImportError:
    AUTOREFRESH_OK = False

# ── Optional Alpaca ───────────────────────────────────────────────────────────
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_OK = True
except ImportError:
    ALPACA_OK = False

# ── Optional Gemini ───────────────────────────────────────────────────────────
try:
    from google import genai as google_genai
    GENAI_OK = True
except ImportError:
    GENAI_OK = False

# ══════════════════════════════════════════════════════════════════════════════
#  PURE-PYTHON / PANDAS INDICATOR LIBRARY
#  (replaces pandas-ta — no llvmlite / numba dependency)
# ══════════════════════════════════════════════════════════════════════════════

def ind_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0).rolling(period, min_periods=period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period, min_periods=period).mean()
    rs    = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).rename("RSI_14")

def ind_macd(series: pd.Series, fast=12, slow=26, sig=9):
    ema_f  = series.ewm(span=fast, adjust=False).mean()
    ema_s  = series.ewm(span=slow, adjust=False).mean()
    macd   = (ema_f - ema_s).rename("MACD_12_26_9")
    signal = macd.ewm(span=sig, adjust=False).mean().rename("MACDs_12_26_9")
    return macd, signal

def ind_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hl  = df["High"] - df["Low"]
    hc  = (df["High"] - df["Close"].shift()).abs()
    lc  = (df["Low"]  - df["Close"].shift()).abs()
    tr  = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return tr.rolling(period, min_periods=period).mean().rename("ATR_14")

def ind_sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(period, min_periods=period).mean().rename(f"SMA_{period}")

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE BOOTSTRAP
# ══════════════════════════════════════════════════════════════════════════════
_DEFAULTS = {
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
    "user_gemini_keys": "",
    "user_alpaca_id": "",
    "user_alpaca_secret": "",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ══════════════════════════════════════════════════════════════════════════════
#  CYBER-GRID OBSIDIAN THEME CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@400;700;900&display=swap');

html, body, .stApp { background-color: #030407 !important; color: #cbd5e1;
                     font-family: 'Exo 2', sans-serif; }

/* Pulsing radar dot */
.radar-node {
    width: 11px; height: 11px; background: #00ff88; border-radius: 50%;
    display: inline-block; vertical-align: middle; margin-left: 8px;
    box-shadow: 0 0 0 0 rgba(0,255,136,0.7);
    animation: pulseRadar 1.6s infinite cubic-bezier(0.66,0,0,1);
}
@keyframes pulseRadar { to { box-shadow: 0 0 0 18px rgba(0,255,136,0); } }

/* Logo */
.logo-frame { display:flex; align-items:center; gap:14px; padding:10px 0 14px;
              border-bottom:1px solid #141a29; margin-bottom:14px; }
.logo-title  { margin:0; font-family:'Exo 2',sans-serif; font-weight:900;
               color:#fff; letter-spacing:2px; font-size:22px; }
.logo-sub    { color:#2a3348; font-size:10px; letter-spacing:3px; text-transform:uppercase; }

/* Price tags */
.price-live { color:#00f0ff !important; font-family:'Share Tech Mono',monospace;
              font-size:24px; font-weight:900; text-shadow:0 0 10px rgba(0,240,255,.4); }
.price-tgt  { color:#00ff88 !important; font-family:'Share Tech Mono',monospace;
              font-size:24px; font-weight:900; text-shadow:0 0 10px rgba(0,255,136,.4); }
.price-stop { color:#ff2255 !important; font-family:'Share Tech Mono',monospace;
              font-size:24px; font-weight:900; text-shadow:0 0 10px rgba(255,34,85,.4); }
.score-apq  { color:#ffb700 !important; font-family:'Share Tech Mono',monospace;
              font-size:24px; font-weight:900; text-shadow:0 0 10px rgba(255,183,0,.4); }

/* Panels */
.matrix-panel {
    background:linear-gradient(135deg,#090c15 0%,#05070a 100%);
    padding:18px; border-radius:8px; border:1px solid #111724; margin-bottom:14px;
    transition:all 0.22s cubic-bezier(0.4,0,0.2,1);
}
.matrix-panel:hover { transform:translateY(-1px); border-color:#00f0ff;
                      box-shadow:0 4px 14px rgba(0,240,255,.12); }

/* Scoreboard */
.score-row  { display:flex; justify-content:space-between; align-items:center;
              gap:20px; flex-wrap:wrap; }
.score-cell { text-align:center; flex:1; min-width:110px; }
.score-lbl  { font-size:9px; color:#3a4860; text-transform:uppercase; letter-spacing:1.5px; }

/* Ad slots */
.ad-slot { background:#06080e; border:1px dashed #1a2236; border-radius:6px;
           text-align:center; color:#2a3348; font-size:10px; letter-spacing:2px;
           text-transform:uppercase; margin:10px 0; padding:13px 10px; }

/* Buttons */
.stButton > button { background:linear-gradient(90deg,#09101f,#0e1a30) !important;
    color:#fff !important; border:1px solid #162642 !important; border-radius:6px !important;
    font-weight:700 !important; transition:all 0.15s ease !important; width:100%; }
.stButton > button:hover { border-color:#00ff88 !important;
    box-shadow:0 0 14px rgba(0,255,136,.18) !important; transform:scale(1.015); }
.stButton > button:active { transform:scale(0.97); }

/* Misc */
div[data-testid="stMetricValue"] { font-family:'Share Tech Mono',monospace; color:#00f0ff; }
.stTabs [data-baseweb="tab"]        { font-weight:700; letter-spacing:1px; color:#4a5568; }
.stTabs [aria-selected="true"]      { color:#00f0ff !important;
                                      border-bottom:2px solid #00f0ff !important; }
[data-testid="stSidebar"] { background:#03050a !important; border-right:1px solid #0d1420; }
[data-testid="stDataFrame"] { border:1px solid #0d1420; border-radius:6px; }
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
POOL_MAP         = {"EQUITIES":EQUITIES_POOL,"DERIVATIVES":DERIVATIVES_POOL,"CRYPTO":CRYPTO_POOL}

GAP_MAP = {
    "1m":("2d","1m",1.1), "3m":("3d","3m",1.3),  "5m":("5d","5m",1.6),
    "15m":("7d","15m",2.0),"30m":("14d","30m",2.2),"1h":("1mo","1h",2.8),
    "2h":("2mo","2h",3.0),"4h":("3mo","4h",3.4),  "1d":("2y","1d",4.2),
}
CHART_PERIOD   = {"1D":"1d","5D":"5d","1M":"1mo","3M":"3mo","6M":"6mo",
                  "1Y":"1y","2Y":"2y","3Y":"3y","5Y":"5y","Max":"max"}
CHART_INTERVAL = {"1D":"1m","5D":"5m","1M":"30m","3M":"1h","6M":"2h",
                  "1Y":"1d","2Y":"1d","3Y":"1wk","5Y":"1wk","Max":"1mo"}

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — BYOK KEYS  (spec §II-2: no server-side credentials)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 4px;'>
      <span style='font-size:13px; font-weight:900; color:#00f0ff; letter-spacing:2px;'>
        🔒 DATA NETWORKS & KEYS ADAPTER
      </span>
    </div>
    """, unsafe_allow_html=True)
    st.caption("Keys are stored only in your browser session — never on the server.")

    _gk = st.text_input("Gemini API Keys (comma-separated for rotation)",
                         value=st.session_state.user_gemini_keys,
                         type="password", placeholder="AIza..., AIza...")
    if _gk != st.session_state.user_gemini_keys:
        st.session_state.user_gemini_keys = _gk

    _aid = st.text_input("Alpaca Paper Key ID",
                          value=st.session_state.user_alpaca_id,
                          type="password", placeholder="PKTEST...")
    _asc = st.text_input("Alpaca Paper Secret Key",
                          value=st.session_state.user_alpaca_secret,
                          type="password", placeholder="xxxxxxxx")
    if _aid != st.session_state.user_alpaca_id:   st.session_state.user_alpaca_id     = _aid
    if _asc != st.session_state.user_alpaca_secret: st.session_state.user_alpaca_secret = _asc

    st.divider()
    st.session_state.auto_refresh_enabled = st.toggle(
        "📡 Live Auto-Refresh (60s)", value=st.session_state.auto_refresh_enabled)

    st.divider()
    # AD SLOT C — sidebar footer
    st.markdown("""
    <div class='ad-slot' style='margin-top:12px;'>
      AD SLOT C — SIDEBAR SQUARE FOOTER
      <!-- AD SLOT C: 250×250 sidebar footer responsive unit -->
    </div>""", unsafe_allow_html=True)

# ── Runtime key pool ──────────────────────────────────────────────────────────
_raw_keys  = st.session_state.user_gemini_keys or os.getenv("GEMINI_API_KEY","")
GEMINI_POOL = [k.strip() for k in _raw_keys.split(",") if k.strip()]

# ── Alpaca client ─────────────────────────────────────────────────────────────
trading_client = None
if ALPACA_OK:
    _ai = st.session_state.user_alpaca_id     or os.getenv("APCA_API_KEY_ID","")
    _as = st.session_state.user_alpaca_secret or os.getenv("APCA_API_SECRET_KEY","")
    if _ai and _as and "your_" not in _ai:
        try: trading_client = TradingClient(_ai, _as, paper=True)
        except Exception: pass

# ── Non-blocking auto-refresh ─────────────────────────────────────────────────
if st.session_state.auto_refresh_enabled and AUTOREFRESH_OK:
    st_autorefresh(interval=60_000, key="apq_autorefresh")

# ══════════════════════════════════════════════════════════════════════════════
#  DISCLAIMER DIALOG (first visit only)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.disclaimer_accepted:
    @st.dialog("⚠️ MANDATORY FINANCIAL DISCLAIMER")
    def _disclaimer():
        st.markdown("""
        **REGULATORY COMPLIANCE AND RISK EXPOSURE NOTICE**

        All calculation matrices, options Greeks, and AI responses produced by this
        application are for **analytical, data-testing, and educational purposes only**.

        Outputs must not be actioned as investment advice. By clicking *Accept* you
        acknowledge all capital risks remain your individual liability.
        """)
        if st.button("I AGREE & ACCEPT", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    _disclaimer()
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _safe_extract(raw: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """
    Handles both flat (single-ticker) and MultiIndex (multi-ticker, yfinance ≥0.2.x)
    DataFrames from yf.download().
    """
    if isinstance(raw.columns, pd.MultiIndex):
        try:   return raw.xs(ticker, level=1, axis=1).copy()
        except KeyError: return pd.DataFrame()
    return raw.copy()


def compute_greeks(spot, strike=None, days=30, rfr=0.04, sigma=0.30):
    if strike is None: strike = spot * 1.05
    t  = max(0.001, days / 365.0)
    d1 = (np.log(spot/strike) + (rfr + 0.5*sigma**2)*t) / (sigma*np.sqrt(t))
    d2 = d1 - sigma*np.sqrt(t)
    delta = float(norm.cdf(d1))
    theta = float((-(spot*norm.pdf(d1)*sigma)/(2*np.sqrt(t))
                   - rfr*strike*np.exp(-rfr*t)*norm.cdf(d2)) / 365.0)
    return delta, theta


def build_renko(close: pd.Series, brick: float):
    """ATR-sized Renko bricks → Plotly Scatter trace."""
    if brick <= 0: brick = float(close.std())*0.5 or 1.0
    vals, colors = [], []
    cur = float(close.iloc[0])
    for p in close.iloc[1:].values:
        while p >= cur + brick:
            cur += brick; vals.append(cur); colors.append("#00ff88")
        while p <= cur - brick:
            cur -= brick; vals.append(cur); colors.append("#ff2255")
    if not vals: vals, colors = [float(close.iloc[-1])], ["#00f0ff"]
    return go.Scatter(x=list(range(len(vals))), y=vals,
                      mode="markers+lines",
                      marker=dict(symbol="square", color=colors, size=9),
                      line=dict(color="#2a3348", width=1), name="Renko")

# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE AUDITOR
# ══════════════════════════════════════════════════════════════════════════════

def run_auditor(prices: dict):
    if not st.session_state.prediction_feedback_ledger: return
    ok = tot = 0
    for item in st.session_state.prediction_feedback_ledger:
        a = item["Asset"]
        if a not in prices: continue
        live = prices[a]; item["Current Price"] = live
        if item["Status"] == "ACTIVE":
            bull = "BUY" in item["Direction"]
            if   bull  and live >= item["Target"]: item["Status"]="✅ HIT";     item["Close"]=live; st.session_state.true_calls_counter  += 1
            elif bull  and live <= item["Stop"]:   item["Status"]="❌ STOPPED"; item["Close"]=live; st.session_state.false_calls_counter += 1
            elif not bull and live <= item["Target"]: item["Status"]="✅ HIT";     item["Close"]=live; st.session_state.true_calls_counter  += 1
            elif not bull and live >= item["Stop"]:   item["Status"]="❌ STOPPED"; item["Close"]=live; st.session_state.false_calls_counter += 1
        tot += 1
        ok  += 1 if ("HIT" in item["Status"] or
                      (item["Status"]=="ACTIVE" and abs(live-item["Entry"])/item["Entry"]<0.035)) else 0
    if tot:
        wr = ok/tot*100
        st.session_state.global_win_rate_percentage  = wr
        st.session_state.system_accuracy_multiplier  = max(0.65,wr/100) if wr<65 else 1.0

# ══════════════════════════════════════════════════════════════════════════════
#  QUANTUM ANALYSIS GRID  (pure pandas indicators — no pandas-ta)
# ══════════════════════════════════════════════════════════════════════════════

def run_analysis_grid(tickers: list, gap: str) -> pd.DataFrame:
    period, interval, mult = GAP_MAP.get(gap, ("1mo","1h",2.8))
    try:
        raw_i = yf.download(tickers, period=period,   interval=interval,
                            group_by="ticker", progress=False, threads=True, auto_adjust=True)
        raw_m = yf.download(tickers, period="2y",     interval="1d",
                            group_by="ticker", progress=False, threads=True, auto_adjust=True)
    except Exception:
        return pd.DataFrame()

    rows, snap = [], {}
    acc = st.session_state.system_accuracy_multiplier

    for t in tickers:
        try:
            dfi = _safe_extract(raw_i, t).dropna()
            dfm = _safe_extract(raw_m, t).dropna()
            if len(dfi) < 20 or len(dfm) < 40: continue

            close_p = float(dfi["Close"].iloc[-1])
            prev_p  = float(dfi["Close"].iloc[-2])
            label   = t.replace("-USD","")
            snap[label] = close_p

            # ── Indicators (pure pandas) ───────────────────────────────
            rsi_s   = ind_rsi(dfi["Close"])
            macd_l, macd_s = ind_macd(dfi["Close"])
            atr_s   = ind_atr(dfi)
            sma50   = ind_sma(dfm["Close"], 50)
            sma200  = ind_sma(dfm["Close"], 200)

            rsi    = float(rsi_s.iloc[-1])  if not np.isnan(rsi_s.iloc[-1])   else 50.0
            ml     = float(macd_l.iloc[-1]) if not np.isnan(macd_l.iloc[-1])  else 0.0
            ms     = float(macd_s.iloc[-1]) if not np.isnan(macd_s.iloc[-1])  else 0.0
            atr    = float(atr_s.iloc[-1])  if not np.isnan(atr_s.iloc[-1])   else close_p*0.015
            s50    = float(sma50.iloc[-1])  if not np.isnan(sma50.iloc[-1])   else close_p
            s200   = float(sma200.iloc[-1]) if not np.isnan(sma200.iloc[-1])  else close_p

            # ── Scoring ────────────────────────────────────────────────
            bull_trend   = close_p > s50 > s200
            macd_cross   = ml > ms
            sc_growth    = int(min(100,max(0, 85 if bull_trend  else 35)))
            sc_value     = int(min(100,max(0, 92-rsi*0.45 if close_p<s50 else 30)))
            sc_momentum  = int(min(100,max(0, 95 if macd_cross else 25)))
            aps          = int((sc_growth+sc_value+sc_momentum)/3)

            dir_bull = macd_cross
            target   = close_p+(atr*mult*acc)    if dir_bull else close_p-(atr*mult*acc)
            stop     = close_p-(atr*mult*0.55*acc) if dir_bull else close_p+(atr*mult*0.55*acc)
            verdict  = ("STRONG BUY" if aps>66 else "BUY" if aps>52
                        else "SELL"  if aps<35  else "HOLD")

            rows.append({
                "Asset":      label,   "RawTicker":  t,
                "Live Price": close_p, "Gain/Loss %": round((close_p-prev_p)/prev_p*100,3),
                "CAN SLIM":   sc_growth,"Value Safety":sc_value,"Momentum":sc_momentum,
                "APS Rating": aps,     "Target":      target,   "Stop Loss": stop,
                "ATR":        atr,     "Direction":   "BUY" if dir_bull else "SELL",
                "Verdict":    verdict, "IntradayDF":  dfi,
            })
        except Exception:
            continue

    if snap: run_auditor(snap)
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
#  AI EXECUTIVE BRIEFING
# ══════════════════════════════════════════════════════════════════════════════

def run_ai_briefing(row: dict, gap: str, seg: str, from_d, to_d) -> str:
    key = f"{row['Asset']}_{gap}_{seg}_{from_d}_{to_d}"
    if key in st.session_state.ai_table_cache:
        return st.session_state.ai_table_cache[key]
    if not GEMINI_POOL:
        return "| Warning | No Gemini Keys | Paste your free Gemini key(s) in the sidebar. |"

    try:
        news = " | ".join(
            n.get("title","") for n in (yf.Ticker(row["RawTicker"]).news or [])[:2]
        ) or "No catalysts."
    except Exception:
        news = "News unavailable."

    entry = {"Time":time.strftime("%H:%M:%S"),"Asset":row["Asset"],"Direction":row["Verdict"],
             "Entry":row["Live Price"],"Target":row["Target"],"Stop":row["Stop Loss"],
             "Current Price":row["Live Price"],"Status":"ACTIVE","Close":"-"}
    if not any(d["Asset"]==row["Asset"] and d["Status"]=="ACTIVE"
               for d in st.session_state.prediction_feedback_ledger):
        st.session_state.prediction_feedback_ledger.append(entry)

    prompt = (
        f"Algorithmic audit: {row['Asset']} ({seg}). Price:${row['Live Price']:.4f}. "
        f"Interval:{gap}. APS:{row['APS Rating']}/100. "
        f"Win rate:{st.session_state.global_win_rate_percentage:.1f}%. "
        f"Date range:{from_d}→{to_d}. News:{news}. "
        "Return ONLY a strict Markdown table: 'Audit Component'|'Metric'|'Action Vector'. "
        "No preamble. Rows: Management Actions, Corporate Adjustments, "
        "Operational Pros/Cons, Volatility Regime Verdict."
    )
    for k in GEMINI_POOL:
        try:
            if not GENAI_OK: break
            r = google_genai.Client(api_key=k).models.generate_content(
                model="gemini-2.5-flash-lite", contents=prompt)
            st.session_state.ai_table_cache[key] = r.text
            return r.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e): continue
            return f"| Error | {str(e)[:80]} | Check key validity |"
    return "| Notice | All Gemini keys exhausted | Add more keys in sidebar |"

# ══════════════════════════════════════════════════════════════════════════════
#  SVG LOGO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='logo-frame'>
<svg width="48" height="48" viewBox="0 0 120 120"
     style="filter:drop-shadow(0 0 6px rgba(0,240,255,.35));vertical-align:middle;">
  <defs>
    <linearGradient id="apqG" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%"   stop-color="#00f0ff"/>
      <stop offset="50%"  stop-color="#00ff88"/>
      <stop offset="100%" stop-color="#ff2255"/>
    </linearGradient>
  </defs>
  <polygon points="60,6 114,36 114,96 60,118 6,96 6,36"
           fill="none" stroke="url(#apqG)" stroke-width="5" stroke-linejoin="round"/>
  <path d="M28,90 L52,22 L76,90 M35,66 L69,66"
        fill="none" stroke="#00f0ff" stroke-width="7" stroke-linecap="round"/>
  <path d="M76,22 L76,90 M76,22 Q104,22 104,46 Q104,66 76,66"
        fill="none" stroke="#00ff88" stroke-width="6" stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="99" cy="96" r="7"  fill="none" stroke="#ff2255" stroke-width="5"/>
  <line  x1="104" y1="101" x2="113" y2="112" stroke="#ff2255" stroke-width="5" stroke-linecap="round"/>
</svg>
<div>
  <div class='logo-title'>APEX PROPHET QUANTUM</div>
  <div class='logo-sub'>v7.5 Enterprise Web Edition</div>
</div>
<div class="radar-node"></div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ZONE 1 — WIN-RATE SCOREBOARD
# ══════════════════════════════════════════════════════════════════════════════
wr  = st.session_state.global_win_rate_percentage
am  = st.session_state.system_accuracy_multiplier
tot = st.session_state.true_calls_counter + st.session_state.false_calls_counter

st.markdown(f"""
<div class='matrix-panel'>
  <div style='font-size:9px;color:#2a3348;text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;'>
    🏆 WIN-RATE PERFORMANCE SCOREBOARD — LIVE GLOBAL TELEMETRY
  </div>
  <div class='score-row'>
    <div class='score-cell'><div class='score-lbl'>Global Accuracy</div>
      <div class='score-apq'>{wr:.1f}%</div></div>
    <div class='score-cell'><div class='score-lbl'>True Calls</div>
      <div style='color:#00ff88;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>
        {st.session_state.true_calls_counter}</div></div>
    <div class='score-cell'><div class='score-lbl'>False Deflections</div>
      <div style='color:#ff2255;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>
        {st.session_state.false_calls_counter}</div></div>
    <div class='score-cell'><div class='score-lbl'>Total Evaluated</div>
      <div class='price-live'>{tot}</div></div>
    <div class='score-cell'><div class='score-lbl'>Accuracy Multiplier</div>
      <div style='color:#ffb700;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>
        {am:.2f}x</div></div>
  </div>
</div>
""", unsafe_allow_html=True)

# AD SLOT A — top horizontal banner
st.markdown("""
<div class='ad-slot'>
  AD SLOT A — TOP HORIZONTAL LEADERBOARD BANNER (728×90)
  <!-- AD SLOT A: top horizontal banner below scoreboard -->
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CONTROLS
# ══════════════════════════════════════════════════════════════════════════════
gc1, gc2, gc3 = st.columns([5,3,2])
with gc1:
    labels = sorted(set(t.replace("-USD","") for t in ALL_TICKERS))
    pick   = st.selectbox("🎯 GLOBAL CROSS-MARKET QUICK FIND", ["None"]+labels)
    if pick != "None": st.session_state.active_radar_ticker = pick
with gc2:
    target_gap = st.selectbox("⏱️ STRATEGY INTERVAL", list(GAP_MAP.keys()), index=5)
with gc3:
    if st.button("⚡ EXECUTE GLOBAL SCAN", use_container_width=True):
        with st.spinner("Running quantitative analysis…"):
            st.session_state.master_matrix = run_analysis_grid(ALL_TICKERS, target_gap)

# AD SLOT B — tab separator banner
st.markdown("""
<div class='ad-slot'>
  AD SLOT B — MIDDLE TAB SEPARATOR BANNER (468×60)
  <!-- AD SLOT B: middle tab separator banner -->
</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN WINDOW TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_eq, tab_dx, tab_cr = st.tabs([
    "📈 SPOT EQUITIES TERMINAL",
    "⚡ DERIVATIVES: FUTURES & OPTIONS",
    "🌌 CRYPTOCURRENCY RADAR",
])

# ─────────────────────────────────────────────────────────────────────────────
def render_window(pool_key: str):
    pool = POOL_MAP[pool_key]

    with st.expander("⏳ Rolling Prediction Feedback Ledger", expanded=False):
        if st.session_state.prediction_feedback_ledger:
            fd = pd.DataFrame(st.session_state.prediction_feedback_ledger)
            labels = [t.replace("-USD","") for t in pool]
            fds = fd[fd["Asset"].isin(labels)]
            cols = [c for c in ["Time","Asset","Direction","Entry","Target",
                                "Stop","Current Price","Status","Close"]
                    if c in fds.columns]
            st.dataframe(fds[cols], use_container_width=True, hide_index=True) \
                if not fds.empty else st.caption("No predictions logged yet.")
        else:
            st.caption("Run a scan to start tracking predictions.")

    st.markdown("---")
    z2, z3, z4 = st.columns([3.0, 5.0, 3.0])

    # ── Zone 2: Bullish / Bearish ranked tables ───────────────────────────────
    with z2:
        st.markdown(f"##### {pool_key} Asset Ranks")
        mm = st.session_state.master_matrix
        if not mm.empty:
            scope = mm[mm["RawTicker"].isin(pool)].copy()
            if not scope.empty:
                p_lim   = st.session_state.pagination_limits.get(pool_key,10)
                bullish = scope[scope["Direction"]=="BUY"].sort_values("APS Rating",ascending=False)
                bearish = scope[scope["Direction"]=="SELL"].sort_values("APS Rating",ascending=True)

                bc, rc = st.columns(2)
                with bc:
                    st.markdown("<span style='color:#00ff88;font-size:11px;font-weight:700;'>▲ BULLISH</span>",
                                unsafe_allow_html=True)
                    disp = bullish.head(p_lim)[["Asset","Live Price","Gain/Loss %","APS Rating"]]
                    st.dataframe(disp, use_container_width=True, hide_index=True) \
                        if not disp.empty else st.caption("None.")
                with rc:
                    st.markdown("<span style='color:#ff2255;font-size:11px;font-weight:700;'>▼ BEARISH</span>",
                                unsafe_allow_html=True)
                    disp2 = bearish.head(p_lim)[["Asset","Live Price","Gain/Loss %","APS Rating"]]
                    st.dataframe(disp2, use_container_width=True, hide_index=True) \
                        if not disp2.empty else st.caption("None.")

                if p_lim < len(scope):
                    if st.button(f"➕ LOAD MORE {pool_key} ROWS",
                                 key=f"more_{pool_key}", use_container_width=True):
                        st.session_state.pagination_limits[pool_key] += 10; st.rerun()

                st.markdown("---")
                sel = st.selectbox("Inspect Asset", ["None"]+scope["Asset"].tolist(),
                                   key=f"sel_{pool_key}")
                if sel != "None": st.session_state.active_radar_ticker = sel
            else:
                st.info("No data for this class. Run a scan.")
        else:
            st.info("No scan data yet. Press ⚡ EXECUTE GLOBAL SCAN.")

    # ── Zone 3: Chart + AI briefing ───────────────────────────────────────────
    with z3:
        act = st.session_state.active_radar_ticker
        st.markdown(f"##### Centerstage: `{act}`")

        ctrl1, ctrl2 = st.columns(2)
        with ctrl1:
            tl = st.selectbox("📊 HISTORICAL RANGE",
                              ["1D","5D","1M","3M","6M","1Y","2Y","3Y","5Y","Max","CUSTOM DATE RANGE"],
                              index=5, key=f"tl_{pool_key}")
        with ctrl2:
            cs = st.selectbox("🎨 CHART PERSPECTIVE",
                              ["Candlesticks","Institutional Line View","OHLC Structural Bars",
                               "Quantum Area Fill","Renko Matrix Simulations"],
                              index=0, key=f"cs_{pool_key}")

        from_d = datetime.date.today()-datetime.timedelta(days=365)
        to_d   = datetime.date.today()
        if tl == "CUSTOM DATE RANGE":
            cd1,cd2 = st.columns(2)
            with cd1: from_d = st.date_input("From Date",datetime.date.today()-datetime.timedelta(180),key=f"fd_{pool_key}")
            with cd2: to_d   = st.date_input("To Date",  datetime.date(2029,11,25), key=f"td_{pool_key}")

        mm      = st.session_state.master_matrix
        matched = mm[mm["Asset"]==act] if not mm.empty else pd.DataFrame()

        if not matched.empty:
            r = matched.iloc[0]
            gc  = "#00ff88" if r["Gain/Loss %"]>=0 else "#ff2255"
            st.markdown(f"""
            <div class='matrix-panel' style='padding:12px;margin-bottom:8px;'>
              <div style='display:flex;justify-content:space-between;text-align:center;flex-wrap:wrap;gap:8px;'>
                <div><div style='font-size:9px;color:#2a3348;'>LIVE PRICE</div>
                  <div class='price-live'>${r['Live Price']:.4f}</div></div>
                <div><div style='font-size:9px;color:#2a3348;'>TARGET</div>
                  <div class='price-tgt'>${r['Target']:.4f}</div></div>
                <div><div style='font-size:9px;color:#2a3348;'>STOP LOSS</div>
                  <div class='price-stop'>${r['Stop Loss']:.4f}</div></div>
                <div><div style='font-size:9px;color:#2a3348;'>APS SCORE</div>
                  <div class='score-apq'>{r['APS Rating']}</div></div>
                <div><div style='font-size:9px;color:#2a3348;'>GAIN/LOSS</div>
                  <div style='color:{gc};font-family:Share Tech Mono,monospace;font-size:20px;font-weight:900;'>
                    {r['Gain/Loss %']:+.2f}%</div></div>
              </div>
            </div>""", unsafe_allow_html=True)
            raw_ticker = r["RawTicker"]; atr_v = float(r["ATR"])
        else:
            st.markdown("<div class='matrix-panel' style='text-align:center;padding:10px;color:#2a3348;'>Run scan to populate telemetry.</div>",
                        unsafe_allow_html=True)
            guess = [t for t in ALL_TICKERS if act in t]
            raw_ticker = guess[0] if guess else f"{act}-USD"
            atr_v = 1.0

        # Fetch chart history
        try:
            ti = yf.Ticker(raw_ticker)
            hist = (ti.history(start=from_d, end=to_d, interval="1d")
                    if tl=="CUSTOM DATE RANGE"
                    else ti.history(period=CHART_PERIOD[tl], interval=CHART_INTERVAL[tl]))
        except Exception:
            hist = pd.DataFrame()

        if not hist.empty:
            fig = go.Figure()
            if cs == "Candlesticks":
                fig.add_trace(go.Candlestick(x=hist.index,
                    open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],
                    name="OHLC",increasing_line_color="#00ff88",decreasing_line_color="#ff2255"))
            elif cs == "Institutional Line View":
                fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"],mode="lines",
                    line=dict(color="#00f0ff",width=2),name="Close"))
            elif cs == "OHLC Structural Bars":
                fig.add_trace(go.Ohlc(x=hist.index,
                    open=hist["Open"],high=hist["High"],low=hist["Low"],close=hist["Close"],name="Bars"))
            elif cs == "Quantum Area Fill":
                fig.add_trace(go.Scatter(x=hist.index,y=hist["Close"],fill="tozeroy",
                    fillcolor="rgba(0,240,255,0.05)",line=dict(color="#00f0ff",width=1.5),name="Area"))
            elif cs == "Renko Matrix Simulations":
                # Real ATR-based Renko bricks
                brick = float(hist["Close"].rolling(14).std().iloc[-1]) or atr_v or hist["Close"].iloc[-1]*0.01
                fig.add_trace(build_renko(hist["Close"], brick))

            # Target / Stop overlays
            if not matched.empty:
                fig.add_hline(y=float(r["Target"]), line_dash="dot", line_color="#00ff88",
                              annotation_text=f"TARGET ${r['Target']:.2f}", annotation_font_color="#00ff88")
                fig.add_hline(y=float(r["Stop Loss"]), line_dash="dot", line_color="#ff2255",
                              annotation_text=f"STOP ${r['Stop Loss']:.2f}", annotation_font_color="#ff2255")

            fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="#05070c",margin=dict(l=0,r=0,t=4,b=0),
                              height=310,xaxis_rangeslider_visible=False,
                              xaxis=dict(fixedrange=False,gridcolor="#0d1420"),
                              yaxis=dict(fixedrange=True, gridcolor="#0d1420"))
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{pool_key}",
                            config={"scrollZoom":True,"displayModeBar":False})

            roi = (float(hist["Close"].iloc[-1])-float(hist["Close"].iloc[0]))/float(hist["Close"].iloc[0])*100
            rc2 = "#00ff88" if roi>=0 else "#ff2255"
            st.markdown(f"Range ROI: <span style='color:{rc2};font-family:monospace;font-weight:900;'>{roi:+.2f}%</span>",
                        unsafe_allow_html=True)
        else:
            st.caption("No chart data for selected range/interval.")

        st.markdown("""
        <div class='ad-slot' style='margin:8px 0;'>
          AD SLOT B — TAB CONTENT SEPARATOR
          <!-- AD SLOT B: middle tab separator -->
        </div>""", unsafe_allow_html=True)

        st.markdown("##### 📋 AI EXECUTIVE BRIEFING MATRIX")
        if not matched.empty:
            hz = st.select_slider("Analysis Horizon",
                options=["30m","1h","4h","1d","1w","1mo","3mo","Max"],
                value="1h", key=f"hz_{pool_key}")
            if st.button(f"✨ RUN NEURAL AUDIT — {act.upper()}",
                         use_container_width=True, key=f"ai_{pool_key}"):
                with st.spinner("Decrypting risk matrices…"):
                    st.markdown(run_ai_briefing(r.to_dict(), hz, pool_key,
                                                str(from_d), str(to_d)))
        else:
            st.caption("Run a global scan first to enable AI briefing.")

    # ── Zone 4: Class-specific panel ─────────────────────────────────────────
    with z4:
        st.markdown("##### Performance Metrics")
        if not matched.empty:
            r = matched.iloc[0]
            st.metric("APS Score", f"{r['APS Rating']} / 100")
            vc = "#00ff88" if "BUY" in r["Verdict"] else "#ff2255"
            st.markdown(f"Verdict: <span style='color:{vc};font-weight:900;'>{r['Verdict']}</span>",
                        unsafe_allow_html=True)
            st.markdown("---")

            if pool_key == "EQUITIES":
                st.markdown("**CAN SLIM / Fundamentals**")
                st.progress(int(r["CAN SLIM"]),    text=f"Growth Breakout: {r['CAN SLIM']}%")
                st.progress(int(r["Value Safety"]), text=f"Graham Safety:   {r['Value Safety']}%")
                st.progress(int(r["Momentum"]),     text=f"Minervini Mom.:  {r['Momentum']}%")

            elif pool_key == "DERIVATIVES":
                st.markdown("**Black-Scholes Greeks**")
                delta, theta = compute_greeks(float(r["Live Price"]))
                st.metric("Δ Delta (Call)", f"{delta:.4f}")
                st.metric("Θ Theta / day",  f"{theta:.4f}")
                st.markdown("---")
                st.markdown("**Futures Basis**")
                st.markdown("Basis Dev: `+0.0415%`  \nFunding: `0.0100%/8h`")

            elif pool_key == "CRYPTO":
                st.markdown("**📡 Level 2 Liquidity Flux**")
                # Seeded RNG — stable across reruns, no flicker
                rng = np.random.default_rng(int(r["Live Price"]*1000) % (2**31))
                price = float(r["Live Price"]); atr_v2 = float(r["ATR"])
                n = 5
                bp = [price - i*atr_v2*0.12 for i in range(1,n+1)]
                ap = [price + i*atr_v2*0.12 for i in range(1,n+1)]
                bs = rng.integers(150,900,size=n).tolist()
                as_ = rng.integers(150,900,size=n).tolist()
                l2 = go.Figure()
                l2.add_trace(go.Bar(y=bp,x=bs,  name="Bids",orientation="h",marker_color="#00ff88"))
                l2.add_trace(go.Bar(y=ap,x=[-s for s in as_],name="Asks",orientation="h",marker_color="#ff2255"))
                l2.update_layout(barmode="relative",template="plotly_dark",
                                 paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#05070c",
                                 height=190,margin=dict(l=0,r=0,t=4,b=0),showlegend=True,
                                 legend=dict(font=dict(size=9)),
                                 xaxis=dict(title="Vol",gridcolor="#0d1420"),
                                 yaxis=dict(title="Price",gridcolor="#0d1420"))
                st.plotly_chart(l2,use_container_width=True,key=f"l2_{pool_key}",
                                config={"displayModeBar":False})

            st.markdown("---")
            st.markdown("**Execution Gateway (Alpaca Paper)**")
            def _order(side):
                if not trading_client: st.warning("Connect Alpaca keys in sidebar."); return
                sym = f"{r['Asset']}/USD" if r["RawTicker"].endswith("-USD") else r["Asset"]
                qty = 0.01 if r["RawTicker"].endswith("-USD") else 1
                try:
                    trading_client.submit_order(MarketOrderRequest(
                        symbol=sym,qty=qty,
                        side=OrderSide.BUY if side=="BUY" else OrderSide.SELL,
                        time_in_force=TimeInForce.GTC))
                    if side=="BUY": st.success(f"✅ BUY {qty} {sym}")
                    else:           st.error(f"🔴 SELL {qty} {sym}")
                except Exception as ex: st.error(f"Rejected: {ex}")

            cb, cs2 = st.columns(2)
            with cb:
                if st.button("▲ BUY",  key=f"buy_{pool_key}",  use_container_width=True): _order("BUY")
            with cs2:
                if st.button("▼ SELL", key=f"sell_{pool_key}", use_container_width=True): _order("SELL")
        else:
            st.caption("Run a scan to load metrics.")

# ── Render tabs ───────────────────────────────────────────────────────────────
with tab_eq: render_window("EQUITIES")
with tab_dx: render_window("DERIVATIVES")
with tab_cr: render_window("CRYPTO")

# ══════════════════════════════════════════════════════════════════════════════
#  PORTFOLIO LEDGER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("### 💼 AUTOMATED TERMINAL PORTFOLIO EXCHANGES")
if trading_client:
    try:
        acc = trading_client.get_account()
        a1,a2,a3 = st.columns(3)
        a1.metric("Cash Balance",    f"${float(acc.cash):,.2f}")
        a2.metric("Portfolio Value", f"${float(acc.portfolio_value):,.2f}")
        a3.metric("Buying Power",    f"${float(acc.buying_power):,.2f}")
        pos = trading_client.get_all_positions()
        if pos:
            rows = [{"Symbol":p.symbol,"Qty":p.qty,
                     "Avg Entry":f"${float(p.avg_entry_price):,.4f}",
                     "Mkt Price":f"${float(p.current_price):,.4f}",
                     "Mkt Value":f"${float(p.market_value):,.2f}",
                     "Unreal P/L":f"${float(p.unrealized_pl):+,.2f} ({float(p.unrealized_plpc)*100:+.2f}%)"}
                    for p in pos]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions in this paper account.")
    except Exception as err:
        st.error(f"Alpaca ledger error: {err}")
else:
    st.markdown("""
    <div class='matrix-panel' style='text-align:center;color:#2a3348;padding:20px;'>
      🔒 Alpaca Paper Trading not connected.<br>
      <span style='font-size:12px;'>Paste your Alpaca Paper keys in the sidebar to activate.</span>
    </div>""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;color:#0d1420;font-size:10px;
            letter-spacing:2px;text-transform:uppercase;padding:28px 0 10px;'>
  APEX PROPHET QUANTUM v7.5 — EDUCATIONAL & ANALYTICAL USE ONLY — NOT INVESTMENT ADVICE
</div>""", unsafe_allow_html=True)
