import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# VIP Dark Theme Layout Configuration
st.set_page_config(page_title="SMC Pro Dashboard", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    h1 { color: #00ffcc; text-align: center; font-family: 'Helvetica'; }
    .stSelectbox { color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ SMC PRO INSTITUTIONAL DASHBOARD")
st.write("---")

# --- AAPKI TELEGRAM SETTINGS ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA}/sendMessage"
    payload = {"chat_id": 905358263, "text": message}
    try: requests.post(url, json=payload)
    except: pass

# --- USER SELECTION ---
pair_input = st.selectbox("🎯 Target Asset:", ["XAUUSD=X", "EURUSD=X", "GBPUSD=X", "USDJPY=X", "BTC-USD"])
timeframe = st.selectbox("⏱️ Operational Timeframe:", ["1h", "4h", "1d"], index=0)

# Fetching Data
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 20:
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    opens = df['Open'].values
    
    # Interactive Base Chart
    fig = go.Figure(data=[go.Candlestick(
        x=df.index, open=opens, high=highs, low=lows, close=closes,
        name="Price Action", increasing_line_color='#00ffcc', decreasing_line_color='#ff3366'
    )])

    # Scanning for FVG, OB and Structure Breaks
    last_fvg_top = 0
    last_fvg_bottom = 0
    order_block_price = 0

    for i in range(15, len(df)-2):
        # Bullish FVG Detection (Candle i-2 High and Candle i Low)
        if highs[i-2] < lows[i]:
            last_fvg_top = lows[i]
            last_fvg_bottom = highs[i-2]
            order_block_price = lows[i-2] # Last down candle base
            
        # Bearish FVG Detection
        if lows[i-2] > highs[i]:
            last_fvg_top = lows[i-2]
            last_fvg_bottom = highs[i]
            order_block_price = highs[i-2]

    # Plotting FVG Zone (Shaded Area)
    if last_fvg_top > 0:
        fig.add_shape(type="rect",
            x0=df.index[-15], y0=last_fvg_bottom, x1=df.index[-1], y1=last_fvg_top,
            fillcolor="rgba(0, 255, 204, 0.12)", line=dict(color="#00ffcc", width=1),
            name="Fair Value Gap"
        )
        
    # Plotting Order Block / Demand Zone Line
    if order_block_price > 0:
        fig.add_hline(y=order_block_price, line_dash="solid", line_color="#ffcc00", 
                      annotation_text="🎯 ORDER BLOCK (OB)", annotation_position="top left")

    # Current Market Structure Lines (BOS/CHoCH Levels)
    recent_resistance = float(highs[-15:-2].max())
    recent_support = float(lows[-15:-2].min())
    current_price = float(closes[-2])

    fig.add_hline(y=recent_resistance, line_dash="dash", line_color="#00bfff", annotation_text="BOS / CHoCH Upside")
    fig.add_hline(y=recent_support, line_dash="dash", line_color="#ff4500", annotation_text="BOS / CHoCH Downside")

    # 🔥 FIXED ZOOM & SCROLL FOR MOBILE 🔥
    fig.update_layout(
        template="plotly_dark", 
        xaxis_rangeslider_visible=False,
        margin=dict(l=5, r=5, t=10, b=5), 
        height=500,
        paper_bgcolor='#0e1117', 
        plot_bgcolor='#0e1117',
        dragmode='pan' # Touch karne par sirf scroll hoga, galti se zoom nahi hoga!
    )
    
    # Render Chart
    st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True})

    # --- 🎯 PRO TRADING RULES & ALERTS ---
    st.markdown("### 🗺️ Live Execution Strategy:")
    clean_name = pair_input.replace("=X", "")
    
    if current_price > recent_resistance and last_fvg_top > 0:
        msg = f"🚀 **SMC BUY SETUP:** {clean_name}\nMarket ne BOS kiya hai. FVG Zone ({last_fvg_bottom:.5f} - {last_fvg_top:.5f}) ya Order Block ({order_block_price:.5f}) par aate hi BUY entry plan karein."
        st.info(msg)
        # Ek key session me automatic state save karke duplicate message rokna
        if 'last_alert' not in st.session_state or st.session_state.last_alert != f"BUY_{clean_name}":
            send_telegram_alert(msg)
            st.session_state.last_alert = f"BUY_{clean_name}"
            
    elif current_price < recent_support and last_fvg_top > 0:
        msg = f"🚨 **SMC SHORT SETUP:** {clean_name}\nMarket ne structure toda hai. Price ke wapas OB Zone ({order_block_price:.5f}) retest par SHORT entry karein."
        st.error(msg)
        if 'last_alert' not in st.session_state or st.session_state.last_alert != f"SHORT_{clean_name}":
            send_telegram_alert(msg)
            st.session_state.last_alert = f"SHORT_{clean_name}"
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market abhi ranges ke andar chal raha hai. Kisi setup ka wait karein.")

else:
    st.error("Data loading issues, please refresh.")