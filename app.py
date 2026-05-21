import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import mpld3
import streamlit.components.v1 as components
import requests

# --- 1. PREMIUM VIP DARK THEME DESIGN ---
st.set_page_config(page_title="SMC Institutional Terminal", layout="centered")

st.markdown("""
    <style>
    .main { background-color: #0c0d14; }
    div.block-container { padding-top: 1.5rem; padding-bottom: 0rem; }
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    h1, h2, h3, p, span { color: #d1d4dc !important; }
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
    
    # Auto detect date/datetime index to avoid KeyErrors
    df = df.reset_index()
    time_col = 'Date' if 'Date' in df.columns else 'Datetime'
    
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    opens = df['Open'].values
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

    # --- 5. 🔥 NEW INTERACTIVE MOBILE-FRIENDLY SMOOTH CHART ENGINE 🔥 ---
    # Matplotlib with Dark Aesthetic for ultra-stable mobile pinch zoom
    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor='#0c0d14')
    ax.set_facecolor('#0c0d14')
    
    # Custom Candlestick Drawing for extreme performance
    for i in range(len(df)):
        color = '#00ffb3' if closes[i] >= opens[i] else '#ff3366'
        ax.plot([i, i], [lows[i], highs[i]], color=color, linewidth=1)
        ax.bar(i, closes[i] - opens[i], bottom=opens[i], color=color, width=0.6)
        
    # Plotting Levels cleanly
    if ob_price > 0:
        ax.axhline(y=ob_price, color='#ffcc00', linestyle='-', linewidth=1.2, label='OB ZONE')
    ax.axhline(y=recent_high, color='#00bcff', linestyle=':', linewidth=1, label='BOS HIGH')
    ax.axhline(y=recent_low, color='#ff5500', linestyle=':', linewidth=1, label='BOS LOW')
    ax.axhline(y=current_price, color='#ff3366', linestyle='--', linewidth=1.5, label=f'LIVE: {current_price:.4f}')

    # Styling Axes
    ax.tick_params(colors='#d1d4dc', labelsize=9)
    ax.grid(color='#1f2231', linestyle='-', linewidth=0.5)
    ax.yaxis.tick_right() # TradingView Style Right Side Axis
    for spine in ax.spines.values():
        spine.set_color('#1f2231')

    # Convert to HTML for perfect responsive touch zoom & pan controls
    html_chart = mpld3.fig_to_html(fig)
    plt.close(fig)
    components.html(html_chart, height=460)

    # --- 6. 📢 AUTOMATED READY-TO-TRADE ENTRY + SL / TP LOGIC ---
    clean_name = selected_pair_label.split()[-1]
    st.markdown(f"### 🛡️ Live Execution Plan: {clean_name}")
    
    current_alert_key = f"alert_trigger_{clean_name}_{timeframe}"
    
    # SL/TP Pip Buffer Calculation based on asset type
    is_gold_or_btc = "GOLD" in selected_pair_label or "BITCOIN" in selected_pair_label
    buffer = 1.50 if is_gold_or_btc else 0.00150 # Gold me points aur Forex me pips
    tp_multiplier = 3 # 1:3 Risk Reward Ratio 🔥
    
    # A. PRO BUY ENTRY TRIGGER WITH SL & TP
    if current_price > recent_high and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price - (buffer * 0.5) if ob_price > 0 else current_price - buffer
        risk = current_price - sl_level
        tp_level = current_price + (risk * tp_multiplier)
        
        msg = f"🔥 SMC LIVE TRADE TRIGGER (BUY) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: BUY NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🛡️ RR Ratio: 1:3 Institutional Target!"
        
        st.success(f"🟢 **LIVE TRADE ACTIVE:**\n\n* **Action:** BUY NOW\n* **Entry Price:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "BUY_TRIGGER":
            st.session_state[current_alert_key] = "BUY_TRIGGER"
            send_telegram_alert(msg)
            
    # B. PRO SHORT ENTRY TRIGGER WITH SL & TP
    elif current_price < recent_low and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price + (buffer * 0.5) if ob_price > 0 else current_price + buffer
        risk = sl_level - current_price
        tp_level = current_price - (risk * tp_multiplier)
        
        msg = f"🔥 SMC LIVE TRADE TRIGGER (SHORT/SELL) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: SELL NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}\n🛡️ RR Ratio: 1:3 Institutional Target!"
        
        st.error(f"🔴 **LIVE TRADE ACTIVE:**\n\n* **Action:** SELL NOW\n* **Entry Price:** {current_price:.5f}\n* **Stop Loss (SL):** {sl_level:.5f}\n* **Take Profit (TP):** {tp_level:.5f}")
        
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "SHORT_TRIGGER":
            st.session_state[current_alert_key] = "SHORT_TRIGGER"
            send_telegram_alert(msg)
            
    # C. ADVANCE WATCHLIST (Breakout happened but waiting for pullback)
    elif current_price > recent_high and last_fvg_top > 0 and current_price > last_fvg_top:
        st.info(f"👀 **Watchlist:** {clean_name} ne bullish breakout kiya hai. Price ko pullback lekar neeche **{last_fvg_top:.5f}** ke institutional zone me aane do. Jab touch karega tab bot exact SL aur TP ke sath instant trigger bhejega!")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    elif current_price < recent_low and last_fvg_top > 0 and current_price < last_fvg_bottom:
        st.info(f"👀 **Watchlist:** Bearish breakdown ho chuka hai. Price ke wapas upar **{last_fvg_bottom:.5f}** supply zone me retest karne ka wait karo, tabhi high-probability SL/TP entry alert aayega.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market ranges ke andar consolidation me chal raha hai. Kisi heavy volume breakout ka wait karein.")
        if current_alert_key in st.session_state:
            del os.session_state[current_alert_key]

else:
    st.error("Market data access issue. Please check network or refresh the page.")