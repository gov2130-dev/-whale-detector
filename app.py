import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V98 CALL PUT")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_data(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d"); curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    daily=tk.history(period="20d", interval="1d")
    return curr, daily, tk

def is_strong_both(ticker):
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False, "", "no data"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100
        high_t=float(daily['High'].iloc[-1])
        low_t=float(daily['Low'].iloc[-1])
        
        # CALL قوي
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8:
            return True, "CALL", f"CALL قوي {chg:.1f}%"
        # PUT قوي
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", f"PUT قوي {chg:.1f}%"
        else:
            return False, "", f"حيادي {chg:.1f}%"
    except: return False, "", "error"

def get_contract_dir(ticker, direction):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,tk = get_data(ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=curr_real
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.04)]
                opts=opts.sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_opt*0.96) & (opts['strike']<=curr_opt*0.998)]
                opts=opts.sort_values('strike', ascending=False)
            
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0)
                    bid=float(r['bid'] or 0)
                    ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0)
                    oi=int(r['openInterest'] or 0)
                    if not (1.0 <= last <= 4.0): continue
                    if bid < 0.65: continue
                    if (ask-bid) > 0.25: continue
                    if vol < 200 and oi < 800: continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"type":direction}
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.01:.1f} → {base*1.025:.1f} → {base*1.04:.1f}"
        emoji="🟢"
    else:
        tg=f"{base*0.99:.1f} → {base*0.975:.1f} → {base*0.96:.1f}"
        emoji="🔴"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%)"""

# واجهة
st.title("V98 - CALL و PUT - عقود قوية تحت $4")
ksa=datetime.now(RIYADH).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa} | {len(WATCHLIST_54)} شركة")

colA,colB,colC=st.columns(3)
with colA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        if send(f"✅ اختبار V98 CALL+PUT - {ksa}\n🟢 CALL و 🔴 PUT شغال"): st.success("انرسل - شيك تلجرام")
        else: st.error("فشل الإرسال")
with colB:
    if st.button("🗑️ تصفير المرسلة"):
        save(SENT_FILE, []); st.success("تصفر")
with colC:
    st.metric("المرسلة اليوم", len(load(SENT_FILE)))

st.divider()
sent=load(SENT_FILE)

if st.button(f"🔍 افحص 54 - CALL + PUT", type="primary"):
    call_c=0; put_c=0
    for t in WATCHLIST_54:
        ok, direction, reason = is_strong_both(t)
        if not ok:
            st.write(f"⏸️ {t}: {reason}")
            continue
        c=get_contract_dir(t, direction)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد")
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} {direction} مرسل")
            continue
        msg=build_msg(c)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            st.success(f"✅ {t} {direction} - {reason}")
            sent.append(key); save(SENT_FILE, sent)
        time.sleep(0.4)
    st.balloons()
    st.info(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c}")

auto=st.checkbox("🚀 تحديث تلقائي كل 5 دقايق CALL+PUT")
if auto:
    status=st.empty()
    while True:
        ksa = datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
        status.write(f"⏰ {ksa} - يفحص 54 CALL+PUT - المرسلة {len(sent)}")
        for t in WATCHLIST_54:
            ok, direction, _ = is_strong_both(t)
            if ok:
                c=get_contract_dir(t, direction)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
        time.sleep(300)
