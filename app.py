import streamlit as st, yfinance as yf, requests, json, os, time, random
from datetime import datetime
import pytz
from curl_cffi import requests as c_requests

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V115 FINAL")
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

def find_one_direction(ticker):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real, session=get_session())
        try: curr=float(tk.fast_info['last_price'])
        except:
            h=tk.history(period="2d")
            curr=float(h['Close'].iloc[-1]) if not h.empty else 0
        if curr==0: return []
        today=datetime.now(NY).date()
        try: exps=[e for e in tk.options if 0 <= (datetime.strptime(e,"%Y-%m-%d").date()-today).days <= 21][:3]
        except: return []
        # نجمع كل العقود
        all_calls_puts={}
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            try: chain=tk.option_chain(exp)
            except:
                time.sleep(random.uniform(2.0,3.0))
                continue
            for direction, opts in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if opts.empty: continue
                for _, r in opts.iterrows():
                    try:
                        oi=int(r.get('openInterest',0) or 0)
                        last=float(r.get('lastPrice',0) or 0)
                        bid=float(r.get('bid',0) or 0)
                        ask=float(r.get('ask',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        if last==0: last=bid
                        if last==0: last=ask*0.85 if ask>0 else 0
                        if last==0: continue
                        if not (0.15 <= last <= 4.00): continue
                        if oi < 5000: continue
                        strike=float(r['strike'])
                        bw=abs(strike-curr)/curr*100
                        if bw > 3.5: continue
                        if bid==0 and ask==0: continue
                        spread=(ask-bid)/last if last>0 and bid>0 and ask>0 else 0.2
                        if spread > 0.45: continue
                        # تصحيح 1: بدون ذكر يوم - خصم عام
                        high = float(r.get('high', last))
                        low = float(r.get('low', last))
                        discount = ((high - last)/high*100) if high>0 else 0
                        score = oi + vol*0.5 + discount*20 - bw*100
                        if oi>=8000: score+=3000
                        key_exp = exp
                        if key_exp not in all_calls_puts:
                            all_calls_puts[key_exp]=[]
                        all_calls_puts[key_exp].append((score, {
                            "ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":strike,
                            "last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,
                            "bw":round(bw,2),"high":round(high,2),"low":round(low,2),"discount":round(discount,1),"score":score
                        }))
                    except: continue
            time.sleep(random.uniform(1.5,2.5))
        # تصحيح 2: لكل تاريخ نختار اتجاه واحد فقط - الأقوى
        final=[]
        for exp, lst in all_calls_puts.items():
            if not lst: continue
            lst.sort(key=lambda x: x[0], reverse=True)
            # شف CALL ولا PUT الأقوى في نفس التاريخ
            best_score, best_contract = lst[0]
            # لو فيه عقد ثاني باتجاه معاكس قوي - نتجاهله - نختار واحد بس
            final.append(best_contract)
        final.sort(key=lambda x: x['score'], reverse=True)
        return final[:2]
    except: return []

def build_msg(c):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    mode="LIVE" if is_market_open() else "PRE"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    tag = "🐋 8000+" if c['oi']>=8000 else "⚡ 5000+"
    if c['discount']>=30: tag+=f" 🔥 خصم {c['discount']}%"
    return f"{emoji} {c['ticker']} {int(c['strike'])} {c['type']} {mode} - {tag}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f} BW {c['bw']}%\nRange: ${c['low']} - ${c['high']} Close: ${last:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}\nStop: ${last*0.50:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"

st.title("V115 FINAL - اتجاه واحد فقط + بدون يوم")
st.caption(f"الرياض {datetime.now(RIYADH).strftime('%H:%M:%S')} | سعر 0.15-4$ | OI 5000+ | لكل تاريخ اتجاه واحد")
col1,col2=st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام"): st.success("✅") if send("✅ V115 اتجاه واحد") else st.error("فشل")
with col2:
    if st.button("🗑️ تصفير"):
        save([]); st.success("تصفر ✅")
    st.metric("المرسلة اليوم", len(load()))
sent=load()

if st.button("🔍 افحص 54 - اتجاه واحد", type="primary"):
    prog=st.progress(0)
    all_found=[]
    for i,t in enumerate(WATCHLIST_54):
        res=find_one_direction(t)
        if res: all_found.extend(res)
        prog.progress((i+1)/len(WATCHLIST_54))
    if not all_found:
        st.warning("ما فيه - Reboot")
    else:
        all_found.sort(key=lambda x: -x['score'])
        st.success(f"لقي {len(all_found)} - كل تاريخ اتجاه واحد فقط")
        for c in all_found:
            key=f"{c['ticker']}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
            msg=build_msg(c)
            st.code(msg)
            if key not in sent and send(msg):
                sent.append(key); save(sent)
