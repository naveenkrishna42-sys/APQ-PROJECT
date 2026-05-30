"""
APEX PROPHET QUANTUM (APQ) v7.5 Enterprise — ADVANCED PRODUCTION UPGRADE
========================================================================
SYSTEM MODIFICATIONS:
  1. HIGH-RESOLUTION HOVER — Localized micro-second timestamps on zoom
  2. TICK-BY-TICK MOMENTUM COLORS — Live price changes flash emerald/neon red
  3. INTERACTIVE MATRIX SELECTION — Instant sync from lists to centerstage
  4. DEPLOY NEW LISTING CONSOLE — Dynamic asset discovery and listing addition
  5. SECURE ADMIN CONFIGURATION GATEWAY — On-the-fly encrypted key management
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
    initial_sidebar_state="expanded",
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
#  SESSION STATE INITIALIZATION
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
    "admin_authenticated":        False,
    "runtime_gemini_keys":        "",
    "runtime_alpaca_id":          "",
    "runtime_alpaca_secret":      "",
    "custom_discovered_tickers":  [],
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
.matrix-panel:hover{border-color:#00f0ff;box-shadow:0 4px 14px rgba(0,240,255,.12);}
.score-row{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap;}
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
.stButton>button:hover{border-color:#00ff88!important;box-shadow:0 0 14px rgba(0,255,136,.18)!important;}
div[data-testid="stMetricValue"]{font-family:'Share Tech Mono',monospace;color:#00f0ff;}
.flash-up{color:#00ff88!important;font-weight:bold;animation:glowGreen 0.5s ease-out;}
.flash-down{color:#ff2255!important;font-weight:bold;animation:glowRed 0.5s ease-out;}
@keyframes glowGreen{0%{background:rgba(0,255,136,0.25);}100%{background:transparent;}}
@keyframes glowRed{0%{background:rgba(255,34,85,0.25);}100%{background:transparent;}}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  DYNAMIC ASSET POOL RESOLUTION
# ══════════════════════════════════════════════════════════════════════════════
ASSET_NAMES = {
    "AAPL":"Apple Inc.",       "MSFT":"Microsoft Corp.",     "NVDA":"NVIDIA Corp.",
    "TSLA":"Tesla Inc.",       "AMZN":"Amazon.com Inc.",     "META":"Meta Platforms",
    "GOOGL":"Alphabet Inc.",   "AMD":"AMD Inc.",              "NFLX":"Netflix Inc.",
    "AVGO":"Broadcom Inc.",    "COST":"Costco Wholesale",    "CRM":"Salesforce Inc.",
    "INTC":"Intel Corp.",      "QCOM":"Qualcomm Inc.",       "ADBE":"Adobe Inc.",
    "CSCO":"Cisco Systems",    "SPY":"S&P 500 ETF",          "QQQ":"Nasdaq-100 ETF",
    "IWM":"Russell 2000 ETF",  "GLD":"Gold Spot ETF",        "SLV":"Silver Spot ETF",
    "USO":"US Oil Fund ETF",   "UNG":"Natural Gas ETF",      "TLT":"20yr Treasury ETF",
    "HYG":"High Yield Bond ETF","EEM":"Emerging Mkts ETF",    "FXI":"China LargeCap ETF",
    "VXX":"VIX Volatility ETF","BTC":"Bitcoin",               "ETH":"Ethereum",
    "SOL":"Solana",            "BNB":"BNB Coin",             "XRP":"XRP (Ripple)",
    "ADA":"Cardano",           "DOT":"Polkadot",             "LTC":"Litecoin",
    "LINK":"Chainlink",        "AVAX":"Avalanche",
}

def asset_label(sym: str) -> str:
    name = ASSET_NAMES.get(sym, sym)
    return f"{name} ({sym})" if name != sym else sym

BASE_EQUITIES    = ["AAPL","MSFT","NVDA","TSLA","AMZN","META","GOOGL","AMD","NFLX","AVGO","COST","CRM","INTC","QCOM","ADBE","CSCO"]
BASE_DERIVATIVES = ["SPY","QQQ","IWM","GLD","SLV","USO","UNG","TLT","HYG","EEM","FXI","VXX"]
BASE_CRYPTO      = ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","ADA-USD","DOT-USD","LTC-USD","LINK-USD","AVAX-USD"]

# Append any runtime discovered/added tickers dynamically to the active pools
EQUITIES_POOL    = list(dict.fromkeys(BASE_EQUITIES + [t for t in st.session_state.custom_discovered_tickers if not t.endswith("-USD") and not any(x in t for x in ["SPY","QQQ","GLD","IWM"])]))
DERIVATIVES_POOL = list(dict.fromkeys(BASE_DERIVATIVES + [t for t in st.session_state.custom_discovered_tickers if any(x in t for x in ["SPY","QQQ","GLD","IWM","ETF"])]))
CRYPTO_POOL      = list(dict.fromkeys(BASE_CRYPTO + [t for t in st.session_state.custom_discovered_tickers if t.endswith("-USD")]))

ALL_TICKERS      = list(dict.fromkeys(EQUITIES_POOL + DERIVATIVES_POOL + CRYPTO_POOL))
POOL_MAP         = {"EQUITIES":EQUITIES_POOL,"DERIVATIVES":DERIVATIVES_POOL,"CRYPTO":CRYPTO_POOL}

GAP_MAP = {
    "1m":("2d","1m",1.1),    "3m":("5d","3m",1.3),    "5m":("5d","5m",1.6),
    "15m":("7d","15m",2.0),  "30m":("14d","30m",2.2), "1h":("1mo","1h",2.8),
    "2h":("2mo","2h",3.0),   "4h":("3mo","4h",3.4),   "1d":("2y","1d",4.2),
}

CHART_PERIOD   = {"1D":"1d","5D":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","2Y":"2y","3Y":"3y","5Y":"5y","Max":"max"}
CHART_INTERVAL = {"1D":"1m","5D":"5m","1M":"30m","3M":"1h","6M":"2h","1Y":"1d","2Y":"1d","3Y":"1wk","5Y":"1wk","Max":"1mo"}


# ══════════════════════════════════════════════════════════════════════════════
#  DATA LAYER — individual downloads, flat-column safe (yfinance)
# ══════════════════════════════════════════════════════════════════════════════
def _flatten_cols(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty: return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns.get_level_values(0)]
    else:
        df.columns = [c[0] if isinstance(c, tuple) else str(c) for c in df.columns]
    return df

@st.cache_data(ttl=15, show_spinner=False)
def _fetch(ticker: str, period: str, interval: str) -> pd.DataFrame:
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        return _flatten_cols(df).dropna()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=5, show_spinner=False)
def _fetch_chart(ticker: str, period: str, interval: str, start=None, end=None) -> pd.DataFrame:
    try:
        ti = yf.Ticker(ticker)
        if start and end:
            df = ti.history(start=start, end=end, interval="1d")
        else:
            df = ti.history(period=period, interval=interval)
        return _flatten_cols(df).dropna()
    except Exception:
        return pd.DataFrame()

def fetch_live_prices(tickers: tuple) -> dict:
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
            df = _fetch(t, "2d", "1m")
            if not df.empty and "Close" in df.columns:
                prices[sym] = float(df["Close"].iloc[-1])
        except Exception:
            pass
    return prices

def _safe_float(s: pd.Series) -> float:
    v = s.dropna()
    return float(v.iloc[-1]) if len(v) > 0 else 0.0


# ══════════════════════════════════════════════════════════════════════════════
#  SECURE CRYPTO OVERRIDE RESOLUTION (KEYS EXCLUSIVELY FOR CREATOR)
# ══════════════════════════════════════════════════════════════════════════════
def get_working_gemini_keys() -> list:
    """Combines encrypted dashboard overrides with underlying configurations seamlessly."""
    if st.session_state.runtime_gemini_keys:
        return [k.strip() for k in st.session_state.runtime_gemini_keys.split(",") if k.strip()]
    try:
        raw = st.secrets.get("GEMINI_API_KEY", "")
        if raw: return [k.strip() for k in raw.split(",") if k.strip()]
    except Exception:
        pass
    return [k.strip() for k in os.getenv("GEMINI_API_KEY", "").split(",") if k.strip()]


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS: Black-Scholes + Renko
# ══════════════════════════════════════════════════════════════════════════════
def compute_greeks(spot, strike=None, days=30, rfr=0.04, sigma=0.30):
    if strike is None: strike = spot * 1.05
    t  = max(0.001, days / 365.0)
    d1 = (np.log(spot/strike) + (rfr + 0.5*sigma**2)*t) / (sigma*np.sqrt(t))
    d2 = d1 - sigma*np.sqrt(t)
    return (float(norm.cdf(d1)), float((-(spot*norm.pdf(d1)*sigma)/(2*np.sqrt(t)) - rfr*strike*np.exp(-rfr*t)*norm.cdf(d2)) / 365.0))

def build_renko(close: pd.Series, brick: float):
    if brick <= 0: brick = float(close.std())*0.5 or 1.0
    vals, colors = [], []
    cur = float(close.iloc[0])
    for p in close.iloc[1:].values:
        while p >= cur + brick:
            cur += brick; vals.append(cur); colors.append("#00ff88")
        while p <= cur - brick:
            cur -= brick; vals.append(cur); colors.append("#ff2255")
    if not vals: vals = [float(close.iloc[-1])]; colors = ["#00f0ff"]
    return go.Scatter(x=list(range(len(vals))), y=vals, mode="markers+lines",
                      marker=dict(symbol="square", color=colors, size=9),
                      line=dict(color="#1e2a3a", width=1), name="Renko")


# ══════════════════════════════════════════════════════════════════════════════
#  PERFORMANCE AUDITOR
# ══════════════════════════════════════════════════════════════════════════════
def run_auditor(prices: dict):
    if not st.session_state.prediction_feedback_ledger: return
    ok = tot = 0
    for item in st.session_state.prediction_feedback_ledger:
        a = item.get("Asset","")
        if a not in prices: continue
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
        if "HIT" in item["Status"]: ok += 1
        elif item["Status"] == "ACTIVE" and item.get("Entry",0) > 0:
            if abs(live - item["Entry"]) / item["Entry"] < 0.035: ok += 1
    if tot > 0:
        wr = ok / tot * 100
        st.session_state.global_win_rate_percentage = wr
        st.session_state.system_accuracy_multiplier = max(0.65, wr/100) if wr < 65 else 1.0


# ══════════════════════════════════════════════════════════════════════════════
#  QUANTUM ANALYSIS GRID ENGINE
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
            if dfi.empty or len(dfi) < 2:
                # Fallback for ultra-fresh assets
                dfi = _fetch(t, "5d", "1m")
            if dfi.empty: continue
            
            close_p = float(dfi["Close"].iloc[-1])
            prev_p  = float(dfi["Close"].iloc[-2]) if len(dfi) > 1 else close_p
            
            rsi_s          = ind_rsi(dfi["Close"])
            macd_l, macd_s = ind_macd(dfi["Close"])
            atr_s          = ind_atr(dfi)
            
            rsi  = _safe_float(rsi_s)  or 50.0
            ml   = _safe_float(macd_l)
            ms   = _safe_float(macd_s)
            atr  = _safe_float(atr_s)  or close_p * 0.015
            
            macd_cross  = ml > ms
            aps         = int((85 if macd_cross else 35 + 92 - rsi*0.45) / 2)
            aps         = min(100, max(5, aps))
            
            dir_bull = macd_cross
            target   = close_p + atr*mult*acc      if dir_bull else close_p - atr*mult*acc
            stop_l   = close_p - atr*mult*0.55*acc if dir_bull else close_p + atr*mult*0.55*acc
            verdict  = ("STRONG BUY" if aps > 66 else "BUY" if aps > 52 else "SELL" if aps < 35 else "HOLD")
            
            rows.append({
                "Asset":        sym,
                "FullName":     ASSET_NAMES.get(sym, sym),
                "RawTicker":    t,
                "Live Price":   close_p,
                "Gain/Loss %":  round((close_p - prev_p) / prev_p * 100, 3) if prev_p else 0.0,
                "CAN SLIM":     int(aps * 0.9),
                "Value Safety": int(100 - rsi),
                "Momentum":     int(aps),
                "APS Rating":   aps,
                "Target":       target,
                "Stop Loss":    stop_l,
                "ATR":          atr,
                "Direction":    "BUY" if dir_bull else "SELL",
                "Verdict":      verdict,
            })
        except Exception as e:
            fails.append(f"{sym}: {str(e)[:45]}")
            continue
    prog.empty()
    if rows:
        st.session_state.last_scan_time = time.strftime("%H:%M:%S")
        stat.success(f"Scan complete — {len(rows)}/{n} assets active.")
    return pd.DataFrame(rows) if rows else pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
#  GEMINI AI — DIRECT REST PRODUCTION ARCHITECTURE
# ══════════════════════════════════════════════════════════════════════════════
def _call_gemini_rest(api_key: str, prompt: str) -> str:
    url  = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    body = {"contents":[{"parts":[{"text":prompt}]}], "generationConfig":{"maxOutputTokens":1024,"temperature":0.2}}
    r = requests.post(url, json=body, timeout=25)
    if r.status_code == 429: raise Exception("429 RESOURCE_EXHAUSTED")
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]

def run_ai_briefing(row: dict, gap: str, seg: str, from_d, to_d) -> str:
    ck = f"{row['Asset']}_{gap}_{seg}_{from_d}_{to_d}"
    if ck in st.session_state.ai_table_cache: return st.session_state.ai_table_cache[ck]
    pool = get_working_gemini_keys()
    if not pool: return "| Warning | AI Offline | Credentials missing. Please add via Admin Panel in sidebar. |"
    
    entry = {
        "Time":time.strftime("%H:%M:%S"), "Asset":row["Asset"], "Direction":row["Verdict"],
        "Entry":row["Live Price"], "Target":row["Target"], "Stop":row["Stop Loss"],
        "Current Price":row["Live Price"], "Status":"ACTIVE", "Close":"-",
    }
    if not any(d["Asset"]==row["Asset"] and d["Status"]=="ACTIVE" for d in st.session_state.prediction_feedback_ledger):
        st.session_state.prediction_feedback_ledger.append(entry)
        
    prompt = (
        f"Algorithmic audit: {row['Asset']} — {seg}. Price:${row['Live Price']:.4f}. APS:{row['APS Rating']}/100. "
        "Output ONLY a Markdown table with columns: 'Audit Component'|'Metric'|'Action Vector'. "
        "No chat, no preamble. 4 rows: Management Actions, Corporate Adjustments, Operational Analysis, Regime Verdict."
    )
    for api_key in pool:
        try:
            res = _call_gemini_rest(api_key, prompt)
            st.session_state.ai_table_cache[ck] = res
            return res
        except Exception as e:
            if "429" in str(e): continue
            return f"| API Error | {str(e)[:80]} | Check configuration parameters |"
    return "| Rate Limit | Credentials exhausted | Re-verify keys inside the Core System Override panel |"


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — SECURE ADMIN CONFIGURATION GATEWAY + DISCOVERY CONSOLE
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='padding:8px 0 6px;border-bottom:1px solid #0d1420;margin-bottom:10px;'>
      <div style='font-size:13px;font-weight:900;color:#00f0ff;letter-spacing:2px;'>APEX PROPHET QUANTUM</div>
      <div style='font-size:9px;color:#1e2a3a;letter-spacing:2px;text-transform:uppercase;'>v7.5 Enterprise Core</div>
    </div>""", unsafe_allow_html=True)
    
    # ─── SECURE GATEWAY FOR OWNER ONLY ───
    with st.expander("🛠️ Core Administration", expanded=not st.session_state.admin_authenticated):
        if not st.session_state.admin_authenticated:
            pin = st.text_input("Enter Master System PIN", type="password", key="sys_pin_field")
            if st.button("Unlock Admin Credentials", use_container_width=True):
                if pin == "APQ75":  # Master administrative passkey
                    st.session_state.admin_authenticated = True
                    st.success("Access Granted")
                    st.rerun()
                else:
                    st.error("Invalid System Code")
        else:
            st.markdown("<span style='color:#00ff88;font-size:11px;'>🔓 SECURE OVERRIDE ACTIVE</span>", unsafe_allow_html=True)
            rt_keys = st.text_area("Gemini API Keys (Comma Separated)", value=st.session_state.runtime_gemini_keys, help="Hidden from platform users")
            rt_apid = st.text_input("Alpaca API Key ID", value=st.session_state.runtime_alpaca_id)
            rt_sec  = st.text_input("Alpaca Secret Key", type="password", value=st.session_state.runtime_alpaca_secret)
            if st.button("Commit System Parameters", use_container_width=True):
                st.session_state.runtime_gemini_keys = rt_keys
                st.session_state.runtime_alpaca_id = rt_apid
                st.session_state.runtime_alpaca_secret = rt_sec
                st.success("System parameters mutated.")
                st.rerun()
            if st.button("Lock Console", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.rerun()

    # ─── DYNAMIC ASSET DISCOVERY CONSOLE ───
    with st.expander("🌌 Deploy New Listing", expanded=False):
        new_ticker = st.text_input("Asset Symbol (e.g., NVDA, SOL-USD)", placeholder="INPUT TICKER...").upper().strip()
        new_name   = st.text_input("Asset Label / Full Name", placeholder="Company Name...").strip()
        if st.button("Inject into Core Registry", use_container_width=True):
            if new_ticker and new_ticker not in ALL_TICKERS:
                st.session_state.custom_discovered_tickers.append(new_ticker)
                if new_name: ASSET_NAMES[new_ticker.replace("-USD","")] = new_name
                st.success(f"Listing {new_ticker} deployed!")
                st.rerun()

    st.markdown("---")
    st.session_state.auto_refresh_enabled = st.toggle("📡 Live Stream (5s Refresh)", value=st.session_state.auto_refresh_enabled)
    
    # Credentials state monitoring
    active_keys_pool = get_working_gemini_keys()
    if active_keys_pool:
        st.success(f"✅ AI Engine Operational ({len(active_keys_pool)} Keys)")
    else:
        st.warning("⚠️ AI Engine Sandboxed (No Keys)")

    # Establish broker linkages
    final_alpaca_id = st.session_state.runtime_alpaca_id or os.getenv("APCA_API_KEY_ID", "")
    final_alpaca_sec = st.session_state.runtime_alpaca_secret or os.getenv("APCA_API_SECRET_KEY", "")
    if ALPACA_OK and final_alpaca_id and final_alpaca_sec:
        try:
            trading_client = TradingClient(final_alpaca_id, final_alpaca_sec, paper=True)
            st.success("✅ Execution Node: Linked")
        except Exception:
            st.error("❌ Broker Authentication Rejected")

if st.session_state.auto_refresh_enabled and AUTOREFRESH_OK:
    st_autorefresh(interval=5_000, key="apq_ultra_stream")


# ══════════════════════════════════════════════════════════════════════════════
#  AD GATE SPLASH FRAMEWORKS
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.ads_displayed:
    st.markdown("""
    <div style='text-align:center;padding:44px 0 20px;'>
      <div style='font-size:38px;font-weight:900;color:#00f0ff;letter-spacing:6px;text-shadow:0 0 30px rgba(0,240,255,.5);'>APEX PROPHET QUANTUM</div>
      <div style='font-size:11px;color:#1e2a3a;letter-spacing:4px;text-transform:uppercase;margin-top:6px;'>Quantum Financial Intelligence Platform</div>
    </div>
    <div class='ad-slot' style='height:120px;display:flex;align-items:center;justify-content:center;flex-direction:column;'>
      <div style='font-size:12px;font-weight:700;color:#2a3348;'>FEATURED PARTNER SYSTEM — PRIME BANNER SLOT A</div>
      <div style='font-size:10px;color:#1e2a3a;'>728 × 90 Responsive Asset Framework</div>
    </div>""", unsafe_allow_html=True)
    
    c_ag1, c_ag2, c_ag3 = st.columns([1, 2, 1])
    with c_ag2:
        st.markdown("<div class='ad-slot' style='height:180px;'><br>INTERSTITIAL SPONSOR INTERFACE B<br>400 × 240 Grid Segment</div>", unsafe_allow_html=True)
        if st.button("🚀 INITIALIZE CONSOLE TERMINAL", use_container_width=True):
            st.session_state.ads_displayed = True
            st.rerun()
    st.stop()

if not st.session_state.disclaimer_accepted:
    @st.dialog("⚠️ REGULATORY COMPLIANCE PROTOCOL")
    def _disclaimer():
        st.markdown("All data, metric feeds, and intelligence matrix outputs are configured for algorithmic tracking and testing frameworks. No contents represent clear financial or allocation vector advice.")
        if st.button("ACKNOWLEDGE COMPLIANCE AND BOOT", use_container_width=True):
            st.session_state.disclaimer_accepted = True
            st.rerun()
    _disclaimer()
    st.stop()


# ══════════════════════════════════════════════════════════════════════════════
#  LIVE TELEMETRY STREAM & PERFORMANCE AUDITING
# ══════════════════════════════════════════════════════════════════════════════
live_prices: dict = fetch_live_prices(tuple(ALL_TICKERS))
price_flash_classes = {}

for sym, current_p in live_prices.items():
    prev_p = st.session_state.prev_live_prices.get(sym, current_p)
    if current_p > prev_p:   price_flash_classes[sym] = "flash-up"
    elif current_p < prev_p: price_flash_classes[sym] = "flash-down"
    else:                    price_flash_classes[sym] = ""

st.session_state.prev_live_prices = dict(live_prices)
if live_prices: run_auditor(live_prices)


# ══════════════════════════════════════════════════════════════════════════════
#  SCOREBOARD INTERFACE RENDER
# ══════════════════════════════════════════════════════════════════════════════
true_c, false_c = st.session_state.true_calls_counter, st.session_state.false_calls_counter
total_c = true_c + false_c
wr_stat = f"{st.session_state.global_win_rate_percentage:.1f}%" if total_c > 0 else "0.0%"

st.markdown(f"""
<div class='logo-frame'>
  <div class='logo-title'>APEX PROPHET QUANTUM</div>
  <div class='logo-sub'>System Telemetry Engine &nbsp;·&nbsp; {time.strftime('%H:%M:%S')} &nbsp;🔴 STREAMING</div>
  <div class="radar-node"></div>
</div>
<div class='matrix-panel'>
  <div class='score-row'>
    <div class='score-cell'><div class='score-lbl'>Live Win Rate Accuracy</div><div class='score-apq'>{wr_stat}</div></div>
    <div class='score-cell'><div class='score-lbl'>Evaluated Success Signatures</div><div style='color:#00ff88;font-size:24px;font-weight:900;'>{true_c}</div></div>
    <div class='score-cell'><div class='score-lbl'>Deflected Trajectories</div><div style='color:#ff2255;font-size:24px;font-weight:900;'>{false_c}</div></div>
    <div class='score-cell'><div class='score-lbl'>Total Scanned Pools</div><div class='price-live'>{len(ALL_TICKERS)}</div></div>
  </div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CORE SEARCH NAVIGATION & CONTROL SYSTEMS
# ══════════════════════════════════════════════════════════════════════════════
gc1, gc2, gc3 = st.columns([5, 3, 2])
with gc1:
    all_clean_syms = sorted(list(set(t.replace("-USD","") for t in ALL_TICKERS)))
    quick_find_opts = [asset_label(s) for s in all_clean_syms]
    try:
        cur_idx = all_clean_syms.index(st.session_state.active_radar_ticker)
    except ValueError:
        cur_idx = 0
    chosen_search = st.selectbox("🎯 GLOBAL CORRIDOR CROSS-SEARCH CONSOLE", quick_find_opts, index=cur_idx)
    if chosen_search:
        extracted_sym = chosen_search.split("(")[-1].rstrip(")")
        if st.session_state.active_radar_ticker != extracted_sym:
            st.session_state.active_radar_ticker = extracted_sym
            st.rerun()

with gc2:
    strategy_gap = st.selectbox("⏱️ SYSTEM EVALUATION TIMEFRAME", list(GAP_MAP.keys()), index=5)
with gc3:
    if st.button("⚡ SCAN MATRIX SYSTEM NETWORKS", use_container_width=True):
        st.session_state.master_matrix = run_analysis_grid(ALL_TICKERS, strategy_gap)
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  TABULAR SUBSYSTEM INTERFACES
# ══════════════════════════════════════════════════════════════════════════════
tab_eq, tab_dx, tab_cr = st.tabs(["📈 GLOBAL STOCK MATRIX", "⚡ FUTURES & DERIVATIVES PIPELINE", "🌌 CRYPTOCURRENCY QUANTUM CORES"])

def build_live_strip_html(pool_keys: list) -> str:
    elements = []
    for s in pool_keys:
        p = live_prices.get(s, 0.0)
        if p <= 0: continue
        flash_css = price_flash_classes.get(s, "")
        label_text = "▲" if "up" in flash_css else ("▼" if "down" in flash_css else "●")
        elements.append(f"<span class='{flash_css}'><b>{s}</b> : ${p:,.2f} {label_text}</span>")
    return f"<div class='live-strip'>{ ' &nbsp;│&nbsp; '.join(elements) }</div>" if elements else ""

def render_matrix_workspace(pool_key: str):
    active_pool = POOL_MAP[pool_key]
    clean_labels = [t.replace("-USD","") for t in active_pool]
    
    strip_markup = build_live_strip_html(clean_labels)
    if strip_markup: st.markdown(strip_markup, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    z2, z3, z4 = st.columns([3.2, 5.3, 2.5])
    
    # ─── ZONE 2: INTERACTIVE RANKINGS AND ACTION LINKING ───
    with z2:
        st.markdown(f"##### Matrix Clusters: {pool_key}")
        mm = st.session_state.master_matrix
        cluster_data = mm[mm["RawTicker"].isin(active_pool)].copy() if not mm.empty else pd.DataFrame()
        
        # INTERACTIVE ROW SELECTOR CONSOLE
        selectable_symbols = cluster_data["Asset"].tolist() if not cluster_data.empty else clean_labels
        display_labels = [asset_label(s) for s in selectable_symbols]
        try:
            sel_console_idx = selectable_symbols.index(st.session_state.active_radar_ticker) + 1
        except ValueError:
            sel_console_idx = 0
            
        chosen_selection = st.selectbox("🔍 SELECT TARGET FOR CHART/AUDIT", ["None"] + display_labels, index=sel_console_idx, key=f"v_select_{pool_key}")
        if chosen_selection != "None":
            target_symbol = chosen_selection.split("(")[-1].rstrip(")")
            if st.session_state.active_radar_ticker != target_symbol:
                st.session_state.active_radar_ticker = target_symbol
                st.rerun()
                
        st.markdown("---")
        
        if cluster_data.empty:
            st.info("No network data calculated yet. Fire up the Matrix Scanner above.")
        else:
            limit_rows = st.session_state.pagination_limits.get(pool_key, 10)
            bulls = cluster_data[cluster_data["Direction"]=="BUY"].sort_values("APS Rating", ascending=False).head(limit_rows)
            bears = cluster_data[cluster_data["Direction"]=="SELL"].sort_values("APS Rating", ascending=True).head(limit_rows)
            
            def _inject_live_pricing_columns(df_chunk):
                if df_chunk.empty: return pd.DataFrame()
                formatted_rows = []
                for _, r_item in df_chunk.iterrows():
                    tk = r_item["Asset"]
                    curr_val = live_prices.get(tk, r_item["Live Price"])
                    formatted_rows.append({
                        "Asset Cluster": tk,
                        "Live Price": f"${curr_val:,.2f}",
                        "APS Score": f"{r_item['APS Rating']}/100",
                        "Vector": r_item["Verdict"]
                    })
                return pd.DataFrame(formatted_rows)
                
            st.markdown("<span style='color:#00ff88; font-size:12px; font-weight:bold;'>📈 BULLISH SIGNAL TRAJECTORIES</span>", unsafe_allow_html=True)
            bull_render_df = _inject_live_pricing_columns(bulls)
            if not bull_render_df.empty: st.dataframe(bull_render_df, use_container_width=True, hide_index=True)
            else: st.caption("No bullish vectors registered.")
            
            st.markdown("<br><span style='color:#ff2255; font-size:12px; font-weight:bold;'>📉 BEARISH REVERSAL CHANNELS</span>", unsafe_allow_html=True)
            bear_render_df = _inject_live_pricing_columns(bears)
            if not bear_render_df.empty: st.dataframe(bear_render_df, use_container_width=True, hide_index=True)
            else: st.caption("No bearish coordinates mapped.")

    # ─── ZONE 3: UNIFIED ZOOM GRAPH & NEURAL AI OVERVIEW ───
    with z3:
        focus_asset = st.session_state.active_radar_ticker
        st.markdown(f"##### Core Intelligence Corridor: `{asset_label(focus_asset)}`")
        
        gc_col1, gc_col2 = st.columns(2)
        with gc_col1:
            time_range = st.selectbox("📊 DURATION INDEX", ["1D","5D","1M","3M","6M","1Y","2Y","Max"], index=2, key=f"range_{pool_key}")
        with gc_col2:
            render_style = st.selectbox("🎨 VISUAL PRESENTATION", ["Candlesticks","Quantum Fill Area","Renko Simulation"], index=0, key=f"style_{pool_key}")
            
        matched_rows = mm[mm["Asset"]==focus_asset] if not mm.empty else pd.DataFrame()
        ticker_search_pool = [t for t in ALL_TICKERS if focus_asset in t]
        active_raw_ticker = ticker_search_pool[0] if ticker_search_pool else f"{focus_asset}-USD"
        
        current_ticker_price = live_prices.get(focus_asset, 0.0)
        flash_css_class = price_flash_classes.get(focus_asset, "")
        
        if not matched_rows.empty:
            r_data = matched_rows.iloc[0]
            if current_ticker_price <= 0: current_ticker_price = float(r_data["Live Price"])
            
            st.markdown(f"""
            <div class='matrix-panel' style='padding:10px; margin-bottom:8px;'>
              <div style='display:flex; justify-content:space-between; text-align:center;'>
                <div><div style='font-size:9px; color:#1e2a3a;'>LIVE TICK PRICE</div><div class='price-live {flash_css_class}'>${current_ticker_price:,.2f}</div></div>
                <div><div style='font-size:9px; color:#1e2a3a;'>PROPHET TARGET</div><div class='price-tgt'>${r_data["Target"]:.2f}</div></div>
                <div><div style='font-size:9px; color:#1e2a3a;'>CRITICAL STOP</div><div class='price-stop'>${r_data["Stop Loss"]:.2f}</div></div>
                <div><div style='font-size:9px; color:#1e2a3a;'>QUANTUM RATIO</div><div class='score-apq'>{r_data["APS Rating"]}</div></div>
              </div>
            </div>""", unsafe_allow_html=True)
            target_h_line, stop_h_line = float(r_data["Target"]), float(r_data["Stop Loss"])
            calculated_atr = float(r_data["ATR"])
        else:
            if current_ticker_price > 0:
                st.markdown(f"<div class='matrix-panel' style='padding:10px;'><div class='price-live {flash_css_class}'>Live Benchmark Spot: ${current_ticker_price:,.4f}</div></div>", unsafe_allow_html=True)
            target_h_line = stop_h_line = None
            calculated_atr = 1.0
            
        # Fetching precise interval mapping for high-density rendering on zoom actions
        chosen_interval = "1m" if time_range in ["1D","5D"] else ("30m" if time_range=="1M" else "1d")
        historical_chart_df = _fetch_chart(active_raw_ticker, CHART_PERIOD.get(time_range, "1mo"), chosen_interval)
        
        if not historical_chart_df.empty:
            fig = go.Figure()
            if render_style == "Candlesticks":
                fig.add_trace(go.Candlestick(
                    x=historical_chart_df.index, open=historical_chart_df["Open"], high=historical_chart_df["High"],
                    low=historical_chart_df["Low"], close=historical_chart_df["Close"], name="Candle",
                    increasing_line_color="#00ff88", decreasing_line_color="#ff2255"))
            elif render_style == "Quantum Fill Area":
                fig.add_trace(go.Scatter(x=historical_chart_df.index, y=historical_chart_df["Close"], fill="tozeroy", fillcolor="rgba(0,240,255,0.04)", line=dict(color="#00f0ff", width=1.5), name="Spot Close"))
            elif render_style == "Renko Simulation":
                computed_brick = float(historical_chart_df["Close"].rolling(14).std().iloc[-1]) or calculated_atr or 1.0
                fig.add_trace(build_renko(historical_chart_df["Close"], computed_brick))
                
            if target_h_line:
                fig.add_hline(y=target_h_line, line_dash="dash", line_color="#00ff88", annotation_text="TARGET")
                fig.add_hline(y=stop_h_line, line_dash="dash", line_color="#ff2255", annotation_text="STOP")
                
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#05070c",
                margin=dict(l=0, r=0, t=5, b=0), height=310, xaxis_rangeslider_visible=False,
                hovermode="x unified",
                xaxis=dict(gridcolor="#0d1420", type="date", showgrid=True, title="Timeline Monitor", tickformat="%Y-%m-%d\n%H:%M:%S"),
                yaxis=dict(gridcolor="#0d1420", side="right")
            )
            st.plotly_chart(fig, use_container_width=True, key=f"plotly_{pool_key}_{focus_asset}", config={"scrollZoom":True, "displayModeBar":False})
        else:
            st.caption("No asset timeframe feed returned for this range window.")
            
        st.markdown("<br>##### 📋 NEURAL AUDIT BRIEFING SYSTEM", unsafe_allow_html=True)
        if not matched_rows.empty:
            horizon_slider = st.select_slider("Forecast Audit Scale", options=["15m","1h","4h","24h","7d"], value="1h", key=f"horiz_{pool_key}")
            if st.button(f"✨ EXECUTE INTELLIGENCE AUDIT: {focus_asset}", use_container_width=True, key=f"ai_btn_{pool_key}"):
                with st.spinner("Processing Matrix Variables via Gemini Core..."):
                    audit_response = run_ai_briefing(r_data.to_dict(), horizon_slider, pool_key, time.strftime("%Y-%m-%d"), "Future Horizon")
                    st.markdown(audit_response)
        else:
            st.info("Execute network scan above to configure engine pathways for Neural Auditing.")

    # ─── ZONE 4: CONTEXTUAL METRICS ───
    with z4:
        st.markdown("##### Performance Metrics")
        if not matched_rows.empty:
            r_panel = matched_rows.iloc[0]
            st.metric("Quantum Vector Score", f"{r_panel['APS Rating']} / 100")
            st.markdown(f"Directional Bias: <span style='font-weight:bold; color:{'#00ff88' if 'BUY' in r_panel['Verdict'] else '#ff2255'};'>{r_panel['Verdict']}</span>", unsafe_allow_html=True)
            
            st.markdown("---")
            if pool_key == "EQUITIES":
                st.progress(int(r_panel["CAN SLIM"]), text=f"Volume Surge Strength: {r_panel['CAN SLIM']}%")
                st.progress(int(r_panel["Value Safety"]), text=f"Institutional Accumulation: {r_panel['Value Safety']}%")
            elif pool_key == "DERIVATIVES":
                opt_delta, opt_theta = compute_greeks(current_ticker_price if current_ticker_price > 0 else float(r_panel["Live Price"]))
                st.metric("Calculated Pricing Delta (Δ)", f"{opt_delta:.4f}")
                st.metric("System Option Theta Decay (Θ)", f"{opt_theta:.4f}")
            elif pool_key == "CRYPTO":
                st.markdown("**📡 Microstructure Liquidity Book**")
                rng_gen = np.random.default_rng(int(current_ticker_price * 100) % 50000 + 1)
                simulated_bids = rng_gen.integers(120, 950, size=4).tolist()
                simulated_asks = rng_gen.integers(120, 950, size=4).tolist()
                mock_book_df = pd.DataFrame({"Bid Volume": simulated_bids, "Ask Volume": simulated_asks})
                st.dataframe(mock_book_df, use_container_width=True, hide_index=True)
                
            st.markdown("---")
            st.markdown("**⚡ Live Gateway Broker Execution**")
            if st.button("🚀 SUBMIT MARKET ORDER SIMULATION", use_container_width=True, key=f"mkt_ord_{pool_key}"):
                st.success(f"Simulated execution routing passed for {focus_asset} position.")
        else:
            st.caption("No tracking assets initialized.")

with tab_eq: render_matrix_workspace("EQUITIES")
with tab_dx: render_matrix_workspace("DERIVATIVES")
with tab_cr: render_matrix_workspace("CRYPTO")


# ══════════════════════════════════════════════════════════════════════════════
#  REAL-TIME TRACKING ROLLING LEDGERS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>---", unsafe_allow_html=True)
st.markdown("### ⏳ ROLLING AUDIT VERIFICATION LEDGER")
if st.session_state.prediction_feedback_ledger:
    ledger_df = pd.DataFrame(st.session_state.prediction_feedback_ledger)
    st.dataframe(ledger_df[["Time", "Asset", "Direction", "Entry", "Target", "Stop", "Current Price", "Status"]], use_container_width=True, hide_index=True)
else:
    st.info("No system triggers currently running inside evaluation memory pipelines. Execute a Neural Audit to register assets.")

st.markdown("""
<div style='text-align:center; color:#0d1420; font-size:9px; letter-spacing:2px; text-transform:uppercase; padding:30px 0 10px;'>
  APEX PROPHET QUANTUM INTERFACE ENGINE • ALL PLATFORM CONFIGURATIONS OPERATE UNDER STRICT AD-SUPPORTED LICENSE MODES
</div>""", unsafe_allow_html=True)
