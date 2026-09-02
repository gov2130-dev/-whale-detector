import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return True
    except:
        return False

def today_file(): return os.path.join(BASE, f"{date.today()}.json")
def get_fibo(h,l,d):
    diff=(h-l) or 1.0
    if d=="PUT": return round(l-diff*0.382,2), round(l-diff*0.618,2), round(l-diff*1.0,2)
    return round(h+diff*0.382,2), round(h+diff*0.618,2), round(h+diff*1.0,2)

@st.cache_data(ttl=20)
def get_now_fast(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==float(strike)]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0); ask=float(row['ask'].iloc[0] or 0)
        return round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row['lastPrice'].iloc[0]),2)
    except:
        return None

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>""", unsafe_allow_html=True)

if st.button("🚀 فحص وارسال تلقائي للتيليجرام", use_container_width=True, type="primary"):
    sent=0
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="5d")
            if hist.empty: continue
            curr=round(float(hist['Close'].iloc[-1]),2)
            high=round(float(hist['High'].iloc[-1]),2); low=round(float(hist['Low'].iloc[-1]),2)
            exp=tk.options[0] if tk.options else None
            if not exp: continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if dte<0 and len(tk.options)>1:
                exp=tk.options[1]
                dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            chain=tk.option_chain(exp)
            direction="CALL" if curr>float(hist['Close'].mean()) else "PUT"
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            bid=float(row['bid'] or 0); ask=float(row['ask'] or 0)
            entry=round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row.get('lastPrice',0) or 0),2)
            if entry<0.05: continue
            strike=float(row['strike']); strike_s=int(strike) if strike==int(strike) else strike
            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now_fast(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            emoji="🟢" if direction=="CALL" else "🔴"
            txt=(f"{emoji} {t} {strike_s} {direction} 🐳\nExp: {exp} ({dte}d) Stock: ${curr:.2f}\nEntry: ${entry} Bid: ${bid}\nStop: ${entry*0.5:.1f}\nTarget: ${entry*1.5:.1f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\nTarget Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p} | {pnl:+.1f}% شغال\n{datetime.now().strftime('%H:%M:%S')}")
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
            continue
    st.success(f"تم ارسال {sent} عقد")

st.divider()
files=sorted([f for f in os.listdir(BASE) if f.endswith(".json")], reverse=True)
if files:
    sel=st.selectbox("الأرشيف", [f.replace(".json","") for f in files])
    if st.button("📨 ارسال كل عقود اليوم المختار"):
        data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
        for item in data:
            send(item.get('text',''))
            time.sleep(1)
        st.success("تم")
