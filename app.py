import requests, time, threading
BOT_TOKEN="حط_توكنك_الجديد_هنا"
CHAT_ID="13889370"

# تابع سعر السهم لحظيا
def get_price(symbol):
    try:
        # من Yahoo Finance
        r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1m&range=1d", headers={"User-Agent":"Mozilla"}, timeout=5).json()
        return r['chart']['result'][0]['meta']['regularMarketPrice']
    except:
        return None

# ارسال رسالة
def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID, "text":msg})

# امر /check
def check_symbol(symbol):
    price=get_price(symbol)
    if not price:
        send(f"❌ ما قدرت اجيب سعر {symbol}")
        return
    send(f"📈 {symbol} سعره الان: ${price}\n\nاذا نزل عن اهداف البوت اللي ارسلناها = الهدف تحقق ✅\nاذا طلع عن الستوب = ضرب ستوب 🔴")

# مراقب رسائل تلجرام
def listen():
    offset=0
    while True:
        try:
            r=requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={offset}&timeout=30").json()
            for u in r.get('result',[]):
                offset=u['update_id']+1
                text=u.get('message',{}).get('text','')
                if text.startswith('/check'):
                    parts=text.split()
                    if len(parts)>=2:
                        check_symbol(parts[1].upper())
                    else:
                        send("اكتب: /check NVDL")
        except:
            time.sleep(5)

threading.Thread(target=listen, daemon=True).start()    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False,"",0,""
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100
        high_t=float(daily['High'].iloc[-1])
        low_t=float(daily['Low'].iloc[-1])
        if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8: return True, "CALL", chg, f"CALL {chg:+.1f}%"
        elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8: return True, "PUT", chg, f"PUT {chg:+.1f}%"
        else: return False,"",chg,""
    except: return False,"",0,""
def get_contract(ticker, direction):
    market_open = is_market_open()
    try:
        curr_real,_,tk = get_data(ticker)
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:4]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (0 <= days <= (10 if market_open else 14)): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL": opts=opts[(opts['strike']>=curr_real*0.98) & (opts['strike']<=curr_real*1.06)].sort_values('strike')
            else: opts=opts[(opts['strike']>=curr_real*0.94) & (opts['strike']<=curr_real*1.02)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                try:
                    last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0); vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                    if market_open:
                        if not (1.0 <= last <= 4.0): continue
                        if bid < 0.65: continue
                    else:
                        if not (0.40 <= last <= 6.0): continue
                    mode = "LIVE" if market_open else "PRE"
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"mode":mode}
                except: continue
    except: pass
    return None
def build_msg(c, reason):
    base=c['curr']; last=c['last']; emoji="🟢" if c['type']=="CALL" else "🔴"
    if c['type']=="CALL": t1=base*1.01; t2=base*1.025; t3=base*1.04
    else: t1=base*0.99; t2=base*0.975; t3=base*0.96
    return f"{emoji} {c['ticker']} {c['strike']} {c['type']} {c['mode']} - {reason}\nExp: {c['exp']} ({c['days']}d) Stock: ${base:.2f}\nEntry: ${last:.2f} Bid: ${c['bid']:.2f} Vol: {c['vol']} OI: {c['oi']}\nStop: ${last*0.55:.2f}\nTarget Stock: {t1:.1f} > {t2:.1f} > {t3:.1f}\nTarget Contract: ${last*1.5:.2f} (+50%) | ${last*2.3:.2f} (+130%) | ${last*3.2:.2f} (+220%)"
st.title("V99 - عقود مرتبة من الاقوى")
ksa_time = datetime.now(RIYADH).strftime("%H:%M:%S")
ny_time = datetime.now(NY).strftime("%H:%M")
m_status = "LIVE السوق فاتح" if is_market_open() else "PRE السوق مقفل"
st.caption(f"الرياض {ksa_time} | نيويورك {ny_time} | {m_status}")
col1,col2 = st.columns(2)
with col1:
    if st.button("📨 اختبار تلجرام", type="primary"):
        ok = send("✅ V99 شغال - اختبار")
        if ok: st.success("انرسل ✅ شيك تلجرام")
        else: st.error("فشل")
with col2:
    if st.button("🗑️ تصفير المرسلة"): save([]); st.success("تصفر ✅")
    st.metric("المرسلة اليوم", len(load()))
sent = load()
if st.button("🔍 افحص 54 - الاقوى اول", type="primary"):
    prog = st.progress(0)
    candidates = []
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, chg, reason = is_strong(t)
        if ok: candidates.append((abs(chg), chg, t, direction, reason))
        prog.progress((i+1)/len(WATCHLIST_54)*0.5)
    candidates.sort(key=lambda x: x[0], reverse=True)
    call_c = 0; put_c = 0
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c = get_contract(t, direction)
        if not c: continue
        key = f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: continue
        msg = build_msg(c, reason)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
        prog.progress(0.5 + (idx+1)/len(candidates)*0.5)
        time.sleep(0.2)
    st.balloons()
    st.info(f"تم ✅ CALL {call_c} | PUT {put_c} | الاقوى اول")
