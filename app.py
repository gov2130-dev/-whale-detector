import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V61 PURE REVERSAL")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:14px;margin:10px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#fbbf24;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #f59e0b;font-size:13px;font-weight:900;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;}
.rev{background:#fef3c7!important;border-color:#d97706!important;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str} - V61 PURE")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V61 PURE REVERSAL - فقط عكسي لبكره - يخفي كل عقود الآن المتأخرة - يحل NVDA RSI 21 PUT خطأ</div>', unsafe_allow_html=True)

if st.button("🧹 فحص عكسي بكره فقط - 10 شركات"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.results:
    final=sorted(st.session_state.results, key=lambda x: x["confirm"], reverse=True)
    st.success(f"✅ {len(final)} عقد - بكره عكسي فقط - {ksa_str} - بدون الآن")
    for w in final:
        conf=w["confirm"]
        st.markdown(f"""<div class="card rev" style="border-color:#d97706;border-width:4px;">
        <b style="font-size:16px;">🔄 {w['ticker']} {w['strike']} {w['type_en']} - {conf}% | بكره عكسي | {w['whale']} | ارتداد</b><br>
        <span style="font-size:14px;font-weight:800;color:#92400e;">{w['reason_ar']}</span><br>
        <span style="font-size:11px;">اليوم {w['ch1']:+.1f}% RSI {w['rsi']:.0f} | قاع {w['rsi']:.0f} = تشبع بيع = CALL بكره | VOL {w['vol']} OI {w['oi']} {w['vol']/max(1,w['oi']):.1f}x | ${w['stock_now']:.2f} | {w['exp_short']}</span>
        </div>""", unsafe_allow_html=True)
    if len(final)==0:
        st.warning("لا يوجد عكسي اليوم - السوق متوازن - انتظر بكره")
else:
    if not st.session_state.auto_done:
        st.info("⏳ V61 يبحث فقط عن قيعان RSI < 35 وقمم RSI > 70 - عكسي لبكره...")

if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AAPL","AMD","SOFI"]
    log=st.empty(); prog=st.progress(0)
    new_results=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100))
        log.text(f"🔄 يفحص عكسي {ticker} {i+1}/{len(tickers)}...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="10d")
            if len(h)<5: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2])
            ch1=float((curr-prev)/prev*100)
            # RSI
            rsi=50
            try:
                d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50

            # فقط عكسي
            trend=None; reason_ar=""
            # شرط 1: RSI <=38 و نزول -1% ولو -0.8% بس RSI 21 قاع = CALL بكره - هذا حل NVDA صورتك
            if rsi<=38 and ch1<=-0.8:
                trend="BULL"
                reason_ar=f"قاع حقيقي RSI {rsi:.0f} + نزل {ch1:.1f}% = تشبع بيع = CALL عكسي بكره ارتداد 4 الفجر"
            # شرط 2: RSI >=68 و صعود
            elif rsi>=68 and ch1>=1.0:
                trend="BEAR"
                reason_ar=f"قمة حقيقية RSI {rsi:.0f} + صعد {ch1:+.1f}% = تشبع شراء = PUT عكسي بكره هبوط"
            else:
                continue # تجاهل كل الآن - هذا حل مشكلتك

            opts=tk.options
            if not opts: continue
            exp=opts[1] if len(opts)>1 else opts[0]
            exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>7: continue
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.30) & (df['lastPrice']<=6)].sort_values('volume', ascending=False).head(1)
            if df.empty: continue
            r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
            if vol<150: continue
            whale="حقيقي 🔥" if vol>oi*0.45 else "تحوط 🔒" if oi>1200 and vol<oi*0.3 else "مختلط ⚠️"
            if "تحوط" in whale: continue # فقط حقيقي
            strike=int(r['strike']); dist=(strike-curr)/curr*100
            if abs(dist)>6: continue
            conf=70
            if rsi<=25 or rsi>=75: conf+=12 # قاع سحيق = ثقة عالية
            if abs(ch1)>=2.5: conf+=8
            if "حقيقي" in whale: conf+=10
            new_results.append({
                "ticker":ticker,"type_en":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason_ar":reason_ar,
                "confirm":int(max(62,min(90,conf)))
            })
            time.sleep(0.2)
        except: time.sleep(0.3); continue
    prog.progress(100); log.empty()
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(0.3); st.rerun()

st.caption(f"V61 PURE | {ksa_str} | فقط عكسي RSI<38 + نزول = CALL بكره | RSI>68 + صعود = PUT بكره | يخفي كل الآن - حل NVDA RSI21 PUT خطأ")
