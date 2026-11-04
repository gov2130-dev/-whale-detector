# الحيتان V7.4 - اصلاح زر مكرر + تثبيت النتائج
# الزرين صار لهم اسم مختلف: فوق وتحت

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="توصيات V7.4", layout="wide")
st.title("توصيات صانع السوق V7.4")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"}

col1, col2 = st.columns(2)
with col1:
    MIN_IV = st.slider("اقل IV %", 15, 60, 20)
with col2:
    TOP_N = st.slider("كم توصية؟", 5, 15, 8)

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return True
    except:
        return False

def build_msg(top):
    msg = "توصيات صانع السوق - " + str(datetime.date.today()) + "\n\n"
    for r in top:
        if r["type"] == "CALL":
            e2 = "🟢"
        else:
            e2 = "🔴"
        if r["is_whale"]:
            w2 = "🐋"
        else:
            w2 = "👀"
        strike2 = int(r["strike"])
        msg = msg + e2 + " " + r["ticker"] + " " + str(strike2) + " " + r["type"] + " " + w2 + "\n"
        msg = msg + "Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Stock: $" + str(r["price"]) + "\n"
        msg = msg + "Entry: $" + str(r["entry"]) + " Bid: $" + str(r["bid"]) + "\n"
        msg = msg + "Stop: $" + str(r["stop"]) + "\n"
        msg = msg + "Target: $" + str(r["t1"]) + " (+50%) | $" + str(r["t2"]) + " (+130%) | $" + str(r["t3"]) + " (+220%)\n\n"
    return msg

def show_send_buttons(top, suffix):
    msg = build_msg(top)
    encoded = urllib.parse.quote(msg)
    wa_link = "https://wa.me/?text=" + encoded
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("ارسل واتساب", wa_link, use_container_width=True, key="wa_" + suffix)
    with c2:
        if st.button("ارسل تلجرام", use_container_width=True, key="tg_" + suffix):
            if send_telegram(msg):
                st.success("انرسل لتلجرام")
            else:
                st.error("ما انرسل - سوي خطوات التلجرام تحت")
    st.caption("واتساب: بيفتح لك الواتساب والتوصيات مكتوبة، اختر الشخص وارسل. تلجرام: يرسل تلقائي بدون ما تختار.")

@st.cache_data(ttl=3600)
def get_universe():
    universe = []
    try:
        sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        for s in sp:
            universe.append(s.replace('.', '-'))
    except:
        pass
    try:
        nd = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[0]['Ticker'].tolist()
        for s in nd:
            universe.append(s)
    except:
        pass
    hot = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","NFLX","AMD","SMCI","ARM","APP","PLTR","HOOD","COIN","MSTR","MARA","RIOT","CLSK","GME","AMC","OPEN","CVNA","SOFI","BABA","PDD","JD","MRNA","RIVN","LCID","NIO","DKNG","RBLX","U","AI","SOUN","UPST","AFRM","CHWY","BYND","SPCE","INTC","MU","QCOM","TXN","ADI","MCHP","ON","SHOP","SQ","PYPL","ABNB","UBER","DASH","ROKU","ZM","DOCU","PTON","TLRY","CGC","NOK","PLUG","FCEL","QS","GPRO","TSM","ASML","CRM","ORCL","BAC","JPM","XOM","CVX","WMT","COST","PEP","KO","PFE","BIIB","NUE","FCX","OXY","USO","GLD","SLV","CLF","X","LLY","V","MA","HD","JNJ","UNH","WFC","CSCO","ACN","MCD","ABT","DHR","GE","CAT","LOW","INTU","DE","AMAT","BKNG","LRCX","KLAC","SNPS","CDNS","MRVL","PANW","CRWD","NET","DDOG","ZS","MDB","SNOW","TEAM","WDAY","EA"]
    for s in hot:
        if s not in universe:
            universe.append(s)
    universe = sorted(universe)
    return universe

def get_best_option(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        if hist.empty:
            return None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
        prev_high = float(hist['High'].iloc[-2])
        prev_low = float(hist['Low'].iloc[-2])
        change = 0
        if prev_close != 0:
            change = (price - prev_close) / prev_close * 100
        avg_vol = float(hist['Volume'].iloc[:-1].mean())
        today_vol = float(hist['Volume'].iloc[-1])
        vol_mult = 0
        if avg_vol > 0:
            vol_mult = today_vol / avg_vol
        vwap = price
        try:
            intra = yf.download(ticker, period="1d", interval="15m", progress=False, auto_adjust=False)
            if not intra.empty:
                if isinstance(intra.columns, pd.MultiIndex):
                    intra.columns = intra.columns.get_level_values(0)
                tp = (intra['High'] + intra['Low'] + intra['Close']) / 3
                total_vol = float(intra['Volume'].sum())
                if total_vol > 0:
                    vwap = float((tp * intra['Volume']).sum() / total_vol)
        except:
            pass
        exps = tk.options
        if not exps:
            return None
        best = None
        best_score = -1
        iv_val = 0
        today = datetime.date.today()
        for exp_str in exps[:3]:
            try:
                exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if days_left < 0 or days_left > 14:
                    continue
                chain = tk.option_chain(exp_str)
                pairs = [(chain.calls, "CALL"), (chain.puts, "PUT")]
                for df, typ in pairs:
                    if len(df) == 0:
                        continue
                    valid_iv = df[df['volume'] > 5]
                    if len(valid_iv) > 0:
                        cur_iv = float(valid_iv['impliedVolatility'].median() * 100)
                        if cur_iv > iv_val:
                            iv_val = cur_iv
                    for idx, row in df.iterrows():
                        vol = int(row['volume'])
                        if vol < 100:
                            continue
                        strike = float(row['strike'])
                        diff = abs(strike - price) / price
                        if diff > 0.05:
                            continue
                        bid = 0
                        ask = 0
                        last = 0
                        try:
                            bid = float(row['bid'])
                        except:
                            bid = 0
                        try:
                            ask = float(row['ask'])
                        except:
                            ask = 0
                        try:
                            last = float(row['lastPrice'])
                        except:
                            last = 0
                        entry = ask
                        if entry <= 0:
                            entry = last
                        if entry <= 0.10 or entry > 10:
                            continue
                        score = vol
                        if diff < 0.02:
                            score = score + 500
                        if price > vwap and typ == "CALL":
                            score = score + 1000
                        if price < vwap and typ == "PUT":
                            score = score + 1000
                        if score > best_score:
                            best_score = score
                            best = {"ticker": ticker, "type": typ, "strike": strike, "exp": exp_str, "days": days_left, "vol": vol, "oi": int(row['openInterest']), "bid": round(bid, 2), "ask": round(ask, 2), "entry": round(entry, 2), "price": round(price, 2), "vwap": round(vwap, 2), "change": round(change, 2), "vol_mult": round(vol_mult, 2), "prev_high": round(prev_high, 2), "prev_low": round(prev_low, 2), "iv": round(iv_val, 1)}
            except:
                continue
        if best is None:
            return None
        entry = best["entry"]
        best["stop"] = round(entry * 0.5, 2)
        best["t1"] = round(entry * 1.5, 2)
        best["t2"] = round(entry * 2.3, 2)
        best["t3"] = round(entry * 3.2, 2)
        score = 0
        if best["iv"] >= MIN_IV:
            score = score + 1
        if best["vol_mult"] >= 1.2:
            score = score + 1
        if best["vol"] > 500:
            score = score + 1
        is_call_up = best["price"] > best["vwap"] and best["type"] == "CALL"
        is_put_down = best["price"] < best["vwap"] and best["type"] == "PUT"
        if is_call_up or is_put_down:
            score = score + 1
        best["score"] = score
        if score >= 3:
            best["is_whale"] = True
        else:
            best["is_whale"] = False
        return best
    except:
        return None

universe = get_universe()
st.write("الكون: " + str(len(universe)) + " سهم | IV فوق " + str(MIN_IV) + "% | بنعرض اقوى " + str(TOP_N) + " توصية")

if st.button("افحص الان - جيب توصيات", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        for i, item in enumerate(ex.map(get_best_option, universe)):
            if item is not None:
                results.append(item)
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text("فحصت " + str(i+1) + " / " + str(len(universe)))
    progress.progress(1.0)
    results = sorted(results, key=lambda x: (x["score"], x["vol"], x["vol_mult"]), reverse=True)
    top = results[:TOP_N]
    status.text("خلص - اقوى " + str(len(top)) + " توصية")
    st.markdown("### ارسال التوصيات")
    show_send_buttons(top, "top")
    for r in top:
        if r["type"] == "CALL":
            emoji_txt = "🟢"
            border = "#22c55e"
        else:
            emoji_txt = "🔴"
            border = "#ef4444"
        if r["is_whale"]:
            whale_txt = "🐋"
            whale_note = "حوت مؤكد - صانع سوق داخل بقوة"
        else:
            whale_txt = "👀"
            whale_note = "اشارة مراقبة - ادخل بنصف كمية"
        strike_int = int(r["strike"])
        st.markdown(
            "<div style='border:2px solid " + border + "; border-radius:16px; padding:16px; margin-bottom:14px; background:#0f172a;'>"
            + "<div style='font-size:22px; font-weight:800; color:white;'>" + emoji_txt + " " + r["ticker"] + " " + str(strike_int) + " " + r["type"] + " " + whale_txt + "</div>"
            + "<div style='color:#cbd5e1; margin-top:6px; font-size:15px;'>Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Stock: $" + str(r["price"]) + " (" + str(r["change"]) + "%) IV: " + str(r["iv"]) + "% Vol: " + str(r["vol_mult"]) + "x</div>"
            + "<div style='color:white; margin-top:10px; font-size:16px;'>Entry: <b>$" + str(r["entry"]) + "</b> Bid: $" + str(r["bid"]) + " Ask: $" + str(r["ask"]) + "</div>"
            + "<div style='color:#fca5a5; margin-top:4px; font-size:15px;'>Stop: <b>$" + str(r["stop"]) + "</b> <span style='color:#94a3b8;'>Vol " + str(r["vol"]) + " | OI " + str(r["oi"]) + " | Score " + str(r["score"]) + "/4</span></div>"
            + "<div style='color:#86efac; margin-top:8px; font-size:16px; font-weight:700;'>Target: $" + str(r["t1"]) + " (+50%) | $" + str(r["t2"]) + " (+130%) | $" + str(r["t3"]) + " (+220%)</div>"
            + "<div style='color:#94a3b8; margin-top:6px; font-size:13px;'>" + whale_note + "</div>"
            + "</div>",
            unsafe_allow_html=True
        )
    st.markdown("### ارسال مرة ثانية")
    show_send_buttons(top, "bottom")
else:
    st.info("اضغط افحص الان عشان تطلع لك بطاقات التوصيات.")
    st.write("واتساب - بدون اي اعداد:")
    st.write("1. افحص")
    st.write("2. اضغط زر ارسل واتساب فوق البطاقات")
    st.write("3. بيفتح الواتساب والتوصيات مكتوبة جاهزة")
    st.write("4. اختر الشخص او القروب وارسل")
    st.write("تلجرام - يحتاج اعداد مرة واحدة:")
    st.write("1. افتح تلجرام وابحث عن BotFather")
    st.write("2. ارسل له newbot وسم البوت اي اسم، بيعطيك توكن طويل")
    st.write("3. افتح بوتك الجديد وارسل له اي رسالة مثل هلا")
    st.write("4. افتح في المتصفح: api.telegram.org/bot - توكنك - /getUpdates")
    st.write("5. دور على chat id - هذا هو CHAT_ID حقك")
    st.write("6. روح Streamlit - Settings - Secrets والصق BOT_TOKEN و CHAT_ID")
    st.write("7. بعدها زر ارسل تلجرام بيرسل تلقائي")

st.caption("اخر تحديث: " + datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M') + " بتوقيت الرياض")
