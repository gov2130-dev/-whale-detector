import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime

st.set_page_config(layout="wide")
st.title("👑 V820 - فحص مباشر + تشخيص")

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

t = st.sidebar.selectbox("الشركة", ["SPY","QQQ","NVDA"], index=0)
st.sidebar.write("اختار شركة وحدة بس عشان yfinance ما يعلق")

if st.sidebar.button("🚀 افحص الآن", type="primary", use_container_width=True):
    st.write(f"جاري فحص {t}...")
    try:
        tk = yf.Ticker(t)
        hist = tk.history(period="5d")
        if hist.empty:
            st.error("yfinance ما رجع سعر - جرب بعد دقيقة (بلوك مؤقت)")
            st.stop()
        S = float(hist['Close'].iloc[-1])
        st.success(f"سعر {t} الآن: ${S:.2f} - التاريخ: {date.today()} - DTE اليوم ويكند")

        exps = tk.options
        if not exps:
            st.error("ما فيه عقود - yfinance معلق في الويكند")
            st.stop()

        st.write(f"تواريخ الانتهاء المتاحة: {exps[:5]}")

        rows=[]
        for exp in exps[:2]: # تاريخين بس
            dd = dte(exp)
            st.write(f"--- يفحص {exp} (DTE={dd}) ---")
            try:
                chain = tk.option_chain(exp)
                calls = chain.calls
                st.write(f"لقي {len(calls)} عقد Call في {exp}")
                # اعرض بدون فلتر اول
                for _, r in calls.head(30).iterrows():
                    oi = int(r.get('openInterest',0) or 0)
                    strike = float(r['strike'])
                    bw = abs(strike-S)/S*100
                    if oi>100 and bw<10: # فلتر خفيف جدا
                        rows.append({"T":t,"Strike":strike,"S":round(S,2),"Exp":exp,"DTE":dd,"OI":oi,"Vol":int(r.get('volume',0) or 0),"Price":float(r.get('lastPrice',0) or 0),"BW%":round(bw,1)})
            except Exception as e:
                st.warning(f"ما قدر يقرا {exp}: {e}")
                continue

        if rows:
            df = pd.DataFrame(rows).sort_values("OI", ascending=False)
            st.success(f"✅ لقيت {len(df)} عقد شغال حتى في الويكند")
            st.dataframe(df.head(25), use_container_width=True)

            best = df.iloc[0]
            st.markdown(f"## 🔥 أقوى تجميع: {best['T']} {best['Strike']}C OI {best['OI']} BW {best['BW%']}%")
        else:
            st.error("لقي العقود بس كلها OI صفر - لأن اليوم السبت. الاثنين بيطلع كل شي")

    except Exception as e:
        st.error(f"خطأ عام: {e}")
else:
    st.info("اضغط افحص الآن - SPY لحاله - هذا الكود يوريك كل شي حتى لو السوق مقفل")
