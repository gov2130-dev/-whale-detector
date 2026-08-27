import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, timedelta
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"

st.set_page_config(layout="wide")
st.markdown("""
<style>
.telegram-box {
    background: #182533;
    border: 3px solid #00e6a8;
    border-radius: 18px;
    padding: 28px;
    max-width: 500px;
    margin: 20px auto;
    color: white;
    font-size: 20px;
    line-height: 2.0;
    white-space: pre-wrap;
    direction: ltr;
    text-align: left;
}
.box-update {
    background: #0f2b1d;
    border: 3px solid #ffcc00;
    border-radius: 18px;
    padding: 20px;
    max-width: 500px;
    margin: 15px auto;
    color: white;
    font-size: 18px;
    white-space: pre-wrap;
}
</style>
""", unsafe_allow_html=True)

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={'chat_id':CHAT_ID,'text':msg})

def load(): return json.load(open(FILE)) if os.path.exists(FILE) else []
def save(d): json.dump(d, open(FILE,'w'))

def get_price(ticker):
    try:
        hist=yf.Ticker(ticker).history(period="1d", interval="1m")
        if not hist.empty:
            return float(hist['Close'].iloc[-1]), hist.index[-1]
    except: pass
    return None, None

# رسالة الدخول النظيفة - بدون اللي طلبت حذفه
def build_entry(c):
    tg=" → ".join([str(int(x)) for x in c['targets_stock']])
    return f"""${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['date']}
💵 السعر الحالي: ${c['curr']:.2f}

💰 دخول العقد: ${c['opt_entry']:.2f}
🛑 وقف العقد: ${c['stop']:.2f}
📊 Vol {c['vol']} | RSI {c['rsi']}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['opt_entry']*1.5:.2f} (+50%) | T2 ${c['opt_entry']*2.2:.2f} (+120%)

🐋 حيتان ابو راكان
🔥 GOLDEN {c['score']}/7"""

# رسالة التحديث المنفصلة
def build_update(ticker, event, curr, extra=""):
    if event=="T1":
        return f"""🔥 تحديث العقد ${ticker}
✅ تحقق الهدف الاول

💵 السعر الآن: ${curr:.2f}
💰 العقد: +50% ربح
{extra}"""
    elif event=="T2":
        return f"""🔥🔥 تحديث العقد ${ticker}
🚀 تحقق الهدف الثاني

💵 السعر الآن: ${curr:.2f}
💰 العقد: +120% ربح
{extra}"""
    elif event=="STOP":
        return f"""🛑 تحديث العقد ${ticker}
⚠️ ضرب وقف الخسارة

💵 السعر الآن: ${curr:.2f}
اغلاق العقد"""
    elif event=="MOVE":
        return f"""📈 تحديث العقد ${ticker}
السعر تغير: ${curr:.2f}
{extra}"""

st.title("V86 CLEAN - بدون حشو")

contracts=load()
if not contracts:
    contracts=[{"ticker":"NVDA","type":"CALL","strike":209,"curr":205.30,"opt_entry":4.50,"stop":2.70,"targets_stock":[207,209,211,213,217,221,225],"date":"28/08/2026","vol":850,"rsi":58,"score":6,"last_price":205.30,"t1_hit":False}]
    save(contracts)

# عرض
for c in contracts:
    st.markdown(f'<div class="telegram-box">{build_entry(c)}</div>', unsafe_allow_html=True)

st.write("---")
st.subheader("رسالة التحديث (منفصلة):")
update_example="""🔥 تحديث العقد $NVDA
✅ تحقق الهدف الاول 207

💵 السعر الآن: $207.50
💰 العقد: +50% ربح"""
st.markdown(f'<div class="box-update">{update_example}</div>', unsafe_allow_html=True)

col1,col2=st.columns(2)
with col1:
    if st.button("📩 ارسل رسالة الدخول النظيفة"):
        for c in contracts:
            send(build_entry(c))
        st.success("انرسلت نظيفة - بدون تحديث العقد وبدون TrkHrTrading وبدون ليست توصية")

with col2:
    if st.button("🔄 فحص وارسال تحديث منفصل كل 5 دق"):
        for c in contracts:
            curr, lt = get_price(c['ticker'])
            if curr and abs(curr - c.get('last_price',curr)) > 0.1:
                # اذا تحقق هدف
                if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                    send(build_update(c['ticker'],"T1",curr))
                    c['t1_hit']=True
                elif curr < c.get('last_price',curr)*0.97:
                    send(build_update(c['ticker'],"MOVE",curr, f"تعديل: السعر نزل من ${c['last_price']:.2f}"))
                c['last_price']=curr
                c['curr']=curr
        save(contracts)
        st.success("تم")

auto=st.checkbox("🚀 تفعيل المتابعة التلقائية كل 5 دقائق")
if auto:
    while True:
        time.sleep(300)
        for c in contracts:
            curr, _ = get_price(c['ticker'])
            if curr and abs(curr - c.get('last_price',curr)) > 0.05:
                if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                    send(build_update(c['ticker'],"T1",curr))
                    c['t1_hit']=True
                    save(contracts)
