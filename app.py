import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 FIXED")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

# جلسة مضادة للحجب
session = c_requests.Session(impersonate="chrome")

def is_market_open():
    now_ny = datetime.now(NY)
    if now_ny.weekday() >= 5: return False
    mins = now_ny.hour*60 + now_ny.minute
    return 570 <= mins <= 960

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
    try:
        curr=float(tk.fast_info['last_price'])
    except:
        try:
            h=tk.history(period="1d")
            curr=float(h['Close'].iloc[-1]) if not h.empty else 0
        except: curr=0
    try:
        daily=tk.history(period="20d", interval="1d")
    except:
        daily = tk.history(period="20d", interval="1d")
    return curr, daily, tk

def is_strong(ticker):
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False,"",0,f"ما فيه بيانات {ticker} - ياهو حاجب"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        high_t=float(daily['High'].iloc[-1])
        low_t=float(daily['Low'].iloc[-1])
        chg=(curr/open_t-1)*100 if open_t!=0 else 0

        # تساهل يوم السبت
        is_sat = datetime.now(NY).weekday() >= 5
        if is_sat:
            # السبت نقبل اي شي قريب من EMA
            if curr > ema20*0.985: return True, "CALL", chg, f"PRE CALL {chg:+.1f}% فوق EMA"
            elif curr < ema20*1.015: return True, "PUT", chg, f"PRE PUT {chg:+.1f}% تحت EMA"
            else: return False,"",chg,""
        else:
            if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8: return True, "CALL", chg, f"CALL {chg:+.1f}%"
            elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8: return True, "PUT", chg, f"PUT {chg:+.1f}%"
            else: return False,"",chg,f"ضعيف {chg:.1f}%"
    except Exception as e: return False,"",0,str(e)

def get_contract(ticker, direction):
    market_open = is_market_open()
    try:
        curr_real,daily,tk = get_data(ticker)
        if curr_real==0: return None
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:4]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (0 <= days <= (10 if market_open else 21)): continue
            try: chain=tk.option_chain(exp)
            except:
                time.sleep(0.6)
                continue
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_real*0.95) & (opts['strike']<=curr_real*1.08)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_real*0.92) & (opts['strike']<=curr_real*1.05)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0); vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if market_open:
                        if not (0.8 <= last <= 5.0): continue
                        if bid < 0.50: continue
                    else:
                        if not (0.30 <= last <= 7.0): continue
                    mode = "LIVE" if market_open else "PRE"
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"mode":mode}
                except: continue
            time.sleep(random.uniform(0.4,0.8))
    except: pass
    return None

def build_msg(c, reason):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    return f"{emoji} {c['ticker']} {c['strike']} {c['type']} {c['mode']} - {reason}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}\nStop: ${last*0.55:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V99 FIXED - يطلع حتى السبت")
ksa_time = datetime.now(RIYADH).strftime("%H:%M:%S")
ny_time = datetime.now(NY).strftime("%H:%M")
m_status = "LIVE السوق فاتح" if is_market_open() else "PRE السوق مقفل - وضع متساهل"
st.caption(f"الرياض {ksa_time} | نيويورك {ny_time} | {m_status} | مضاد حجب curl_cffi")

col1,col2 = st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام", type="primary"):
        ok = send("✅ V99 FIXED شغال - اختبار السبت")
        st.success("انرسل ✅") if ok else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر ✅")
    st.metric("المرسلة اليوم", len(load()))
sent = load()

if st.button("🔍 افحص 54 - الاقوى اول - مضمون", type="primary"):
    prog = st.progress(0)
    st.write("يفحص 54 شركة...")
    candidates = []
    failed = []
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, chg, reason = is_strong(t)
        if ok:
            candidates.append((abs(chg), chg, t, direction, reason))
        else:
            if "ياهو حاجب" in reason or "ما فيه بيانات" in reason:
                failed.append(t)
        prog.progress((i+1)/len(WATCHLIST_54)*0.5)
        time.sleep(0.1)

    st.write(f"لقي {len(candidates)} قوي | فشل {len(failed)} بسبب الحجب: {failed[:5]}")
    candidates.sort(key=lambda x: x[0], reverse=True)
    call_c = 0; put_c = 0
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c = get_contract(t, direction)
        if not c:
            st.write(f"❌ {t} {direction} ما لقي عقد")
            continue
        key = f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل قبل")
            continue
        msg = build_msg(c, reason)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
            st.success(f"انرسل {t}")
        prog.progress(0.5 + (idx+1)/max(len(candidates),1)*0.5)
        time.sleep(0.3)
    st.balloons()
    st.info(f"تم ✅ CALL {call_c} | PUT {put_c} | الاقوى اول")
