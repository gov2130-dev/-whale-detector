import streamlit as st, yfinance as yf, requests, json, os, pytz, time
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"

st.set_page_config(layout="wide")

# --- CSS البوكس الواضح للابتوب ---
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
    font-family: -apple-system, sans-serif;
    direction: ltr;
    text-align: left;
    white-space: pre-wrap;
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}
.status-open { background: #00a86b; padding: 10px; border-radius: 10px; color: white; text-align: center; font-size: 18px; }
.status-closed { background: #d90429; padding: 10px; border-radius: 10px; color: white; text-align: center; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

def is_market_open():
    ny = pytz.timezone('America/New_York')
    now_ny = datetime.now(ny)
    if now_ny.weekday() >= 5:
        return False, f"مقفل - ويكند {now_ny.strftime('%A')} - نيويورك {now_ny.strftime('%H:%M')}"
    open_t = now_ny.replace(hour=9, minute=30, second=0)
    close_t = now_ny.replace(hour=16, minute=0, second=0)
    if open_t <= now_ny <= close_t:
        return True, f"مفتوح ✅ نيويورك {now_ny.strftime('%H:%M')} | السعودية {(datetime.now()+timedelta(hours=3)).strftime('%H:%M')}"
    return False, f"مقفل ⏸️ نيويورك {now_ny.strftime('%H:%M')} - يفتح 9:30 صباحاً ET (4:30 عصراً KSA)"

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={'chat_id':CHAT_ID,'text':msg}, timeout=10)

def load(): return json.load(open(FILE)) if os.path.exists(FILE) else []
def save(d): json.dump(d, open(FILE,'w'))

def build_msg(c):
    tg_str=" → ".join([str(int(x)) for x in c['targets_stock']])
    return f"""تحديث العقد والاهداف والدخول
${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['date']}
💵 السعر الحالي: ${c['curr']:.2f}

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

def check_and_update():
    open_now, status = is_market_open()
    if not open_now:
        return False, status, None
    contracts=load()
    logs=[]
    for c in contracts:
        try:
            tk=yf.Ticker(c['ticker'])
            # سعر لحظي حقيقي فقط اذا السوق مفتوح
            curr=float(tk.history(period="1d", interval="1m")['Close'].iloc[-1])
            c['curr']=curr
            # فحص هدف حقيقي
            if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                send(f"✅ ${c['ticker']} حقق الهدف الاول {int(c['targets_stock'][0])} → الآن {curr:.2f}\nالعقد +50% 💰")
                c['t1_hit']=True
                logs.append(f"حقق {c['ticker']}")
            if curr <= c['stop_stock'] and not c.get('stop_hit'):
                send(f"🛑 ${c['ticker']} ضرب الوقف {c['stop_stock']:.2f}")
                c['stop_hit']=True
        except Exception as e:
            logs.append(str(e))
    save(contracts)
    return True, status, contracts

# --- الواجهة ---
st.title("V84 - متابعة كل 5 دقايق + بوكس واضح")

is_open, status_txt = is_market_open()
if is_open:
    st.markdown(f'<div class="status-open">{status_txt} - سيتم التحديث كل 5 دقايق بأسعار حية</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="status-closed">{status_txt} - البيانات من الاغلاق فقط - لن يرسل اهداف وهمية</div>', unsafe_allow_html=True)

contracts=load()
if contracts:
    for c in contracts:
        st.markdown(f'<div class="telegram-box">{build_msg(c)}</div>', unsafe_allow_html=True)
else:
    # مثال افتراضي اذا ما فيه عقود
    example="""تحديث العقد والاهداف والدخول
$NVDA - 209 CALL 🎯
📅 28/08/2026
💵 السعر الحالي: $205.30

💰 دخول العقد: $4.50
🛑 وقف العقد: $2.70
📊 Vol 850 | RSI 58

🎯 اهداف السهم:
207 → 209 → 211 → 213 → 217 → 221 → 225

🎯 اهداف العقد:
T1 $6.75 (+50%) | T2 $9.90 (+120%)

⚠️ ليست توصية بيع أو شراء، للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN 6/7"""
    st.markdown(f'<div class="telegram-box">{example}</div>', unsafe_allow_html=True)
    st.info("هذا مثال - اضغط 'اضافة عقد' تحت عشان تبدأ المتابعة الحقيقية")

col1,col2,col3=st.columns(3)
with col1:
    if st.button("➕ اضافة NVDA للمتابعة"):
        c={
            "ticker":"NVDA","type":"CALL","strike":209,
            "curr":205.30,"opt_entry":4.50,"stop":2.70,
            "stop_stock":200.0,
            "targets_stock":[207,209,211,213,217,221,225],
            "date":(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y'),
            "vol":850,"rsi":58,"score":6,
            "t1_hit":False,"stop_hit":False
        }
        save([c])
        send(build_msg(c))
        st.success("تمت الاضافة - بيتم متابعته كل 5 دقايق")
        st.rerun()
with col2:
    if st.button("🔄 فحص الآن"):
        ok, txt, data=check_and_update()
        st.write(txt)
        if not ok:
            st.warning("السوق مقفل - ما فحصنا عشان ما نرسل وهمي")
        else:
            st.success("تم الفحص - السعر حي")
            st.rerun()
with col3:
    if st.button("🗑️ حذف الكل"):
        save([])
        st.rerun()

st.write("---")
auto=st.checkbox("🚀 تفعيل التحديث التلقائي كل 5 دقايق (للسحابة)")
if auto:
    st.info("شغال كل 5 دقايق... حتى لو قفلت اللابتوب اذا رفعته على Streamlit Cloud")
    placeholder=st.empty()
    while True:
        ok, txt, data=check_and_update()
        with placeholder.container():
            st.write(f"آخر فحص: {datetime.now().strftime('%H:%M:%S')} - {txt}")
            if data:
                for c in data:
                    st.markdown(f'<div class="telegram-box">{build_msg(c)}</div>', unsafe_allow_html=True)
        time.sleep(300) # 5 دقايق
