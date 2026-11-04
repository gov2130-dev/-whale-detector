# الحيتان V6 - مضمون يطلع نتائج
# التغيير الجوهري: ما فيه حذف. كل سهم ياخذ نقاط 0-4 ونعرض أقوى 20

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="صانع السوق V6", layout="wide")
st.title("🦈 صانع السوق V6 - أقوى 20 سهم دائماً")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json", "Accept-Language": "en-US,en;q=0.9"}

col1, col2, col3 = st.columns(3)
with col1:
    MIN_IV = st.slider("أقل IV %", 15, 60, 20)
with col2:
    MIN_BLOCK = st.number_input("أقل بلوك سهم", value=10000, step=5000)
with col3:
    TOP_N = st.slider("كم سهم أعرض؟", 10, 30, 20)

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
    hot = ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","NFLX","AMD","SMCI","ARM","APP","PLTR","HOOD","COIN","MSTR","MARA","RIOT","CLSK","GME","AMC","OPEN","CVNA","SOFI","BABA","PDD","JD","MRNA","RIVN","LCID","NIO","DKNG","RBLX","U","AI","SOUN","UPST","AFRM","CHWY","BYND","SPCE","INTC","MU","QCOM","TXN","ADI","MCHP","ON","SHOP","SQ","PYPL","ABNB","UBER","DASH","ROKU","ZM","DOCU","PTON","TLRY","CGC","NOK","PLUG","FCEL","QS","GPRO","TSM","ASML","CRM","ORCL","BAC","JPM","XOM","CVX","WMT","COST","PEP","KO","PFE","BIIB","NUE","FCX","OXY","USO","GLD","SLV","CLF","X","LLY","V","MA","HD","JNJ","UNH","WFC","CSCO","ACN","MCD","ABT","DHR","GE","CAT","LOW","INTU","DE","AMAT","BKNG","LRCX","KLAC","SNPS","CDNS","MRVL","PANW","CRWD","NET","DDOG","ZS","MDB","SNOW","TEAM","WDAY","EA"]
    universe = sorted(list(set(universe + hot)))
    return universe

def get_data(ticker):
    try:
        tk = yf.Ticker(ticker)
        iv = 0
        top_call = None
        top_put = None
        try:
            exps = tk.options
            if exps:
                for exp in exps[:1]:
                    try:
                        chain = tk.option_chain(exp)
                        for df, typ in [(chain.calls, "CALL"), (chain.puts, "PUT")]:
                            if len(df) == 0:
                                continue
                            valid = df[df['volume'] > 5]
                            if len(valid) > 0:
                                iv = max(iv, float(valid['impliedVolatility'].median() * 100))
                            df2 = df[df['volume'] > 100].sort_values('volume', ascending=False)
                            if len(df2) > 0:
                                r = df2.iloc[0]
                                item = {"strike": r['strike'], "vol": int(r['volume']), "oi": int(r['openInterest']), "type": typ, "price": round(float(r['lastPrice']), 2)}
                                if typ == "CALL" and (top_call is None or item['vol'] > top_call['vol']):
                                    top_call = item
                                if typ == "PUT" and (top_put is None or item['vol'] > top_put['vol']):
                                    top_put = item
                    except:
                        continue
        except:
            pass

        hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        if hist.empty or len(hist) < 2:
            return None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
        prev_high = float(hist['High'].iloc[-2])
        prev_low = float(hist['Low'].iloc[-2])
        change = (price - prev_close) / prev_close * 100 if prev_close else 0
        avg_vol = float(hist['Volume'].iloc[:-1].mean())
        today_vol = float(hist['Volume'].iloc[-1])
        vol_mult = today_vol / avg_vol if avg_vol > 0 else 0

        vwap = price
        try:
            intra = yf.download(ticker, period="1d", interval="15m", progress=False, auto_adjust=False)
            if not intra.empty:
                if isinstance(intra.columns, pd.MultiIndex):
                    intra.columns = intra.columns.get_level_values(0)
                tp = (intra['High'] + intra['Low'] + intra['Close']) / 3
                vwap = float((tp * intra['Volume']).sum() / intra['Volume'].sum()) if intra['Volume'].sum() > 0 else price
        except:
            pass

        has_block = False
        block_size = 0
        try:
            url = f"https://api.nasdaq.com/api/quote/{ticker}/trades?assetclass=stock&limit=100"
            r = requests.get(url, headers=HEADERS, timeout=5)
            trades = r.json().get('data', {}).get('trades', [])
            for t in trades:
                try:
                    sz = int(float(str(t.get('size', '0')).replace(',', '')))
                    if sz >= MIN_BLOCK:
                        has_block = True
                        block_size = max(block_size, sz)
                except:
                    continue
        except:
            pass

        score = 0
        reasons = []
        if iv >= MIN_IV:
            score += 1
            reasons.append(f"IV {round(iv,1)}%")
        if vol_mult >= 1.2:
            score += 1
            reasons.append(f"فوليوم {round(vol_mult,2)}x")
        if top_call or top_put:
            score += 1
            if top_call and (not top_put or top_call['vol'] >= top_put['vol']):
                reasons.append(f"CALL {top_call['strike']} Vol {top_call['vol']}")
            elif top_put:
                reasons.append(f"PUT {top_put['strike']} Vol {top_put['vol']}")
        if has_block:
            score += 1
            reasons.append(f"بلوك {block_size}")

        call_vol = top_call['vol'] if top_call else 0
        put_vol = top_put['vol'] if top_put else 0
        if price > vwap and call_vol >= put_vol:
            direction = "🟢 صعود"
            trade = f"CALL فوق ${prev_high} - هدف +3%"
            action = "CALL"
        elif price < vwap and put_vol > call_vol:
            direction = "🔴 نزول"
            trade = f"PUT تحت ${prev_low} - هدف -3%"
            action = "PUT"
        elif price > prev_high:
            direction = "🟢 اختراق"
            trade = f"اختراق ${prev_high}"
            action = "CALL"
        elif price < prev_low:
            direction = "🔴 كسر"
            trade = f"كسر ${prev_low}"
            action = "PUT"
        else:
            direction = "🟡 تجميع"
            trade = "انتظر الاختراق"
            action = "WATCH"

        top_opt = ""
        if top_call and (not top_put or call_vol >= put_vol):
            top_opt = f"CALL {top_call['strike']} Vol {top_call['vol']} OI {top_call['oi']} ${top_call['price']}"
        elif top_put:
            top_opt = f"PUT {top_put['strike']} Vol {top_put['vol']} OI {top_put['oi']} ${top_put['price']}"

        return {
            "Ticker": ticker,
            "Price": round(price, 2),
            "التغير %": round(change, 2),
            "VWAP": round(vwap, 2),
            "IV %": round(iv, 1),
            "فوليوم x": round(vol_mult, 2),
            "الاتجاه": direction,
            "أقوى أوبشن": top_opt,
            "بلوك": f"✅ {block_size}" if has_block else "❌",
            "Score": f"{score}/4",
            "الصفقة": trade,
            "أسباب": " + ".join(reasons) if reasons else "لا توجد إشارة قوية",
            "_score": score,
            "_action": action,
        }
    except Exception as e:
        return None

universe = get_universe()
st.write(f"الكون: **{len(universe)} سهم** | IV فوق {MIN_IV}% | بلوك فوق {MIN_BLOCK} | بنعرض أقوى {TOP_N} سهم")
st.info("💡 V6 ما يحذف أي سهم. حتى لو السوق ضعيف، بيطلع لك أقوى الأسهم الموجودة مرتبة.")

if st.button("🔍 افحص الآن - صانع السوق", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        for i, item in enumerate(ex.map(get_data, universe)):
            if item:
                results.append(item)
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text(f"فحصت {i+1} / {len(universe)} ...")
    progress.progress(1.0)
    results = sorted(results, key=lambda x: (x['_score'], x['فوليوم x'], x['IV %']), reverse=True)
    top = results[:TOP_N]
    status.text(f"خلص الفحص - فحصت {len(results)} سهم، بنعرض أقوى {len(top)}")
    df = pd.DataFrame(top)
    st.dataframe(df[["Ticker","Price","التغير %","VWAP","IV %","فوليوم x","الاتجاه","أقوى أوبشن","بلوك","Score","الصفقة"]], use_container_width=True)
    bulls = [r for r in top if "صعود" in r['الاتجاه'] or "اختراق" in r['الاتجاه']]
    bears = [r for r in top if "نزول" in r['الاتجاه'] or "كسر" in r['الاتجاه']]
    colA, colB = st.columns(2)
    with colA:
        st.success(f"🟢 صعود: {len(bulls)} سهم")
        for r in bulls[:7]:
            st.write(f"**{r['Ticker']}** ${r['Price']} ({r['التغير %']}%) - {r['أقوى أوبشن']} | {r['Score']}")
    with colB:
        st.error(f"🔴 نزول: {len(bears)} سهم")
        for r in bears[:7]:
            st.write(f"**{r['Ticker']}** ${r['Price']} ({r['التغير %']}%) - {r['أقوى أوبشن']} | {r['Score']}")
    st.markdown("### 🔍 ليش هالأسهم اختيرت؟")
    for r in top[:10]:
        st.text(f"{r['Ticker']} {r['Score']} - {r['أسباب']}")
    if st.button("📩 أرسل التقرير لتلجرام"):
        msg = f"🦈 <b>صانع السوق V6 - {datetime.date.today()}</b>\nأقوى {len(top)} سهم\n\n"
        msg += f"🟢 <b>صعود:</b>\n"
        for r in bulls[:7]:
            msg += f"{r['Ticker']} ${r['Price']} {r['التغير %']}% IV {r['IV %']}% Vol {r['فوليوم x']}x {r['Score']}\n  {r['أقوى أوبشن']}\n  {r['الصفقة']}\n"
        msg += f"\n🔴 <b>نزول:</b>\n"
        for r in bears[:7]:
            msg += f"{r['Ticker']} ${r['Price']} {r['التغير %']}% IV {r['IV %']}% Vol {r['فوليوم x']}x {r['Score']}\n  {r['أقوى أوبشن']}\n  {r['الصفقة']}\n"
        if send_telegram(msg):
            st.success("انرسل لتلجرام ✅")
        else:
            st.error("ما انرسل - تأكد من BOT_TOKEN و CHAT_ID")
else:
    st.info("اضغط افحص الآن. بياخذ 1-2 دقيقة.")
    st.markdown("""
    **كيف تداول على V6:**
    - ركز على اللي جاب **3/4 أو 4/4** فقط - هذي أقوى إشارة
    - 🟢 صعود = CALL فوق قمة أمس
    - 🔴 نزول = PUT تحت قاع أمس
    - 🟡 تجميع = لا تدخل
    - **لا تدخل إذا IV فوق 80%** - الأوبشن غالي
    """)

st.caption(f"آخر تحديث: {datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')} بتوقيت الرياض")
