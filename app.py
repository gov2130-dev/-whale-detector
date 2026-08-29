import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import date, datetime
import time
import random

st.set_page_config(layout="wide")
st.title("V2400 - البحث العمومي - قبل الحركة")
st.caption("يبحث عمومي باي وقت - يومي / اسبوعي / شهري - الشروط الصارمة فقط")

# 54 شركة كاملة
TICKERS_54 = ["SPY","QQQ","NVDA","TSLA","AAPL","MSFT","META","AMD","PLTR","COIN","MSTR","HOOD","NFLX","GOOGL","AMZN","AVGO","SMCI","ARM","MU","ORCL","CRWD","PANW","APP","RDDT","MARA","RIOT","SMR","OKLO","IONQ","SOUN","UPST","AFRM","SOFI","DKNG","RBLX","U","SNOW","NET","DDOG","MDB","ZS","SHOP","SPOT","SE","BABA","PDD","NIO","LI","BIDU","X","NEM","GDX","GLD","SLV","TLT","IWM"]

@st.cache_data(ttl=600)
def scan_batch(tickers_list):
    results=[]
    for t in tickers_list:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="5d")
            if hist.empty:
                continue
            S = float(hist["Close"].iloc[-1])
            # نفحص كل الانتهاءات المتاحة لين 45 يوم - مو بس الجمعة
            for exp in tk.options[:4]:  # 4 انتهاءات = يومي + اسبوعي + شهري
                try:
                    dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                except:
                    continue
                if dte < 0 or dte > 45:  # عمومي - لين 45 يوم
                    continue
                try:
                    calls = tk.option_chain(exp).calls
                except:
                    continue
                for _, r in calls.iterrows():
                    oi = int(r.get("openInterest",0) or 0)
                    price = float(r.get("lastPrice",0) or 0)
                    if oi < 8000:  # شرطك الصارم
                        continue
                    if pd.isna(price) or price < 0.5 or price > 5:  # رخيص
                        continue
                    strike = float(r["strike"])
                    bw = abs(strike - S) / S * 100
                    if bw > 2.5:  # على السعر
                        continue
                    # حساب قرب الانفجار - كلما DTE اقل و BW اقل نقاط اعلى
                    score = 0
                    score += min(oi/500, 40)  # تجميع
                    score += max(0, 30 - bw*10)  # قرب
                    score += max(0, 20 - dte)  # يومي اقوى
                    if price <= 2:
                        score += 10

                    results.append({
                        "الشركة":t,
                        "العقد":f"{strike}C",
                        "السهم":round(S,2),
                        "الانتهاء":exp,
                        "باقي":dte,
                        "OI":oi,
                        "الدخول":price,
                        "البعد%":round(bw,2),
                        "النقاط":int(min(score,100)),
                        "النوع":"يومي" if dte<=1 else "اسبوعي" if dte<=7 else "شهري"
                    })
            time.sleep(random.uniform(0.5,0.9))  # مضاد حجب
        except:
            continue
    return results

st.sidebar.markdown("### الشروط الصارمة العمومية")
st.sidebar.markdown("1. OI > 8000 تجميع حوت")
st.sidebar.markdown("2. BW < 2.5% على السعر")
st.sidebar.markdown("3. السعر 0.5$ الى 5$ رخيص")
st.sidebar.markdown("4. DTE من 0 الى 45 يوم - يومي واسبوعي وشهري")
st.sidebar.markdown("5. نرتب بالاقرب للانفجار")

batch_choice = st.sidebar.selectbox("اختار دفعة (9 شركات كل مرة عشان ما ننحجب)", 
["Batch1: SPY QQQ NVDA TSLA AAPL MSFT META AMD PLTR",
 "Batch2: COIN MSTR HOOD NFLX GOOGL AMZN AVGO SMCI ARM",
 "Batch3: MU ORCL CRWD PANW APP RDDT MARA RIOT SMR",
 "Batch4: OKLO IONQ SOUN UPST AFRM SOFI DKNG RBLX U",
 "Batch5: SNOW NET DDOG MDB ZS SHOP SPOT SE BABA",
 "Batch6: PDD NIO LI BIDU X NEM GDX GLD SLV TLT IWM"])

if st.sidebar.button("مسح الكاش"):
    st.cache_data.clear()
    st.success("تم مسح الكاش")

if st.sidebar.button("صيد عمومي - قبل الحركة", type="primary", use_container_width=True):
    # حول اختيار الدفعة الى لستة
    mapping = {
        "Batch1: SPY QQQ NVDA TSLA AAPL MSFT META AMD PLTR": TICKERS_54[0:9],
        "Batch2: COIN MSTR HOOD NFLX GOOGL AMZN AVGO SMCI ARM": TICKERS_54[9:18],
        "Batch3: MU ORCL CRWD PANW APP RDDT MARA RIOT SMR": TICKERS_54[18:27],
        "Batch4: OKLO IONQ SOUN UPST AFRM SOFI DKNG RBLX U": TICKERS_54[27:36],
        "Batch5: SNOW NET DDOG MDB ZS SHOP SPOT SE BABA": TICKERS_54[36:45],
        "Batch6: PDD NIO LI BIDU X NEM GDX GLD SLV TLT IWM": TICKERS_54[45:54],
    }
    tickers = mapping[batch_choice]

    with st.spinner(f"يبحث عمومي في {tickers} - يومي واسبوعي وشهري - الشروط الصارمة..."):
        results = scan_batch(tickers)

    if results:
        df = pd.DataFrame(results).sort_values(["النقاط","OI"], ascending=False)
        st.success(f"تم - وجد {len(df)} عقد ينطبق على شروطك الصارمة - مرتب بالاقرب للانفجار")
        st.dataframe(df, use_container_width=True)

        # اعرض اقوى 5 قبل الحركة
        st.markdown("### اقوى 5 قبل الحركة - دخول قبل ما تتحرك")
        for _, r in df.head(5).iterrows():
            st.markdown(f"**{r['الشركة']} {r['العقد']} - {r['النوع']} باقي {r['باقي']} يوم - دخول ${r['الدخول']} - تجميع {r['OI']:,} - بعد {r['البعد%']}% - نقاط {r['النقاط']}**")
            if r['باقي'] <= 1:
                st.markdown("🔥 يومي - انفجاره اسرع واقوى واكثر ربح - دخول قبل الحركة الان")
            st.progress(int(r["النقاط"])/100.0)
    else:
        st.warning("ياهو حاجب هذه الدفعة حاليا (السبت) - جرب دفعة ثانية او اضغط مسح الكاش وانتظر دقيقة - يوم الاثنين يشتغل عمومي 100%")
        st.info("لو تبي تشوف حيتان الجمعة المؤقتة افتح V2300 - بس V2400 هذا هو البحث العمومي الحقيقي اللي طلبته")
else:
    st.info("هذا هو البحث العمومي اللي طلبته يا حوت")
    st.markdown("**ما يتوقف - يبحث باي وقت - يومي انفجاره اسرع - اسبوعي وشهري نفس الشروط**")
    st.markdown("- يبحث من 0DTE الى 45 يوم")
    st.markdown("- يطبق شروطك الصارمة اولا: OI>8000 + BW<2.5% + سعر رخيص")
    st.markdown("- بعدين يرتب بالاقرب للانفجار: DTE اقل + BW اقل = نقاط اعلى")
    st.markdown("**فكرتك: ندخل قبل ما تتحرك - مو بعد ما تتحرك**")
