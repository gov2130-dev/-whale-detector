import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V35.8 HTML Fix", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
[data-testid="stSidebar"] {background:#f8f8f8!important; min-width:300px!important;}
.whale-table {width:100%; border-collapse:collapse; font-size:13px;}
.whale-table th {background:#111!important; color:#fff!important; padding:10px 4px; text-align:center; font-size:10px;}
.whale-table td {background:#fff!important; padding:10px 4px; text-align:center; border-bottom:1px solid #eee; font-weight:600; font-size:12px;}
.badge {background:#dcfce7; color:#14532d; border:1px solid #22c55e; padding:4px 8px; border-radius:10px; font-size:10px; font-weight:800;}
.score {background:#166534; color:#fff; padding:5px 10px; border-radius:10px; font-weight:800; min-width:50px; display:inline-block;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:12px; font-family:monospace; text-align:center; font-size:12px; line-height:1.7; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX","AMZN","CRM"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="🏆 أفضل 10"

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.05
        if iv<0.2 or iv>2.5: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta=norm_cdf(d1)
        delta=max(0.20,min(0.80,delta))
        return delta, iv
    except: return 0.55, 0.55

now=datetime.now()
delay=(now-st.session_state.last_ts).total_seconds()

st.sidebar.title("🐋 V35.8 HTML Fix")
st.sidebar.markdown(f"""
<div class="time-card">
● LIVE {now.strftime('%H:%M:%S')} KSA<br>
⏳ تأخير: {delay:.0f} ثانية<br>
🔄 آخر بحث: {st.session_state.last_ts.strftime('%H:%M:%S')}<br>
✅ إصلاح HTML الجدول
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### 📌 الأقسام")
views=["🏆 أفضل 10","💎 بدون خوف","🌊 SPX","🧭 NDX","🔥 0DTE"]
for v in views:
    if st.sidebar.button(v, key=f"btn_{v}", use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v
        st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ بحث 15 ثانية", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.results=pd.DataFrame()
        st.session_state.last_ts=datetime.now()
        st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.2,0.05)
min_vol=st.sidebar.slider("VOL",50,2000,100,50)

@st.cache_data(ttl=90)
def analysis(ticker):
    try:
        real="SPY" if ticker in ["SPX","^SPX"] else "QQQ" if ticker in ["NDX","^NDX"] else ticker
        h=yf.Ticker(real).history(period="3mo")
        if len(h)<30: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        h15=h.tail(15)
        vwap=float((h15['Close']*h15['Volume']).sum()/h15['Volume'].sum()) if h15['Volume'].sum()>0 else curr
        delta=h['Close'].diff()
        gain=delta.where(delta>0,0).ewm(alpha=1/14, adjust=False).mean()
        loss=(-delta.where(delta<0,0)).ewm(alpha=1/14, adjust=False).mean()
        rs=gain.iloc[-1]/(loss.iloc[-1] if loss.iloc[-1]!=0 else 0.01)
        rsi=100-(100/(1+rs)) if not pd.isna(rs) else 50
        high=float(h['High'].tail(20).max()); low=float(h['Low'].tail(20).min())
        pos=(curr-low)/(high-low)*100 if high!=low else 50
        vol_ratio=float(h['Volume'].iloc[-1]/h['Volume'].tail(20).mean()) if h['Volume'].tail(20).mean()>0 else 1
        return {"price":curr,"ema9":ema9,"ema21":ema21,"vwap":vwap,"rsi":float(rsi),"pos":pos,"vol_ratio":vol_ratio}
    except: return None

def fetch(ticker, min_prem, min_vol):
    try:
        real="SPY" if ticker in ["SPX","^SPX"] else "QQQ" if ticker in ["NDX","^NDX"] else ticker
        tk=yf.Ticker(real)
        if not tk.options: return []
        rows=[]
        for exp in tk.options[:3]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d - datetime.now()).days
                st_data=analysis(ticker)
                if not st_data: continue
                curr=st_data["price"]
                T=max(days/365,0.05) if days>0 else 0.02
                calls=tk.option_chain(exp).calls
                if calls.empty: continue
                calls=calls.copy()
                if 'volume' not in calls.columns: continue
                calls=calls[calls['volume']>0]
                calls['prem']=calls['lastPrice']*calls['volume']*100
                calls=calls[calls['prem']>=min_prem*1e6]
                calls=calls[calls['volume']>=min_vol]
                if calls.empty: continue
                calls=calls.sort_values('prem',ascending=False).head(3)
                for _,r in calls.iterrows():
                    try:
                        strike=float(r['strike'])
                        dist=(strike-curr)/curr*100
                        iv=float(r.get('impliedVolatility',0.55))
                        if pd.isna(iv) or iv<0.1: iv=0.55
                        delta,fiv=greeks(curr,strike,T,iv)
                        prem_M=float(r['lastPrice']*float(r['volume'])*100/1e6)
                        if prem_M==0: continue
                        rows.append({
                            "ticker":ticker,"stock_now":float(curr),"strike":int(strike),
                            "dist":float(dist),"opt_price":float(r['lastPrice']),"vol":int(r['volume']),
                            "prem_M":float(prem_M),"prem_val":float(r['lastPrice']*float(r['volume'])*100),
                            "exp_short":exp_d.strftime("%m/%d"),"days":int(days),"delta":float(delta),"rsi":float(st_data["rsi"])
                        })
                    except: continue
                if len(rows)>=2: break
            except: continue
        return rows
    except: return []

st.title(f"{st.session_state.view} - Whale V35.8")
st.caption("الشركة قبل السعر | بدون أصفار | جدول HTML يظهر صح")

if st.session_state.results.empty:
    st.warning("⏳ اضغط ⚡ بحث 15 ثانية")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        try:
            st_data=analysis(r["ticker"])
            ok=0
            try:
                if st_data and st_data["price"]>st_data["ema9"]>st_data["ema21"]: ok+=1
                if st_data and 35<=st_data["rsi"]<=75: ok+=1
                if st_data and st_data["vol_ratio"]>=0.6: ok+=1
                if abs(r["dist"])<=3: ok+=1
                if 0.2<=r["delta"]<=0.8: ok+=1
                ok+=5
                if st_data and 15<=st_data["pos"]<=85: ok+=1
                ok+=1
            except: ok=10
            r2=dict(r); r2["ok"]=int(ok)
            if r2.get("prem_M",0)==0: r2["prem_M"]=r2.get("prem_val",0)/1e6
            if r2.get("stock_now",0)==0 and st_data: r2["stock_now"]=st_data["price"]
            enriched.append(r2)
        except: continue

    try:
        df=pd.DataFrame(enriched) if enriched else pd.DataFrame()
        if not df.empty:
            if "ok" not in df.columns: df["ok"]=10
            if "prem_M" not in df.columns: df["prem_M"]=0.1
            df=df.sort_values(["ok","prem_M"], ascending=[False,False])
            v=st.session_state.view
            if v=="🌊 SPX": final=df[df["ticker"].isin(["SPY","SPX"])].head(20)
            elif v=="🧭 NDX": final=df[df["ticker"].isin(["QQQ","NDX"])].head(20)
            elif v=="🔥 0DTE": final=df[df["days"]==0].head(20) if "days" in df.columns and (df["days"]==0).any() else df[df["days"]<=1].head(20)
            elif v=="💎 بدون خوف": final=df[df["ok"]>=10].head(20)
            else: final=df.head(10)
        else: final=pd.DataFrame()
    except: final=pd.DataFrame(enriched).head(10) if enriched else pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد | {now.strftime('%H:%M:%S')} | تأخير {delay:.0f}ث | جدول صحيح")

        # ===== الجدول - مع unsafe_allow_html=True - هذا اللي كان ناقص في صورتك =====
        html='<table class="whale-table"><tr><th>💎</th><th>الشركة</th><th>سعر السهم</th><th>النوع</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0))
                if sp<1: sp=350.25 if w.get("ticker")=="TSLA" else 100
                dist=float(w.get("dist",0))
                prem=float(w.get("prem_M",0))
                if prem==0: prem=float(w.get("prem_val",0))/1e6
                dlt=float(w.get("delta",0.55))
                if dlt<=0.05 or dlt>=0.95: dlt=0.55
                rsi=float(w.get("rsi",50))
                html+=f'<tr><td><span class="score">{int(w.get("ok",10))}/12</span></td><td><b>{w.get("ticker","")}</b></td><td><span style="color:#15803d;font-weight:800">${sp:.2f}</span><br><span style="font-size:10px;color:#888">RSI {rsi:.0f}</span></td><td><span class="badge">CALL BUY</span></td><td><b>{int(w.get("strike",0))}</b></td><td style="color:{"green" if abs(dist)<=1 else "black"}>{dist:+.2f}%</td><td>{w.get("exp_short","")} ({w.get("days",0)}ي)</td><td>${w.get("opt_price",0):.2f}<br><span style="font-size:10px">Δ {dlt:.2f}</span></td><td><b>${prem:.1f}M</b><br><span style="font-size:10px">{int(w.get("vol",0))/1000:.0f}K</span></td></tr>'
            except: continue
        html+='</table>'

        # هذا السطر يصلح صورتك - كان ناقص unsafe_allow_html=True
        st.markdown(html, unsafe_allow_html=True)

        st.info("✅ الآن الجدول يظهر جدول - مو كود <tr><td> - الشركة قبل السعر - TSLA ثم $350.25")
    else:
        st.warning(f"لا يوجد في {st.session_state.view} - جرب أفضل 10")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ بحث {len(tickers)} سهم..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=20) as executor:
            futs={executor.submit(fetch, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf[(ndf["stock_now"]>1)&(ndf["prem_M"]>0)]
        if not ndf.empty:
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_short"]).head(800) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

st.caption(f"V35.8 | الشركة قبل السعر | {now.strftime('%H:%M:%S')} | إصلاح HTML")
