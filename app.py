import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("👑 V1500 - المنطقي 24/7")
is_weekend = date.today().weekday() >= 5
st.caption(f"اليوم {'سبت - يجيب تجميع الجمعة' if is_weekend else 'سوق فاتح - يجيب Vol اليوم'}")

st.sidebar.markdown("""
### ✅ المنطق:
**لو سوق فاتح:** Vol > OI = فلوس جديدة  
**لو ويكند:** OI > 12k + BW<2% + سعر رخيص + سهم محشور = تجميع الجمعة قبل صعود الاثنين
""")

TICKERS = ["SPY","QQQ","NVDA","TSLA","META","AAPL","AMD","PLTR","COIN","MSTR","HOOD"]

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

if st.button(f"🚀 فحص {'تجميع الجمعة' if is_weekend else 'Vol اليوم'}", type="primary", use_container_width=True):
    rows=[]; bar=st.progress(0)
    for i,t in enumerate(TICKERS):
        bar.progress((i+1)/len(TICKERS))
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="7d")
            if hist.empty: continue
            S=float(hist['Close'].iloc[-1])
            range3=(hist['High'].iloc[-3:].max()-hist['Low'].iloc[-3:].min())/S*100
            if range3>3.5: continue # يتحرك كثير

            for exp in tk.options[:2]:
                dd=dte(exp)
                if dd<2 or dd>14: continue
                try:
                    calls=tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        oi=int(r.get('openInterest',0) or 0)
                        vol=int(r.get('volume',0) or 0)
                        price=float(r.get('lastPrice',0) or 0)
                        strike=float(r['strike'])
                        if price<0.3 or price>5: continue
                        bw=abs(strike-S)/S*100
                        if bw>2.5: continue
                        if oi<8000: continue

                        # المنطق المزدوج
                        if is_weekend:
                            # ويكند: نبي OI عالي + محشور + رخيص = قبل الصعود
                            if range3>2: continue
                            score = (20 if oi>15000 else 0) + (25 if bw<1.2 else 10) + (20 if price<2 else 0) + (20 if range3<1.2 else 10)
                            if score>=50:
                                rows.append({"T":t,"عقد":f"{strike}C","S":S,"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"Price":price,"BW%":round(bw,2),"Range%":round(range3,2),"SCORE":score,"النوع":"💎 تجميع الجمعة"})
                        else:
                            # سوق فاتح: Vol > OI
                            if vol < oi*0.6: continue
                            score = 40 if vol>oi else 25
                            rows.append({"T":t,"عقد":f"{strike}C","S":S,"Exp":exp,"DTE":dd,"OI":oi,"Vol":vol,"Price":price,"BW%":round(bw,2),"SCORE":score,"النوع":"🚀 Vol>OI اليوم"})
                except: continue
        except: continue
        time.sleep(0.6)

    bar.empty()
    if rows:
        df=pd.DataFrame(rows).sort_values("SCORE", ascending=False)
        st.success(f"✅ لقيت {len(df)} عقد منطقي - {'تجميع الجمعة قبل صعود الاثنين' if is_weekend else 'فلوس جديدة اليوم'}")
        for _,r in df.head(15).iterrows():
            st.markdown(f"### {r['النوع']} | {r['T']} {r['عقد']} | دخول ${r['Price']} | BW {r['BW%']}% | OI {r['OI']:,}")
            c1,c2,c3=st.columns(3)
            c1.metric("OI", f"{r['OI']:,}"); c2.metric("BW% (قريب)", f"{r['BW%']}%"); c3.metric("محشور", f"{r.get('Range%',0)}%")
            st.divider()
        st.dataframe(df, use_container_width=True)
    else:
        st.error("ما لقى - yfinance بلوك مؤقت - انتظر دقيقتين وحدث الصفحة")
else:
    st.info(f"👈 اضغط فحص - الحين هو { 'ويكند فبيجيب تجميع الجمعة' if is_weekend else 'سوق فاتح فبيجيب Vol اليوم'} - هذا منطقي 100%")
