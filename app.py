import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={'chat_id':CHAT_ID,'text':msg}, timeout=20)
        print(r.text) # عشان تشوف الخطأ بالكونسول
        return r.json().get('ok', False)
    except Exception as e:
        print(e)
        return False

def today_file(): return os.path.join(BASE, f"{date.today()}.json")
def get_fibo(h,l,d):
    diff=h-l or 1.0
    if d=="PUT": return round(l-diff*0.382,2), round(l-diff*0.618,2), round(l-diff*1.0,2)
    else: return round(h+diff*0.382,2), round(h+diff*0.618,2), round(h+diff*1.0,2)

def get_now(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==strike]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0); ask=float(row['ask'].iloc[0] or 0)
        return round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row['lastPrice'].iloc[0]),2)
    except: return None

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>""", unsafe_allow_html=True)

if st.button("🚀 فحص وارسال", use_container_width=True):
    all_msgs = [] # نجمع كل العقود برسالة وحدة مثل القديم
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
            bw=round(abs(strike-curr)/curr*100,2)
            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            stt=f"شغال {pnl:+.1f}%" if abs(pnl)<50 else f"هدف {pnl:+.1f}%" if pnl>0 else f"وقف {pnl:+.1f}%"
            emoji="🔴" if direction=="PUT" else "🟢"
            txt=(f"{emoji} {t} {strike_s} {direction}\nExp: {exp} ({dte}d) Stock: ${curr:.2f} BW {bw:.2f}%\nRange: ${low:.2f} - ${high:.2f}\nClose: ${close_c:.2f}\nEntry: ${entry:.2f} Bid: ${bid_c:.2f}\nStop: ${entry*0.5:.2f}\nTarget Stock: {ft1:.2f} > {ft2:.2f} > {ft3:.2f} (Fibo)\nTarget Contract: ${entry*1.5:.2f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\nNow: ${now_p:.2f} | {stt}")
            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)
            all_msgs.append(txt)

            fpath=today_file()
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d['key']==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"{t}: {e}")

    # ارسال مجمّع مثل الكود القديم - رسالة وحدة فقط = ما فيه بلوك
    if all_msgs:
        final_msg = "\n\n---\n\n".join(all_msgs)
        if send(final_msg):
            st.success(f"✅ تم ارسال {len(all_msgs)} عقد برسالة واحدة - مثل القديم")
        else:
            # لو الرسالة طويلة جدا، ارسلها كل 3 عقود مع بعض
            st.warning("الرسالة طويلة، بجرب اقسمها")
            for i in range(0, len(all_msgs), 3):
                chunk = "\n\n---\n\n".join(all_msgs[i:i+3])
                send(chunk)
                time.sleep(1)

st.divider()
st.subheader("الارشيف")
files=sorted(os.listdir(BASE), reverse=True)
days=[f.replace(".json","") for f in files]
sel=st.selectbox("اختر اليوم", days if days else ["لا يوجد"])
if sel!="لا يوجد":
    if st.button("🔄 تحديث"): st.rerun()
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for i,c in enumerate(data):
        st.markdown(f'<div class="box">{c["text"]}</div>', unsafe_allow_html=True)
        if st.button(f"📨 {c['ticker']}", key=f"s_{sel}_{i}"):
            send(c['text'])
            st.success("ارسل")
