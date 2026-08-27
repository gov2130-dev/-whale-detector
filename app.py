import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V60 EARLY FIX")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:14px;margin:10px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-size:13px;font-weight:900;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "view" not in st.session_state: st.session_state.view="ALL"
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str} - V60 EARLY FIX")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V60 FIXED - بدون خطأ KeyError - تنبؤ بكره عكسي - يحل V59 03:04</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("🔮 بكره"): st.session_state.view="TOMORROW"; st.rerun()
with c2:
    if st.button("⚡ الآن"): st.session_state.view="NOW"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="ALL"; st.rerun()

if st.button("🧹 فحص مبكر جديد"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.results:
    results=st.session_state.results
    v=st.session_state.view
    if v=="TOMORROW": final=[r for r in results if r["when_type"]=="TOMORROW"]
    elif v=="NOW": final=[r for r in results if r["when_type"]=="NOW"]
    else: final=results
    final=sorted(final, key=lambda x: x["confirm"], reverse=True)
    st.success(f"✅ {len(final)} تنبؤ - {ksa_str}")
    for w in final:
        conf=w["confirm"]; typ=w["type_en"]
        when_t=w["when_type"]
        is_rev=w["is_reverse"]
        border="#16a34a" if typ=="CALL" else "#dc2626"
        icon="🔮" if when_t=="TOMORROW" else "⚡"
        label="بكره عكسي" if is_rev else "بكره استمرار" if when_t=="TOMORROW" else "الآن"
        q="ادخل عكسي" if is_rev else "ادخل"
        st.markdown(f"""<div class="card" style="border-color:{border};border-width:4px;">
        <b style="font-size:15px;">{icon} {w['ticker']} {w['strike']} {w['type_en']} - {conf}% | {label} | {w['whale']} | {q}</b><br>
        <span style="font-size:13px;font-weight:700;">{w['reason_ar']}</span><br>
        <span style="font-size:11px;">اليوم {w['ch1']:+.1f}% RSI {w['rsi']:.0f} | VOL {w['vol']} OI {w['oi']} {w['vol']/max(1,w['oi']):.1f}x | ${w['stock_now']:.2f} | عقد ${w['opt_price']:.2f} | {w['exp_short']}</span>
        </div>""", unsafe_allow_html=True)
else:
    if not st.session_state.auto_done:
        st.info("⏳ V60 يفحص مبكر بدون خطأ - 15 ثانية...")

if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AAPL","AMD","SOFI"]
    log=st.empty(); prog=st.progress(0)
    new_results=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100))
        log.text(f"🔮 يفحص {ticker} {i+1}/{len(tickers)}...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="10d")
            if len(h)<5: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); prev2=float(h['Close'].iloc[-3])
            ch1=float((curr-prev)/prev*100); ch2=float((prev-prev2)/prev2*100)
            rsi=50
            try:
                d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50

            when_type="NOW"; is_reverse=False; reason_ar=""
            trend="BULL" if ch1>=0 else "BEAR"

            if ch1<=-2 and rsi<=38:
                trend="BULL"; when_type="TOMORROW"; is_reverse=True
                reason_ar=f"عكسي - نزل {ch1:.1f}% RSI {rsi:.0f} قاع - تجميع CALL بكره"
            elif ch1>=2.5 and rsi>=67:
                trend="BEAR"; when_type="TOMORROW"; is_reverse=True
                reason_ar=f"عكسي - صعد {ch1:+.1f}% RSI {rsi:.0f} قمة - تصريف PUT بكره"
            elif ch1<0 and ch2<0 and rsi<=45:
                trend="BEAR"; when_type="TOMORROW"; is_reverse=False
                reason_ar=f"استمرار هبوط {ch1:.1f}% امس {ch2:.1f}%"
            elif ch1>0 and ch2>0 and rsi>=52:
                trend="BULL"; when_type="TOMORROW"; is_reverse=False
                reason_ar=f"استمرار صعود {ch1:+.1f}% امس {ch2:+.1f}%"
            else:
                when_type="NOW"; is_reverse=False
                reason_ar=f"تفاعل الآن {ch1:+.1f}% RSI {rsi:.0f}"

            opts=tk.options
            if not opts: continue
            exp_idx=1 if len(opts)>1 else 0
            exp=opts[exp_idx]
            exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>8: continue
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.25) & (df['lastPrice']<=8)].sort_values('volume', ascending=False).head(1)
            if df.empty: continue
            r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
            if vol<150: continue
            whale="حقيقي 🔥" if vol>oi*0.5 else "تحوط 🔒" if oi>1200 and vol<oi*0.3 else "مختلط ⚠️"
            strike=int(r['strike']); dist=(strike-curr)/curr*100
            if abs(dist)>7: continue
            conf=50
            if is_reverse: conf+=22
            if when_type=="TOMORROW": conf+=10
            if "حقيقي" in whale: conf+=12
            if abs(ch1)>=2: conf+=8
            if "تحوط" in whale: conf-=15
            if conf<56: continue
            new_results.append({
                "ticker":ticker,"type_en":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason_ar":reason_ar,"when_type":when_type,
                "is_reverse":is_reverse,"confirm":int(max(52,min(86,conf)))
            })
            time.sleep(0.2)
        except Exception as e:
            log.text(f"{ticker} {str(e)[:50]}")
            time.sleep(0.3); continue
    prog.progress(100); log.empty()
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(0.3); st.rerun()

st.caption(f"V60 FIXED | {ksa_str} | حل KeyError line 47 - when_type ENGLISH بدل عربي | تنبؤ بكره عكسي")
