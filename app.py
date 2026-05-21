import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- APP KI SETTING (Mobile Responsive) ---
st.set_page_config(page_title="Mera SMC Trading App", layout="centered")

st.title("📱 My Smart Money Dashboard")
st.write("Job ke sath sukoon wali trading — BUY aur SHORT dono signals ek sath.")

# --- TELEGRAM SETTINGS ---
BOT_TOKEN = "8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA"
CHAT_ID = "905358263"

def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{8831983662:AAE0r8keSZ5p1Kb1JynIHH_0r_A0e7RqsEA}/sendMessage"
    payload = {"chat_id": 905358263, "text": message}
    try: requests.post(url, json=payload)
    except: pass

# --- PAIRS SELECT KARNE KA OPTION ---
pair_input = st.selectbox(
    "Forex Pair Ya Gold Chuno:",
    ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "XAUUSD=X"]
)

timeframe = st.selectbox("Timeframe Chuno:", ["1h", "4h", "1d"], index=0)

# --- DATA DOWNLOAD AUR LOGIC ---
if st.button("🔴 Live Chart Aur Signal Dekho"):
    with st.spinner("Market se footprints nikal raha hu..."):
        
        # Data fetch karna
        df = yf.download(pair_input, period="1mo", interval=timeframe)
        
        if not df.empty and len(df) > 15:
            last_closed = df.iloc[-2]
            older_2 = df.iloc[-4]
            current_close = float(last_closed['Close'])
            
            # SMC Logic (BOS + FVG)
            recent_high = float(df['High'].iloc[-12:-2].max())
            recent_low = float(df['Low'].iloc[-12:-2].min())
            
            # Buy Conditions
            is_bullish_BOS = current_close > recent_high
            bullish_FVG = float(last_closed['Low']) > float(older_2['High'])
            
            # Short (Sell) Conditions
            is_bearish_BOS = current_close < recent_low
            bearish_FVG = float(last_closed['High']) < float(older_2['Low'])
            
            # --- APP PAR RESULT DIKHANA ---
            st.subheader("📊 Market Ka Haal:")
            st.metric(label="Current Price", value=f"{current_close:.5f}")
            
            st.write("📝 Pichli Candles Ka Data:")
            st.dataframe(df[['Open', 'High', 'Low', 'Close']].tail(5))
            
            clean_name = pair_input.replace("=X", "")
            
            # 1. GREEN SIGNAL (BUY)
            if is_bullish_BOS and bullish_FVG:
                msg = f"🚀 PRO SMC BUY: {clean_name}\n⏱️ TF: {timeframe}\n💰 Price: {current_close:.5f}\n🎯 Target: Lamba Profit (1:3+)"
                st.success(msg)
                send_telegram_alert(msg)
                
            # 2. RED SIGNAL (SHORT / SELL)
            elif is_bearish_BOS and bearish_FVG:
                msg = f"🚨 PRO SMC SHORT (SELL): {clean_name}\n⏱️ TF: {timeframe}\n💰 Price: {current_close:.5f}\n🎯 Target: Lamba Profit (1:3+)"
                st.error(msg)
                send_telegram_alert(msg)
                
            # 3. NO SIGNAL
            else:
                st.warning("💤 Abhi koi pakka trade nahi hai. Chill karo, job par dhyan do!")
        else:
            st.error("Data nahi mil pa raha hai, thodi der baad try karein.")