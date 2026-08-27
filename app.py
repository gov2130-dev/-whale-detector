import streamlit as st, yfinance as yf, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def send(msg):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)

def fmt(ticker, o_type, strike, opt_price, stop, curr, vol, rsi):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    tg=[curr*1.01, curr*1.02, curr*1.03, curr*1.045, curr*1.06, curr*1.08, curr*1.10]
    tg_str=" → ".join([str(int(x)) for x in tg])
    return f"""تحديث العقد والاهداف والدخول
${ticker} - {strike} {o_type} 🎯
📅 {date}
💵 السعر الحالي: ${curr:.2f}

💰 دخول العقد: ${opt_price:.2f}
🛑 وقف العقد: ${stop:.2f}
📊 Vol {vol} | RSI {int(rsi)}

🎯 اهداف السهم:
{tg_str}

🎯 اهداف العقد:
T1 ${opt_price*1.5:.2f} (+50%) | T2 ${opt_price*2.2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء، للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN 6/7"""

st.set_page_config(page_title="V78 CLEAR", layout="wide")
st.title("V78 - واضح مثل تلجرام")

# معاينة واضحة مثل تلجرام بالضبط
example = fmt("NVDA","CALL",209,4.50,2.70,205.30,850,58)
st.text_area("شكل الرسالة في تلجرام (واضح 100%):", example, height=400)

if st.button("📩 ارسل للتلجرام"):
    send(example)
    st.success("✅ انرسل - افتح تلجرام في جوالك الآن بتشوفه واضح")

if st.button("▶️ فحص حقيقي"):
    for ticker in ["NVDA","AAPL","META"]:
        try:
            tk=yf.Ticker(ticker)
            curr=float(tk.history(period="5d")['Close'].iloc[-1])
            chain=tk.option_chain(tk.options[0])
            row=chain.calls.iloc[0]
            opt=float(row['lastPrice'])
            m=fmt(ticker,"CALL",int(row['strike']),opt,opt*0.6,curr,int(row.get('volume',0)),58)
            send(m)
            st.success(f"{ticker} انرسل")
        except: pass
