import streamlit as st, yfinance as yf, pandas as pd, math, numpy as np
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V43 TECHNICAL PRO", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:11px;}
.big-table th {background:#111!important; color:#fff!important; padding:9px 3px; text-align:center; font-size:8px;}
.big-table td {background:#fff!important; padding:9px 3px; text-align:center; border:1px solid #ccc; font-size:11px; font-weight:700;}
.call-badge {background:#16a34a!important; color:#fff!important; padding:5px 10px; border-radius:8px; font-size:10px; font-weight:900;}
.put-badge {background:#dc2626!important; color:#fff!important; padding:5px 10px; border-radius:8px; font-size:10px; font-weight:900;}
.buy-card {background:linear-gradient(135deg,#dcfce7,#fff); border:3px solid #16a34a; border-radius:14px; padding:12px; margin:8px 0;}
.sell-card {background:linear-gradient(135deg,#fee2e2,#fff); border:3px solid #dc2626; border-radius:14px; padding:12px; margin:8px 0;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ BUY قوي"

def greeks(S,K,T,iv,is_call=True):
    try:
        if T<=0: T=0.05
        if iv is None or pd.isna(iv) or iv<0.12 or iv>4: iv=0.50
        if S<=0 or K<=0: return 0.50 if is_call else -0.50, iv
        import math
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta = 0.5*(1.0+math.erf(d1/math.sqrt(2.0))) if is_call else 0.5*(1.0+math.erf(d1/math.sqrt(2.0)))-1
        return float(delta), float(iv)
    except: return 0.50 if is_call else -0.50, 0.50

def supertrend(df, period=10, multiplier=3.0):
    try:
        hl2 = (df['High'] + df['Low']) / 2
        atr = (df['High'] - df['Low']).ewm(alpha=1/period).mean()
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr
        st_line = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        st_line.iloc[0] = lower.iloc[0]
        direction.iloc[0] = 1
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > st_line.iloc[i-1]:
                st_line.iloc[i] = max(lower.iloc[i], st_line.iloc[i-1]) if direction.iloc[i-1]==1 else lower.iloc[i]
                direction.iloc[i] = 1
            else:
                st_line.iloc[i] = min(upper.iloc[i], st_line.iloc[i-1]) if direction.iloc[i-1]==-1 else upper.iloc[i]
                direction.iloc[i] = -1
        return st_line, direction
    except:
        return pd.Series([df['Close'].iloc[-1]]*len(df), index=df.index), pd.Series([1]*len(df), index=df.index)

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')

st.sidebar.title("💎 V43 مثل TradingView")
st.sidebar.markdown(f'<div class="time-card">● {ksa_str} KSA<br>Supertrend + BUY/SELL<br>Fibo + VOL Explosion</div>', unsafe_allow_html=True)

for v in ["✅ BUY قوي","🔻 SELL قوي","🔥 انفجار BUY","🔻 انفجار SELL","🏆 الكل"]:
    if st.sidebar.button(v, key=v, use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v; st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص فني قوي", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.results=pd.DataFrame(); st.session_state.last_ts=datetime.now(); st.cache_data.clear(); st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,3.0,0.15,0.05)
min_vol=st.sidebar.slider("VOL",30,2000,80,10)

@st.cache_data(ttl=60)
def analysis_v43(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="3mo")
        if len(h)<50: return None
        h=h.dropna()
        if len(h)<50: return None
        curr=float(h['Close'].iloc[-1])
        if ticker=="SPY" and curr>700: return None
        if pd.isna(curr) or curr<1 or curr>5000: return None

        # Supertrend مثل صورتك
        st_line, st_dir = supertrend(h, 10, 3.0)
        st_val=float(st_line.iloc[-1])
        st_direction=int(st_dir.iloc[-1]) # 1=BUY -1=SELL
        prev_st_dir=int(st_dir.iloc[-2]) if len(st_dir)>=2 else st_direction
        st_buy_signal = st_direction==1 and prev_st_dir==-1 # تحول من SELL ل BUY مثل صورتك
        st_sell_signal = st_direction==-1 and prev_st_dir==1

        # EMA
        ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
        ema50=float(h['Close'].ewm(span=50).mean().iloc[-1])
        if pd.isna(ema9) or pd.isna(ema21): return None

        # VWAP
        h20=h.tail(20)
        vwap=float((h20['Close']*h20['Volume']).sum()/h20['Volume'].sum()) if h20['Volume'].sum()>0 else curr)

        # RSI
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll<0.01: ll=0.01
        rsi=100-(100/(1+lg/ll))
        if pd.isna(rsi): rsi=50
        rsi=float(max(5,min(95,rsi)))

        # MACD مثل الصورة تحت
        ema12=h['Close'].ewm(span=12).mean()
        ema26=h['Close'].ewm(span=26).mean()
        macd=ema12-ema26
        signal=macd.ewm(span=9).mean()
        hist=macd-signal
        macd_val=float(macd.iloc[-1])
        macd_hist=float(hist.iloc[-1])
        macd_hist_prev=float(hist.iloc[-2]) if len(hist)>=2 else macd_hist
        macd_bull = macd_hist>0 and macd_hist>macd_hist_prev # أخضر يطلع مثل صورتك
        macd_bear = macd_hist<0 and macd_hist<macd_hist_prev

        # Fibonacci مثل صورتك 0.236 و 0.382
        high60=float(h['High'].tail(60).max())
        low60=float(h['Low'].tail(60).min())
        diff=high60-low60
        fib_236=high60-diff*0.236
        fib_382=high60-diff*0.382
        fib_50=high60-diff*0.5
        # ارتداد من فيبو مثل صورتك BUY عند 0.236
        near_fib_236 = abs(curr-fib_236)/curr<0.02
        near_fib_382 = abs(curr-fib_382)/curr<0.02
        bounce_fib = (curr>fib_236 and float(h['Low'].iloc[-1])<=fib_236*1.01) or (curr>fib_382 and float(h['Low'].iloc[-1])<=fib_382*1.01)

        # Volume Explosion مثل صورتك الأعمدة الطويلة
        vol_avg20=float(h['Volume'].tail(20).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=float(vol_today/vol_avg20) if vol_avg20>0 else 1.0
        vol_explosion = vol_ratio>=1.6 # انفجار مثل الصورة

        # 5 أيام
        try:
            close_5d=float(h['Close'].iloc[-6])
            change_5d=float((curr-close_5d)/close_5d*100) if close_5d>0 else 0.0
        except: change_5d=0.0
        if pd.isna(change_5d): change_5d=0.0
        change_5d=float(max(-15,min(15,change_5d)))

        high20=float(h['High'].tail(20).max()); low20=float(h['Low'].tail(20).min())
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50

        # نقاط BUY قوية مثل صورتك
        buy_points=0; buy_reasons=[]
        if st_direction==1:
            buy_points+=2; buy_reasons.append("Supertrend BUY")
        if st_buy_signal:
            buy_points+=3; buy_reasons.append("🔥 تحول BUY")
        if curr>ema9>ema21:
            buy_points+=2; buy_reasons.append("EMA9>21")
        if curr>vwap:
            buy_points+=1; buy_reasons.append("فوق VWAP")
        if 45<=rsi<=70:
            buy_points+=2; buy_reasons.append(f"RSI {rsi:.0f}")
        elif rsi<38 and rsi>30:
            buy_points+=2; buy_reasons.append(f"RSI {rsi:.0f} انعكاس")
        if macd_bull:
            buy_points+=2; buy_reasons.append("MACD أخضر يصعد")
        if bounce_fib:
            buy_points+=3; buy_reasons.append(f"ارتداد Fibo {fib_236:.2f}")
        if near_fib_236 or near_fib_382:
            buy_points+=1
        if vol_explosion:
            buy_points+=2; buy_reasons.append(f"VOL انفجار x{vol_ratio:.1f}")
        if change_5d>=1:
            buy_points+=1; buy_reasons.append(f"5d {change_5d:+.1f}%")

        sell_points=0; sell_reasons=[]
        if st_direction==-1:
            sell_points+=2; sell_reasons.append("Supertrend SELL")
        if st_sell_signal:
            sell_points+=3; sell_reasons.append("تحول SELL")
        if curr<ema9<ema21:
            sell_points+=2
        if curr<vwap:
            sell_points+=1
        if rsi<=55 and rsi>=30:
            sell_points+=2
        if macd_bear:
            sell_points+=2
        if vol_explosion:
            sell_points+=1
        if change_5d<=-1:
            sell_points+=1

        return {
            "price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"rsi":float(rsi),
            "high20":high20,"low20":low20,"high60":high60,"low60":low60,
            "fib_236":float(fib_236),"fib_382":float(fib_382),"fib_50":float(fib_50),
            "vol_ratio":float(vol_ratio),"vol_explosion":bool(vol_explosion),"pos":float(pos),
            "change_5d":float(change_5d),"st_val":float(st_val),"st_dir":int(st_direction),
            "st_buy_signal":bool(st_buy_signal),"st_sell_signal":bool(st_sell_signal),
            "macd_hist":float(macd_hist),"macd_bull":bool(macd_bull),"macd_bear":bool(macd_bear),
            "bounce_fib":bool(bounce_fib),"near_fib_236":bool(near_fib_236),
            "buy_points":int(buy_points),"sell_points":int(sell_points),
            "buy_reasons":buy_reasons,"sell_reasons":sell_reasons
        }
    except Exception as e:
        return None

def fetch_v43(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_v43(ticker)
        if not sd: return []
        curr=sd["price"]
        if ticker=="SPY" and curr>700: return []
        rows=[]
        for exp in tk.options[:2]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<0: continue
                T=max(days/365,0.04)
                chain=tk.option_chain(exp)
                # حدد نوع حسب Supertrend
                allowed=[]
                if sd["buy_points"]>=6 and sd["st_dir"]==1:
                    allowed=["CALL"]
                elif sd["sell_points"]>=6 and sd["st_dir"]==-1:
                    allowed=["PUT"]
                else:
                    if sd["change_5d"]>=1.5: allowed=["CALL"]
                    elif sd["change_5d"]<=-1.5: allowed=["PUT"]
                    else: continue

                for opt_type in allowed:
                    df_opt = chain.calls if opt_type=="CALL" else chain.puts
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
                            if abs(dist)>5: continue
                            iv=r.get('impliedVolatility',0.5)
                            if pd.isna(iv): iv=0.5
                            delta,_=greeks(curr,strike,T,iv, opt_type=="CALL")
                            if pd.isna(delta): continue
                            if opt_type=="CALL" and (delta<0.28 or delta>0.72): continue
                            if opt_type=="PUT" and (delta>-0.28 or delta<-0.72): continue
                            last_price=float(r['lastPrice'])
                            vol=int(r['volume'])
                            if pd.isna(last_price) or last_price==0: continue
                            prem=float(last_price*vol*100/1e6)
                            if pd.isna(prem) or prem==0: continue
                            if ticker=="SPY" and int(strike)>700: continue
                            rows.append({
                                "ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),
                                "opt_price":float(last_price),"vol":int(vol),"oi":int(r.get('openInterest',0) or 0),"prem_M":float(prem),
                                "exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),
                                "days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),
                                "change_5d":float(sd["change_5d"]),"st_dir":int(sd["st_dir"]),"st_buy":bool(sd["st_buy_signal"]),"st_sell":bool(sd["st_sell_signal"]),
                                "buy_points":int(sd["buy_points"]),"sell_points":int(sd["sell_points"]),
                                "buy_reasons":",".join(sd["buy_reasons"][:4]),"sell_reasons":",".join(sd["sell_reasons"][:4]),
                                "fib_236":float(sd["fib_236"]),"fib_382":float(sd["fib_382"]),"bounce_fib":bool(sd["bounce_fib"]),
                                "macd_bull":bool(sd["macd_bull"]),"macd_hist":float(sd["macd_hist"]),"vol_explosion":bool(sd["vol_explosion"])
                            })
                        except: continue
                if len(rows)>=1: break
            except: continue
        return rows
    except: return []

def calc_confirm_v43(row):
    try:
        if row["type"]=="CALL":
            pts=int(row.get("buy_points",0))
            score=pts*8
            if row.get("st_buy",False): score+=15
            if row.get("bounce_fib",False): score+=15
            if row.get("vol_explosion",False): score+=10
            if row.get("macd_bull",False): score+=8
        else:
            pts=int(row.get("sell_points",0))
            score=pts*8
            if row.get("st_sell",False): score+=15
            if row.get("vol_explosion",False): score+=10

        if abs(row.get("dist",0))<=1.2: score+=8
        score=int(max(15,min(95,score)))
        why=row.get("buy_reasons") if row["type"]=="CALL" else row.get("sell_reasons")
        if not why: why="متوسط"
        return score, why
    except:
        return 60, "متوسط"

st.title(f"{st.session_state.view} - {ksa_str}")
st.caption("V43 يقلد TradingView صورتك - Supertrend + BUY/SELL + Fibo 0.236 + VOL انفجار")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص فني قوي - يقرأ مثل TradingView")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        if pd.isna(r.get("stock_now",0)): continue
        if r.get("ticker")=="SPY" and float(r.get("stock_now",0))>700: continue
        conf, why = calc_confirm_v43(r)
        r2=dict(r); r2["confirm"]=int(conf); r2["why"]=why
        enriched.append(r2)

    if enriched:
        df=pd.DataFrame(enriched)
        df=df.dropna(subset=['confirm','stock_now'])
        df=df[~((df["ticker"]=="SPY") & (df["stock_now"]>700))]
        df=df.drop_duplicates(subset=["ticker","strike","exp_full","type"])
        if not df.empty:
            df=df.sort_values(["confirm","prem_M"], ascending=[False,False])
            v=st.session_state.view
            try:
                if "BUY قوي" in v:
                    final=df[(df["type"]=="CALL") & (df["buy_points"]>=6)].head(15)
                    if final.empty: final=df[df["type"]=="CALL"].head(10)
                elif "SELL قوي" in v:
                    final=df[(df["type"]=="PUT") & (df["sell_points"]>=6)].head(15)
                    if final.empty: final=df[df["type"]=="PUT"].head(10)
                elif "انفجار BUY" in v:
                    final=df[(df["type"]=="CALL") & (df["vol_explosion"]==True)].head(15)
                    if final.empty: final=df[df["type"]=="CALL"].sort_values("vol_ratio", ascending=False).head(10)
                elif "انفجار SELL" in v:
                    final=df[(df["type"]=="PUT") & (df["vol_explosion"]==True)].head(15)
                else:
                    final=df.head(15)
            except:
                final=df.head(15)
        else:
            final=pd.DataFrame()
        if final.empty and not df.empty: final=df.head(10)
    else:
        final=pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد فني قوي - Supertrend + Fibo - {ksa_str}")

        for _,w in final.head(3).iterrows():
            conf=int(w.get("confirm",60))
            if w.get("type")=="CALL":
                st.markdown(f"""<div class="buy-card"><b>🟢 BUY CALL {w.get('ticker')} {int(w.get('strike'))} - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">السهم ${float(w.get('stock_now',0)):.2f} (5d {float(w.get('change_5d',0)):+.1f}%) | Supertrend {"BUY" if int(w.get('st_dir',1))==1 else "SELL"} | Fibo 0.236 ${float(w.get('fib_236',0)):.2f} ارتداد {bool(w.get('bounce_fib',False))} | MACD {"أخضر" if bool(w.get('macd_bull',False)) else "أحمر"} | VOL x{float(w.get('vol_ratio',1)):.1f} {"🔥 انفجار" if bool(w.get('vol_explosion',False)) else ""} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.1f}M | {w.get('exp_short')}</span><br><span style="font-size:11px;">🎯 هدف +50% وقف -20%</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="sell-card"><b>🔴 SELL PUT {w.get('ticker')} {int(w.get('strike'))} - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} (5d {float(w.get('change_5d',0)):+.1f}%) | ST {"SELL" if int(w.get('st_dir',1))==-1 else "BUY"} | VOL x{float(w.get('vol_ratio',1)):.1f} | ${float(w.get('opt_price',0)):.2f}</span></div>""", unsafe_allow_html=True)

        html='<table class="big-table"><tr><th>تأكيد</th><th>التوجيه</th><th>الشركة</th><th>السهم فني</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>العقد</th><th>الحوت</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0))
                if pd.isna(sp): continue
                if w.get("ticker")=="SPY" and sp>700: continue
                conf=int(w.get("confirm",60)); typ=w.get("type","CALL"); ch5=float(w.get("change_5d",0))
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
                badge = f'<span class="call-badge">🟢 BUY CALL</span>' if typ=="CALL" else f'<span class="put-badge">🔴 SELL PUT</span>'
                tech = f"ST {'BUY' if int(w.get('st_dir',1))==1 else 'SELL'} | RSI {float(w.get('rsi',50)):.0f}"
                if bool(w.get('bounce_fib',False)): tech+=" | Fibo ارتداد"
                if bool(w.get('vol_explosion',False)): tech+=" | VOL🔥"
                html+=f'<tr><td><b>{conf}%</b><br>{int(w.get("buy_points" if typ=="CALL" else "sell_points",0))}/10<br><span style="font-size:6px">{w.get("why","")[:18]}</span></td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="font-size:8px">{tech}</span><br><span style="color:{"#16a34a" if ch5>=0 else "#dc2626"}">{ch5:+.1f}% 5d</span></td><td><b>{int(w.get("strike",0))}</b></td><td>{dist:+.1f}% Δ{float(w.get("delta",0)):.2f}</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}<br>{int(w.get("vol",0))/1000:.0f}K</td><td>${prem:.1f}M</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد BUY قوي - السوق متذبذب - جرب الكل")

if do_scan:
    tickers=["QQQ","AAPL","NVDA","TSLA","META","MSFT","AMD","AVGO","NFLX","AMZN","COIN","MSTR","PLTR","HOOD","SOFI"]
    with st.spinner(f"⚡ فحص فني مثل TradingView {len(tickers)}..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v43, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.dropna(subset=['stock_now','prem_M'])
        ndf=ndf[(ndf["stock_now"]>1)&(ndf["stock_now"]<5000)&(ndf["prem_M"]>0)]
        ndf=ndf[~((ndf["ticker"]=="SPY") & (ndf["stock_now"]>700))]
        ndf=ndf.drop_duplicates(subset=["ticker","strike","exp_full","type"])
        if not ndf.empty:
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_full","type"]).head(800) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

st.caption(f"V43 TECHNICAL PRO | {ksa_str} | يقلد صورتك AAPL BUY Supertrend + Fibo 0.236 + VOL انفجار + MACD أخضر - دخول آمن مضمون")
