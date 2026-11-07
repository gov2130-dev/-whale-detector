import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import urllib.parse

st.set_page_config(page_title="راصد الحيتان", layout="centered")
st.title("📊 راصد الحيتان")
st.caption("✅ نفس شروط البوت المرجعي - عقود 2 إلى 3 - أفضل 5 فقط")

MIN_PREMIUM = 100000
MIN_VOL = 300
MIN_PRICE = 2.0
MAX_PRICE = 3.0
MIN_RATIO = 1.2
MAX_DAYS = 14
MAX_DISTANCE = 0.15
TOP_N = 5  # جديد: نرسل أفضل 5 فقط مثل البوت المرجعي

def get_targets(entry):
    return [round(entry*1.25,2), round(entry*1.35,2), round(entry*1.50,2), round(entry*1.65,2),
            round(entry*1.75,2), round(entry*1.85,2), round(entry*1.90,2), round(entry*2.00,2)]

def format_message(symbol, company, opt_type, strike, exp, entry, stop, vol):
    targets = get_targets(entry)
    type_txt = "🔴 شراء مرجح PUT" if opt_type == "PUT" else "🟢 شراء مرجح CALL"
    exp_fmt = datetime.strptime(exp, "%Y-%m-%d").strftime("%b %d %Y").upper()
    time_now = datetime.now().strftime("%H:%M:%S")
    total_cost = int(entry * 100)
    msg = f"""🔍 راصد الحيتان
{symbol} - {company}
{type_txt} {strike}
الانتهاء: {exp_fmt} 📅
سعر التنفيذ: {entry} ({total_cost} دولار للعقد) 💰
الوقف: {stop} 🔴 | الكمية: {int(vol)} عقد 📦
الأهداف بالترتيب 🎯
{targets[0]} | {targets[1]} | {targets[2]} | {targets[3]}
{targets[4]} | {targets[5]} | {targets[6]} | {targets[7]}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
وقت التنفيذ: {time_now} SA 🕐
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""
    return msg

if "results" not in st.session_state:
    st.session_state.results = []
if "seen" not in st.session_state:
    st.session_state.seen = set()

if st.button("🔍 افحص الآن", use_container_width=True):
    st.session_state.results = []
    st.session_state.seen = set()
    all_candidates = []
    tickers = ["BABA","AMZN","MSFT","NVDA","TSLA","META","GOOGL","AMD","NFLX","GDX","SPY","QQQ","COIN","PLTR","AAPL","CRM","ORCL","AVGO","JPM","MU","NOW","SMCI","OKLO","APP","HOOD","MSTR","LLY","UNH","XOM","CVX"]
    with st.spinner("جاري الفحص..."):
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company = info.get('shortName', symbol)
                stock_price = info.get('currentPrice') or info.get('regularMarketPrice')
                if not stock_price:
                    try:
                        hist = ticker.history(period="1d")
                        if not hist.empty:
                            stock_price = float(hist['Close'].iloc[-1])
                    except:
                        pass
                if not stock_price:
                    continue
                best = None
                best_score = 0
                best_premium = 0
                for exp in ticker.options[:4]:
                    days = (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    if days < 0 or days > MAX_DAYS:
                        continue
                    chain = ticker.option_chain(exp)
                    for opt_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                        for _, row in df.iterrows():
                            vol = row['volume'] if pd.notna(row['volume']) else 0
                            oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
                            price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
                            strike = row['strike']
                            if vol < MIN_VOL or oi == 0:
                                continue
                            if price < MIN_PRICE or price > MAX_PRICE:
                                continue
                            premium = vol * price * 100
                            if premium < MIN_PREMIUM:
                                continue
                            distance = abs(strike - stock_price) / stock_price
                            if distance > MAX_DISTANCE:
                                continue
                            score = premium * (1 - distance * 0.5)
                            key = f"{symbol}-{opt_type}-{strike}-{exp}"
                            if key in st.session_state.seen:
                                continue
                            if vol/oi >= MIN_RATIO and score > best_score:
                                best_score = score
                                best_premium = premium
                                best = (opt_type, row, exp, price, vol, key)
                if best:
                    opt_type, row, exp, price, vol, key = best
                    st.session_state.seen.add(key)
                    entry = round(float(price), 2)
                    stop = round(entry * 0.67, 2)
                    msg = format_message(symbol, company, opt_type, row['strike'], exp, entry, stop, vol)
                    all_candidates.append((best_premium, symbol, msg))
            except:
                continue
        # ===== هنا الترتيب: أفضل 5 فقط =====
        all_candidates.sort(key=lambda x: x[0], reverse=True)
        st.session_state.results = [(s, m) for _, s, m in all_candidates[:TOP_N]]
    st.success(f"✅ لقيت {len(st.session_state.results)} سهم - أفضل 5")

if st.session_state.results:
    st.divider()
    st.markdown("### 📦 ارسل الكل مع بعض")
    all_msg = "\n\n━━━━━━━━━━━━━━\n\n".join([m for _, m in st.session_state.results])
    wa_all = f"https://wa.me/?text={urllib.parse.quote(all_msg)}"
    st.link_button(f"📲 ارسل الكل ({len(st.session_state.results)} توصية) - اختر من الواتس", wa_all, use_container_width=True)
    st.divider()
    st.markdown("### 📄 ارسل كل توصية لوحدها")
    for symbol, msg in st.session_state.results:
        st.markdown(f"""
        <div dir="rtl" style="background-color:white; padding:18px; border-radius:18px; box-shadow:0 2px 10px rgba(0,0,0,0.1); margin-bottom:10px; text-align:right; font-size:17px; line-height:1.8; color:black; white-space:pre-line;">
        {msg}
        </div>
        """, unsafe_allow_html=True)
        wa_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
        st.link_button(f"📲 ارسل {symbol} - اختر من الواتس", wa_link, use_container_width=True)
        st.divider()
