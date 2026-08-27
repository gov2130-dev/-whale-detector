import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V96 TECHNICAL LINKED")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
    except: pass
def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_data(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try: curr=float(tk.fast_info['last_price'])
    except: curr=float(tk.history(period="1d")['Close'].iloc[-1])
    daily=tk.history(period="30d", interval="1d")
    intraday=tk.history(period="5d", interval="5m")
    return curr, daily, intraday, tk

def analyze_technical(ticker):
    """
    يرجع: هل قوي + اسم الاستراتيجية + سبب فني
    """
    curr, daily, intraday, _ = get_data(ticker)
    if daily.empty or len(daily)<20: return False, "", "بيانات ناقصة"

    # مؤشرات
    daily['EMA20'] = daily['Close'].ewm(span=20).mean()
    daily['EMA50'] = daily['Close'].ewm(span=50).mean()
    daily['SMA20'] = daily['Close'].rolling(20).mean()
    daily['STD20'] = daily['Close'].rolling(20).std()
    daily['Upper'] = daily['SMA20'] + daily['STD20']*2
    daily['Lower'] = daily['SMA20'] - daily['STD20']*2
    daily['ATR5'] = (daily['High']-daily['Low']).rolling(5).mean()
    daily['ATR20'] = (daily['High']-daily['Low']).rolling(20).mean()
    daily['VolAvg10'] = daily['Volume'].rolling(10).mean()

    ema20 = daily['EMA20'].iloc[-1]
    ema50 = daily['EMA50'].iloc[-1]
    upper = daily['Upper'].iloc[-1]
    lower = daily['Lower'].iloc[-1]
    atr5 = daily['ATR5'].iloc[-1]
    atr20 = daily['ATR20'].iloc[-1]
    
    # شروط اساسية
    open_t = float(daily['Open'].iloc[-1])
    day_chg = (curr/open_t-1)*100
    if day_chg < 0.3 or day_chg > 4.0: return False, "", f"حركة {day_chg:.1f}%"
    if curr < ema20*0.99: return False, "", "تحت EMA20"

    # VWAP من الـ 5m
    try:
        intraday['VWAP'] = (intraday['Close']*intraday['Volume']).cumsum() / intraday['Volume'].cumsum()
        vwap = float(intraday['VWAP'].iloc[-1])
        above_vwap = curr > vwap
    except:
        above_vwap = True
        vwap = curr

    vol_today = float(daily['Volume'].iloc[-1])
    vol_avg = float(daily['VolAvg10'].iloc[-1])
    bb_width = (upper-lower)/curr*100  # عرض البولنجر

    # 1. SQUEEZE انفجار
    if bb_width < 3.5 and atr5/atr20 < 0.85 and vol_today > vol_avg*1.2 and above_vwap:
        return True, "SQUEEZE انفجار وشيك 🔥", f"البولنجر ضيق {bb_width:.1f}% + ATR يتقلص + فوق VWAP"

    # 2. FLAG علم
    high_10 = float(daily['High'].tail(10).max())
    low_10 = float(daily['Low'].tail(10).min())
    range_10 = (high_10-low_10)/curr*100
    if range_10 < 4.5 and curr > high_10*0.985 and vol_today > vol_avg*1.3:
        return True, "FLAG اختراق علم 🚩", f"تجميع ضيق {range_10:.1f}% 10 أيام + قرب هاي + فوليوم"

    # 3. VWAP اختراق مؤسسات
    if above_vwap and curr > vwap*1.002 and vol_today > vol_avg*1.5 and day_chg > 1.0:
        return True, "VWAP اختراق مؤسسات 🐋", f"فوق VWAP {vwap:.2f} + فوليوم {vol_today/vol_avg:.1f}x + قوة {day_chg:.1f}%"

    # 4. GOLDEN ترند جديد
    if curr > ema20 > ema50 and daily['EMA20'].iloc[-2] < daily['EMA50'].iloc[-2] or (curr > ema20*1.01 and curr > ema50*1.02):
        if vol_today > vol_avg:
            return True, "GOLDEN ترند صاعد ✨", f"فوق EMA20 {ema20:.1f} و EMA50 {ema50:.1f} + تقاطع"

    return False, "", "ما فيه نمط قوي"

def get_contract(ticker):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,_,_ = get_data(ticker)
        tk=yf.Ticker(opt_ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=float(tk.history(period="1d")['Close'].iloc[-1])
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            opts=tk.option_chain(exp).calls
            opts=opts[(opts['strike']>=curr_opt*1.001) & (opts['strike']<=curr_opt*1.035)]
            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if last < 1.0 or last > 4.0: continue
                    if bid < 0.7 or (ask-bid)>0.20 or (ask-bid)/last>0.12: continue
                    if vol < 250 and oi < 1000: continue
                    delta = 0.5 - ((curr_opt - r['strike'])/curr_opt)*5
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"delta":delta}
                except: continue
    except: pass
    return None

def build_msg(c, pattern, tech):
    base=c['curr']
    tg=f"{base*1.01:.1f} → {base*1.022:.1f} → {base*1.035:.1f}"
    return f"""${c['ticker']} - {c['strike']} CALL 🔥
{pattern}
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f} | Delta {c['delta']:.2f}
📊 {tech}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم:
{tg}
🎯 اهداف العقد: T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%)"""

st.title("V96 - عقد مربوط بحدث فني قوي")
ksa=datetime.now(RIYADH).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa} | 54 شركة | عقد + استراتيجية فنية")

sent=load(SENT_FILE)
if st.button(f"🔍 افحص 54 - عقود مربوطة بتحليل فني", type="primary"):
    for t in WATCHLIST_54:
        ok, pattern, tech = analyze_technical(t)
        if not ok:
            st.write(f"⏸️ {t}: {tech}")
            continue
        c=get_contract(t)
        if not c:
            st.write(f"❌ {t}: {pattern} - بس ما فيه عقد تحت $4")
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: continue
        msg=build_msg(c, pattern, tech)
        st.code(msg)
        st.success(f"✅ {t} - {pattern}")
        send(msg)
        sent.append(key); save(SENT_FILE, sent)
        time.sleep(0.3)
