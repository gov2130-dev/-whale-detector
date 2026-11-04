# الحيتان V5 - صانع السوق الحقيقي
# شروط واقعية: فوليوم انفجار + أوبشن غير طبيعي + VWAP + بلوك
# يعطي صعود ونزول - الاثنين فيهم فلوس

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="صانع السوق V5", layout="wide")
st.title("🦈 صانع السوق V5 - إشارات حقيقية يومية")

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
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"}

# ===== إعدادات - خففتها عشان تطلع نتائج =====
col1, col2, col3, col4 = st.columns(4)
with col1:
    MIN_IV = st.slider("أقل IV %", 15, 60, 25)
with col2:
    MIN_BLOCK = st.number_input("أقل بلوك سهم", value=10000, step=5000)
with col3:
    MIN_VOL_MULT = st.slider("فوليوم اليوم كم مرة من المعدل؟", 1.0, 3.0, 1.5)
with col4:
    MIN_SCORE = st.selectbox("اعرض بس اللي نتيجته", [1, 2, 3, 4], index=1)

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return True
    except:
        return False

@st.cache_data(ttl=3600)
def get_universe():
    universe = []
    try:
        sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        universe += [s.replace('.', '-') for s in sp]
    except:
        pass
    try:
        nd = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[0]['Ticker'].tolist()
        universe += nd
    except:
        pass
    # قائمة مركزة: أسهم صانع السوق يحبها - عالية السيولة والحركة
    hot = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","NFLX","AMD","SMCI","ARM","APP","PLTR","HOOD","COIN","MSTR","MARA","RIOT","CLSK","GME","AMC","OPEN","CVNA","SOFI","BABA","PDD","JD","MRNA","RIVN","LCID","NIO","DKNG","RBLX","U","AI","SOUN","UPST","AFRM","CHWY","BYND","SPCE","INTC","MU","QCOM","TXN","ADI","MCHP","ON","SHOP","SQ","PYPL","ABNB","UBER","DASH","ROKU","ZM","DOCU","PTON","TLRY","CGC","NOK","PLUG","FCEL","QS","GPRO","TSM","ASML","CRM","ORCL","BAC","JPM","XOM","CVX","WMT","COST","PEP","KO","PFE","BIIB","NUE","FCX","OXY","USO","GLD","SLV","CLF","X","LLY","V","MA","HD","JNJ","UNH","WFC","CSCO","ACN","MCD","ABT","DHR","GE","CAT","LOW","INTU","DE","AMAT","BKNG","LRCX","KLAC","SNPS","CDNS","MRVL","PANW","CRWD","NET","DDOG","ZS","MDB","SNOW","TEAM","WDAY","EA"]
    universe = sorted(list(set(universe + hot)))
    return universe

def get_iv_and_options(ticker):
    # يجيب IV + أقوى أوبشن CALL و PUT
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return None, [], 0
        best_calls = []
        best_puts = []
        iv_list = []
        for exp in exps[:2]:
            try:
                chain = tk.option_chain(exp)
                for df, typ in [(chain.calls, "CALL"), (chain.puts, "PUT")]:
                    if len(df) == 0:
                        continue
                    # IV
                    valid_iv = df[df['volume'] > 5]
                    if len(valid_iv) > 0:
                        iv_list.append(valid_iv['impliedVolatility'].median())
                    # أوبشن غير طبيعي: فوليوم > OI
                    df2 = df[(df['volume'] > 200) & (df['openInterest'] > 0) & (df['volume'] > df['openInterest'] * 0.8)]
                    for _, row in df2.sort_values('volume', ascending=False).head(2).iterrows():
                        item = {"strike": row['strike'], "vol": int(row['volume']), "oi": int(row['openInterest']), "type": typ, "exp": exp, "lastPrice": round(float(row['lastPrice']), 2)}
                        if typ == "CALL":
                            best_calls.append(item)
                        else:
                            best_puts.append(item)
            except:
                continue
        iv = float(pd.Series(iv_list).median() * 100) if iv_list else 0
        return iv, best_calls, best_puts
    except:
        return None, [], []

def get_price_data(ticker):
    try:
        # 25 يوم عشان نحسب معدل الفوليوم + VWAP + قمة وقاع أمس
        hist = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=False)
        if hist.empty or len(hist) < 5:
            return None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        # فوليوم اليوم vs المعدل
        avg_vol = hist['Volume'].iloc[:-1].mean()
        today_vol = hist['Volume'].iloc[-1]
        vol_mult = today_vol / avg_vol if avg_vol > 0 else 0
        # سعر اليوم
        price = float(hist['Close'].iloc[-1])
        prev_high = float(hist['High'].iloc[-2])
        prev_low = float(hist['Low'].iloc[-2])
        prev_close = float(hist['Close'].iloc[-2])
        change = (price - prev_close) / prev_close * 100

        # VWAP اليوم من بيانات 15 دقيقة
        try:
            intraday = yf.download(ticker, period="1d", interval="15m", progress=False, auto_adjust=False)
            if isinstance(intraday.columns, pd.MultiIndex):
                intraday.columns = intraday.columns.get_level_values(0)
            intraday['typical'] = (intraday['High'] + intraday['Low'] + intraday['Close']) / 3
            vwap = float((intraday['typical'] * intraday['Volume']).sum() / intraday['Volume'].sum())
        except:
            vwap = price

        return {
            "price": round(price, 2),
            "vwap": round(vwap, 2),
            "above_vwap": price > vwap,
            "vol_mult": round(float(vol_mult), 2),
            "vol_surge": vol_mult >= MIN_VOL_MULT,
            "change": round(change, 2),
            "prev_high": round(prev_high, 2),
            "prev_low": round(prev_low, 2),
            "breakout_up": price > prev_high,
            "breakdown_down": price < prev_low,
        }
    except:
        return None

def get_darkpool_nasdaq(ticker):
    try:
        url = f"https://api.nasdaq.com/api/quote/{ticker}/trades?assetclass=stock&limit=100"
        r = requests.get(url, headers=HEADERS, timeout=7)
        trades = r.json().get('data', {}).get('trades', [])
        blocks = []
        for t in trades:
            try:
                size = int(float(str(t.get('size', '0')).replace(',', '')))
                price = float(str(t.get('price', '0')).replace('$', '').replace(',', ''))
                if size >= MIN_BLOCK:
                    blocks.append({"size": size, "price": price})
            except:
                continue
        blocks = sorted(blocks, key=lambda x: x['size'], reverse=True)[:2]
        return {"has_block": len(blocks) > 0, "blocks": blocks}
    except:
        return {"has_block": False, "blocks": []}

def check_one(ticker):
    iv, calls, puts = get_iv_and_options(ticker)
    if iv is None or iv < MIN_IV:
        return None
    pdta = get_price_data(ticker)
    if not pdta:
        return None
    dark = get_darkpool_nasdaq(ticker)

    # 4 شروط جديدة واقعية
    cond_vol = pdta['vol_surge']  # فوليوم انفجار
    cond_opt = len(calls) > 0 or len(puts) > 0  # أوبشن غير طبيعي CALL أو PUT
    cond_vwap = True  # دايماً نحسب الاتجاه من VWAP
    cond_block = dark['has_block']

    score = sum([cond_vol, cond_opt, cond_block]) + (1 if pdta['breakout_up'] or pdta['breakdown_down'] else 0)

    if score < MIN_SCORE:
        return None

    # تحديد الاتجاه - صانع السوق وين رايح؟
    call_vol = sum([c['vol'] for c in calls]) if calls else 0
    put_vol = sum([p['vol'] for p in puts]) if puts else 0

    if pdta['above_vwap'] and call_vol >= put_vol:
        direction = "🟢 صعود - صانع سوق يجمع CALL"
        trade = f"اشتري CALL فوق ${pdta['prev_high']} - هدف +3% إلى +5%"
        action = "CALL"
    elif not pdta['above_vwap'] and put_vol > call_vol:
        direction = "🔴 نزول - صانع سوق يجمع PUT"
        trade = f"اشتري PUT تحت ${pdta['prev_low']} - هدف -3% إلى -5%"
        action = "PUT"
    elif pdta['breakout_up']:
        direction = "🟢 اختراق قمة أمس"
        trade = f"اختراق ${pdta['prev_high']} - تابع صعود"
        action = "CALL"
    elif pdta['breakdown_down']:
        direction = "🔴 كسر قاع أمس"
        trade = f"كسر ${pdta['prev_low']} - تابع نزول"
        action = "PUT"
    else:
        direction = "🟡 تجميع - صانع سوق يجمع بهدوء"
        trade = "راقب الاختراق - لا تدخل الآن"
        action = "WATCH"

    top_opt = ""
    if calls and (not puts or call_vol >= put_vol):
        c = max(calls, key=lambda x: x['vol'])
        top_opt = f"CALL {c['strike']} Vol {c['vol']} OI {c['oi']} سعر ${c['lastPrice']}"
    elif puts:
        p = max(puts, key=lambda x: x['vol'])
        top_opt = f"PUT {p['strike']} Vol {p['vol']} OI {p['oi']} سعر ${p['lastPrice']}"

    return {
        "Ticker": ticker,
        "Price": pdta['price'],
        "التغير %": pdta['change'],
        "VWAP": pdta['vwap'],
        "IV %": round(iv, 1),
        "فوليوم x": pdta['vol_mult'],
        "الاتجاه": direction,
        "أقوى أوبشن": top_opt,
        "بلوك": f"✅ {dark['blocks'][0]['size']} سهم" if cond_block else "❌",
        "Score": f"{score}/4",
        "الصفقة": trade,
        "_score": score,
        "_action": action,
        "_calls": calls[:1],
        "_puts": puts[:1],
        "_blocks": dark['blocks'],
    }

universe = get_universe()
st.write(f"الكون: **{len(universe)} سهم** | IV فوق {MIN_IV}% | فوليوم فوق {MIN_VOL_MULT}x | بلوك فوق {MIN_BLOCK}")
st.info("💡 V5 يعطيك صعود ونزول. صانع السوق يربح بالاتجاهين. لا تنتظر بس الصعود.")

if st.button("🔍 افحص الآن - صانع السوق", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        for i, item in enumerate(ex.map(check_one, universe)):
            if item:
                results.append(item)
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text(f"فحصت {i+1} / {len(universe)} ... لقيت {len(results)} سهم")
    progress.progress(1.0)
    status.text(f"خلص الفحص - لقيت {len(results)} سهم")

    if not results:
        st.warning("ما فيه نتائج - السوق مغلق أو الفوليوم ضعيف اليوم. جرب تخفف: IV 15% و فوليوم 1.0x و اعرض 1/4")
    else:
        results = sorted(results, key=lambda x: (x['_score'], x['فوليوم x']), reverse=True)
        df = pd.DataFrame(results)
        st.dataframe(df[["Ticker","Price","التغير %","VWAP","IV %","فوليوم x","الاتجاه","أقوى أوبشن","بلوك","Score","الصفقة"]], use_container_width=True)

        # تقسيم صعود / نزول
        bulls = [r for r in results if "صعود" in r['الاتجاه'] or "اختراق" in r['الاتجاه']]
        bears = [r for r in results if "نزول" in r['الاتجاه'] or "كسر" in r['الاتجاه']]
        colA, colB = st.columns(2)
        with colA:
            st.success(f"🟢 صعود: {len(bulls)} سهم")
            for r in bulls[:5]:
                st.write(f"**{r['Ticker']}** ${r['Price']} ({r['التغير %']}%) - {r['أقوى أوبشن']}")
        with colB:
            st.error(f"🔴 نزول: {len(bears)} سهم")
            for r in bears[:5]:
                st.write(f"**{r['Ticker']}** ${r['Price']} ({r['التغير %']}%) - {r['أقوى أوبشن']}")

        if st.button("📩 أرسل التقرير لتلجرام"):
            msg = f"🦈 <b>صانع السوق - {datetime.date.today()}</b>\nفحصت {len(universe)} سهم\n\n"
            msg += f"🟢 <b>صعود ({len(bulls)}):</b>\n"
            for r in bulls[:7]:
                msg += f"{r['Ticker']} ${r['Price']} {r['التغير %']}% IV {r['IV %']}% Vol {r['فوليوم x']}x\n  {r['أقوى أوبشن']}\n  {r['الصفقة']}\n"
            msg += f"\n🔴 <b>نزول ({len(bears)}):</b>\n"
            for r in bears[:7]:
                msg += f"{r['Ticker']} ${r['Price']} {r['التغير %']}% IV {r['IV %']}% Vol {r['فوليوم x']}x\n  {r['أقوى أوبشن']}\n  {r['الصفقة']}\n"
            if send_telegram(msg):
                st.success("انرسل لتلجرام ✅")
            else:
                st.error("ما انرسل - تأكد من BOT_TOKEN و CHAT_ID")
else:
    st.info("اضغط افحص الآن. بياخذ 1-2 دقيقة.")
    st.markdown("""
    **كيف تداول على V5 - مهم:**
    - 🟢 صعود + CALL فوليوم عالي = اشتري CALL فوق قمة أمس
    - 🔴 نزول + PUT فوليوم عالي = اشتري PUT تحت قاع أمس
    - 🟡 تجميع = لا تدخل، انتظر الاختراق
    - **لا تدخل إذا IV فوق 80%** - الأوبشن غالي وممكن يخسرك حتى لو السهم مشى صح
    - **هدفك 3% - 5% فقط** - الأوبشن يومي، لا تطمع
    """)

st.caption(f"آخر تحديث: {datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')} بتوقيت الرياض")
