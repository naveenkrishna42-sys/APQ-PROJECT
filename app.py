"""
PLANET9WORLD QUANTUM PLATFORM (ENTERPRISE CORE v8.5)
===================================================
SYSTEM MODIFICATIONS:
  1. EMBEDDED QUANTUM SCORING ENGINE — Completely eliminates external AI APIs.
  2. ST.FRAGMENT ISOLATION — Ticks and charts stream without page jitter.
  3. DYNAMIC PARAMETER SORTING — Ranks market indicators by statistical urgency.
  4. PLANET9WORLD ULTRA-CONTRAST THEME — High text visibility with neon accents.
"""
import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import plotly.graph_objects as go
import time
import warnings
import logging

warnings.filterwarnings("ignore")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)

st.set_page_config(
    page_title="PLANET9WORLD QUANTUM CORE",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INITIALIZATION
# ══════════════════════════════════════════════════════════════════════════════
if "active_radar_ticker" not in st.session_state:
    st.session_state.active_radar_ticker = "BTC-USD"
if "master_matrix" not in st.session_state:
    st.session_state.master_matrix = pd.DataFrame()
if "custom_pool" not in st.session_state:
    st.session_state.custom_pool = []

# ══════════════════════════════════════════════════════════════════════════════
#  HIGH-CONTRAST SYSTEM CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Exo+2:wght@400;700;900&display=swap');
html, body, .stApp { background: #020408 !important; color: #f8fafc !important; font-family: 'Exo 2', sans-serif; }
.p9-header { border-bottom: 2px solid #00f0ff; padding-bottom: 10px; margin-bottom: 20px; }
.p9-title { font-weight: 900; color: #ffffff; letter-spacing: 3px; font-size: 26px; }
.p9-subtitle { color: #00f0ff; font-family: 'Share Tech Mono', monospace; font-size: 11px; letter-spacing: 2px; }
.price-metric { font-family: 'Share Tech Mono', monospace; font-size: 32px; font-weight: 900; text-shadow: 0 0 10px rgba(0,240,255,0.5); }
.val-up { color: #00ff88 !important; }
.val-down { color: #ff2255 !important; }
.matrix-container { background: #090d1a; border: 1px solid #1e293b; border-radius: 8px; padding: 18px; margin-bottom: 15px; }
.stButton>button { background: linear-gradient(90deg, #0f172a, #1e293b) !important; color: #ffffff !important; border: 1px solid #384ddb !important; font-weight: 700 !important; font-size: 14px; }
.stButton>button:hover { border-color: #00ff88 !important; box-shadow: 0 0 12px rgba(0,255,136,0.4) !important; }
h4, h5 { color: #ffffff !important; font-weight: 700 !important; letter-spacing: 1px; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  NATIVE COMPACT LIGHTWEIGHT "AI" ENGINE (ALGORITHMIC VERDICT)
# ══════════════════════════════════════════════════════════════════════════════
def run_native_ai_audit(df: pd.DataFrame) -> pd.DataFrame:
    """
    Acts as an internal, lightweight AI module.
    Calculates key trading parameters, determines anomalies, and sorts them by impact urgency.
    """
    if df.empty or len(df) < 15:
        return pd.DataFrame([{
            "Parameter Vector": "Insufficient Historical Depth",
            "Calculated Metric": "N/A",
            "Impact Weight": "CRITICAL",
            "Strategic Allocation Vector": "Awaiting Data Arrays"
        }])

    close_series = df["Close"]
    high_series = df["High"]
    low_series = df["Low"]

    # 1. Trend Vector (EMA Crossover Matrix)
    ema_fast = close_series.ewm(span=5, adjust=False).mean().iloc[-1]
    ema_slow = close_series.ewm(span=15, adjust=False).mean().iloc[-1]
    trend_deviation = abs(ema_fast - ema_slow) / ema_slow * 100
    trend_dir = "BULLISH EXPANSION" if ema_fast >= ema_slow else "BEARISH COMPRESSION"

    # 2. Momentum Vector (Internal RSI Calculation)
    delta = close_series.diff()
    gain = delta.clip(lower=0).rolling(window=14).mean().iloc[-1]
    loss = (-delta.clip(upper=0)).rolling(window=14).mean().iloc[-1]
    rsi = 100 - (100 / (1 + (gain / loss if loss != 0 else 1)))
    rsi_anomaly = abs(rsi - 50)

    # 3. Volatility Vector (ATR Calculation)
    tr = pd.concat([high_series - low_series, (high_series - close_series.shift()).abs(), (low_series - close_series.shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(14).mean().iloc[-1]
    volatility_ratio = (atr / close_series.iloc[-1]) * 100

    # 4. Mean Reversion Vector (Bollinger Band Positioning)
    sma_20 = close_series.rolling(20).mean().iloc[-1]
    std_20 = close_series.rolling(20).std().iloc[-1]
    bb_position = ((close_series.iloc[-1] - sma_20) / (2 * std_20 if std_20 != 0 else 1)) * 100

    # Compile findings to allow the code to "decide" what matters most right now
    parameters = [
        {
            "Parameter Vector": "⚡ MACD/EMA Trend Bias",
            "Calculated Metric": f"{trend_dir} ({trend_deviation:.2f}% Dev)",
            "Impact Weight": round(trend_deviation * 2.5, 2),
            "Strategic Allocation Vector": "Maintain current momentum exposures" if ema_fast >= ema_slow else "Hedge spot inventory risks"
        },
        {
            "Parameter Vector": "🔮 RSI Momentum Wave",
            "Calculated Metric": f"RSI @ {rsi:.2f}",
            "Impact Weight": round(rsi_anomaly, 2),
            "Strategic Allocation Vector": "Overextended Upside" if rsi > 70 else ("Deeply Oversold / Accumulate" if rsi < 30 else "Neutral Baseline Compression")
        },
        {
            "Parameter Vector": "🌊 Volatility (ATR Ratio)",
            "Calculated Metric": f"ATR Compression @ {volatility_ratio:.2f}%",
            "Impact Weight": round(volatility_ratio * 10, 2),
            "Strategic Allocation Vector": "Prepare for imminent breakout expansion" if volatility_ratio < 1.5 else "Volatile swings active; widen stops"
        },
        {
            "Parameter Vector": "🎯 Mean Reversion Deviation",
            "Calculated Metric": f"BB Stretch: {bb_position:.1f}%",
            "Impact Weight": round(abs(bb_position), 2),
            "Strategic Allocation Vector": "Targeting mean reversal down to average" if bb_position > 80 else ("Expecting bounce back to midband" if bb_position < -80 else "Trading inside fair price band")
        }
    ]

    # Sort the parameters dynamically based on which indicator shows the highest mathematical urgency
    audit_df = pd.DataFrame(parameters)
    return audit_df.sort_values(by="Impact Weight", ascending=False)

# ══════════════════════════════════════════════════════════════════════════════
#  DATA RETRIEVAL SUBSYSTEM
# ══════════════════════════════════════════════════════════════════════════════
# ══════════════════════════════════════════════════════════════════════════════
#  DATA RETRIEVAL SUBSYSTEM
# ══════════════════════════════════════════════════════════════════════════════
BASE_ASSETS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "SPY", "QQQ", "GLD", "BTC-USD", "ETH-USD", "SOL-USD"]
ALL_ACTIVE_ASSETS = list(dict.fromkeys(BASE_ASSETS + st.session_state.custom_pool))

def clean_symbol(sym):
    return sym.replace("-USD", "")

@st.cache_data(ttl=5, show_spinner=False)
def fetch_ticker_data(ticker, period="1mo", interval="1d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
        if df.empty:
            return pd.DataFrame()
            
        # Ensure we flatten the multi-index properly
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] for c in df.columns]
            
        # Final safety check before returning
        if "Close" not in df.columns:
            return pd.DataFrame()
            
        return df.dropna()
    except Exception:
        return pd.DataFrame()
# ══════════════════════════════════════════════════════════════════════════════
#  UI STRUCTURE & HEADERS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class='p9-header'>
    <div class='p9-title'>PLANET9WORLD QUANTUM NETWORK</div>
    <div class='p9-subtitle'>NATIVE EMBEDDED AUTOMATION UNIT // ZERO-API DEPENDENCY PIPELINE</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR MANAGEMENT (UNIVERSAL REGISTRY DISCOVERY)
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🌌 UNIVERSAL DISCOVERY CORE")
    st.markdown("<small>Inject any global asset identifier directly into active data processing arrays without configuration adjustments.</small>", unsafe_allow_html=True)
    
    discovered_ticker = st.text_input("Global Market Symbol", placeholder="e.g., RELIANCE.NS, COIN, ETH-USD").upper().strip()
    if st.button("Inject into Core Registry", use_container_width=True):
        if discovered_ticker and discovered_ticker not in ALL_ACTIVE_ASSETS:
            st.session_state.custom_pool.append(discovered_ticker)
            st.success(f"Asset '{discovered_ticker}' linked to matrix registry.")
            time.sleep(0.5)
            st.rerun()

    st.markdown("---")
    st.caption("PLANET9WORLD Automated Architecture v8.5")

# ══════════════════════════════════════════════════════════════════════════════
#  CONTROL GRID INTERFACE
# ══════════════════════════════════════════════════════════════════════════════
c1, c2 = st.columns([7, 3])
with c1:
    clean_options = [clean_symbol(s) for s in ALL_ACTIVE_ASSETS]
    try:
        def_idx = clean_options.index(clean_symbol(st.session_state.active_radar_ticker))
    except ValueError:
        def_idx = 0
    selected_asset_label = st.selectbox("🎯 RADAR TARGET ALIGNMENT FOCUS", clean_options, index=def_idx)
    if selected_asset_label:
        for original in ALL_ACTIVE_ASSETS:
            if clean_symbol(original) == selected_asset_label:
                st.session_state.active_radar_ticker = original
                break

with c2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("⚡ ENGAGE MATRIX DATA REFRESH", use_container_width=True):
        rows = []
        for t in ALL_ACTIVE_ASSETS:
            df = fetch_ticker_data(t, "5d", "15m")
            # ADDED DEFENSIVE CHECK HERE: "Close" in df.columns
            if not df.empty and len(df) >= 2 and "Close" in df.columns:
                last_p = float(df["Close"].iloc[-1])
                prev_p = float(df["Close"].iloc[-2])
                pct = ((last_p - prev_p) / prev_p) * 100
                score = min(100, max(0, int(50 + pct * 5)))
                rows.append({
                    "Asset": clean_symbol(t),
                    "Price": last_p,
                    "APS Score": score,
                    "Direction": "BULLISH" if pct >= 0 else "BEARISH"
                })
        st.session_state.master_matrix = pd.DataFrame(rows)

# ══════════════════════════════════════════════════════════════════════════════
#  ISOLATED PRODUCTION STREAM RUNTIME FRAGMENT (ONLY THIS REFRESHES)
# ══════════════════════════════════════════════════════════════════════════════
@st.fragment(ttl=3)
def render_isolated_telemetry_corridor():
    focus_ticker = st.session_state.active_radar_ticker
    df_chart = fetch_ticker_data(focus_ticker, "5d", "5m")
    
    current_price = 0.0
    change_pct = 0.0
    style_class = "val-up"
    
    # ADDED DEFENSIVE CHECK HERE: "Close" in df_chart.columns
    if not df_chart.empty and len(df_chart) >= 2 and "Close" in df_chart.columns:
        current_price = float(df_chart["Close"].iloc[-1])
        prev_price = float(df_chart["Close"].iloc[-2])
        change_pct = ((current_price - prev_price) / prev_price) * 100
        if change_pct < 0:
            style_class = "val-down"

    # Display isolated live scoreboard metrics
    st.markdown(f"""
    <div class='matrix-container'>
        <div style='display:flex; justify-content:space-between; align-items:center;'>
            <div>
                <div style='font-size:10px; color:#94a3b8; letter-spacing:1px;'>MONITORED REGISTRY VECTOR</div>
                <div style='font-size:22px; font-weight:900; color:#ffffff;'>{clean_symbol(focus_ticker)}</div>
            </div>
            <div style='text-align:right;'>
                <div style='font-size:10px; color:#94a3b8; letter-spacing:1px;'>REALTIME SPOT FEED VALUE</div>
                <div class='price-metric {style_class}'>${current_price:,.2f}</div>
                <div style='font-size:13px; font-weight:700;' class='{style_class}'>{change_pct:+.3f}%</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Secondary layout splits inside the stable runtime block
    z_left, z_right = st.columns([4, 6])
    
    with z_left:
        st.markdown("#### 📊 Dynamic Market Matrices")
        mm = st.session_state.master_matrix
        if mm.empty:
            st.caption("Engage Matrix Data Refresh to compute market pipelines.")
        else:
            bulls = mm[mm["Direction"] == "BULLISH"].sort_values("APS Score", ascending=False)
            bears = mm[mm["Direction"] == "BEARISH"].sort_values("APS Score", ascending=True)
            
            st.markdown("<b style='color:#00ff88;'>📈 Bullish Configurations</b>", unsafe_allow_html=True)
            st.dataframe(bulls[["Asset", "Price", "APS Score"]], use_container_width=True, hide_index=True)
            
            st.markdown("<b style='color:#ff2255;'>📉 Bearish Channels</b>", unsafe_allow_html=True)
            st.dataframe(bears[["Asset", "Price", "APS Score"]], use_container_width=True, hide_index=True)

    with z_right:
        st.markdown("#### ⚡ Timeline Corridor & Embedded AI Decision Matrix")
        
        # 1. Plotly interactive timeline tracking chart
        if not df_chart.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df_chart.index, open=df_chart["Open"], high=df_chart["High"],
                low=df_chart["Low"], close=df_chart["Close"], name="Candle Tick",
                increasing_line_color="#00ff88", decreasing_line_color="#ff2255"
            ))
            fig.update_layout(
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#04060b",
                margin=dict(l=0, r=0, t=5, b=0), height=220, xaxis_rangeslider_visible=False,
                hovermode="x unified",
                xaxis=dict(gridcolor="#1e293b", type="date", tickformat="%Y-%m-%d\n%H:%M:%S"),
                yaxis=dict(gridcolor="#1e293b", side="right")
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.caption("Awaiting timeline streaming array initialization.")
            
        # 2. Render sorted lightweight expert "AI" audit table instantly
        st.markdown("<br><b style='color:#00f0ff;'>🤖 Sorted Internal AI Urgency Analysis</b>", unsafe_allow_html=True)
        native_ai_table = run_native_ai_audit(df_chart)
        st.dataframe(native_ai_table[["Parameter Vector", "Calculated Metric", "Strategic Allocation Vector"]], use_container_width=True, hide_index=True)

# Execute stable UI rendering logic block
render_isolated_telemetry_corridor()
