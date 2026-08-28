import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="ضع_توكنك_الجديد_هنا"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V98 SMART FINAL")

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def is_market_open():
    now_ny = datetime.now(NY)
    if now_ny.weekday() >= 5: return False
    return 570 <= now_ny.hour*60 + now_ny.minute <= 960

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
        if daily.empty or len(daily)<10: return False,"",0,"no data"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1]); open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100; high_t=float(daily['High'].iloc[-1]); low_t=float(daily['Low'].iloc[-1])
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8:
            return True, "CALL", chg, f"CALL {chg:+.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", chg, f"PUT {chg:+.1f}%"
        else: return False,"",chg,f"حيادي {chg:+.1f}%"
    except: return False,"",0,"error"

def get_contract_dir(ticker, direction):
    market_open = is_market_open()
    try:
        curr_real,_,tk = get_data(ticker)
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:4]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (0 <= days <= (10 if market_open else 14)): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_real*0.98) & (opts['strike']<=curr_real*1.06)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_real*0.94) & (opts['strike']<=curr_real*1.02)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if market_open:
                        if not (1.0 <= last <= 4.0): continue
                        if bid < 0.65: continue
                        if (ask-bid) > 0.25: continue
                        if vol < 200 and oi < 800: continue
                    else:
                        if not (0.40 <= last <= 6.0): continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction, "mode":"LIVE" if market_open else "PRE"}
                except: continue
    except: pass
    return None

def build_msg(c, reason):
    base=c['curr']; last=c['last']
    emoji="🟢" if c['type']=="CALL" else "🔴"
    t1=base*1.01 if c['type']=="CALL" else base*0.99
    t2=base*1.025 if c['type']=="CALL" else base*0.975
    t3=base*1.04 if c['type']=="CALL" else base*0.96
    return f"""{emoji} {c['ticker']} {c['strike']} {c['type']} {c['mode']} - {reason}
Exp: {c['exp']} ({c['days']}d) Stock: ${base:.2f}
Entry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}
Stop: ${last*0.55:.2f}
Target Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}
Target Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"""

# واجهة
st.title("V98 SMART FINAL - مرتب من الأقوى")
ksa_now=datetime.now(RIYADH).strftime("%H:%M:%S")
ny_now=datetime.now(NY).strftime("%H:%M")
status = "🟢 السوق فاتح - فلتر 1-4$" if is_market_open() else "🌙 السوق مقفل - فلتر 0.4-6$"
st.caption(f"⏰ الرياض {ksa_now} | نيويورك {ny_now} | {status}")

c1,c2=st.columns(2)
with c1:
    if st.button("📨 اختبار تلجرام", type="primary"):
        st.success("انرسل") if send(f"✅ V98 SMART FINAL - {status}") else st.error("بدل التوكن")
with c2:
    if st.button("🗑️ تصفير"):
        save([]); st.success("تصفر")
    st.metric("المرسلة", len(load()))

sent=load()
if st.button(f"🔍 افحص 54 مرتب من الأقوى للأضعف", type="primary"):
    prog=st.progress(0)
    candidates=[]
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, chg, reason = is_strong_both(t)
        if ok: candidates.append((abs(chg), chg, t, direction, reason))
        prog.progress((i+1)/len(WATCHLIST_54)*0.5)

    candidates.sort(key=lambda x: x[0], reverse=True)
    st.write(f"🔥 وجد {len(candidates)} سهم قوي:")
    for score, chg, t, direction, reason in candidates:
        st.write(f"{'🟢' if direction=='CALL' else '🔴'} {t} {direction} {chg:+.1f}%")

    call_c=put_c=0
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c=get_contract_dir(t, direction)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد"); continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: st.write(f"⏭️ {t} مرسل"); continue
        msg=build_msg(c, reason)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
            st.success(f"✅ {t} {direction} - {chg:+.1f}%")
        time.sleep(0.2)
    st.balloons()
    st.info(f"تم: CALL {call_c} | PUT {put_c}")
