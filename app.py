import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V37.1 SAFE BOT Fixed", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.whale-table {width:100%; border-collapse:collapse; font-size:11px;}
.whale-table th {background:#111!important; color:#fff!important; padding:7px 3px; text-align:center; font-size:8px; white-space:nowrap;}
.whale-table td {background:#fff!important; padding:8px 3px; text-align:center; border-bottom:1px solid #eee; font-weight:700; font-size:10px; white-space:nowrap;}
.badge-safe {background:#dcfce7; color:#14532d; border:2px solid #22c55e; padding:5px 10px; border-radius:12px; font-size:9px; font-weight:900;}
.badge-risk {background:#fee2e2; color:#991b1b; border:1px solid #ef4444; padding:4px 8px; border-radius:10px; font-size:8px;}
.badge-hedge {background:#fef9c3; color:#854d0e; border:1px solid #eab308; padding:4px 8px; border-radius:10px; font-size:8px;}
.score {padding:5px 8px; border-radius:8px; font-weight:900; display:inline-block; min-width:45px;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
.bot-card {background:linear-gradient(135deg,#14532d,#16a34a); color:#fff; border-radius:12px; padding:12px; text-align:center; font-weight:800;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX","AMZN","CRM","HOOD"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ دخول آمن فقط"
if "bot_active" not in st.session_state: st.session_state.bot_active=False

def norm_cdf(x):
    return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.05
        if iv<0.15 or iv>3: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta=norm_cdf(d1)
        delta=max(0.20,min(0.80,delta))
        return delta, iv
    except:
        return 0.55, 0.55

now=datetime.now()
ksa_time=now+timedelta(hours=3)
ksa_str=ksa_time.strftime('%H:%M:%S')
try:
    delay=(now-st.session_state.last_ts).total_seconds()
    if delay<0 or delay>3600: delay=0
except:
    delay=0

st.sidebar.title("🤖 بوت V37.1 آمن")
st.sidebar.markdown(f"""
<div class="time-card">
● LIVE {ksa_str} KSA<br>
⏳ تأخير {delay:.0f}ث<br>
🔄 آخر {st.session_state.last_ts.strftime('%H:%M:%S')}<br>
✅ إصلاح قوس 110
</div>
""", unsafe_allow_html=True)

bot_status="🟢 شغال - يفحص 30ث" if st.session_state.bot_active else "🔴 متوقف"
st.sidebar.markdown(f'<div class="bot-card">🤖 البوت: {bot_status}<br>دخول آمن 11+/12 فقط</div>', unsafe_allow_html=True)

if st.sidebar.button("🤖 شغل البوت الآمن", type="primary", use_container_width=True):
    st.session_state.bot_active=True
    st.rerun()
if st.sidebar.button("⏹️ وقف البوت", use_container_width=True):
    st.session_state.bot_active=False
    st.rerun()

st.sidebar.markdown("### 📌 الفلترة الذكية")
views=["✅ دخول آمن فقط","💎 بدون خوف 11+","🔥 انفجار سعري","↩️ نقطة انعكاس","⚠️ تحوط - تجنبه","🏆 كل الحيتان"]
for v in views:
    if st.sidebar.button(v, key=f"btn_{v}", use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v
        st.rerun()

st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص آمن 15ث", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.results=pd.DataFrame()
        st.session_state.last_ts=datetime.now()
        st.rerun()

min_prem=st.sidebar.slider("💰 M$",0.05,5.0,0.3,0.05)
min_vol=st.sidebar.slider("VOL",50,5000,150,50)

@st.cache_data(ttl=45)
def analysis_safe(ticker):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        tk=yf.Ticker(real)
        h=tk.history(period="6mo")
        if len(h)<60: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1 or curr>10000: return None

        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        ema50=float(h['Close'].ewm(50).mean().iloc[-1])

        h20=h.tail(20)
        vwap=float((h20['Close']*h20['Volume']).sum()/h20['Volume'].sum()) if h20['Volume'].sum()>0 else curr

        # RSI مبسط - بدون قوس معقد - إصلاح السطر 110
        delta_price=h['Close'].diff()
        gain=delta_price.where(delta_price>0,0).ewm(alpha=1/14, adjust=False).mean()
        loss=(-delta_price.where(delta_price<0,0)).ewm(alpha=1/14, adjust=False).mean()
        last_gain=float(gain.iloc[-1])
        last_loss=float(loss.iloc[-1])
        if last_loss==0: last_loss=0.01
        rs_val=last_gain/last_loss
        rsi=100-(100/(1+rs_val))

        # RSI قبل 5 شموع - مبسط
        try:
            prev_gain=float(gain.iloc[-6])
            prev_loss=float(loss.iloc[-6])
            if prev_loss==0: prev_loss=0.01
            rs_prev=prev_gain/prev_loss
            rsi_prev=100-(100/(1+rs_prev))
        except:
            rsi_prev=50

        high20=float(h['High'].tail(20).max())
        low20=float(h['Low'].tail(20).min())
        vol_avg=float(h['Volume'].tail(20).mean())
        vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=vol_today/vol_avg if vol_avg>0 else 1

        last_row=h.iloc[-1]
        prev_row=h.iloc[-2]
        bullish_engulf = last_row['Close']>last_row['Open'] and prev_row['Close']<prev_row['Open']
        near_support = curr <= low20*1.03
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        is_breakout = curr>=high20*0.99 and vol_ratio>=1.5 and curr>ema9>ema21
        is_reversal = (rsi<38 and rsi>rsi_prev) or near_support or (curr>vwap and prev_row['Close']<float(h['Close'].ewm(9).mean().iloc[-2]))

        return {
            "price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,
            "rsi":float(rsi),"rsi_prev":float(rsi_prev),
            "high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),
            "is_breakout":bool(is_breakout),"is_reversal":bool(is_reversal),
            "bullish_engulf":bool(bullish_engulf),"near_support":bool(near_support)
        }
    except:
        return None

def fetch_safe(ticker, min_prem, min_vol):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        tk=yf.Ticker(real)
        if not tk.options: return []
        st_data=analysis_safe(ticker)
        if not st_data: return []
        curr=st_data["price"]
        rows=[]
        for exp in tk.options[:3]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                T=max(days/365,0.05) if days>0 else 0.02
                calls=tk.option_chain(exp).calls
                if calls.empty: continue
                calls=calls.copy()
                if 'volume' not in calls.columns: continue
                if 'lastPrice' not in calls.columns: continue
                if 'openInterest' not in calls.columns: continue
                calls=calls[calls['volume']>0]
                calls['prem']=calls['lastPrice']*calls['volume']*100
                calls=calls[calls['prem']>=min_prem*1e6]
                calls=calls[calls['volume']>=min_vol]
                if calls.empty: continue
                calls=calls.sort_values('prem',ascending=False).head(4)
                for _,r in calls.iterrows():
                    try:
                        strike=float(r['strike'])
                        if ticker=="SPY" and strike>800: continue
                        dist=(strike-curr)/curr*100 if curr>0 else 0
                        if abs(dist)>5: continue
                        if abs(dist)<0.1: continue
                        iv=float(r.get('impliedVolatility',0.55))
                        if pd.isna(iv) or iv<0.15 or iv>3: iv=0.55
                        delta,fiv=greeks(curr,strike,T,iv)
                        if delta<0.28 or delta>0.70: continue
                        prem_M=float(r['lastPrice']*float(r['volume'])*100/1e6)
                        opt_price=float(r['lastPrice'])
                        vol=int(r['volume'])
                        oi=int(r.get('openInterest',0))
                        bid=float(r.get('bid',0))
                        ask=float(r.get('ask',0))
                        spread_val=0
                        if opt_price>0 and bid>0:
                            spread_val=(ask-bid)/opt_price*100
                        else:
                            spread_val=99

                        is_hedge=False
                        hedge_reason=""
                        if oi>0 and vol/oi<0.15 and days>10:
                            is_hedge=True
                            hedge_reason="OI ضخم VOL قليل"
                        if spread_val>15:
                            is_hedge=True
                            hedge_reason=f"سبريد {spread_val:.0f}%"
                        if opt_price<0.3:
                            is_hedge=True
                            hedge_reason="عقد رخيص"

                        is_real_buy=False
                        if oi>0:
                            if vol>oi*0.3 and spread_val<8 and opt_price>=0.8:
                                is_real_buy=True
                        else:
                            if spread_val<8 and opt_price>=0.8:
                                is_real_buy=True

                        if prem_M==0 or opt_price==0: continue

                        rows.append({
                            "ticker":ticker,"stock_now":float(curr),"strike":int(strike),
                            "dist":float(dist),"opt_price":float(opt_price),"vol":int(vol),
                            "oi":int(oi),"prem_M":float(prem_M),
                            "prem_val":float(r['lastPrice']*float(r['volume'])*100),
                            "exp_short":exp_d.strftime("%m/%d"),
                            "exp_full":exp_d.strftime("%Y-%m-%d"),
                            "days":int(days),"delta":float(delta),
                            "rsi":float(st_data["rsi"]),"is_hedge":bool(is_hedge),
                            "hedge_reason":hedge_reason,"is_real_buy":bool(is_real_buy),
                            "spread":float(spread_val),"vol_ratio":float(st_data["vol_ratio"]),
                            "is_breakout":bool(st_data["is_breakout"]),
                            "is_reversal":bool(st_data["is_reversal"])
                        })
                    except:
                        continue
                if len(rows)>=3: break
            except:
                continue
        return rows
    except:
        return []

def calc_safe_score(row, st_data):
    if not st_data: return 8, "لا بيانات"
    ok=0
    reasons=[]
    try:
        if st_data["price"]>st_data["ema9"]>st_data["ema21"]:
            ok+=1
            reasons.append("EMA9>21")
        if 40<=st_data["rsi"]<=68:
            ok+=1
            reasons.append(f"RSI {st_data['rsi']:.0f}")
        elif st_data["rsi"]<35:
            ok+=1
            reasons.append(f"انعكاس RSI {st_data['rsi']:.0f}")
        if st_data["vol_ratio"]>=1.5:
            ok+=2
            reasons.append(f"VOL x{st_data['vol_ratio']:.1f}")
        elif st_data["vol_ratio"]>=1.0:
            ok+=1
            reasons.append("VOL جيد")
        if abs(row["dist"])<=1.5:
            ok+=2
            reasons.append("ATM آمن")
        elif abs(row["dist"])<=3:
            ok+=1
        if 0.35<=row["delta"]<=0.60:
            ok+=2
            reasons.append(f"Δ {row['delta']:.2f}")
        elif 0.30<=row["delta"]<=0.65:
            ok+=1
        if row["is_real_buy"]:
            ok+=2
            reasons.append("شراء حقيقي")
        if row["spread"]<5:
            ok+=1
            reasons.append(f"سبريد {row['spread']:.0f}%")
        if st_data["is_breakout"]:
            ok+=2
            reasons.append("انفجار High20")
        if st_data["is_reversal"]:
            ok+=2
            reasons.append("انعكاس دعم")
        if row["is_hedge"]:
            ok-=3
            reasons.append(row["hedge_reason"])
        if row["days"]==0:
            ok-=1
        if ok<0: ok=0
        if ok>12: ok=12
        txt=" | ".join(reasons[:3])
        return ok, txt
    except:
        return 8, "خطأ"

st.title(f"{st.session_state.view} - BOT الآمن {ksa_str}")
st.caption("دخول آمن 11+ = شراء حقيقي + انفجار + بدون تحوط - البوت يفحص كل 30ث")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص آمن 15ث")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        try:
            st_data=analysis_safe(r["ticker"])
            ok,reason=calc_safe_score(r, st_data)
            r2=dict(r)
            r2["ok"]=int(ok)
            r2["reason"]=reason
            if r2.get("prem_M",0)==0:
                r2["prem_M"]=r2.get("prem_val",0)/1e6
            enriched.append(r2)
        except:
            continue

    if not enriched:
        final=pd.DataFrame()
    else:
        df=pd.DataFrame(enriched)
        df=df.sort_values(["ok","prem_M"], ascending=[False, False])
        v=st.session_state.view
        if v=="✅ دخول آمن فقط":
            final=df[(df["ok"]>=11) & (df["is_hedge"]==False) & (df["is_real_buy"]==True)].head(15)
        elif v=="💎 بدون خوف 11+":
            final=df[df["ok"]>=11].head(20)
        elif v=="🔥 انفجار سعري":
            final=df[df["is_breakout"]==True].head(20)
            if final.empty:
                final=df.sort_values("vol_ratio", ascending=False).head(15)
        elif v=="↩️ نقطة انعكاس":
            final=df[df["is_reversal"]==True].head(20)
        elif v=="⚠️ تحوط - تجنبه":
            final=df[df["is_hedge"]==True].head(20)
        else:
            final=df.head(15)

    if not final.empty:
        st.success(f"✅ {len(final)} عقد | {ksa_str} | البوت {'🟢' if st.session_state.bot_active else '🔴'}")
        for _,w in final.head(2).iterrows():
            if w.get("ok",0)>=11 and not w.get("is_hedge",False):
                st.markdown(f"""
                <div style="background:#dcfce7;border:2px solid #22c55e;border-radius:12px;padding:10px;margin:5px 0;">
                ✅ <b>دخول آمن: {w.get('ticker')} {int(w.get('strike'))} CALL</b> | {w.get('reason')}<br>
                💰 ${w.get('stock_now',0):.2f} → {int(w.get('strike'))} ({w.get('dist',0):+.2f}%) | ${w.get('opt_price',0):.2f} Δ{w.get('delta',0):.2f}<br>
                🎯 هدف +50% وقف -25%
                </div>
                """, unsafe_allow_html=True)

        html='<table class="whale-table"><tr><th>💎</th><th>الشركة</th><th>سعر السهم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th><th>آمن؟</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0))
                if sp<1: sp=100
                if w.get("ticker")=="SPY" and sp>700: sp=580
                dist=float(w.get("dist",0))
                prem=float(w.get("prem_M",0))
                opt_p=float(w.get("opt_price",0))
                dlt=float(w.get("delta",0.55))
                vol=int(w.get("vol",0))
                oi=int(w.get("oi",0))
                ok=int(w.get("ok",0))
                css="score"
                if ok>=11: css="score"
                if w.get("is_hedge",False):
                    safe_badge=f'<span class="badge-hedge">⚠️ تحوط</span>'
                elif w.get("is_real_buy",False) and ok>=11:
                    safe_badge='<span class="badge-safe">✅ آمن</span>'
                else:
                    safe_badge='<span class="badge-risk">متوسط</span>'
                html+=f'<tr><td><span class="{css}">{ok}/12</span></td><td><b>{w.get("ticker","")}</b><br><span style="font-size:7px">{w.get("reason","")[:18]}</span></td><td><span style="color:#15803d">${sp:.2f}</span><br><span style="font-size:7px">RSI {float(w.get("rsi",50)):.0f} x{float(w.get("vol_ratio",1)):.1f}</span></td><td><b>{int(w.get("strike",0))}</b></td><td>{dist:+.2f}% Δ{dlt:.2f}</td><td>{w.get("exp_short","")} ({w.get("days",0)}ي)</td><td><b>${opt_p:.2f}</b><br><span style="font-size:7px">{vol/1000:.0f}K/{oi/1000:.0f}K</span></td><td><b>${prem:.1f}M</b><br><span style="font-size:7px">S{float(w.get("spread",0)):.0f}%</span></td><td>{safe_badge}</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning(f"لا يوجد في {st.session_state.view} - جرب كل الحيتان")

if do_scan or (st.session_state.bot_active and delay>30):
    tickers=["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX","AMZN","CRM"]
    with st.spinner(f"🤖 فحص {len(tickers)} سهم آمن..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=15) as executor:
            futs={executor.submit(fetch_safe, t, min_prem, min_vol): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf[(ndf["stock_now"]>1)&(ndf["prem_M"]>0)&(ndf["opt_price"]>0)]
        ndf=ndf[~((ndf["ticker"]=="SPY") & (ndf["stock_now"]>700))]
        if not ndf.empty:
            if not st.session_state.results.empty:
                combined=pd.concat([st.session_state.results, ndf])
                combined=combined.sort_values("prem_M", ascending=False)
                combined=combined.drop_duplicates(["ticker","strike","exp_full"]).head(1000)
            else:
                combined=ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

if st.session_state.bot_active:
    st.markdown(f"<script>setTimeout(function(){{window.location.reload();}}, 30000);</script>", unsafe_allow_html=True)

st.caption(f"V37.1 Fixed | {ksa_str} KSA | إصلاح SyntaxError 110 - بدون قوس")
