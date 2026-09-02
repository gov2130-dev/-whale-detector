import streamlit as st, yfinance as yf, requests, json, os, time, re
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

def get_fibo(high, low, direction):
    try:
        high=float(high); low=float(low)
    except:
        high=low=0
    diff=high-low
    if diff<=0: diff=1.0
    if direction=="PUT":
        return round(low-diff*0.382,2), round(low-diff*0.618,2), round(low-diff*1.0,2)
    else:
        return round(high+diff*0.382,2), round(high+diff*0.618,2), round(high+diff*1.0,2)

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
            bid_c=round(float(row['bid']),2)

            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now_fast(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            emoji="🟢" if direction=="CALL" else "🔴"

            txt=(f"{emoji} {t} {strike_s} {direction} 🐳\n"
                 f"Exp: {exp} ({dte}d) Stock: ${curr:.2f}\n"
                 f"Entry: ${entry} Bid: ${bid_c}\n"
                 f"Stop: ${entry*0.5:.1f}\n"
                 f"Target: ${entry*1.5:.1f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\n"
                 f"Target Stock: {ft1} > {ft2} > {ft3} (Fibo)\n"
                 f"Now: ${now_p} | {pnl:+.1f}% شغال\n{datetime.now().strftime('%H:%M:%S')}")

            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)

            fpath=today_file()
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d.get('key')==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
                send(txt)
                st.success(f"تم ارسال {t}")

            time.sleep(1)
        except Exception as e:
            st.error(f"{t}: {e}")

st.divider()
st.subheader("الأرشيف")

files=sorted([f for f in os.listdir(BASE) if f.endswith(".json")], reverse=True)
if not files:
    st.write("لا يوجد")
else:
    sel=st.selectbox("اختر اليوم", [f.replace(".json","") for f in files])
    fpath=os.path.join(BASE, f"{sel}.json")
    try:
        raw=open(fpath, encoding='utf-8').read()
        data=json.loads(raw)
    except:
        data=[]

    if st.button("🔄 تحديث سريع"):
        get_now_fast.clear()
        st.rerun()

    for i,c in enumerate(data):
        try:
            # قراءة آمنة - ما يعلق لو الملف قديم
            high=c.get('high',0); low=c.get('low',0)
            if high==0 or low==0:
                m=re.search(r"Range:.*?\$(.*?) - \$(.*?)\n", c.get('text',''))
                if m:
                    try:
                        low=float(m.group(1)); high=float(m.group(2))
                    except: pass

            # لو لسه صفر جيبه من ياهو
            if high==0 or low==0:
                try:
                    tk=yf.Ticker(c.get('ticker','SPY'))
                    h=tk.history(period="1d")
                    high=round(float(h['High'].iloc[-1]),2); low=round(float(h['Low'].iloc[-1]),2)
                except:
                    high=low=0

            entry=c.get('entry',0)
            exp=c.get('exp',''); strike=c.get('strike',0); direction=c.get('dir','CALL')
            now_p=get_now_fast(c.get('ticker',''), exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            ft1,ft2,ft3=get_fibo(high, low, direction)

            base_txt=c.get('text','').split("Target Stock:")[0] if "Target Stock:" in c.get('text','') else c.get('text','')
            updated=f"{base_txt}Target Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p} | {pnl:+.1f}% | {datetime.now().strftime('%H:%M:%S')}"

            st.markdown(f'<div class="box">{updated}</div>', unsafe_allow_html=True)

            c1,c2=st.columns(2)
            with c1:
                if st.button(f"🔄 {c.get('ticker','')}", key=f"u_{sel}_{i}"):
                    get_now_fast.clear()
                    st.rerun()
            with c2:
                if st.button(f"📨 {c.get('ticker','')}", key=f"s_{sel}_{i}"):
                    send(updated)
                    st.toast("تم الارسال")
        except Exception as e:
            st.warning(f"تخطي عقد تالف {i}: {e}")
            continue
