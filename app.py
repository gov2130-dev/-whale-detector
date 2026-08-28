import streamlit as st, requests

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data, timeout=10)
    return r.status_code == 200

st.title("V99.1 - اختبار البوت")

if st.button("اختبار تلجرام"):
    if send_telegram("اختبار ناجح - البوت شغال لحظي"):
        st.success("نجح - وصلت الرسالة")
    else:
        st.error("فشل - راجع التوكن")

st.write("اذا ظهر هذا النص فالكود صحيح")    if send_telegram("✅ اختبار ناجح - البوت شغال لحظي الآن!"):
        st.success("نجح ✅ - راحت الرسالة للتلجرام")
    else:
        st.error("فشل - تأكد من BOT_TOKEN و CHAT_ID في Secrets")

st.divider()

# هنا تحط باقي كود فحص العملات اللي كان عندك
# مثال بسيط:
coins = ["BTC-USD", "ETH-USD", "SOL-USD"]
for coin in coins:
    try:
        data = yf.download(coin, period="1d", interval="1m", progress=False)
        price = float(data['Close'].iloc[-1])
        st.write(f"🟢 {coin} = ${price:,.2f}")
    except:
        st.write(f"⚪ {coin} - جاري التحميل...")    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False, "", "no data"
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100
        high_t=float(daily['High'].iloc[-1])
        low_t=float(daily['Low'].iloc[-1])
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8:
            return True, "CALL", f"CALL {chg:.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8:
            return True, "PUT", f"PUT {chg:.1f}%"
        else:
            return False, "", f"حيادي {chg:.1f}%"
    except: return False, "", "error"

def get_contract_dir(ticker, direction):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,tk = get_data(ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=curr_real
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.04)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_opt*0.96) & (opts['strike']<=curr_opt*0.998)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if not (1.0 <= last <= 4.0): continue
                    if bid < 0.65 or (ask-bid) > 0.25: continue
                    if vol < 200 and oi < 800: continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"type":direction}
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.01:.1f} → {base*1.025:.1f} → {base*1.04:.1f}"; emoji="🟢"
    else:
        tg=f"{base*0.99:.1f} → {base*0.975:.1f} → {base*0.96:.1f}"; emoji="🔴"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم: {tg}
🎯 اهداف العقد: T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%)"""

st.title("V99.1 AUTO - CALL و PUT تحت 4$")
ksa_now=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | 54 شركة")

colA,colB,colC=st.columns(3)
with colA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        if send(f"✅ V99.1 شغال - {ksa_now}\n🟢 CALL + 🔴 PUT"): st.success("انرسل ✅ شيك تلجرام")
        else: st.error("فشل - تأكد من النت")
with colB:
    if st.button("🗑️ تصفير المرسلة"):
        save(SENT_FILE, []); st.success("تصفر ✅")
with colC:
    mins=st.selectbox("كل كم دقيقة يحدث؟", [2,5,10,15,30], index=1)

sent=load(SENT_FILE)
st.metric("المرسلة اليوم", len(sent))

if st.button(f"🔍 افحص الآن 54", type="primary"):
    call_c=put_c=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, _ = is_strong_both(t)
        if ok:
            c=get_contract_dir(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    st.code(build_msg(c))
                    if send(build_msg(c)):
                        if c['type']=="CALL": call_c+=1
                        else: put_c+=1
                        sent.append(key); save(SENT_FILE, sent)
        prog.progress((i+1)/len(WATCHLIST_54))
    st.success(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c}")

st.divider()
auto=st.checkbox(f"🚀 شغل التحديث التلقائي كل {mins} دقايق", value=False)

if auto:
    st.info(f"🔄 التحديث التلقائي شغال كل {mins} دقايق - لا تسكر الصفحة - {ksa_now}")
    
    # فحص تلقائي
    new_found=[]
    for t in WATCHLIST_54:
        ok, direction, _ = is_strong_both(t)
        if ok:
            c=get_contract_dir(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    if send(build_msg(c)):
                        sent.append(key); new_found.append(f"{c['type']} {t}")
    
    if new_found:
        save(SENT_FILE, sent)
        st.success(f"✅ أرسل تلقائي الآن: {', '.join(new_found)}")
    else:
        st.write(f"⏸️ ما فيه جديد - بنفحص بعد {mins} دقايق")
    
    st.caption(f"آخر فحص: {ksa_now} - بيحدث بعد {mins} دقايق")
    time.sleep(mins*60)
    st.rerun()
