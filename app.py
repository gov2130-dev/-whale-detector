import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V58 FULL")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:14px;margin:10px 0;background:#fff;color:#000;box-shadow:0 2px 8px #0002;}
.call{border-color:#16a34a!important;}.put{border-color:#dc2626!important;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-size:14px;font-weight:900;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;font-size:15px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "view" not in st.session_state: st.session_state.view="🏆 الكل"
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V58 FULL - 8 شركات AUTO - 🔥 حقيقي vs 🔒 تحوط - حل TSLA 252</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY"): st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

if st.button("🧹 تصفير - فحص جديد"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

# عرض فوق مباشرة
if st.session_state.results:
    results=st.session_state.results
    v=st.session_state.view
    if "BUY" in v: final=[r for r in results if r["type"]=="CALL"]
    elif "SELL" in v: final=[r for r in results if r["type"]=="PUT"]
    else: final=results
    final=sorted(final, key=lambda x: (x["confirm"] + (15 if "حقيقي" in x["whale"] else 0)), reverse=True)
    st.success(f"✅ {len(final)} عقد - V58 - {ksa_str} - اسحب لفوق تشوف الجودة")
    for w in final:
        conf=w["confirm"]; whale=w["whale"]
        is_real="حقيقي" in whale
        border="#16a34a" if (w["type"]=="CALL" and is_real) else "#dc2626" if (w["type"]=="PUT" and is_real) else "#888"
        icon="🔥" if is_real else "🔒" if "تحوط" in whale else "⚠️"
        q="ممتاز ادخل" if is_real and conf>=65 else "جيد" if is_real else "لا تدخل تحوط" if "تحوط" in whale else "حذر"
        st.markdown(f"""<div class="card" style="border-color:{border};border-width:4px;">
        <b style="font-size:15px;">{icon} {w['ticker']} {w['strike']} {w['type']} - {conf}% | {whale} | {q}</b><br>
        <span style="font-size:13px;">يوم {w['ch1']:+.1f}% | RSI {w['rsi']:.0f} | VOL {w['vol']} OI {w['oi']} = {w['vol']/max(1,w['oi']):.1f}x</span><br>
        <span style="font-size:12px;">سهم ${w['stock_now']:.2f} | عقد ${w['opt_price']:.2f} | {w['exp_short']} {w['days']}ي | dist {w['dist']:+.1f}%</span>
        </div>""", unsafe_allow_html=True)
else:
    if st.session_state.auto_done:
        st.error("فحصنا 8 شركات - لا يوجد - السوق مغلق أو كلها تحوط")
    else:
        st.info("⏳ V58 يفحص 8 شركات AUTO - انتظر 25 ثانية...")

if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AAPL"]
    log=st.empty()
    prog=st.progress(0)
    new_results=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int((i/len(tickers))*100))
        log.text(f"🔴 يفحص {ticker} {i+1}/{len(tickers)}...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="5d")
            if h.empty:
                h=tk.history(period="1mo")
                if h.empty: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); ch1=float((curr-prev)/prev*100)
            trend="BULL" if ch1>=0 else "BEAR"
            rsi=50
            try:
                d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50
            opts=tk.options
            if not opts: continue
            exp=opts[0]; exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<0: continue
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[df['lastPrice']>=0.15].sort_values('volume', ascending=False).head(1)
            if df.empty: continue
            r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
            whale="حقيقي 🔥" if vol>oi*0.55 else "تحوط 🔒" if oi>1500 and vol<oi*0.35 else "مختلط ⚠️"
            strike=int(r['strike']); dist=(strike-curr)/curr*100
            if abs(dist)>7: continue
            conf=55
            if abs(ch1)>=1.5: conf+=15
            elif abs(ch1)>=0.5: conf+=8
            if "حقيقي" in whale: conf+=15
            elif "تحوط" in whale: conf-=12
            if days<=2: conf-=5
            if rsi>=75 or rsi<=25: conf-=8
            new_results.append({
                "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason":f"زخم يوم {ch1:+.1f}% RSI {rsi:.0f}",
                "confirm":int(max(30,min(88,conf)))
            })
            time.sleep(0.3)
        except: time.sleep(0.5); continue
    prog.progress(100)
    log.empty()
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(0.3)
    st.rerun()

st.caption(f"V58 FULL | {ksa_str} | 8 شركات AUTO بدون زر | 🔥 حقيقي VOL>OI*0.55 = دخول | 🔒 تحوط = TSLA 252 لا تدخل | V57 اشتغل 3 عقد 19:42:50")
