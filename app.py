import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def today_file():
    return os.path.join(BASE, f"{date.today()}.json")

def save_daily(contract):
    f=today_file()
    data=[]
    if os.path.exists(f):
        try: data=json.load(open(f, encoding='utf-8'))
        except: data=[]
    # لا تكرر نفس العقد بنفس اليوم
    if not any(d['key']==contract['key'] for d in data):
        data.append(contract)
        json.dump(data, open(f,"w",encoding='utf-8'), ensure_ascii=False, indent=2)

def load_day(day):
    f=os.path.join(BASE, f"{day}.json")
    if os.path.exists(f):
        return json.load(open(f, encoding='utf-8'))
    return []

st.set_page_config(layout="wide")
st.markdown("""
<style>
.box{background:#1f1f1f;color:#fff;padding:18px;border-radius:12px;
font-family:monospace;font-size:15px;line-height:1.7;border:1px solid #333;margin-bottom:14px}
.day{color:#aaa;font-size:13px}
</style>
""", unsafe_allow_html=True)

st.title("📅 V99 - أرشيف يومي للنتائج")

col1,col2 = st.columns([1,2])
with col1:
    if st.button("🚀 فحص اليوم وحفظ", use_container_width=True):
        for t in ["QQQ","AAPL","META","AMD","IWM","SOFI","COIN","HOOD","SPY"]:
            try:
                tk=yf.Ticker(t)
                curr=float(tk.fast_info.get('last_price') or tk.history(period="1d")['Close'].iloc[-1])
                exp=tk.options[0]
                dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                chain=tk.option_chain(exp)
                is_put = curr < float(tk.history(period="5d")['Close'].mean())
                opts=chain.puts if is_put else chain.calls
                direction="PUT" if is_put else "CALL"
                row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
                entry=round((row['bid']+row['ask'])/2,2)
                strike=int(row['strike']) if row['strike']==int(row['strike']) else row['strike']

                emoji="🔴" if direction=="PUT" else "🟢"
                text=f"{emoji} {t} {strike} {direction} 🐋\nExp: {exp} ({dte}d) Stock: ${round(curr,2)}\nEntry: ${entry} Bid: ${round(row['bid'],2)}\nStop: ${round(entry*0.5,2)}\nTarget: ${round(entry*1.5,2)} (+50%) | ${round(entry*2.3,2)} (+130%) | ${round(entry*3.2,2)} (+220%)"

                contract={"key":f"{t}_{strike}_{direction}_{exp}","ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"curr_stock":round(curr,2),"text":text,"time":datetime.now().strftime("%H:%M")}
                save_daily(contract)
                st.markdown(f'<div class="box">{text.replace(chr(10),"<br>")}<div class="day">حفظ: {date.today()} {contract["time"]}</div></div>', unsafe_allow_html=True)
                send(text)
                time.sleep(0.5)
            except: continue
        st.success(f"تم حفظ بحث اليوم {date.today()}")

with col2:
    st.subheader("📂 الأرشيف - اختر يوم")
    files=sorted(os.listdir(BASE), reverse=True) if os.path.exists(BASE) else []
    days=[f.replace(".json","") for f in files]
    sel=st.selectbox("اختر اليوم", days if days else ["لا يوجد"])

    if sel and sel!="لا يوجد":
        data=load_day(sel)
        st.write(f"**{len(data)} عقد في {sel}**")
        for c in data:
            # جلب السعر الحالي للمقارنة
            try:
                tk=yf.Ticker(c['ticker'])
                chain=tk.option_chain(c['exp'])
                opts=chain.calls if c['dir']=="CALL" else chain.puts
                row=opts[opts['strike']==c['strike']]
                now=round((float(row['bid'].iloc[0])+float(row['ask'].iloc[0]))/2,2) if not row.empty else 0
                pnl=(now-c['entry'])/c['entry']*100 if now else 0
                if now:
                    if now <= c['entry']*0.5: res=f"🔴 ضرب وقف | كان ${c['entry']} الآن ${now} {pnl:+.1f}%"
                    elif now >= c['entry']*3.2: res=f"🟢 هدف 3 | كان ${c['entry']} الآن ${now} {pnl:+.1f}%"
                    elif now >= c['entry']*2.3: res=f"🟢 هدف 2 | كان ${c['entry']} الآن ${now} {pnl:+.1f}%"
                    elif now >= c['entry']*1.5: res=f"🟢 هدف 1 | كان ${c['entry']} الآن ${now} {pnl:+.1f}%"
                    else: res=f"⚪ شغال | كان ${c['entry']} الآن ${now} {pnl:+.1f}%"
                else:
                    res="منتهي أو غير موجود"
            except:
                res="--"

            st.markdown(f'<div class="box">{c["text"].replace(chr(10),"<br>")}<br><br>📌 النتيجة الآن: {res}<br><span class="day">وقت الحفظ: {c["time"]} يوم {sel}</span></div>', unsafe_allow_html=True)
