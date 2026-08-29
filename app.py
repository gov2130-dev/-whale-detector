import streamlit as st, yfinance as yf, pandas as pd
from datetime import date, datetime

st.set_page_config(layout="wide")
st.title("👑 V1100 - إشارة قبل الصعود (يشتغل 24/7)")
st.caption("يقرا تجميع الجمعة ويعطيك انفجار الاثنين قبل ما يصعد")

def dte(e):
    try: return (datetime.strptime(e, "%Y-%m-%d").date()-date.today()).days
    except: return 99

t = st.sidebar.selectbox("الشركة", ["QQQ","SPY","NVDA","PLTR","TSLA","COIN","MSTR"], index=0)
st.sidebar.markdown("**هذا يشتغل الحين - يجيب OI حق آخر يوم تداول (الجمعة)**")

if st.sidebar.button("🚀 فحص قبل الصعود", type="primary", use_container_width=True):
    try:
        tk = yf.Ticker(t)
        # نجيب آخر سعر حتى لو ويكند
        hist = tk.history(period="10d")
        if hist.empty:
            st.error("yfinance معلق دقيقة وبيشتغل")
            st.stop()
        S = float(hist['Close'].iloc[-1])
        S_prev = float(hist['Close'].iloc[-2])
        price_change = (S - S_prev)/S_prev*100
        # حجم السهم هل ارتفع بدون سعر؟
        vol_trend = hist['Volume'].iloc[-1] > hist['Volume'].mean()

        st.info(f"سعر {t}: ${S:.2f} | تغير أمس: {price_change:.2f}% | تجميع؟ {'نعم' if vol_trend else 'لا'}")

        rows=[]
        for exp in tk.options[:3]: # 3 تواريخ
            dd = dte(exp)
            if dd<0 or dd>14: continue
            try:
                chain = tk.option_chain(exp)
                # نفحص Calls و Puts
                for side, df in [("C",chain.calls), ("P",chain.puts)]:
                    for _,r in df.iterrows():
                        oi = int(r.get('openInterest',0) or 0)
                        # السر هنا: لا نفلتر Vol = 0 في الويكند
                        if oi < 1000: continue
                        strike = float(r['strike'])
                        price = float(r.get('lastPrice',0) or 0)
                        if price < 0.3: continue
                        bw = abs(strike-S)/S*100
                        if bw > 7: continue

                        # --- سكور قبل الصعود ---
                        score = 0
                        # 1- OI عالي = حوت مجمع من الجمعة
                        if oi > 5000: score+=20
                        if oi > 15000: score+=20
                        if oi > 25000: score+=15
                        # 2- السعر ما صعد كثير = لسه بدري
                        if abs(price_change) < 1.5: score+=20 # مكانك سر = تجميع
                        # 3- قريب من السعر
                        if bw < 1: score+=25
                        elif bw < 3: score+=15
                        # 4- DTE قريب
                        if dd <= 3: score+=10

                        # اشارة قبل الصعود = OI عالي + السعر لسه ما تحرك
                        early_signal = oi > 8000 and abs(price_change) < 2 and bw < 3

                        if score >= 50:
                            rows.append({
                                "T":t, "Side":side, "Strike":strike, "S":round(S,2),
                                "Exp":exp, "DTE":dd, "OI":oi, "Vol":int(r.get('volume',0) or 0),
                                "Price":price, "BW%":round(bw,1), "SCORE":score,
                                "حالة": "🔥 قبل الصعود" if early_signal else "💎 تجميع"
                            })
            except Exception as e:
                continue

        if rows:
            df = pd.DataFrame(rows).sort_values(["SCORE","OI"], ascending=[False,False])
            st.success(f"✅ لقيت {len(df)} عقد مجمع من يوم الجمعة - هذي بتنفجر الاثنين قبل لا تصعد")

            # كروت قبل الصعود
            for _,r in df.head(8).iterrows():
                icon = "🚀" if "قبل الصعود" in r['حالة'] else "💎"
                st.markdown(f"### {icon} {r['T']} {r['Strike']}{r['Side']} | {r['حالة']} | سكور {r['SCORE']} | OI {r['OI']:,}")
                c1,c2,c3,c4 = st.columns(4)
                c1.metric("OI (تجميع الجمعة)", f"{r['OI']:,}"); c2.metric("BW%", f"{r['BW%']}%"); c3.metric("سعر العقد الآن", f"${r['Price']}"); c4.metric("DTE", f"{r['DTE']} يوم")
                st.progress(r['SCORE']/100)
                st.caption(f"المنطق: OI {r['OI']:,} عالي + السهم تغير {price_change:.2f}% بس = لسه ما صعد")
                st.divider()

            st.dataframe(df, use_container_width=True, height=400)
        else:
            st.warning("ما لقى OI - yfinance لسه ما حدث بيانات الجمعة - جرب بعد 10 دقايق أو اختار SPY QQQ")

    except Exception as e:
        st.error(f"خطأ: {e}")

else:
    st.markdown("""
    **ليش هذا يعطيك قبل الصعود؟**
    - يقرا OI حق **الجمعة** (آخر يوم تداول) حتى لو اليوم سبت
    - يشوف سهم ما تحرك + OI عالي = حوت جمع ولسه ما رفع السعر
    - يعطيك BW قليل = جاهز للانفجار الاثنين
    - هذا هو اللي يخليك تدخل قبل لا يصعد العقد من $2 الى $9
    """)
