import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return True
    except:
        return False

def today_file(): return os.path.join(BASE, f"{date.today()}.json")

def get_fibo(high, low, direction):
    diff = high - low
    if diff <= 0: diff = 1.0
    # تصحيح: لازم نضيف للهاي / نطرح من اللو
    if direction == "PUT":
        t1 = low - diff*0.382
        t2 = low - diff*0.618
        t3 = low - diff*1.0
    else:
        t1 = high + diff*0.382
        t2 = high + diff*0.618
        t3 = high + diff*1.0
    return round(t1,2), round(t2,2), round(t3,2)

@st.cache_data(ttl=20) # تحديث كل 20 ثانية فقط عشان السرعة
def get_now_fast(ticker, exp, strike, direction):
    try:
        tk = yf.Ticker(ticker)
        chain = tk.option_chain(exp)
        opts = chain.calls if direction=="CALL" else chain.puts
        row = opts[opts['strike']==strike]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0); ask=float(row['ask'].iloc[0] or 0)
        return round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row['lastPrice'].iloc[0]),2)
    except:
        return None

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>""", unsafe_allow_html=True)

# زر واحد يفحص ويرسل تلقائيا
if st.button("🚀 فحص وارسال تلقائي للتيليجرام", use_container_width=True, type="primary"):
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="1d")
            if hist.empty: continue
            curr=round(float(tk.fast_info.get('last_price') or hist['Close'].iloc[-1]),2)
            high=round(float(hist['High'].iloc[-1]),2); low=round(float(hist['Low'].iloc[-1]),2)
            exp=None
            for e in tk.options[:3]:
                dte=(datetime.strptime(e, "%Y-%m-%d").date() - date.today()).days
                if 0 <= dte <= 7: exp=e; break
            if not exp: continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            chain=tk.option_chain(exp)
            direction="CALL" if curr>float(tk.history(period="5d")['Close'].mean()) else "PUT"
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            entry=round((float(row['bid'])+float(row['ask']))/2,2)
            if entry<0.2: continue
            strike=float(row['strike']); strike_s=int(strike) if strike==int(strike) else strike
            close_c=round(float(row.get('lastPrice',entry) or entry),2); bid_c=round(float(row['bid']),2)

            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now_fast(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            stt=f"شغال {pnl:+.1f}%" if abs(pnl)<50 else f"هدف {pnl:+.1f}%" if pnl>0 else f"وقف {pnl:+.1f}%"
            emoji="🟢" if direction=="CALL" else "🔴"

            txt=(f"{emoji} {t} {strike_s} {direction} 🐳\nExp: {exp} ({dte}d) Stock: ${curr:.2f}\nEntry: ${entry} Bid: ${bid_c}\nStop: ${entry*0.5:.1f}\nTarget: ${entry*1.5:.1f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\nTarget Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p} | ⚪️ | {pnl:+.1f}% شغال\n{datetime.now().strftime('%H:%M:%S')}")

            # حفظ + ارسال تلقائي مباشرة بدون ما تضغط ايقونة الشركة
            fpath=today_file()
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d['key']==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
                send(txt) # يرسل فقط العقود الجديدة تلقائيا
                st.toast(f"تم ارسال {t}")

            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)
            time.sleep(0.8)
        except Exception as e:
            st.error(f"{t}: {e}")

# الأرشيف
st.divider()
files=sorted(os.listdir(BASE), reverse=True)
sel=st.selectbox("الأرشيف", [f.replace(".json","") for f in files] if files else ["لا يوجد"])
if sel!="لا يوجد":
    if st.button("🔄 تحديث سريع"):
        get_now_fast.clear()
        st.rerun()
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for i,c in enumerate(data):
        now_p=get_now_fast(c['ticker'], c['exp'], c['strike'], c['dir']) or c['entry']
        pnl=(now_p-c['entry'])/c['entry']*100 if c['entry'] else 0
        ft1,ft2,ft3=get_fibo(c['high'], c['low'], c['dir'])
        txt=c['text'].split("Target Stock:")[0] + f"Target Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p} | {pnl:+.1f}% | {datetime.now().strftime('%H:%M:%S')}"
        st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            if st.button(f"🔄 {c['ticker']}", key=f"u_{sel}_{i}"):
                get_now_fast.clear()
                st.rerun()
        with col2:
            if st.button(f"📨 {c['ticker']}", key=f"s_{sel}_{i}"):
                send(txt)
