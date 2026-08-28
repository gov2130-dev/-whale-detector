import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
import pandas as pd

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"

RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V95 CLEAN")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

WATCHLIST_54 = [
    "NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META",
    "MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST",
    "GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR",
    "AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL",
    "SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL",
    "APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM",
    "SPX","NDX"
]

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
    except: pass

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_data(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d"); curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    daily=tk.history(period="20d", interval="1d")
    intraday=tk.history(period="2d", interval="5m")
    return curr, daily, intraday

def is_strong_before_move(ticker):
    try:
        curr, daily, intraday = get_data(ticker)
        if daily.empty or len(daily)<10 or curr==0: return False, "no data"
        daily['EMA20'] = daily['Close'].ewm(span=20).mean()
        daily['EMA50'] = daily['Close'].ewm(span=50).mean()
        daily['ATR5'] = (daily['High']-daily['Low']).rolling(5).mean()
        daily['ATR10'] = (daily['High']-daily['Low']).rolling(10).mean()
        ema20 = daily['EMA20'].iloc[-1]
        ema50 = daily['EMA50'].iloc[-1]
        if curr < ema20*0.995 or curr < ema50*0.98: return False, "تحت المتوسطات"
        atr5 = daily['ATR5'].iloc[-1]; atr10 = daily['ATR10'].iloc[-1]
        atr_ratio = atr5/atr10 if atr10>0 else 1
        if atr_ratio > 1.3: return False, f"انفجر {atr_ratio:.2f}"
        if atr_ratio < 0.4: return False, f"نايم {atr_ratio:.2f}"
        open_t = float(daily['Open'].iloc[-1])
        day_chg = (curr/open_t-1)*100
        if day_chg < 0.3 or day_chg > 3.8: return False, f"حركة {day_chg:.1f}%"
        high_t = float(daily['High'].iloc[-1])
        dist_high = (curr/high_t-1)*100
        if dist_high < -1.2: return False, f"بعيد عن هاي {dist_high:.1f}%"
        vol_today = float(daily['Volume'].iloc[-1])
        avg_vol = float(daily['Volume'].tail(10).mean())
        if vol_today < avg_vol*0.85: return False, f"فوليوم ضعيف"
        high_10 = float(daily['High'].tail(10).max())
        if curr > high_10*0.995: return False, "قريب قمة"
        score=0
        if 0.5 <= day_chg <= 2.5: score+=2
        if 0.7 <= atr_ratio <= 1.1: score+=2
        if vol_today > avg_vol*1.3: score+=1
        if curr > ema20: score+=1
        if score < 3: return False, f"Score {score}"
        return True, f"Score {score} | {day_chg:.1f}%"
    except: return False, "error"

def get_executable_contract(ticker):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,_=get_data(ticker)
        tk=yf.Ticker(opt_ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=float(tk.history(period="1d")['Close'].iloc[-1])
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts=chain.calls
            if opts.empty: continue
            opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.035)]
            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0
                    if last < 1.0 or last > 4.0: continue
                    if bid < 0.7: continue
                    if (ask-bid) > 0.20: continue
                    if (ask-bid)/last > 0.12: continue
                    if vol < 300 and oi < 1200: continue
                    moneyness = (curr_opt - r['strike'])/curr_opt
                    est_delta = 0.5 - moneyness*5
                    return {"ticker":ticker,"opt_ticker":opt_ticker,"curr":curr_real,"curr_opt":curr_opt,"exp":exp,"days":days,"strike":int(r['strike']),"type":"CALL","last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"delta":est_delta}
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    tg=f"{base*1.01:.1f} → {base*1.022:.1f} → {base*1.035:.1f} → {base*1.05:.1f}"
    # رسالة نظيفة - بس اللي يأثر على القرار
    return f"""${c['ticker']} - {c['strike']} CALL 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f} | Delta ~{c['delta']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%) | T3 ${c['last']*3.2:.2f} (+220%)"""

st.title("V95 - رسالة نظيفة - عقد قوي تحت $4")
ksa_now = datetime.now(RIYADH).strftime("%H:%M:%S")
ny_now = datetime.now(NY).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | نيويورك {ny_now} | {len(WATCHLIST_54)} شركة")

sent=load(SENT_FILE)
active=load(FILE)

if st.button(f"🔍 افحص {len(WATCHLIST_54)} شركة", type="primary"):
    for t in WATCHLIST_54:
        ok, reason = is_strong_before_move(t)
        if not ok:
            st.write(f"⏸️ {t}: {reason}")
            continue
        c=get_executable_contract(t)
        if not c:
            st.write(f"❌ {t}: {reason} - لا يوجد عقد تحت $4")
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل")
            continue
        msg=build_msg(c)
        st.code(msg)
        st.success(f"✅ {t} - {reason} - ${c['last']:.2f}")
        send(msg)
        sent.append(key); save(SENT_FILE, sent)
        active.append({**c, "last_price":c['curr'], "t1_hit":False})
        save(FILE, active)
        time.sleep(0.3)

st.divider()
col1,col2=st.columns(2)
with col1:
    if st.button("🗑️ تصفير المرسلة"): save(SENT_FILE, []); st.success("تم")
with col2:
    st.write(f"المرسلة اليوم: {len(sent)}")

auto=st.checkbox(f"🚀 تحديث تلقائي كل 5 دقايق - بدون تكرار")
if auto:
    status=st.empty()
    while True:
        ksa = datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
        status.write(f"⏰ الرياض {ksa} - يفحص 54 - المرسلة {len(sent)}")
        for t in WATCHLIST_54:
            ok,_=is_strong_before_move(t)
            if ok:
                c=get_executable_contract(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
        time.sleep(300)
