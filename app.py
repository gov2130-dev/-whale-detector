import streamlit as st, yfinance as yf, time, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def send_text(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=20)
        return r.status_code==200
    except: return False

def format_msg(ticker, o_type, strike, entry, stop, targets, score):
    # نفس ستايل صورتك بالضبط
    date_str = (datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    t_line = " → ".join([f"{int(t)}" for t in targets])
    return f"""تحديث العقد والاهداف والدخول
${ticker} - {strike} {o_type} 🎯
📅 {date_str}

💰 الدخول: {int(entry)}
🛑 الوقف: {int(stop)}

🎯 الأهداف:
{t_line}

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🇺🇸 الأمريكي تحت المجهر
TrkHrTrading
{'🔥 GOLDEN 6/7' if score>=6 else '⭐ GOOD 5/7'}"""

st.set_page_config(layout="wide")
now=datetime.now()+timedelta(hours=3); s=now.strftime('%H:%M:%S'); h=now.hour
is_fajer=2<=h<=6
st.title(f"{s} - V73 TEXT STYLE")
st.success(f"V73 مثل صورتك | {s} KSA | {'FAJR ON' if is_fajer else 'WAIT'}")

if st.button("📩 اختبار رسالة نصية مثل صورتك"):
    # نفس AVGO اللي في الصورة
    targets=[368,370,374,378,381,385,388,390,392]
    msg=format_msg("AVGO","CALL",380,365,360,targets,6)
    if send_text(msg):
        st.success("✅ انرسلت - شف تلجرام نفس صورتك"); st.code(msg)
    else: st.error("فشل")

if "sent" not in st.session_state: st.session_state.sent=set()
if "auto" not in st.session_state: st.session_state.auto=False

if (not st.session_state.auto) or is_fajer:
    tickers=["MSFT","NVDA","AAPL","AVGO","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD"]
    prog=st.progress(0); log=st.empty()
    for i,ticker in enumerate(tickers):
        prog.progress(int((i+1)/len(tickers)*100)); log.text(f"يفحص {ticker}...")
        try:
            tk=yf.Ticker(ticker); hist=tk.history(period="20d")
            if len(hist)<15: continue
            curr=float(hist['Close'].iloc[-1]); prev=float(hist['Close'].iloc[-2]); ch=float((curr-prev)/prev*100)
            d=hist['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            trend="BEAR" if rsi>=63 and ch<=-0.3 else "BULL" if rsi<=40 and ch>=0.3 else None
            if not trend: continue
            opts=tk.options
            if not opts: continue
            exp=opts[1] if len(opts)>1 else opts[0]
            chain=tk.option_chain(exp); df=chain.puts if trend=="BEAR" else chain.calls
            df=df[(df['lastPrice']>=0.4)&(df['lastPrice']<=9)]
            if df.empty: continue
            df=df.sort_values('volume', ascending=False).head(3)
            for _,rw in df.iterrows():
                vol=int(rw.get('volume',0)or 0)
                if vol<200: continue
                bid=float(rw.get('bid',0)or 0); ask=float(rw.get('ask',0)or 0)
                if bid<=0 or ask<=0: continue
                if (ask-bid)/((ask+bid)/2)*100>18: continue
                strike=int(rw['strike']); entry=ask; stop=entry*0.6
                # اهداف مثل صورتك - على سعر السهم
                base = curr
                step = base*0.01
                targets=[base+step, base+step*2, base+step*3, base+step*4, base+step*5, base+step*6, base+step*7, base+step*8, base+step*9]
                total=6 if vol>800 else 5
                key=f"{ticker}{strike}{trend}"
                if key in st.session_state.sent: continue
                msg=format_msg(ticker, "PUT" if trend=="BEAR" else "CALL", strike, entry, stop, targets, total)
                if send_text(msg):
                    st.session_state.sent.add(key)
                    st.success(f"✅ {ticker} انرسل"); st.code(msg)
                break
        except: continue
    prog.progress(100); log.empty()
    st.session_state.auto=True
    if is_fajer:
        time.sleep(60); st.session_state.auto=False; st.rerun()
