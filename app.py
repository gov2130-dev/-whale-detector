import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import json
import os
import time
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="حيتان أبو راكان V93 FINAL - GOLDEN UNDER $4", layout="wide")

# Secrets - هذا هو التصحيح للخطأ اللي في صورتك
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
BOT_USERNAME = "@v68_golden_555371577_bot"

if not BOT_TOKEN or not CHAT_ID:
    st.error("⚠️ BOT_TOKEN أو CHAT_ID ناقص من Secrets في Streamlit")
    st.stop()

RIYADH_TZ = pytz.timezone("Asia/Riyadh")
NY_TZ = pytz.timezone("America/New_York")

STOCKS_52 = [
    "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOGL", "GOOG", "NFLX", "AMD",
    "MSTR", "COIN", "PLTR", "SMCI", "AVGO", "COST", "PEP", "ADBE", "CRM", "ORCL",
    "QCOM", "INTC", "MU", "AMAT", "LRCX", "KLAC", "PANW", "CRWD", "NOW", "SHOP",
    "SQ", "ROKU", "DKNG", "HOOD", "AFRM", "UPST", "SOFI", "MARA", "RIOT", "ARM",
    "SNOW", "DDOG", "NET", "MDB", "AI", "SMR", "NVO", "LLY", "JPM", "GS", "BA", "CAT"
]
INDICES = ["^GSPC", "^NDX"]
ALL_TICKERS = STOCKS_52 + INDICES
SENT_FILE = "sent_today.json"

def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_sent(data):
    with open(SENT_FILE, "w") as f:
        json.dump(data, f)

def get_today_key():
    return datetime.now(RIYADH_TZ).strftime("%Y-%m-%d")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        return requests.post(url, json=payload, timeout=10).json()
    except Exception as e:
        return {"error": str(e)}

def check_filters(ticker, hist):
    if len(hist) < 6:
        return False, "بيانات ناقصة"
    last_close = hist['Close'].iloc[-1]
    prev_close = hist['Close'].iloc[-2]
    change_pct = (last_close - prev_close) / prev_close * 100
    vol_today = hist['Volume'].iloc[-1]
    vol_avg_5 = hist['Volume'].iloc[-6:-1].mean()
    is_index = ticker in INDICES
    if is_index:
        if abs(change_pct) < 0.35:
            return False, f"تذبذب ضعيف {change_pct:.2f}% < 0.35%"
    else:
        if change_pct > 4.2: return False, f"طار كثير {change_pct:.2f}%"
        if change_pct < -3.5: return False, f"نازل كثير {change_pct:.2f}%"
        if abs(change_pct) < 1.1: return False, f"تذبذب ضعيف {change_pct:.2f}%"
        if vol_today < vol_avg_5: return False, "فوليوم ضعيف"
    return True, f"مقبول {change_pct:.2f}%"

def find_golden_contract(ticker):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps: return None
        valid_contracts = []
        for exp in exps[:3]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d")
                days_to_exp = (exp_date - datetime.now()).days
                if days_to_exp < 1 or days_to_exp > 7: continue
                chain = tk.option_chain(exp)
                calls = chain.calls
                current_price = tk.history(period="1d")['Close'].iloc[-1]
                for _, row in calls.iterrows():
                    price = row['lastPrice']
                    if pd.isna(price): continue
                    if price > 4.0 or price < 0.6: continue
                    bid, ask = row['bid'], row['ask']
                    if pd.isna(bid) or pd.isna(ask) or bid <=0: continue
                    spread_pct = (ask - bid) / ask * 100 if ask>0 else 100
                    if spread_pct > 20: continue
                    vol = row['volume'] if not pd.isna(row['volume']) else 0
                    oi = row['openInterest'] if not pd.isna(row['openInterest']) else 0
                    if vol < 50 and oi < 100: continue
                    valid_contracts.append({
                        "ticker": ticker, "exp": exp, "days": days_to_exp,
                        "strike": row['strike'], "price": price,
                        "bid": bid, "ask": ask, "vol": vol, "oi": oi,
                        "current_stock_price": current_price,
                        "target1": price * 1.5, "target2": price * 2.5
                    })
            except: continue
        if not valid_contracts: return None
        valid_contracts.sort(key=lambda x: (abs(x['current_stock_price']-x['strike']), x['price']))
        return valid_contracts[0]
    except: return None

# واجهة
now_riyadh = datetime.now(RIYADH_TZ)
now_ny = datetime.now(NY_TZ)
st.title("🐋 بوت حيتان أبو راكان - V93 FINAL | GOLDEN UNDER $4")
c1, c2, c3 = st.columns(3)
c1.metric("🕐 وقت الرياض", now_riyadh.strftime("%Y-%m-%d %H:%M:%S"))
c2.metric("🗽 وقت نيويورك", now_ny.strftime("%Y-%m-%d %H:%M:%S"))
c3.metric("🤖 البوت", BOT_USERNAME)
st.divider()

if st.button("🔍 فحص الآن - كشف حيتان تحت $4"):
    sent_data = load_sent()
    today_key = get_today_key()
    if today_key not in sent_data: sent_data[today_key] = []
    progress = st.progress(0)
    results = []
    logs = st.empty()
    for i, ticker in enumerate(ALL_TICKERS):
        progress.progress((i+1)/len(ALL_TICKERS))
        logs.text(f"يفحص {ticker}... {i+1}/{len(ALL_TICKERS)}")
        try:
            hist = yf.Ticker(ticker).history(period="7d")
            passed, _ = check_filters(ticker, hist)
            if not passed: continue
            contract = find_golden_contract(ticker)
            if not contract: continue
            contract_id = f"{contract['ticker']}_{contract['exp']}_{contract['strike']}"
            if contract_id in sent_data[today_key]: continue
            stock_target1 = contract['current_stock_price'] * 1.02
            stock_target2 = contract['current_stock_price'] * 1.05
            msg = f"""🐋 *GOLDEN UNDER $4 - {contract['ticker']}*

💰 *سعر السهم:* ${contract['current_stock_price']:.2f}
📅 *الانتهاء:* {contract['exp']} ({contract['days']} أيام)
🎯 *Strike:* ${contract['strike']}

📜 *العقد:*
السعر الحالي: ${contract['price']:.2f}
Bid/Ask: {contract['bid']:.2f}/{contract['ask']:.2f}
Vol: {contract['vol']} | OI: {contract['oi']}

🎯 *أهداف السهم:*
1️⃣ ${stock_target1:.2f}
2️⃣ ${stock_target2:.2f}

🚀 *أهداف العقد:*
50% 👉 ${contract['target1']:.2f}
150% 👉 ${contract['target2']:.2f}

⏰ وقت الرياض: {now_riyadh.strftime('%H:%M')}
🤖 {BOT_USERNAME}
#V93_FINAL
"""
            send_telegram(msg)
            sent_data[today_key].append(contract_id)
            save_sent(sent_data)
            results.append(contract)
            st.success(f"تم إرسال {contract['ticker']} - ${contract['price']:.2f}")
            time.sleep(1)
        except Exception as e:
            continue
    progress.empty()
    logs.empty()
    if results: st.dataframe(pd.DataFrame(results))
    else: st.info("لم يتم العثور على عقود ذهبية تحت $4 تطابق الفلاتر الآن")
