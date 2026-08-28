import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="ضع_توكنك_الجديد_هنا"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V98 FORMATTED")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def load(): return json.load(open(SENT_FILE)) if os.path.exists(SENT_FILE) else []
def save(d): json.dump(d, open(SENT_FILE,'w'))

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
            return True, "CALL", f"CALL {chg:+.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", f"PUT {chg:+.1f}%"
        else:
            return False, "", f"حيادي {chg:+.1f}%"
    except: return False, "", "error"

# نفس دالة V98 بالحرف - ما لمستها
def get_contract_dir(ticker, direction):
    try:
        curr_real,_,tk = get_data(ticker)
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_real*1.002) & (opts['strike']<=curr_real*1.04)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_real*0.96) & (opts['strike']<=curr_real*0.998)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if not (1.0 <= last <= 4.0): continue
                    if bid < 0.65: continue
                    if (ask-bid) > 0.25: continue
                    if vol < 200 and oi < 800: continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction}
                except: continue
    except: pass
    return None

def build_msg_fancy(c, reason):
    base=c['curr']; last=c['last']
    if c['type']=="CALL":
        emoji="🟢"; trend="صاعد"; t_stock=f"{base*1.01:.1f} → {base*1.025:.1f} → {base*1.04:.1f}"; stop=f"{base*0.992:.1f}"
    else:
        emoji="🔴"; trend="هابط"; t_stock=f"{base*0.99:.1f} → {base*0.975:.1f} → {base*0.96:.1f}"; stop=f"{base*1.008:.1f}"
    
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥 {reason}
📅 {c['exp']} ({c['days']} يوم) | 💵 السهم ${base:.2f} ({trend})

💰 دخول العقد: ${last:.2f} | Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f}
📊 Vol {c['vol']} OI {c['oi']}
🛑 وقف العقد: ${last*0.55:.2f} (-45%) | وقف السهم: ${stop}

🎯 أهداف السهم: {t_stock}
🚀 أهداف العقد: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"""

# واجهة
st.title("V98 الأصلي + صياغة فخمة")
ksa=datetime.now(RIYADH).strftime("%H:%M:%S")
st.caption(f"⏰ {ksa} | 54 شركة")

c1,c2=st.columns(2)
with c1:
    if st.button("📨 اختبار تلجرام", type="primary"):
        if send(f"✅ V98 شغال - {ksa}"): st.success("انرسل")
        else: st.error("بدل التوكن - 401")
with c2:
    if st.button("🗑️ تصفير"):
        save([]); st.success("تصفر")
    st.metric("المرسلة", len(load()))

sent=load()
if st.button(f"🔍 افحص 54 - نفس V98", type="primary"):
    call_c=put_c=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, reason = is_strong_both(t)
        if not ok:
            st.write(f"⏸️ {t}: {reason}")
            prog.progress((i+1)/len(WATCHLIST_54))
            continue
        c=get_contract_dir(t, direction)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد 1-4$")
            prog.progress((i+1)/len(WATCHLIST_54))
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل")
            prog.progress((i+1)/len(WATCHLIST_54))
            continue
        msg=build_msg_fancy(c, reason)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
            st.success(f"✅ {t} {direction}")
        prog.progress((i+1)/len(WATCHLIST_54))
        time.sleep(0.3)
    st.balloons()
    st.info(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c}")

mins=st.selectbox("تحديث كل", [2,5,10,15], index=1)
auto=st.checkbox(f"🚀 تحديث تلقائي كل {mins} دقايق")
if auto:
    st.info("شغال...")
    for t in WATCHLIST_54:
        ok, direction, reason = is_strong_both(t)
        if ok:
            c=get_contract_dir(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    if send(build_msg_fancy(c, reason)):
                        sent.append(key)
    save(sent)
    time.sleep(mins*60)
    st.rerun()
