import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V50 FAST", initial_sidebar_state="collapsed")

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

def calc_delta(S,K,T,iv,is_call=True):
    try:
        if T<=0: T=0.05
        if iv is None or pd.isna(iv) or iv<0.12 or iv>4: iv=0.5
        if S<=0 or K<=0: return 0.5 if is_call else -0.5
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        erf_val=math.erf(d1/math.sqrt(2.0))
        if is_call: delta=0.5*(1.0+erf_val)
        else: delta=0.5*(1.0+erf_val)-1
        return float(delta)
    except: return 0.5 if is_call else -0.5

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"## {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V50 سريع | 8 شركات فقط | COIN اتجاه واحد</div>', unsafe_allow_html=True)

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
with b1: do_scan=st.button("⚡ فحص سريع 8 شركات", type="primary")
with b2:
    if st.button("🧹 تصفير"):
        st.session_state.results=pd.DataFrame(); st.cache_data.clear(); st.rerun()

@st.cache_data(ttl=30)
def quick_analysis(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="1mo")
        if len(h)<20: return None
        curr=float(h['Close'].iloc[-1])
        if pd.isna(curr) or curr<5 or curr>3000: return None
        if ticker=="NFLX" and curr<200: return None
        if ticker=="AVGO" and curr<150: return None
        # تغيير يوم
        prev=float(h['Close'].iloc[-2])
        ch1=float((curr-prev)/prev*100) if prev>0 else 0.0
        if pd.isna(ch1): ch1=0.0
        # EMA سريع
        ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
        # RSI سريع
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll<0.01: ll=0.01
        rsi=100-(100/(1+lg/ll))
        if pd.isna(rsi): rsi=50
        # VOL
        vol_avg=float(h['Volume'].tail(10).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=float(vol_today/vol_avg) if vol_avg>0 else 1.0
        # اتجاه واحد واضح
        trend="NEUTRAL"
        if ch1>=0.7 and curr>ema9: trend="BULL"
        elif ch1<=-0.7 and curr<ema9: trend="BEAR"
        elif ch1>=1.2: trend="BULL"
        elif ch1<=-1.2: trend="BEAR"
        return {"price":curr,"ch1":ch1,"ema9":ema9,"ema21":ema21,"rsi":float(rsi),"vol_ratio":float(vol_ratio),"trend":trend}
    except: return None

def fetch_quick(ticker):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=quick_analysis(ticker)
        if not sd: return []
        if sd["trend"]=="NEUTRAL": return []
        if sd["vol_ratio"]<0.5: return []
        curr=sd["price"]
        trend=sd["trend"]
        rows=[]
        exp=tk.options[0]
        try:
            exp_d=datetime.strptime(exp,"%Y-%m-%d")
            days=(exp_d-datetime.now()).days
            if days<0: return []
            T=max(days/365,0.04)
            chain=tk.option_chain(exp)
            allowed=["CALL"] if trend=="BULL" else ["PUT"]
            for opt_type in allowed:
                df_opt=chain.calls if opt_type=="CALL" else chain.puts
                if df_opt.empty: continue
                df_opt=df_opt.copy().dropna(subset=['volume','lastPrice'])
                df_opt=df_opt[df_opt['volume']>0]
                df_opt['prem']=df_opt['lastPrice']*df_opt['volume']*100
                df_opt=df_opt[df_opt['prem']>=0.1*1e6]
                df_opt=df_opt[df_opt['volume']>=50]
                if df_opt.empty: continue
                df_opt=df_opt.sort_values('prem',ascending=False).head(1)
                for _,r in df_opt.iterrows():
                    try:
                        strike=float(r['strike'])
                        dist=(strike-curr)/curr*100 if curr!=0 else 0
                        if abs(dist)>5: continue
                        last_price=float(r['lastPrice'])
                        vol=int(r['volume'])
                        prem=float(last_price*vol*100/1e6)
                        rows.append({"ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),"opt_price":float(last_price),"vol":int(vol),"prem_M":float(prem),"exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),"days":int(days),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),"change_1d":float(sd["ch1"]),"trend":trend})
                    except: continue
        except: pass
        return rows
    except: return []

def calc_score(row):
    ch1=float(row.get("change_1d",0))
    vol_r=float(row.get("vol_ratio",1))
    score=50
    if row["type"]=="CALL":
        if ch1>=1.5: score+=20
        elif ch1>=0.5: score+=10
        elif ch1<0: score-=25
        if vol_r>=1.5: score+=15
        elif vol_r<0.7: score-=10
    else:
        if ch1<=-1.5: score+=20
        elif ch1<=-0.5: score+=12
        elif ch1>0.5: score-=25
        if vol_r>=1.2: score+=10
    score=int(max(35,min(88,score)))
    return score, f"اليوم {ch1:+.1f}% | {row.get('trend')} | VOL x{vol_r:.1f} | RSI {float(row.get('rsi',50)):.0f}"

# عرض
if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    df=df.drop_duplicates(subset=["ticker"], keep="first")
    # حساب نسبة
    enriched=[]
    for _,r in df.iterrows():
        s, why=calc_score(r)
        r2=dict(r); r2["confirm"]=s; r2["why"]=why
        enriched.append(r2)
    df2=pd.DataFrame(enriched)
    df2=df2.sort_values("confirm", ascending=False)
    v=st.session_state.view
    if "BUY قوي" in v: final=df2[df2["type"]=="CALL"]
    elif "SELL قوي" in v: final=df2[df2["type"]=="PUT"]
    else: final=df2
else:
    final=pd.DataFrame()
    # فحص تلقائي سريع
    st.info("⏳ يفحص تلقائيا - 8 شركات فقط - 8 ثواني...")
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR"]
    with st.spinner("فحص..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=8) as executor:
            futs={executor.submit(fetch_quick, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.warning("لا يوجد - اضغط فحص سريع")

if not final.empty:
    st.success(f"✅ {len(final)} شركة - {ksa_str} - كل شركة اتجاه واحد")
    for _,w in final.head(4).iterrows():
        conf=int(w.get("confirm",60))
        border="#16a34a" if w.get("type")=="CALL" else "#dc2626"
        icon="🟢" if w.get("type")=="CALL" else "🔴"
        st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;"><b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.1f}M | {w.get('exp_short')} {int(w.get('days'))}ي</span></div>""", unsafe_allow_html=True)
    html='<table class="big-table"><tr><th>%</th><th>نوع</th><th>شركة</th><th>سهم اليوم</th><th>سترايك</th><th>📅</th><th>عقد</th><th>حوت</th></tr>'
    for _,w in final.iterrows():
        sp=float(w.get("stock_now",0)); conf=int(w.get("confirm",60)); ch1=float(w.get("change_1d",0))
        prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
        badge=f'<span class="call-badge">CALL</span>' if w.get("type")=="CALL" else f'<span class="put-badge">PUT</span>'
        html+=f'<tr><td><b>{conf}%</b></td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch1>=0 else "#dc2626"}">{ch1:+.1f}%</span></td><td><b>{int(w.get("strike",0))}</b><br>{float(w.get("dist",0)):+.1f}%</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}</td><td>${prem:.1f}M<br>x{float(w.get("vol_ratio",1)):.1f}</td></tr>'
    html+='</table>'
    st.markdown(html, unsafe_allow_html=True)

if do_scan:
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR","AMD","AMZN"]
    with st.spinner(f"⚡ فحص {len(tickers)}..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_quick, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.error("لا يوجد - السوق مغلق؟")

st.caption(f"V50 FAST | {ksa_str} | 8 شركات فقط - COIN اتجاه واحد | يفحص لحاله")
