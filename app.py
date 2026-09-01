import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
import pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 SORTED")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def is_market_open():
    now_ny = datetime.now(NY)
    if now_ny.weekday() >= 5: return False
    mins = now_ny.hour*60 + now_ny.minute
    return 570 <= mins <= 960

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id':CHAT_ID,'text':msg,'parse_mode':'Markdown'}, timeout=15)
        return r.status_code==200
    except: return False

def load():
    if os.path.exists(SENT_FILE):
        try: return json.load(open(SENT_FILE))
        except: return []
    return []

def save(d): json.dump(d, open(SENT_FILE,'w'))

def get_data(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d")
        curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    daily=tk.history(period="20d", interval="1d")
    return curr, daily, tk

# ========= الجزء الأول: is_strong - 4 مدارس فنية =========
def is_strong(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    try:
        # نفحص 30د و 4س - اقوى فريمات للحيتان
        best = None
        for interval, period in [("30m","10d"), ("60m","10d"), ("4h","20d"), ("1d","50d")]:
            df = yf.download(real, period=period, interval=interval, progress=False, auto_adjust=True)
            if len(df) < 40: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            close=df['Close']; vol=df['Volume']; open_=df['Open']; high=df['High']; low=df['Low']

            # 1- الترند
            vwap = (close * vol).cumsum() / vol.cumsum()
            ema200 = close.ewm(span=200).mean()
            ema20 = close.ewm(span=20).mean()
            ema50 = close.ewm(span=50).mean()
            trend = 0
            trend += 1 if close.iloc[-1] > vwap.iloc[-1] else -1
            trend += 1 if close.iloc[-1] > ema200.iloc[-1] else -1
            trend += 1 if ema20.iloc[-1] > ema50.iloc[-1] else -1

            # 2- الزخم RSI + Squeeze
            delta=close.diff()
            gain=delta.where(delta>0,0).rolling(14).mean()
            loss=-delta.where(delta<0,0).rolling(14).mean()
            rs=gain/loss
            rsi=100-(100/(1+rs))
            bb_mid=close.rolling(20).mean()
            bb_std=close.rolling(20).std()
            bb_u=bb_mid+bb_std*2
            bb_l=bb_mid-bb_std*2
            mom=0
            mom += 1 if rsi.iloc[-1] > 60 else -1 if rsi.iloc[-1] < 40 else 0
            mom += 1 if close.iloc[-1] > bb_u.iloc[-1] else -1 if close.iloc[-1] < bb_l.iloc[-1] else 0

            # 3- السيولة
            vol_avg=vol.rolling(50).mean()
            vol_s = 1 if vol.iloc[-1] > vol_avg.iloc[-1]*1.5 else -1 if vol.iloc[-1] < vol_avg.iloc[-1]*0.7 else 0

            # 4- السلوك السعري
            body=abs(close.iloc[-1]-open_.iloc[-1])
            rng=high.iloc[-1]-low.iloc[-1]
            price_s = 1 if body > rng*0.7 and close.iloc[-1] > open_.iloc[-1] else -1 if body > rng*0.7 else 0

            total=trend+mom+vol_s+price_s

            curr_res = None
            if total >= 4: curr_res = {"dir":"CALL","score":total,"label":"شراء قوي جدا","tf":interval,"rsi":round(float(rsi.iloc[-1]),1)}
            elif total >= 2: curr_res = {"dir":"CALL","score":total,"label":"شراء","tf":interval,"rsi":round(float(rsi.iloc[-1]),1)}
            elif total <= -4: curr_res = {"dir":"PUT","score":total,"label":"بيع قوي جدا","tf":interval,"rsi":round(float(rsi.iloc[-1]),1)}
            elif total <= -2: curr_res = {"dir":"PUT","score":total,"label":"بيع","tf":interval,"rsi":round(float(rsi.iloc[-1]),1)}

            if curr_res:
                if best is None or abs(curr_res['score']) > abs(best['score']):
                    best = curr_res

        if best: return True, best
        return False, None
    except Exception as e:
        return False, None

# ========= الجزء الثاني: فلتر العقود =========
def filter_whale_contracts(ticker, tech_dir):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real)
        curr=float(tk.fast_info.get('last_price',0))
        if curr==0:
            h=tk.history(period="1d")
            curr=float(h['Close'].iloc[-1])
        exps=tk.options[:2] # اقرب تاريخين فقط 1-3 DTE
        whales=[]
        for exp in exps:
            chain=tk.option_chain(exp)
            opts = chain.calls if tech_dir=="CALL" else chain.puts
            for _, row in opts.iterrows():
                strike=row['strike']
                dist=abs(strike-curr)/curr
                if dist>0.015: continue
                bid=row.get('bid',0); ask=row.get('ask',0)
                if not bid or not ask: continue
                spread=(ask-bid)/ask*100 if ask>0 else 100
                if spread>5: continue
                vol=row.get('volume',0) or 0
                premium = (bid+ask)/2 * vol * 100
                if premium < 100000: continue # ارفعها 400000 في اللايف
                whales.append({"ticker":ticker,"type":tech_dir,"strike":strike,"exp":exp,"premium":int(premium),"spread":round(spread,1),"vol":int(vol),"dist":round(dist*100,2),"price":round((bid+ask)/2,2),"curr":round(curr,2)})
        return sorted(whales, key=lambda x:x['premium'], reverse=True)[:2]
    except: return []

# ========= الواجهة =========
st.title("🐋 V99 SORTED - نظام الجزأين")
st.caption("الجزء 1: تحليل فني 4 مدارس | الجزء 2: فلتر عقود حيتان")

if st.button("🚀 فحص شامل - 54 سهم"):
    results=[]
    whales_all=[]
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        prog.progress((i+1)/len(WATCHLIST_54))
        ok, tech = is_strong(t)
        if ok:
            results.append({"Ticker":t,"اتجاه":tech['dir'],"قوة":tech['label'],"نقاط":tech['score'],"فريم":tech['tf'],"RSI":tech['rsi']})
            # فلتر عقود لنفس السهم
            wc = filter_whale_contracts(t, tech['dir'])
            whales_all.extend(wc)

    if results:
        df=pd.DataFrame(results).sort_values("نقاط", ascending=False)
        st.dataframe(df, use_container_width=True)

        if whales_all:
            st.subheader("🐋 عقود حيتان مطابقة للاتجاه الفني")
            st.dataframe(pd.DataFrame(whales_all).sort_values("premium", ascending=False), use_container_width=True)

            # ارسال تيليجرام فقط للاقوى
            sent=load()
            for r in results:
                if abs(r['نقاط'])>=4:
                    key=f"{r['Ticker']}_{r['اتجاه']}_{datetime.now(RIYADH).date()}"
                    if key in sent: continue
                    w = [x for x in whales_all if x['ticker']==r['Ticker']]
                    if w:
                        w=w[0]
                        msg=f"🐋 *{r['Ticker']} {r['اتجاه']}* | {r['قوة']}\nفريم: {r['فريم']} | نقاط: {r['نقاط']}/6 | RSI: {r['RSI']}\n\n💰 عقد حوت: {w['strike']} {w['exp']}\nPremium: ${w['premium']:,} | Spread: {w['spread']}%\nDist: {w['dist']}% | Vol: {w['vol']} | سعر: ${w['price']}"
                        if send(msg):
                            sent.append(key)
                            save(sent)
                            time.sleep(1)
    else:
        st.warning("لا يوجد اسهم قوية حاليا - كلها محايدة")

st.divider()
st.info("الشروط: Premium>100k (اختبار) / 400k لايف | Spread<5% | Strike قريب 1.5% | اتجاه العقد = اتجاه فني")
if is_market_open(): st.success("السوق مفتوح - البيانات لحظية")
else: st.warning("السوق مغلق - بيانات متأخرة")
