import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

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

# --- 2. FIXED CRASH-PROOF TELEGRAM CONNECTOR ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    token_str = str(BOT_TOKEN).strip()
    chat_str = str(CHAT_ID).strip()
    # Fixed URL structure to avoid syntax and value errors
    url = f"https://api.telegram.org/bot{token_str}/sendMessage"
    payload = {"chat_id": chat_str, "text": str(message)}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass

# --- 3. FOREX PAIRS + GOLD ---
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
    
    # Date vs Datetime auto-resolver
    if 'Date' in df.columns:
        df_index_vals = df['Date']
    elif 'Datetime' in df.columns:
        df_index_vals = df['Datetime']
    else:
        df_index_vals = df.index
        
    highs = df['High'].values
    lows = df['Low'].values
    closes = df['Close'].values
    opens = df['Open'].values
    current_price = float(closes[-1]) 
    
    # Base Candlestick Graphics
    fig = go.Figure(data=[go.Candlestick(
        x=df_index_vals, open=opens, high=highs, low=lows, close=closes,
        name="Price Action", 
        increasing_line_color='#00ffb3', decreasing_line_color='#ff3366',
        increasing_fillcolor='#00ffb3', decreasing_fillcolor='#ff3366'
    )])

    # --- 4. CORE SMC LOGIC & ZONE CALCULATIONS ---
    recent_high = float(highs[-15:-2].max())
    recent_low = float(lows[-15:-2].min())
    
    last_fvg_top, last_fvg_bottom, ob_price = 0, 0, 0
    for i in range(15, len(df)-2):
        if highs[i-2] < lows[i]: # Bullish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i], highs[i-2], lows[i-2]
        if lows[i-2] > highs[i]: # Bearish FVG
            last_fvg_top, last_fvg_bottom, ob_price = lows[i-2], highs[i], highs[i-2]

    # Shading the Fair Value Gap Box
    if last_fvg_top > 0:
        fig.add_shape(type="rect",
            x0=df_index_vals[-12], y0=last_fvg_bottom, x1=df_index_vals[-1], y1=last_fvg_top,
            fillcolor="rgba(0, 255, 179, 0.05)", line=dict(width=0), name="FVG"
        )
        
    # Institutional Order Block Line
    if ob_price > 0:
        fig.add_hline(y=ob_price, line_dash="solid", line_color="#ffcc00", line_width=1.5,
                      annotation_text="  OB ZONE", annotation_position="top left")

    # Structure Break Lines (FIXED NameErrors here)
    fig.add_hline(y=recent_high, line_dash="dot", line_color="#00bcff", line_width=1, annotation_text="  BOS HIGH")
    fig.add_hline(y=recent_low, line_dash="dot", line_color="#ff5500", line_width=1, annotation_text="  BOS LOW")

    # LIVE PRICE LEVEL INDICATOR
    fig.add_hline(y=current_price, line_dash="dash", line_color="#ff3366", line_width=2,
                  annotation_text=f"  LIVE: {current_price:.5f}", annotation_position="top right",
                  annotation_font=dict(size=12, color="#ff3366"))

    # --- 5. 🔥 THE PERFECT MOBILE ZOOM SETTING 🔥 ---
    fig.update_layout(
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=70, t=10, b=10),
        height=500,
        paper_bgcolor='#0c0d14',
        plot_bgcolor='#0c0d14',
        dragmode='zoom', # Standard zoom mode to select areas manually
        yaxis=dict(side="right", gridcolor="#1f2231", fixedrange=False), 
        xaxis=dict(gridcolor="#1f2231", fixedrange=False) 
    )
    
    # In-built full zoom UI configs
    st.plotly_chart(fig, use_container_width=True, config={
        'scrollZoom': True,           # Desktop wheel & Mobile pinch zoom ON
        'displayModeBar': True,       # Saare clear zoom out / reset buttons screen par rahenge
        'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'toggleHover'],
        'doubleClick': 'reset'        # Double tap karte hi zoom automatic normal ho jayega!
    })

    # --- 6. 📢 AUTOMATED READY-TO-TRADE ENTRY + SL / TP LOGIC ---
    clean_name = selected_pair_label.split()[-1] 
    st.markdown(f"### 🛡️ Live Execution Plan: {clean_name}")
    
    current_alert_key = f"alert_trigger_{clean_name}_{timeframe}"
    
    # SL/TP Buffer Multipliers
    is_gold_or_btc = "GOLD" in selected_pair_label or "BITCOIN" in selected_pair_label
    buffer = 1.50 if is_gold_or_btc else 0.00150
    tp_multiplier = 3 
    
    # A. PRO BUY ENTRY TRIGGER
    if current_price > recent_high and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price - (buffer * 0.5) if ob_price > 0 else current_price - buffer
        risk = current_price - sl_level
        tp_level = current_price + (risk * tp_multiplier)
        
        msg = f"🔥 SMC LIVE TRADE TRIGGER (BUY) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: BUY NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}"
        st.success(f"🟢 **LIVE TRADE ACTIVE:** BUY NOW\n\n* **Entry:** {current_price:.5f} | **SL:** {sl_level:.5f} | **TP:** {tp_level:.5f}")
        
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "BUY_TRIGGER":
            st.session_state[current_alert_key] = "BUY_TRIGGER"
            send_telegram_alert(msg)
            
    # B. PRO SHORT ENTRY TRIGGER
    elif current_price < recent_low and last_fvg_top > 0 and (last_fvg_bottom <= current_price <= last_fvg_top or abs(current_price - ob_price) / ob_price < 0.001):
        sl_level = ob_price + (buffer * 0.5) if ob_price > 0 else current_price + buffer
        risk = sl_level - current_price
        tp_level = current_price - (risk * tp_multiplier)
        
        msg = f"🔥 SMC LIVE TRADE TRIGGER (SHORT) 🔥\n\n📌 Asset: {clean_name} ({timeframe})\n⚡ Action: SELL NOW\n🎯 Entry: {current_price:.5f}\n🛑 Stop Loss (SL): {sl_level:.5f}\n🎯 Take Profit (TP): {tp_level:.5f}"
        st.error(f"🔴 **LIVE TRADE ACTIVE:** SELL NOW\n\n* **Entry:** {current_price:.5f} | **SL:** {sl_level:.5f} | **TP:** {tp_level:.5f}")
        
        if current_alert_key not in st.session_state or st.session_state[current_alert_key] != "SHORT_TRIGGER":
            st.session_state[current_alert_key] = "SHORT_TRIGGER"
            send_telegram_alert(msg)
            
    # C. WATCHLIST
    elif current_price > recent_high and last_fvg_top > 0 and current_price > last_fvg_top:
        st.info(f"👀 **Watchlist:** {clean_name} ne breakout kiya hai. Price ko neeche **{last_fvg_top:.5f}** ke zone me aane do. Bot exact SL/TP calculate karke automatic message bhejega.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    elif current_price < recent_low and last_fvg_top > 0 and current_price < last_fvg_bottom:
        st.info(f"👀 **Watchlist:** Breakdown ho chuka hai. Price ke upar **{last_fvg_bottom:.5f}** zone me retest karne ka wait karo.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]
        
    else:
        st.warning("💤 **NO-TRADE ZONE:** Market ranges ke andar hai.")
        if current_alert_key in st.session_state: del st.session_state[current_alert_key]

else:
    st.error("Market data access issue. Please reload.")