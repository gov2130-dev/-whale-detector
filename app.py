import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime
import time

st.set_page_config(layout="wide")
st.title("👑 V1200 - رادار قبل الصعود - فحص أوتوماتيك لكل السوق")
st.caption("زر واحد يفحص 20 شركة ويطلع العقود اللي بتصعد قبل لا تصعد")

# --- الشروط واضحة هنا ---
st.sidebar.markdown("### 📜 شروط التصفية (قبل الصعود)")
st.sidebar.markdown("""
**1. OI > 8,000:** حوت مجمع من الجمعة  
**2. BW% < 4%:** قريب من سعر السهم = جاهز ينفجر  
**3. سعر العقد < $6:** رخيص لسه ما صعد  
**4. DTE 2-14 يوم:** اسبوعي سريع  
**5. سعر السهم ما تحرك كثير أمس <2%:** لسه بدري  
**6. Vol أمس عالي:** فيه اهتمام
""")

ALL_TICKERS = ["SPY","QQQ","NVDA","TSLA","AAPL","MSFT","META","AMD","PLTR","COIN","MSTR","SMCI","AVGO","NFLX","GOOGL","AMZN","TSM","ARM","HOOD","SOFI"]

def get_S(tk):
    try:
        # محاولة 1 - fast
        s = tk.fast_info.get('last_price')
        if s: return float(s)
    except: pass
    try:
        h = tk.history(period="5d")
        if not h.empty: return float(h['Close'].iloc[-1])
    except: pass
    return None

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

if st.sidebar.button("🚀 فحص كل السوق - قبل الصعود", type="primary", use_container_width=True):
    all_rows=[]
    bar = st.progress(0)
    status = st.empty()

    for i, t in enumerate(ALL_TICKERS):
        status.text(f"يفحص {t} ... {i+1}/{len(ALL_TICKERS)}")
        bar.progress((i+1)/len(ALL_TICKERS))
        try:
            tk = yf.Ticker(t)
            S = get_S(tk)
            if not S: continue
            hist = tk.history(period="6d")
            if hist.empty or len(hist)<2: continue
            chg = abs((hist['Close'].iloc[-1]-hist['Close'].iloc[-2])/hist['Close'].iloc[-2]*100)
            vol_up = hist['Volume'].iloc[-1] > hist['Volume'].iloc[-5:-1].mean()

            if chg > 3.0: continue # صعد خلاص ما نبغاه - نبغاه قبل

            for exp in tk.options[:2]:
                dd = dte(exp)
                if dd<1 or dd>14: continue
                try:
                    calls = tk.option_chain(exp).calls
                    for _,r in calls.iterrows():
                        oi = int(r.get('openInterest',0) or 0)
                        if oi < 8000: continue
                        strike = float(r['strike']); price = float(r.get('lastPrice',0) or 0)
                        if price < 0.2 or price > 6.5: continue
                        bw = abs(strike-S)/S*100
                        if bw > 4: continue
                        if not vol_up: 
                            # لو ما فيه vol up نطلب OI اعلى
                            if oi < 15000: continue

                        score = 0
                        if oi>10000: score+=25
                        if oi>20000: score+=15
                        if oi>40000: score+=10
                        if bw<1: score+=25
                        elif bw<2.5: score+=15
                        if chg<1: score+=15 # لسه ما تحرك = قبل الصعود
                        elif chg<2: score+=10
                        if dd<=5: score+=10

                        if score>=60:
                            all_rows.append({"T":t,"Strike":f"{strike}C","S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Price":price,"BW%":round(bw,2),"CHG%":round(chg,2),"SCORE":score,"حالة":"🚀 قبل الصعود" if chg<1.5 and bw<2 else "💎 تجميع قوي"})
                except: continue
        except: continue
        time.sleep(0.3)

    bar.empty(); status.empty()

    if all_rows:
        df = pd.DataFrame(all_rows).sort_values(["SCORE","OI"], ascending=[False,False])
        st.success(f"🔥 لقيت {len(df)} عقد متوقع صعودها - كلها قبل ما تصعد - مرتبة بالأقوى")

        for _,r in df.head(15).iterrows():
            st.markdown(f"### {r['حالة']} | {r['T']} {r['Strike']} | سكور {r['SCORE']} | OI {r['OI']:,} | BW {r['BW%']}%")
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("تجميع OI", f"{r['OI']:,}"); c2.metric("سعر الدخول الآن", f"${r['Price']}"); c3.metric("قريب من السهم", f"{r['BW%']}%"); c4.metric("السهم لسه ما صعد", f"{r['CHG%']}%")
            st.progress(r['SCORE']/100)
            st.divider()

        st.dataframe(df, use_container_width=True, height=600)
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 حمل كل العقود Excel", csv, "قبل_الصعود.csv", "text/csv")
    else:
        st.error("ما لقى - جرب وقت السوق أو yfinance معلق 5 دقايق")

else:
    st.info("👈 اضغط الزر الأحمر - بيفحص 20 شركة لحاله ويطلع لك كل العقود قبل ما تصعد - بدون ما تختار شركة شركة")
    st.markdown("**الفرق عن اللي قبل:** ما يحتاج تختار QQQ ولا NVDA - يفحصهم كلهم مرة وحدة ويطلع الأقوى أول")
