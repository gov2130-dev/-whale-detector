import streamlit as st, yfinance as yf, requests, json, time, os
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
    except: pass

def load_contracts():
    if os.path.exists(FILE):
        with open(FILE,'r') as f: return json.load(f)
    return []

def save_contracts(data):
    with open(FILE,'w') as f: json.dump(data,f)

def build_msg(d):
    tg_str=" → ".join([str(int(x)) for x in d['targets_stock']])
    return f"""تحديث العقد والاهداف والدخول
${d['ticker']} - {d['strike']} {d['type']} 🎯
📅 {d['date']}
💵 السعر الحالي: ${d['curr']:.2f}

💰 دخول العقد: ${d['opt_entry']:.2f}
🛑 وقف العقد: ${d['stop']:.2f}
📊 Vol {d['vol']} | RSI {d['rsi']}

🎯 اهداف السهم:
{tg_str}

🎯 اهداف العقد:
T1 ${d['opt_entry']*1.5:.2f} (+50%) | T2 ${d['opt_entry']*2.2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء، للتعليم فقط.
🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN {d['score']}/7"""

def check_targets():
    contracts=load_contracts()
    updated=[]
    for c in contracts:
        try:
            tk=yf.Ticker(c['ticker'])
            curr=float(tk.history(period="1d", interval="1m")['Close'].iloc[-1])
            # فحص الاهداف
            if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                send(f"✅ ${c['ticker']} حقق الهدف الاول {int(c['targets_stock'][0])} → السعر الآن {curr:.2f} 🎯\n💰 العقد ربح +50%")
                c['t1_hit']=True
            if curr >= c['targets_stock'][2] and not c.get('t2_hit'):
                send(f"🔥🔥 ${c['ticker']} حقق الهدف الثالث {int(c['targets_stock'][2])} → {curr:.2f} \n💰 العقد ربح +120%")
                c['t2_hit']=True
            if curr <= c['stop_stock']:
                send(f"🛑 ${c['ticker']} ضرب وقف الخسارة {c['stop_stock']:.2f} - اغلاق العقد")
                continue # احذفه

            # تحديث سعر العقد الحالي
            chain=tk.option_chain(c['exp_date'])
            all_opts=chain.calls if c['type']=='CALL' else chain.puts
            row=all_opts[all_opts['strike']==c['strike']]
            if not row.empty:
                c['opt_now']=float(row.iloc[0]['lastPrice'])
                change=((c['opt_now']/c['opt_entry'])-1)*100
                if abs(change)>=20: # كل 20% تغيير
                    send(f"📈 تحديث ${c['ticker']} {c['strike']} {c['type']}\nدخول ${c['opt_entry']:.2f} → الآن ${c['opt_now']:.2f} ({change:+.0f}%)\nسهم ${curr:.2f}")
            c['curr']=curr
            updated.append(c)
        except:
            updated.append(c)
            continue
    save_contracts(updated)

st.set_page_config(layout="wide")
st.title("V82 - متابعة العقود حتى واللابتوب مقفل 🐋")

contracts=load_contracts()
st.write(f"عقود نشطة: {len(contracts)}")
for c in contracts:
    st.code(build_msg(c))

col1,col2=st.columns(2)
with col1:
    if st.button("➕ اضافة عقد جديد ومتابعته"):
        # مثال NVDA
        curr=205.30
        c={
            "ticker":"NVDA","type":"CALL","strike":209,
            "curr":curr,"opt_entry":4.50,"stop":2.70,
            "stop_stock":curr*0.97,
            "targets_stock":[curr*1.01, curr*1.02, curr*1.03, curr*1.04, curr*1.06, curr*1.08, curr*1.10],
            "date":(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y'),
            "exp_date":yf.Ticker("NVDA").options[0],
            "vol":850,"rsi":58,"score":6,
            "t1_hit":False,"t2_hit":False
        }
        contracts.append(c)
        save_contracts(contracts)
        send(build_msg(c))
        st.success("تمت الاضافة وسيتم متابعته كل 3 دقايق")

with col2:
    if st.button("🔄 فحص الاهداف الآن"):
        check_targets()
        st.success("تم الفحص")

# حلقة المتابعة التلقائية
st.write("---")
auto=st.checkbox("🚀 تفعيل المتابعة التلقائية كل 3 دقايق (لازم ترفعه للسحابة)")
if auto:
    st.info("شغال... حتى لو قفلت الصفحة - بيشتغل على السحابة")
    while True:
        check_targets()
        time.sleep(180) # 3 دقايق
