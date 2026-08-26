import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V38 STRONG & CLEAR", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
[data-testid="stSidebar"] {background:#f5f5f5!important; min-width:300px!important;}
/* جدول كبير واضح */
.big-table {width:100%; border-collapse:collapse; font-size:15px; margin-top:10px;}
.big-table th {background:#000!important; color:#fff!important; padding:14px 8px; text-align:center; font-size:13px; font-weight:800; border:1px solid #000;}
.big-table td {background:#fff!important; padding:14px 8px; text-align:center; border:1px solid #ddd; font-size:14px; font-weight:700; color:#000;}
.strong-card {background:#fff; border:3px solid #16a34a; border-radius:16px; padding:16px; margin:10px 0; box-shadow:0 4px 12px rgba(0,0,0,0.1);}
.strong-title {font-size:18px; font-weight:900; color:#14532d;}
.score-big {background:#14532d; color:#fff; padding:8px 16px; border-radius:12px; font-size:18px; font-weight:900;}
.badge-buy {background:#16a34a; color:#fff; padding:6px 12px; border-radius:10px; font-size:12px; font-weight:800;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:12px; font-family:monospace; text-align:center; font-size:13px; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","HOOD","AVGO","NFLX"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ دخول آمن فقط"

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))
def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.05
        if iv<0.1 or iv>4: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        return max(0.20,min(0.80,0.5*(1.0+math.erf(d1/math.sqrt(2.0))))), iv
    except: return 0.55,0.55

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')
try: delay=(now-st.session_state.last_ts).total_seconds()
except: delay=0
if delay<0 or delay>3600: delay=0

st.sidebar.title("💎 V38 عقد قوي")
st.sidebar.markdown(f'<div class="time-card">● {ksa_str} KSA<br>⏳ {delay:.0f}ث<br>خط كبير 14px</div>', unsafe_allow_html=True)
st.sidebar.markdown("### 📌")
for v in ["✅ دخول آمن فقط","💎 10+ قوي","🔥 انفجار","↩️ انعكاس","🏆 الكل"]:
    if st.sidebar.button(v, key=v, use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v; st.rerun()
st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص قوي", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True): st.session_state.results=pd.DataFrame(); st.session_state.last_ts=datetime.now(); st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.15,0.05)
min_vol=st.sidebar.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=40)
def analysis_strong(ticker):
    try:
        real="SPY" if ticker=="SPX" else ticker
        h=yf.Ticker(real).history(period="6mo")
        if len(h)<50: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        ema50=float(h['Close'].ewm(50).mean().iloc[-1])
        vwap=float((h.tail(20)['Close']*h.tail(20)['Volume']).sum()/h.tail(20)['Volume'].sum())
        # RSI
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
        lg=float(g.iloc[-1]); ll=float(l.iloc[-1])
        if ll==0: ll=0.01
        rsi=100-(100/(1+lg/ll))
        # تحليل قوي
        high20=float(h['High'].tail(20).max()); low20=float(h['Low'].tail(20).min())
        vol_avg=float(h['Volume'].tail(20).mean()); vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=vol_today/vol_avg if vol_avg>0 else 1
        # انفجار: فوق High20 + VOL عالي + فوق VWAP
        breakout = curr>=high20*0.985 and vol_ratio>=1.3 and curr>vwap and curr>ema9>ema21
        # انعكاس: قريب من Low20 + RSI <42
        reversal = (curr<=low20*1.08 and rsi<45) or (rsi<38)
        support_strength = (curr-low20)/low20*100
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        return {"price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"rsi":float(rsi),"high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),"breakout":breakout,"reversal":reversal,"support":support_strength}
    except: return None

def fetch_strong(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_strong(ticker)
        if not sd: return []
        curr=sd["price"]
        rows=[]
        for exp in tk.options[:3]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                T=max(days/365,0.04)
                calls=tk.option_chain(exp).calls
                if calls.empty: continue
                calls=calls.copy()
                calls=calls[calls['volume']>0]
                calls['prem']=calls['lastPrice']*calls['volume']*100
                calls=calls[calls['prem']>=min_prem*1e6]
                calls=calls[calls['volume']>=min_vol]
                if calls.empty: continue
                calls=calls.sort_values('prem',ascending=False).head(4)
                for _,r in calls.iterrows():
                    try:
                        strike=float(r['strike']); dist=(strike-curr)/curr*100
                        if abs(dist)>6: continue
                        iv=float(r.get('impliedVolatility',0.5))
                        if pd.isna(iv): iv=0.5
                        delta,_=greeks(curr,strike,T,iv)
                        if delta<0.25 or delta>0.75: continue
                        prem=float(r['lastPrice']*float(r['volume'])*100/1e6)
                        opt=float(r['lastPrice']); vol=int(r['volume']); oi=int(r.get('openInterest',0))
                        bid=float(r.get('bid',0)); ask=float(r.get('ask',0))
                        spread=(ask-bid)/opt*100 if opt>0 and bid>0 else 10
                        if prem==0 or opt==0: continue
                        # عقد قوي = تحوط بسيط فقط
                        is_hedge = oi>0 and vol/oi<0.08 and days>12 and spread>18
                        rows.append({"ticker":ticker,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),"opt_price":float(opt),"vol":int(vol),"oi":int(oi),"prem_M":float(prem),"exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),"days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),"spread":float(spread),"is_hedge":bool(is_hedge),"breakout":bool(sd["breakout"]),"reversal":bool(sd["reversal"]),"pos":float(sd["pos"]),"vwap":float(sd["vwap"]),"high20":float(sd["high20"]),"low20":float(sd["low20"])})
                    except: continue
                if len(rows)>=2: break
            except: continue
        return rows
    except: return []

def score_strong(row, sd):
    if not sd: return 7, "لا بيانات"
    s=0; why=[]
    if sd["price"]>sd["ema9"]>sd["ema21"]: s+=2; why.append("ترند صاعد EMA9>21")
    elif sd["price"]>sd["ema9"]: s+=1; why.append("فوق EMA9")
    if 38<=sd["rsi"]<=67: s+=2; why.append(f"RSI {sd['rsi']:.0f} قوي")
    elif sd["rsi"]<38: s+=2; why.append(f"RSI {sd['rsi']:.0f} انعكاس")
    if sd["vol_ratio"]>=1.5: s+=3; why.append(f"🔥 VOL انفجار x{sd['vol_ratio']:.1f}")
    elif sd["vol_ratio"]>=1.1: s+=1; why.append(f"VOL x{sd['vol_ratio']:.1f}")
    if abs(row["dist"])<=1.2: s+=3; why.append("ATM قوي 1.2%")
    elif abs(row["dist"])<=2.5: s+=2; why.append(f"قريب {row['dist']:+.1f}%")
    else: s+=1
    if 0.35<=row["delta"]<=0.60: s+=2; why.append(f"Δ {row['delta']:.2f} آمن")
    else: s+=1
    if row["spread"]<5: s+=1; why.append(f"سبريد {row['spread']:.0f}% ضيق")
    if sd["breakout"]: s+=3; why.append(f"اختراق High20 ${sd['high20']:.2f}")
    if sd["reversal"]: s+=3; why.append(f"انعكاس من ${sd['low20']:.2f}")
    if sd["pos"]>=70 and sd["pos"]<=95: s+=1; why.append(f"موقع قوي {sd['pos']:.0f}%")
    if row["is_hedge"]: s-=4; why.append("⚠️ تحوط")
    s=max(0,min(12,s))
    return s, " | ".join(why[:4])

st.title(f"{st.session_state.view} - عقد قوي يعتمد عليه {ksa_str}")
st.caption("عقد قوي = انفجار + انعكاس + ATM + VOL + بدون تحوط - جدول خط 14px واضح")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص قوي - بيطلع 3 عقود قوية فقط")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        sd=analysis_strong(r["ticker"])
        ok,reason=score_strong(r, sd)
        r2=dict(r); r2["ok"]=int(ok); r2["reason"]=reason
        enriched.append(r2)

    if enriched:
        df=pd.DataFrame(enriched)
        df=df.sort_values(["ok","prem_M"], ascending=[False,False])
        v=st.session_state.view
        if v=="✅ دخول آمن فقط": final=df[(df["ok"]>=9) & (df["is_hedge"]==False)].head(6)
        elif v=="💎 10+ قوي": final=df[df["ok"]>=10].head(8)
        elif v=="🔥 انفجار": final=df[df["breakout"]==True].head(8)
        elif v=="↩️ انعكاس": final=df[df["reversal"]==True].head(8)
        else: final=df.head(10)
        if final.empty: final=df.head(6)
    else:
        final=pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد قوي | {ksa_str} | تأخير {delay:.0f}ث")

        # كروت كبيرة - عقد قوي يعتمد عليه
        for _,w in final.head(3).iterrows():
            if w.get("ok",0)>=9:
                entry=float(w.get("stock_now",0))
                target=entry*1.04
                stop=entry*0.985
                st.markdown(f"""
                <div class="strong-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                <span class="strong-title">✅ {w.get('ticker')} {int(w.get('strike'))} CALL - عقد قوي</span>
                <span class="score-big">{int(w.get('ok'))}/12</span>
                </div>
                <div style="margin-top:10px; font-size:14px; line-height:1.8; color:#000;">
                📊 <b>السهم:</b> ${entry:.2f} | VWAP ${float(w.get('vwap',0)):.2f} | High20 ${float(w.get('high20',0)):.2f}<br>
                🎯 <b>سترايك:</b> {int(w.get('strike'))} ({float(w.get('dist',0)):+.2f}%) | Δ {float(w.get('delta',0)):.2f} | RSI {float(w.get('rsi',0)):.0f}<br>
                💰 <b>العقد:</b> ${float(w.get('opt_price',0)):.2f} | الحوت ${float(w.get('prem_M',0)):.1f}M | VOL {int(w.get('vol',0))/1000:.1f}K<br>
                🔍 <b>لماذا قوي:</b> {w.get('reason')}<br>
                🚀 <b>دخول:</b> الآن ${entry:.2f} | <b>هدف السهم:</b> ${target:.2f} (+4%) | <b>وقف:</b> ${stop:.2f} (-1.5%)<br>
                💎 <b>هدف العقد:</b> +50% إلى +90% | <b>وقف العقد:</b> -25%
                </div>
                <div style="margin-top:8px;"><span class="badge-buy">CALL BUY - دخول آمن</span> <span style="font-size:12px;"> {w.get('exp_short')} ({int(w.get('days'))} يوم)</span></div>
                </div>
                """, unsafe_allow_html=True)

        # جدول كبير واضح 14px
        html='<table class="big-table"><tr><th>💎</th><th>الشركة</th><th>سعر السهم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th><th>قوة</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0)); ok=int(w.get("ok",0))
                if sp<1: sp=100
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0)); dlt=float(w.get("delta",0.55)); vol=int(w.get("vol",0)); oi=int(w.get("oi",0))
                html+=f'<tr><td><b>{ok}/12</b></td><td><b style="font-size:16px">{w.get("ticker","")}</b><br><span style="font-size:11px;color:#555">{w.get("reason","")[:25]}</span></td><td><b style="font-size:15px;color:#15803d">${sp:.2f}</b><br><span style="font-size:11px">RSI {float(w.get("rsi",50)):.0f} VOLx{float(w.get("vol_ratio",1)):.1f}</span></td><td><b style="font-size:16px">{int(w.get("strike",0))}</b></td><td><b>{dist:+.2f}%</b><br>Δ {dlt:.2f}</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td><b style="font-size:15px">${opt_p:.2f}</b><br><span style="font-size:11px">{vol/1000:.0f}K / {oi/1000:.0f}K</span></td><td><b style="font-size:15px">${prem:.1f}M</b><br><span style="font-size:11px">S{float(w.get("spread",0)):.0f}%</span></td><td><b>{"✅ قوي" if ok>=10 else "👍 جيد" if ok>=8 else "⚠️ متوسط"}</b></td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد - اضغط كل الحيتان")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ فحص {len(tickers)} عقد قوي..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=12) as executor:
            futs={executor.submit(fetch_strong, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf[(ndf["stock_now"]>1)&(ndf["prem_M"]>0)]
        if not ndf.empty:
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_full"]).head(600) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

st.caption(f"V38 STRONG CLEAR | {ksa_str} KSA | جدول 14px واضح | 3 عقود قوية فقط - دخول آمن + انفجار + انعكاس")
