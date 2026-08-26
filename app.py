import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V39 CALL PUT CLEAR", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:14px;}
.big-table th {background:#111!important; color:#fff!important; padding:12px 5px; text-align:center; font-size:11px; font-weight:800;}
.big-table td {background:#fff!important; padding:12px 5px; text-align:center; border:1px solid #ccc; font-size:13px; font-weight:700; color:#000;}
.call-badge {background:#16a34a!important; color:#fff!important; padding:7px 14px; border-radius:10px; font-size:13px; font-weight:900; display:inline-block;}
.put-badge {background:#dc2626!important; color:#fff!important; padding:7px 14px; border-radius:10px; font-size:13px; font-weight:900; display:inline-block;}
.score-high {background:#14532d; color:#fff; padding:8px 14px; border-radius:12px; font-size:16px; font-weight:900;}
.confirm-bar {height:10px; border-radius:5px; background:#e5e7eb; overflow:hidden;}
.confirm-fill {height:100%; background:linear-gradient(90deg,#16a34a,#22c55e);}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:12px; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

def get_tickers(): return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","HOOD","AVGO","NFLX","CRM"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ قوي فقط 75%+"

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))
def greeks(S,K,T,iv, is_call=True):
    try:
        if T<=0: T=0.05
        if iv<0.1 or iv>4: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta = norm_cdf(d1) if is_call else norm_cdf(d1)-1
        return delta, iv
    except: return 0.55 if is_call else -0.45, 0.55

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')
try: delay=(now-st.session_state.last_ts).total_seconds()
except: delay=0
if delay<0 or delay>3600: delay=0

st.sidebar.title("💎 V39 توجيه واضح")
st.sidebar.markdown(f'<div class="time-card">● {ksa_str} KSA<br>تأكيد % + CALL/PUT</div>', unsafe_allow_html=True)

for v in ["✅ قوي فقط 75%+","🔥 انفجار CALL","🔻 انفجار PUT","💎 10+ قوي","🏆 الكل"]:
    if st.sidebar.button(v, key=v, use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v; st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص CALL PUT", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.results=pd.DataFrame(); st.session_state.last_ts=datetime.now(); st.cache_data.clear(); st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.15,0.05)
min_vol=st.sidebar.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=40)
def analysis_v39(ticker):
    try:
        h=yf.Ticker(ticker).history(period="3mo")
        if len(h)<40: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1]); ema21=float(h['Close'].ewm(21).mean().iloc[-1]); ema50=float(h['Close'].ewm(50).mean().iloc[-1])
        h20=h.tail(20); vwap=float((h20['Close']*h20['Volume']).sum()/h20['Volume'].sum()) if h20['Volume'].sum()>0 else curr
        d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
        lg=float(g.iloc[-1]); ll=float(l.iloc[-1])
        if ll==0: ll=0.01
        rsi=100-(100/(1+lg/ll))
        high20=float(h['High'].tail(20).max()); low20=float(h['Low'].tail(20).min())
        vol_avg=float(h['Volume'].tail(20).mean()); vol_ratio=float(h['Volume'].iloc[-1]/vol_avg) if vol_avg>0 else 1
        # نسب تأكيد قوية
        trend_bull = curr>ema9>ema21 and curr>ema50 and curr>vwap
        trend_bear = curr<ema9<ema21 and curr<ema50 and curr<vwap
        breakout_bull = curr>=high20*0.985 and vol_ratio>=1.3
        breakout_bear = curr<=low20*1.015 and vol_ratio>=1.3
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        return {"price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"rsi":float(rsi),"high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),"trend_bull":bool(trend_bull),"trend_bear":bool(trend_bear),"breakout_bull":bool(breakout_bull),"breakout_bear":bool(breakout_bear)}
    except: return None

def fetch_v39(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_v39(ticker)
        if not sd: return []
        curr=sd["price"]
        rows=[]
        for exp in tk.options[:3]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<0: continue
                T=max(days/365,0.04)
                # جيب CALL و PUT
                chain=tk.option_chain(exp)
                for opt_type, df_opt in [("CALL", chain.calls), ("PUT", chain.puts)]:
                    if df_opt.empty: continue
                    df_opt=df_opt.copy()
                    if 'volume' not in df_opt.columns or 'lastPrice' not in df_opt.columns: continue
                    df_opt=df_opt[df_opt['volume']>0]
                    df_opt['prem']=df_opt['lastPrice']*df_opt['volume']*100
                    df_opt=df_opt[df_opt['prem']>=min_prem*1e6]
                    df_opt=df_opt[df_opt['volume']>=min_vol]
                    if df_opt.empty: continue
                    df_opt=df_opt.sort_values('prem',ascending=False).head(3)
                    for _,r in df_opt.iterrows():
                        try:
                            strike=float(r['strike']); dist=(strike-curr)/curr*100
                            if abs(dist)>6: continue
                            iv=float(r.get('impliedVolatility',0.5))
                            if pd.isna(iv): iv=0.5
                            is_call = opt_type=="CALL"
                            delta,_=greeks(curr,strike,T,iv,is_call)
                            # فلتر دلتا قوي
                            if is_call and (delta<0.25 or delta>0.75): continue
                            if not is_call and (delta>-0.25 or delta<-0.75): continue
                            prem=float(r['lastPrice']*float(r['volume'])*100/1e6)
                            opt=float(r['lastPrice']); vol=int(r['volume']); oi=int(r.get('openInterest',0))
                            bid=float(r.get('bid',0)); ask=float(r.get('ask',0))
                            spread=(ask-bid)/opt*100 if opt>0 and bid>0 else 10
                            if prem==0 or opt==0: continue
                            rows.append({
                                "ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),
                                "opt_price":float(opt),"vol":int(vol),"oi":int(oi),"prem_M":float(prem),
                                "exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),
                                "days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),
                                "spread":float(spread),"trend_bull":bool(sd["trend_bull"]),"trend_bear":bool(sd["trend_bear"]),
                                "breakout_bull":bool(sd["breakout_bull"]),"breakout_bear":bool(sd["breakout_bear"]),
                                "pos":float(sd["pos"]),"vwap":float(sd["vwap"]),"high20":float(sd["high20"]),"low20":float(sd["low20"])
                            })
                        except: continue
                if len(rows)>=4: break
            except: continue
        return rows
    except: return []

def calc_confirm(row):
    # حساب نسبة تأكيد 0-100%
    score=0; details=[]
    try:
        # 1. ترند (30%)
        if row["type"]=="CALL" and row["trend_bull"]:
            score+=30; details.append("ترند صاعد 30%")
        elif row["type"]=="PUT" and row["trend_bear"]:
            score+=30; details.append("ترند هابط 30%")
        elif row["type"]=="CALL" and row["pos"]>50:
            score+=15; details.append("فوق المتوسط 15%")
        elif row["type"]=="PUT" and row["pos"]<50:
            score+=15; details.append("تحت المتوسط 15%")

        # 2. انفجار VOL (25%)
        if row["vol_ratio"]>=1.8:
            score+=25; details.append(f"انفجار VOL x{row['vol_ratio']:.1f} 25%")
        elif row["vol_ratio"]>=1.3:
            score+=15; details.append(f"VOL x{row['vol_ratio']:.1f} 15%")
        elif row["vol_ratio"]>=1.0:
            score+=8

        # 3. RSI + موقع (20%)
        if row["type"]=="CALL" and 40<=row["rsi"]<=68:
            score+=20; details.append(f"RSI {row['rsi']:.0f} قوي 20%")
        elif row["type"]=="PUT" and 32<=row["rsi"]<=60:
            score+=20; details.append(f"RSI {row['rsi']:.0f} قوي 20%")
        elif row["rsi"]<38 or row["rsi"]>65:
            score+=15; details.append(f"RSI {row['rsi']:.0f} انعكاس 15%")

        # 4. مسافة + دلتا (15%)
        if abs(row["dist"])<=1.5:
            score+=15; details.append(f"ATM {row['dist']:+.1f}% 15%")
        elif abs(row["dist"])<=3:
            score+=10; details.append(f"{row['dist']:+.1f}% 10%")

        # 5. سيولة (10%)
        if row["spread"]<5 and row["prem_M"]>=1:
            score+=10; details.append(f"سيولة ممتازة {row['spread']:.0f}% 10%")
        elif row["spread"]<8:
            score+=5

        # انفجار إضافي
        if row["type"]=="CALL" and row["breakout_bull"]:
            score+=10; details.append("اختراق High20 +10%")
        if row["type"]=="PUT" and row["breakout_bear"]:
            score+=10; details.append("كسر Low20 +10%")

        score=min(99, score)
        return int(score), " | ".join(details[:4])
    except:
        return 50, "متوسط"

st.title(f"{st.session_state.view} - {ksa_str}")
st.caption("V39 نسب تأكيد قوية + CALL 🟢 / PUT 🔴 واضح - عقد يعتمد عليه")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص CALL PUT")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        conf, why = calc_confirm(r)
        r2=dict(r); r2["confirm"]=int(conf); r2["why"]=why
        # 12/12 قديم نحوله لنسبة
        r2["ok"]=int(conf/8) # 100% = 12/12
        if r2["ok"]>12: r2["ok"]=12
        enriched.append(r2)

    if enriched:
        df=pd.DataFrame(enriched)
        for col in ["breakout_bull","breakout_bear","trend_bull","trend_bear","confirm"]:
            if col not in df.columns: df[col]=False if "breakout" in col or "trend" in col else 50
        df=df.sort_values(["confirm","prem_M"], ascending=[False,False])
        v=st.session_state.view
        try:
            if "قوي" in v and "75%" in v:
                final=df[df["confirm"]>=75].head(12)
                if final.empty: final=df[df["confirm"]>=60].head(12)
            elif "انفجار CALL" in v:
                final=df[(df["type"]=="CALL") & (df["breakout_bull"]==True)].head(12)
                if final.empty: final=df[df["type"]=="CALL"].sort_values("vol_ratio", ascending=False).head(10)
            elif "انفجار PUT" in v:
                final=df[(df["type"]=="PUT") & (df["breakout_bear"]==True)].head(12)
                if final.empty: final=df[df["type"]=="PUT"].sort_values("vol_ratio", ascending=False).head(10)
            elif "10+" in v:
                final=df[df["ok"]>=10].head(12)
            else:
                final=df.head(15)
        except:
            final=df.head(15)
        if final.empty: final=df.head(10)
    else:
        final=pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد - تأكيد قوي - {ksa_str}")

        # كروت قوية بنسبة
        for _,w in final.head(3).iterrows():
            conf=int(w.get("confirm",0))
            if conf>=70:
                color="#14532d" if w.get("type")=="CALL" else "#991b1b"
                badge = "🟢 CALL BUY" if w.get("type")=="CALL" else "🔴 PUT BUY"
                st.markdown(f"""
                <div style="background:#fff;border:3px solid {color};border-radius:16px;padding:14px;margin:10px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                <b style="font-size:17px;">{badge} {w.get('ticker')} {int(w.get('strike'))} - {conf}% تأكيد</b>
                <span style="background:{color};color:#fff;padding:6px 12px;border-radius:10px;font-weight:900;">{conf}%</span>
                </div>
                <div style="margin-top:8px;font-size:13px;color:#000;line-height:1.7;">
                📊 السهم ${float(w.get('stock_now',0)):.2f} | {w.get('type')} {int(w.get('strike'))} ({float(w.get('dist',0)):+.1f}%) Δ{float(w.get('delta',0)):.2f}<br>
                💰 العقد ${float(w.get('opt_price',0)):.2f} | الحوت ${float(w.get('prem_M',0)):.1f}M | VOL {int(w.get('vol',0))/1000:.1f}K | {w.get('exp_short')} ({int(w.get('days'))}ي)<br>
                ✅ <b>لماذا {conf}%:</b> {w.get('why')}<br>
                🎯 هدف +50% وقف -25%
                </div>
                <div style="margin-top:8px;"><div class="confirm-bar"><div class="confirm-fill" style="width:{conf}%"></div></div></div>
                </div>
                """, unsafe_allow_html=True)

        # جدول واضح CALL/PUT + نسبة
        html='<table class="big-table"><tr><th>تأكيد</th><th>التوجيه</th><th>الشركة</th><th>سعر السهم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0)); conf=int(w.get("confirm",0)); typ=w.get("type","CALL")
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0)); dlt=float(w.get("delta",0))
                badge = f'<span class="call-badge">🟢 {typ}</span>' if typ=="CALL" else f'<span class="put-badge">🔴 {typ}</span>'
                if conf>=80: conf_color="#14532d"
                elif conf>=70: conf_color="#16a34a"
                elif conf>=60: conf_color="#ca8a04"
                else: conf_color="#991b1b"
                html+=f'<tr><td><b style="color:{conf_color};font-size:15px">{conf}%</b><br><div class="confirm-bar" style="width:60px"><div class="confirm-fill" style="width:{conf}%"></div></div></td><td>{badge}</td><td><b style="font-size:15px">{w.get("ticker","")}</b><br><span style="font-size:10px">{w.get("why","")[:22]}</span></td><td><b style="color:#15803d">${sp:.2f}</b><br><span style="font-size:10px">RSI {float(w.get("rsi",50)):.0f} x{float(w.get("vol_ratio",1)):.1f}</span></td><td><b style="font-size:15px">{int(w.get("strike",0))}</b></td><td><b>{dist:+.1f}%</b><br>Δ {dlt:.2f}</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td><b>${opt_p:.2f}</b><br>{int(w.get("vol",0))/1000:.0f}K</td><td><b>${prem:.1f}M</b></td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد - جرب الكل")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ فحص CALL/PUT {len(tickers)}..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=12) as executor:
            futs={executor.submit(fetch_v39, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf[(ndf["stock_now"]>1)&(ndf["prem_M"]>0)]
        if not ndf.empty:
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_full","type"]).head(800) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

st.caption(f"V39 | {ksa_str} | نسب تأكيد 75%+ قوية + CALL 🟢 PUT 🔴 واضح - بدون 2/12")
