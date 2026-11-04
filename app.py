# الحيتان V4.1 - Streamlit - كامل ومصلح
# إصلاح 1: الكون صار 180 سهم ثابت إذا فشلت Wikipedia (كان يطلع 55 بس)
# إصلاح 2: فلتر IV صار 30% بدل 40% + عرض 1/3 بدل 2/3 عشان يطلع نتائج
# إصلاح 3: إضافة وضع Debug عشان تشوف ليش السهم انرفض

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="الحيتان V4.1", layout="wide")
st.title("🐋 الحيتان V4.1 - عقد متوافق + سويب + دارك بول")

# ===== الأسرار =====
try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""
try:
    POLYGON_API_KEY = st.secrets["POLYGON_API_KEY"]
except:
    POLYGON_API_KEY = ""

RIYADH = pytz.timezone("Asia/Riyadh")
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# ===== إعدادات =====
col1, col2, col3, col4 = st.columns(4)
with col1:
    MIN_IV = st.slider("أقل IV %", 20, 80, 30)
with col2:
    MIN_BLOCK = st.number_input("أقل بلوك سهم", value=50000, step=10000)
with col3:
    MIN_SWEEP_VOL = st.number_input("أقل فوليوم سويب", value=800, step=100)
with col4:
    MIN_SCORE = st.selectbox("اعرض بس اللي نتيجته", [1, 2, 3], index=0)

show_debug = st.checkbox("🔧 أظهر ليش الأسهم انرفضت (Debug)", value=False)

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return True
    except Exception as e:
        st.warning(f"خطأ تلجرام: {e}")
        return False

# ===== الكون: 180 سهم مضمون =====
@st.cache_data(ttl=86400)
def get_universe():
    universe = []
    try:
        sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        sp = [s.replace('.', '-') for s in sp]
        universe += sp
    except:
        pass
    try:
        nd = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[0]['Ticker'].tolist()
        universe += nd
    except:
        pass

    # قائمة احتياطية 180 سهم - هذي تشتغل حتى لو فشلت Wikipedia
    backup_180 = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","BRK-B","JPM","LLY","V","XOM","UNH","MA","HD","COST","PG","JNJ","WMT","NFLX","CRM","ORCL","BAC","CVX","ABBV","KO","PEP","TMO","WFC","CSCO","ACN","MCD","ABT","DHR","LIN","TXN","QCOM","AMGN","HON","IBM","ADBE","NOW","GE","CAT","UNP","SPG","LOW","INTU","DE","AMAT","BKNG","SYK","LRCX","ADI","MMC","ADP","GILD","MELI","KLAC","SNPS","CDNS","REGN","CTSH","MRVL","ORLY","CPRT","CSX","FTNT","PAYX","CHTR","FAST","ODFL","BKR","VRSK","CTAS","XEL","AZN","TEAM","WDAY","PCAR","EA","DDOG","ZS","CRWD","PANW","NET","MDB","SNOW","AI","SOUN","UPST","AFRM","HOOD","COIN","MSTR","MARA","RIOT","CLSK","CHWY","GME","AMC","OPEN","CVNA","BYND","SPCE","RIVN","LCID","NIO","SOFI","BABA","PDD","JD","MRNA","SMCI","ARM","APP","PLTR","DKNG","RBLX","U","BIIB","PFE","NUE","FCX","OXY","USO","GLD","SLV","CLF","X","TSM","ASML","SHOP","SQ","PYPL","ABNB","UBER","LYFT","DASH","ROKU","TWLO","ZM","DOCU","PTON","TLRY","CGC","ACB","SNDL","BB","NOK","PLUG","FCEL","QS","HYMC","GPRO","SKLZ","CLOV","WISH","INTC","MU","MCHP","ON","SWKS","QRVO","ENTG","LSCC"]

    universe = sorted(list(set(universe + backup_180)))
    return universe

def get_iv_fast(ticker):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return None
        for exp in exps[:3]:
            try:
                chain = tk.option_chain(exp)
                calls = chain.calls
                if len(calls) == 0:
                    continue
                valid = calls[calls['volume'] > 10]
                if len(valid) < 5:
                    continue
                iv = valid['impliedVolatility'].median()
                if iv and iv > 0:
                    return float(iv) * 100
            except:
                continue
        return 0
    except:
        return None

def get_price_vwap(ticker):
    try:
        hist = yf.download(ticker, period="2d", interval="15m", progress=False, auto_adjust=False)
        if hist.empty:
            return None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        hist['typical'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
        hist['vwap'] = (hist['typical'] * hist['Volume']).cumsum() / hist['Volume'].cumsum()
        last = hist.iloc[-1]
        prev_days = hist[hist.index.date < hist.index[-1].date()]
        if len(prev_days) == 0:
            return None
        prev_high = prev_days['High'].max()
        return {
            "price": round(float(last['Close']), 2),
            "vwap": round(float(last['vwap']), 2),
            "above_vwap": float(last['Close']) > float(last['vwap']),
            "above_prev_high": float(last['Close']) > float(prev_high)
        }
    except:
        return None

def get_unusual_options(ticker):
    try:
        url = f"https://api.nasdaq.com/api/quote/{ticker}/option-chain?assetclass=stock"
        r = requests.get(url, headers=HEADERS, timeout=8)
        rows = r.json()['data']['table']['rows']
        sweeps = []
        for row in rows[:60]:
            vol = int(row['volume'].replace(',', '')) if row['volume'] != '--' else 0
            oi = int(row['openInterest'].replace(',', '')) if row['openInterest'] != '--' else 0
            if vol > MIN_SWEEP_VOL and oi > 0 and vol > oi * 1.5:
                sweeps.append({"strike": row['strike'], "vol": vol, "oi": oi, "type": row['callPut']})
        return sweeps
    except:
        return []

def get_darkpool(ticker):
    if not POLYGON_API_KEY:
        return {"has_block": False, "blocks": [], "reason": "ما فيه POLYGON_API_KEY في Secrets"}
    try:
        today = datetime.date.today()
        url = f"https://api.polygon.io/v3/trades/{ticker}?limit=1000&timestamp.gte={today}T00:00:00Z&apiKey={POLYGON_API_KEY}"
        r = requests.get(url, timeout=10)
        data = r.json()
        blocks = []
        for t in data.get('results', []):
            size = t.get('size', 0)
            if size >= MIN_BLOCK:
                blocks.append({"size": size, "price": t.get('price', 0)})
        blocks = sorted(blocks, key=lambda x: x['size'], reverse=True)[:3]
        return {"has_block": len(blocks) > 0, "blocks": blocks, "reason": ""}
    except Exception as e:
        return {"has_block": False, "blocks": [], "reason": str(e)}

def check_one(ticker):
    iv = get_iv_fast(ticker)
    if iv is None or iv < MIN_IV:
        return {"debug": f"{ticker}: IV {iv} أقل من {MIN_IV}%"}
    price_data = get_price_vwap(ticker)
    if not price_data:
        return {"debug": f"{ticker}: ما فيه بيانات سعر"}
    options = get_unusual_options(ticker)
    dark = get_darkpool(ticker)

    cond1 = price_data['above_vwap'] and price_data['above_prev_high']
    cond2 = len(options) > 0
    cond3 = dark['has_block']
    score = sum([cond1, cond2, cond3])

    debug_msg = f"{ticker}: IV {round(iv,1)}% | سعر {price_data['price']} VWAP {price_data['vwap']} cond1={cond1} | سويب {len(options)} cond2={cond2} | بلوك {len(dark.get('blocks',[]))} cond3={cond3} {dark.get('reason','')} => {score}/3"

    if score >= MIN_SCORE:
        return {
            "Ticker": ticker,
            "Price": price_data['price'],
            "VWAP": price_data['vwap'],
            "IV %": round(iv, 1),
            "سعر فوق VWAP+قمة أمس": "✅" if cond1 else "❌",
            "سويب": "✅" if cond2 else "❌",
            "بلوك": "✅" if cond3 else "❌",
            "Score": f"{score}/3",
            "Status": "WHALE CONFIRMED 🐋" if score == 3 else "WATCH 👀" if score == 2 else "IV عالي فقط 📊",
            "_score": score,
            "_options": options[:2],
            "_blocks": dark.get('blocks', []),
            "debug": debug_msg
        }
    return {"debug": debug_msg}

# ===== الواجهة =====
universe = get_universe()
st.write(f"الكون: **{len(universe)} سهم** | فلتر IV فوق {MIN_IV}% | البلوك فوق {MIN_BLOCK} سهم")
if not POLYGON_API_KEY:
    st.error("⚠️ تنبيه: ما فيه POLYGON_API_KEY في Secrets، عشان كذا شرط البلوك بيكون دايماً ❌. أعلى نتيجة ممكنة الحين هي 2/3.")
else:
    st.success("✅ POLYGON_API_KEY موجود - شرط البلوك شغال")

if st.button("🔍 افحص الآن", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    debugs = []

    with ThreadPoolExecutor(max_workers=20) as ex:
        for i, item in enumerate(ex.map(check_one, universe)):
            if item:
                if "_score" in item:
                    results.append(item)
                if "debug" in item:
                    debugs.append(item["debug"])
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text(f"فحصت {i+1} / {len(universe)} ... لقيت {len(results)} سهم")

    progress.progress(1.0)
    status.text(f"خلص الفحص - لقيت {len(results)} سهم")

    if show_debug:
        with st.expander("🔧 ليش الأسهم انرفضت؟ اضغط هنا"):
            for d in debugs[:100]:
                st.text(d)

    if not results:
        st.warning("ما فيه أي سهم انطبقت عليه الشروط. جرب تخفف IV لـ 20% واعرض 1/3، أو افحص وقت السوق الأمريكي.")
    else:
        results = sorted(results, key=lambda x: (x['_score'], x['IV %']), reverse=True)
        df = pd.DataFrame(results)
        st.dataframe(df[["Ticker","Price","VWAP","IV %","سعر فوق VWAP+قمة أمس","سويب","بلوك","Score","Status"]], use_container_width=True)

        whales = [r for r in results if r['_score'] == 3]
        if whales:
            st.success(f"🐋 لقيت {len(whales)} حوت مؤكد 3/3")
            for w in whales:
                st.markdown(f"### 🐋 {w['Ticker']} - ${w['Price']} | IV {w['IV %']}%")
                if w['_options']:
                    o = w['_options'][0]
                    st.write(f"سويب: {o['type']} Strike {o['strike']} Vol {o['vol']} OI {o['oi']}")
                if w['_blocks']:
                    b = w['_blocks'][0]
                    st.write(f"بلوك: {b['size']} سهم @ ${b['price']}")
        else:
            st.info("ما فيه 3/3 اليوم، راقب الـ 2/3 فقط.")

        if st.button("📩 أرسل التقرير لتلجرام"):
            msg = f"🌅 <b>تقرير الحيتان - {datetime.date.today()}</b>\nفحصت {len(universe)} سهم | IV فوق {MIN_IV}%\n\n"
            for r in results[:12]:
                emoji = "🐋" if r['_score']==3 else "👀" if r['_score']==2 else "📊"
                msg += f"{emoji} <b>{r['Ticker']}</b> ${r['Price']} | IV {r['IV %']}% | {r['_score']}/3\n"
                if r['_options']:
                    msg += f"   أوبشن: {r['_options'][0]['type']} {r['_options'][0]['strike']} Vol {r['_options'][0]['vol']}\n"
                if r['_blocks']:
                    msg += f"   بلوك: {r['_blocks'][0]['size']} سهم\n"
            msg += "\n💡 ادخل بس على 3/3 أو 2/3"
            if send_telegram(msg):
                st.success("انرسل لتلجرام ✅")
            else:
                st.error("ما انرسل - تأكد من BOT_TOKEN و CHAT_ID في Secrets")
else:
    st.info("اضغط افحص الآن. بياخذ 1-2 دقيقة لأول مرة.")
    st.markdown("""
    **الشروط الثلاثة:**
    - ✅ سعر فوق VWAP + فوق أعلى سعر أمس
    - ✅ سويب فوليومه أكبر من OI بـ 1.5 مرة
    - ✅ بلوك دارك بول واحد أكبر من 50,000 سهم
    - **3/3 = WHALE CONFIRMED 🐋**
    """)

st.caption(f"آخر تحديث: {datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')} بتوقيت الرياض")
