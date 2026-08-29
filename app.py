import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V105 UNBLOCK")
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

# جلسة جديدة كل مرة عشان نفك الحظر
session = c_requests.Session(impersonate="chrome", timeout=20)

def is_market_open():
    now_ny = datetime.now(NY)
    if now_ny.weekday() >= 5: return False
    return 570 <= now_ny.hour*60 + now_ny.minute <= 960

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def load():
    if os.path.exists(SENT_FILE):
        try: return json.load(open(SENT_FILE))
        except: return []
    return []
def save(d): json.dump(d, open(SENT_FILE,'w'))

# كاش 10 دقايق عشان ما ننحظر
@st.cache_data(ttl=600, show_spinner=False)
def get_data_cached(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real, session=session)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d")
        curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    return curr, tk

def find_one(ticker):
    try:
        curr, tk = get_data_cached(ticker)
        if curr==0: return []
        today=datetime.now(NY).date()
        try: exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 21][:3] # قللنا لـ 3 بس عشان ما ننحظر
        except: return []
        res=[]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            try:
                chain=tk.option_chain(exp)
            except:
                time.sleep(random.uniform(1.5,2.5)) # نوم طويل عشان ياهو يفك الحظر
                continue
            for direction, opts in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if opts.empty: continue
                for _, r in opts.iterrows():
                    try:
                        oi=int(r.get('openInterest',0) or 0)
                        last=float(r.get('lastPrice',0) or 0)
                        bid=float(r.get('bid',0) or 0)
                        if last==0: last=bid
                        if last==0: last=float(r.get('ask',0) or 0)*0.85
                        if last<0.3 or last>6.0: continue
                        strike=float(r['strike'])
                        bw=abs(strike-curr)/curr*100
                        if bw>4.0: continue
                        if oi<500: continue
                        res.append({"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":strike,"last":last,"bid":bid,"vol":int(r.get('volume',0) or 0),"oi":oi,"type":direction,"bw":round(bw,2)})
                    except: continue
            time.sleep(random.uniform(1.0,1.8))
        return res
    except Exception as e:
        st.write(f"{ticker} خطأ: {e}")
        return []

def build_msg(c, reason):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    mode="LIVE" if is_market_open() else "PRE"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    return f"{emoji} {c['ticker']} {int(c['strike'])} {c['type']} {mode} - {reason}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}\nStop: ${last*0.55:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V105 UNBLOCK - يفك حظر ياهو")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | كاش 10د + نوم 1.5ث بين الطلبات")

c1,c2,c3=st.columns(3)
with c1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V105 شغال") else st.error("فشل")
with c2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر - الحين بيرجع يطلع"); st.cache_data.clear()
with c3:
    if st.button("♻️ فك الحظر Reboot"):
        st.cache_data.clear()
        st.write("سوي من فوق Manage App > Reboot App")
    st.metric("المرسلة اليوم", len(load()))
sent=load()

if st.button("🔍 افحص 54 - باي وقت - نفس الاستايل", type="primary"):
    # اهم خطوة: امسح الكاش عشان IP جديد
    st.cache_data.clear()
    prog=st.progress(0)
    all_found=[]
    status=st.empty()
    for i,t in enumerate(WATCHLIST_54):
        status.write(f"يفحص {t}... ({i+1}/54)")
        res=find_one(t)
        if res: all_found.extend(res)
        prog.progress((i+1)/len(WATCHLIST_54))
    if not all_found:
        st.error("ياهو حاظر الIP باقي - انتظر 20 دقيقة وسوي Manage App > Reboot > ثم تصفير المرسلة")
        st.info("السبب: فحصت 54 شركة بسرعة وياهو حظرك مؤقتا - الحل Reboot + انتظار")
    else:
        all_found.sort(key=lambda x: (-x['oi'], x['bw']))
        st.success(f"لقي {len(all_found)} عقد بأي وقت - بعد فك الحظر")
        for c in all_found[:30]:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            # لو تبيه يطلع حتى لو مرسل قبل شيل السطرين الجاية
            if key in sent:
                continue
            msg=build_msg(c, f"{c['type']} BW {c['bw']}%")
            st.code(msg)
            if send(msg):
                sent.append(key); save(sent)
        st.balloons()
