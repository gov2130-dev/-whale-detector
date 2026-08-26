import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V51 ULTRA", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:11px;}
.big-table th {background:#000!important; color:#fff!important; padding:8px 2px; text-align:center; font-size:7px;}
.big-table td {background:#fff!important; padding:8px 2px; text-align:center; border:1px solid #ccc; font-size:10px; font-weight:700;}
.call-badge {background:#16a34a!important; color:#fff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.put-badge {background:#dc2626!important; color:#fff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
div.stButton > button {width:100%; height:48px; font-size:15px; font-weight:900; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "view" not in st.session_state: st.session_state.view="🏆 الكل"
if "debug" not in st.session_state: st.session_state.debug=[]

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"## {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V51 فلتر ضعيف VOL 10 | يطلع نتائج حتى لو السوق ضعيف</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY", type="primary" if st.session_state.view=="✅ BUY قوي" else "secondary"):
        st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL", type="primary" if st.session_state.view=="🔻 SELL قوي" else "secondary"):
        st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل", type="primary" if st.session_state.view=="🏆 الكل" else "secondary"):
        st.session_state.view="🏆 الكل"; st.rerun()

b1,b2=st.columns(2)
with b1: do_scan=st.button("⚡ فحص ضعيف يطلع كل شي", type="primary")
with b2:
    if st.button("🧹 تصفير + مسح كاش"):
        st.session_state.results=pd.DataFrame(); st.session_state.debug=[]; st.cache_data.clear(); st.rerun()

@st.cache_data(ttl=20)
def quick_analysis_v51(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="1mo")
        if len(h)<15: return None, f"{ticker} history {len(h)} قليل"
        curr=float(h['Close'].iloc[-1])
        if pd.isna(curr) or curr<3 or curr>5000: return None, f"{ticker} سعر {curr} غلط"
        prev=float(h['Close'].iloc[-2])
        ch1=float((curr-prev)/prev*100) if prev>0 else 0.0
        if pd.isna(ch1): ch1=0.0
        ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
        # RSI
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll<0.01: ll=0.01
        rsi=100-(100/(1+lg/ll))
        if pd.isna(rsi): rsi=50
        vol_avg=float(h['Volume'].tail(10).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=float(vol_today/vol_avg) if vol_avg>0 else 1.0
        trend="NEUTRAL"
        if ch1>=0.5 and curr>ema9: trend="BULL"
        elif ch1<=-0.5 and curr<ema9: trend="BEAR"
        elif ch1>=1: trend="BULL"
        elif ch1<=-1: trend="BEAR"
        return {"price":curr,"ch1":ch1,"ema9":ema9,"rsi":float(rsi),"vol_ratio":float(vol_ratio),"trend":trend}, f"{ticker} OK {curr:.2f} {ch1:+.1f}% {trend}"
    except Exception as e:
        return None, f"{ticker} error {str(e)[:50]}"

def fetch_v51(ticker):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return [], f"{ticker} لا يوجد options"
        sd, msg = quick_analysis_v51(ticker)
        if not sd: return [], msg
        if sd["trend"]=="NEUTRAL": return [], f"{ticker} متذبذب {sd['ch1']:+.1f}%"
        curr=sd["price"]
        trend=sd["trend"]
        rows=[]
        for exp in tk.options[:1]: # أول انتهاء فقط - أسرع
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<0: continue
                chain=tk.option_chain(exp)
                allowed=["CALL"] if trend=="BULL" else ["PUT"]
                for opt_type in allowed:
                    df_opt=chain.calls if opt_type=="CALL" else chain.puts
                    if df_opt.empty: continue
                    df_opt=df_opt.copy().dropna(subset=['lastPrice'])
                    # فلتر ضعيف جدا
                    df_opt=df_opt[df_opt['lastPrice']>0.05]
                    if df_opt.empty: continue
                    # فلتر volume ضعيف
                    if 'volume' in df_opt.columns:
                        df_opt=df_opt[(df_opt['volume']>=10) | (df_opt['volume'].isna())]
                    df_opt=df_opt.sort_values('volume' if 'volume' in df_opt.columns else 'lastPrice', ascending=False).head(1)
                    for _,r in df_opt.iterrows():
                        try:
                            strike=float(r['strike'])
                            dist=(strike-curr)/curr*100 if curr!=0 else 0
                            if abs(dist)>8: continue # مسافة أوسع
                            last_price=float(r['lastPrice'])
                            vol=int(r.get('volume',100) or 100)
                            prem=float(last_price*vol*100/1e6) if vol>0 else float(last_price*100/1e6)
                            rows.append({"ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),"opt_price":float(last_price),"vol":int(vol),"prem_M":float(prem),"exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),"days":int(days),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),"change_1d":float(sd["ch1"]),"trend":trend})
                        except: continue
                if len(rows)>=1: break
            except Exception as e:
                return [], f"{ticker} chain error {str(e)[:30]}"
        if rows: return rows, f"{ticker} ✅ {len(rows)} عقد"
        else: return [], f"{ticker} لا يوجد عقد بعد الفلتر"
    except Exception as e:
        return [], f"{ticker} fetch error {str(e)[:50]}"

# عرض سابق
if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    df=df.drop_duplicates(subset=["ticker"], keep="first")
    enriched=[]
    for _,r in df.iterrows():
        ch1=float(r.get("change_1d",0))
        vol_r=float(r.get("vol_ratio",1))
        score=50
        if r["type"]=="CALL":
            if ch1>=1: score+=20
            elif ch1>=0: score+=8
            else: score-=20
        else:
            if ch1<=-1: score+=20
            elif ch1<=0: score+=8
            else: score-=20
        score=int(max(35,min(85,score)))
        r2=dict(r); r2["confirm"]=score; r2["why"]=f"اليوم {ch1:+.1f}% | {r.get('trend')} | VOL x{vol_r:.1f}"
        enriched.append(r2)
    df2=pd.DataFrame(enriched)
    df2=df2.sort_values("confirm", ascending=False)
    v=st.session_state.view
    if "BUY قوي" in v: final=df2[df2["type"]=="CALL"]
    elif "SELL قوي" in v: final=df2[df2["type"]=="PUT"]
    else: final=df2
else:
    final=pd.DataFrame()

if not final.empty:
    st.success(f"✅ {len(final)} شركة - {ksa_str}")
    for _,w in final.head(3).iterrows():
        conf=int(w.get("confirm",60))
        border="#16a34a" if w.get("type")=="CALL" else "#dc2626"
        icon="🟢" if w.get("type")=="CALL" else "🔴"
        st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;"><b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.2f}M | {w.get('exp_short')}</span></div>""", unsafe_allow_html=True)
    html='<table class="big-table"><tr><th>%</th><th>نوع</th><th>شركة</th><th>سهم</th><th>سترايك</th><th>📅</th><th>عقد</th><th>حوت</th></tr>'
    for _,w in final.iterrows():
        sp=float(w.get("stock_now",0)); conf=int(w.get("confirm",60)); ch1=float(w.get("change_1d",0))
        prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
        badge=f'<span class="call-badge">CALL</span>' if w.get("type")=="CALL" else f'<span class="put-badge">PUT</span>'
        html+=f'<tr><td><b>{conf}%</b></td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch1>=0 else "#dc2626"}">{ch1:+.1f}%</span></td><td><b>{int(w.get("strike",0))}</b><br>{float(w.get("dist",0)):+.1f}%</td><td>{w.get("exp_short","")}</td><td>${opt_p:.2f}</td><td>${prem:.2f}M</td></tr>'
    html+='</table>'
    st.markdown(html, unsafe_allow_html=True)
    if st.session_state.debug:
        with st.expander("🔍 Debug"):
            for d in st.session_state.debug: st.text(d)
else:
    # فحص تلقائي
    st.info("⏳ يفحص تلقائيا - فلتر ضعيف جدا - بيطلع نتائج الآن")
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR"]
    with st.spinner("يفحص 8 شركات بفلتر ضعيف..."):
        rows=[]
        debug=[]
        with ThreadPoolExecutor(max_workers=8) as executor:
            futs={executor.submit(fetch_v51, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res, msg = fu.result()
                    debug.append(msg)
                    if res: rows.extend(res)
                except Exception as e:
                    debug.append(f"error {e}")
    st.session_state.debug=debug
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.warning("لا يوجد - حتى بالفلتر الضعيف")
        with st.expander("🔍 ليش لا يوجد - اضغط هنا"):
            for d in debug:
                st.text(d)
        st.markdown("**الحل:**")
        st.markdown("1. السوق مغلق؟ الآن 18:25 KSA = 11:25 ET السوق مفتوح")
        st.markdown("2. اضغط Manage app > Reboot app")
        st.markdown("3. اضغط 🧹 تصفير + مسح كاش")
        st.markdown("4. انتظر 10 ثواني")
        final=pd.DataFrame()

if do_scan:
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR","AMD","AMZN","AVGO","SOFI"]
    with st.spinner(f"⚡ فحص {len(tickers)} بفلتر ضعيف..."):
        rows=[]
        debug=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v51, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res, msg = fu.result()
                    debug.append(msg)
                    if res: rows.extend(res)
                except: pass
    st.session_state.debug=debug
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.error("حتى بالفلتر الضعيف لا يوجد")
        for d in debug: st.text(d)

st.caption(f"V51 ULTRA LOW | {ksa_str} | VOL 10 PREM 0.02M | debug")
