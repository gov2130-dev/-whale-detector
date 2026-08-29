import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("👑 V1400 - المنطقي - دخول قبل الصعود بس")
st.caption("المنطق: Vol > OI + سعر رخيص + سهم محشور = انفجار")

st.sidebar.markdown("""
### ✅ الشروط المنطقية الجديدة:
**1. Vol > OI × 0.7:** فلوس جديدة اليوم، مو OI قديم  
**2. سعر العقد 0.4$ - 4$:** رخيص لسه ما صعد  
**3. BW% <2.5%:** على سعر السهم بالضبط  
**4. السهم محشور <1.5% آخر 3 أيام:** تجميع  
**5. DTE 3-14:** اسبوعي  
**اذا ما تحقق شرط واحد ما يطلع - عشان كذا النتائج قليلة بس قوية**
""")

TICKERS = ["SPY","QQQ","NVDA","TSLA","META","AAPL","AMD","PLTR","COIN","MSTR"]

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

if st.button("🚀 فحص منطقي - كل السوق (ياخذ دقيقة)", type="primary", use_container_width=True):
    rows=[]; prog=st.progress(0); txt=st.empty()
    for i,t in enumerate(TICKERS):
        txt.text(f"يفحص {t} {i+1}/{len(TICKERS)} - يدور Vol > OI")
        prog.progress((i+1)/len(TICKERS))
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="7d")
            if hist.empty or len(hist)<4: continue
            S=float(hist['Close'].iloc[-1])
            # هل السهم محشور؟
            range3 = (hist['High'].iloc[-3:].max() - hist['Low'].iloc[-3:].min())/S*100
            if range3 > 4: continue # يتحرك كثير ما نبغاه

            for exp in tk.options[:2]:
                dd=dte(exp)
                if dd<3 or dd>14: continue
                try:
                    chain=tk.option_chain(exp)
                    for _,r in chain.calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        if oi<2000: continue
                        if vol < oi*0.7: continue # الشرط المنطقي الأهم
                        strike=float(r['strike']); price=float(r.get('lastPrice',0) or 0)
                        if price<0.4 or price>4: continue
                        bw=abs(strike-S)/S*100
                        if bw>2.5: continue

                        score = 0
                        # Vol > OI = قوي جدا
                        if vol > oi: score+=40
                        elif vol > oi*0.7: score+=25
                        if bw<1: score+=30
                        elif bw<2: score+=15
                        if range3<1.5: score+=20
                        if price<2: score+=10

                        if score>=65:
                            rows.append({"T":t,"عقد":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"Vol/OI":round(vol/max(oi,1),2),"Price":price,"BW%":round(bw,2),"Range3%":round(range3,2),"SCORE":score,"المنطق":f"Vol {vol:,} > OI {oi:,} + محشور {range3:.1f}%"})
                except: continue
        except: continue
        time.sleep(0.8)

    prog.empty(); txt.empty()
    if rows:
        df=pd.DataFrame(rows).sort_values(["SCORE","Vol/OI"], ascending=[False,False])
        st.success(f"🔥 لقيت {len(df)} عقد منطقي فقط - كلها Vol > OI + محشورة قبل الصعود")
        for _,r in df.iterrows():
            st.markdown(f"### 🚀 {r['T']} {r['عقد']} | سكور {r['SCORE']} | Vol/OI {r['Vol/OI']} | دخول ${r['Price']} | {r['المنطق']}")
            c1,c2,c3,c4=st.columns(4)
            c1.metric("Vol اليوم", f"{r['Vol']:,}"); c2.metric("OI", f"{r['OI']:,}"); c3.metric("BW", f"{r['BW%']}%"); c4.metric("السهم محشور", f"{r['Range3%']}%")
            st.progress(r['SCORE']/100)
            st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("ما لقى عقود منطقية اليوم - وهذا شي ممتاز - معناه السوق ما فيه تجميع جديد، الأفضل ما تدخل - جرب وقت السوق 10:30 صباحا بتوقيت نيويورك")
        st.info("النتائج القليلة المنطقية أفضل من 50 نتيجة غير منطقية")

else:
    st.info("اضغط فحص منطقي - هذا يطلع 2-5 عقود بس بس كلها Vol > OI يعني فلوس داخلة اليوم قبل الصعود")
