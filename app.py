import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V53 REAL")
st.markdown("""<style>.stApp{background:#fff!important;}
.time-card{background:#111;color:#4ade80;border-radius:10px;padding:10px;text-align:center;font-family:monospace;border:2px solid #22c55e;}
div.stButton > button{width:100%;height:50px;font-weight:900;border-radius:12px;}</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "view" not in st.session_state: st.session_state.view="🏆 الكل"

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')
st.markdown(f"# V53 REAL - {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V53 واقعي - زخم لحظي + حوت حقيقي مو تحوط + انعكاس حاضر - يحل خدعة TSLA 252</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("✅ BUY"): st.session_state.view="✅ BUY قوي"; st.rerun()
with c2:
    if st.button("🔻 SELL"): st.session_state.view="🔻 SELL قوي"; st.rerun()
with c3:
    if st.button("🏆 الكل"): st.session_state.view="🏆 الكل"; st.rerun()

b1,b2=st.columns(2)
with b1: do_scan=st.button("⚡ فحص واقعي - زخم الآن", type="primary")
with b2:
    if st.button("🧹 تصفير"): st.session_state.results=pd.DataFrame(); st.cache_data.clear(); st.rerun()

@st.cache_data(ttl=20)
def real_analysis(ticker):
    try:
        tk=yf.Ticker(ticker)
        h=tk.history(period="2d", interval="15m") # 15 دقيقة - تفاعل مباشر
        if len(h)<30: return None
        h_daily=tk.history(period="1mo")
        curr=float(h['Close'].iloc[-1])
        if curr<5 or curr>5000: return None
        # VWAP لحظي
        h['vwap']=(h['High']+h['Low']+h['Close'])/3
        vwap=float(h['vwap'].tail(20).mean())
        # زخم الآن - آخر 4 شموع 15 دقيقة = ساعة
        last_hour_ch=float((h['Close'].iloc[-1]-h['Close'].iloc[-4])/h['Close'].iloc[-4]*100)
        # RSI لحظي
        d=h['Close'].diff()
        g=d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l=(-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg=float(g.iloc[-1]); ll=float(l.iloc[-1]) if float(l.iloc[-1])>0.01 else 0.01
        rsi=100-(100/(1+lg/ll)) if not pd.isna(lg) else 50
        # يومي
        prev=float(h_daily['Close'].iloc[-2])
        ch1=float((curr-prev)/prev*100)
        # شرط واقعي: لا تدخل إذا مبالغ فيه RSI 80+
        if rsi>=78 and ch1>=3: return None # تصريف
        if rsi<=22 and ch1<=-3: return None # تجميع - لا تدخل PUT
        # اتجاه حقيقي الآن
        trend="NEUTRAL"; reason=""
        if curr>vwap and last_hour_ch>=0.5 and rsi>=52 and rsi<=72 and ch1>=0.3:
            trend="BULL"; reason=f"فوق VWAP ${vwap:.1f} + زخم ساعة {last_hour_ch:+.1f}% + RSI {rsi:.0f}"
        elif curr<vwap and last_hour_ch<=-0.5 and rsi<=48 and rsi>=28 and ch1<=-0.3:
            trend="BEAR"; reason=f"تحت VWAP ${vwap:.1f} + هبوط ساعة {last_hour_ch:+.1f}% + RSI {rsi:.0f}"
        if trend=="NEUTRAL": return None
        return {"price":curr,"vwap":vwap,"ch1":ch1,"hour_ch":last_hour_ch,"rsi":rsi,"trend":trend,"reason":reason}
    except: return None

def fetch_real(ticker):
    try:
        sd=real_analysis(ticker)
        if not sd: return []
        tk=yf.Ticker(ticker)
        if not tk.options: return []
        curr=sd["price"]; trend=sd["trend"]
        rows=[]
        exp=tk.options[0]
        try:
            exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<0 or days>10: return [] # فقط 10 أيام - تفاعل مباشر
            chain=tk.option_chain(exp)
            df_opt=chain.calls if trend=="BULL" else chain.puts
            if df_opt.empty: return []
            # فلتر حوت حقيقي مو تحوط
            df_opt=df_opt.copy()
            df_opt=df_opt[df_opt['lastPrice']>0.3] # عقد له قيمة
            df_opt=df_opt.dropna(subset=['volume','openInterest'])
            # حقيقي = VOL > OI*0.6 = دخول جديد - تحوط = OI كبير VOL صغير
            df_opt['is_real']=df_opt['volume']>df_opt['openInterest']*0.6
            df_opt_real=df_opt[df_opt['is_real']==True]
            if df_opt_real.empty: df_opt_real=df_opt # إذا مافي حقيقي خذ أفضل الموجود
            df_opt_real=df_opt_real.sort_values('volume', ascending=False).head(1)
            for _,r in df_opt_real.iterrows():
                strike=float(r['strike']); dist=(strike-curr)/curr*100
                if abs(dist)>4: continue
                # خداع: إذا CALL بعيد OTM +5% وهو طاير = تصريف
                if trend=="BULL" and dist>3.5: continue
                if trend=="BEAR" and dist<-3.5: continue
                vol=int(r['volume']); oi=int(r['openInterest'])
                # تأكد حوت حقيقي
                whale_type="تحوط" if vol<oi*0.4 else "دخول حقيقي" if vol>oi*0.8 else "مختلط"
                if whale_type=="تحوط": continue # استبعد التحوط - هذا اللي ورطنا في TSLA
                rows.append({
                    "ticker":ticker,"type":"CALL" if trend=="BULL" else "PUT",
                    "stock_now":curr,"strike":int(strike),"dist":dist,
                    "opt_price":float(r['lastPrice']),"vol":vol,"oi":oi,
                    "exp_short":exp_d.strftime("%m/%d"),"days":days,
                    "rsi":sd["rsi"],"ch1":sd["ch1"],"hour_ch":sd["hour_ch"],
                    "vwap":sd["vwap"],"trend":trend,"reason":sd["reason"],"whale":whale_type
                })
        except: pass
        return rows
    except: return []

# عرض
if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    enriched=[]
    for _,r in df.iterrows():
        ch1=float(r.get("ch1",0)); hour_ch=float(r.get("hour_ch",0)); rsi=float(r.get("rsi",50))
        score=50
        if r["type"]=="CALL":
            if hour_ch>=1: score+=25
            elif hour_ch>=0.5: score+=15
            if rsi>=55 and rsi<=68: score+=15
        else:
            if hour_ch<=-1: score+=25
            elif hour_ch<=-0.5: score+=15
            if rsi<=45 and rsi>=30: score+=15
        score=int(max(40,min(90,score)))
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
    st.info("📱 V53 واقعي - لا يعتمد 4 أيام - يعتمد تفاعل الآن - VWAP + زخم ساعة + حوت حقيقي")

if not final.empty:
    st.success(f"✅ {len(final)} عقد حقيقي - تفاعل مباشر - {ksa_str}")
    for _,w in final.head(4).iterrows():
        conf=int(w.get("confirm",60))
        border="#16a34a" if w.get("type")=="CALL" else "#dc2626"
        icon="🟢" if w.get("type")=="CALL" else "🔴"
        st.markdown(f"""<div style="background:#fff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;">
        <b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}% | {w.get('whale')} | VOL {int(w.get('vol',0))} OI {int(w.get('oi',0))}</b><br>
        {w.get('reason')}<br>
        <span style="font-size:11px;">سهم ${float(w.get('stock_now',0)):.2f} | ساعة {float(w.get('hour_ch',0)):+.1f}% | يوم {float(w.get('ch1',0)):+.1f}% | RSI {float(w.get('rsi',0)):.0f} | {w.get('exp_short')} {int(w.get('days'))}ي</span>
        </div>""", unsafe_allow_html=True)

if do_scan:
    tickers=["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR","AMD","AVGO"]
    with st.spinner("فحص واقعي - VWAP + زخم ساعة + استبعاد تحوط..."):
        rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futs={executor.submit(fetch_real, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res=fu.result()
                    if res: rows.extend(res)
                except: pass
    if rows:
        ndf=pd.DataFrame(rows)
        ndf=ndf.drop_duplicates(subset=["ticker"], keep="first")
        st.session_state.results=ndf
        st.rerun()
    else:
        st.warning("لا يوجد زخم حقيقي الآن - السوق عرضي أو تحوط فقط - لا تدخل - هذا هو الواقع")
        st.markdown("**TSLA أمس 252:** كان VOL 10k OI 25k = تحوط = V53 كان بيستبعده")

st.caption(f"V53 REAL | {ksa_str} | تفاعل مباشر VWAP + ساعة + VOL>OI*0.6 حوت حقيقي | يستبعد تحوط TSLA 252")
