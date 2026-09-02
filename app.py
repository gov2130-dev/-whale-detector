import streamlit as st, yfinance as yf, requests, json, os, time, re
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370" # تأكد انه نفس اللي في @userinfobot
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)

WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send_telegram(msg, debug_box=True):
    """ترسل وتطلع لك سبب الفشل بالتفصيل"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {'chat_id': CHAT_ID, 'text': msg} # بدون parse_mode عشان $ ما يخرب
        r = requests.post(url, data=payload, timeout=20)
        j = r.json()
        if debug_box:
            st.write(f"Telegram status: {r.status_code}")
            st.json(j)
        if r.status_code==200 and j.get('ok'):
            return True
        else:
            if debug_box:
                st.error(f"سبب الفشل: {j}")
            return False
    except Exception as e:
        st.error(f"Exception telegram: {e}")
        return False

def today_file(): return os.path.join(BASE, f"{date.today()}.json")
def get_fibo(high, low, direction):
    diff=high-low
    if diff<=0: diff=1.0
    if direction=="PUT":
        t1=low - diff*0.382; t2=low - diff*0.618; t3=low - diff*1.0
    else:
        t1=high + diff*0.382; t2=high + diff*0.618; t3=high + diff*1.0
    return round(t1,2), round(t2,2), round(t3,2)

def get_now(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==strike]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0); ask=float(row['ask'].iloc[0] or 0)
        if bid>0 and ask>0: return round((bid+ask)/2,2)
        return round(float(row['lastPrice'].iloc[0]),2)
    except: return None

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>""", unsafe_allow_html=True)

# === اختبار تيليجرام لحاله ===
st.subheader("🔧 اختبار تيليجرام")
if st.button("اختبر الارسال الآن"):
    ok = send_telegram("✅ اختبار البوت شغال - V99")
    if ok:
        st.success("البوت يرسل تمام - المشكلة كانت من قبل في $ او sleep")
    else:
        st.error("ما يرسل - لازم تروح للبوت وتضغط /start")

    # جيب اخر تحديثات البوت عشان تعرف CHAT_ID الصحيح
    try:
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", timeout=10).json()
        st.write("اخر محادثات البوت - انسخ chat_id الصحيح من هنا:")
        st.json(r)
    except Exception as e:
        st.error(str(e))

st.divider()
st.title("V99 - نهائي")

if st.button("🚀 فحص وارسال", use_container_width=True):
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

            fpath=today_file()
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d['key']==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)

            if send_telegram(txt, debug_box=False):
                st.caption(f"✅ {t}")
            else:
                st.caption(f"❌ فشل {t} - شف الخطأ فوق")
            time.sleep(2) # زودناها ل 2 ثانية عشان ما يبلّك
        except Exception as e:
            st.error(f"{t}: {e}")

# الارشيف مثل قبل
st.divider()
files=sorted(os.listdir(BASE), reverse=True)
days=[f.replace(".json","") for f in files]
sel=st.selectbox("اختر اليوم", days if days else ["لا يوجد"])
if sel!="لا يوجد":
    if st.button("🔄 تحديث الان", use_container_width=True): st.rerun()
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for i,c in enumerate(data):
        high=c.get('high',0); low=c.get('low',0)
        if high==0 or low==0:
            m=re.search(r"Range: \$(.*?) - \$(.*?)\n", c['text'])
            if m: low=float(m.group(1)); high=float(m.group(2))
        now_p=get_now(c['ticker'], c['exp'], c['strike'], c['dir']) or c.get('entry',0)
        entry=c.get('entry',now_p); pnl=(now_p-entry)/entry*100 if entry else 0
        ft1,ft2,ft3=get_fibo(high, low, c['dir'])
        stt=f"وقف {pnl:+.1f}%" if now_p<=entry*0.5 else f"هدف {pnl:+.1f}%" if now_p>=entry*1.5 else f"شغال {pnl:+.1f}%"
        base="\n".join([l for l in c['text'].split("\n") if not l.startswith("Target Stock:") and not l.startswith("Now:")])
        updated=f"{base}\nTarget Stock: {ft1:.2f} > {ft2:.2f} > {ft3:.2f} (Fibo)\nNow: ${now_p:.2f} | {stt} | {datetime.now().strftime('%H:%M:%S')}"
        st.markdown(f'<div class="box">{updated}</div>', unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            if st.button(f"🔄 {c['ticker']}", key=f"u_{sel}_{i}"): st.rerun()
        with col2:
            if st.button(f"📨 {c['ticker']}", key=f"s_{sel}_{i}"):
                send_telegram(updated)
