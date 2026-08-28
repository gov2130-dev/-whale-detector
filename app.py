import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V99.3 AUTO")
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
    daily=tk.history(period="50d", interval="1d")
    return curr, daily, tk

def is_strong_confirmed(ticker):
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<30: return False, "", 0, "no data"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        daily['EMA50']=daily['Close'].ewm(span=50).mean()
        daily['VOL_AVG']=daily['Volume'].rolling(20).mean()
        ema20=float(daily['EMA20'].iloc[-1]); ema50=float(daily['EMA50'].iloc[-1])
        vol=float(daily['Volume'].iloc[-1]); vol_avg=float(daily['VOL_AVG'].iloc[-1])
        high=float(daily['High'].iloc[-1]); low=float(daily['Low'].iloc[-1]); open_p=float(daily['Open'].iloc[-1])
        chg=(curr/open_p-1)*100
        vr=vol/vol_avg if vol_avg>0 else 0
        if curr > ema20 and ema20 > ema50 and curr >= high*0.985 and vr > 1.3 and chg > 0.5:
            return True, "CALL", vr+chg, f"CALL قوي {chg:.1f}% Vol x{vr:.1f}"
        elif curr < ema20 and ema20 < ema50 and curr <= low*1.015 and vr > 1.3 and chg < -0.5:
            return True, "PUT", vr+abs(chg), f"PUT قوي {chg:.1f}% Vol x{vr:.1f}"
        else:
            return False, "", 0, f"حيادي {chg:.1f}%"
    except: return False, "", 0, "error"

def get_strong_contract(ticker, direction):
    try:
        curr,_,tk = get_data(ticker)
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if (datetime.strptime(e,"%Y-%m-%d").date()-today).days in range(3,8)][:2]
        best=None; best_score=0
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr*1.005) & (opts['strike']<=curr*1.03)]
            else:
                opts=opts[(opts['strike']>=curr*0.97) & (opts['strike']<=curr*0.995)]
            for _, r in opts.iterrows():
                last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0); spread=ask-bid if ask>0 and bid>0 else 99
                if not (1.2 <= last <= 3.8): continue
                if bid < 0.90: continue
                if spread > 0.15: continue
                if vol < 800 and oi < 3000: continue
                if oi < 1500: continue
                score=vol*0.3+oi*0.2+(1/spread)*100
                if score>best_score:
                    best_score=score
                    best={"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"score":score}
        return best
    except: return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.015:.1f} → {base*1.03:.1f} → {base*1.05:.1f}"; emoji="🟢🔥"
    else:
        tg=f"{base*0.985:.1f} → {base*0.97:.1f} → {base*0.95:.1f}"; emoji="🔴🔥"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 💎
📅 {c['exp']} ({c['days']} يوم) | قوة {c['score']:.0f}
💵 السهم: ${c['curr']:.2f}
💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
📊 Vol {c['vol']} | OI {c['oi']} | Spread ${c['ask']-c['bid']:.2f}
🛑 وقف: ${c['last']*0.60:.2f}
🎯 اهداف: {tg}
🎯 العقد: +70% = ${c['last']*1.7:.2f} | +150% = ${c['last']*2.5:.2f}"""

# ====== الواجهة القديمة رجعت ======
st.title("V99.3 AUTO - العقود القوية المؤكدة 💎")
ksa_now=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | 54 شركة | فلتر قوي Vol>800 OI>3000")

colA,colB,colC=st.columns(3)
with colA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        if send(f"✅ V99.3 شغال - {ksa_now}\n💎 فلتر قوي مؤكد"): st.success("انرسل ✅ شيك تلجرام")
        else: st.error("فشل - تأكد من النت")
with colB:
    if st.button("🗑️ تصفير المرسلة"):
        save(SENT_FILE, []); st.success("تصفر ✅")
with colC:
    mins=st.selectbox("كل كم دقيقة يحدث؟", [2,5,10,15,30], index=1)

sent=load(SENT_FILE)
st.metric("المرسلة اليوم", len(sent))

if st.button(f"🔍 افحص الآن 54 - عقود قوية فقط", type="primary"):
    call_c=put_c=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, score, info = is_strong_confirmed(t)
        if ok and score>2:
            c=get_strong_contract(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    st.code(build_msg(c))
                    if send(build_msg(c)):
                        if c['type']=="CALL": call_c+=1
                        else: put_c+=1
                        sent.append(key); save(SENT_FILE, sent)
        prog.progress((i+1)/len(WATCHLIST_54))
    if call_c+put_c==0:
        st.warning("⏸️ ما فيه عقود قوية مؤكدة حالياً - الفلتر يحميك")
    else:
        st.success(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c}")

st.divider()
auto=st.checkbox(f"🚀 شغل التحديث التلقائي كل {mins} دقايق", value=False)

if auto:
    st.info(f"🔄 التحديث التلقائي شغال كل {mins} دقايق - لا تسكر الصفحة - {ksa_now}")
    new_found=[]
    for t in WATCHLIST_54:
        ok, direction, score, _ = is_strong_confirmed(t)
        if ok and score>2:
            c=get_strong_contract(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    if send(build_msg(c)):
                        sent.append(key); new_found.append(f"{c['type']} {t}")
    if new_found:
        save(SENT_FILE, sent)
        st.success(f"✅ أرسل تلقائي الآن: {', '.join(new_found)}")
    else:
        st.write(f"⏸️ ما فيه جديد - بنفحص بعد {mins} دقايق")
    st.caption(f"آخر فحص: {ksa_now} - بيحدث بعد {mins} دقايق")
    time.sleep(mins*60)
    st.rerun()
