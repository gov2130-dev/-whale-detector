import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
import pandas as pd
import numpy as np

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 WHALE FILTER V2")
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

# ===== الجزء الأول: محرك التحليل الفني - 4 مدارس =====
def analyze_technical(ticker):
    real = TICKER_MAP.get(ticker, ticker)
    try:
        df = yf.download(real, period="10d", interval="30m", progress=False)
        if len(df) < 50: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']
        
        # مدرسة 1: الترند
        vwap = (close * vol).cumsum() / vol.cumsum()
        ema200 = close.ewm(span=200).mean()
        ema20 = close.ewm(span=20).mean()
        ema50 = close.ewm(span=50).mean()
        
        trend_score = 0
        if close.iloc[-1] > vwap.iloc[-1]: trend_score += 1
        else: trend_score -= 1
        if close.iloc[-1] > ema200.iloc[-1]: trend_score += 1
        else: trend_score -= 1
        if ema20.iloc[-1] > ema50.iloc[-1]: trend_score += 1
        else: trend_score -= 1

        # مدرسة 2: الزخم - RSI + Squeeze
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        bb_upper = bb_mid + bb_std*2
        bb_lower = bb_mid - bb_std*2
        
        momentum_score = 0
        if rsi.iloc[-1] > 60: momentum_score += 1
        elif rsi.iloc[-1] < 40: momentum_score -= 1
        
        if close.iloc[-1] > bb_upper.iloc[-1]: momentum_score += 1
        elif close.iloc[-1] < bb_lower.iloc[-1]: momentum_score -= 1

        # مدرسة 3: السيولة
        vol_avg = vol.rolling(50).mean()
        vol_score = 1 if vol.iloc[-1] > vol_avg.iloc[-1]*1.5 else -1 if vol.iloc[-1] < vol_avg.iloc[-1]*0.5 else 0
        
        # مدرسة 4: السلوك السعري
        body = abs(close.iloc[-1] - df['Open'].iloc[-1])
        rng = high.iloc[-1] - low.iloc[-1]
        price_score = 1 if body > rng*0.7 and close.iloc[-1] > df['Open'].iloc[-1] else -1 if body > rng*0.7 else 0
        
        total = trend_score + momentum_score + vol_score + price_score
        
        if total >= 4: return {"dir": "CALL", "score": total, "label": "شراء قوي جدا"}
        elif total >= 2: return {"dir": "CALL", "score": total, "label": "شراء"}
        elif total <= -4: return {"dir": "PUT", "score": total, "label": "بيع قوي جدا"}
        elif total <= -2: return {"dir": "PUT", "score": total, "label": "بيع"}
        else: return {"dir": "NEUTRAL", "score": total, "label": "محايد"}
    except:
        return None

def is_strong(ticker):
    tech = analyze_technical(ticker)
    if not tech: return False, None
    return tech['dir'] != "NEUTRAL", tech

# ===== الجزء الثاني: فلتر العقود الصارم - هنا تربط بياناتك الحقيقية =====
def filter_contract(contract, tech_dir):
    # contract = {'type': 'PUT'/'CALL', 'delta': 0.55, 'premium': 500000, 'spread': 2.5, 'contracts': 600, 'dte': 2, 'strike_dist': 0.01, 'is_sweep': True, 'gamma':0.08, 'theta':-0.10, 'iv_rank':50}
    
    if contract['type'] != tech_dir: return False # مخالف للاتجاه
    if not (0.40 <= contract.get('delta',0) <= 0.70): return False
    if contract.get('gamma',0) < 0.05: return False
    if contract.get('theta',0) < -0.20: return False
    if contract.get('iv_rank',0) > 70: return False
    if contract.get('premium',0) < 400000: return False
    if contract.get('spread',0) > 5: return False
    if contract.get('contracts',0) < 500: return False
    if contract.get('strike_dist',1) > 0.015: return False
    if contract.get('dte',0) < 1 or contract.get('dte',0) > 3: return False
    if not contract.get('is_sweep', False): return False
    return True

# ===== واجهة Streamlit =====
st.title("🐋 V99 - فلتر الحيتان V2 - جزأين")
st.caption("الجزء 1: تحليل فني 4 مدارس | الجزء 2: فلتر عقود صارم")

col1, col2 = st.columns(2)
with col1:
    if st.button("فحص فني لجميع الأسهم"):
        results = []
        for t in WATCHLIST_54:
            ok, tech = is_strong(t)
            if tech:
                results.append({"Ticker": t, "الاتجاه": tech['dir'], "القوة": tech['label'], "النقاط": tech['score']})
        df_res = pd.DataFrame(results).sort_values("النقاط", ascending=False)
        st.dataframe(df_res, use_container_width=True)
        
        # ارسال اقوى 3 فقط
        for r in results:
            if abs(r['النقاط']) >= 4:
                msg = f"📊 *{r['Ticker']}* - {r['القوة']} {r['الاتجاه']}\nنقاط: {r['النقاط']}/6 - فريم 30m\nالان نبحث عن عقود {r['الاتجاه']} فقط"
                send(msg)

with col2:
    st.info("المرحلة القادمة: اربط بيانات Polygon للعقود في دالة filter_contract")
    st.json({"شروط الحوت": "Premium>400k, Sweep=True, Delta 0.40-0.70, Spread<5%, DTE 1-3, قريب 1.5%"})

if is_market_open():
    st.success("السوق مفتوح - البوت يعمل")
else:
    st.warning("السوق مغلق")
