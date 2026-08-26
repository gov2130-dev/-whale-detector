import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V57 AUTO")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:12px;padding:12px;margin:8px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:10px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-size:13px;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "view" not in st.session_state: st.session_state.view="🏆 الكل"
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# V57 AUTO - {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V57 AUTO - يفحص لحاله بدون زر - 3 شركات فقط - أسرع - يحل V56</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY"): st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

if st.button("🧹 تصفير"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

# عرض النتائج
if st.session_state.results:
    results=st.session_state.results
    v=st.session_state.view
    if "BUY" in v: final=[r for r in results if r["type"]=="CALL"]
    elif "SELL" in v: final=[r for r in results if r["type"]=="PUT"]
    else: final=results
    final=sorted(final, key=lambda x: x["confirm"], reverse=True)
    st.success(f"✅ {len(final)} عقد AUTO - {ksa_str}")
    for w in final:
        conf=w["confirm"]; whale=w["whale"]
        border="#16a34a" if w["type"]=="CALL" else "#dc2626"
        if "تحوط" in whale: border="#888"
        icon="🔥" if "حقيقي" in whale else "🔒"
        st.markdown(f"""<div class="card" style="border-color:{border}">
        <b>{icon} {w['ticker']} {w['strike']} {w['type']} - {conf}% | {whale} | VOL {w['vol']} OI {w['oi']}</b><br>
        يوم {w['ch1']:+.1f}% RSI {w['rsi']:.0f} | {w['reason']}<br>
        <span style="font-size:11px;">${w['stock_now']:.2f} | عقد ${w['opt_price']:.2f} | {w['exp_short']} {w['days']}ي | dist {w['dist']:+.1f}%</span>
        </div>""", unsafe_allow_html=True)
else:
    st.info("⏳ V57 يفحص لحاله الآن - 3 شركات - انتظر 15 ثانية...")

# فحص تلقائي بدون زر
if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR"] # 3 فقط - أسرع
    log=st.empty()
    prog=st.progress(0)
    new_results=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int((i/len(tickers))*100))
        log.text(f"🔴 LIVE يفحص {ticker} {i+1}/3 - انتظر...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="5d")
            if h.empty:
                log.text(f"{ticker} فشل history - يحاول مرة ثانية")
                time.sleep(2)
                h=tk.history(period="1mo")
                if h.empty:
                    continue
            curr=float(h['Close'].iloc[-1])
            prev=float(h['Close'].iloc[-2])
            ch1=float((curr-prev)/prev*100)
            trend="BULL" if ch1>=0 else "BEAR"
            rsi=50
            try:
                d=h['Close'].diff()
                g=d.where(d>0,0).ewm(alpha=1/14).mean()
                l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50
            opts=tk.options
            if not opts:
                log.text(f"{ticker} لا options")
                continue
            exp=opts[0]
            exp_d=datetime.strptime(exp,"%Y-%m-%d")
            days=(exp_d-datetime.now()).days
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[df['lastPrice']>0.1].sort_values('volume', ascending=False).head(1)
            if df.empty:
                log.text(f"{ticker} لا عقود >0.1")
                continue
            r=df.iloc[0]
            vol=int(r.get('volume',0) or 0)
            oi=int(r.get('openInterest',0) or 0)
            whale="حقيقي 🔥" if vol>oi*0.5 else "تحوط 🔒" if oi>1000 and vol<oi*0.3 else "مختلط ⚠️"
            strike=int(r['strike'])
            dist=(strike-curr)/curr*100
            conf=60
            if abs(ch1)>=1: conf+=15
            if "حقيقي" in whale: conf+=10
            if "تحوط" in whale: conf-=10
            new_results.append({
                "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason":f"VWAP يوم {ch1:+.1f}% {whale}",
                "confirm":int(min(88,max(35,conf)))
            })
            log.text(f"{ticker} ✅ {trend} {strike} {whale} {ch1:+.1f}%")
            time.sleep(0.5)
        except Exception as e:
            log.text(f"{ticker} خطأ {str(e)[:60]}")
            time.sleep(1)
            continue
    prog.progress(100)
    log.text(f"✅ انتهى - {len(new_results)} عقد")
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(1)
    st.rerun()

st.caption(f"V57 AUTO | {ksa_str} | يفحص لحاله 3 شركات HOOD COIN MSTR بدون زر | حقيقي 🔥 VOL>OI*0.5 vs تحوط 🔒 | حل نهائي V56 7:38")
