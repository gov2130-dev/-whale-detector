import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V59 EARLY")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:14px;margin:10px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-size:13px;font-weight:900;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;}
.predict{background:#e0f2fe;border-color:#0284c7!important;}
.reverse{background:#fef3c7;border-color:#d97706!important;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "view" not in st.session_state: st.session_state.view="🔮 بكره"
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str} - V59 EARLY")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V59 EARLY - تنبؤ بكره مو لحاق اليوم | يكشف تجميع الحيتان قبل الافتتاح | يحل V58 المتأخر</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("🔮 بكره"): st.session_state.view="🔮 بكره"; st.rerun()
with c2:
    if st.button("⚡ الآن"): st.session_state.view="⚡ الآن"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

if st.button("🧹 فحص مبكر جديد"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.results:
    results=st.session_state.results
    v=st.session_state.view
    if "بكره" in v: final=[r for r in results if "بكره" in r["when"]]
    elif "الآن" in v: final=[r for r in results if "الآن" in r["when"]]
    else: final=results
    final=sorted(final, key=lambda x: x["confirm"], reverse=True)
    st.success(f"✅ {len(final)} تنبؤ مبكر - {ksa_str}")
    for w in final:
        conf=w["confirm"]; typ=w["type"]
        is_rev="عكسي" in w["reason"]
        css="reverse" if is_rev else "predict"
        border="#0284c7" if not is_rev else "#d97706"
        icon="🔮" if "بكره" in w["when"] else "⚡"
        if typ=="CALL": border="#16a34a"
        else: border="#dc2626"
        st.markdown(f"""<div class="card {css}" style="border-color:{border};border-width:4px;">
        <b style="font-size:15px;">{icon} {w['ticker']} {w['strike']} {w['type']} - {conf}% | {w['when']} | {w['whale']}</b><br>
        <span style="font-size:13px;font-weight:700;">{w['reason']}</span><br>
        <span style="font-size:11px;">اليوم {w['ch1']:+.1f}% RSI {w['rsi']:.0f} | VOL {w['vol']} OI {w['oi']} {w['vol']/max(1,w['oi']):.1f}x | سهم ${w['stock_now']:.2f} | عقد ${w['opt_price']:.2f} | {w['exp_short']}</span>
        </div>""", unsafe_allow_html=True)
else:
    if not st.session_state.auto_done:
        st.info("⏳ V59 يفحص مبكر - يبحث عن تجميع اليوم لبكره... 20 ثانية")

if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AAPL","AMD","SOFI"]
    log=st.empty(); prog=st.progress(0)
    new_results=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100))
        log.text(f"🔮 مبكر يفحص {ticker} {i+1}/{len(tickers)}...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="10d")
            if len(h)<5: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); prev2=float(h['Close'].iloc[-3])
            ch1=float((curr-prev)/prev*100); ch2=float((prev-prev2)/prev2*100)
            # RSI
            rsi=50
            try:
                d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50
            # تنبؤ مبكر
            when="⚡ الآن"
            reason=""
            trend="BULL" if ch1>=0 else "BEAR"
            # 1- قاع + تجميع PUT = عكسي CALL بكره
            if ch1<=-2 and rsi<=35:
                trend="BULL"; when="🔮 بكره عكسي"; reason=f"عكسي 🔄 نزل {ch1:.1f}% RSI {rsi:.0f} قاع + حيتان بتجمع CALL لبكره"
            # 2- قمة + تصريف CALL = عكسي PUT بكره
            elif ch1>=2.5 and rsi>=68:
                trend="BEAR"; when="🔮 بكره عكسي"; reason=f"عكسي 🔄 صعد {ch1:+.1f}% RSI {rsi:.0f} قمة + تصريف = PUT بكره"
            # 3- استمرار - اليوم -1% أمس -2% = تجميع
            elif ch1<0 and ch2<0 and rsi<=45:
                trend="BEAR"; when="🔮 بكره استمرار"; reason=f"استمرار هبوط {ch1:.1f}% أمس {ch2:.1f}% ضعف"
            elif ch1>0 and ch2>0 and rsi>=50:
                trend="BULL"; when="🔮 بكره استمرار"; reason=f"استمرار صعود {ch1:+.1f}% أمس {ch2:+.1f}% قوة"
            else:
                when="⚡ الآن"; reason=f"تفاعل الآن {ch1:+.1f}% RSI {rsi:.0f}"

            opts=tk.options
            if not opts: continue
            exp=opts[1] if len(opts)>1 else opts[0] # ثاني انتهاء = بكره مو اليوم
            exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>7: continue
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.25) & (df['lastPrice']<=8)].sort_values('volume', ascending=False).head(1)
            if df.empty: continue
            r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
            if vol<200: continue # لازم حجم
            whale="حقيقي 🔥" if vol>oi*0.5 else "تحوط 🔒" if oi>1500 and vol<oi*0.3 else "مختلط ⚠️"
            strike=int(r['strike']); dist=(strike-curr)/curr*100
            if abs(dist)>6: continue
            conf=50
            if "بكره عكسي" in when: conf+=20 # العكسي أقوى
            if "بكره" in when: conf+=10
            if "حقيقي" in whale: conf+=12
            if abs(ch1)>=2: conf+=8
            if 30<=rsi<=68: conf+=5
            if "تحوط" in whale: conf-=15
            if conf<55: continue
            new_results.append({
                "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason":reason,"when":when,
                "confirm":int(max(50,min(85,conf)))
            })
            time.sleep(0.2)
        except: time.sleep(0.3); continue
    prog.progress(100); log.empty()
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(0.3); st.rerun()

st.caption(f"V59 EARLY | {ksa_str} | 🔮 بكره عكسي = قاع اليوم + RSI 35 = CALL بكره | يحل V58 المتأخر اللي يطلع بعد النزول")
