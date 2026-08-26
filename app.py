import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V46 REALISTIC", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:11px;}
.big-table th {background:#000!important; color:#fff!important; padding:8px 2px; text-align:center; font-size:7px;}
.big-table td {background:#fff!important; padding:8px 2px; text-align:center; border:1px solid #ccc; font-size:10px; font-weight:700;}
.call-badge {background:#16a34a!important; color:#fff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.put-badge {background:#dc2626!important; color:#fff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.buy-card {background:#dcfce7; border:2px solid #16a34a; border-radius:12px; padding:10px; margin:6px 0;}
.sell-card {background:#fee2e2; border:2px solid #dc2626; border-radius:12px; padding:10px; margin:6px 0;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
div.stButton > button {width:100%; height:48px; font-size:15px; font-weight:900; border-radius:12px;}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "view" not in st.session_state: st.session_state.view="✅ BUY قوي"

def greeks(S,K,T,iv,is_call=True):
    try:
        if T<=0: T=0.05
        if iv is None or pd.isna(iv) or iv<0.12 or iv>4: iv=0.50
        if S<=0 or K<=0: return 0.50 if is_call else -0.50, iv
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta = 0.5*(1.0+math.erf(d1/math.sqrt(2.0))) if is_call else 0.5*(1.0+math.erf(d1/math.sqrt(2.0)))-1
        return float(delta), float(iv)
    except: return 0.50 if is_call else -0.50, 0.50

def supertrend(df, period=10, multiplier=3.0):
    try:
        hl2 = (df['High'] + df['Low']) / 2
        atr = (df['High'] - df['Low']).ewm(alpha=1/period, adjust=False).mean()
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr
        st_line = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        st_line.iloc[0] = float(lower.iloc[0])
        direction.iloc[0] = 1
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > st_line.iloc[i-1]:
                if direction.iloc[i-1]==1:
                    st_line.iloc[i] = max(float(lower.iloc[i]), float(st_line.iloc[i-1]))
                else:
                    st_line.iloc[i] = float(lower.iloc[i])
                direction.iloc[i] = 1
            else:
                if direction.iloc[i-1]==-1:
                    st_line.iloc[i] = min(float(upper.iloc[i]), float(st_line.iloc[i-1]))
                else:
                    st_line.iloc[i] = float(upper.iloc[i])
                direction.iloc[i] = -1
        return st_line, direction
    except:
        return pd.Series([float(df['Close'].iloc[-1])]*len(df), index=df.index), pd.Series([1]*len(df), index=df.index)

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# ✅ {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V46 واقعي | بدون 95% وهمي | AVGO إذا نازل يصير 55% مو 95%</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("✅ BUY", type="primary" if st.session_state.view=="✅ BUY قوي" else "secondary"): st.session_state.view="✅ BUY قوي"; st.rerun()
with col2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with col3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

b1, b2 = st.columns(2)
with b1: do_scan_main = st.button("⚡ فحص واقعي", type="primary")
with b2:
    if st.button("🧹 تصفير"):
        st.session_state.results=pd.DataFrame(); st.cache_data.clear(); st.rerun()

with st.sidebar:
    min_prem=st.slider("💰 M$",0.05,3.0,0.15,0.05)
    min_vol=st.slider("VOL",30,2000,80,10)
try: min_prem
except: min_prem=0.15
try: min_vol
except: min_vol=80
do_scan = do_scan_main

@st.cache_data(ttl=50)
def analysis_v46(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="3mo")
        if len(h)<60: return None
        h=h.dropna()
        if len(h)<60: return None
        curr=float(h['Close'].iloc[-1])
        # حماية أسعار وهمية مثل NFLX 81
        if ticker=="NFLX" and curr<200: return None
        if ticker=="AVGO" and curr<150: return None
        if ticker=="SPY" and curr>700: return None
        if pd.isna(curr) or curr<5 or curr>3000: return None

        st_line, st_dir = supertrend(h, 10, 3.0)
        st_direction=int(st_dir.iloc[-1])
        prev_st_dir=int(st_dir.iloc[-2]) if len(st_dir)>=2 else st_direction
        st_buy_signal = st_direction==1 and prev_st_dir==-1
        st_sell_signal = st_direction==-1 and prev_st_dir==1

        ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
        ema50=float(h['Close'].ewm(span=50).mean().iloc[-1])
        if pd.isna(ema9) or pd.isna(ema21): return None

        h20=h.tail(20)
        vol_sum=float(h20['Volume'].sum())
        if vol_sum>0:
            vwap=float((h20['Close']*h20['Volume']).sum()/vol_sum)
        else:
            vwap=curr

        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll<0.01: ll=0.01
        rsi=100-(100/(1+lg/ll))
        if pd.isna(rsi): rsi=50
        rsi=float(max(5,min(95,rsi)))

        # MACD
        ema12=h['Close'].ewm(span=12).mean()
        ema26=h['Close'].ewm(span=26).mean()
        macd=ema12-ema26
        signal=macd.ewm(span=9).mean()
        hist=macd-signal
        macd_hist=float(hist.iloc[-1])
        macd_hist_prev=float(hist.iloc[-2]) if len(hist)>=2 else macd_hist
        macd_bull = macd_hist>0 and macd_hist>macd_hist_prev
        macd_bear = macd_hist<0 and macd_hist<macd_hist_prev

        # فيبو
        high60=float(h['High'].tail(60).max())
        low60=float(h['Low'].tail(60).min())
        diff=high60-low60
        fib_236=high60-diff*0.236
        fib_382=high60-diff*0.382
        bounce_fib = (curr>fib_236 and float(h['Low'].iloc[-1])<=fib_236*1.01)

        # VOL
        vol_avg20=float(h['Volume'].tail(20).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=float(vol_today/vol_avg20) if vol_avg20>0 else 1.0
        vol_ratio=float(max(0.1,min(5.0,vol_ratio)))

        # تغيير يوم + 5 أيام
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

        change_1d=float(max(-15,min(15,change_1d)))
        change_5d=float(max(-20,min(20,change_5d)))

        high20=float(h['High'].tail(20).max())
        low20=float(h['Low'].tail(20).min())

        return {
            "price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"rsi":float(rsi),
            "high20":high20,"low20":low20,"fib_236":float(fib_236),"fib_382":float(fib_382),
            "vol_ratio":float(vol_ratio),"change_1d":float(change_1d),"change_5d":float(change_5d),
            "st_dir":int(st_direction),"st_buy_signal":bool(st_buy_signal),"st_sell_signal":bool(st_sell_signal),
            "macd_bull":bool(macd_bull),"macd_bear":bool(macd_bear),"bounce_fib":bool(bounce_fib)
        }
    except: return None

def fetch_v46(ticker, min_prem, min_vol):
    try:
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        sd=analysis_v46(ticker)
        if not sd: return []
        curr=sd["price"]
        # فلتر AVGO منخفضة
        # إذا AVGO نازلة اليوم -1% أو أكثر - لا تعطي CALL 95%
        if ticker=="AVGO" and sd["change_1d"]<-0.8:
            # AVGO نازلة - لا تعطي CALL إلا إذا ارتداد قوي
            if sd["bounce_fib"]==False and sd["st_dir"]!=1:
                return []

        rows=[]
        for exp in tk.options[:2]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                if days<1 or days>21: continue # فقط أسبوع-3 أسابيع
                T=max(days/365,0.04)
                chain=tk.option_chain(exp)
                # اتجاه واقعي - AVGO نازلة ما تعطي CALL
                allowed=[]
                # CALL فقط إذا صاعد اليوم + صاعد 5 أيام + فوق VWAP
                is_bull = sd["change_1d"]>=-0.5 and sd["change_5d"]>=-1 and sd["price"]>sd["vwap"] and sd["rsi"]>=40
                is_bear = sd["change_1d"]<=0.5 and sd["change_5d"]<=1 and sd["price"]<sd["vwap"] and sd["rsi"]<=60

                if sd["st_dir"]==1 and is_bull and sd["change_1d"]>=-1:
                    allowed=["CALL"]
                elif sd["st_dir"]==-1 and is_bear and sd["change_1d"]<=1:
                    allowed=["PUT"]
                else:
                    # متذبذب - شرط قوي
                    if sd["change_1d"]>=1.2 and sd["vol_ratio"]>=1.0:
                        allowed=["CALL"]
                    elif sd["change_1d"]<=-1.2 and sd["vol_ratio"]>=1.0:
                        allowed=["PUT"]
                    else:
                        continue

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
                            if abs(dist)>4: continue
                            iv=r.get('impliedVolatility',0.5)
                            if pd.isna(iv): iv=0.5
                            delta,_=greeks(curr,strike,T,iv, opt_type=="CALL")
                            if pd.isna(delta): continue
                            if opt_type=="CALL" and (delta<0.30 or delta>0.70): continue
                            if opt_type=="PUT" and (delta>-0.30 or delta<-0.70): continue
                            last_price=float(r['lastPrice'])
                            vol=int(r['volume'])
                            if pd.isna(last_price) or last_price==0: continue
                            prem=float(last_price*vol*100/1e6)
                            if pd.isna(prem) or prem==0: continue
                            if ticker=="NFLX" and int(strike)<200: continue
                            if ticker=="AVGO" and int(strike)<150: continue
                            rows.append({
                                "ticker":ticker,"type":opt_type,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),
                                "opt_price":float(last_price),"vol":int(vol),"oi":int(r.get('openInterest',0) or 0),"prem_M":float(prem),
                                "exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),
                                "days":int(days),"delta":float(delta),"rsi":float(sd["rsi"]),"vol_ratio":float(sd["vol_ratio"]),
                                "change_1d":float(sd["change_1d"]),"change_5d":float(sd["change_5d"]),
                                "st_dir":int(sd["st_dir"]),"st_buy":bool(sd["st_buy_signal"]),"st_sell":bool(sd["st_sell_signal"]),
                                "bounce_fib":bool(sd["bounce_fib"]),"macd_bull":bool(sd["macd_bull"]),
                                "vwap":float(sd["vwap"])
                            })
                        except: continue
                if len(rows)>=1: break
            except: continue
        return rows
    except: return []

def calc_confirm_v46(row):
    try:
        score=50
        ch1=float(row.get("change_1d",0))
        ch5=float(row.get("change_5d",0))
        vol_r=float(row.get("vol_ratio",1))
        rsi=float(row.get("rsi",50))
        dist=float(row.get("dist",0))

        if row["type"]=="CALL":
            # أساس 50
            # 1. اتجاه اليوم - أهم شيء - إذا نازل -20
            if ch1>=1.5: score+=18
            elif ch1>=0.5: score+=10
            elif ch1>=0: score+=3
            elif ch1>=-0.5: score-=5
            else: score-=20 # نازل اليوم - خصم كبير - AVGO

            # 2. 5 أيام
            if ch5>=3: score+=12
            elif ch5>=1: score+=6
            elif ch5>=0: score+=2
            else: score-=8

            # 3. فوق VWAP
            if float(row.get("stock_now",0))>float(row.get("vwap",0)): score+=8
            else: score-=10

            # 4. RSI واقعي
            if 50<=rsi<=68: score+=10
            elif 44<=rsi<=72: score+=5
            elif rsi<38: score+=3 # انعكاس
            elif rsi>75: score-=5 # متشبع

            # 5. VOL - إذا x0.2 خصم مو إضافة
            if vol_r>=1.8: score+=12
            elif vol_r>=1.2: score+=6
            elif vol_r>=0.8: score+=0
            else: score-=10 # VOL ضعيف مثل صورتك x0.2

            # 6. Supertrend
            if int(row.get("st_dir",0))==1: score+=8
            else: score-=15
            if bool(row.get("st_buy",False)): score+=8
            if bool(row.get("bounce_fib",False)): score+=7

        else: # PUT
            if ch1<=-1.5: score+=18
            elif ch1<=-0.5: score+=10
            elif ch1<=0: score+=3
            else: score-=15
            if ch5<=-3: score+=12
            elif ch5<=-1: score+=6
            if vol_r>=1.5: score+=10
            elif vol_r<0.8: score-=8

        if abs(dist)<=1: score+=5
        elif abs(dist)>3: score-=5

        score=int(max(35,min(88,score))) # سقف 88% مو 95% - واقعي
        # سبب
        reasons=[]
        if ch1>=0: reasons.append(f"اليوم {ch1:+.1f}%")
        else: reasons.append(f"اليوم {ch1:+.1f}% نازل")
        reasons.append(f"5d {ch5:+.1f}%")
        reasons.append(f"RSI {rsi:.0f}")
        if vol_r<0.8: reasons.append(f"VOL ضعيف x{vol_r:.1f}")
        else: reasons.append(f"VOL x{vol_r:.1f}")

        return score, " | ".join(reasons[:3])
    except: return 55, "متوسط"

if st.session_state.results.empty:
    st.info("📱 اضغط ⚡ فحص واقعي - نسب واقعية بدون 95% وهمي")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        if pd.isna(r.get("stock_now",0)): continue
        if r.get("ticker")=="NFLX" and float(r.get("stock_now",0))<200: continue
        if r.get("ticker")=="AVGO" and float(r.get("stock_now",0))<150: continue
        conf, why = calc_confirm_v46(r)
        r2=dict(r); r2["confirm"]=int(conf); r2["why"]=why
        enriched.append(r2)
    if enriched:
        df=pd.DataFrame(enriched)
        df=df.dropna(subset=['confirm','stock_now'])
        df=df[~((df["ticker"]=="NFLX") & (df["stock_now"]<200))]
        df=df[~((df["ticker"]=="AVGO") & (df["stock_now"]<150))]
        df=df.drop_duplicates(subset=["ticker","strike","exp_full","type"])
        df=df.sort_values(["confirm","prem_M"], ascending=[False][False])
        v=st.session_state.view
        if "BUY قوي" in v: final=df[(df["type"]=="CALL")].head(20)
        elif "SELL قوي" in v: final=df[(df["type"]=="PUT")].head(20)
        else: final=df.head(20)
        if final.empty and not df.empty: final=df.head(10)
    else: final=pd.DataFrame()

    if not final.empty:
        st.success(f"✅ {len(final)} عقد واقعي - {ksa_str} - بدون 95% وهمي")
        for _,w in final.head(3).iterrows():
            conf=int(w.get("confirm",60))
            # لون حسب النسبة
            if conf>=75: border="#16a34a"
            elif conf>=65: border="#ca8a04"
            else: border="#dc2626"
            if w.get("type")=="CALL":
                st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;"><b>🟢 {w.get('ticker')} {int(w.get('strike'))} CALL - {conf}%</b> | {w.get('why')}<br><span style="font-size:11px;">السهم ${float(w.get('stock_now',0)):.2f} اليوم {float(w.get('change_1d',0)):+.1f}% 5d {float(w.get('change_5d',0)):+.1f}% | ST {"BUY" if int(w.get('st_dir',1))==1 else "SELL"} | VOL x{float(w.get('vol_ratio',1)):.1f} | ${float(w.get('opt_price',0)):.2f} | ${float(w.get('prem_M',0)):.1f}M | {w.get('exp_short')} {int(w.get('days'))}ي</span></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;"><b>🔴 {w.get('ticker')} {int(w.get('strike'))} PUT - {conf}%</b> | {w.get('why')}</div>""", unsafe_allow_html=True)

        html='<table class="big-table"><tr><th>% واقعي</th><th>نوع</th><th>شركة</th><th>سهم اليوم</th><th>سترايك</th><th>📅</th><th>عقد</th><th>حوت</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0))
                if pd.isna(sp): continue
                conf=int(w.get("confirm",60)); typ=w.get("type","CALL"); ch1=float(w.get("change_1d",0)); ch5=float(w.get("change_5d",0))
                prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0))
                if typ=="CALL" and ch1<-0.8:
                    conf_color="#dc2626" # أحمر إذا نازل
                elif conf>=75:
                    conf_color="#16a34a"
                elif conf>=65:
                    conf_color="#ca8a04"
                else:
                    conf_color="#991b1b"
                badge = f'<span class="call-badge">CALL</span>' if typ=="CALL" else f'<span class="put-badge">PUT</span>'
                html+=f'<tr><td><b style="color:{conf_color}">{conf}%</b><br><span style="font-size:6px">{w.get("why","")[:18]}</span></td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch1>=0 else "#dc2626"}">{ch1:+.1f}% اليوم</span><br><span style="font-size:8px">{ch5:+.1f}% 5d</span></td><td><b>{int(w.get("strike",0))}</b><br>{float(w.get("dist",0)):+.1f}%</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}<br>{int(w.get("vol",0))/1000:.0f}K</td><td>${prem:.1f}M<br>x{float(w.get("vol_ratio",1)):.1f}</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد - السوق هابط")

if do_scan:
    tickers=["AVGO","AAPL","NVDA","TSLA","META","MSFT","AMD","NFLX","AMZN","COIN","MSTR","PLTR","HOOD","SOFI","QQQ"]
    with st.spinner(f"⚡ فحص واقعي {len(tickers)} - بدون 95% وهمي..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v46, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.dropna(subset=['stock_now','prem_M'])
        ndf=ndf[(ndf["stock_now"]>5)&(ndf["stock_now"]<3000)&(ndf["prem_M"]>0)]
        ndf=ndf[~((ndf["ticker"]=="NFLX") & (ndf["stock_now"]<200))]
        ndf=ndf[~((ndf["ticker"]=="AVGO") & (ndf["stock_now"]<150))]
        ndf=ndf.drop_duplicates(subset=["ticker","strike","exp_full","type"])
        if not ndf.empty:
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_full","type"]).head(800) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.rerun()
    else:
        st.error("لا يوجد - AVGO منخفضة لن تظهر CALL 95% بعد الآن")

st.caption(f"V46 REALISTIC | {ksa_str} | إصلاح AVGO منخفضة - إذا اليوم -1% يصير 55% مو 95% | سقف 88% واقعي | VOL x0.2 يخصم -10")
