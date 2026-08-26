import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V49 ONE DIR", initial_sidebar_state="collapsed")

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

def supertrend(df, period=10, multiplier=3.0):
    try:
        hl2=(df['High']+df['Low'])/2
        atr=(df['High']-df['Low']).ewm(alpha=1/period, adjust=False).mean()
        upper=hl2+multiplier*atr
        lower=hl2-multiplier*atr
        st_line=pd.Series(index=df.index, dtype=float)
        direction=pd.Series(index=df.index, dtype=int)
        st_line.iloc[0]=float(lower.iloc[0])
        direction.iloc[0]=1
        for i in range(1,len(df)):
            close=float(df['Close'].iloc[i])
            prev_line=float(st_line.iloc[i-1])
            if close>prev_line:
                st_line.iloc[i]=max(float(lower.iloc[i]),prev_line) if direction.iloc[i-1]==1 else float(lower.iloc[i])
                direction.iloc[i]=1
            else:
                st_line.iloc[i]=min(float(upper.iloc[i]),prev_line) if direction.iloc[i-1]==-1 else float(upper.iloc[i])
                direction.iloc[i]=-1
        return st_line, direction
    except:
        return pd.Series([float(df['Close'].iloc[-1])]*len(df), index=df.index), pd.Series([1]*len(df), index=df.index)

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V49 اتجاه واحد فقط | COIN -3% = PUT فقط مستحيل CALL</div>', unsafe_allow_html=True)

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
with b1: do_scan_main=st.button("⚡ فحص اتجاه واحد", type="primary")
with b2:
    if st.button("🧹 تصفير يحل COIN مكرر"):
        st.session_state.results=pd.DataFrame(); st.cache_data.clear(); st.rerun()

min_prem=0.15
min_vol=80
with st.sidebar:
    min_prem=st.slider("💰 M$",0.05,3.0,0.15,0.05)
    min_vol=st.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=40)
def analysis_v49(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="3mo")
        if len(h)<60: return None
        h=h.dropna()
        if len(h)<60: return None
        curr=float(h['Close'].iloc[-1])
        if ticker=="NFLX" and curr<200: return None
        if ticker=="AVGO" and curr<150: return None
        if ticker=="SPY" and curr>700: return None
        if pd.isna(curr) or curr<5 or curr>3000: return None
        st_line, st_dir=supertrend(h,10,3.0)
        st_direction=int(st_dir.iloc[-1])
        ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
        if pd.isna(ema9) or pd.isna(ema21): return None
        h20=h.tail(20)
        vol_sum=float(h20['Volume'].sum())
        vwap=float((h20['Close']*h20['Volume']).sum()/vol_sum) if vol_sum>0 else curr
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll<0.01: ll=0.01
        rsi=100-(100/(1+lg/ll))
        if pd.isna(rsi): rsi=50
        rsi=float(max(5,min(95,rsi)))
        ema12=h['Close'].ewm(span=12).mean()
        ema26=h['Close'].ewm(span=26).mean()
        macd=ema12-ema26
        hist=macd-macd.ewm(span=9).mean()
        macd_hist=float(hist.iloc[-1])
        macd_hist_prev=float(hist.iloc[-2]) if len(hist)>=2 else macd_hist
        macd_bull=macd_hist>0 and macd_hist>macd_hist_prev
        macd_bear=macd_hist<0 and macd_hist<macd_hist_prev
        high60=float(h['High'].tail(60).max())
        low60=float(h['Low'].tail(60).min())
        fib_236=high60-(high60-low60)*0.236
        bounce_fib=curr>fib_236 and float(h['Low'].iloc[-1])<=fib_236*1.01
        vol_avg20=float(h['Volume'].tail(20).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=float(vol_today/vol_avg20) if vol_avg20>0 else 1.0
        vol_ratio=float(max(0.1,min(5.0,vol_ratio)))
        try:
            prev_close=float(h['Close'].iloc[-2])
            change_1d=float((curr-prev_close)/prev_close*100) if prev_close>0 else 0.0
        except: change_1d=0.0
        if pd.isna(change_1d): change_1d=0.0
        try:
            close_5d=float(h['Close'].iloc[-6])
            change_5d=float((curr-close_5d)/close_5d*100) if close_5d>0 else 0.0
        except: change_5d=change_1d
        if pd.isna(change_5d): change_5d=change_1d
        # اتجاه واحد واضح - COIN -3% = هابط
        trend="NEUTRAL"
        if change_1d>=0.8 and curr>vwap and st_direction==1:
            trend="BULL"
        elif change_1d<=-0.8 and curr<vwap and st_direction==-1:
            trend="BEAR"
        elif change_1d>=1.5:
            trend="BULL"
        elif change_1d<=-1.5:
            trend="BEAR"
        return {"price":curr,"vwap":vwap,"rsi":rsi,"fib_236":fib_236,"vol_ratio":vol_ratio,"change_1d":change_1d,"change_5d":change_5d,"st_dir":st_direction,"macd_bull":macd_bull,"macd_bear":macd_bear,"bounce_fib":bounce_fib,"trend":trend}
    except: return None

def fetch_v49(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_v49(ticker)
        if not sd: return []
        curr=sd["price"]
        trend=sd["trend"]
        if trend=="NEUTRAL": return [] # لا تعطي إذا متذبذب - يحل COIN CALL+PUT
        if sd["vol_ratio"]<0.6: return [] # VOL x0.3 ضعيف - لا تعطي
        rows=[]
        for exp in tk.options[:2]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<1 or days>21: continue
                T=max(days/365,0.04)
                chain=tk.option_chain(exp)
                # اتجاه واحد فقط
                if trend=="BULL":
                    allowed=["CALL"]
                elif trend=="BEAR":
                    allowed=["PUT"]
                else:
                    continue
                for opt_type in allowed:
                    df_opt=chain.calls if opt_type=="CALL" else chain.puts
                    if df_opt.empty: continue
                    df_opt=df_opt.copy().dropna(subset=['volume','lastPrice'])
                    df_opt=df_opt[df_opt['volume']>0]
                    df_opt['prem']=df_opt['lastPrice']*df_opt['volume']*100
                    df_opt=df_opt[df_opt['prem']>=min_prem*1e6]
                    df_opt=df_opt[df_opt['volume']>=min_vol]
                    if df_opt.empty: continue
                    df_opt=df_opt.sort_values('prem',ascending=False).head(1)
                    for _,r in df_opt.iterrows():
                        try:
                            strike=float(r['strike'])
                            if pd.isna(strike): continue
                            dist=(strike-curr)/curr*100 if curr!=0 else 0
                            if abs(dist)>4: continue
                            iv=r.get('impliedVolatility',0.5)
                            if pd.isna(iv): iv=0.5
                            delta=calc_delta(curr,strike,T,iv,opt_type=="CALL")
                            if pd.isna(delta): continue
                            if opt_type=="CALL" and (delta<0.30 or delta>0.70): continue
                            if opt_type=="PUT" and (delta>-0.30 or delta<-0.70): continue
                            last_price=float(r['lastPrice'])
                            vol=int(r['volume'])
                            if pd.isna(last_price) or last_price==0: continue
                            prem=float(last_price*vol*100/1e6)
                            if pd.isna(prem) or prem==0: continue
                            rows.append({"ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),"opt_price":float(last_price),"vol":int(vol),"oi":int(r.get('openInterest',0) or 0),"prem_M":float(prem),"exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),"days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),"change_1d":float(sd["change_1d"]),"change_5d":float(sd["change_5d"]),"st_dir":int(sd["st_dir"]),"bounce_fib":bool(sd["bounce_fib"]),"macd_bull":bool(sd["macd_bull"]),"macd_bear":bool(sd["macd_bear"]),"vwap":float(sd["vwap"]),"trend":trend})
                        except: continue
                if len(rows)>=1: break
            except: continue
        return rows
    except: return []

def calc_confirm_v49(row):
    try:
        score=50
        ch1=float(row.get("change_1d",0))
        ch5=float(row.get("change_5d",0))
        vol_r=float(row.get("vol_ratio",1))
        rsi=float(row.get("rsi",50))
        if row["type"]=="CALL":
            if ch1>=1.5: score+=18
            elif ch1>=0.5: score+=10
            elif ch1<0: score-=20
            if ch5>=3: score+=10
            elif ch5<0: score-=8
            if float(row.get("stock_now",0))>float(row.get("vwap",0)): score+=8
            else: score-=12
            if 50<=rsi<=68: score+=10
            elif rsi>75: score-=5
            if vol_r>=1.5: score+=12
            elif vol_r<0.8: score-=10
            if int(row.get("st_dir",0))==1: score+=8
            else: score-=15
        else:
            if ch1<=-1.5: score+=18
            elif ch1<=-0.5: score+=12
            elif ch1>0.5: score-=20
            if ch5<=-2: score+=10
            if vol_r>=1.2: score+=10
        score=int(max(35,min(88,score)))
        why=f"اليوم {ch1:+.1f}% | 5d {ch5:+.1f}% | {row.get('trend')} | RSI {rsi:.0f} | VOL x{vol_r:.1f}"
        return score, why
    except: return 55, "متوسط"

# AUTO SCAN إذا فاضي
if st.session_state.results.empty:
    st.info("⏳ يفحص - اتجاه واحد فقط لكل شركة - COIN -3% = PUT فقط")
    tickers=["AAPL","NVDA","TSLA","META","MSFT","AMD","AVGO","AMZN","COIN","PLTR","HOOD","SOFI","QQQ","MSTR"]
    with st.spinner(f"⚡ فحص {len(tickers)} - اتجاه واحد..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v49, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.dropna(subset=['stock_now','prem_M'])
        ndf=ndf[(ndf["stock_now"]>5)&(ndf["stock_now"]<3000)&(ndf["prem_M"]>0)]
        # شركة واحدة = صف واحد فقط - يحل COIN مكرر
        ndf=ndf.sort_values("prem_M", ascending=False)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        if not ndf.empty:
            st.session_state.results=ndf
            st.rerun()
    else:
        st.warning("لا يوجد - اضغط فحص")
        final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        if pd.isna(r.get("stock_now",0)): continue
        conf, why=calc_confirm_v49(r)
        r2=dict(r); r2["confirm"]=int(conf); r2["why"]=why
        enriched.append(r2)
    if enriched:
        df=pd.DataFrame(enriched)
        df=df.dropna(subset=['confirm','stock_now'])
        df=df.sort_values(["confirm","prem_M"], ascending=[False][False])
        # شركة واحدة فقط
        df=df.drop_duplicates(subset=["ticker"], keep="first")
        v=st.session_state.view
        if "BUY قوي" in v: final=df[(df["type"]=="CALL")].head(20)
        elif "SELL قوي" in v: final=df[(df["type"]=="PUT")].head(20)
        else: final=df.head(20)
    else: final=pd.DataFrame()

if 'final' in locals() and not final.empty:
    st.success(f"✅ {len(final)} شركة - كل شركة اتجاه واحد فقط - {ksa_str}")
    for _,w in final.head(4).iterrows():
        conf=int(w.get("confirm",60))
        border="#16a34a" if w.get("type")=="CALL" else "#dc2626"
        icon="🟢" if w.get("type")=="CALL" else "🔴"
        st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;"><b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} اليوم {float(w.get('change_1d',0)):+.1f}% | {w.get('trend')} | VOL x{float(w.get('vol_ratio',1)):.1f} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.1f}M | {w.get('exp_short')}</span></div>""", unsafe_allow_html=True)
    html='<table class="big-table"><tr><th>%</th><th>نوع</th><th>شركة</th><th>سهم اليوم</th><th>سترايك</th><th>📅</th><th>عقد</th><th>حوت</th></tr>'
    for _,w in final.iterrows():
        try:
            sp=float(w.get("stock_now",0))
            conf=int(w.get("confirm",60)); ch1=float(w.get("change_1d",0))
            prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
            badge=f'<span class="call-badge">{w.get("type")}</span>' if w.get("type")=="CALL" else f'<span class="put-badge">{w.get("type")}</span>'
            html+=f'<tr><td><b>{conf}%</b><br>{w.get("trend")}</td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch1>=0 else "#dc2626"}">{ch1:+.1f}%</span></td><td><b>{int(w.get("strike",0))}</b><br>{float(w.get("dist",0)):+.1f}%</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}<br>{int(w.get("vol",0))/1000:.0f}K</td><td>${prem:.1f}M<br>x{float(w.get("vol_ratio",1)):.1f}</td></tr>'
        except: continue
    html+='</table>'
    st.markdown(html, unsafe_allow_html=True)

if do_scan_main:
    tickers=["AVGO","AAPL","NVDA","TSLA","META","MSFT","AMD","AMZN","COIN","MSTR","PLTR","HOOD","SOFI","QQQ"]
    with st.spinner(f"⚡ فحص {len(tickers)}..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v49, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.dropna(subset=['stock_now','prem_M'])
        ndf=ndf[(ndf["stock_now"]>5)&(ndf["stock_now"]<3000)&(ndf["prem_M"]>0)]
        ndf=ndf.sort_values("prem_M", ascending=False)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        if not ndf.empty:
            st.session_state.results=ndf
            st.rerun()

st.caption(f"V49 ONE DIRECTION | {ksa_str} | شركة واحدة = اتجاه واحد | COIN -3% = PUT فقط | VOL x0.3 محذوف")
