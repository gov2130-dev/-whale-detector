import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

# === حط التوكن الجديد هنا بعد ما تسويه ===
BOT_TOKEN="ضع_التوكن_الجديد_هنا"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V99.3 CONTRACT FORMATTED")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=20)
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
        if daily.empty or len(daily)<10: return False,"","no data"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1]); open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100; high_t=float(daily['High'].iloc[-1]); low_t=float(daily['Low'].iloc[-1])
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8:
            return True, "CALL", f"CALL قوي {chg:+.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", f"PUT قوي {chg:+.1f}%"
        else: return False,"",f"حيادي {chg:+.1f}%"
    except: return False,"","error"

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
                last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0); vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                if not (1.0 <= last <= 4.0): continue
                if bid < 0.65 or (ask-bid) > 0.25: continue
                if vol < 200 and oi < 800: continue
                return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction}
    except: pass
    return None

def build_msg_fancy(c):
    base=c['curr']; last=c['last']; strike=c['strike']; typ=c['type']; exp=c['exp']; days=c['days']
    if typ=="CALL":
        emoji="🟢"; trend="صاعد 🔼"; t1_stock=base*1.01; t2_stock=base*1.025; t3_stock=base*1.04; stop_stock=base*0.992
        t1_con=last*1.5; t2_con=last*2.3; t3_con=last*3.2
    else:
        emoji="🔴"; trend="هابط 🔽"; t1_stock=base*0.99; t2_stock=base*0.975; t3_stock=base*0.96; stop_stock=base*1.008
        t1_con=last*1.5; t2_con=last*2.3; t3_con=last*3.2
    
    return f"""{emoji} **تصفية عقد {typ} - ${c['ticker']}** {emoji}
━━━━━━━━━━━━━━━━━━━━
📊 **حالة السهم:** {trend}
💵 **سعر السهم الآن:** ${base:.2f}
🎯 **Strike:** ${strike} | 📅 **الانتهاء:** {exp} ({days} يوم)

💰 **بيانات العقد:**
├ دخول: ${last:.2f}
├ Bid: ${c['bid']:.2f} / Ask: ${c['ask']:.2f}
├ Vol: {c['vol']} | OI: {c['oi']}
└ وقف خسارة العقد: ${last*0.55:.2f} (-45%)

🎯 **أهداف السهم:**
T1: ${t1_stock:.2f} | T2: ${t2_stock:.2f} | T3: ${t3_stock:.2f}
🛑 وقف السهم: ${stop_stock:.2f}

🚀 **أهداف العقد (ربح):**
T1: ${t1_con:.2f} (+50%) 🟢
T2: ${t2_con:.2f} (+130%) 🔥
T3: ${t3_con:.2f} (+220%) 💎

⏰ {datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M:%S')} - V99.3
━━━━━━━━━━━━━━━━━━━━"""

# واجهة
st.title("V99.3 - صياغة عقود احترافية - CALL و PUT تحت $4")
ksa=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"⏰ الرياض {ksa} | {len(WATCHLIST_54)} شركة")

colA,colB=st.columns(2)
with colA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        if send(f"✅ V99.3 صياغة جديدة - {ksa}\n🟢 CALL + 🔴 PUT"): st.success("انرسل ✅")
        else: st.error("فشل - غير التوكن")
with colB:
    if st.button("🗑️ تصفير"):
        save([]); st.success("تصفر")
    st.metric("المرسلة اليوم", len(load()))

sent=load()
if st.button(f"🔍 افحص الآن 54 عقد بصياغة فخمة", type="primary"):
    call_c=put_c=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, reason = is_strong_both(t)
        if not ok: 
            prog.progress((i+1)/len(WATCHLIST_54)); continue
        c=get_contract_dir(t, direction)
        if not c: 
            prog.progress((i+1)/len(WATCHLIST_54)); continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: 
            prog.progress((i+1)/len(WATCHLIST_54)); continue
        msg=build_msg_fancy(c)
        st.code(msg, language="text")
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
        prog.progress((i+1)/len(WATCHLIST_54))
        time.sleep(0.2)
    st.success(f"تم ✅: 🟢 CALL {call_c} | 🔴 PUT {put_c}")
    if call_c+put_c>0: st.balloons()

st.divider()
mins=st.selectbox("تحديث كل", [2,5,10,15], index=1)
auto=st.checkbox(f"🚀 تحديث تلقائي كل {mins} دقايق")
if auto:
    st.info(f"🔄 شغال - {ksa}")
    new=[]
    for t in WATCHLIST_54:
        ok, direction, _ = is_strong_both(t)
        if ok:
            c=get_contract_dir(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    if send(build_msg_fancy(c)):
                        sent.append(key); new.append(f"{c['type']} {t}")
    if new: save(sent); st.success(f"أرسل: {', '.join(new)}")
    time.sleep(mins*60); st.rerun()
