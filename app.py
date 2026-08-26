import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V37.2 SAFE RELAXED", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fff!important;}
.whale-table {width:100%; border-collapse:collapse; font-size:11px;}
.whale-table th {background:#111!important; color:#fff!important; padding:7px 3px; text-align:center; font-size:8px;}
.whale-table td {background:#fff!important; padding:8px 3px; text-align:center; border-bottom:1px solid #eee; font-weight:700; font-size:10px;}
.badge-safe {background:#dcfce7; color:#14532d; border:2px solid #22c55e; padding:5px 10px; border-radius:12px; font-size:9px; font-weight:900;}
.time-card {background:#111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
.bot-card {background:linear-gradient(135deg,#14532d,#16a34a); color:#fff; border-radius:12px; padding:12px; text-align:center; font-weight:800;}
</style>
""", unsafe_allow_html=True)

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX","AMZN","CRM","HOOD","GME","ORCL"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_ts" not in st.session_state: st.session_state.last_ts=datetime.now()
if "view" not in st.session_state: st.session_state.view="✅ دخول آمن فقط"
if "bot_active" not in st.session_state: st.session_state.bot_active=False

def norm_cdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))
def greeks(S,K,T,iv):
    try:
        if T<=0: T=0.05
        if iv<0.15 or iv>3: iv=0.55
        d1=(math.log(S/K)+0.5*iv*iv*T)/(iv*math.sqrt(T))
        delta=norm_cdf(d1)
        return max(0.15,min(0.85,delta)), iv
    except: return 0.55,0.55

now=datetime.now()
ksa_time=now+timedelta(hours=3)
ksa_str=ksa_time.strftime('%H:%M:%S')
try: delay=(now-st.session_state.last_ts).total_seconds()
except: delay=0
if delay<0 or delay>3600: delay=0

st.sidebar.title("🤖 بوت V37.2 مرخي")
st.sidebar.markdown(f'<div class="time-card">● LIVE {ksa_str} KSA<br>⏳ {delay:.0f}ث | {st.session_state.view}</div>', unsafe_allow_html=True)
bot_status="🟢 شغال" if st.session_state.bot_active else "🔴 متوقف"
st.sidebar.markdown(f'<div class="bot-card">البوت: {bot_status}<br>مرخي 9+/12</div>', unsafe_allow_html=True)

if st.sidebar.button("🤖 شغل البوت", type="primary", use_container_width=True): st.session_state.bot_active=True; st.rerun()
if st.sidebar.button("⏹️ وقف", use_container_width=True): st.session_state.bot_active=False; st.rerun()

st.sidebar.markdown("### 📌 الفلترة")
views=["✅ دخول آمن فقط","💎 بدون خوف 10+","🔥 انفجار سعري","↩️ نقطة انعكاس","🏆 كل الحيتان"]
for v in views:
    if st.sidebar.button(v, key=f"btn_{v}", use_container_width=True, type="primary" if st.session_state.view==v else "secondary"):
        st.session_state.view=v; st.rerun()
st.sidebar.markdown("---")
c1,c2=st.sidebar.columns(2)
with c1: do_scan=st.button("⚡ فحص مرخي", type="primary", use_container_width=True)
with c2:
    if st.button("🧹 تصفير", use_container_width=True): st.session_state.results=pd.DataFrame(); st.session_state.last_ts=datetime.now(); st.rerun()

# إرخاء الفلتر - 0.1M و 50 VOL
min_prem=st.sidebar.slider("💰 M$",0.05,5.0,0.1,0.05)
min_vol=st.sidebar.slider("VOL",20,5000,50,20)

@st.cache_data(ttl=45)
def analysis_safe(ticker):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        h=yf.Ticker(real).history(period="3mo")
        if len(h)<30: return None
        curr=float(h['Close'].iloc[-1])
        if curr<1 or curr>10000: return None
        ema9=float(h['Close'].ewm(9).mean().iloc[-1])
        ema21=float(h['Close'].ewm(21).mean().iloc[-1])
        h20=h.tail(20)
        vwap=float((h20['Close']*h20['Volume']).sum()/h20['Volume'].sum()) if h20['Volume'].sum()>0 else curr
        delta_price=h['Close'].diff()
        gain=delta_price.where(delta_price>0,0).ewm(alpha=1/14, adjust=False).mean()
        loss=(-delta_price.where(delta_price<0,0)).ewm(alpha=1/14, adjust=False).mean()
        last_gain=float(gain.iloc[-1]); last_loss=float(loss.iloc[-1])
        if last_loss==0: last_loss=0.01
        rsi=100-(100/(1+last_gain/last_loss))
        try:
            pg=float(gain.iloc[-6]); pl=float(loss.iloc[-6])
            if pl==0: pl=0.01
            rsi_prev=100-(100/(1+pg/pl))
        except: rsi_prev=50
        high20=float(h['High'].tail(20).max()); low20=float(h['Low'].tail(20).min())
        vol_avg=float(h['Volume'].tail(20).mean()); vol_today=float(h['Volume'].iloc[-1])
        vol_ratio=vol_today/vol_avg if vol_avg>0 else 1
        pos=(curr-low20)/(high20-low20)*100 if high20!=low20 else 50
        is_breakout=curr>=high20*0.98 and vol_ratio>=1.2
        is_reversal=(rsi<40) or (curr<=low20*1.05) or (rsi>rsi_prev and rsi<45)
        return {"price":curr,"ema9":ema9,"ema21":ema21,"vwap":vwap,"rsi":float(rsi),"rsi_prev":float(rsi_prev),"high20":high20,"low20":low20,"vol_ratio":float(vol_ratio),"pos":float(pos),"is_breakout":bool(is_breakout),"is_reversal":bool(is_reversal)}
    except: return None

def fetch_safe(ticker, min_prem, min_vol):
    try:
        real="SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
        tk=yf.Ticker(real)
        if not tk.options: return []
        st_data=analysis_safe(ticker)
        if not st_data: return []
        curr=st_data["price"]
        rows=[]
        for exp in tk.options[:4]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d")
                days=(exp_d-datetime.now()).days
                T=max(days/365,0.03) if days>=0 else 0.02
                calls=tk.option_chain(exp).calls
                if calls.empty: continue
                calls=calls.copy()
                if 'volume' not in calls.columns or 'lastPrice' not in calls.columns: continue
                calls=calls[calls['volume']>0]
                calls['prem']=calls['lastPrice']*calls['volume']*100
                calls=calls[calls['prem']>=min_prem*1e6]
                calls=calls[calls['volume']>=min_vol]
                if calls.empty: continue
                calls=calls.sort_values('prem',ascending=False).head(5)
                for _,r in calls.iterrows():
                    try:
                        strike=float(r['strike'])
                        if ticker=="SPY" and strike>900: continue
                        dist=(strike-curr)/curr*100 if curr>0 else 0
                        if abs(dist)>8: continue
                        iv=float(r.get('impliedVolatility',0.55))
                        if pd.isna(iv) or iv<0.1 or iv>4: iv=0.55
                        delta,fiv=greeks(curr,strike,T,iv)
                        # إرخاء دلتا 0.15-0.85
                        if delta<0.15 or delta>0.85: continue
                        prem_M=float(r['lastPrice']*float(r['volume'])*100/1e6)
                        opt_price=float(r['lastPrice'])
                        vol=int(r['volume'])
                        oi=int(r.get('openInterest',0))
                        bid=float(r.get('bid',0)); ask=float(r.get('ask',0))
                        spread_val=(ask-bid)/opt_price*100 if opt_price>0 and bid>0 else 10
                        # تحوط مرخي جدا
                        is_hedge=False
                        if oi>0 and vol/oi<0.05 and days>15 and spread_val>20:
                            is_hedge=True
                        is_real_buy=spread_val<12 and opt_price>=0.4
                        if prem_M==0 or opt_price==0: continue
                        rows.append({"ticker":ticker,"stock_now":float(curr),"strike":int(strike),"dist":float(dist),"opt_price":float(opt_price),"vol":int(vol),"oi":int(oi),"prem_M":float(prem_M),"prem_val":float(r['lastPrice']*float(r['volume'])*100),"exp_short":exp_d.strftime("%m/%d"),"exp_full":exp_d.strftime("%Y-%m-%d"),"days":int(days),"delta":float(delta),"rsi":float(st_data["rsi"]),"is_hedge":bool(is_hedge),"is_real_buy":bool(is_real_buy),"spread":float(spread_val),"vol_ratio":float(st_data["vol_ratio"]),"is_breakout":bool(st_data["is_breakout"]),"is_reversal":bool(st_data["is_reversal"])})
                    except: continue
                if len(rows)>=3: break
            except: continue
        return rows
    except: return []

def calc_safe_score(row, st_data):
    if not st_data: return 7, "لا بيانات"
    ok=0; reasons=[]
    try:
        if st_data["price"]>st_data["ema9"]: ok+=1; reasons.append("فوق EMA9")
        if st_data["price"]>st_data["ema21"]: ok+=1
        if 30<=st_data["rsi"]<=70: ok+=2; reasons.append(f"RSI {st_data['rsi']:.0f}")
        elif st_data["rsi"]<35: ok+=2; reasons.append("انعكاس")
        if st_data["vol_ratio"]>=1.0: ok+=1; reasons.append(f"VOLx{st_data['vol_ratio']:.1f}")
        if abs(row["dist"])<=2: ok+=2; reasons.append("ATM")
        elif abs(row["dist"])<=4: ok+=1
        if 0.25<=row["delta"]<=0.70: ok+=2; reasons.append(f"Δ{row['delta']:.2f}")
        else: ok+=1
        if row["is_real_buy"]: ok+=1; reasons.append("حقيقي")
        if row["spread"]<8: ok+=1
        if st_data["is_breakout"]: ok+=2; reasons.append("انفجار")
        if st_data["is_reversal"]: ok+=2; reasons.append("انعكاس")
        if row["is_hedge"]: ok-=2
        ok=max(0,min(12,ok))
        return ok, " | ".join(reasons[:3])
    except: return 7, "خطأ"

st.title(f"{st.session_state.view} - BOT {ksa_str}")
st.caption(f"دخول آمن 9+/12 مرخي - بدون تحوط قوي فقط - {ksa_str} KSA")

if st.session_state.results.empty:
    st.info("⏳ اضغط ⚡ فحص مرخي - 0.1M و VOL 50")
    final=pd.DataFrame()
else:
    enriched=[]
    for _,r in st.session_state.results.iterrows():
        try:
            st_data=analysis_safe(r["ticker"])
            ok,reason=calc_safe_score(r, st_data)
            r2=dict(r); r2["ok"]=int(ok); r2["reason"]=reason
            enriched.append(r2)
        except: continue

    if not enriched:
        final=pd.DataFrame()
    else:
        df=pd.DataFrame(enriched)
        df=df.sort_values(["ok","prem_M"], ascending=[False, False])
        v=st.session_state.view
        if v=="✅ دخول آمن فقط":
            # مرخي: 9+ فقط + مو تحوط قوي
            final=df[(df["ok"]>=9) & (df["is_hedge"]==False)].head(20)
            if final.empty:
                final=df[df["ok"]>=8].head(20)
        elif v=="💎 بدون خوف 10+":
            final=df[df["ok"]>=10].head(20)
        elif v=="🔥 انفجار سعري":
            final=df[df["is_breakout"]==True].head(20)
            if final.empty: final=df.sort_values("vol_ratio", ascending=False).head(15)
        elif v=="↩️ نقطة انعكاس":
            final=df[df["is_reversal"]==True].head(20)
            if final.empty: final=df[df["rsi"]<45].head(15)
        else:
            final=df.head(20)

    if not final.empty:
        st.success(f"✅ {len(final)} عقد آمن (مرخي 9+) | {ksa_str} | البوت {'🟢' if st.session_state.bot_active else '🔴'}")
        for _,w in final.head(2).iterrows():
            if w.get("ok",0)>=9:
                st.markdown(f"""<div style="background:#dcfce7;border:2px solid #22c55e;border-radius:12px;padding:10px;margin:5px 0;">✅ <b>دخول: {w.get('ticker')} {int(w.get('strike'))} CALL</b> | {w.get('reason')} | {w.get('ok')}/12<br>💰 ${w.get('stock_now',0):.2f} → {int(w.get('strike'))} ({w.get('dist',0):+.1f}%) | ${w.get('opt_price',0):.2f} Δ{w.get('delta',0):.2f} | هدف +40% وقف -20%</div>""", unsafe_allow_html=True)
        html='<table class="whale-table"><tr><th>💎</th><th>الشركة</th><th>سعر السهم</th><th>سترايك</th><th>مسافة</th><th>📅</th><th>سعر العقد</th><th>الحوت</th><th>آمن؟</th></tr>'
        for _,w in final.iterrows():
            try:
                sp=float(w.get("stock_now",0))
                if sp<1: sp=100
                if w.get("ticker")=="SPY" and sp>800: sp=580
                dist=float(w.get("dist",0)); prem=float(w.get("prem_M",0)); opt_p=float(w.get("opt_price",0)); dlt=float(w.get("delta",0.55)); vol=int(w.get("vol",0)); oi=int(w.get("oi",0)); ok=int(w.get("ok",0))
                safe_badge='<span class="badge-safe">✅ آمن</span>' if not w.get("is_hedge",False) and ok>=9 else '<span style="background:#fee2e2;padding:3px 6px;border-radius:8px;font-size:8px">متوسط</span>'
                html+=f'<tr><td>{ok}/12</td><td><b>{w.get("ticker","")}</b><br><span style="font-size:7px">{w.get("reason","")[:18]}</span></td><td>${sp:.2f}<br><span style="font-size:7px">RSI {float(w.get("rsi",50)):.0f}</span></td><td><b>{int(w.get("strike",0))}</b></td><td>{dist:+.1f}% Δ{dlt:.2f}</td><td>{w.get("exp_short","")} ({w.get("days",0)}ي)</td><td>${opt_p:.2f}<br><span style="font-size:7px">{vol/1000:.0f}K/{oi/1000:.0f}K</span></td><td>${prem:.1f}M S{float(w.get("spread",0)):.0f}%</td><td>{safe_badge}</td></tr>'
            except: continue
        html+='</table>'
        st.markdown(html, unsafe_allow_html=True)
    else:
        st.warning("لا يوجد حتى بعد الإرخاء - اضغط كل الحيتان أو فحص مرخي")
        if 'df' in locals() and not df.empty:
            st.write("أفضل موجود:")
            st.dataframe(df.head(5))

if do_scan or (st.session_state.bot_active and delay>30):
    tickers=["SPY","QQQ","TSLA","NVDA","AAPL","META","MSFT","AMD","COIN","MSTR","PLTR","SOFI","MARA","SMCI","AVGO","NFLX","AMZN","CRM"]
    with st.spinner(f"🤖 فحص مرخي {len(tickers)}..."):
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
            combined=pd.concat([st.session_state.results, ndf]).sort_values("prem_M",ascending=False).drop_duplicates(["ticker","strike","exp_full"]).head(1000) if not st.session_state.results.empty else ndf
            st.session_state.results=combined
            st.session_state.last_ts=datetime.now()
            st.rerun()

if st.session_state.bot_active:
    st.markdown(f"<script>setTimeout(function(){{window.location.reload();}}, 30000);</script>", unsafe_allow_html=True)

st.caption(f"V37.2 Relaxed | {ksa_str} KSA | مرخي 9+/12 - يطلع نتائج حتى لو السوق هادي")
