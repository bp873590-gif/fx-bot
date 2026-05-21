import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- 1. PREMIUM TERMINAL SYSTEM CONFIG ---
st.set_page_config(page_title="SMC Institutional Signal Engine", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0c0d14; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    h1, h2, h3, p, span { color: #d1d4dc !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🦅 SMC PRO SIGNAL ENGINE")
st.write("---")

# --- 2. FIXED CRASH-PROOF TELEGRAM CONNECTOR ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    token_str = str(BOT_TOKEN).strip()
    chat_str = str(CHAT_ID).strip()
    url = f"https://api.telegram.org/bot{token_str}/sendMessage"
    payload = {"chat_id": chat_str, "text": str(message)}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# --- 3. ALL FOREX PAIRS + CORRECT GOLD TICKER ---
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

# Fetch Data from Yahoo Finance
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 20:
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    current_price = float(closes[-1]) 

    # --- 4. CORE SMC LOGIC & ZONE CALCULATIONS ---
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]: # Bullish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]: # Bearish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # --- 5. 📢 AUTOMATED SINGLE-TRIGGER SIGNAL SYSTEM (NO SPAM) ---
    clean_name = selected_pair_label.split()[-1]
    st.markdown(f"### 🛡️ Live Action Plan: {clean_name}")
    st.write(f"**Current Price:** {current_price:.5f}")
    
    # Unique key har pair aur timeframe ke liye alert tracking ke liye
    current_alert_key = f"alert_state_{clean_name}_{timeframe}"
    
    # Initialize history dictionary in session state if not exists
    if "alert_history" not in st.session_state:
        st.session_state.alert_history = {}
    
    # SL/TP Buffer Multipliers
    is_gold_or_btc = "GOLD" in selected_pair_label or "BITCOIN" in selected_pair_label
    buffer = 1.50 if is_gold_or_btc else 0.00150
    tp_multiplier = 3 
    
    # A. PRO BUY ENTRY TRIGGER
    if current_price > recent_high and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price - (buffer * 0.5) if ob_price > 0 else current_price - buffer
        risk = current_price - sl_level
        tp_level = current_price + (risk * tp_multiplier)
        
        st.success(f"🟢 **LIVE ENTRY ACTIVE (BUY):**\n\n* **Entry:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        # 👑 LOGIC: Agar is pair ka BUY signal pehle nahi bheja gaya, tabhi bhejo!
        if st.session_state.alert_history.get(current_alert_key) != "BUY_SENT":
            msg = f"🔥 SMC LIVE TRADE TRIGGER (BUY) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: BUY NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🦅 Target: 1:3 RR"
            send_telegram_alert(msg)
            st.session_state.alert_history[current_alert_key] = "BUY_SENT" # Block further messages
            
    # B. PRO SHORT ENTRY TRIGGER
    elif current_price < recent_low and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price + (buffer * 0.5) if ob_price > 0 else current_price + buffer
        risk = sl_level - current_price
        tp_level = current_price - (risk * tp_multiplier)
        
        st.error(f"🔴 **LIVE ENTRY ACTIVE (SELL):**\n\n* **Entry:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        # 👑 LOGIC: Agar is pair ka SELL signal pehle nahi bheja gaya, tabhi bhejo!
        if st.session_state.alert_history.get(current_alert_key) != "SELL_SENT":
            msg = f"🔥 SMC LIVE TRADE TRIGGER (SHORT) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: SELL NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🦅 Target: 1:3 RR"
            send_telegram_alert(msg)
            st.session_state.alert_history[current_alert_key] = "SELL_SENT" # Block further messages
            
    # C. ADVANCE WATCHLIST & STATE RESET
    elif current_price > recent_high and last_fvg_top > 0 and current_price > last_fvg_top:
        st.info(f"👀 **Watchlist:** {clean_name} ne breakout kiya hai. Zone me wapas aane par signal active hoga.")
        # Price zone se bahar nikal gayi, toh alert state reset karo taaki naye setup par naya alert ja sake
        if current_alert_key in st.session_state.alert_history: 
            del st.session_state.alert_history[current_alert_key]
        
    elif current_price < recent_low and last_fvg_top > 0 and current_price < last_fvg_bottom:
        st.info(f"👀 **Watchlist:** Breakdown ho chuka hai. Pullback ka wait karo.")
        if current_alert_key in st.session_state.alert_history: 
            del st.session_state.alert_history[current_alert_key]
        
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market ranges ke andar chal raha hai.")
        if current_alert_key in st.session_state.alert_history: 
            del st.session_state.alert_history[current_alert_key]

else:
    st.error("Market data access issue or invalid token. Please check back later.")