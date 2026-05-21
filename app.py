import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- PREMIUM NOTIFICATION & UI CLEANUP ---
st.set_page_config(page_title="SMC Institutional Terminal", layout="centered")

# CSS se faltu borders aur Streamlit ka branding saaf karna (Clean UI)
st.markdown("""
    <style>
    .main { background-color: #0c0d14; }
    div.block-container { padding-top: 2rem; padding-bottom: 0rem; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 SMC PRO TERMINAL")
st.write("---")

# --- TELEGRAM DETAILS ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA}/sendMessage"
    payload = {"chat_id": 905358263, "text": message}
    try: requests.post(url, json=payload)
    except: pass

# --- CLEAN DROP-DOWNS ---
col1, col2 = st.columns(2)
with col1:
    pair_input = st.selectbox("🎯 Asset:", ["XAUUSD=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "BTC-USD"])
with col2:
    timeframe = st.selectbox("⏱️ Timeframe:", ["1h", "4h", "1d"], index=0)

# Fetch Data
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 20:
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    opens = df['Open'].values
    
    # LIVE CURRENT PRICE DETECTOR
    current_price = float(closes[-1]) 
    
    # Base Chart Creation
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=opens, high=highs, low=lows, close=closes,
        name="Price", 
        increasing_line_color='#00ffb3', decreasing_line_color='#ff3366',
        increasing_fillcolor='#00ffb3', decreasing_fillcolor='#ff3366'
    )])

    # --- AUTOMATIC SMC CALCULATION ---
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    # Last FVG & OB detection logic
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]: # Bullish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]: # Bearish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # Shading the FVG Box elegantly
    if last_fvg_top > 0:
        fig.add_shape(type="rect",
            x0=df.index[-12], y0=last_fvg_bottom, x1=df.index[-1], y1=last_fvg_top,
            fillcolor="rgba(0, 255, 179, 0.08)", line=dict(width=0), name="FVG"
        )
        
    # Order Block Line (Yellow)
    if ob_price > 0:
        fig.add_hline(y=ob_price, line_dash="solid", line_color="#ffcc00", line_width=1.5,
                      annotation_text="  OB ZONE", annotation_position="top left")

    # Structure Break Lines (BOS/CHoCH) - ERROR FIXED HERE
    fig.add_hline(y=recent_high, line_dash="dot", line_color="#00bcff", line_width=1, annotation_text="  BOS HIGH")
    fig.add_hline(y=recent_low, line_dash="dot", line_color="#ff5500", line_width=1, annotation_text="  BOS LOW")

    # LIVE PRICE LEVEL INDICATOR LINE (CHAMAKTI HUYI RED LINE)
    fig.add_hline(y=current_price, line_dash="dash", line_color="#ff3366", line_width=2,
                  annotation_text=f"  LIVE: {current_price:.5f}", annotation_position="top right",
                  annotation_font=dict(size=12, color="#ff3366"))

    # TRADINGVIEW MOBILE ZOOM & SCROLL GRAPHICS CONFIG
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=60, t=10, b=10),
        height=480,
        paper_bgcolor='#0c0d14',
        plot_bgcolor='#0c0d14',
        dragmode='zoom', # DO UNGLI SE MKT ZOOM KARNE KE LIYE
        yaxis=dict(side="right", gridcolor="#1f2231"), # Price labels right side me bilkul TradingView ki tarah
        xaxis=dict(gridcolor="#1f2231")
    )
    
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,       # Do-finger pinch zoom active
        'displayModeBar': False,  # Clean look
        'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d']
    })

    # --- LIVE ACTION BLUEPRINT BOX ---
    clean_name = pair_input.replace("=X", "")
    st.markdown(f"### 🛡️ Strategy: {clean_name}")
    
    if current_price > recent_high and last_fvg_top > 0:
        msg = f"🚀 **SMC BUY ALERT:** {clean_name} ne structure break kiya hai. Price jab pullback karke FVG ({last_fvg_bottom:.5f}) ya OB ({ob_price:.5f}) zone me aaye, tabhi long karein."
        st.info(msg)
        if 'last_alert' not in st.session_state or st.session_state.last_alert != f"BUY_{clean_name}":
            send_telegram_alert(msg)
            st.session_state.last_alert = f"BUY_{clean_name}"
            
    elif current_price < recent_low and last_fvg_top > 0:
        msg = f"🚨 **SMC SHORT ALERT:** {clean_name} ne mandi ka signal diya hai. Retest zone ({ob_price:.5f}) par short opportunities dekhein."
        st.error(msg)
        if 'last_alert' not in st.session_state or st.session_state.last_alert != f"SHORT_{clean_name}":
            send_telegram_alert(msg)
            st.session_state.last_alert = f"SHORT_{clean_name}"
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market sideway hai. Do-finger se zoom karke liquidity zones track karein.")

else:
    st.error("Data issues, check connection.")