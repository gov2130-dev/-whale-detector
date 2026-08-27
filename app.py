import streamlit as st, yfinance as yf, time, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def fmt(ticker, o_type, strike, entry, stop, tg, score):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    targets=" → ".join([str(int(x)) for x in tg])
    level="🔥 GOLDEN 6/7" if score>=6 else "⭐ GOOD 5/7"
    return f"""تحديث العقد والاهداف والدخول
${ticker} - {strike} {o_type} 🎯
📅 {date}

💰 الدخول: {int(entry)}
🛑 الوقف: {int(stop)}

🎯 الأهداف:
{targets}

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
{level}"""

st.set_page_config(layout="wide")
now=datetime.now()+timedelta(hours=3)
st.title(f"V74 حيتان ابو راكان - {now.strftime('%H:%M:%S')}")

if st.button("📩 اختبار - حيتان ابو راكان"):
    m=fmt("AVGO","CALL",380,365,360,[368,370,374,378,381,385,388,390,392],6)
    if send(m):
        st.success("✅ انرسل - شف تلجرام")
        st.code(m)
    else: st.error("فشل")

# لوب فحص حقيقي
if "sent" not in st.session_state: st.session_state.sent=set()
tickers=["AVGO","MSFT","NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META"]

if st.button("▶️ بدء فحص الفجر - كتابة فقط"):
    prog=st.progress(0)
    for i,ticker in enumerate(tickers):
        prog.progress(int((i+1)/len(tickers)*100))
        try:
            tk=yf.Ticker(ticker); h=tk.history(period="20d")
            if len(h)<15: continue
            curr=float(h['Close'].iloc[-1])
            # اهداف على سعر السهم مثل صورتك
            tg=[curr*1.01, curr*1.02, curr*1.03, curr*1.04, curr*1.05, curr*1.06, curr*1.07, curr*1.08, curr*1.09]
            key=f"{ticker}{int(curr)}"
            if key in st.session_state.sent: continue
            m=fmt(ticker,"CALL",int(curr),curr*0.98,curr*0.95,tg,6)
            if send(m):
                st.session_state.sent.add(key)
                st.code(m)
        except: continue
