import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import requests

# --- APP CONFIG ---
st.set_page_config(page_title="Mera SMC Trading App", layout="centered")

st.title("📊 My Smart Money Charting App")
st.write("Ab poora din live chart dekho mobile par, automatic SMC markings ke sath.")

# --- TELEGRAM SETTINGS ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA}/sendMessage"
    payload = {"chat_id": 905358263, "text": message}
    try: requests.post(url, json=payload)
    except: pass

# --- USER SELECTION ---
pair_input = st.selectbox("Forex Pair Ya Gold Chuno:", ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "XAUUSD=X"])
timeframe = st.selectbox("Timeframe Chuno:", ["1h", "4h", "1d"], index=0)

# --- DATA DOWNLOAD ---
df = yf.download(pair_input, period="1mo", interval=timeframe)

if not df.empty and len(df) > 15:
    # Columns name fix karna
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    
    last_closed = df.iloc[-2]
    older_2 = df.iloc[-4]
    current_close = float(last_closed['Close'])
    
    # --- SMC CALCULATION ---
    recent_high = float(df['High'].iloc[-12:-2].max())
    recent_low = float(df['Low'].iloc[-12:-2].min())
    
    is_bullish_BOS = current_close > recent_high
    is_bearish_BOS = current_close < recent_low
    bullish_FVG = float(last_closed['Low']) > float(older_2['High'])
    bearish_FVG = float(last_closed['High']) < float(older_2['Low'])

    # --- 📈 CANDLESTICK CHART MAKING ---
    fig = go.Figure(data=[go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name="Market Candles"
    )])

    # --- AUTOMATIC MARKINGS ON CHART ---
    # Recent High (Resistance) ki line draw karna
    fig.add_hline(y=recent_high, line_dash="dash", line_color="green", annotation_text="SMC High / BOS Level")
    # Recent Low (Support) ki line draw karna
    fig.add_hline(y=recent_low, line_dash="dash", line_color="red", annotation_text="SMC Low / BOS Level")

    # Mobile friendly settings for chart
    fig.update_layout(
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=450
    )
    
    # Display the Chart on Mobile
    st.plotly_chart(fig, use_container_width=True)

    # --- SIGNAL STATUS BOX BELOW CHART ---
    clean_name = pair_input.replace("=X", "")
    st.subheader("📢 Signal Status:")
    
    if is_bullish_BOS and bullish_FVG:
        st.success(f"🚀 PRO BUY ZONE ACTIVE on {clean_name}! (BOS + FVG)")
    elif is_bearish_BOS and bearish_FVG:
        st.error(f"🚨 PRO SHORT ZONE ACTIVE on {clean_name}! (BOS + FVG)")
    else:
        st.warning("💤 No clear institutional setup right now. Range bound market.")

else:
    st.error("Market data load nahi ho pa raha hai.")