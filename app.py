import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

# تثبيت: pip install streamlit-autorefresh
try:
    from streamlit_autorefresh import st_autorefresh
    HAS_REFRESH=True
except:
    HAS_REFRESH=False

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V99 AUTO")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
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
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8:
            return True, "CALL", f"CALL {chg:.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", f"PUT {chg:.1f}%"
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
                opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.04)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_opt*0.96) & (opts['strike']<=curr_opt*0.998)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if not (1.0 <= last <= 4.0): continue
                    if bid < 0.65 or (ask-bid) > 0.25: continue
                    if vol < 200 and oi < 800: continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"type":direction}
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.01:.1f} → {base*1.025:.1f} → {base*1.04:.1f}"; emoji="🟢"
    else:
        tg=f"{base*0.99:.1f} → {base*0.975:.1f} → {base*0.96:.1f}"; emoji="🔴"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم: {tg}
🎯 اهداف العقد: T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%)"""

# ===== الواجهة =====
st.title("V99 - تحديث تلقائي AUTO - CALL + PUT")
ksa_now=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
ny_now=datetime.now(NY).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | نيويورك {ny_now} | 54 شركة")

colA,colB,colC,colD=st.columns(4)
with colA:
    if st.button("📨 اختبار تلجرام"):
        if send(f"✅ V99 AUTO شغال - {ksa_now}\n🟢 CALL + 🔴 PUT + تحديث تلقائي"): st.success("انرسل")
        else: st.error("فشل")
with colB:
    if st.button("🗑️ تصفير"):
        save(SENT_FILE, []); st.success("تصفر")
with colC:
    mins=st.selectbox("كل كم دقيقة يحدث؟", [2,5,10,15,30], index=1)
with colD:
    st.metric("المرسلة اليوم", len(load(SENT_FILE)))

sent=load(SENT_FILE)

# ===== زر فحص يدوي =====
if st.button(f"🔍 افحص الآن 54 - CALL + PUT", type="primary"):
    call_c=0; put_c=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, reason = is_strong_both(t)
        if ok:
            c=get_contract_dir(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    msg=build_msg(c)
                    st.code(msg)
                    if send(msg):
                        if c['type']=="CALL": call_c+=1
                        else: put_c+=1
                        sent.append(key); save(SENT_FILE, sent)
        prog.progress((i+1)/len(WATCHLIST_54))
    st.success(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c} | الرياض {ksa_now}")

st.divider()

# ===== التحديث التلقائي الجديد =====
auto=st.checkbox(f"🚀 شغل التحديث التلقائي كل {mins} دقايق - حتى لو قفلت الصفحة يحدث لحاله", value=False)

if auto:
    if HAS_REFRESH:
        st_autorefresh(interval=mins*60*1000, key="auto_refresh_v99")
        st.info(f"🔄 التحديث التلقائي شغال كل {mins} دقايق - الصفحة بتحدث لحالها - {ksa_now}")
        
        # يفحص ويرسل تلقائي مع كل تحديث
        new_found=[]
        for t in WATCHLIST_54:
            ok, direction, _ = is_strong_both(t)
            if ok:
                c=get_contract_dir(t, direction)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key)
                        new_found.append(f"{c['type']} {t} {c['strike']}")
        
        if new_found:
            save(SENT_FILE, sent)
            st.success(f"✅ أرسل تلقائي: {', '.join(new_found)}")
        else:
            st.write(f"⏸️ ما فيه عقود جديدة - {ksa_now} - بنفحص بعد {mins} دقايق")
        
        st.caption(f"آخر فحص: {ksa_now} | المرسلة: {len(sent)}")
    else:
        st.warning("ركب المكتبة: pip install streamlit-autorefresh")
        # fallback للطريقة القديمة
        status=st.empty()
        while True:
            ksa = datetime.now(RIYADH).strftime("%H:%M:%S")
            status.write(f"⏰ {ksa} - يفحص")
            time.sleep(mins*60)
            st.rerun()
