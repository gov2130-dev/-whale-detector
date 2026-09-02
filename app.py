import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id': CHAT_ID, 'text': msg}, timeout=15)
        st.write(f"Telegram status: {r.status_code} - {r.text[:200]}") # يطلع لك السبب
        return r.status_code==200
    except Exception as e:
        st.error(f"Send error: {e}")
        return False

def today_file(): return os.path.join(BASE, f"{date.today()}.json")

def get_fibo(h,l,d):
    diff = (h-l) or 1.0
    if d=="PUT": return round(l-diff*0.382,2), round(l-diff*0.618,2), round(l-diff*1.0,2)
    return round(h+diff*0.382,2), round(h+diff*0.618,2), round(h+diff*1.0,2)

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>""", unsafe_allow_html=True)

# زر اختبار التيليجرام
if st.button("📨 اختبار التيليجرام فقط"):
    send("تست - البوت شغال ✅")

if st.button("🚀 فحص وارسال تلقائي للتيليجرام", use_container_width=True, type="primary"):
    sent=0
    logs=[]
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="5d") # 5 ايام عشان لو اليوم مقفل ياخذ اخر يوم
            if hist.empty:
                logs.append(f"{t}: hist empty")
                continue
            curr=round(float(hist['Close'].iloc[-1]),2)
            high=round(float(hist['High'].iloc[-1]),2); low=round(float(hist['Low'].iloc[-1]),2)

            if not tk.options:
                logs.append(f"{t}: no options")
                continue
            # خذ اقرب اكسبايري حتى لو 0d او 1d
            exp = tk.options[0]
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            # لو منتهي خذ اللي بعده
            if dte < 0 and len(tk.options)>1:
                exp = tk.options[1]
                dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days

            chain=tk.option_chain(exp)
            avg5=float(hist['Close'].mean())
            direction="CALL" if curr>avg5 else "PUT"
            opts=chain.calls if direction=="CALL" else chain.puts
            if opts.empty:
                logs.append(f"{t}: opts empty")
                continue
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            bid=float(row['bid'] or 0); ask=float(row['ask'] or 0)
            entry=round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row.get('lastPrice',0) or 0),2)

            # كان الشرط 0.2 هو اللي يخلي 0 عقد - خليته 0.05
            if entry < 0.05:
                logs.append(f"{t}: entry {entry} too low")
                continue

            strike=float(row['strike']); strike_s=int(strike) if strike==int(strike) else strike
            ft1,ft2,ft3=get_fibo(high, low, direction)
            emoji="🟢" if direction=="CALL" else "🔴"

            txt=(f"{emoji} {t} {strike_s} {direction} 🐳\n"
                 f"Exp: {exp} ({dte}d) Stock: ${curr:.2f}\n"
                 f"Entry: ${entry} Bid: ${bid}\n"
                 f"Stop: ${entry*0.5:.1f}\n"
                 f"Target: ${entry*1.5:.1f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\n"
                 f"Target Stock: {ft1} > {ft2} > {ft3} (Fibo)\n"
                 f"Now: ${entry} | 0.0% شغال\n{datetime.now().strftime('%H:%M:%S')}")

            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)

            fpath=today_file()
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d.get('key')==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)

            if send(txt):
                sent+=1
            time.sleep(1.2)
        except Exception as e:
            logs.append(f"{t}: {e}")

    st.success(f"تم ارسال {sent} عقد للتيليجرام")
    if logs:
        st.write("السبب:")
        st.write(logs)

st.divider()
st.subheader("الأرشيف - ارسال الكل")
files=sorted([f for f in os.listdir(BASE) if f.endswith(".json")], reverse=True)
if files:
    sel=st.selectbox("اختر اليوم", [f.replace(".json","") for f in files])
    if st.button("📨 ارسال كل عقود اليوم المختار للتيليجرام", use_container_width=True):
        data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
        c=0
        for item in data:
            if send(item.get('text','')):
                c+=1
            time.sleep(1.2)
        st.success(f"تم ارسال {c} من الأرشيف")

    # عرض سريع بدون KeyError
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for i,c in enumerate(data[:10]): # اعرض 10 فقط عشان ما يعلق
        st.markdown(f'<div class="box">{c.get("text","")}</div>', unsafe_allow_html=True)
