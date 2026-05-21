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

# --- 2. CRASH-PROOF TELEGRAM CONNECTOR ---
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

# --- 3. ALL FOREX PAIRS + GOLD + BITCOIN ---
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
    # Last 15 candles ka structural high/low nikalna breakout check karne ke liye
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]: # Bullish FVG & OB setup
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]: # Bearish FVG & OB setup
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # --- 5. 📢 AUTOMATED SINGLE-TRIGGER SIGNAL SYSTEM ---
    clean_name = selected_pair_label.split()[-1]
    st.markdown(f"### 🛡️ Live Action Plan: {clean_name}")
    
    # Dashboard pe details print karne ke liye taaki calculation live dikhe
    st.info(f"**Live Price:** {current_price:.5f} | **OB Level:** {ob_price:.5f} | **BOS High:** {recent_high:.5f} | **BOS Low:** {recent_low:.5f}")
    
    current_alert_key = f"alert_state_{clean_name}_{timeframe}"
    
    if "alert_history" not in st.session_state:
        st.session_state.alert_history = {}
    
    # SL/TP Pip Buffer Calculations
    is_gold_or_btc = "GOLD" in selected_pair_label or "BITCOIN" in selected_pair_label
    buffer = 1.50 if is_gold_or_btc else 0.00150
    tp_multiplier = 3 
    
    # --- PRO ENTRY RE-DESIGNED LOGIC ---
    
    # A. BULLISH ENTRY TRIGGER (Price breakout ke baad agar FVG ya OB zone ke upar ya aas-paas retest kare)
    if current_price > recent_high or (ob_price > 0 and abs(current_price - ob_price) / ob_price < 0.005):
        # Stop Loss safe structure (OB line se thoda niche)
        sl_level = ob_price - (buffer * 0.3) if ob_price > 0 else current_price - buffer
        risk = max(current_price - sl_level, buffer)
        tp_level = current_price + (risk * tp_multiplier)
        
        st.success(f"🟢 **LIVE ENTRY ACTIVE (BUY):**\n\n* **Action:** BUY NOW\n* **Entry Price:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        # Anti-Spam Memory: Sirf ek baar message jayega
        if st.session_state.alert_history.get(current_alert_key) != "BUY_SENT":
            msg = f"🔥 SMC LIVE TRADE TRIGGER (BUY) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: BUY NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🦅 Target: 1:3 Risk Reward Ratio"
            send_telegram_alert(msg)
            st.session_state.alert_history[current_alert_key] = "BUY_SENT"
            
    # B. BEARISH ENTRY TRIGGER (Price breakdown ke baad retest kare)
    elif current_price < recent_low or (ob_price > 0 and abs(current_price - ob_price) / ob_price < 0.005):
        # Stop Loss safe structure (OB line se thoda upar)
        sl_level = ob_price + (buffer * 0.3) if ob_price > 0 else current_price + buffer
        risk = max(sl_level - current_price, buffer)
        tp_level = current_price - (risk * tp_multiplier)
        
        st.error(f"🔴 **LIVE ENTRY ACTIVE (SELL):**\n\n* **Action:** SELL NOW\n* **Entry Price:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        # Anti-Spam Memory: Sirf ek baar message jayega
        if st.session_state.alert_history.get(current_alert_key) != "SELL_SENT":
            msg = f"🔥 SMC LIVE TRADE TRIGGER (SHORT) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: SELL NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🦅 Target: 1:3 Risk Reward Ratio"
            send_telegram_alert(msg)
            st.session_state.alert_history[current_alert_key] = "SELL_SENT"

    # C. NO-TRADE CONSOLIDATION ZONE RESET
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market rules ke hisab se structure ke andar range bound hai.")
        # Agar market wapas center range me aa jaye toh memory clear karo taaki naye breakout pe alert de sake
        if current_alert_key in st.session_state.alert_history: 
            del st.session_state.alert_history[current_alert_key]

else:
    st.error("Market data access issue. Please check pair settings or try again.")