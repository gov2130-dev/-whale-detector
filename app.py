# الحيتان V8 - مؤشر صانع السوق الحقيقي
# لا نعبي القائمة غصب - اذا ما فيه صانع سوق، نقول ما فيه

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="مؤشر صانع السوق V8", layout="wide")
st.title("مؤشر صانع السوق V8")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")

col1, col2 = st.columns(2)
with col1:
    MIN_SCORE = st.slider("قوة صانع السوق المطلوبة", 5, 8, 6)
with col2:
    TOP_N = st.slider("اقصى عدد توصيات", 3, 10, 5)

if "top" not in st.session_state:
    st.session_state.top = None
if "last_scan" not in st.session_state:
    st.session_state.last_scan = ""
if "scan_msg" not in st.session_state:
    st.session_state.scan_msg = ""

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
    msg = "مؤشر صانع السوق - " + str(datetime.date.today()) + "\n\n"
    for r in top:
        if r["type"] == "CALL":
            e2 = "🟢"
        else:
            e2 = "🔴"
        strike2 = int(r["strike"])
        msg = msg + e2 + " " + r["ticker"] + " " + str(strike2) + " " + r["type"] + " MM:" + str(r["mm_score"]) + "/8\n"
        msg = msg + "Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Stock: $" + str(r["price"]) + "\n"
        msg = msg + "Vol/OI: " + str(r["vol_oi"]) + "x Premium: $" + str(r["premium"]) + "\n"
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

def show_cards(top):
    for r in top:
        if r["type"] == "CALL":
            emoji_txt = "🟢"
            border = "#22c55e"
        else:
            emoji_txt = "🔴"
            border = "#ef4444"
        if r["mm_score"] >= 7:
            mm_txt = "صانع سوق قوي جدا"
            mm_color = "#22c55e"
        else:
            mm_txt = "صانع سوق مؤكد"
            mm_color = "#f59e0b"
        strike_int = int(r["strike"])
        st.markdown(
            "<div style='border:2px solid " + border + "; border-radius:16px; padding:16px; margin-bottom:14px; background:#0f172a;'>"
            + "<div style='font-size:22px; font-weight:800; color:white;'>" + emoji_txt + " " + r["ticker"] + " " + str(strike_int) + " " + r["type"] + " 🐋</div>"
            + "<div style='font-size:15px; font-weight:700; color:" + mm_color + "; margin-top:4px;'>مؤشر صانع السوق: " + str(r["mm_score"]) + "/8 - " + mm_txt + "</div>"
            + "<div style='color:#cbd5e1; margin-top:6px; font-size:14px;'>Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Stock: $" + str(r["price"]) + " (" + str(r["change"]) + "%)</div>"
            + "<div style='color:white; margin-top:8px; font-size:14px;'>Vol/OI: <b>" + str(r["vol_oi"]) + "x</b> | Premium: <b>$" + str(r["premium"]) + "</b> | OI: " + str(r["oi"]) + " | Vol: " + str(r["vol"]) + "</div>"
            + "<div style='color:#94a3b8; margin-top:4px; font-size:13px;'>" + r["mm_reasons"] + "</div>"
            + "<div style='color:white; margin-top:10px; font-size:16px;'>Entry: <b>$" + str(r["entry"]) + "</b> Bid: $" + str(r["bid"]) + " Ask: $" + str(r["ask"]) + "</div>"
            + "<div style='color:#fca5a5; margin-top:4px; font-size:15px;'>Stop: <b>$" + str(r["stop"]) + "</b> | Delta: " + str(r["delta"]) + " | IV: " + str(r["iv"]) + "%</div>"
            + "<div style='color:#86efac; margin-top:8px; font-size:16px; font-weight:700;'>Target: $" + str(r["t1"]) + " (+50%) | $" + str(r["t2"]) + " (+130%) | $" + str(r["t3"]) + " (+220%)</div>"
            + "</div>",
            unsafe_allow_html=True
        )

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

def calc_mm_score(row, price, vwap, exp_days, ticker_iv):
    mm = 0
    reasons = []
    vol = int(row['volume'])
    oi = int(row['openInterest'])
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
    if entry <= 0:
        return None
    vol_oi = 0
    if oi > 0:
        vol_oi = vol / oi
    premium = int(vol * entry * 100)
    strike = float(row['strike'])
    delta = 0
    try:
        delta = abs(float(row['delta']))
    except:
        delta = 0
    iv = 0
    try:
        iv = float(row['impliedVolatility']) * 100
    except:
        iv = ticker_iv
    if vol_oi >= 2.0:
        mm = mm + 2
        reasons.append("فلوس جديدة Vol/OI 2x+")
    elif vol_oi >= 1.0:
        mm = mm + 1
        reasons.append("Vol/OI فوق 1x")
    if premium >= 500000:
        mm = mm + 2
        reasons.append("بريميوم ضخم +500k")
    elif premium >= 100000:
        mm = mm + 1
        reasons.append("بريميوم +100k")
    if oi >= 5000:
        mm = mm + 1
        reasons.append("OI عالي 5000+")
    if vol >= 2000:
        mm = mm + 1
        reasons.append("فوليوم 2000+")
    if delta >= 0.30 and delta <= 0.60:
        mm = mm + 1
        reasons.append("دلتا صانع سوق 0.3-0.6")
    if iv >= 40:
        mm = mm + 1
        reasons.append("IV عالي")
    if abs(strike - price) / price <= 0.02:
        mm = mm + 1
        reasons.append("ATM تماما")
    if premium < 50000:
        return None
    if vol < 500:
        return None
    if oi < 200:
        return None
    out = {"mm_score": mm, "vol_oi": round(vol_oi, 2), "premium": premium, "delta": round(delta, 2), "iv": round(iv, 1), "reasons": " | ".join(reasons), "entry": round(entry, 2), "bid": round(bid, 2), "ask": round(ask, 2), "vol": vol, "oi": oi}
    return out

def get_mm_for_ticker(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        if hist.empty:
            return None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
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
        today = datetime.date.today()
        for exp_str in exps[:4]:
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
                    for idx, row in df.iterrows():
                        vol = int(row['volume'])
                        if vol < 500:
                            continue
                        strike = float(row['strike'])
                        diff = abs(strike - price) / price
                        if diff > 0.05:
                            continue
                        info = calc_mm_score(row, price, vwap, days_left, 0)
                        if info is None:
                            continue
                        if info["mm_score"] < MIN_SCORE:
                            continue
                        if price > vwap and typ == "PUT":
                            continue
                        if price < vwap and typ == "CALL":
                            continue
                        if best is None or info["mm_score"] > best["mm_score"] or (info["mm_score"] == best["mm_score"] and info["premium"] > best["premium"]):
                            entry = info["entry"]
                            best = {"ticker": ticker, "type": typ, "strike": strike, "exp": exp_str, "days": days_left, "vol": info["vol"], "oi": info["oi"], "bid": info["bid"], "ask": info["ask"], "entry": info["entry"], "price": round(price, 2), "vwap": round(vwap, 2), "change": round(change, 2), "vol_mult": round(vol_mult, 2), "iv": info["iv"], "mm_score": info["mm_score"], "vol_oi": info["vol_oi"], "premium": info["premium"], "delta": info["delta"], "mm_reasons": info["reasons"]}
                            best["stop"] = round(entry * 0.5, 2)
                            best["t1"] = round(entry * 1.5, 2)
                            best["t2"] = round(entry * 2.3, 2)
                            best["t3"] = round(entry * 3.2, 2)
            except:
                continue
        return best
    except:
        return None

universe = get_universe()
st.write("الكون: " + str(len(universe)) + " سهم | قوة صانع السوق المطلوبة: " + str(MIN_SCORE) + "/8 | اقصى عدد: " + str(TOP_N))
st.write("مبدأ V8: اذا ما فيه صانع سوق حقيقي، ما نعطيك توصية. الافضل لا تدخل ولا تخسر على توصية وهمية.")

c_scan, c_clear = st.columns(2)
with c_scan:
    do_scan = st.button("افحص صانع السوق الان", type="primary", use_container_width=True)
with c_clear:
    do_new = st.button("فحص جديد - امسح القديم", use_container_width=True)

if do_new:
    st.session_state.top = None
    st.session_state.last_scan = ""
    st.session_state.scan_msg = ""
    st.rerun()

if do_scan:
    progress = st.progress(0)
    status = st.empty()
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for i, item in enumerate(ex.map(get_mm_for_ticker, universe)):
            if item is not None:
                results.append(item)
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text("فحصت " + str(i+1) + " / " + str(len(universe)) + " - لقيت " + str(len(results)) + " صانع سوق")
    progress.progress(1.0)
    results = sorted(results, key=lambda x: (-x["mm_score"], -x["premium"], x["ticker"]))
    top = results[:TOP_N]
    st.session_state.top = top
    st.session_state.last_scan = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
    if len(top) == 0:
        st.session_state.scan_msg = "ما فيه صانع سوق اليوم - كل الاسهم فشلت في اختبار صانع السوق. لا تدخل اي صفقة اليوم."
    else:
        st.session_state.scan_msg = "لقيت " + str(len(top)) + " صانع سوق حقيقي - هذولي فقط اللي عدوا الاختبار"

if st.session_state.top is not None:
    if len(st.session_state.top) == 0:
        st.warning(st.session_state.scan_msg)
        st.write("هذا شي زين مو شين. معناها صانع السوق ما دخل اليوم. اللي يدخل على اي سهم في هاليوم يخسر.")
    else:
        st.success(st.session_state.scan_msg)
        st.write("اخر فحص: " + st.session_state.last_scan + " بتوقيت الرياض - النتيجة محفوظة")
        st.markdown("### ارسال التوصيات")
        show_send_buttons(st.session_state.top, "top")
        show_cards(st.session_state.top)
        st.markdown("### ارسال مرة ثانية")
        show_send_buttons(st.session_state.top, "bottom")
else:
    st.info("اضغط افحص صانع السوق الان.")
    st.write("كيف يشتغل مؤشر صانع السوق V8:")
    st.write("1. Vol/OI فوق 2x = فلوس جديدة داخلة اليوم - نقطتين")
    st.write("2. بريميوم فوق 500k = صانع سوق يدفع فلوس كبيرة - نقطتين")
    st.write("3. OI فوق 5000 = متمركز من قبل - نقطة")
    st.write("4. فوليوم فوق 2000 - نقطة")
    st.write("5. دلتا 0.3 الى 0.6 = عقد صانع السوق المفضل - نقطة")
    st.write("6. IV فوق 40 - نقطة")
    st.write("7. سترايك ATM تماما - نقطة")
    st.write("اذا السهم ما جاب 6 من 8، ما يطلع لك. عشان كذا النتيجة ثابتة وما تتغير كل 5 دقايق.")

st.caption("اخر تحديث: " + datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M') + " بتوقيت الرياض")
