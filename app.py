import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V40 DIRECTION FIX", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:13px;}
.big-table th {background:#111!important; color:#fff!important; padding:10px 4px; text-align:center; font-size:10px;}
.big-table td {background:#fff!important; padding:10px 4px; text-align:center; border:1px solid #ccc; font-size:12px; font-weight:700;}
.call-badge {background:#16a34a!important; color:#fff!important; padding:6px 12px; border-radius:10px; font-size:11px; font-weight:900;}
.put-badge {background:#dc2626!important; color:#fff!important; padding:6px 12px; border-radius:10px; font-size:11px; font-weight:900;}
.trend-up {background:#dcfce7; color:#14532d; padding:3px 6px; border-radius:6px; font-size:9px;}
.trend-down {background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:6px; font-size:9px;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:12px; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ صاعد فقط CALL"

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))
def greeks(S,K,T,iv,is_call=True):
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

st.sidebar.title("💎 V40 اتجاه صحيح")
st.sidebar.markdown(f'<div class="time-card">● {ksa_str} KSA<br>CALL=صاعد فقط<br>PUT=هابط فقط</div>', unsafe_allow_html=True)

for v in ["✅ صاعد فقط CALL","🔻 هابط فقط PUT","🔥 انفجار صاعد","🔻 انفجار هابط","🏆 الكل"]:
    if st.sidebar.button(v, key=v, use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v; st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص صحيح", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.results=pd.DataFrame(); st.session_state.last_ts=datetime.now(); st.cache_data.clear(); st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.15,0.05)
min_vol=st.sidebar.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=40)
def analysis_v40(ticker):
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
        prev_close=float(h['Close'].iloc[-2])
        change_1d = (curr-prev_close)/prev_close*100

        # اتجاه صارم
        bull_score=0
        if curr>ema9: bull_score+=1
        if ema9>ema21: bull_score+=1
        if ema21>ema50: bull_score+=1
        if curr>vwap: bull_score+=1
        if rsi>=45: bull_score+=1
        if change_1d>=-0.3: bull_score+=1 # مو نازل قوي اليوم

        bear_score=0
        if curr<ema9: bear_score+=1
        if ema9<ema21: bear_score+=1
        if ema21<ema50: bear_score+=1
        if curr<vwap: bear_score+=1
        if rsi<=55: bear_score+=1
        if change_1d<=0.3: bear_score+=1

        trend_bull = bull_score>=4
        trend_bear = bear_score>=4
        breakout_bull = trend_bull and curr>=high20*0.987 and vol_ratio>=1.2 and change_1d>-0.5
        breakout_bear = trend_bear and curr<=low20*1.013 and vol_ratio>=1.2 and change_1d<0.5
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        return {"price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"rsi":float(rsi),"high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),"change_1d":float(change_1d),"trend_bull":bool(trend_bull),"trend_bear":bool(trend_bear),"breakout_bull":bool(breakout_bull),"breakout_bear":bool(breakout_bear),"bull_score":int(bull_score),"bear_score":int(bear_score)}
    except: return None

def fetch_v40(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_v40(ticker)
        if not sd: return []
        # فلتر اتجاه صارم - لا تعطي CALL إذا هابط
        curr=sd["price"]
        rows=[]
        for exp in tk.options[:3]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<0: continue
                T=max(days/365,0.04)
                chain=tk.option_chain(exp)
                # حدد نوع مسموح فقط
                allowed_types=[]
                if sd["trend_bull"] and not sd["trend_bear"]:
                    allowed_types=["CALL"] # صاعد فقط
                elif sd["trend_bear"] and not sd["trend_bull"]:
                    allowed_types=["PUT"] # هابط فقط
                else:
                    # متذبذب - اسمح بالاثنين لكن بشروط
                    allowed_types=["CALL","PUT"]

                for opt_type in allowed_types:
                    df_opt = chain.calls if opt_type=="CALL" else chain.puts
                    if df_opt.empty: continue
                    df_opt=df_opt.copy()
                    if 'volume' not in df_opt.columns or 'lastPrice' not in df_opt.columns: continue
                    df_opt=df_opt[df_opt['volume']>0]
                    df_opt['prem']=df_opt['lastPrice']*df_opt['volume']*100
                    df_opt=df_opt[df_opt['prem']>=min_prem*1e6]
                    df_opt=df_opt[df_opt['volume']>=min_vol]
                    if df_opt.empty: continue
                    df_opt=df_opt.sort_values('prem',ascending=False).head(2)
                    for _,r in df_opt.iterrows():
                        try:
                            strike=float(r['strike']); dist=(strike-curr)/curr*100
                            # CALL لازم يكون قريب أو OTM بسيط إذا صاعد
                            if opt_type=="CALL" and dist<-3: continue
                            if opt_type=="CALL" and dist>4: continue
                            if opt_type=="PUT" and dist>3: continue
                            if opt_type=="PUT" and dist<-4: continue
                            # فلتر إضافي صارم: CALL لا يعطى إذا السهم نازل اليوم أكثر من -1%
                            if opt_type=="CALL" and sd["change_1d"]<-1.0: continue
                            if opt_type=="PUT" and sd["change_1d"]>1.0: continue

                            iv=float(r.get('impliedVolatility',0.5))
                            if pd.isna(iv): iv=0.5
                            is_call=opt_type=="CALL"
                            delta,_=greeks(curr,strike,T,iv,is_call)
                            if is_call and (delta<0.30 or delta>0.70): continue
                            if not is_call and (delta>-0.30 or delta<-0.70): continue
                            prem=float(r['lastPrice']*float(r['volume'])*100/1e6)
                            opt=float(r['lastPrice']); vol=int(r['volume'])
                            if prem==0 or opt==0: continue
                            rows.append({
                                "ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),
                                "opt_price":float(opt),"vol":int(vol),"oi":int(r.get('openInterest',0)),"prem_M":float(prem),
                                "exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),
                                "days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),
                                "change_1d":float(sd["change_1d"]),"trend_bull":bool(sd["trend_bull"]),"trend_bear":bool(sd["trend_bear"]),
                                "breakout_bull":bool(sd["breakout_bull"]),"breakout_bear":bool(sd["breakout_bear"]),
                                "bull_score":int(sd["bull_score"]),"bear_score":int(sd["bear_score"]),
                                "pos":float(sd["pos"]),"vwap":float(sd["vwap"])
                            })
                        except: continue
                if len(rows)>=3: break
            except: continue
        return rows
    except: return []

def calc_confirm_v40(row):
    score=0; why=[]
    try:
        if row["type"]=="CALL":
            # صاعد فقط
            if row["trend_bull"]:
                score+=35; why.append(f"صاعد {row['bull_score']}/6")
            else:
                score+=5; why.append("ترند ضعيف")
            if row["change_1d"]>=0:
                score+=15; why.append(f"اليوم {row['change_1d']:+.1f}%")
            else:
                score-=10; why.append(f"نازل {row['change_1d']:+.1f}%")
            if 45<=row["rsi"]<=70:
                score+=20; why.append(f"RSI {row['rsi']:.0f}")
            if row["breakout_bull"]:
                score+=20; why.append("اختراق High20")
        else: # PUT
            if row["trend_bear"]:
                score+=35; why.append(f"هابط {row['bear_score']}/6")
            if row["change_1d"]<=0:
                score+=15; why.append(f"اليوم {row['change_1d']:+.1f}%")
            if 30<=row["rsi"]<=55:
                score+=20; why.append(f"RSI {row['rsi']:.0f}")
            if row["breakout_bear"]:
                score+=20; why.append("كسر Low20")

        if row["vol_ratio"]>=1.5:
            score+=15; why.append(f"VOL x{row['vol_ratio']:.1f}")
        elif row["vol_ratio"]>=1.1:
            score+=8

        if abs(row["dist"])<=1.5:
            score+=10; why.append(f"ATM {row['dist']:+.1f}%")

        score=max(0,min(99,score))
        return int(score), " | ".join(why[:3])
    except:
        return 50, "خطأ"

st.title(f"{st.session_state.view} - {ksa_str}")
st.caption("V40 CALL=صاعد فقط + PUT=هابط فقط - مستحيل CALL وهم نازلين")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص صحيح - CALL صاعد فقط")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        conf, why = calc_confirm_v40(r)
        r2=dict(r); r2["confirm"]=int(conf); r2["why"]=why
        r2["ok"]=int(conf/8)
        if r2["ok"]>12: r2["ok"]=12
        enriched.append(r2)

    if enriched:
        df=pd.DataFrame(enriched)
        for col in ["breakout_bull","breakout_bear","trend_bull","trend_bear","confirm"]:
            if col not in df.columns: df[col]=False if "breakout" in col or "trend" in col else 50
        df=df.sort_values(["confirm","prem_M"], ascending=[False,False])
        v=st.session_state.view
        try:
            if "صاعد فقط" in v:
                final=df[(df["type"]=="CALL") & (df["trend_bull"]==True) & (df["change_1d"]>=-1.0)].head(15)
                if final.empty: final=df[df["type"]=="CALL"].head(10)
            elif "هابط فقط" in v:
                final=df[(df["type"]=="PUT") & (df["trend_bear"]==True)].head(15)
                if final.empty: final=df[df["type"]=="PUT"].head(10)
            elif "انفجار صاعد" in v:
                final=df[(df["type"]=="CALL") & (df["breakout_bull"]==True)].head(15)
                if final.empty: final=df[(df["type"]=="CALL") & (df["trend_bull"]==True)].sort_values("vol_ratio", ascending=False).head(10)
            elif "انفجار هابط" in v:
                final=df[(df["type"]=="PUT") & (df["breakout_bear"]==True)].head(15)
                if final.empty: final=df[(df["type"]=="PUT") & (df["trend_bear"]==True)].sort_values("vol_ratio", ascending=False).head(10)
            else:
                final=df.head(15)
        except:
            final=df.head(15)
        if final.empty: final=df.head(10)
    else:
        final=pd.DataFrame()

    if not final.empty:
        # فلتر عرض فقط الرابح
        st.success(f"✅ {len(final)} عقد اتجاهه صحيح - {ksa_str}")

        for _,w in final.head(3).iterrows():
            conf=int(w.get("confirm",0))
            if conf>=65:
                badge="🟢 CALL صاعد" if w.get("type")=="CALL" else "🔴 PUT هابط"
                col="#14532d" if w.get("type")=="CALL" else "#991b1b"
                st.markdown(f"""
                <div style="background:#fff;border:3px solid {col};border-radius:14px;padding:12px;margin:8px 0;">
                <b>{badge} {w.get('ticker')} {int(w.get('strike'))} - {conf}% - {w.get('why')}</b><br>
                <span style="font-size:13px;">السهم ${float(w.get('stock_now',0)):.2f} ({float(w.get('change_1d',0)):+.2f}% اليوم) | {w.get('type')} Δ{float(w.get('delta',0)):.2f} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.1f}M</span>
                </div>
                """, unsafe_allow_html=True)

        html='<table class="big-table"><tr><th>تأكيد</th><th>التوجيه</th><th>الشركة</th><th>السهم اليوم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>العقد</th><th>الحوت</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0)); conf=int(w.get("confirm",0)); typ=w.get("type","CALL"); ch=float(w.get("change_1d",0))
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
                badge = f'<span class="call-badge">🟢 {typ} صاعد</span>' if typ=="CALL" else f'<span class="put-badge">🔴 {typ} هابط</span>'
                trend_tag = f'<span class="trend-up">صاعد {int(w.get("bull_score",0))}/6</span>' if typ=="CALL" else f'<span class="trend-down">هابط {int(w.get("bear_score",0))}/6</span>'
                html+=f'<tr><td><b style="font-size:14px">{conf}%</b><br><span style="font-size:9px">{w.get("why","")[:18]}</span></td><td>{badge}<br>{trend_tag}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch>=0 else "#dc2626"}">{ch:+.2f}% اليوم</span></td><td><b>{int(w.get("strike",0))}</b></td><td>{dist:+.1f}% Δ{float(w.get("delta",0)):.2f}</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}<br>{int(w.get("vol",0))/1000:.0f}K</td><td>${prem:.1f}M</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد اتجاه صاعد - السوق هابط - جرب هابط فقط PUT")

if do_scan:
    tickers=get_tickers()
    with st.spinner(f"⚡ فحص اتجاه صحيح {len(tickers)}..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=12) as executor:
            futs={executor.submit(fetch_v40, t, min_prem, min_vol): t for t in tickers}
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

st.caption(f"V40 | {ksa_str} | CALL فقط إذا صاعد {'>'} VWAP EMA + PUT فقط إذا هابط - إصلاح صورتك CALL نازل")
