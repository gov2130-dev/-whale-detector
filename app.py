import streamlit as st, yfinance as yf, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

st.set_page_config(layout="wide")

# CSS يخلي الكتابة واضحة وكبيرة في اللابتوب
st.markdown("""
<style>
.telegram-box {
    background: #182533;
    border-radius: 18px;
    padding: 30px;
    max-width: 500px;
    margin: auto;
    color: white;
    font-size: 20px;
    line-height: 1.9;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    direction: ltr;
    text-align: left;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)

def send(msg):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg})
    return r.status_code==200

def build_msg(ticker, o_type, strike, curr, opt_entry, stop, vol, rsi, score):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    # اهداف دقيقة على سعر الحالي
    tg=[curr*1.01, curr*1.02, curr*1.03, curr*1.04, curr*1.06, curr*1.08, curr*1.10]
    tg_str=" → ".join([str(int(x)) for x in tg])
    t1=opt_entry*1.5
    t2=opt_entry*2.2
    return f"""تحديث العقد والاهداف والدخول
${ticker} - {strike} {o_type} 🎯
📅 {date}
💵 السعر الحالي: ${curr:.2f}

💰 دخول العقد: ${opt_entry:.2f}
🛑 وقف العقد: ${stop:.2f}
📊 Vol {vol} | RSI {rsi}

🎯 اهداف السهم:
{tg_str}

🎯 اهداف العقد:
T1 ${t1:.2f} (+50%) | T2 ${t2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN {score}/7"""

# رسالتك اللي تبيها
msg_example = """تحديث العقد والاهداف والدخول
$NVDA - 209 CALL 🎯
📅 28/08/2026
💵 السعر الحالي: $205.30

💰 دخول العقد: $4.50
🛑 وقف العقد: $2.70
📊 Vol 850 | RSI 58

🎯 اهداف السهم:
207 → 209 → 211 → 214 → 217 → 221 → 225

🎯 اهداف العقد:
T1 $6.75 (+50%) | T2 $9.90 (+120%)

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN 6/7"""

st.title("V81 FINAL - الشكل النهائي الواضح")

# عرض مثل تلجرام بالضبط - خط كبير واضح في اللابتوب
st.markdown(f'<div class="telegram-box">{msg_example}</div>', unsafe_allow_html=True)

st.write("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("📩 ارسل نفس هذه الرسالة لتلجرام"):
        if send(msg_example):
            st.success("✅ انرسلت - شف تلجرام الآن نفس الشكل")
        else:
            st.error("فشل")

with col2:
    if st.button("▶️ فحص حي بأسعار حقيقية"):
        try:
            tk=yf.Ticker("NVDA")
            curr=float(tk.history(period="5d")['Close'].iloc[-1])
            chain=tk.option_chain(tk.options[0])
            row=chain.calls.iloc[1]
            opt=float(row['lastPrice'])
            vol=int(row.get('volume',0))
            m=build_msg("NVDA","CALL",int(row['strike']),curr,opt,opt*0.6,vol,58,6)
            st.markdown(f'<div class="telegram-box">{m}</div>', unsafe_allow_html=True)
            send(m)
            st.success("تم الفحص والارسال بسعر حقيقي")
        except Exception as e:
            st.error(f"خطأ: {e}")
