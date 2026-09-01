import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)

# ثبت الشركات - نفسها كل مرة بنفس الترتيب
WATCHLIST = ["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=20)
        if r.status_code!=200:
            st.error(f"Telegram فشل: {r.text}")
            return False
        return True
    except Exception as e:
        st.error(f"خطأ تيليجرام: {e}")
        return False

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
        if bid>0 and ask>0: return round((bid+ask)/2,2)
        return round(float(row['lastPrice'].iloc[0]),2)
    except: return None

st.set_page_config(layout="wide")
st.markdown("""<style>.box{background:#1e1e1e;color:#fff;padding:16px;border-radius:10px;
font-family:monospace;font-size:14px;line-height:1.7;border:1px solid #333;margin-bottom:12px}</style>""", unsafe_allow_html=True)

st.title("V99 موحد")

if st.button("🚀 فحص اليوم وحفظ + ارسال تيليجرام", use_container_width=True):
    success=0
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            curr=float(tk.fast_info.get('last_price') or tk.history(period="1d")['Close'].iloc[-1])
            # ثبت تاريخ واحد للكل 0-7 ايام فقط
            exp=None
            for e in tk.options[:2]:
                dte=(datetime.strptime(e, "%Y-%m-%d").date() - date.today()).days
                if 0 <= dte <= 7:
                    exp=e; break
            if not exp: continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            chain=tk.option_chain(exp)
            # اتجاه ثابت - لا يتغير كل بحث
            df=tk.history(period="5d")
            direction="CALL" if curr>float(df['Close'].mean()) else "PUT"
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            entry=round((row['bid']+row['ask'])/2,2)
            if entry<0.2: continue
            strike=row['strike']
            strike_s=int(strike) if strike==int(strike) else strike
            dr=tk.history(period="1d")
            low=round(float(dr['Low'].iloc[-1]),2)
            high=round(float(dr['High'].iloc[-1]),2)
            now_price = get_now_price(t, exp, strike, direction) or entry
            pnl=(now_price-entry)/entry*100
            status=f"⚪ شغال {pnl:+.1f}%" if abs(pnl)<50 else f"🟢 هدف {pnl:+.1f}%" if pnl>0 else f"🔴 وقف {pnl:+.1f}%"

            emoji="🔴" if direction=="PUT" else "🟢"
            unified = (
                f"{emoji} {t} {strike_s} {direction} 🐋\n"
                f"Exp: {exp} ({dte}d) Stock: ${round(curr,2)}\n"
                f"Range: ${low} - ${high}\n"
                f"Entry: ${entry} Bid: ${round(row['bid'],2)}\n"
                f"Stop: ${round(entry*0.5,2)}\n"
                f"Target: ${round(entry*1.5,2)} (+50%) | ${round(entry*2.3,2)} (+130%) | ${round(entry*3.2,2)} (+220%)\n"
                f"Now: ${now_price} | {status}"
            )
            st.markdown(f'<div class="box">{unified.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

            contract={"key":f"{t}_{strike}_{direction}_{exp}","ticker":t,"strike":float(strike),"dir":direction,"exp":exp,"entry":entry,"text":unified}
            save_daily(contract)

            if send(unified):
                success+=1
                st.caption(f"✅ انرسل {t}")
            else:
                st.caption(f"❌ ما انرسل {t}")
            time.sleep(1.5) # مهم عشان التيليجرام لا يبلّك
        except Exception as e:
            st.error(f"{t} خطأ: {e}")
            continue
    st.success(f"تم ارسال {success}/{len(WATCHLIST)} للتيليجرام")

st.divider()
st.subheader("📂 الأرشيف + زر تحديث الآن لكل عقد")
files=sorted(os.listdir(BASE), reverse=True)
days=[f.replace(".json","") for f in files]
sel=st.selectbox("اختر اليوم", days if days else ["لا يوجد"], key="sel_day")

if sel!="لا يوجد":
    fpath=os.path.join(BASE,f"{sel}.json")
    data=json.load(open(fpath, encoding='utf-8'))

    # زر تحديث الكل
    if st.button("🔄 تحديث الآن لكل العقود", key="update_all"):
        st.rerun()

    for i,c in enumerate(data):
        now_price = get_now_price(c['ticker'], c['exp'], c['strike'], c['dir'])
        if now_price is None: now_price=c['entry']
        pnl=(now_price-c['entry'])/c['entry']*100

        if now_price <= c['entry']*0.5: status=f"🔴 وقف {pnl:+.1f}%"
        elif now_price >= c['entry']*3.2: status=f"🟢 هدف 3 {pnl:+.1f}%"
        elif now_price >= c['entry']*2.3: status=f"🟢 هدف 2 {pnl:+.1f}%"
        elif now_price >= c['entry']*1.5: status=f"🟢 هدف 1 {pnl:+.1f}%"
        else: status=f"⚪ شغال {pnl:+.1f}%"

        base_text="\n".join([l for l in c['text'].split("\n") if not l.startswith("Now:")])
        updated_text=f"{base_text}\nNow: ${now_price} | {status}"

        st.markdown(f'<div class="box">{updated_text.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

        # زر تحديث لكل عقد لحاله
        col1,col2=st.columns(2)
        with col1:
            if st.button(f"🔄 تحديث {c['ticker']} {c['strike']}", key=f"upd_{sel}_{i}"):
                st.rerun()
        with col2:
            if st.button(f"📨 اعادة ارسال {c['ticker']}", key=f"resend_{sel}_{i}"):
                if send(updated_text):
                    st.toast(f"تم اعادة ارسال {c['ticker']}")
                else:
                    st.toast("فشل الارسال")
