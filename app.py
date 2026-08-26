import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V38.1 FIX KeyError", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:15px; margin-top:15px;}
.big-table th {background:#000!important; color:#fff!important; padding:14px 6px; text-align:center; font-size:12px; font-weight:800;}
.big-table td {background:#fff!important; padding:14px 6px; text-align:center; border:1px solid #ccc; font-size:14px; font-weight:700; color:#000;}
.strong-card {background:#fff; border:3px solid #16a34a; border-radius:16px; padding:16px; margin:12px 0;}
.score-big {background:#14532d; color:#fff; padding:8px 16px; border-radius:12px; font-size:18px; font-weight:900;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:12px; font-family:monospace; text-align:center; font-size:13px; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","HOOD","AVGO","NFLX","AMZN"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ دخول آمن فقط"

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))
def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.05
        if iv<0.1 or iv>4: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        return max(0.20,min(0.80, norm_cdf(d1))), iv
    except: return 0.55,0.55

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')
try: delay=(now-st.session_state.last_ts).total_seconds()
except: delay=0
if delay<0 or delay>3600: delay=0

st.sidebar.title("💎 V38.1 بدون KeyError")
st.sidebar.markdown(f'<div class="time-card">● {ksa_str} KSA<br>⏳ {delay:.0f}ث<br>إصلاح انفجار</div>', unsafe_allow_html=True)

for v in ["✅ دخول آمن فقط","💎 10+ قوي","🔥 انفجار","↩️ انعكاس","🏆 الكل"]:
    if st.sidebar.button(v, key=f"btn_{v}", use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v
        st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص قوي", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير - يحل KeyError", use_container_width=True):
        st.session_state.results=pd.DataFrame()
        st.session_state.last_ts=datetime.now()
        st.cache_data.clear()
        st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.15,0.05)
min_vol=st.sidebar.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=40)
def analysis_strong(ticker):
    try:
        h=yf.Ticker(ticker if ticker!="SPX" else "SPY").history(period="3mo")
        if len(h)<40: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        h20=h.tail(20)
        vwap=float((h20['Close']*h20['Volume']).sum()/h20['Volume'].sum()) if h20['Volume'].sum()>0 else curr
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
        lg=float(g.iloc[-1]); ll=float(l.iloc[-1])
        if ll==0: ll=0.01
        rsi=100-(100/(1+lg/ll))
        high20=float(h['High'].tail(20).max()); low20=float(h['Low'].tail(20).min())
        vol_avg=float(h['Volume'].tail(20).mean()); vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=vol_today/vol_avg if vol_avg>0 else 1
        breakout = curr>=high20*0.985 and vol_ratio>=1.2 and curr>vwap
        reversal = (curr<=low20*1.08 and rsi<45) or (rsi<38)
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        return {"price":curr,"ema9":ema9,"ema21":ema21,"vwap":vwap,"rsi":float(rsi),"high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),"breakout":bool(breakout),"reversal":bool(reversal)}
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
                if 'volume' not in calls.columns or 'lastPrice' not in calls.columns: continue
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
                        if delta<0.20 or delta>0.80: continue
                        prem=float(r['lastPrice']*float(r['volume'])*100/1e6)
                        opt=float(r['lastPrice']); vol=int(r['volume']); oi=int(r.get('openInterest',0))
                        bid=float(r.get('bid',0)); ask=float(r.get('ask',0))
                        spread=(ask-bid)/opt*100 if opt>0 and bid>0 else 10
                        if prem==0 or opt==0: continue
                        is_hedge = oi>0 and vol/oi<0.08 and days>12 and spread>18
                        rows.append({
                            "ticker":ticker,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),
                            "opt_price":float(opt),"vol":int(vol),"oi":int(oi),"prem_M":float(prem),
                            "exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),
                            "days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),
                            "vol_ratio":float(sd["vol_ratio"]),"spread":float(spread),
                            "is_hedge":bool(is_hedge),"breakout":bool(sd["breakout"]),"reversal":bool(sd["reversal"]),
                            "pos":float(sd["pos"]),"vwap":float(sd["vwap"]),"high20":float(sd["high20"]),"low20":float(sd["low20"])
                        })
                    except: continue
                if len(rows)>=2: break
            except: continue
        return rows
    except: return []

def score_strong(row, sd):
    if not sd: return 7, "لا بيانات"
    s=0; why=[]
    try:
        if sd["price"]>sd["ema9"]>sd["ema21"]: s+=2; why.append("ترند صاعد")
        elif sd["price"]>sd["ema9"]: s+=1
        if 35<=sd["rsi"]<=67: s+=2; why.append(f"RSI {sd['rsi']:.0f}")
        elif sd["rsi"]<35: s+=2; why.append("انعكاس")
        if sd["vol_ratio"]>=1.5: s+=3; why.append(f"VOL x{sd['vol_ratio']:.1f}")
        elif sd["vol_ratio"]>=1.0: s+=1
        if abs(row["dist"])<=1.5: s+=3; why.append("ATM قوي")
        elif abs(row["dist"])<=3: s+=2
        if 0.35<=row["delta"]<=0.60: s+=2; why.append(f"Δ {row['delta']:.2f}")
        if sd["breakout"]: s+=3; why.append("انفجار High20")
        if sd["reversal"]: s+=3; why.append("انعكاس")
        if row["is_hedge"]: s-=4
        s=max(0,min(12,s))
        return s, " | ".join(why[:4])
    except: return 7, "خطأ"

st.title(f"{st.session_state.view} - {ksa_str}")
st.caption("V38.1 إصلاح KeyError انفجار - جدول واضح 14px")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص قوي - أول مرة")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        sd=analysis_strong(r["ticker"])
        ok,reason=score_strong(r, sd)
        r2=dict(r); r2["ok"]=int(ok); r2["reason"]=reason
        # تأكد كل الأعمدة موجودة - إصلاح KeyError
        if "breakout" not in r2: r2["breakout"]=False
        if "reversal" not in r2: r2["reversal"]=False
        if "is_hedge" not in r2: r2["is_hedge"]=False
        enriched.append(r2)

    if enriched:
        df=pd.DataFrame(enriched)
        # إصلاح KeyError - لو الأعمدة ناقصة - أنشئها
        for col in ["breakout","reversal","is_hedge","ok","prem_M"]:
            if col not in df.columns:
                df[col]=False if col in ["breakout","reversal","is_hedge"] else 0

        df=df.sort_values(["ok","prem_M"], ascending=[False,False])
        v=st.session_state.view

        # كلها آمنة - بدون KeyError
        try:
            if "🔥" in v or "انفجار" in v:
                if df["breakout"].any():
                    final=df[df["breakout"]==True].head(10)
                else:
                    # لو ما فيه انفجار - رتب حسب VOL
                    final=df.sort_values("vol_ratio", ascending=False).head(10)
            elif "انعكاس" in v:
                if df["reversal"].any():
                    final=df[df["reversal"]==True].head(10)
                else:
                    final=df[df["rsi"]<45].head(10) if "rsi" in df.columns else df.head(10)
            elif "آمن" in v:
                final=df[(df["ok"]>=9) & (df["is_hedge"]==False)].head(10)
                if final.empty: final=df[df["ok"]>=8].head(10)
            elif "10+" in v:
                final=df[df["ok"]>=10].head(10)
            else:
                final=df.head(12)
        except Exception as e:
            st.warning(f"فلتر: {e} - أعرض الكل")
            final=df.head(12)

        if final.empty:
            final=df.head(10)
    else:
        final=pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد | {ksa_str} | بدون KeyError")

        for _,w in final.head(3).iterrows():
            if w.get("ok",0)>=8:
                st.markdown(f"""
                <div class="strong-card">
                <b style="font-size:17px;">✅ {w.get('ticker')} {int(w.get('strike'))} CALL - {int(w.get('ok'))}/12</b> - {w.get('reason')}<br>
                <span style="font-size:14px; color:#000;">
                السهم ${float(w.get('stock_now',0)):.2f} → {int(w.get('strike'))} ({float(w.get('dist',0)):+.1f}%) | العقد ${float(w.get('opt_price',0)):.2f} Δ{float(w.get('delta',0)):.2f}<br>
                الحوت ${float(w.get('prem_M',0)):.1f}M | VOL {int(w.get('vol',0))/1000:.1f}K | {w.get('exp_short')} ({int(w.get('days'))}ي)<br>
                🎯 هدف +50% وقف -25%
                </span>
                </div>
                """, unsafe_allow_html=True)

        html='<table class="big-table"><tr><th>💎</th><th>الشركة</th><th>سعر السهم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th><th>قوة</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0)); ok=int(w.get("ok",0))
                if sp<1: sp=100
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0)); dlt=float(w.get("delta",0.5)); vol=int(w.get("vol",0))
                html+=f'<tr><td><b>{ok}/12</b></td><td><b style="font-size:16px">{w.get("ticker","")}</b><br><span style="font-size:11px">{w.get("reason","")[:22]}</span></td><td><b style="color:#15803d;font-size:15px">${sp:.2f}</b><br><span style="font-size:11px">RSI {float(w.get("rsi",50)):.0f}</span></td><td><b style="font-size:16px">{int(w.get("strike",0))}</b></td><td>{dist:+.1f}% Δ{dlt:.2f}</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td><b>${opt_p:.2f}</b><br>{vol/1000:.0f}K</td><td><b>${prem:.1f}M</b></td><td>{"✅ قوي" if ok>=10 else "👍 جيد" if ok>=8 else "متوسط"}</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد - اضغط فحص قوي")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ فحص {len(tickers)}..."):
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

st.caption(f"V38.1 | {ksa_str} | إصلاح KeyError انفجار + 12/6 = تاريخ 6/12 وليس عدد شركات | جدول 14px")
