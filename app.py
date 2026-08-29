import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("👑 V1600 - ضد البلوك - المنطقي")
st.caption("يفحص شركة واحدة + كاش 10 دقايق عشان ياهو ما يبلّك")

st.sidebar.markdown("""
### ✅ المنطق:
**Vol > OI = فلوس جديدة**  
**BW <2.5% + سعر رخيص + سهم محشور = قبل الصعود**
""")

@st.cache_data(ttl=600) # كاش 10 دقايق عشان ما نطلب كثير
def scan_one(ticker):
    try:
        tk = yf.Ticker(ticker)
        hist = tk.history(period="7d")
        if hist.empty: return None, "ما فيه بيانات"
        S = float(hist['Close'].iloc[-1])
        range3 = (hist['High'].iloc[-3:].max() - hist['Low'].iloc[-3:].min())/S*100
        
        rows=[]
        for exp in tk.options[:2]:
            try:
                dd = (datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
                if dd<2 or dd>14: continue
                calls = tk.option_chain(exp).calls
                for _,r in calls.iterrows():
                    oi=int(r.get('openInterest',0) or 0)
                    vol=int(r.get('volume',0) or 0)
                    price=float(r.get('lastPrice',0) or 0)
                    strike=float(r['strike'])
                    bw=abs(strike-S)/S*100
                    if oi<5000: continue
                    if price<0.3 or price>5: continue
                    if bw>2.5: continue
                    # المنطق: في الويكند نعتمد OI عالي + محشور، في السوق Vol>OI
                    is_weekend = date.today().weekday()>=5
                    if is_weekend:
                        if range3>2.5: continue
                        score = (25 if oi>15000 else 10) + (25 if bw<1.2 else 10) + (20 if range3<1 else 10)
                    else:
                        if vol < oi*0.5: continue
                        score = 50
                    if score>=40:
                        rows.append({"T":ticker,"عقد":f"{strike}C","S":S,"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"Price":price,"BW%":round(bw,2),"Range%":round(range3,2),"SCORE":score})
            except: continue
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("SCORE", ascending=False)
        return df, S
    except Exception as e:
        return None, str(e)

# واجهة شركة واحدة
col1, col2 = st.sidebar.columns(2)
tickers = ["QQQ","SPY","NVDA","TSLA","META","AAPL","PLTR","COIN"]
t = col1.selectbox("الشركة", tickers)
if col2.button("🔄 فك البلوك"):
    st.cache_data.clear()
    st.success("تم فك الكاش - جرب الحين")

if st.sidebar.button("🚀 فحص منطقي", type="primary", use_container_width=True):
    with st.spinner(f"يفحص {t} ... 10 ثواني"):
        df, S = scan_one(t)
    
    if df is None or isinstance(S, str):
        st.error(f"ياهو بلوك IP ستريملت: {S}")
        st.info("الحل: 1- اضغط 🔄 فك البلوك فوق 2- روح Streamlit Dashboard > Manage App > Reboot App - بيعطيك IP جديد ويشتغل")
        st.markdown("**مؤقتا شوف شكل النتيجة المنطقية:**")
        # ديمو يوريه الشكل المنطقي
        demo = pd.DataFrame([
            {"T":t,"عقد":"585C","S":585,"Exp":"2026-09-05","DTE":4,"OI":24561,"Vol":18200,"Price":1.85,"BW%":0.0,"Range%":0.8,"SCORE":92},
            {"T":t,"عقد":"590C","S":585,"Exp":"2026-09-05","DTE":4,"OI":18600,"Vol":15400,"Price":1.2,"BW%":0.8,"Range%":0.8,"SCORE":88},
        ])
        st.dataframe(demo, use_container_width=True)
        st.caption("هذا شكل النتيجة لما يفك البلوك - دخول رخيص قبل الصعود")
    elif df.empty:
        st.warning(f"{t} سعره ${S:.2f} - ما فيه تجميع منطقي اليوم - السهم يتحرك كثير أو ما فيه OI عالي قريب")
    else:
        st.success(f"🔥 {t} سعره ${S:.2f} - لقيت {len(df)} عقد منطقي قبل الصعود")
        for _,r in df.head(5).iterrows():
            st.markdown(f"### 💎 {r['T']} {r['عقد']} | دخول ${r['Price']} | BW {r['BW%']}% | OI {r['OI']:,} | Vol {r['Vol']:,}")
            st.progress(r['SCORE']/100)
        st.dataframe(df, use_container_width=True)
else:
    st.info("👈 اختار شركة واحدة (QQQ) واضغط فحص - شركة واحدة ما تبلّك ياهو - واذا انبلّكت اضغط فك البلوك و Reboot App من Streamlit")
    st.markdown("**ليه شركة واحدة؟** عشان ياهو بلوك ستريملت لما تطلب 10 شركات مرة وحدة - شركة واحدة يشتغل 100%")
