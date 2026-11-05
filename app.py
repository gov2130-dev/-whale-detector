# الحيتان V9 - صانع سوق حقيقي مجمع
# سهم واحد = حتى 4 عقود - سعر 0.5 الى 3 دولار - انتهاء 7 الى 14 يوم
# وقت السوق الشتوي: 5:30 عصر الى 12 ليل بتوقيت الرياض

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="صانع السوق الحقيقي V9", layout="wide")
st.title("صانع السوق الحقيقي V9")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")

st.write("وقت السوق الشتوي: 5:30 عصر الى 12 ليل بتوقيت الرياض")
st.write("القاعدة: صانع سوق حقيقي دخل سهم، ننشر السهم وكل عقوده القوية من 0.5 الى 3 دولار. اذا ما دخل احد، ما ننشر شي.")

col1, col2 = st.columns(2)
with col1:
    MAX_PRICE = st.slider("اعلى سعر عقد تدخله", 1.0, 5.0, 3.0)
with col2:
    MAX_PER_TICKER = st.slider("كم عقد لكل سهم", 1, 4, 4)

if "groups" not in st.session_state:
    st.session_state.groups = None
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

def build_msg(groups):
    msg = "صانع السوق الحقيقي - " + str(datetime.date.today()) + "\n"
    msg = msg + "وقت السوق: 5:30 عصر الى 12 ليل بتوقيت الرياض\n\n"
    for g in groups:
        ticker = g["ticker"]
        price = g["price"]
        msg = msg + "=== " + ticker + " سعر السهم $" + str(price) + " ===\n"
        msg = msg + "صانع السوق داخل في هالسهم - عندك " + str(len(g["contracts"])) + " عقود اختر حسب سيولتك\n"
        for r in g["contracts"]:
            if r["type"] == "CALL":
                e2 = "🟢"
            else:
                e2 = "🔴"
            strike2 = int(r["strike"])
            msg = msg + e2 + " " + ticker + " " + str(strike2) + " " + r["type"] + "\n"
            msg = msg + "Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Entry: $" + str(r["entry"]) + " Bid: $" + str(r["bid"]) + "\n"
            msg = msg + "Vol/OI: " + str(r["vol_oi"]) + "x Premium: $" + str(r["premium"]) + "\n"
            msg = msg + "Stop: $" + str(r["stop"]) + " Target: $" + str(r["t1"]) + " | $" + str(r["t2"]) + " | $" + str(r["t3"]) + "\n\n"
    msg = msg + "صالحه 5 ايام الى اسبوع - صانع السوق ممكن يشدها اليوم او بكره او بعد يومين\n"
    return msg

def show_send_buttons(groups, suffix):
    msg = build_msg(groups)
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
    st.caption("واتساب: بيفتح لك الواتساب والتوصيات مكتوبة، اختر الشخص وارسل. تلجرام: يرسل تلقائي.")

def show_groups(groups):
    for g in groups:
        ticker = g["ticker"]
        price = g["price"]
        change = g["change"]
        st.markdown(
            "<div style='background:#1e293b; border-radius:16px; padding:14px; margin-top:18px; margin-bottom:6px;'>"
            + "<div style='font-size:24px; font-weight:800; color:white;'>🐋 " + ticker + " - $" + str(price) + " (" + str(change) + "%)</div>"
            + "<div style='color:#86efac; margin-top:4px; font-size:15px;'>صانع السوق الحقيقي داخل في هالسهم - " + str(len(g["contracts"])) + " عقود قوية - اختر حسب سيولتك</div>"
            + "<div style='color:#94a3b8; margin-top:4px; font-size:13px;'>صالحه 5 ايام الى اسبوع - ممكن يشدها اليوم او بكره او بعد يومين</div>"
            + "</div>"
        )
        for r in g["contracts"]:
            if r["type"] == "CALL":
                emoji_txt = "🟢"
                border = "#22c55e"
            else:
                emoji_txt = "🔴"
                border = "#ef4444"
            strike_int = int(r["strike"])
            st.markdown(
                "<div style='border:2px solid " + border + "; border-radius:16px; padding:16px; margin-bottom:12px; margin-left:16px; background:#0f172a;'>"
                + "<div style='font-size:20px; font-weight:800; color:white;'>" + emoji_txt + " " + ticker + " " + str(strike_int) + " " + r["type"] + "</div>"
                + "<div style='color:#cbd5e1; margin-top:6px; font-size:14px;'>Exp: " + r["exp"] + " (" + str(r["days"]) + "d) | Vol/OI: <b>" + str(r["vol_oi"]) + "x</b> | Premium: <b>$" + str(r["premium"]) + "</b></div>"
                + "<div style='color:#94a3b8; margin-top:4px; font-size:13px;'>" + r["mm_reasons"] + "</div>"
                + "<div style='color:white; margin-top:10px; font-size:16px;'>Entry: <b>$" + str(r["entry"]) + "</b> Bid: $" + str(r["bid"]) + " Ask: $" + str(r["ask"]) + "</div>"
                + "<div style='color:#fca5a5; margin-top:4px; font-size:15px;'>Stop: <b>$" + str(r["stop"]) + "</b> | Delta: " + str(r["delta"]) + " | IV: " + str(r["iv"]) + "% | Vol: " + str(r["vol"]) + " | OI: " + str(r["oi"]) + "</div>"
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

def check_mm(row, price):
    vol = int(row['volume'])
    oi = int(row['openInterest'])
    if vol < 500:
        return None
    if oi < 500:
        return None
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
    entry = 0
    is_live = False
    if bid > 0 and ask > 0 and bid <= ask:
        entry = (bid + ask) / 2
        is_live = True
    else:
        if last <= 0:
            return None
        entry = last
        is_live = False
    if entry < 0.50 or entry > MAX_PRICE:
        return None
    vol_oi = 0
    if oi > 0:
        vol_oi = vol / oi
    if vol_oi < 1.0:
        return None
    premium = int(vol * entry * 100)
    if premium < 100000:
        return None
    strike = float(row['strike'])
    diff = abs(strike - price) / price
    if diff > 0.06:
        return None
    delta = 0
    try:
        delta = abs(float(row['delta']))
    except:
        delta = 0
    iv = 0
    try:
        iv = float(row['impliedVolatility']) * 100
    except:
        iv = 0
    reasons = []
    if vol_oi >= 2.0:
        reasons.append("فلوس جديدة Vol/OI 2x+")
    else:
        reasons.append("Vol/OI فوق 1x")
    if premium >= 500000:
        reasons.append("بريميوم ضخم +500k")
    else:
        reasons.append("بريميوم +100k")
    if oi >= 5000:
        reasons.append("OI عالي 5000+")
    if delta >= 0.20 and delta <= 0.65:
        reasons.append("دلتا صانع سوق")
    if iv >= 30:
        reasons.append("IV عالي")
    out = {"vol": vol, "oi": oi, "bid": round(bid, 2), "ask": round(ask, 2), "entry": round(entry, 2), "vol_oi": round(vol_oi, 2), "premium": premium, "delta": round(delta, 2), "iv": round(iv, 1), "mm_reasons": " | ".join(reasons), "is_live": is_live}
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
        if abs(change) > 25:
            return None
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
        contracts = []
        today = datetime.date.today()
        for exp_str in exps[:5]:
            try:
                exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if days_left < 5 or days_left > 14:
                    continue
                chain = tk.option_chain(exp_str)
                pairs = [(chain.calls, "CALL"), (chain.puts, "PUT")]
                for df, typ in pairs:
                    if len(df) == 0:
                        continue
                    if price > vwap and typ == "PUT":
                        continue
                    if price < vwap and typ == "CALL":
                        continue
                    for idx, row in df.iterrows():
                        info = check_mm(row, price)
                        if info is None:
                            continue
                        strike = float(row['strike'])
                        entry = info["entry"]
                        c = {"ticker": ticker, "type": typ, "strike": strike, "exp": exp_str, "days": days_left, "vol": info["vol"], "oi": info["oi"], "bid": info["bid"], "ask": info["ask"], "entry": info["entry"], "price": round(price, 2), "vwap": round(vwap, 2), "change": round(change, 2), "iv": info["iv"], "vol_oi": info["vol_oi"], "premium": info["premium"], "delta": info["delta"], "mm_reasons": info["mm_reasons"], "is_live": info["is_live"]}
                        c["stop"] = round(entry * 0.5, 2)
                        c["t1"] = round(entry * 1.5, 2)
                        c["t2"] = round(entry * 2.3, 2)
                        c["t3"] = round(entry * 3.2, 2)
                        contracts.append(c)
            except:
                continue
        if len(contracts) == 0:
            return None
        contracts = sorted(contracts, key=lambda x: (-x["premium"], x["entry"]))
        contracts = contracts[:MAX_PER_TICKER]
        group = {"ticker": ticker, "price": round(price, 2), "change": round(change, 2), "contracts": contracts, "total_premium": sum([x["premium"] for x in contracts])}
        return group
    except:
        return None

universe = get_universe()
st.write("الكون: " + str(len(universe)) + " سهم | عقود من $0.50 الى $" + str(MAX_PRICE) + " | انتهاء 5 الى 14 يوم")

c_scan, c_clear = st.columns(2)
with c_scan:
    do_scan = st.button("افحص صانع السوق الحقيقي الان", type="primary", use_container_width=True)
with c_clear:
    do_new = st.button("فحص جديد - امسح القديم", use_container_width=True)

if do_new:
    st.session_state.groups = None
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
                status.text("فحصت " + str(i+1) + " / " + str(len(universe)) + " - لقيت " + str(len(results)) + " سهم فيه صانع سوق")
    progress.progress(1.0)
    results = sorted(results, key=lambda x: (-x["total_premium"], x["ticker"]))
    st.session_state.groups = results
    st.session_state.last_scan = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
    if len(results) == 0:
        st.session_state.scan_msg = "ما فيه صانع سوق حقيقي اليوم - لا تدخل اي صفقة."
    else:
        st.session_state.scan_msg = "لقيت " + str(len(results)) + " سهم فيه صانع سوق حقيقي"

if st.session_state.groups is not None:
    if len(st.session_state.groups) == 0:
        st.warning(st.session_state.scan_msg)
        st.write("هذا زين مو شين. معناها صانع السوق ما دخل اليوم. اللي يدخل على اي سهم في هاليوم يخسر.")
    else:
        st.success(st.session_state.scan_msg)
        st.write("اخر فحص: " + st.session_state.last_scan + " بتوقيت الرياض - النتيجة محفوظة")
        st.markdown("### ارسال التوصيات")
        show_send_buttons(st.session_state.groups, "top")
        show_groups(st.session_state.groups)
        st.markdown("### ارسال مرة ثانية")
        show_send_buttons(st.session_state.groups, "bottom")
else:
    st.info("اضغط افحص صانع السوق الحقيقي الان.")
    st.write("مثال اللي تبيه انت:")
    st.write("AMD دخلها صانع سوق - بنعطيك AMD 480 و AMD 470 و AMD 460 و AMD 450 كلها")
    st.write("انت تختار اللي سعره يناسب سيولتك - اللي معه فلوس يدخل ابو 2.80، واللي سيولته ضعيفة يدخل ابو 1.50")
    st.write("كلها نفس السهم ونفس صانع السوق، الفرق بس السعر")
    st.write("افضل وقت للفحص: 5:30 عصر الى 12 ليل بتوقيت الرياض")

st.caption("اخر تحديث: " + datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M') + " بتوقيت الرياض")
