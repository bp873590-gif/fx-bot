import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- 1. SUPER CLEAN VIP DARK THEME & LAYOUT CONFIG ---
st.set_page_config(page_title="SMC Institutional Terminal", layout="centered")

# Streamlit ki faltu chizen hatane ke liye (Pure Clean UI Feel)
st.markdown("""
    <style>
    .main { background-color: #0c0d14; }
    div.block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 SMC PRO TERMINAL")
st.write("---")

# --- 2. BULLET-PROOF TELEGRAM CONNECTOR ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    # 'bot' prefix aur data type casting ko fix kar diya hai
    url = f"https://api.telegram.org/bot{str(8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA).strip()}/sendMessage"
    payload = {"chat_id": str(905358263).strip(), "text": str(message)}
    try:
        requests.post(url, json=payload, timeout=8)
    except:
        pass  # Agar network issue ho toh app block nahi hogi

# --- 3. DROP-DOWNS FOR ASSETS & TIMEFRAME ---
col1, col2 = st.columns(2)
with col1:
    pair_input = st.selectbox("🎯 Select Asset:", ["XAUUSD=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "BTC-USD"])
with col2:
    timeframe = st.selectbox("⏱️ Timeframe:", ["1h", "4h", "1d"], index=0)

# Fetching Data from Yahoo Finance
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 20:
    # Multi-level columns fix (TypeError solution)
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    opens = df['Open'].values
    
    current_price = float(closes[-1]) 
    
    # Premium Candlestick Color Coding
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=opens, high=highs, low=lows, close=closes,
        name="Price Action", 
        increasing_line_color='#00ffb3', decreasing_line_color='#ff3366',
        increasing_fillcolor='#00ffb3', decreasing_fillcolor='#ff3366'
    )])

    # --- 4. ADVANCED AUTOMATIC SMC ALGORITHM ---
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]: # Bullish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]: # Bearish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # Shading the Fair Value Gap Zone elegantly
    if last_fvg_top > 0:
        fig.add_shape(type="rect",
            x0=df.index[-12], y0=last_fvg_bottom, x1=df.index[-1], y1=last_fvg_top,
            fillcolor="rgba(0, 255, 179, 0.06)", line=dict(width=0), name="FVG"
        )
        
    # Institutional Order Block Line (Yellow)
    if ob_price > 0:
        fig.add_hline(y=ob_price, line_dash="solid", line_color="#ffcc00", line_width=1.5,
                      annotation_text="  OB ZONE", annotation_position="top left")

    # Structure Break Lines (NameError Fixed)
    fig.add_hline(y=recent_high, line_dash="dot", line_color="#00bcff", line_width=1, annotation_text="  BOS HIGH")
    fig.add_hline(y=recent_low, line_dash="dot", line_color="#ff5500", line_width=1, annotation_text="  BOS LOW")

    # LIVE PRICE LEVEL INDICATOR LINE (CHAMAKTI HUYI RED LINE)
    fig.add_hline(y=current_price, line_dash="dash", line_color="#ff3366", line_width=2,
                  annotation_text=f"  LIVE: {current_price:.5f}", annotation_position="top right",
                  annotation_font=dict(size=12, color="#ff3366"))

    # --- 5. PERFECT MOBILE PINCH-ZOOM & TRADINGVIEW LAYOUT ---
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=65, t=10, b=10), # Price padhne ke liye right margin set kiya
        height=480,
        paper_bgcolor='#0c0d14',
        plot_bgcolor='#0c0d14',
        dragmode='zoom', # Do-finger zoom dynamic responsive
        yaxis=dict(side="right", gridcolor="#1f2231"), # TradingView style layout
        xaxis=dict(gridcolor="#1f2231")
    )
    
    # Rendering Chart with Pinch Controls active
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,       # Do-finger stretch zoom enabled
        'displayModeBar': False,  # No unnecessary clutter buttons
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d']
    })

    # --- 6. CRASH-PROOF LIVE EXECUTION STRATEGY & ALERTS ---
    clean_name = str(pair_input).replace("=X", "")
    st.markdown(f"### 🛡️ Execution Blueprint: {clean_name}")
    
    current_alert_key = f"alert_{clean_name}_{timeframe}"
    
    if current_price > recent_high and last_fvg_top > 0:
        msg = f"🚀 SMC BUY ALERT: {clean_name} ({timeframe}) ne structure break kiya hai. Price jab pullback karke FVG ({last_fvg_bottom:.5f}) ya OB ({ob_price:.5f}) zone me aaye, tabhi long positions dekhein."
        st.info(msg)
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "BUY":
            st.session_state[current_alert_key] = "BUY"
            send_telegram_alert(msg)
            
    elif current_price < recent_low and last_fvg_top > 0:
        msg = f"🚨 SMC SHORT ALERT: {clean_name} ({timeframe}) ne market structure toda hai. Retest zone ({ob_price:.5f}) ke aas-pass short entries talashein."
        st.error(msg)
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "SHORT":
            st.session_state[current_alert_key] = "SHORT"
            send_telegram_alert(msg)
    else:
        st.warning("💤 NO-TRADE ZONE: Market consolidation me hai. Levels ke breakout ya retest ka wait karein.")
        if current_alert_key in st.session_state:
            del st.session_state[current_alert_key]

else:
    st.error("Market data access issue, please reload the page.")