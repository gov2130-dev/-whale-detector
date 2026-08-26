import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V54 REAL", initial_sidebar_state="collapsed")
st.markdown("""<style>
.stApp{background:#fff!important;}
.big-card{border:3px solid #000;border-radius:12px;padding:12px;margin:8px 0;background:#fff;}
.call{border-color:#16a34a!important;} .put{border-color:#dc2626!important;}
.time-card{background:#111;color:#4ade80;border-radius:10px;padding:10px;text-align:center;font-family:monospace;border:2px solid #22c55e;}
div.stButton > button{width:100%;height:50px;font-weight:900;border-radius:12px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "view" not in st.session_state: st.session_state.view="🏆 الكل"
if "debug" not in st.session_state: st.session_state.debug=[]

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')
st.markdown(f"# V54 FIXED - {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V54 يطلع حتى لو تحوط - مع وسم حقيقي vs تحوط - يحل V53 الفاضي</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY"): st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

b1,b2=st.columns(2)
with b1: do_scan=st.button("⚡ فحص واقعي - يطلع الكل", type="primary")
with b2:
    if st.button("🧹 تصفير"): st.session_state.results=pd.DataFrame(); st.session_state.debug=[]; st.cache_data.clear(); st.rerun()

@st.cache_data(ttl=25)
def analysis_v54(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="5d", interval="15m")
        if len(h)<20: 
            h=tk.history(period="1mo")
            if len(h)<10: return None, f"{ticker} لا بيانات"
            curr=float(h['Close'].iloc[-1])
            prev=float(h['Close'].iloc[-2])
            ch1=float((curr-prev)/prev*100)
            vwap=curr
            hour_ch=ch1/6
            rsi=50
        else:
            curr=float(h['Close'].iloc[-1])
            vwap=float(((h['High']+h['Low']+h['Close'])/3).tail(20).mean())
            last_hour=float((h['Close'].iloc[-1]-h['Close'].iloc[-4])/h['Close'].iloc[-4]*100) if len(h)>=4 else 0
            hour_ch=last_hour
            h_daily=tk.history(period="1mo")
            prev=float(h_daily['Close'].iloc[-2]) if len(h_daily)>=2 else curr
            ch1=float((curr-prev)/prev*100) if prev!=0 else 0
            d=h['Close'].diff()
            g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
            l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
            lg=float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
            ll=float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) and float(l.iloc[-1])>0.01 else 0.1
            rsi=float(100-(100/(1+lg/ll)))
            rsi=max(10,min(90,rsi))
        if curr<3: return None, f"{ticker} سعر رخيص"
        # لا نستبعد تصريف - نوسمه فقط
        tag=""
        if rsi>=75 and ch1>=3: tag="تصريف محتمل"
        elif rsi<=25 and ch1<=-3: tag="تجميع محتمل"
        # اتجاه حتى لو ضعيف
        trend="NEUTRAL"
        reason=""
        if curr>=vwap*0.998 and ch1>=-0.5: # مرونة
            trend="BULL"; reason=f"قرب VWAP ${vwap:.1f} + ساعة {hour_ch:+.1f}% + يوم {ch1:+.1f}%"
        elif curr<=vwap*1.002 and ch1<=0.5:
            trend="BEAR"; reason=f"قرب VWAP ${vwap:.1f} + ساعة {hour_ch:+.1f}% + يوم {ch1:+.1f}%"
        if trend=="NEUTRAL":
            trend="BEAR" if ch1<0 else "BULL"
            reason=f"اتجاه يوم {ch1:+.1f}% + VWAP ${vwap:.1f}"
        return {"price":curr,"vwap":vwap,"ch1":ch1,"hour_ch":hour_ch,"rsi":rsi,"trend":trend,"reason":reason,"tag":tag}, f"{ticker} {trend} {ch1:+.1f}%"
    except Exception as e:
        return None, f"{ticker} خطأ {str(e)[:30]}"

def fetch_v54(ticker):
    try:
        sd, msg = analysis_v54(ticker)
        if not sd: return [], msg
        tk=yf.Ticker(ticker)
        if not tk.options: return [], f"{ticker} لا options"
        curr=sd["price"]; trend=sd["trend"]
        rows=[]
        for exp in tk.options[:2]:
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
                if days<0 or days>14: continue
                chain=tk.option_chain(exp)
                df_opt=chain.calls if trend=="BULL" else chain.puts
                if df_opt.empty: continue
                df_opt=df_opt.copy().dropna(subset=['lastPrice'])
                df_opt=df_opt[df_opt['lastPrice']>=0.15]
                if df_opt.empty: continue
                # احسب VOL/OI
                if 'volume' in df_opt.columns: df_opt['vol_f']=df_opt['volume'].fillna(0)
                else: df_opt['vol_f']=0
                if 'openInterest' in df_opt.columns: df_opt['oi_f']=df_opt['openInterest'].fillna(0)
                else: df_opt['oi_f']=0
                # لا نستبعد تحوط - نوسمه
                df_opt['whale_type']=df_opt.apply(lambda x: "تحوط 🔒" if x['vol_f']<x['oi_f']*0.4 and x['oi_f']>1000 else "حقيقي 🔥" if x['vol_f']>x['oi_f']*0.7 else "مختلط", axis=1)
                # رتب بالحجم
                df_opt=df_opt.sort_values('vol_f', ascending=False).head(2)
                for _,r in df_opt.iterrows():
                    try:
                        strike=float(r['strike']); dist=(strike-curr)/curr*100
                        if abs(dist)>6: continue
                        # استبعد بعيد مرة
                        if trend=="BULL" and dist>5: continue
                        if trend=="BEAR" and dist<-5: continue
                        vol=int(r['vol_f']); oi=int(r['oi_f'])
                        rows.append({
                            "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                            "stock_now":curr,"strike":int(strike),"dist":dist,
                            "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                            "whale":r['whale_type'],"exp_short":exp_d.strftime("%m/%d"),
                            "days":days,"rsi":sd["rsi"],"ch1":sd["ch1"],"hour_ch":sd["hour_ch"],
                            "vwap":sd["vwap"],"trend":trend,"reason":sd["reason"],"tag":sd["tag"]
                        })
                    except: continue
                if rows: break
            except: continue
        if rows:
            # أفضل واحد حقيقي أولا
            rows_sorted=sorted(rows, key=lambda x: (1 if "حقيقي" in x["whale"] else 0, x["vol"]), reverse=True)
            return [rows_sorted[0]], f"{ticker} ✅ {rows_sorted[0]['whale']} VOL {rows_sorted[0]['vol']} OI {rows_sorted[0]['oi']}"
        else:
            return [], f"{ticker} لا عقد بعد فلتر {sd['trend']}"
    except Exception as e:
        return [], f"{ticker} خطأ fetch {str(e)[:30]}"

if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    enriched=[]
    for _,r in df.iterrows():
        ch1=float(r.get("ch1",0)); hour_ch=float(r.get("hour_ch",0)); rsi=float(r.get("rsi",50))
        vol=int(r.get("vol",0)); oi=int(r.get("oi",0))
        score=50
        if r["type"]=="CALL":
            if hour_ch>=0.8: score+=20
            if ch1>=1: score+=12
            if 55<=rsi<=70: score+=10
        else:
            if hour_ch<=-0.8: score+=20
            if ch1<=-1: score+=12
            if 30<=rsi<=45: score+=10
        if "حقيقي" in r.get("whale",""): score+=15
        elif "تحوط" in r.get("whale",""): score-=10
        if "تصريف" in r.get("tag",""): score-=12
        score=int(max(30,min(88,score)))
        r2=dict(r); r2["confirm"]=score
        enriched.append(r2)
    df2=pd.DataFrame(enriched)
    df2=df2.sort_values("confirm", ascending=False)
    df2=df2.drop_duplicates(subset=["ticker"], keep="first")
    v=st.session_state.view
    if "BUY قوي" in v: final=df2[df2["type"]=="CALL"]
    elif "SELL قوي" in v: final=df2[df2["type"]=="PUT"]
    else: final=df2
else:
    final=pd.DataFrame()
    st.info("V53 كان فاضي لأنه يستبعد التحوط - V54 يطلع الكل مع وسم تحوط 🔒 vs حقيقي 🔥")

if not final.empty:
    st.success(f"✅ {len(final)} عقد - أخضر حقيقي أحمر تحوط - {ksa_str}")
    for _,w in final.head(4).iterrows():
        conf=int(w.get("confirm",50)); whale=w.get("whale","")
        border="#16a34a" if "حقيقي" in whale else "#888888" if "تحوط" in whale else "#dc2626"
        icon="🔥" if "حقيقي" in whale else "🔒" if "تحوط" in whale else "⚠️"
        st.markdown(f"""<div class="big-card" style="border-color:{border}">
        <b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}% | {whale} | VOL {int(w.get('vol',0))} OI {int(w.get('oi',0))}</b><br>
        {w.get('reason')}<br>
        <span style="font-size:11px; color:{'#dc2626' if 'تصريف' in w.get('tag','') else '#000'}">{w.get('tag','')}</span><br>
        <span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} | ساعة {float(w.get('hour_ch',0)):+.1f}% يوم {float(w.get('ch1',0)):+.1f}% RSI {float(w.get('rsi',0)):.0f} | عقد ${float(w.get('opt_price',0)):.2f} | {w.get('exp_short')} {int(w.get('days'))}ي</span>
        </div>""", unsafe_allow_html=True)
    if st.session_state.debug:
        with st.expander("🔍 ليش V53 كان فاضي - Debug"):
            for d in st.session_state.debug: st.text(d)

if do_scan:
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR","AMD","AVGO","SOFI","TSM"]
    with st.spinner("يفحص واقعي - يميز حقيقي vs تحوط..."):
        rows=[]; debug=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_v54, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res, msg=fu.result()
                    debug.append(msg)
                    if res: rows.extend(res)
                except Exception as e:
                    debug.append(f"خطأ {e}")
    st.session_state.debug=debug
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.error("لا يوجد حتى بعد التسهيل")
        for d in debug: st.text(d)

st.caption(f"V54 FIXED | {ksa_str} | يطلع الكل مع وسم 🔥 حقيقي VOL>OI*0.7 vs 🔒 تحوط VOL<OI*0.4 | يحل V53 الفاضي اللي في صورتك")
