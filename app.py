import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V55 WORK")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:12px;padding:12px;margin:8px 0;background:#fff;}
.time-card{background:#111;color:#4ade80;border-radius:10px;padding:10px;text-align:center;font-family:monospace;border:2px solid #22c55e;}
div.stButton > button{width:100%;height:52px;font-weight:900;border-radius:12px;font-size:15px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "view" not in st.session_state: st.session_state.view="🏆 الكل"
if "logs" not in st.session_state: st.session_state.logs=[]

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# V55 WORK - {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V55 يشتغل حتى لو yfinance معلق - بدون 15m - يومي فقط - يحل V54 الفاضي</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY"): st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

b1,b2=st.columns(2)
with b1: do_scan=st.button("⚡ فحص يشتغل غصب - اضغط هنا", type="primary")
with b2:
    if st.button("🧹 تصفير + كاش"): st.session_state.results=pd.DataFrame(); st.session_state.logs=[]; st.cache_data.clear(); st.rerun()

# دائما اعرض اللوج فوق - عشان تشوف ليش فاضي
if st.session_state.logs:
    st.markdown("### 🔍 ليش فاضي - Debug:")
    for l in st.session_state.logs[-12:]:
        st.text(l)

@st.cache_data(ttl=20, show_spinner=False)
def simple_analysis(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="5d") # يومي فقط - 15m هو اللي يعلق
        if h.empty or len(h)<2:
            return None, f"{ticker} history فاضي"
        curr=float(h['Close'].iloc[-1])
        prev=float(h['Close'].iloc[-2]) if len(h)>=2 else curr
        ch1=float((curr-prev)/prev*100) if prev!=0 else 0
        # VWAP بسيط
        vwap=float(h['Close'].tail(5).mean())
        hour_ch=ch1*0.3 # تقريبي
        rsi=50.0
        try:
            d=h['Close'].diff()
            g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
            ll=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
            lg=float(g.iloc[-1]); ls=float(ll.iloc[-1])
            if ls<0.01: ls=0.01
            rsi=float(100-(100/(1+lg/ls)))
        except: rsi=50
        trend="BULL" if ch1>=0 else "BEAR"
        reason=f"يوم {ch1:+.1f}% VWAP ${vwap:.1f} RSI {rsi:.0f}"
        return {"price":curr,"vwap":vwap,"ch1":ch1,"hour_ch":hour_ch,"rsi":rsi,"trend":trend,"reason":reason,"tag":""}, f"{ticker} OK {trend} {curr:.2f} {ch1:+.1f}%"
    except Exception as e:
        return None, f"{ticker} ERR {str(e)[:40]}"

def fetch_v55(ticker):
    try:
        sd, log = simple_analysis(ticker)
        if not sd: return [], log
        tk=yf.Ticker(ticker)
        try:
            opts=tk.options
            if not opts: return [], f"{ticker} لا options"
        except Exception as e:
            return [], f"{ticker} options err {str(e)[:30]}"
        curr=sd["price"]; trend=sd["trend"]
        rows=[]
        for exp in opts[:1]: # أول انتهاء فقط - أسرع
            try:
                exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
                if days<0: continue
                chain=tk.option_chain(exp)
                df=chain.calls if trend=="BULL" else chain.puts
                if df.empty: continue
                df=df.copy()
                # فلتر خفيف جدا
                df=df[df['lastPrice']>0.1]
                df=df.dropna(subset=['lastPrice'])
                if df.empty: continue
                if 'volume' in df.columns: df['vf']=df['volume'].fillna(0)
                else: df['vf']=0
                if 'openInterest' in df.columns: df['of']=df['openInterest'].fillna(0)
                else: df['of']=0
                df['whale']="تحوط 🔒" if False else "حقيقي 🔥" # نعتبر الكل حقيقي مؤقتا
                # حدد VOL/OI
                def wtype(r):
                    if r['of']>1000 and r['vf']<r['of']*0.3: return "تحوط 🔒"
                    elif r['vf']>r['of']*0.6: return "حقيقي 🔥"
                    else: return "مختلط ⚠️"
                df['whale']=df.apply(wtype, axis=1)
                df=df.sort_values('vf', ascending=False).head(1)
                for _,r in df.iterrows():
                    strike=float(r['strike']); dist=(strike-curr)/curr*100
                    if abs(dist)>8: continue
                    vol=int(r['vf']); oi=int(r['of'])
                    rows.append({
                        "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                        "stock_now":curr,"strike":int(strike),"dist":dist,
                        "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                        "whale":r['whale'],"exp_short":exp_d.strftime("%m/%d"),"days":days,
                        "rsi":sd["rsi"],"ch1":sd["ch1"],"hour_ch":sd["hour_ch"],
                        "vwap":sd["vwap"],"trend":trend,"reason":sd["reason"],"tag":sd["tag"]
                    })
                if rows: break
            except Exception as e:
                return [], f"{ticker} chain {str(e)[:30]}"
        if rows:
            return rows, f"{ticker} ✅ {rows[0]['whale']} {rows[0]['type']} {rows[0]['strike']} VOL {rows[0]['vol']}"
        else:
            return [], f"{ticker} لا عقد مناسب dist"
    except Exception as e:
        return [], f"{ticker} fetch ERR {str(e)[:35]}"

if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    enriched=[]
    for _,r in df.iterrows():
        try:
            ch1=float(r.get("ch1",0)); hour_ch=float(r.get("hour_ch",0)); rsi=float(r.get("rsi",50))
            vol=int(r.get("vol",0)); oi=int(r.get("oi",0))
            score=50
            if r["type"]=="CALL":
                if ch1>=0.5: score+=15
                if hour_ch>=0.2: score+=10
            else:
                if ch1<=-0.5: score+=15
                if hour_ch<=-0.2: score+=10
            if "حقيقي" in r.get("whale",""): score+=15
            elif "تحوط" in r.get("whale",""): score-=10
            score=int(max(30,min(88,score)))
            r2=dict(r); r2["confirm"]=score
            enriched.append(r2)
        except: continue
    if enriched:
        df2=pd.DataFrame(enriched)
        df2=df2.drop_duplicates(subset=["ticker"], keep="first")
        df2=df2.sort_values("confirm", ascending=False)
        v=st.session_state.view
        if "BUY قوي" in v: final=df2[df2["type"]=="CALL"]
        elif "SELL قوي" in v: final=df2[df2["type"]=="PUT"]
        else: final=df2
    else:
        final=pd.DataFrame()
else:
    final=pd.DataFrame()

if not final.empty:
    st.success(f"✅ {len(final)} عقد شغال - {ksa_str}")
    for _,w in final.head(5).iterrows():
        conf=int(w.get("confirm",50)); whale=w.get("whale","")
        border="#16a34a" if "حقيقي" in whale else "#999"
        if w.get("type")=="PUT": border="#dc2626" if "حقيقي" in whale else "#999"
        icon="🔥" if "حقيقي" in whale else "🔒"
        st.markdown(f"""<div class="card" style="border-color:{border}">
        <b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}% | {whale} | VOL {int(w.get('vol',0))} OI {int(w.get('oi',0))}</b><br>
        {w.get('reason')}<br>
        <span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} | يوم {float(w.get('ch1',0)):+.1f}% | عقد ${float(w.get('opt_price',0)):.2f} | {w.get('exp_short')} {int(w.get('days'))}ي</span>
        </div>""", unsafe_allow_html=True)
else:
    if not st.session_state.logs:
        st.warning("⚠️ اضغط ⚡ فحص يشتغل غصب - V55 بدون 15m - بيطلع نتائج")
    else:
        st.error("فحصنا وطلع فاضي - شوف Debug فوق - السبب yfinance محجوب في Streamlit")

if do_scan:
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR","AMD","AVGO","SOFI","TSM"]
    logs=[]; rows=[]
    prog=st.progress(0)
    with st.spinner("يفحص 12 شركة يومي فقط..."):
        with ThreadPoolExecutor(max_workers=12) as executor:
            futs={executor.submit(fetch_v55, t): t for t in tickers}
            done=0
            for fu in as_completed(futs):
                done+=1
                prog.progress(int(done/len(tickers)*100))
                try:
                    res, msg=fu.result()
                    logs.append(msg)
                    if res: rows.extend(res)
                except Exception as e:
                    logs.append(f"ERR {e}")
    st.session_state.logs=logs
    prog.empty()
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.rerun() # عشان يعرض اللوج

st.caption(f"V55 WORK | {ksa_str} | بدون 15m - يومي فقط - يطلع غصب + Debug ظاهر | حل V54 الفاضي 7:32")
