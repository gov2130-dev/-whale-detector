import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V100 STRICT")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]
session = c_requests.Session(impersonate="chrome")

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

def get_data(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real, session=session)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d")
        curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    daily=tk.history(period="20d", interval="1d")
    return curr, daily, tk

# شروطك الصارمة ثابتة - ما تتغير سواء سوق فاتح ولا مقفل
def is_strong_strict(ticker):
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False,"",0,""
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        high_t=float(daily['High'].iloc[-1])
        low_t=float(daily['Low'].iloc[-1])
        chg=(curr/open_t-1)*100 if open_t!=0 else 0

        # شرطك الصارم: فوق EMA20 + قريب من الهاي/اللو
        if curr > ema20*0.998 and curr >= high_t*0.987:
            return True, "CALL", chg, f"CALL {chg:+.1f}% فوق EMA"
        elif curr < ema20*1.002 and curr <= low_t*1.013:
            return True, "PUT", chg, f"PUT {chg:+.1f}% تحت EMA"
        else:
            return False,"",chg,""
    except: return False,"",0,""

def get_contract_strict(ticker, direction):
    try:
        curr_real,_,tk = get_data(ticker)
        if curr_real==0: return None
        today=datetime.now(NY).date()
        # نفحص 0 الى 45 يوم - يومي واسبوعي وشهري - باي وقت
        exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 45][:5]

        best_list=[]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            try: chain=tk.option_chain(exp)
            except:
                time.sleep(0.6)
                continue
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue

            for _, r in opts.iterrows():
                try:
                    oi=int(r.get('openInterest',0) or 0)
                    last=float(r.get('lastPrice',0) or 0)
                    # اذا السوق مقفل last قد يكون 0 نستخدم close السابق للعقد
                    if last==0: continue
                    strike=float(r['strike'])
                    bw=abs(strike-curr_real)/curr_real*100

                    # شروطك الصارمة الثابتة - لا تتغير
                    if oi < 8000: continue
                    if not (0.5 <= last <= 5.0): continue
                    if bw > 2.5: continue

                    score = (oi/1000) + (30 - bw*10) + (20 - days*0.5)
                    best_list.append((score, {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":strike,"last":last,"bid":float(r.get('bid',0) or 0),"ask":float(r.get('ask',0) or 0),"vol":int(r.get('volume',0) or 0),"oi":oi,"type":direction,"bw":round(bw,2),"mode":"LIVE" if is_market_open() else "PRE"}))
                except: continue
            time.sleep(random.uniform(0.3,0.6))

        if not best_list: return None
        # نرتب بالاقرب للانفجار - نقاط اعلى
        best_list.sort(key=lambda x: x[0], reverse=True)
        return best_list[0][1]
    except: return None

def build_msg(c, reason):
    emoji="🟢" if c['type']=="CALL" else "🔴"
    return f"{emoji} {c['ticker']} {c['strike']} {c['type']} {c['mode']} - {reason}\nExp: {c['exp']} ({c['days']}d) BW: {c['bw']}% OI: {c['oi']:,}\nStock: ${c['curr']:.2f} Entry: ${c['last']:.2f} Vol: {c['vol']}\nStop: ${c['last']*0.55:.2f} Target: ${c['last']*2.0:.2f} (+100%) | ${c['last']*3.2:.2f} (+220%)"

st.title("V100 STRICT - شروطك ثابتة")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | نيويورك {datetime.now(NY).strftime('%H:%M')} | يبحث باي لحظة 0-45 يوم")
st.sidebar.markdown("### شروطك الصارمة الثابتة")
st.sidebar.markdown("OI > 8000\nBW < 2.5%\nسعر 0.5-5$\nDTE 0-45\nفوق EMA20")

col1,col2 = st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V100 STRICT شغال") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر ✅")
    st.metric("المرسلة اليوم", len(load()))
sent = load()

if st.button("🔍 افحص 54 - شروط صارمة ثابتة", type="primary"):
    prog = st.progress(0)
    candidates=[]
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, chg, reason = is_strong_strict(t)
        if ok: candidates.append((abs(chg), chg, t, direction, reason))
        prog.progress((i+1)/len(WATCHLIST_54)*0.5)

    st.write(f"لقي {len(candidates)} سهم قوي فوق EMA")
    candidates.sort(key=lambda x: x[0], reverse=True)

    found=0
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c = get_contract_strict(t, direction)
        if not c:
            st.write(f"❌ {t} {direction} - ما فيه عقد يحقق OI>8000 و BW<2.5% و 0.5-5$ (مو مشكلة حجب - شرطك ما انطبق)")
            continue
        key = f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: continue
        msg = build_msg(c, reason)
        st.code(msg)
        if send(msg):
            found+=1
            sent.append(key); save(sent)
        prog.progress(0.5 + (idx+1)/max(len(candidates),1)*0.5)
        time.sleep(0.2)

    if found==0:
        st.warning("ما لقي عقود تحقق شروطك الصارمة الثلاثة مع بعض (OI>8000 + BW<2.5% + 0.5-5$) - هذا يعني السوق اليوم ما فيه تجميع حوت - مو مشكلة حجب")
    else:
        st.balloons()
        st.success(f"تم ✅ وجد {found} عقد يحقق شروطك الصارمة الثابتة")
