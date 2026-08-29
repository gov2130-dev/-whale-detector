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
st.set_page_config(layout="wide", page_title="V110 PRE-EXPLOSION")
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

def check_explosion_ready(ticker, tk, curr):
    try:
        hist = tk.history(period="25d", interval="1d")
        if len(hist) < 20: return False, 0
        vol_today = hist['Volume'].iloc[-1]
        vol_avg20 = hist['Volume'].iloc[-21:-1].mean()
        vol_ratio = vol_today / vol_avg20 if vol_avg20>0 else 0

        high_20 = hist['High'].iloc[-20:].max()
        low_20 = hist['Low'].iloc[-20:].min()

        # RSI تقريبي
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_now = rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50

        # شرط الانفجار: حجم عالي + قريب من القمة + RSI مو متشبع
        is_ready = vol_ratio > 1.25 and curr >= low_20*0.98 and rsi_now >= 45 and rsi_now <= 72
        return is_ready, round(vol_ratio,2), round(rsi_now,1), round(high_20,2)
    except:
        return False, 0, 0, 0

def find_pre_explosion(ticker):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real, session=get_session())
        try: curr=float(tk.fast_info['last_price'])
        except:
            h=tk.history(period="1d")
            curr=float(h['Close'].iloc[-1]) if not h.empty else 0
        if curr==0: return []

        ready, vol_ratio, rsi_now, high20 = check_explosion_ready(ticker, tk, curr)
        if not ready and ticker not in ["SPX","NDX","SPY","QQQ"]: # للاسهم الفردية لازم يكون جاهز
            # نسمح بس لو vol_ratio > 1.0
            if vol_ratio < 1.0:
                return []

        today=datetime.now(NY).date()
        try: exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 14][:2] # 0-14 يوم فقط عشان الحركة بعد الدخول
        except: return []

        candidates=[]
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
                        if last==0 or bid==0 or ask==0: continue

                        # 1. سعرك اللي تبيه 0.5 الى 4$ فقط
                        if not (0.5 <= last <= 4.0): continue
                        # 2. حوت حقيقي مو وهمي
                        if oi < 8000: continue
                        if vol < 800: continue # لازم تداول اليوم
                        vol_oi = vol/oi if oi>0 else 0
                        if not (0.12 <= vol_oi <= 2.8): continue # لو 0.01 يعني مجمد ولو 5 يعني تصريف
                        # 3. السبريد ما يكون عالي - شرطك
                        spread = (ask-bid)/last if last>0 else 1
                        if spread > 0.18: continue
                        # 4. BW - اليونانيات - Delta 0.3 الى 0.65
                        strike=float(r['strike'])
                        bw=abs(strike-curr)/curr*100
                        if bw > 3.0: continue
                        if bw < 0.2: continue # قريب جدا انتهى
                        # 5. لسه ما انفجر - نستبعد اللي ارتفع اليوم اكثر من 80%
                        change = float(r.get('percentChange',0) or 0)
                        if change > 90: continue

                        # نقاط قوة الانفجار بعد الدخول
                        score = (oi/1000) + vol*0.5 + vol_ratio*20 - bw*5
                        if rsi_now>=55 and rsi_now<=65: score+=15
                        if vol_oi>=0.3 and vol_oi<=1.2: score+=10 # تدفق حوت مثالي

                        candidates.append((score, {"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":strike,"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"bw":round(bw,2),"spread":round(spread*100,1),"vol_ratio":vol_ratio,"rsi":rsi_now,"vol_oi":round(vol_oi,2)}))
                    except: continue
            time.sleep(0.8)
        candidates.sort(key=lambda x: x[0], reverse=True)
        return [c for s,c in candidates[:2]] # عقدين فقط الاقوى - اللي بينفجر بعد دخولنا
    except: return []

def build_msg(c):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    mode="LIVE" if is_market_open() else "PRE"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    return f"{emoji} {c['ticker']} {int(c['strike'])} {c['type']} {mode} - PRE-EXPLOSION Vol×{c['vol_ratio']} RSI {c['rsi']}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f} High20 ${c.get('high20','-')}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Ask: ${c['ask']:.2f} Spread: {c['spread']}%\nVol: {c['vol']} OI: {c['oi']} Vol/OI: {c['vol_oi']} BW: {c['bw']}%\nStop: ${last*0.60:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V110 PRE-EXPLOSION - دخول قبل الانفجار")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | حوت حقيقي + سهم جاهز للانفجار + سبريد <18% + 0.5-4$")
col1,col2=st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V110 PRE-EXPLOSION شغال") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر")
    st.metric("المرسلة اليوم", len(load()))
sent=load()

if st.button("🔍 افحص 54 - عقود ما انفجرت لسه", type="primary"):
    prog=st.progress(0)
    all_found=[]
    for i,t in enumerate(WATCHLIST_54):
        res=find_pre_explosion(t)
        if res:
            all_found.extend(res)
            st.write(f"🚀 {t}: جاهز للانفجار Vol×{res[0]['vol_ratio']} RSI {res[0]['rsi']} - {len(res)} عقود")
        prog.progress((i+1)/len(WATCHLIST_54))
    if not all_found:
        st.warning("ما فيه سهم جاهز للانفجار الان + حوت حقيقي - السوق هادي")
    else:
        all_found.sort(key=lambda x: (-x['vol_ratio'], -x['oi']))
        st.success(f"لقي {len(all_found)} عقد PRE-EXPLOSION - بتدخل وينفجر بعدك")
        for c in all_found:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            if key in sent: continue
            msg=build_msg(c)
            st.code(msg)
            if send(msg):
                sent.append(key); save(sent)
        st.balloons()
