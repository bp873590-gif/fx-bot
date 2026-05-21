import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from streamlit_lightweight_charts import renderLightweightCharts

# --- 1. PREMIUM VIP DARK THEME & LAYOUT CONFIG ---
st.set_page_config(page_title="SMC Institutional Terminal", layout="centered")

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

# --- 2. CRASH-PROOF TELEGRAM CONNECTOR ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    token_str = str(BOT_TOKEN).strip()
    chat_str = str(CHAT_ID).strip()
    url = f"https://api.telegram.org/bot{token_str}/sendMessage"
    payload = {"chat_id": chat_str, "text": str(message)}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

# --- 3. ALL FOREX PAIRS + GBPJPY + GOLD ---
pair_mapping = {
    "👑 GOLD (XAUUSD)": "GC=F",
    "🇬🇧🇯🇵 GBPJPY (The Beast)": "GBPJPY=X",
    "🇪🇺 EURUSD": "EURUSD=X",
    "🇬🇧 GBPUSD": "GBPUSD=X",
    "🇯🇵 USDJPY": "USDJPY=X",
    "🇦🇺 AUDUSD": "AUDUSD=X",
    "🇨🇦 USDCAD": "USDCAD=X",
    "🇳🇿 NZDUSD": "NZDUSD=X",
    "🇨🇭 USDCHF": "USDCHF=X",
    "🪙 BITCOIN": "BTC-USD"
}

col1, col2 = st.columns(2)
with col1:
    selected_pair_label = st.selectbox("🎯 Select Asset / Pair:", list(pair_mapping.keys()))
    pair_input = pair_mapping[selected_pair_label]
with col2:
    timeframe = st.selectbox("⏱️ Timeframe:", ["1h", "4h", "1d"], index=0)

# Fetch Data
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 20:
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    # Format data for TradingView Lightweight Chart
    df = df.reset_index()
    df['time'] = df['Date'].dt.strftime('%Y-%m-%d %H:%M:%S' if timeframe != "1d" else '%Y-%m-%d')
    
    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            'time': row['time'],
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close'])
        })
        
    current_price = float(df['Close'].iloc[-1])
    highs = df['High'].values
    lows = df['Low'].values

    # --- 4. CORE SMC LOGIC ---
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]:
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]:
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # --- 5. 🔥 TRADINGVIEW OFFICIAL ENGINE CONFIG 🔥 ---
    chartOptions = {
        "layout": {
            "background": {"type": "solid", "color": "#0c0d14"},
            "textColor": "#d1d4dc",
        },
        "grid": {
            "vertLines": {"color": "#1f2231"},
            "horzLines": {"color": "#1f2231"},
        },
        "rightPriceScale": {
            "borderColor": "#1f2231",
            "scaleMargins": {"top": 0.1, "bottom": 0.1},
        },
        "timeScale": {
            "borderColor": "#1f2231",
            "timeVisible": True,
            "secondsVisible": False,
        },
        "crosshair": {
            "mode": 0
        }
    }

    seriesCandlestickChart = [{
        "type": "Candlestick",
        "data": chart_data,
        "options": {
            "upColor": "#00ffb3",
            "downColor": "#ff3366",
            "borderUpColor": "#00ffb3",
            "borderDownColor": "#ff3366",
            "wickUpColor": "#00ffb3",
            "wickDownColor": "#ff3366",
        }
    }]

    # Rendering the real deal chart (Inbuilt Smooth Pinch Zoom & Drag)
    renderLightweightCharts([{"options": chartOptions, "series": seriesCandlestickChart}], 'main')

    # --- 6. 📢 AUTOMATED READY-TO-TRADE ENTRY SIGNAL LOGIC ---
    clean_name = selected_pair_label.split()[-1] 
    st.markdown(f"### 🛡️ Live Action Plan: {clean_name}")
    st.write(f"**Current Price:** {current_price:.5f} | **OB Level:** {ob_price:.5f} | **FVG Range:** {last_fvg_bottom:.5f} - {last_fvg_top:.5f}")
    
    current_alert_key = f"alert_trigger_{clean_name}_{timeframe}"
    
    # A. PRO BUY ENTRY TRIGGER
    if current_price > recent_high and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        msg = f"🔥 SMC LIVE TRADE TRIGGER (BUY) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: BUY NOW\n🎯 Entry Price: {current_price:.5f}\n🛡️ Zone: Price has retested the Institutional Zone! Place your orders."
        st.success(f"🟢 **LIVE ENTRY ACTIVE:** {msg}")
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "BUY_TRIGGER":
            st.session_state[current_alert_key] = "BUY_TRIGGER"
            send_telegram_alert(msg)
            
    # B. PRO SHORT ENTRY TRIGGER
    elif current_price < recent_low and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        msg = f"🔥 SMC LIVE TRADE TRIGGER (SHORT/SELL) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: SELL NOW\n🎯 Entry Price: {current_price:.5f}\n🛡️ Zone: Price retesting the supply zone. Institutional selling active!"
        st.error(f"🔴 **LIVE ENTRY ACTIVE:** {msg}")
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "SHORT_TRIGGER":
            st.session_state[current_alert_key] = "SHORT_TRIGGER"
            send_telegram_alert(msg)
            
    # C. ADVANCE WATCHLIST
    elif current_price > recent_high and last_fvg_top > 0 and current_price > last_fvg_top:
        st.info(f"👀 **Watchlist:** {clean_name} ne breakout kiya hai. Price ko neeche **{last_fvg_top:.5f}** ke zone me aane do. Jab touch karega tab bot instant automatic signal bhejega!")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    elif current_price < recent_low and last_fvg_top > 0 and current_price < last_fvg_bottom:
        st.info(f"👀 **Watchlist:** Mandi ka breakout ho chuka hai. Price ke wapas upar **{last_fvg_bottom:.5f}** zone me retest karne ka wait karo, tabhi perfect entry alert aayega.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market ranges ke andar hai, koi institutional activity nahi hai.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]

else:
    st.error("Data fetch issue. Please refresh or choose another pair.")