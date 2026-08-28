import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
import pandas as pd
import numpy as np

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"

RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V94 STRONG BEFORE MOVE")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

# 54 شركة نفسها
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
    """
    عقد قوي قبل التفاعل - مواصفات:
    1. السهم محشور قبل انفجار
    2. فوق متوسطات
    3. RSI مش متشبع
    4. فوليوم يتجمع
    """
    try:
        curr, daily, intraday = get_data(ticker)
        if daily.empty or len(daily)<10 or curr==0:
            return False, "بيانات ناقصة"

        # مؤشرات
        daily['EMA20'] = daily['Close'].ewm(span=20).mean()
        daily['EMA50'] = daily['Close'].ewm(span=50).mean()
        daily['ATR5'] = (daily['High']-daily['Low']).rolling(5).mean()
        daily['ATR10'] = (daily['High']-daily['Low']).rolling(10).mean()

        # 1. فوق EMA20 و EMA50 - ترند صاعد
        ema20 = daily['EMA20'].iloc[-1]
        ema50 = daily['EMA50'].iloc[-1]
        if curr < ema20*0.995 or curr < ema50*0.98:
            return False, f"تحت المتوسطات - ترند ضعيف"

        # 2. محشور قبل انفجار - ATR يتقلص
        atr5 = daily['ATR5'].iloc[-1]
        atr10 = daily['ATR10'].iloc[-1]
        atr_ratio = atr5/atr10 if atr10>0 else 1
        if atr_ratio > 1.3: # تذبذب توسع خلاص انفجر
            return False, f"انفجر من قبل ATR {atr_ratio:.2f}"
        if atr_ratio < 0.4: # نايم مرة
            return False, f"نايم ATR {atr_ratio:.2f}"

        # 3. حركة اليوم 0.5% الى 3.5% - قبل التفاعل مو بعده
        open_t = float(daily['Open'].iloc[-1])
        day_chg = (curr/open_t-1)*100
        if day_chg < 0.3 or day_chg > 3.8:
            return False, f"حركة اليوم {day_chg:.1f}% - يا بدري يا متأخر"

        # 4. قريب من هاي اليوم - قوة
        high_t = float(daily['High'].iloc[-1])
        dist_high = (curr/high_t-1)*100
        if dist_high < -1.2: # بعيد عن الهاي 1.2%
            return False, f"بعيد عن هاي اليوم {dist_high:.1f}%"

        # 5. فوليوم يتجمع
        vol_today = float(daily['Volume'].iloc[-1])
        avg_vol = float(daily['Volume'].tail(10).mean())
        if vol_today < avg_vol*0.85:
            return False, f"فوليوم ضعيف {vol_today/avg_vol:.1f}x"

        # 6. مسافة للقمة
        high_10 = float(daily['High'].tail(10).max())
        if curr > high_10*0.995:
            return False, "قريب من قمة 10 ايام"

        # تقييم قوة
        score = 0
        if 0.5 <= day_chg <= 2.5: score+=2 # افضل منطقة دخول
        if 0.7 <= atr_ratio <= 1.1: score+=2 # محشور جاهز
        if vol_today > avg_vol*1.3: score+=1
        if curr > ema20: score+=1

        if score < 3:
            return False, f"Score {score} ضعيف"

        return True, f"قوي قبل انفجار Score {score} | يوم {day_chg:.1f}% | ATR {atr_ratio:.2f} | Vol {vol_today/avg_vol:.1f}x"

    except Exception as e:
        return False, str(e)

def get_executable_contract(ticker):
    """عقد قابل للتنفيذ - مو تحوط"""
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
            if not (1 <= days <= 10): continue # 1-10 ايام
            chain=tk.option_chain(exp)
            opts=chain.calls
            if opts.empty: continue

            # عقد قوي = قريب ATM 0.5% الى 3% OTM فقط
            # دلتا 0.40 - 0.65
            opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.035)]

            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0

                    # شروط العقد القابل للتنفيذ
                    if last < 1.0 or last > 4.0: continue # تحت 4 اللي طلبت
                    if bid < 0.7: continue # عشان التنفيذ
                    if (ask-bid) > 0.20: continue # سبريد ضيق بالدولار مو نسبة
                    if (ask-bid)/last > 0.12: continue # سبريد <12%
                    if vol < 300 and oi < 1200: continue # سيولة عالية
                    if last/bid > 1.8: continue # bid وهمي

                    # هذا عقد قوي - دلتا تقريبا
                    moneyness = (curr_opt - r['strike'])/curr_opt
                    est_delta = 0.5 - moneyness*5 # تقدير سريع

                    return {
                        "ticker":ticker,"opt_ticker":opt_ticker,
                        "curr":curr_real,"curr_opt":curr_opt,
                        "exp":exp,"days":days,"strike":int(r['strike']),
                        "type":"CALL","last":last,"bid":bid,"ask":ask,
                        "vol":vol,"oi":oi,"delta":est_delta
                    }
                except: continue
    except: pass
    return None

def build_msg(c, reason):
    base=c['curr']
    tg=f"{base*1.01:.1f} → {base*1.022:.1f} → {base*1.035:.1f} → {base*1.05:.1f}"
    return f"""${c['ticker']} - {c['strike']} CALL 🔥
📅 {c['exp']} ({c['days']} يوم) عقد قوي قابل للتنفيذ
💵 السعر: ${c['curr']:.2f} | Delta ~{c['delta']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f} - لا تترك العقد يصفر
📊 Vol {c['vol']} | OI {c['oi']} | سبريد ضيق

📈 الحالة: {reason}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%) | T3 ${c['last']*3.2:.2f} (+220%)

🐋 دخول قبل التفاعل - تنفيذ مباشر
🔥 GOLDEN EXECUTABLE"""

st.title("V94 - عقود قوية قبل التفاعل - تحت $4")

sent=load(SENT_FILE)
active=load(FILE)
ksa=datetime.now(RIYADH).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa} | 54 شركة | عقد قوي = ATM + سيولة عالية + قبل الانفجار")

if st.button(f"🔍 افحص 54 - فقط القوي قبل التفاعل", type="primary"):
    for t in WATCHLIST_54:
        ok, reason = is_strong_before_move(t)
        if not ok:
            st.write(f"⏸️ {t}: {reason}")
            continue
        c=get_executable_contract(t)
        if not c:
            st.write(f"❌ {t}: {reason} - بس ما فيه عقد تحت $4 سيولته عالية")
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: 
            st.write(f"⏭️ {t} مرسل")
            continue
        msg=build_msg(c, reason)
        st.markdown(f'<div style="background:#182533; border:3px solid #00e6a8; border-radius:18px; padding:22px; max-width:540px; margin:12px auto; color:white; font-size:18px; line-height:1.9; white-space:pre-wrap;">{msg}</div>', unsafe_allow_html=True)
        st.success(f"✅ {t} - {reason} - ${c['last']:.2f} Delta {c['delta']:.2f}")
        send(msg)
        sent.append(key); save(SENT_FILE, sent)
        active.append({**c, "last_price":c['curr'], "t1_hit":False, "targets_stock":[c['curr']*1.015]})
        save(FILE, active)
        time.sleep(0.4)

st.divider()
auto=st.checkbox("🚀 تحديث كل 5 دقايق - فقط القوي قبل الانفجار")
if auto:
    status=st.empty()
    while True:
        ksa = datetime.now(RIYADH).strftime("%H:%M:%S")
        status.write(f"⏰ {ksa} - يفحص 54 - المرسلة {len(sent)}")
        for t in WATCHLIST_54:
            ok,_=is_strong_before_move(t)
            if ok:
                c=get_executable_contract(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c, "تحديث تلقائي - قبل انفجار"))
                        sent.append(key); save(SENT_FILE, sent)
        time.sleep(300)
