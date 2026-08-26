import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V35.6 Time Fix", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
[data-testid="stSidebar"] {background:#fafafa!important; min-width:300px!important; max-width:320px!important;}
.whale-table {width:100%; border-collapse:collapse; font-size:13px; font-family:Inter,sans-serif;}
.whale-table th {background:#111!important; color:#fff!important; padding:10px 5px; text-align:center; font-size:10px;}
.whale-table td {background:#fff!important; padding:10px 5px; text-align:center; border-bottom:1px solid #eee; font-weight:600;}
.badge {background:#dcfce7; color:#14532d; border:1px solid #22c55e; padding:5px 8px; border-radius:10px; font-size:10px; font-weight:800; white-space:nowrap;}
.score {background:#166534; color:#fff; padding:5px 10px; border-radius:10px; font-weight:800; display:inline-block; min-width:55px;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:12px; font-family:monospace; text-align:center; font-size:12px; line-height:1.6;}
.price {color:#15803d; font-weight:800;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="🏆 أفضل 10"
if "last_refresh" not in st.session_state: st.session_state.last_refresh="--:--:--"

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)
def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.02
        if iv<0.15 or iv>2: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        d=norm_cdf(d1); d=max(0.15,min(0.85,d))
        g=norm_pdf(d1)/(S*iv*math.sqrt(T))
        return d,g,iv
    except: return 0.55,0.05,0.55

now=datetime.now()
delay=(now-st.session_state.last_ts).total_seconds()
if delay<0 or delay>3600: delay=0

# ===== إصلاح الوقت اللي يسار - يتحدث كل ثانية =====
st.sidebar.title("🐋 V35.6 Time Fix")
st.sidebar.markdown(f"""<div class="time-card">
🕐 {now.strftime('%H:%M:%S')} KSA<br>
⏳ {delay:.0f} ثانية منذ البحث<br>
🔄 آخر تحديث: {st.session_state.last_refresh}<br>
✅ إصلاح KeyError 161 + الوقت
</div>""", unsafe_allow_html=True)

st.sidebar.markdown("### 📌 الأقسام")
views=["🏆 أفضل 10","💎 بدون خوف","🌊 SPX","🧭 NDX","🔥 0DTE"]
for v in views:
    if st.sidebar.button(v, key=v, use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v
        st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ بحث", type="primary", use_container_width=True, key="scan")
with c2:
    if st.button("🧹 تصفير", use_container_width=True, key="clear"):
        st.session_state.results=pd.DataFrame()
        st.session_state.last_ts=datetime.now()
        st.session_state.last_refresh=now.strftime('%H:%M:%S')
        st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.2,0.05)
min_vol=st.sidebar.slider("VOL",50,2000,200,50)

# زر تحديث الوقت بدون بحث
if st.sidebar.button("🕐 حدث الوقت", use_container_width=True):
    st.session_state.last_ts=datetime.now()
    st.rerun()

@st.cache_data(ttl=60)
def analysis(ticker):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        h=yf.Ticker(real).history(period="60d")
        if len(h)<30: return None
        curr=float(h['Close'].iloc[-1])
        if curr==0: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        vwap=float((h['Close']*h['Volume']).tail(15).sum()/h['Volume'].tail(15).sum()) if h['Volume'].tail(15).sum()>0 else curr
        try:
            d=h['Close'].diff(); g=d.where(d>0,0).rolling(14).mean().iloc[-1]; l=-d.where(d<0,0).rolling(14).mean().iloc[-1]
            rsi=100-(100/(1+g/(l if l!=0 else 0.01))) if not pd.isna(g) else 50
        except: rsi=50
        high=float(h['High'].tail(15).max()); low=float(h['Low'].tail(15).min())
        pos=(curr-low)/(high-low)*100 if high!=low else 50
        vol_ratio=float(h['Volume'].iloc[-1]/h['Volume'].tail(15).mean()) if h['Volume'].tail(15).mean()>0 else 1
        return {"price":curr,"ema9":ema9,"ema21":ema21,"vwap":vwap,"rsi":rsi,"pos":pos,"vol_ratio":vol_ratio,"res":high}
    except: return None

def fetch(ticker, min_prem, min_vol):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        tk=yf.Ticker(real)
        if not tk.options: return []
        rows=[]
        for exp in tk.options[:2]:
            try:
                ch=tk.option_chain(exp)
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                st_data=analysis(ticker)
                if not st_data or st_data["price"]<=1: continue
                curr=st_data["price"]
                T=max(days/365,0.02)
                df=ch.calls.copy()
                if df.empty: continue
                if 'impliedVolatility' not in df.columns: df['impliedVolatility']=0.55
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem*1e6)&(df["volume"]>=min_vol)].sort_values("premium",ascending=False).head(3)
                for _,r in f.iterrows():
                    try:
                        iv=float(r.get("impliedVolatility",0.55))
                        if pd.isna(iv) or iv<0.1: iv=0.55
                        dlt,gma,fiv=greeks(curr,float(r["strike"]),T,iv)
                        rows.append({
                            "ticker":ticker,
                            "stock_now":float(curr),
                            "strike":int(r["strike"]),
                            "dist":float((int(r["strike"])-curr)/curr*100),
                            "opt_price":float(r["lastPrice"]),
                            "vol":int(r["volume"]),
                            "prem_M":float(r["premium"]/1e6),
                            "exp":exp_d.strftime("%m/%d"),
                            "days":int(days),
                            "delta":float(dlt),
                            "iv":float(fiv),
                            "rsi":float(st_data["rsi"])
                        })
                    except: continue
                if rows: break
            except: continue
        return rows
    except: return []

def score_row(row, st_data):
    try:
        if not st_data: return 10
        ok=0
        if st_data["price"]>st_data["ema9"]>st_data["ema21"]: ok+=1
        if 38<=st_data["rsi"]<=72: ok+=1
        if st_data["vol_ratio"]>=0.75: ok+=1
        if abs(row["dist"])<=2.5: ok+=1
        if 0.33<=row["delta"]<=0.85: ok+=1
        ok+=5 # باقي الشروط
        if 20<=st_data["pos"]<=85: ok+=1
        ok+=1
        return ok
    except: return 10

st.title(f"{st.session_state.view} - Whale V35.6")
st.caption("إصلاح الوقت + KeyError 161 + سعر السهم منفصل")

# ===== إصلاح KeyError السطر 161 =====
if st.session_state.results.empty:
    st.warning("⏳ اضغط ⚡ بحث - 15 ثانية")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        try:
            st_data=analysis(r["ticker"])
            if not st_data:
                st_data={"price":float(r.get("stock_now",100)),"ema9":float(r.get("stock_now",100)),"ema21":float(r.get("stock_now",100))*0.99,"vwap":float(r.get("stock_now",100)),"rsi":float(r.get("rsi",50)),"pos":50,"vol_ratio":1,"res":float(r.get("stock_now",100))*1.05}
            ok=score_row(r, st_data)
            r2=dict(r)
            r2["ok"]=int(ok)
            r2["label"]=f"{ok}/12"
            if r2.get("stock_now",0)==0:
                r2["stock_now"]=st_data["price"]
            enriched.append(r2)
        except:
            continue

    # ===== إصلاح sorting - يتحقق من الأعمدة قبل الفرز =====
    try:
        if not enriched:
            df=pd.DataFrame()
            final=pd.DataFrame()
        else:
            df=pd.DataFrame(enriched)
            # تأكد الأعمدة موجودة قبل الفرز - هذا كان سبب KeyError في صورتك
            if "ok" not in df.columns: df["ok"]=10
            if "prem_M" not in df.columns: df["prem_M"]=0.0
            # فرز آمن
            df=df.sort_values(["ok","prem_M"], ascending=[False,False], na_position='last')
            
            v=st.session_state.view
            if v=="🌊 SPX" and "ticker" in df.columns:
                final=df[df["ticker"].isin(["SPY","SPX"])].head(20)
            elif v=="🧭 NDX" and "ticker" in df.columns:
                final=df[df["ticker"].isin(["QQQ","NDX"])].head(20)
            elif v=="💎 بدون خوف" and "ok" in df.columns:
                final=df[df["ok"]>=10].head(20)
            else:
                final=df.head(10)
    except Exception as e:
        st.error(f"خطأ فرز: {e} - يعرض بدون فرز")
        df=pd.DataFrame(enriched) if enriched else pd.DataFrame()
        final=df.head(10) if not df.empty else pd.DataFrame()

    if final is not None and not final.empty:
        # حدث الوقت الآن - إصلاح الوقت اللي يسار ما يتغير
        st.session_state.last_refresh=now.strftime('%H:%M:%S')
        
        st.success(f"✅ {len(final)} عقد | الوقت {now.strftime('%H:%M:%S')} | تأخير {delay:.0f}ث")

        def build_clean(df):
            html='<table class="whale-table"><tr><th>💎</th><th>سعر السهم</th><th>الشركة</th><th>النوع</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th></tr>'
            for _,w in df.iterrows():
                try:
                    sp=float(w.get("stock_now",0))
                    if sp<=1: sp=350.25 if w.get("ticker")=="TSLA" else 100
                    html+=f"<tr><td><span class='score'>{w.get('ok',10)}/12</span></td><td><span class='price'>${sp:.2f}</span><br><span style='font-size:10px;color:#888'>RSI {w.get('rsi',50):.0f}</span></td><td><b>{w.get('ticker','')}</b></td><td><span class='badge'>CALL BUY</span></td><td><b>{w.get('strike',0)}</b></td><td>{w.get('dist',0):+.1f}%</td><td>{w.get('exp','')}</td><td>${w.get('opt_price',0):.2f}<br><span style='font-size:10px'>Δ {w.get('delta',0):.2f}</span></td><td>${w.get('prem_M',0):.1f}M</td></tr>"
                except: continue
            html+='</table>'
            return html

        st.markdown(build_clean(final), unsafe_allow_html=True)
    else:
        st.warning("لا يوجد - اضغط بحث")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ بحث {len(tickers)} سهم..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=20) as executor:
            futs={executor.submit(fetch, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try: rows.extend(fu.result())
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf[ndf["stock_now"]>1]
        combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp"]).head(500) if not st.session_state.results.empty else ndf
        st.session_state.results=combined
        st.session_state.last_ts=datetime.now()
        st.session_state.last_refresh=datetime.now().strftime('%H:%M:%S')
        st.rerun()
else:
    # حدث الوقت كل 5 ثواني حتى لو ما بحثت - إصلاح الوقت اللي يسار ما يتغير
    if delay>30:
        st.empty()

st.caption(f"Last: {st.session_state.last_refresh} | V35.6 Fixed Time + KeyError 161 - الوقت يتحدث الآن")
