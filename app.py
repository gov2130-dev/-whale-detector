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

def today_file(): return os.path.join(BASE, f"{date.today()}.json")

def save_daily(contract):
    f=today_file()
    data=json.load(open(f, encoding='utf-8')) if os.path.exists(f) else []
    if not any(d['key']==contract['key'] for d in data):
        data.append(contract)
        json.dump(data, open(f,"w",encoding='utf-8'), ensure_ascii=False, indent=2)

def get_now_price(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==strike]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0)
        ask=float(row['ask'].iloc[0] or 0)
        if bid>0 and ask>0:
            return round((bid+ask)/2,2)
        return round(float(row['lastPrice'].iloc[0]),2)
    except: return None

st.set_page_config(layout="wide")
st.markdown("""
<style>
.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;
font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:14px;white-space:pre-wrap}
</style>
""", unsafe_allow_html=True)

st.title("📅 V99 - شكل موحد + Now")

if st.button("🚀 فحص اليوم وحفظ", use_container_width=True):
    for t in ["SPY","QQQ","AAPL","META","AMD","IWM","SOFI","COIN","HOOD","NVDA","TSLA"]:
        try:
            tk=yf.Ticker(t)
            curr=float(tk.fast_info.get('last_price') or tk.history(period="1d")['Close'].iloc[-1])
            exp=tk.options[1] if len(tk.options)>1 else tk.options[0]
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if dte<1 or dte>7: continue
            chain=tk.option_chain(exp)
            is_put = curr < float(tk.history(period="5d")['Close'].mean())
            opts=chain.puts if is_put else chain.calls
            direction="PUT" if is_put else "CALL"
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            entry=round((row['bid']+row['ask'])/2,2)
            if entry<0.3: continue
            strike=int(row['strike']) if row['strike']==int(row['strike']) else row['strike']
            dr=tk.history(period="1d")
            low=round(float(dr['Low'].iloc[-1]),2)
            high=round(float(dr['High'].iloc[-1]),2)
            close_c=round(float(row.get('lastPrice',entry) or entry),2)

            # السعر الحالي Now
            now_price = get_now_price(t, exp, row['strike'], direction) or entry
            pnl = (now_price-entry)/entry*100

            if now_price <= entry*0.5: status=f"🔴 وقف {pnl:+.1f}%"
            elif now_price >= entry*3.2: status=f"🟢 هدف 3 {pnl:+.1f}%"
            elif now_price >= entry*2.3: status=f"🟢 هدف 2 {pnl:+.1f}%"
            elif now_price >= entry*1.5: status=f"🟢 هدف 1 {pnl:+.1f}%"
            else: status=f"⚪ شغال {pnl:+.1f}%"

            emoji="🔴" if direction=="PUT" else "🟢"
            # نص موحد 100% للموقع والتيليجرام
            unified_text = (
                f"{emoji} {t} {strike} {direction} 🐋\n"
                f"Exp: {exp} ({dte}d) Stock: ${round(curr,2)} BW {round(abs(strike-curr)/curr*100,2)}%\n"
                f"Range: ${low} - ${high}\n"
                f"Close: ${close_c}\n"
                f"Entry: ${entry} Bid: ${round(row['bid'],2)}\n"
                f"Stop: ${round(entry*0.5,2)}\n"
                f"Target Stock: {round(strike-0.3,2) if direction=='PUT' else round(strike+0.3,2)} > {round(strike-0.6,2) if direction=='PUT' else round(strike+0.6,2)} > {round(strike-1.0,2) if direction=='PUT' else round(strike+1.0,2)}\n"
                f"Target Contract: ${round(entry*1.5,2)} (+50%) | ${round(entry*2.3,2)} (+130%) | ${round(entry*3.2,2)} (+220%)\n"
                f"Now: ${now_price} | {status}"
            )

            contract={"key":f"{t}_{strike}_{direction}_{exp}","ticker":t,"strike":float(row['strike']),"dir":direction,"exp":exp,"entry":entry,"text":unified_text,"time":datetime.now().strftime("%H:%M")}
            save_daily(contract)

            # نفس النص في الموقع والتيليجرام
            st.markdown(f'<div class="box">{unified_text}</div>', unsafe_allow_html=True)
            send(unified_text)
            time.sleep(0.5)
        except Exception as e:
            continue

st.divider()
st.subheader("📂 الأرشيف - نفس الشكل مع تحديث Now")
files=sorted(os.listdir(BASE), reverse=True)
days=[f.replace(".json","") for f in files]
sel=st.selectbox("اختر اليوم", days if days else ["لا يوجد"])

if sel!="لا يوجد":
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for c in data:
        now_price = get_now_price(c['ticker'], c['exp'], c['strike'], c['dir']) or c['entry']
        pnl=(now_price-c['entry'])/c['entry']*100
        if now_price <= c['entry']*0.5: status=f"🔴 وقف {pnl:+.1f}%"
        elif now_price >= c['entry']*3.2: status=f"🟢 هدف 3 {pnl:+.1f}%"
        elif now_price >= c['entry']*2.3: status=f"🟢 هدف 2 {pnl:+.1f}%"
        elif now_price >= c['entry']*1.5: status=f"🟢 هدف 1 {pnl:+.1f}%"
        else: status=f"⚪ شغال {pnl:+.1f}%"

        # نحدث سطر Now فقط
        lines=c['text'].split("\n")
        lines=[l for l in lines if not l.startswith("Now:")]
        lines.append(f"Now: ${now_price} | {status} | تحديث الآن")
        updated="\n".join(lines)

        st.markdown(f'<div class="box">{updated}</div>', unsafe_allow_html=True)
