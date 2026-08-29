import streamlit as st, yfinance as yf, pandas as pd, os, requests, math
from datetime import datetime
import pytz

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "13889370"
def send_tg(t):
    try:
        if not BOT_TOKEN: return
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id":CHAT_ID,"text":t,"parse_mode":"Markdown"}, timeout=10)
    except: pass

if "--scan" in os.sys.argv:
    tickers=["NVDA","TSLA","AAPL","SPY","QQQ","AMD","META","MSFT","PLTR","COIN","MSTR","GOOGL","AMZN","AVGO"]
    msgs=[]
    for t in tickers:
        try:
            tk=yf.Ticker(t)
            if not tk.options: continue
            for exp in tk.options[:2]:
                try:
                    df=tk.option_chain(exp).calls
                    for _,r in df.iterrows():
                        oi=r.get('openInterest',0); vol=r.get('volume',0); p=r.get('lastPrice',0)
                        if oi and vol and oi>vol*1.2 and vol>50 and 0.2<p<25:
                            msgs.append(f"💎 {t} {int(r['strike'])}C {exp} OI:{int(oi)} V:{int(vol)} ${p}")
                except: continue
        except: continue
    send_tg("👑 V600 فحص:\n\n" + ("\n".join(msgs[:20]) if msgs else "لا يوجد تجميع قوي (ويكند)"))
    os._exit(0)

st.set_page_config(layout="wide", page_title="Whale V600")
st.title("👑 رادار التجميع V600 - حوت 54")
st.caption("OI > Vol = تجميع حيتان قبل الانفجار")

min_oi = st.sidebar.slider("💎 اقل OI", 500, 20000, 3000)
min_vol = st.sidebar.slider("📊 اقل Vol", 10, 500, 30)
ticker_list = st.sidebar.multiselect("الشركات", ["NVDA","TSLA","AAPL","SPY","QQQ","AMD","META","MSFT","PLTR","COIN","MSTR","GOOGL","AMZN","NFLX","AVGO"], default=["NVDA","TSLA","SPY","QQQ","PLTR"])

if st.sidebar.button("🚀 فحص الآن", type="primary"):
    rows=[]
    bar=st.progress(0)
    status=st.empty()
    for i,t in enumerate(ticker_list):
        status.write(f"يفحص {t}... {i+1}/{len(ticker_list)}")
        bar.progress((i+1)/len(ticker_list))
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="2d")
            S=float(hist['Close'].iloc[-1]) if not hist.empty else 100
            if not tk.options: continue
            for exp in tk.options[:3]:
                try:
                    calls=tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        price=float(r.get('lastPrice',0) or 0)
                        strike=float(r['strike'])
                        if oi>=min_oi and vol>=min_vol:
                            ratio=oi/max(vol,1)
                            bw=abs(strike-S)/S*100
                            if ratio>1.2 and bw<10 and price>0.1:
                                state="💎 جاهز للانفجار" if ratio>2 and bw<5 else "👀 مراقبة"
                                rows.append({"Ticker":t,"Strike":strike,"Exp":exp,"S":round(S,1),"OI":oi,"Vol":vol,"OI/Vol":round(ratio,1),"Price":price,"BW%":round(bw,1),"حالة":state})
                except: continue
        except: continue
    bar.empty(); status.empty()
    if rows:
        df=pd.DataFrame(rows).sort_values("OI", ascending=False)
        st.success(f"✅ لقى {len(df)} عقد - {datetime.now(pytz.timezone('Asia/Riyadh')).strftime('%H:%M:%S')}")
        st.dataframe(df, use_container_width=True, height=600)
        if st.button("📤 ارسل لتلجرام"):
            txt="👑 *V600 جواهر:*\n\n"
            for _,r in df.head(10).iterrows():
                txt+=f"{r['Ticker']} {r['Strike']}C OI:{r['OI']} {r['حالة']}\n"
            send_tg(txt)
            st.toast("ارسل ✅")
    else:
        st.warning("😴 ما لقى تجميع بهذي الفلاتر - نزل OI الى 1000 و Vol الى 20 لأن اليوم ويكند والسوق مقفل")
        st.info("جرب يوم الاثنين وقت السوق - او خفف الفلاتر")
else:
    st.info("👈 من اليسار اختر الشركات واضغط 🚀 فحص الآن")
    st.caption("اليوم سبت - السوق مقفل عشان كذا Vol قليل - الفحص الحقيقي الاثنين 4:30 العصر")
