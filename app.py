import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime

st.set_page_config(layout="wide")
st.title("👑 V1700 - العودة للأصل - صيد الحيتان قبل الحركة")
st.caption("نرجع لفكرة الحوت: OI عالي + قريب + رخيص + محشور = قبل الانفجار")

st.sidebar.markdown("""
### 🎯 شروط الحوت الأصلية (قبل الحركة):
**1. OI > 12k:** حوت مجمع قديم  
**2. BW% <2%:** على السعر بالضبط  
**3. سعر 0.8$ - 4.5$:** لسه رخيص  
**4. Spread <15%:** يقدر الحوت يدخل  
**5. سهم محشور <2%:** تجميع قبل الطلعة  
**6. DTE 4-21 يوم:** وقت للانفجار
""")

@st.cache_data(ttl=900)
def whale_scan(ticker):
    tk=yf.Ticker(ticker)
    hist=tk.history(period="10d")
    if hist.empty: return pd.DataFrame(), 0, "ما فيه بيانات"
    S=float(hist['Close'].iloc[-1])
    # هل محشور؟
    rng=(hist['High'].iloc[-5:].max()-hist['Low'].iloc[-5:].min())/S*100
    
    rows=[]
    try:
        for exp in tk.options[:3]:
            dd=(datetime.strptime(exp, "%Y-%m-%d").date()-date.today()).days
            if dd<4 or dd>21: continue
            oc=tk.option_chain(exp)
            for _,r in oc.calls.iterrows():
                oi=int(r.get('openInterest',0) or 0)
                if oi<12000: continue
                strike=float(r['strike']); price=float(r.get('lastPrice',0) or 0)
                bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                if price<0.8 or price>4.5: continue
                bw=abs(strike-S)/S*100
                if bw>2.2: continue
                spread = (ask-bid)/price*100 if bid>0 and price>0 else 99
                if spread>15: continue
                if rng>2.5: continue

                score=0
                if oi>20000: score+=30
                elif oi>12000: score+=20
                if bw<0.8: score+=30
                elif bw<1.5: score+=20
                if price<2: score+=20
                if rng<1.2: score+=20

                if score>=60:
                    rows.append({"T":ticker,"عقد":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Price":price,"BW%":round(bw,2),"Spread%":round(spread,1),"Range%":round(rng,2),"SCORE":score,"المعنى":f"حوت مجمع {oi:,} عقد + لسه رخيص ${price} + على السعر"})
    except Exception as e:
        return pd.DataFrame(), S, str(e)
    return pd.DataFrame(rows).sort_values("SCORE", ascending=False), S, rng

t = st.sidebar.selectbox("اختار حوت", ["QQQ","SPY","NVDA","TSLA","META","PLTR"], index=0)
if st.sidebar.button("🚀 فك بلوك"):
    st.cache_data.clear(); st.success("فكيت الكاش - الحين افحص")

if st.sidebar.button("🎯 صيد الحوت قبل الحركة", type="primary", use_container_width=True):
    df,S,rng = whale_scan(t)
    if df.empty:
        st.warning(f"{t} سعره ${S} محشور {rng:.2f}% - ما فيه حوت مجمع قريب ورخيص اليوم - هذا منطقي - مو كل يوم فيه حوت")
        st.info("جرب SPY و QQQ - دايم فيها حيتان حتى الويكند")
    else:
        st.success(f"🐋 لقيت {len(df)} حوت مجمع من أيام ولسه رخيص - قبل ما يتحرك")
        for _,r in df.head(6).iterrows():
            st.markdown(f"### 🐋 {r['T']} {r['عقد']} | سكور {r['SCORE']} | دخول ${r['Price']} | {r['المعنى']}")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("OI تجميع", f"{r['OI']:,}"); c2.metric("BW قريب", f"{r['BW%']}%"); c3.metric("Spread سيولة", f"{r['Spread%']}%"); c4.metric("محشور", f"{r['Range%']}%")
            st.progress(r['SCORE']/100)
            st.divider()
        st.dataframe(df, use_container_width=True)

else:
    st.info("👈 هذا هو الأصل يا حوت - اضغط صيد الحوت - شركة واحدة عشان ما ننبلّك - هذا يجيبها قبل ما تتحرك مو بعد")    st.success("تم فك الكاش - جرب الحين")

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
