import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
import pandas as pd
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V111 WEEKEND READY")
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}

def get_session(): return c_requests.Session(impersonate="chrome", timeout=20)
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

def find_weekend(ticker):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real, session=get_session())
        try: curr=float(tk.fast_info['last_price'])
        except:
            h=tk.history(period="1d")
            curr=float(h['Close'].iloc[-1]) if not h.empty else 0
        if curr==0: return []
        today=datetime.now(NY).date()
        try: exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 21][:3]
        except: return []
        candidates=[]
        market_open = is_market_open()
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            try: chain=tk.option_chain(exp)
            except:
                time.sleep(1.0)
                continue
            for direction, opts in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if opts.empty: continue
                for _, r in opts.iterrows():
                    try:
                        oi=int(r.get('openInterest',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        last=float(r.get('lastPrice',0) or 0)
                        bid=float(r.get('bid',0) or 0)
                        ask=float(r.get('ask',0) or 0)
                        if last==0: last=bid
                        if last==0: last=ask*0.85 if ask>0 else 0
                        if last==0: continue
                        strike=float(r['strike'])
                        bw=abs(strike-curr)/curr*100
                        # شروطك الثابتة بأي وقت
                        if oi < 5000: continue # نزلنا لـ 5000 عشان الويكند
                        if not (0.4 <= last <= 5.5): continue
                        if bw > 3.0: continue
                        if bid==0 or ask==0: continue
                        spread=(ask-bid)/last if last>0 else 1
                        if spread > 0.35: continue
                        # لو السوق مفتوح نطبق شروط الانفجار
                        if market_open:
                            if vol < 300: continue
                            vol_oi = vol/oi if oi>0 else 0
                            if vol_oi < 0.05: continue
                        else:
                            vol_oi = vol/oi if oi>0 else 0
                        # نقاط قوة
                        score = oi + vol*2 - bw*100
                        candidates.append((score, {"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":strike,"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"bw":round(bw,2),"spread":round(spread*100,1),"vol_oi":round(vol_oi,2) if market_open else 0}))
                    except: continue
            time.sleep(0.7)
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c for s,c in candidates[:3]]
    except: return []

def build_msg(c):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    mode="LIVE" if is_market_open() else "PRE"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    whale=" 🐋" if c['oi']>8000 else ""
    return f"{emoji} {c['ticker']} {int(c['strike'])} {c['type']} {mode} - {c['type']} BW {c['bw']}%{whale}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}\nStop: ${last*0.55:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V111 - يشتغل بالويكند + نفس الاستايل")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | PRE يعني السوق مقفل Vol=0 - يشيل شرط الحجم")
col1,col2=st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V111 شغال") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة - مهم جدا"):
        save([])
        st.success("تصفر ✅ - الحين بيطلع حتى لو 88 مرسل قبل")
    st.metric("المرسلة اليوم", len(load()))
sent=load()

if st.button("🔍 افحص 54 - يشتغل حتى السبت", type="primary"):
    prog=st.progress(0)
    all_found=[]
    for i,t in enumerate(WATCHLIST_54):
        res=find_weekend(t)
        if res: all_found.extend(res)
        prog.progress((i+1)/len(WATCHLIST_54))
    if not all_found:
        st.error("ياهو حاظر IP - سوي Manage App > Reboot وتصفير المرسلة")
    else:
        all_found.sort(key=lambda x: (-x['oi'], x['bw']))
        st.success(f"لقي {len(all_found)} عقد - حتى بالويكند")
        for c in all_found:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            msg=build_msg(c)
            st.code(msg)
            if key in sent:
                st.caption("⚠️ مرسل قبل - اضغط تصفير عشان يرسل مرة ثانية")
            else:
                if send(msg):
                    sent.append(key); save(sent)
        st.balloons()
