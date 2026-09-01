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
        return r.status_code==200, r.text
    except Exception as e: return False, str(e)

def today_file(): return os.path.join(BASE, f"{date.today()}.json")

def get_fibo_targets(high, low, direction):
    diff=high-low
    if direction=="PUT": # نزول - امتداد تحت القاع
        t1=low - diff*0.382
        t2=low - diff*0.618
        t3=low - diff*1.0
    else: # صعود - امتداد فوق القمة
        t1=high + diff*0.382
        t2=high + diff*0.618
        t3=high + diff*1.0
    return round(t1,2), round(t2,2), round(t3,2)

def get_now(ticker, exp, strike, direction):
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
st.markdown("""<style>
.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;
font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:10px}
</style>""", unsafe_allow_html=True)

st.title("V99 - استايل الصورة + فيبو + تحديث")

if st.button("🚀 فحص وحفظ وارسال", use_container_width=True):
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="1d")
            if hist.empty: continue
            curr=float(tk.fast_info.get('last_price') or hist['Close'].iloc[-1])
            high=float(hist['High'].iloc[-1]); low=float(hist['Low'].iloc[-1])

            exp=None
            for e in tk.options[:2]:
                dte=(datetime.strptime(e, "%Y-%m-%d").date() - date.today()).days
                if 0 <= dte <= 7: exp=e; break
            if not exp: continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            chain=tk.option_chain(exp)
            direction="CALL" if curr>float(tk.history(period="5d")['Close'].mean()) else "PUT"
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            entry=round((row['bid']+row['ask'])/2,2)
            if entry<0.2: continue
            strike=float(row['strike'])
            strike_s=int(strike) if strike==int(strike) else strike

            close_c=round(float(row.get('lastPrice',entry) or entry),2)
            bw=round(abs(strike-curr)/curr*100,2)

            # فيبو
            ft1,ft2,ft3=get_fibo_targets(high, low, direction)

            now_p=get_now(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            if now_p<=entry*0.5: stt=f"🔴 وقف {pnl:+.1f}%"
            elif now_p>=entry*3.2: stt=f"🟢 هدف 3 {pnl:+.1f}%"
            elif now_p>=entry*2.3: stt=f"🟢 هدف 2 {pnl:+.1f}%"
            elif now_p>=entry*1.5: stt=f"🟢 هدف 1 {pnl:+.1f}%"
            else: stt=f"⚪ شغال {pnl:+.1f}%"

            emoji="🔴" if direction=="PUT" else "🟢"
            # نفس استايل الصورة بالحرف
            txt=(
                f"{emoji} {t} {strike_s} {direction} 🐋\n"
                f"Exp: {exp} ({dte}d) Stock: ${round(curr,2)} BW {bw}%\n"
                f"Range: ${low} - ${high}\n"
                f"Close: ${close_c}\n"
                f"Entry: ${entry} Bid: ${round(row['bid'],2)}\n"
                f"Stop: ${round(entry*0.5,2)}\n"
                f"Target Stock: {ft1} > {ft2} > {ft3} (Fibo {high}->{low})\n"
                f"Target Contract: ${round(entry*1.5,2)} (+50%) | ${round(entry*2.3,2)} (+130%) | ${round(entry*3.2,2)} (+220%)\n"
                f"Now: ${now_p} | {stt}"
            )
            st.markdown(f'<div class="box">{txt.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)

            # حفظ
            f=today_file()
            data=json.load(open(f, encoding='utf-8')) if os.path.exists(f) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d['key']==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt,"time":datetime.now().strftime("%H:%M")})
                json.dump(data, open(f,"w",encoding='utf-8'), ensure_ascii=False, indent=2)

            ok,msg=send(txt)
            st.caption(f"{'✅' if ok else '❌ '+msg} {t}")
            time.sleep(1.5)
        except Exception as e:
            st.error(f"{t}: {e}")

st.divider()
st.subheader("📂 الأرشيف - تحديث مباشر")
files=sorted(os.listdir(BASE), reverse=True)
days=[f.replace(".json","") for f in files]
sel=st.selectbox("اليوم", days if days else ["لا يوجد"])

if sel!="لا يوجد":
    if st.button("🔄 تحديث الآن كل العقود", use_container_width=True):
        st.rerun()
    data=json.load(open(os.path.join(BASE,f"{sel}.json"), encoding='utf-8'))
    for i,c in enumerate(data):
        now_p=get_now(c['ticker'], c['exp'], c['strike'], c['dir']) or c['entry']
        pnl=(now_p-c['entry'])/c['entry']*100
        ft1,ft2,ft3=get_fibo_targets(c['high'], c['low'], c['dir'])

        if now_p<=c['entry']*0.5: stt=f"🔴 وقف {pnl:+.1f}%"
        elif now_p>=c['entry']*3.2: stt=f"🟢 هدف 3 {pnl:+.1f}%"
        elif now_p>=c['entry']*2.3: stt=f"🟢 هدف 2 {pnl:+.1f}%"
        elif now_p>=c['entry']*1.5: stt=f"🟢 هدف 1 {pnl:+.1f}%"
        else: stt=f"⚪ شغال {pnl:+.1f}%"

        # نفس الاستايل مع تحديث Now واهداف فيبو
        lines=[l for l in c['text'].split("\n") if not l.startswith("Target Stock:") and not l.startswith("Now:")]
        # اعادة بناء سطر فيبو و Now
        new_txt="\n".join(lines[:6]) + f"\nTarget Stock: {ft1} > {ft2} > {ft3} (Fibo {c['high']}->{c['low']})\n" + "\n".join(lines[6:])
        # احذف Now القديم ان وجد وضيف جديد
        new_txt="\n".join([l for l in new_txt.split("\n") if not l.startswith("Now:")]) + f"\nNow: ${now_p} | {stt} | تحديث {datetime.now().strftime('%H:%M:%S')}"

        st.markdown(f'<div class="box">{new_txt.replace(chr(10),"<br>")}</div>', unsafe_allow_html=True)
        c1,c2=st.columns(2)
        with c1:
            if st.button(f"🔄 تحديث {c['ticker']}", key=f"u_{sel}_{i}"):
                st.rerun()
        with c2:
            if st.button(f"📨 ارسل {c['ticker']}", key=f"s_{sel}_{i}"):
                send(new_txt)
                st.toast("انرسل")        opts=chain.calls if direction=="CALL" else chain.puts
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
