import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V62 HYBRID")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:12px;margin:8px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#fbbf24;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #f59e0b;font-size:13px;font-weight:900;}
div.stButton > button{width:100%;height:54px;font-weight:900;border-radius:12px;}
.rev{border-color:#16a34a!important;background:#f0fdf4!important;}
.late{border-color:#9ca3af!important;background:#f9fafb!important;opacity:0.8;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "debug" not in st.session_state: st.session_state.debug=[]
if "auto_done" not in st.session_state: st.session_state.auto_done=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str} - V62 HYBRID")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V62 HYBRID - يطلع عكسي بكره + الآن المتأخر مع تحذير + Debug ليه فاضي - يحل V61 03:14</div>', unsafe_allow_html=True)

if st.button("🧹 فحص هجين - 10 شركات - يطلع حتى لو مافي عكسي"):
    st.session_state.results=[]; st.session_state.debug=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.results:
    st.success(f"✅ {len(st.session_state.results)} عقد - {ksa_str}")
    for w in st.session_state.results:
        is_rev=w["is_reverse"]
        css="rev" if is_rev else "late"
        icon="🔄 بكره عكسي - مفيد" if is_rev else "⚠️ الآن متأخر - لا تدخل"
        border="#16a34a" if is_rev else "#9ca3af"
        st.markdown(f"""<div class="card {css}" style="border-color:{border};border-width:4px;">
        <b>{icon} | {w['ticker']} {w['strike']} {w['type_en']} - {w['confirm']}% | {w['whale']}</b><br>
        <span style="font-weight:700;">{w['reason_ar']}</span><br>
        <span style="font-size:11px;">اليوم {w['ch1']:+.1f}% RSI {w['rsi']:.0f} | VOL {w['vol']} OI {w['oi']} | ${w['stock_now']:.2f} | {w['exp_short']} {w['days']}ي</span>
        </div>""", unsafe_allow_html=True)
    with st.expander("🔍 Debug - ليه V61 كان فاضي"):
        for d in st.session_state.debug:
            st.text(d)
else:
    if st.session_state.auto_done:
        st.error("فحصنا 10 شركات - لا يوجد حتى متأخر - yfinance محجوب - اضغط فحص مرة ثانية")
        with st.expander("Debug"):
            for d in st.session_state.debug: st.text(d)
    else:
        st.info("⏳ V62 يفحص - بيطلع عكسي + متأخر + Debug...")

if not st.session_state.auto_done:
    tickers=["HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AAPL","AMD","SOFI"]
    log=st.empty(); prog=st.progress(0)
    new_results=[]; debug=[]
    for i, ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100))
        log.text(f"يفحص {ticker} {i+1}/{len(tickers)}...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="10d")
            if len(h)<5:
                debug.append(f"{ticker} - history فاضي")
                continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2])
            ch1=float((curr-prev)/prev*100)
            rsi=50
            try:
                d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
                rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            except: rsi=50

            debug.append(f"{ticker} - اليوم {ch1:+.1f}% RSI {rsi:.0f} - {'عكسي' if (rsi<=38 and ch1<=-0.8) or (rsi>=68 and ch1>=1) else 'متأخر'}")

            # منطق هجين
            trend=None; is_reverse=False; reason_ar=""
            if rsi<=40 and ch1<=-0.5: # خففت من 38 الى 40 ومن -0.8 الى -0.5 عشان يطلع
                trend="BULL"; is_reverse=True
                reason_ar=f"🔄 قاع RSI {rsi:.0f} نزل {ch1:.1f}% = CALL بكره 4 الفجر ارتداد مفيد"
            elif rsi>=65 and ch1>=0.8:
                trend="BEAR"; is_reverse=True
                reason_ar=f"🔄 قمة RSI {rsi:.0f} صعد {ch1:+.1f}% = PUT بكره هبوط مفيد"
            else:
                # متأخر - بس نطلعه مع تحذير
                trend="BEAR" if ch1<0 else "BULL"
                is_reverse=False
                reason_ar=f"⚠️ متأخر - نزل/صعد {ch1:+.1f}% RSI {rsi:.0f} - الحركة خلصت - لا تدخل - انتظر عكسي بكره"

            opts=tk.options
            if not opts:
                debug.append(f"{ticker} - لا options")
                continue
            exp=opts[1] if len(opts)>1 else opts[0]
            exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>8: continue
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.20) & (df['lastPrice']<=8)].sort_values('volume', ascending=False).head(1)
            if df.empty: continue
            r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
            if vol<100: continue
            whale="حقيقي 🔥" if vol>oi*0.45 else "تحوط 🔒" if oi>1200 and vol<oi*0.3 else "مختلط ⚠️"
            strike=int(r['strike']); dist=(strike-curr)/curr*100
            if abs(dist)>8: continue
            conf=68 if is_reverse else 55
            if "حقيقي" in whale: conf+=10
            if not is_reverse: conf-=10
            new_results.append({
                "ticker":ticker,"type_en":"CALL" if trend=="BULL" else "PUT",
                "stock_now":curr,"strike":strike,"dist":dist,
                "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                "whale":whale,"exp_short":exp_d.strftime("%m/%d"),"days":days,
                "rsi":rsi,"ch1":ch1,"reason_ar":reason_ar,"is_reverse":is_reverse,
                "confirm":int(max(45,min(88,conf)))
            })
            time.sleep(0.15)
        except Exception as e:
            debug.append(f"{ticker} خطأ {str(e)[:60]}")
            time.sleep(0.2); continue
    # ترتيب: عكسي أول
    new_results=sorted(new_results, key=lambda x: (x["is_reverse"], x["confirm"]), reverse=True)
    prog.progress(100); log.empty()
    st.session_state.results=new_results
    st.session_state.debug=debug
    st.session_state.auto_done=True
    time.sleep(0.3); st.rerun()

st.caption(f"V62 HYBRID | {ksa_str} | 🔄 عكسي أول + ⚠️ متأخر تحذير + Debug | يحل V61 فاضي 03:14 - لأن RSI ما وصل 38")
