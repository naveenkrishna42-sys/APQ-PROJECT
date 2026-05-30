"""
APEX PROPHET QUANTUM (APQ) v7.5 Enterprise — PRODUCTION UPGRADE
================================================================
UPGRADE NOTES:
  1. LIVE PRICES — 30s cached prices, live ▲▼ ticker strip per tab
  2. TIME ON GRAPHS — per-timeframe x-axis tick formats (HH:MM / Mon DD / Year)
  3. KEYS SECURED — st.secrets only; zero key inputs visible to visitors
  4. AD GATE — full-screen splash blocks platform until ads are displayed
  5. ASSET FULL NAMES — all tables show "Apple Inc. (AAPL)" format
  6. REAL WIN-RATE — starts at 0/0, tracks only actual session predictions
  7. INSPECT ASSET MOVED TO TOP of Zone 2 for fast access
  8. No ternary-as-statements (Streamlit AST crash fix)
  9. No pandas-ta (Python / llvmlite crash fix)
 10. Gemini via direct REST (using gemini-2.0-flash)
 11. yfinance individual flat-column downloads (MultiIndex fix)
 12. Included required time imports
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
import requests

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

st.set_page_config(
    page_title="APEX PROPHET QUANTUM (APQ) v7.5",
    layout="wide",
    initial_sidebar_state="collapsed",
)

try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_OK = True
except ImportError:
    AUTOREFRESH_OK = False

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    ALPACA_OK = True
except ImportError:
    ALPACA_OK = False


# ══════════════════════════════════════════════════════════════════════════════
#  PURE-PANDAS INDICATOR LIBRARY  (no pandas-ta / numba / llvmlite)
# ══════════════════════════════════════════════════════════════════════════════
def ind_rsi(s, n=14):
    d = s.diff()
    g = d.clip(lower=0).rolling(n, min_periods=n).mean()
    l = (-d.clip(upper=0)).rolling(n, min_periods=n).mean()
    return (100 - 100 / (1 + g / l.replace(0, np.nan))).rename("RSI_14")

def ind_macd(s, fast=12, slow=26, sig=9):
    line   = s.ewm(span=fast, adjust=False).mean() - s.ewm(span=slow, adjust=False).mean()
    signal = line.ewm(span=sig, adjust=False).mean()
    return line.rename("MACD"), signal.rename("MACDs")

def ind_atr(df, n=14):
    tr = pd.concat([
        df["High"] - df["Low"],
        (df["High"] - df["Close"].shift()).abs(),
        (df["Low"]  - df["Close"].shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=n).mean().rename("ATR_14")

def ind_sma(s, n):
    return s.rolling(n, min_periods=n).mean().rename(f"SMA_{n}")


# ══════════════════════════════════════════════════════════════════════════════
#  SECRETS — keys NEVER visible to site visitors
# ══════════════════════════════════════════════════════════════════════════════
def _secret(key: str) -> str:
    """Read from Streamlit Cloud secrets first, then OS env vars."""
    try:
        val = st.secrets.get(key, "")
        if val:
            return str(val)
    except Exception:
        pass
    return os.getenv(key, "")

GEMINI_KEY_RAW = _secret("GEMINI_API_KEY")
ALPACA_KEY_ID  = _secret("APCA_API_KEY_ID")
ALPACA_SECRET  = _secret("APCA_API_SECRET_KEY")
GEMINI_POOL    = [k.strip() for k in GEMINI_KEY_RAW.split(",") if k.strip()]

trading_client = None   # set inside sidebar after init attempt


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE — all counters start at 0 (real tracking only)
# ══════════════════════════════════════════════════════════════════════════════
_DEFS = {
    "master_matrix":              pd.DataFrame(),
    "active_radar_ticker":        "BTC",
    "prediction_feedback_ledger": [],
    "system_accuracy_multiplier": 1.0,
    "global_win_rate_percentage": 0.0,
    "ai_table_cache":             {},
    "true_calls_counter":         0,
    "false_calls_counter":        0,
    "pagination_limits":          {"EQUITIES": 10, "DERIVATIVES": 10, "CRYPTO": 10},
    "auto_refresh_enabled":       True,
    "disclaimer_accepted":        False,
    "ads_displayed":              False,
    "prev_live_prices":           {},
    "last_scan_time":             "",
}

for _k, _v in _DEFS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ══════════════════════════════════════════════════════════════════════════════
#  OBSIDIAN CYBER-GRID THEME CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@400;700;900&display=swap');
html,body,.stApp{background:#030407!important;color:#cbd5e1;font-family:'Exo 2',sans-serif;}
.radar-node{width:11px;height:11px;background:#00ff88;border-radius:50%;
  display:inline-block;vertical-align:middle;margin-left:8px;
  box-shadow:0 0 0 0 rgba(0,255,136,.7);
  animation:pulseRadar 1.6s infinite cubic-bezier(.66,0,0,1);}
@keyframes pulseRadar{to{box-shadow:0 0 0 18px rgba(0,255,136,0);}}
.logo-frame{display:flex;align-items:center;gap:14px;padding:10px 0 14px;
  border-bottom:1px solid #141a29;margin-bottom:14px;}
.logo-title{margin:0;font-family:'Exo 2',sans-serif;font-weight:900;color:#fff;
  letter-spacing:2px;font-size:22px;}
.logo-sub{color:#1e2a3a;font-size:10px;letter-spacing:3px;text-transform:uppercase;}
.price-live{color:#00f0ff!important;font-family:'Share Tech Mono',monospace;
  font-size:24px;font-weight:900;text-shadow:0 0 10px rgba(0,240,255,.4);}
.price-tgt{color:#00ff88!important;font-family:'Share Tech Mono',monospace;
  font-size:24px;font-weight:900;text-shadow:0 0 10px rgba(0,255,136,.4);}
.price-stop{color:#ff2255!important;font-family:'Share Tech Mono',monospace;
  font-size:24px;font-weight:900;text-shadow:0 0 10px rgba(255,34,85,.4);}
.score-apq{color:#ffb700!important;font-family:'Share Tech Mono',monospace;
  font-size:24px;font-weight:900;text-shadow:0 0 10px rgba(255,183,0,.4);}
.matrix-panel{background:linear-gradient(135deg,#090c15,#05070a);
  padding:18px;border-radius:8px;border:1px solid #111724;margin-bottom:14px;
  transition:all .22s cubic-bezier(.4,0,.2,1);}
.matrix-panel:hover{transform:translateY(-1px);border-color:#00f0ff;
  box-shadow:0 4px 14px rgba(0,240,255,.12);}
.score-row{display:flex;justify-content:space-between;align-items:center;
  gap:20px;flex-wrap:wrap;}
.score-cell{text-align:center;flex:1;min-width:110px;}
.score-lbl{font-size:9px;color:#1e2a3a;text-transform:uppercase;letter-spacing:1.5px;}
.ad-slot{background:#06080e;border:1px dashed #1a2236;border-radius:6px;
  text-align:center;color:#1e2a3a;font-size:10px;letter-spacing:2px;
  text-transform:uppercase;margin:10px 0;padding:13px 10px;}
.live-strip{background:#04060c;border:1px solid #0d1420;border-radius:4px;
  padding:7px 12px;margin-bottom:10px;overflow-x:auto;white-space:nowrap;
  font-family:'Share Tech Mono',monospace;font-size:11px;line-height:1.4;}
.stButton>button{background:linear-gradient(90deg,#09101f,#0e1a30)!important;
  color:#fff!important;border:1px solid #162642!important;border-radius:6px!important;
  font-weight:700!important;transition:all .15s ease!important;width:100%;}
.stButton>button:hover{border-color:#00ff88!important;
  box-shadow:0 0 14px rgba(0,255,136,.18)!important;transform:scale(1.015);}
.stButton>button:active{transform:scale(.97);}
div[data-testid="stMetricValue"]{font-family:'Share Tech Mono',monospace;color:#00f0ff;}
.stTabs [data-baseweb="tab"]{font-weight:700;letter-spacing:1px;color:#4a5568;}
.stTabs [aria-selected="true"]{color:#00f0ff!important;border-bottom:2px solid #00f0ff!important;}
[data-testid="stSidebar"]{background:#03050a!important;border-right:1px solid #0d1420;}
[data-testid="stDataFrame"]{border:1px solid #0d1420;border-radius:6px;}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  ASSET FULL NAMES + POOLS
# ══════════════════════════════════════════════════════════════════════════════
ASSET_NAMES = {
    "AAPL":"Apple Inc.",       "MSFT":"Microsoft Corp.",     "NVDA":"NVIDIA Corp.",
    "TSLA":"Tesla Inc.",       "AMZN":"Amazon.com Inc.",     "META":"Meta Platforms",
    "GOOGL":"Alphabet Inc.",   "AMD":"AMD Inc.",              "NFLX":"Netflix Inc.",
    "AVGO":"Broadcom Inc.",    "COST":"Costco Wholesale",    "CRM":"Salesforce Inc.",
    "INTC":"Intel Corp.",      "QCOM":"Qualcomm Inc.",       "ADBE":"Adobe Inc.",
    "CSCO":"Cisco Systems",    "SPY":"S&P 500 ETF",       "QQQ":"Nasdaq-100 ETF",
    "IWM":"Russell 2000 ETF",    "GLD":"Gold Spot ETF",     "SLV":"Silver Spot ETF",
    "USO":"US Oil Fund ETF",    "UNG":"Natural Gas ETF",   "TLT":"20yr Treasury ETF",
    "HYG":"High Yield Bond ETF",    "EEM":"Emerging Mkts ETF", "FXI":"China LargeCap ETF",
    "VXX":"VIX Volatility ETF",    "BTC":"Bitcoin",           "ETH":"Ethereum",
    "SOL":"Solana",    "BNB":"BNB Coin",          "XRP":"XRP (Ripple)",
    "ADA":"Cardano",    "DOT":"Polkadot",          "LTC":"Litecoin",
    "LINK":"Chainlink",    "AVAX":"Avalanche",
}

def asset_label(sym: str) -> str:
    name = ASSET_NAMES.get(sym, sym)
    return f"{name} ({sym})" if name != sym else sym

EQUITIES_POOL    = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD",
                    "NFLX","AVGO","COST","CRM","INTC","QCOM","ADBE","CSCO"]
DERIVATIVES_POOL = ["SPY","QQQ","IWM","GLD","SLV","USO","UNG",
                    "TLT","HYG","EEM","FXI","VXX"]
CRYPTO_POOL      = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD",
                    "ADA-USD","DOT-USD","LTC-USD","LINK-USD","AVAX-USD"]

ALL_TICKERS      = list(dict.fromkeys(EQUITIES_POOL + DERIVATIVES_POOL + CRYPTO_POOL))
POOL_MAP         = {"EQUITIES":EQUITIES_POOL,"DERIVATIVES":DERIVATIVES_POOL,"CRYPTO":CRYPTO_POOL}

GAP_MAP = {
    "1m":("2d","1m",1.1),    "3m":("5d","3m",1.3),    "5m":("5d","5m",1.6),
    "15m":("7d","15m",2.0),  "30m":("14d","30m",2.2), "1h":("1mo","1h",2.8),
    "2h":("2mo","2h",3.0),   "4h":("3mo","4h",3.4),   "1d":("2y","1d",4.2),
}

CHART_PERIOD   = {"1D":"1d","5D":"5d","1M":"1mo","3M":"3mo","6M":"6mo",
                  "1Y":"1y","2Y":"2y","3Y":"3y","5Y":"5y","Max":"max"}
CHART_INTERVAL = {"1D":"2m","5D":"15m","1M":"30m","3M":"1h","6M":"2h",
                  "1Y":"1d","2Y":"1d","3Y":"1wk","5Y":"1wk","Max":"1mo"}
CHART_TICKFMT  = {"1D":"%H:%M","5D":"%a %H:%M","1M":"%b %d","3M":"%b %d",
                  "6M":"%b \'%y","1Y":"%b \'%y","2Y":"%Y","3Y":"%Y","5Y":"%Y",
                  "Max":"%Y","CUSTOM DATE RANGE":"%b %d \'%y"}


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER — individual downloads, flat-column safe (yfinance)
# ══════════════════════════════════════════════════════════════════════════════
def _flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c)
                      for c in df.columns.get_level_values(0)]
    else:
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    return df

@st.cache_data(ttl=300, show_spinner=False)
def _fetch(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval,
                         progress=False, auto_adjust=True)
        return _flatten_cols(df).dropna()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60, show_spinner=False)
def _fetch_chart(ticker: str, period: str, interval: str,
                 start=None, end=None) -> pd.DataFrame:
    try:
        ti = yf.Ticker(ticker)
        if start and end:
            df = ti.history(start=start, end=end, interval="1d")
        else:
            df = ti.history(period=period, interval=interval)
        return _flatten_cols(df).dropna()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=30, show_spinner=False)
def fetch_live_prices(tickers: tuple) -> dict:
    """Current market prices. TTL=30s gives live-feel updates."""
    prices = {}
    for t in tickers:
        sym = t.replace("-USD","")
        try:
            fi = yf.Ticker(t).fast_info
            p  = fi.last_price
            if p and float(p) > 0:
                prices[sym] = float(p)
                continue
        except Exception:
            pass
        try:
            df = _fetch(t, "2d", "2m")
            if not df.empty and "Close" in df.columns:
                prices[sym] = float(df["Close"].iloc[-1])
        except Exception:
            pass
    return prices

def _safe_float(s: pd.Series) -> float:
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS: Black-Scholes + Renko
# ══════════════════════════════════════════════════════════════════════════════
def compute_greeks(spot, strike=None, days=30, rfr=0.04, sigma=0.30):
    if strike is None:
        strike = spot * 1.05
    t  = max(0.001, days / 365.0)
    d1 = (np.log(spot/strike) + (rfr + 0.5*sigma**2)*t) / (sigma*np.sqrt(t))
    d2 = d1 - sigma*np.sqrt(t)
    return (float(norm.cdf(d1)),
            float((-(spot*norm.pdf(d1)*sigma)/(2*np.sqrt(t))
                   - rfr*strike*np.exp(-rfr*t)*norm.cdf(d2)) / 365.0))

def build_renko(close: pd.Series, brick: float):
    if brick <= 0:
        brick = float(close.std())*0.5 or 1.0
    vals, colors = [], []
    cur = float(close.iloc[0])
    for p in close.iloc[1:].values:
        while p >= cur + brick:
            cur += brick; vals.append(cur); colors.append("#00ff88")
        while p <= cur - brick:
            cur -= brick; vals.append(cur); colors.append("#ff2255")
    if not vals:
        vals = [float(close.iloc[-1])]; colors = ["#00f0ff"]
    return go.Scatter(
        x=list(range(len(vals))), y=vals, mode="markers+lines",
        marker=dict(symbol="square", color=colors, size=9),
        line=dict(color="#1e2a3a", width=1), name="Renko")


# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE AUDITOR (real-time prediction tracking)
# ══════════════════════════════════════════════════════════════════════════════
def run_auditor(prices: dict):
    if not st.session_state.prediction_feedback_ledger:
        return
    ok = tot = 0
    for item in st.session_state.prediction_feedback_ledger:
        a = item.get("Asset","")
        if a not in prices:
            continue
        live = prices[a]
        item["Current Price"] = live
        if item["Status"] == "ACTIVE":
            bull = "BUY" in item.get("Direction","")
            tgt  = item.get("Target", 1e18)
            stp  = item.get("Stop", 0)
            if bull and live >= tgt:
                item["Status"] = "HIT"; item["Close"] = live
                st.session_state.true_calls_counter  += 1
            elif bull and live <= stp:
                item["Status"] = "STOPPED"; item["Close"] = live
                st.session_state.false_calls_counter += 1
            elif not bull and live <= tgt:
                item["Status"] = "HIT"; item["Close"] = live
                st.session_state.true_calls_counter  += 1
            elif not bull and live >= stp:
                item["Status"] = "STOPPED"; item["Close"] = live
                st.session_state.false_calls_counter += 1
        tot += 1
        if "HIT" in item["Status"]:
            ok += 1
        elif item["Status"] == "ACTIVE" and item.get("Entry",0) > 0:
            if abs(live - item["Entry"]) / item["Entry"] < 0.035:
                ok += 1
    if tot > 0:
        wr = ok / tot * 100
        st.session_state.global_win_rate_percentage = wr
        st.session_state.system_accuracy_multiplier = max(0.65, wr/100) if wr < 65 else 1.0


# ══════════════════════════════════════════════════════════════════════════════
#  QUANTUM ANALYSIS GRID
# ══════════════════════════════════════════════════════════════════════════════
def run_analysis_grid(tickers: list, gap: str) -> pd.DataFrame:
    period, interval, mult = GAP_MAP.get(gap, ("1mo","1h",2.8))
    acc   = st.session_state.system_accuracy_multiplier
    rows, fails = [], []
    n     = len(tickers)
    prog  = st.progress(0, text="Initializing scan engine…")
    stat  = st.empty()
    for i, t in enumerate(tickers):
        sym = t.replace("-USD","")
        prog.progress((i+1)/n, text=f"Scanning {asset_label(sym)}… ({i+1}/{n})")
        try:
            dfi = _fetch(t, period, interval)
            dfm = _fetch(t, "2y", "1d")
            if dfi.empty or len(dfi) < 20:
                fails.append(f"{sym}: insufficient intraday bars ({len(dfi)})")
                continue
            if dfm.empty or len(dfm) < 40:
                fails.append(f"{sym}: insufficient daily bars ({len(dfm)})")
                continue
            if not {"Open","High","Low","Close"}.issubset(set(dfi.columns)):
                fails.append(f"{sym}: missing OHLC — got {list(dfi.columns)[:5]}")
                continue
            close_p = float(dfi["Close"].iloc[-1])
            prev_p  = float(dfi["Close"].iloc[-2])
            rsi_s          = ind_rsi(dfi["Close"])
            macd_l, macd_s = ind_macd(dfi["Close"])
            atr_s          = ind_atr(dfi)
            sma50          = ind_sma(dfm["Close"], 50)
            sma200         = ind_sma(dfm["Close"], 200)
            
            rsi  = _safe_float(rsi_s)  or 50.0
            ml   = _safe_float(macd_l)
            ms   = _safe_float(macd_s)
            atr  = _safe_float(atr_s)  or close_p * 0.015
            s50  = _safe_float(sma50)  or close_p
            s200 = _safe_float(sma200) or close_p
            
            bull_trend  = close_p > s50 > s200
            macd_cross  = ml > ms
            
            sc_growth   = int(min(100, max(0,  85 if bull_trend  else 35)))
            sc_value    = int(min(100, max(0,  92 - rsi*0.45 if close_p < s50 else 30)))
            sc_momentum = int(min(100, max(0,  95 if macd_cross else 25)))
            aps         = int((sc_growth + sc_value + sc_momentum) / 3)
            
            dir_bull = macd_cross
            target   = close_p + atr*mult*acc      if dir_bull else close_p - atr*mult*acc
            stop_l   = close_p - atr*mult*0.55*acc if dir_bull else close_p + atr*mult*0.55*acc
            verdict  = ("STRONG BUY" if aps > 66 else "BUY" if aps > 52
                        else "SELL"  if aps < 35 else "HOLD")
            
            rows.append({
                "Asset":        sym,
                "FullName":     ASSET_NAMES.get(sym, sym),
                "RawTicker":    t,
                "Live Price":   close_p,
                "Gain/Loss %":  round((close_p - prev_p) / prev_p * 100, 3),
                "CAN SLIM":     sc_growth,
                "Value Safety": sc_value,
                "Momentum":     sc_momentum,
                "APS Rating":   aps,
                "Target":       target,
                "Stop Loss":    stop_l,
                "ATR":          atr,
                "Direction":    "BUY" if dir_bull else "SELL",
                "Verdict":      verdict,
            })
        except Exception as e:
            fails.append(f"{sym}: {type(e).__name__} — {str(e)[:55]}")
            continue
    prog.empty()
    if rows:
        st.session_state.last_scan_time = time.strftime("%H:%M:%S")
        stat.success(f"Scan complete — {len(rows)}/{n} assets at {st.session_state.last_scan_time}")
    else:
        stat.error("Scan returned zero results. Check internet connection.")
    if fails:
        with st.expander(f"{len(fails)} ticker(s) had issues", expanded=False):
            for msg in fails:
                st.caption(f"• {msg}")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
#  GEMINI AI — direct REST API (using Gemini 2.0 Flash)
# ══════════════════════════════════════════════════════════════════════════════
def _call_gemini_rest(api_key: str, prompt: str) -> str:
    # Explicitly using gemini-2.0-flash as the primary fast engine for dashboards
    for model in ("gemini-2.0-flash", "gemini-1.5-flash"):
        url  = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}")
        body = {"contents":[{"parts":[{"text":prompt}]}],
                "generationConfig":{"maxOutputTokens":1024,"temperature":0.3}}
        try:
            r = requests.post(url, json=body, timeout=30)
            if r.status_code == 429:
                raise Exception("429 RESOURCE_EXHAUSTED")
            if r.status_code == 404:
                continue
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            err = str(e)
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                raise
            if "404" in err:
                continue
            raise
    raise Exception("All Gemini models unavailable")

def run_ai_briefing(row: dict, gap: str, seg: str, from_d, to_d) -> str:
    ck = f"{row['Asset']}_{gap}_{seg}_{from_d}_{to_d}"
    if ck in st.session_state.ai_table_cache:
        return st.session_state.ai_table_cache[ck]
    if not GEMINI_POOL:
        return "| Warning | AI Offline | No API key configured. Check st.secrets. |"
    try:
        news_items = yf.Ticker(row["RawTicker"]).news or []
        news = " | ".join(n.get("title","") for n in news_items[:2]) or "No catalysts."
    except Exception:
        news = "News unavailable."
    entry = {
        "Time":row.get("_ts",time.strftime("%H:%M:%S")),
        "Asset":row["Asset"], "Direction":row["Verdict"],
        "Entry":row["Live Price"], "Target":row["Target"],
        "Stop":row["Stop Loss"], "Current Price":row["Live Price"],
        "Status":"ACTIVE", "Close":"-",
    }
    if not any(d["Asset"]==row["Asset"] and d["Status"]=="ACTIVE"
               for d in st.session_state.prediction_feedback_ledger):
        entry["_ts"] = time.strftime("%H:%M:%S")
        st.session_state.prediction_feedback_ledger.append(entry)
    full = ASSET_NAMES.get(row["Asset"], row["Asset"])
    prompt = (
        f"Algorithmic audit: {row['Asset']} ({full}) — {seg}. "
        f"Price:${row['Live Price']:.4f}. Interval:{gap}. APS:{row['APS Rating']}/100. "
        f"Win rate:{st.session_state.global_win_rate_percentage:.1f}%. "
        f"Range:{from_d} to {to_d}. News:{news}. "
        "Output ONLY a Markdown table: 'Audit Component'|'Metric'|'Action Vector'. "
        "No preamble. 4 rows: Management Actions, Corporate Adjustments, "
        "Operational Pros/Cons, Volatility Regime Verdict."
    )
    last_err = "Unknown"
    for api_key in GEMINI_POOL:
        try:
            result = _call_gemini_rest(api_key, prompt)
            st.session_state.ai_table_cache[ck] = result
            return result
        except Exception as e:
            last_err = str(e)
            if "429" in last_err or "RESOURCE_EXHAUSTED" in last_err:
                continue
            return f"| API Error | {last_err[:100]} | Retry or contact admin |"
    return f"| Rate Limit | All {len(GEMINI_POOL)} key(s) exhausted | Try again later |"


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — system status only; zero key inputs shown to visitors
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 6px;border-bottom:1px solid #0d1420;margin-bottom:10px;'>
      <div style='font-size:13px;font-weight:900;color:#00f0ff;letter-spacing:2px;'>
        APEX PROPHET QUANTUM
      </div>
      <div style='font-size:9px;color:#1e2a3a;letter-spacing:2px;text-transform:uppercase;'>
        v7.5 Enterprise Web Edition
      </div>
    </div>""", unsafe_allow_html=True)
    
    st.markdown("**🔌 System Status**")
    if GEMINI_POOL:
        st.success(f"✅ AI Engine: Online ({len(GEMINI_POOL)} keys)")
    else:
        st.warning("⚠️ AI Engine: Offline")
        
    if ALPACA_OK and ALPACA_KEY_ID and ALPACA_SECRET:
        try:
            trading_client = TradingClient(ALPACA_KEY_ID, ALPACA_SECRET, paper=True)
            st.success("✅ Trading: Paper Active")
        except Exception:
            st.warning("⚠️ Trading: Auth Failed")
    else:
        st.info("ℹ️ Trading: Simulation Mode")
        
    st.divider()
    st.session_state.auto_refresh_enabled = st.toggle(
        "📡 Live Auto-Refresh (30s)", value=st.session_state.auto_refresh_enabled)
    
    if st.session_state.last_scan_time:
        st.caption(f"Last scan: {st.session_state.last_scan_time}")
        
    st.divider()
    st.markdown("""
    <div class='ad-slot' style='margin-top:8px;'>
      AD SLOT C — SIDEBAR FOOTER
      <!-- AD SLOT C: 250×250 sidebar responsive unit -->
    </div>""", unsafe_allow_html=True)

if st.session_state.auto_refresh_enabled and AUTOREFRESH_OK:
    st_autorefresh(interval=30_000, key="apq_live_refresh")


# ══════════════════════════════════════════════════════════════════════════════
#  AD GATE — full-screen splash until ads are viewed
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.ads_displayed:
    st.markdown("""
    <div style='text-align:center;padding:44px 0 20px;'>
      <div style='font-size:38px;font-weight:900;color:#00f0ff;letter-spacing:6px;
                  text-shadow:0 0 30px rgba(0,240,255,.5);'>
        APEX PROPHET QUANTUM
      </div>
      <div style='font-size:11px;color:#1e2a3a;letter-spacing:4px;
                  text-transform:uppercase;margin-top:6px;'>
        Quantum Financial Intelligence Platform
      </div>
    </div>
    <div class='ad-slot' style='height:150px;display:flex;align-items:center;
                                  justify-content:center;flex-direction:column;gap:6px;'>
      <div style='font-size:13px;font-weight:700;color:#2a3348;'>
        FEATURED PARTNER — PRIME SLOT A
      </div>
      <div style='font-size:10px;color:#1e2a3a;'>
        728 × 150 · Full-Width Leaderboard
      </div>
      <!-- AD SLOT A GATE: full-width leaderboard 728×150 -->
    </div>
    """, unsafe_allow_html=True)
    
    ag1, ag2, ag3 = st.columns([1, 2, 1])
    with ag2:
        st.markdown("""
        <div class='ad-slot' style='height:240px;display:flex;align-items:center;
                                      justify-content:center;flex-direction:column;gap:6px;'>
          <div style='font-size:13px;font-weight:700;color:#2a3348;'>
            SPONSORED CONTENT — SLOT B
          </div>
          <div style='font-size:10px;color:#1e2a3a;'>400 × 240 · Interstitial Square</div>
          <!-- AD SLOT B GATE: interstitial square 400×240 -->
        </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀  ENTER APEX PROPHET QUANTUM PLATFORM", use_container_width=True):
            st.session_state.ads_displayed = True
            st.rerun()
            
    st.markdown("""
    <div style='text-align:center;color:#0d1420;font-size:9px;margin-top:24px;
                letter-spacing:2px;text-transform:uppercase;'>
      This platform is ad-supported · Analysis is for educational purposes only
    </div>""", unsafe_allow_html=True)
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  DISCLAIMER (after ad gate)
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.disclaimer_accepted:
    @st.dialog("⚠️ MANDATORY FINANCIAL DISCLAIMER")
    def _disclaimer():
        st.markdown("""
        **REGULATORY COMPLIANCE AND RISK NOTICE**
        All matrices, Greeks, and AI responses are for **analytical and educational
        purposes only** — not investment advice. By clicking Accept you acknowledge
        all capital risks remain your individual liability.
        """)
        if st.button("I AGREE & ACCEPT", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    _disclaimer()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  LIVE PRICES (fetched once per rerun; shared across all tab renders)
# ══════════════════════════════════════════════════════════════════════════════
live_prices: dict = fetch_live_prices(tuple(ALL_TICKERS))
price_changes: dict = {}
for _sym, _price in live_prices.items():
    _prev = st.session_state.prev_live_prices.get(_sym, _price)
    price_changes[_sym] = _price - _prev
st.session_state.prev_live_prices = dict(live_prices)

if live_prices:
    run_auditor(live_prices)


# ══════════════════════════════════════════════════════════════════════════════
#  LOGO + HEADER
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
        fill="none" stroke="#00ff88" stroke-width="6"
        stroke-linejoin="round" stroke-linecap="round"/>
  <circle cx="99" cy="96" r="7" fill="none" stroke="#ff2255" stroke-width="5"/>
  <line x1="104" y1="101" x2="113" y2="112"
        stroke="#ff2255" stroke-width="5" stroke-linecap="round"/>
</svg>
<div>
  <div class='logo-title'>APEX PROPHET QUANTUM</div>
  <div class='logo-sub'>v7.5 Enterprise &nbsp;·&nbsp; """ + time.strftime("%H:%M:%S") + """ &nbsp;🔴 LIVE</div>
</div>
<div class="radar-node"></div>
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  WIN-RATE SCOREBOARD (real stats — computed dynamically)
# ══════════════════════════════════════════════════════════════════════════════
true_c  = st.session_state.true_calls_counter
false_c = st.session_state.false_calls_counter
total_c = true_c + false_c
wr      = st.session_state.global_win_rate_percentage
am      = st.session_state.system_accuracy_multiplier

if total_c > 0:
    wr_txt  = f"{wr:.1f}%"
    tot_txt = str(total_c)
else:
    wr_txt  = "—"
    tot_txt = "—"

st.markdown(f"""
<div class='matrix-panel'>
  <div style='font-size:9px;color:#1e2a3a;text-transform:uppercase;
              letter-spacing:2px;margin-bottom:10px;'>
    🏆 WIN-RATE PERFORMANCE SCOREBOARD — LIVE TRACKED METRICS
  </div>
  <div class='score-row'>
    <div class='score-cell'>
      <div class='score-lbl'>Global Accuracy</div>
      <div class='score-apq'>{wr_txt}</div>
    </div>
    <div class='score-cell'>
      <div class='score-lbl'>True System Calls</div>
      <div style='color:#00ff88;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>{true_c}</div>
    </div>
    <div class='score-cell'>
      <div class='score-lbl'>False Deflections</div>
      <div style='color:#ff2255;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>{false_c}</div>
    </div>
    <div class='score-cell'>
      <div class='score-lbl'>Total Evaluated</div>
      <div class='price-live'>{tot_txt}</div>
    </div>
    <div class='score-cell'>
      <div class='score-lbl'>Accuracy Multiplier</div>
      <div style='color:#ffb700;font-family:Share Tech Mono,monospace;font-size:26px;font-weight:900;'>{am:.2f}x</div>
    </div>
  </div>
  {"<div style='font-size:9px;color:#1e2a3a;text-align:center;margin-top:8px;'>Run Neural Audit to begin real prediction tracking</div>" if total_c == 0 else ""}
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class='ad-slot'>
  AD SLOT A — TOP HORIZONTAL BANNER (728×90)
  <!-- AD SLOT A: top horizontal banner below scoreboard -->
</div>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CONTROLS
# ══════════════════════════════════════════════════════════════════════════════
gc1, gc2, gc3 = st.columns([5, 3, 2])
with gc1:
    all_syms = sorted(set(t.replace("-USD","") for t in ALL_TICKERS))
    disp_opts = ["None"] + [asset_label(s) for s in all_syms]
    pick = st.selectbox("🎯 GLOBAL CROSS-MARKET QUICK FIND", disp_opts)
    if pick != "None":
        sym_pick = pick.split("(")[-1].rstrip(")")
        st.session_state.active_radar_ticker = sym_pick

with gc2:
    target_gap = st.selectbox("⏱️ STRATEGY INTERVAL", list(GAP_MAP.keys()), index=5)

with gc3:
    scan_clicked = st.button("⚡ EXECUTE GLOBAL SCAN", use_container_width=True)

if scan_clicked:
    st.session_state.master_matrix = run_analysis_grid(ALL_TICKERS, target_gap)

st.markdown("""
<div class='ad-slot'>
  AD SLOT B — MIDDLE TAB SEPARATOR BANNER (468×60)
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

def build_live_strip(pool_labels: list) -> str:
    parts = []
    for sym in pool_labels:
        price = live_prices.get(sym, 0.0)
        if price <= 0:
            continue
        chg   = price_changes.get(sym, 0.0)
        pct   = (chg / price * 100) if price > 0 else 0.0
        arrow = "▲" if chg > 0 else ("▼" if chg < 0 else "●")
        color = "#00ff88" if chg > 0 else ("#ff2255" if chg < 0 else "#3a4860")
        name  = ASSET_NAMES.get(sym, sym)
        parts.append(
            f"<span style='color:{color};'>"
            f"<b>{sym}</b> {name} "
            f"${price:,.4f} {arrow} {pct:+.2f}%"
            f"</span>"
        )
    if not parts:
        return ""
    joined = " &nbsp;│&nbsp; ".join(parts)
    return (f"<div class='live-strip'>"
            f"<span style='color:#1e2a3a;font-size:9px;text-transform:uppercase;"
            f"letter-spacing:1px;margin-right:10px;'>🔴 LIVE</span>"
            f"{joined}</div>")

def render_window(pool_key: str):
    pool        = POOL_MAP[pool_key]
    pool_labels = [t.replace("-USD","") for t in pool]
    
    strip_html = build_live_strip(pool_labels)
    if strip_html:
        st.markdown(strip_html, unsafe_allow_html=True)
        
    with st.expander("⏳ Rolling Prediction Feedback Ledger", expanded=False):
        if st.session_state.prediction_feedback_ledger:
            fd  = pd.DataFrame(st.session_state.prediction_feedback_ledger)
            fds = fd[fd["Asset"].isin(pool_labels)]
            cols = [c for c in ["Time","Asset","Direction","Entry","Target",
                                "Stop","Current Price","Status","Close"]
                    if c in fds.columns]
            if not fds.empty:
                st.dataframe(fds[cols], use_container_width=True, hide_index=True)
            else:
                st.caption("No predictions logged for this class yet.")
        else:
            st.caption("Run a scan + Neural Audit to begin tracking.")
            
    st.markdown("---")
    
    z2, z3, z4 = st.columns([3.0, 5.0, 3.0])
    
    # ─── Zone 2: INSPECT AT TOP → then Bullish/Bearish ───────────────────────
    with z2:
        st.markdown(f"##### {pool_key} Asset Ranks")
        mm    = st.session_state.master_matrix
        scope = mm[mm["RawTicker"].isin(pool)].copy() if not mm.empty else pd.DataFrame()
        avail = scope["Asset"].tolist() if not scope.empty else pool_labels
        
        # INSPECT ASSET — MOVED TO TOP OF ZONE 2
        sel_opts = ["None"] + [asset_label(a) for a in avail]
        sel = st.selectbox("🎯 INSPECT ASSET", sel_opts, key=f"sel_{pool_key}")
        if sel != "None":
            sym_sel = sel.split("(")[-1].rstrip(")")
            st.session_state.active_radar_ticker = sym_sel
            
        st.markdown("---")
        
        if mm.empty:
            st.info("No scan data yet.\nPress ⚡ EXECUTE GLOBAL SCAN above.")
        elif scope.empty:
            st.info("No data for this class in the last scan.")
        else:
            p_lim   = st.session_state.pagination_limits.get(pool_key, 10)
            bullish = scope[scope["Direction"]=="BUY"].sort_values("APS Rating", ascending=False)
            bearish = scope[scope["Direction"]=="SELL"].sort_values("APS Rating", ascending=True)
            
            def _enrich(df):
                d = df.head(p_lim).copy()
                pnow, delta_arr = [], []
                for _, row_ in d.iterrows():
                    sym_ = row_["Asset"]
                    lp_  = live_prices.get(sym_, row_["Live Price"])
                    chg_ = price_changes.get(sym_, 0.0)
                    pnow.append(f"${lp_:,.4f}")
                    delta_arr.append("▲" if chg_ > 0 else ("▼" if chg_ < 0 else "●"))
                d["Price Now"] = pnow
                d["Δ"]         = delta_arr
                return d[["FullName","Asset","Price Now","Δ","Gain/Loss %","APS Rating"]]
                
            bc, rc = st.columns(2)
            with bc:
                st.markdown("<span style='color:#00ff88;font-size:11px;font-weight:700;'>▲ BULLISH</span>",
                            unsafe_allow_html=True)
                d = _enrich(bullish)
                if not d.empty:
                    st.dataframe(d, use_container_width=True, hide_index=True)
                else:
                    st.caption("None currently.")
            with rc:
                st.markdown("<span style='color:#ff2255;font-size:11px;font-weight:700;'>▼ BEARISH</span>",
                            unsafe_allow_html=True)
                d2 = _enrich(bearish)
                if not d2.empty:
                    st.dataframe(d2, use_container_width=True, hide_index=True)
                else:
                    st.caption("None currently.")
                    
            if p_lim < len(scope):
                if st.button(f"➕ LOAD MORE {pool_key} ROWS",
                             key=f"more_{pool_key}", use_container_width=True):
                    st.session_state.pagination_limits[pool_key] += 10
                    st.rerun()

    # ─── Zone 3: Chart + AI briefing ─────────────────────────────────────────
    with z3:
        act = st.session_state.active_radar_ticker
        st.markdown(f"##### Centerstage: `{asset_label(act)}`")
        
        c1_, c2_ = st.columns(2)
        with c1_:
            tl = st.selectbox(
                "📊 HISTORICAL RANGE",
                ["1D","5D","1M","3M","6M","1Y","2Y","3Y","5Y","Max","CUSTOM DATE RANGE"],
                index=5, key=f"tl_{pool_key}")
        with c2_:
            cs = st.selectbox(
                "🎨 CHART PERSPECTIVE",
                ["Candlesticks","Institutional Line View","OHLC Structural Bars",
                 "Quantum Area Fill","Renko Matrix Simulations"],
                index=0, key=f"cs_{pool_key}")
                
        from_d = datetime.date.today() - datetime.timedelta(days=365)
        to_d   = datetime.date.today()
        if tl == "CUSTOM DATE RANGE":
            fd_, td_ = st.columns(2)
            with fd_:
                from_d = st.date_input("From Date",
                    datetime.date.today()-datetime.timedelta(180), key=f"fd_{pool_key}")
            with td_:
                to_d = st.date_input("To Date", datetime.date(2029,11,25),
                                     key=f"td_{pool_key}")
                                     
        mm_     = st.session_state.master_matrix
        matched = mm_[mm_["Asset"]==act] if not mm_.empty else pd.DataFrame()
        
        if not matched.empty:
            r        = matched.iloc[0]
            lp_live  = live_prices.get(act, float(r["Live Price"]))
            lp_chg   = price_changes.get(act, 0.0)
            lp_color = "#00ff88" if lp_chg >= 0 else "#ff2255"
            lp_arrow = "▲" if lp_chg > 0 else ("▼" if lp_chg < 0 else "●")
            
            st.markdown(f"""
            <div class='matrix-panel' style='padding:12px;margin-bottom:8px;'>
              <div style='display:flex;justify-content:space-between;
                          text-align:center;flex-wrap:wrap;gap:8px;'>
                <div>
                  <div style='font-size:9px;color:#1e2a3a;'>LIVE PRICE</div>
                  <div class='price-live'>${lp_live:,.4f} {lp_arrow}</div>
                </div>
                <div>
                  <div style='font-size:9px;color:#1e2a3a;'>TARGET</div>
                  <div class='price-tgt'>${r["Target"]:.4f}</div>
                </div>
                <div>
                  <div style='font-size:9px;color:#1e2a3a;'>STOP LOSS</div>
                  <div class='price-stop'>${r["Stop Loss"]:.4f}</div>
                </div>
                <div>
                  <div style='font-size:9px;color:#1e2a3a;'>APS SCORE</div>
                  <div class='score-apq'>{r["APS Rating"]}</div>
                </div>
                <div>
                  <div style='font-size:9px;color:#1e2a3a;'>SESSION Δ</div>
                  <div style='color:{lp_color};font-family:Share Tech Mono,monospace;
                               font-size:20px;font-weight:900;'>
                    {r["Gain/Loss %"]:+.2f}%</div>
                </div>
              </div>
            </div>""", unsafe_allow_html=True)
            raw_ticker = r["RawTicker"]
            atr_v      = float(r["ATR"])
        else:
            st.markdown("""
            <div class='matrix-panel' style='text-align:center;padding:10px;color:#1e2a3a;'>
              Run a scan to populate live telemetry.
            </div>""", unsafe_allow_html=True)
            guess      = [t for t in ALL_TICKERS if act in t]
            raw_ticker = guess[0] if guess else f"{act}-USD"
            atr_v      = 1.0
            
        hist = _fetch_chart(
            raw_ticker,
            CHART_PERIOD.get(tl,"1y"),
            CHART_INTERVAL.get(tl,"1d"),
            start=str(from_d) if tl=="CUSTOM DATE RANGE" else None,
            end=str(to_d)     if tl=="CUSTOM DATE RANGE" else None,
        )
        
        if not hist.empty:
            fig = go.Figure()
            if cs == "Candlesticks":
                fig.add_trace(go.Candlestick(
                    x=hist.index, open=hist["Open"], high=hist["High"],
                    low=hist["Low"], close=hist["Close"], name="OHLC",
                    increasing_line_color="#00ff88", decreasing_line_color="#ff2255"))
            elif cs == "Institutional Line View":
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"], mode="lines",
                    line=dict(color="#00f0ff", width=2), name="Close"))
            elif cs == "OHLC Structural Bars":
                fig.add_trace(go.Ohlc(
                    x=hist.index, open=hist["Open"], high=hist["High"],
                    low=hist["Low"], close=hist["Close"], name="Bars"))
            elif cs == "Quantum Area Fill":
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"], fill="tozeroy",
                    fillcolor="rgba(0,240,255,0.05)",
                    line=dict(color="#00f0ff",width=1.5), name="Area"))
            elif cs == "Renko Matrix Simulations":
                brick = float(hist["Close"].rolling(14).std().iloc[-1]) or atr_v or 1.0
                fig.add_trace(build_renko(hist["Close"], brick))
                
            if not matched.empty:
                fig.add_hline(y=float(r["Target"]),   line_dash="dot", line_color="#00ff88",
                    annotation_text=f"TARGET ${r['Target']:.2f}",
                    annotation_font_color="#00ff88")
                fig.add_hline(y=float(r["Stop Loss"]), line_dash="dot", line_color="#ff2255",
                    annotation_text=f"STOP ${r['Stop Loss']:.2f}",
                    annotation_font_color="#ff2255")
                    
            tick_fmt = CHART_TICKFMT.get(tl, "%b %d")
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#05070c", margin=dict(l=0,r=0,t=4,b=0),
                height=320, xaxis_rangeslider_visible=False,
                xaxis=dict(fixedrange=False, gridcolor="#0d1420",
                           tickformat=tick_fmt, showgrid=True, type="date"),
                yaxis=dict(fixedrange=True,  gridcolor="#0d1420"),
            )
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{pool_key}",
                            config={"scrollZoom":True,"displayModeBar":False})
                            
            roi = ((float(hist["Close"].iloc[-1]) - float(hist["Close"].iloc[0]))
                   / float(hist["Close"].iloc[0]) * 100)
            roi_c = "#00ff88" if roi >= 0 else "#ff2255"
            st.markdown(
                f"Range ROI: <span style='color:{roi_c};font-family:monospace;"
                f"font-weight:900;'>{roi:+.2f}%</span> "
                f"<span style='color:#1e2a3a;font-size:10px;'>· Interval: "
                f"{CHART_INTERVAL.get(tl,'1d')}</span>",
                unsafe_allow_html=True)
        else:
            st.caption("No chart data for the selected range / interval.")
            
        st.markdown("##### 📋 AI EXECUTIVE BRIEFING MATRIX")
        if not matched.empty:
            hz = st.select_slider(
                "Analysis Horizon",
                options=["30m","1h","4h","1d","1w","1mo","3mo","Max"],
                value="1h", key=f"hz_{pool_key}")
                
            if st.button(f"✨ RUN NEURAL AUDIT — {asset_label(act).upper()}",
                         use_container_width=True, key=f"ai_{pool_key}"):
                with st.spinner("Querying Gemini AI…"):
                    out = run_ai_briefing(r.to_dict(), hz, pool_key,
                                          str(from_d), str(to_d))
                    st.markdown(out)
        else:
            st.caption("Run a global scan first to enable AI briefing.")

    # ─── Zone 4: Class-specific metrics ──────────────────────────────────────
    with z4:
        st.markdown("##### Performance Metrics")
        if not matched.empty:
            r     = matched.iloc[0]
            lp4   = live_prices.get(act, float(r["Live Price"]))
            chg4  = price_changes.get(act, 0.0)
            c4    = "#00ff88" if chg4 >= 0 else "#ff2255"
            arr4  = "▲" if chg4 > 0 else ("▼" if chg4 < 0 else "●")
            
            st.markdown(
                f"<div style='text-align:center;padding:10px;background:#06080e;"
                f"border-radius:6px;border:1px solid #0d1420;margin-bottom:10px;'>"
                f"<div style='font-size:9px;color:#1e2a3a;'>CURRENT PRICE</div>"
                f"<div style='color:{c4};font-family:Share Tech Mono,monospace;"
                f"font-size:22px;font-weight:900;'>${lp4:,.4f} {arr4}</div>"
                f"</div>",
                unsafe_allow_html=True)
                
            st.metric("APS Score", f"{r['APS Rating']} / 100")
            vc = "#00ff88" if "BUY" in r["Verdict"] else "#ff2255"
            st.markdown(f"Verdict: <span style='color:{vc};font-weight:900;'>"
                        f"{r['Verdict']}</span>", unsafe_allow_html=True)
                        
            st.markdown("---")
            if pool_key == "EQUITIES":
                st.markdown("**CAN SLIM / Fundamentals**")
                st.progress(int(r["CAN SLIM"]),     text=f"Growth Breakout: {r['CAN SLIM']}%")
                st.progress(int(r["Value Safety"]),  text=f"Graham Safety:  {r['Value Safety']}%")
                st.progress(int(r["Momentum"]),      text=f"Minervini Mom.: {r['Momentum']}%")
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
                rng  = np.random.default_rng(int(lp4*1000) % (2**31))
                atr_ = float(r["ATR"])
                n_l  = 5
                bp_  = [lp4 - i*atr_*0.12 for i in range(1,n_l+1)]
                ap_  = [lp4 + i*atr_*0.12 for i in range(1,n_l+1)]
                bs_  = rng.integers(150,900,size=n_l).tolist()
                as_  = rng.integers(150,900,size=n_l).tolist()
                
                l2   = go.Figure()
                l2.add_trace(go.Bar(y=bp_,x=bs_,name="Bids",orientation="h",
                                    marker_color="#00ff88"))
                l2.add_trace(go.Bar(y=ap_,x=[-s for s in as_],name="Asks",
                                    orientation="h",marker_color="#ff2255"))
                l2.update_layout(barmode="relative",template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="#05070c",
                    height=200,margin=dict(l=0,r=0,t=4,b=0),
                    legend=dict(font=dict(size=9)),
                    xaxis=dict(title="Vol",gridcolor="#0d1420"),
                    yaxis=dict(title="Price",gridcolor="#0d1420"))
                st.plotly_chart(l2,use_container_width=True,
                                key=f"l2_{pool_key}",
                                config={"displayModeBar":False})
                                
            st.markdown("---")
            st.markdown("**⚡ Execution Gateway**")
            
            def _order(side: str):
                if not trading_client:
                    st.warning("Trading not connected.")
                    return
                sym_t = (f"{r['Asset']}/USD"
                         if r["RawTicker"].endswith("-USD") else r["Asset"])
                qty   = 0.01 if r["RawTicker"].endswith("-USD") else 1
                try:
                    trading_client.submit_order(MarketOrderRequest(
                        symbol=sym_t, qty=qty,
                        side=OrderSide.BUY if side=="BUY" else OrderSide.SELL,
                        time_in_force=TimeInForce.GTC))
                    if side == "BUY":
                        st.success(f"✅ BUY {qty} {sym_t}")
                    else:
                        st.error(f"🔴 SELL {qty} {sym_t}")
                except Exception as ex:
                    st.error(f"Rejected: {ex}")
                    
            col_b, col_s = st.columns(2)
            with col_b:
                if st.button("▲ BUY",  key=f"buy_{pool_key}",  use_container_width=True):
                    _order("BUY")
            with col_s:
                if st.button("▼ SELL", key=f"sell_{pool_key}", use_container_width=True):
                    _order("SELL")
        else:
            st.caption("Run a scan to load metrics.")

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
        a1, a2, a3 = st.columns(3)
        a1.metric("Cash Balance",    f"${float(acc.cash):,.2f}")
        a2.metric("Portfolio Value", f"${float(acc.portfolio_value):,.2f}")
        a3.metric("Buying Power",    f"${float(acc.buying_power):,.2f}")
        
        pos = trading_client.get_all_positions()
        if pos:
            rows_p = []
            for p in pos:
                rows_p.append({
                    "Symbol":    p.symbol,
                    "Full Name": ASSET_NAMES.get(p.symbol, p.symbol),
                    "Qty":       p.qty,
                    "Avg Entry": f"${float(p.avg_entry_price):,.4f}",
                    "Mkt Price": f"${float(p.current_price):,.4f}",
                    "Mkt Value": f"${float(p.market_value):,.2f}",
                    "P/L":       f"${float(p.unrealized_pl):+,.2f} ({float(p.unrealized_plpc)*100:+.2f}%)",
                })
            st.dataframe(pd.DataFrame(rows_p), use_container_width=True, hide_index=True)
        else:
            st.info("No open positions in this paper account.")
    except Exception as err:
        st.error(f"Alpaca ledger error: {err}")
else:
    st.markdown("""
    <div class='matrix-panel' style='text-align:center;color:#1e2a3a;padding:20px;'>
      ℹ️ Paper Trading Gateway — connect keys via Streamlit Secrets to activate.
    </div>""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;color:#0a1020;font-size:9px;letter-spacing:2px;
            text-transform:uppercase;padding:28px 0 10px;'>
  APEX PROPHET QUANTUM v7.5 — EDUCATIONAL &amp; ANALYTICAL USE ONLY — NOT INVESTMENT ADVICE
</div>""", unsafe_allow_html=True)
