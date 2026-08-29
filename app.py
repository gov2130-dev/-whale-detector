import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime, timedelta
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
CACHE_FILE="scan_cache.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V117 STABLE TRUST")

WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

# جلسة واحدة ثقة
SESSION = c_requests.Session(impersonate="chrome", timeout=30)

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

def find_stable(ticker):
    # 3 محاولات - مصدر ثقة
    for attempt in range(3):
        try:
            real=TICKER_MAP.get(ticker,ticker)
            tk=yf.Ticker(real, session=SESSION)
            try: curr=float(tk.fast_info['last_price'])
            except:
                h=tk.history(period="2d")
                curr=float(h['Close'].iloc[-1]) if not h.empty else 0
            if curr==0: 
                time.sleep(1.5)
                continue
            today=datetime.now(NY).date()
            try: exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 21][:3]
            except: 
                time.sleep(2)
                continue
            found=[]
            for exp in exps:
                days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
                try: 
                    chain=tk.option_chain(exp)
                except:
                    time.sleep(2.5)
                    continue
                for direction, opts in [("CALL", chain.calls), ("PUT", chain.puts)]:
                    if opts.empty: continue
                    for _, r in opts.iterrows():
                        try:
                            oi=int(r.get('openInterest',0) or 0)
                            if oi < 5000: continue # شرطك
                            last=float(r.get('lastPrice',0) or 0)
                            bid=float(r.get('bid',0) or 0)
                            ask=float(r.get('ask',0) or 0)
                            if last==0: last=bid or ask*0.85 if ask>0 else 0
                            if last==0: continue
                            if not (0.15 <= last <= 4.00): continue # شرطك من الصوت
                            strike=float(r['strike'])
                            bw=abs(strike-curr)/curr*100
                            if bw > 3.5: continue
                            vol=int(r.get('volume',0) or 0)
                            if bid==0 and ask==0: continue
                            high=float(r.get('high',last))
                            low=float(r.get('low',last))
                            # ثقة البيانات
                            found.append({
                                "ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":strike,
                                "last":last,"bid":bid,"vol":vol,"oi":oi,"type":direction,
                                "bw":round(bw,2),"high":round(high,2),"low":round(low,2),
                                "source":"yahoo-direct"
                            })
                        except: continue
            if found:
                return found
        except:
            time.sleep(2.5)
    return []

def build_msg(c):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    mode="LIVE" if is_market_open() else "PRE"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    tag = "🐋 8000+" if c['oi']>=8000 else "⚡ 5000+"
    return f"{emoji} {c['ticker']} {int(c['strike'])} {c['type']} {mode} - {tag}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f} BW {c['bw']}%\nRange: ${c['low']} - ${c['high']} Close: ${last:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']} | مصدر: {c['source']}\nStop: ${last*0.50:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V117 STABLE - مصدر ثقة + نفس الشركات")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | جلسة ثابتة + 2 ثانية بين الشركات + 3 محاولات | بدون فلترة توجه")

col1,col2=st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V117 ثقة") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة والكاش"):
        save([])
        if os.path.exists(CACHE_FILE): os.remove(CACHE_FILE)
        st.success("تصفر ✅")
    st.metric("المرسلة اليوم", len(load()))

if st.button("🔍 افحص 54 - ثبات + ثقة", type="primary"):
    prog=st.progress(0); status=st.empty()
    all_found=[]
    for i,t in enumerate(WATCHLIST_54):
        status.text(f"يفحص {t} - محاولة ثقة {i+1}/54")
        res=find_stable(t)
        if res: all_found.extend(res)
        prog.progress((i+1)/len(WATCHLIST_54))
        time.sleep(2.2) # ثبات - عشان ياهو ما يقطع - هذا اللي يحل مشكلة شركات جديدة
    if not all_found:
        st.warning("ما فيه - ياهو قطع - انتظر دقيقة واعد")
    else:
        # ما نفلتر CALL و PUT - نطلع كل شي يحقق الشرط
        all_found.sort(key=lambda x: (-x['oi'], -x['vol']))
        st.success(f"لقي {len(all_found)} عقد - كلها ثقة - CALL و PUT مسموح")
        for c in all_found[:20]:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            msg=build_msg(c)
            st.code(msg)
            if key not in load() and send(msg):
                s=load(); s.append(key); save(s)
