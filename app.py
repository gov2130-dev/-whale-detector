# الحيتان V7 - بطاقات توصيات فقط - بدون جدول
# الشكل: 🟢 AAPL 325 CALL 🐋
# Exp / Stock / Entry / Bid / Stop / Targets

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="توصيات V7", layout="wide")
st.title("🦈 توصيات صانع السوق V7")

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
    MIN_IV = st.slider("أقل IV %", 15, 60, 20)
with col2:
    TOP_N = st.slider("كم توصية؟", 5, 15, 8)

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

def get_best_option(ticker):
    # يجيب أفضل عقد: أقرب انتهاء 0-7 أيام + سترايك قريب من السعر + أعلى فوليوم
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
        change = (price - prev_close) / prev_close * 100 if prev_close else 0
        avg_vol = float(hist['Volume'].iloc[:-1].mean())
        today_vol = float(hist['Volume'].iloc[-1])
        vol_mult = today_vol / avg_vol if avg_vol > 0 else 0

        # VWAP
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

        exps = tk.options
        if not exps:
            return None

        best = None
        best_score = -1
        iv_val = 0

        # نجرب أول 3 انتهاءات فقط - أسرع
        today = datetime.date.today()
        for exp_str in exps[:3]:
            try:
                exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if days_left < 0 or days_left > 14:
                    continue
                chain = tk.option_chain(exp_str)
                # نفحص CALL و PUT
                for df, typ in [(chain.calls, "CALL"), (chain.puts, "PUT")]:
                    if len(df) == 0:
                        continue
                    # IV
                    valid_iv = df[df['volume'] > 5]
                    if len(valid_iv) > 0:
                        iv_val = max(iv_val, float(valid_iv['impliedVolatility'].median() * 100))
                    # نفلتر: سترايك قريب من السعر +/- 5% + فوليوم > 100
                    df2 = df[(df['volume'] > 100) & (abs(df['strike'] - price) / price < 0.05)].copy()
                    for _, row in df2.iterrows():
                        vol = int(row['volume'])
                        oi = int(row['openInterest'])
                        bid = float(row['bid']) if pd.notna(row['bid']) else 0
                        ask = float(row['ask']) if pd.notna(row['ask']) else 0
                        last = float(row['lastPrice']) if pd.notna(row['lastPrice']) else 0
                        entry = ask if ask > 0 else last
                        if entry <= 0.10 or entry > 10:
                            continue
                        # النقاط: فوليوم عالي + سترايك قريب + سعر عقد رخيص
                        score = vol + (500 if abs(row['strike'] - price) / price < 0.02 else 0)
                        # تفضيل الاتجاه الصحيح: فوق VWAP -> CALL، تحت VWAP -> PUT
                        if price > vwap and typ == "CALL":
                            score += 1000
                        if price < vwap and typ == "PUT":
                            score += 1000
                        if score > best_score:
                            best_score = score
                            best = {
                                "ticker": ticker,
                                "type": typ,
                                "strike": float(row['strike']),
                                "exp": exp_str,
                                "days": days_left,
                                "vol": vol,
                                "oi": oi,
                                "bid": round(bid, 2),
                                "ask": round(ask, 2),
                                "last": round(last, 2),
                                "entry": round(entry, 2),
                                "price": round(price, 2),
                                "vwap": round(vwap, 2),
                                "change": round(change, 2),
                                "vol_mult": round(vol_mult, 2),
                                "prev_high": round(prev_high, 2),
                                "prev_low": round(prev_low, 2),
                                "iv": round(iv_val, 1),
                            }
            except:
                continue

        if not best:
            return None
        # حساب الوقف والأهداف من سعر الدخول
        entry = best['entry']
        best['stop'] = round(entry * 0.5, 2)
        best['t1'] = round(entry * 1.5, 2)
        best['t2'] = round(entry * 2.3, 2)
        best['t3'] = round(entry * 3.2, 2)
        # نقاط القوة
        score = 0
        if best['iv'] >= MIN_IV:
            score += 1
        if best['vol_mult'] >= 1.2:
            score += 1
        if best['vol'] > 500:
            score += 1
        if (best['price'] > best['vwap'] and best['type'] == "CALL") or (best['price'] < best['vwap'] and best['type'] == "PUT"):
            score += 1
        best['score'] = score
        best['is_whale'] = score >= 3
        return best
    except:
        return None

universe = get_universe()
st.write(f"الكون: **{len(universe)} سهم** | IV فوق {MIN_IV}% | بنعرض أقوى {TOP_N} توصية")

if st.button("🔍 افحص الآن - جيب توصيات", type="primary"):
    progress = st.progress(0)
    status = st.empty()
    results = []
    with ThreadPoolExecutor(max_workers=20) as ex:
        for i, item in enumerate(ex.map(get_best_option, universe)):
            if item:
                results.append(item)
            if i % 30 == 0:
                progress.progress(min((i+1)/len(universe), 1.0))
                status.text(f"فحصت {i+1} / {len(universe)} ... لقيت {len(results)} عقد")
    progress.progress(1.0)
    results = sorted(results, key=lambda x: (x['score'], x['vol'], x['vol_mult']), reverse=True)
    top = results[:TOP_N]
    status.text(f"خلص - أقوى {len(top)} توصية")

    # ===== بطاقات التوصيات - بدون جدول =====
    for r in top:
        emoji = "🟢" if r['type'] == "CALL"
