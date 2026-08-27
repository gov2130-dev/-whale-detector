import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, timedelta

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
    max-width: 520px;
    margin: 15px auto;
    color: white;
    font-size: 20px;
    line-height: 1.9;
    white-space: pre-wrap;
    direction: ltr;
    text-align: left;
}
.live { background: #00a86b; color: white; padding: 8px 15px; border-radius: 20px; font-size: 16px; }
.stale { background: #555; color: white; padding: 8px 15px; border-radius: 20px; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={'chat_id':CHAT_ID,'text':msg}, timeout=10)

def load(): return json.load(open(FILE)) if os.path.exists(FILE) else []
def save(d): json.dump(d, open(FILE,'w'))

def get_live_price(ticker):
    # يجيب آخر سعر - حتى لو السوق مقفل يجيب آخر سعر متاح
    try:
        tk=yf.Ticker(ticker)
        # نجرب 1m اول (حي) - اذا فشل نجرب 5m
        for interval in ["1m","5m","15m"]:
            try:
                hist=tk.history(period="1d", interval=interval)
                if not hist.empty:
                    curr=float(hist['Close'].iloc[-1])
                    last_time=hist.index[-1]
                    # هل البيانات جديدة اليوم؟
                    is_today = last_time.date() == datetime.now().date()
                    return curr, last_time, is_today
            except: continue
        return None, None, False
    except:
        return None, None, False

def build_msg(c):
    tg_str=" → ".join([str(int(x)) for x in c['targets_stock']])
    return f"""تحديث العقد والاهداف والدخول
${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['date']}
💵 السعر الحالي: ${c['curr']:.2f} ({c.get('last_update','')})

💰 دخول العقد: ${c['opt_entry']:.2f}
🛑 وقف العقد: ${c['stop']:.2f}
📊 Vol {c['vol']} | RSI {c['rsi']}

🎯 اهداف السهم:
{tg_str}

🎯 اهداف العقد:
T1 ${c['opt_entry']*1.5:.2f} (+50%) | T2 ${c['opt_entry']*2.2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء، للتعليم فقط.
🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN {c['score']}/7"""

st.title("V85 - متابعة ذكية - كل سهم لحاله")

contracts=load()
if not contracts:
    # افتراضي
    contracts=[{
        "ticker":"NVDA","type":"CALL","strike":209,"curr":205.30,
        "opt_entry":4.50,"stop":2.70,"targets_stock":[207,209,211,213,217,221,225],
        "date":"28/08/2026","vol":850,"rsi":58,"score":6,
        "last_price":205.30,"t1_hit":False
    },
    {
        "ticker":"SPX","type":"CALL","strike":6450,"curr":6455.0,
        "opt_entry":12.0,"stop":7.0,"targets_stock":[6460,6475,6490,6505,6520],
        "date":"28/08/2026","vol":1200,"rsi":62,"score":6,
        "last_price":6455.0,"t1_hit":False
    }]
    save(contracts)

# عرض البوكسات مع حالة كل سهم
for c in contracts:
    curr, last_time, is_today = get_live_price(c['ticker'])
    if curr:
        changed = abs(curr - c.get('last_price', curr)) > 0.01
        status = f"<span class='live'>LIVE {curr:.2f} - {last_time.strftime('%H:%M:%S')}</span>" if is_today and changed else f"<span class='stale'>اغلاق {curr:.2f}</span>"
        c['curr']=curr
        st.markdown(f"{status} ${c['ticker']}", unsafe_allow_html=True)
    st.markdown(f'<div class="telegram-box">{build_msg(c)}</div>', unsafe_allow_html=True)

st.write("---")
col1,col2=st.columns(2)
with col1:
    if st.button("🔄 فحص الآن - يحدث فقط اللي تغير"):
        logs=st.empty()
        for c in contracts:
            curr, last_time, is_today = get_live_price(c['ticker'])
            if curr is None: continue
            old=c.get('last_price',0)
            if abs(curr-old) > 0.05: # تغير فعلي
                logs.write(f"🔥 {c['ticker']} تغير {old:.2f} → {curr:.2f}")
                c['curr']=curr
                c['last_price']=curr
                c['last_update']=last_time.strftime('%H:%M:%S')
                send(build_msg(c))
                # فحص هدف
                if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                    send(f"✅ ${c['ticker']} حقق {c['targets_stock'][0]} - الآن {curr:.2f}")
                    c['t1_hit']=True
            else:
                logs.write(f"⏸️ {c['ticker']} ما تغير {curr:.2f} - ما نرسل")
        save(contracts)
        st.success("فحص انتهى - فقط اللي تغيرت بياناته انرسل")

with col2:
    if st.button("➕ اضافة SPX"):
        save(contracts)
        st.rerun()

# تحديث تلقائي كل 5 دقايق - ذكي
auto=st.checkbox("🚀 تحديث كل 5 دقايق - فقط اذا تغيرت البيانات")
if auto:
    placeholder=st.empty()
    while True:
        time.sleep(300)
        for c in contracts:
            curr, lt, _ = get_live_price(c['ticker'])
            if curr and abs(curr - c.get('last_price',curr)) > 0.05:
                c['curr']=curr
                c['last_price']=curr
                send(build_msg(c))
                with placeholder.container():
                    st.write(f"{datetime.now().strftime('%H:%M:%S')} - {c['ticker']} تحدث {curr:.2f}")
        save(contracts)
