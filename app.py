import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V102 TIMELESS")
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
session = c_requests.Session(impersonate="chrome")

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
def get_data(t):
    real=TICKER_MAP.get(t,t)
    tk=yf.Ticker(real, session=session)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d")
        curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    return curr, tk

def find_contracts_anytime(ticker):
    """يبحث باي وقت - لا يهم السوق فاتح ولا مقفل - لا يهم جمعة ولا سبت"""
    try:
        curr, tk = get_data(ticker)
        if curr==0: return []
        today=datetime.now(NY).date()
        # 0 الى 45 يوم - يومي واسبوعي وشهري - باي وقت
        try: all_exps = [e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 45][:6]
        except: return []

        results=[]
        for exp in all_exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            try: chain=tk.option_chain(exp)
            except: 
                time.sleep(0.6)
                continue
            # نفحص CALL و PUT مع بعض باي وقت
            for direction, opts in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if opts.empty: continue
                for _, r in opts.iterrows():
                    try:
                        oi=int(r.get('openInterest',0) or 0)
                        last=float(r.get('lastPrice',0) or 0)
                        if last==0: continue
                        strike=float(r['strike'])
                        bw=abs(strike-curr)/curr*100
                        # شروطك الصارمة الثابتة فقط - باي وقت
                        if oi < 8000: continue
                        if not (0.5 <= last <= 5.0): continue
                        if bw > 2.5: continue
                        # اذا انطبقت الشروط يطلع مهما كان الوقت
                        results.append({"ticker":ticker,"type":direction,"strike":strike,"curr":curr,"exp":exp,"days":days,"oi":oi,"last":last,"bw":round(bw,2),"vol":int(r.get('volume',0) or 0)})
                    except: continue
            time.sleep(0.35)
        return results
    except: return []

st.title("V102 TIMELESS - يبحث بأي وقت")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | نيويورك {datetime.now(NY).strftime('%H:%M')} | بحث بأي لحظة 0-45 يوم")
st.sidebar.markdown("### شروطك بأي وقت\nOI > 8000\nBW < 2.5%\n0.5 - 5$\nDTE 0-45\nيطلع مهما كان وقت البحث")

col1,col2=st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V102 TIMELESS شغال") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر")
    st.metric("المرسلة اليوم", len(load()))
sent=load()

if st.button("🔍 افحص 54 - بأي وقت - شروطك فقط", type="primary"):
    prog=st.progress(0)
    all_found=[]
    for i,t in enumerate(WATCHLIST_54):
        found=find_contracts_anytime(t)
        all_found.extend(found)
        prog.progress((i+1)/len(WATCHLIST_54))
        if found: st.write(f"✅ {t}: لقي {len(found)} عقد يحقق شروطك بأي وقت")
    if not all_found:
        st.error("ما لقي عقود تحقق OI>8000 + BW<2.5% + 0.5-5$ - مو مشكلة جمعة - يعني فعلا ما فيه تجميع حوت الان حسب شروطك")
    else:
        # نرتب بالاقرب للسعر ثم اعلى OI
        all_found.sort(key=lambda x: (x['bw'], -x['oi']))
        st.success(f"تم ✅ {len(all_found)} عقد يحقق شروطك بأي وقت - من 0 الى 45 يوم")
        sent_count=0
        for c in all_found[:30]:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            if key in sent: continue
            msg=f"{'🟢' if c['type']=='CALL' else '🔴'} {c['ticker']} {c['strike']} {c['type']} - {c['days']}d BW {c['bw']}% OI {c['oi']:,}\nStock ${c['curr']:.2f} Exp {c['exp']} Entry ${c['last']:.2f} Vol {c['vol']}\nTarget ${c['last']*2.0:.2f} (+100%)"
            st.code(msg)
            if send(msg):
                sent_count+=1
                sent.append(key); save(sent)
        st.balloons()
        st.info(f"انرسل {sent_count} جديد")
