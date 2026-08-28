import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V97 FIX SEND")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        st.write(f"Telegram response: {r.status_code} - {r.text[:200]}") # للتشخيص
        return r.status_code==200
    except Exception as e:
        st.error(f"Telegram error: {e}")
        return False

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

def is_strong(ticker):
    # فلتر خفيف جدا عشان يطلع عقود - بنختبر الإرسال أول
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty: return False, "no data"
        open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100
        if chg < -2 or chg > 5: return False, f"{chg:.1f}%"
        return True, f"{chg:.1f}%"
    except: return False, "error"

def get_contract_any(ticker):
    """يجيب أي عقد تحت $4 بدون شروط سبريد صارمة - للاختبار"""
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,tk = get_data(ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=curr_real
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (0 <= days <= 10): continue
            try:
                chain=tk.option_chain(exp)
                opts=chain.calls
                opts=opts[(opts['strike']>=curr_opt*0.98) & (opts['strike']<=curr_opt*1.05)]
                for _, r in opts.head(10).iterrows():
                    last=float(r['lastPrice'] or 0)
                    if 0.5 <= last <= 4.0:
                        bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                        return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"delta":0.5}
            except: continue
    except Exception as e:
        st.write(f"{ticker} contract error {e}")
    return None

def build_msg(c):
    base=c['curr']
    return f"""${c['ticker']} - {c['strike']} CALL 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف: {base*1.02:.1f} → {base*1.04:.1f}
T1 ${c['last']*1.5:.2f}"""

# --- واجهة التشخيص ---
st.title("V97 - إصلاح الإرسال")
ksa=datetime.now(RIYADH).strftime("%H:%M:%S")
st.caption(f"⏰ الرياض {ksa} | البوت: {BOT_TOKEN[:10]}... | الشات: {CHAT_ID}")

colA,colB,colC = st.columns(3)
with colA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        ok=send(f"✅ اختبار V97 - الرياض {ksa}\nالموقع شغال ويرسل")
        if ok: st.success("تم الإرسال! شيك تلجرام")
        else: st.error("فشل - تأكد من BOT_TOKEN و CHAT_ID")

with colB:
    if st.button("🗑️ تصفير المرسلة"):
        save(SENT_FILE, [])
        save(FILE, [])
        st.success("تصفر - الآن بيرسل كل شي من جديد")

with colC:
    st.metric("المرسلة اليوم", len(load(SENT_FILE)))

st.divider()

sent=load(SENT_FILE)

if st.button(f"🔍 افحص الآن 54 شركة - فلتر خفيف عشان يرسل", type="primary"):
    count=0
    for t in WATCHLIST_54:
        ok, reason = is_strong(t)
        if not ok:
            st.write(f"⏸️ {t}: {reason}")
            continue
        c=get_contract_any(t)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد تحت $4")
            continue
        
        key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل اليوم - اضغط تصفير لو تبيه يرسل")
            continue

        msg=build_msg(c)
        st.code(msg)
        if send(msg):
            st.success(f"✅ {t} انرسل تلجرام")
            sent.append(key); save(SENT_FILE, sent)
            count+=1
        else:
            st.error(f"❌ {t} فشل إرسال تلجرام")
        time.sleep(0.5)
    
    if count==0:
        st.warning("ما لقى عقود - السبب الفلتر أو yfinance بطيء - جرب مرة ثانية بعد دقيقة")

# تحديث تلقائي
st.divider()
auto=st.checkbox("🚀 شغل التحديث كل 5 دقايق")
if auto:
    status=st.empty()
    while True:
        ksa = datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
        status.write(f"⏰ {ksa} - يفحص 54")
        for t in WATCHLIST_54[:10]: # 10 بس في التلقائي عشان السرعة
            ok,_=is_strong(t)
            if ok:
                c=get_contract_any(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
        time.sleep(300)
