import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="V79 فحص دقيق TSLA", layout="wide")
st.title("🔍 V79 - ليش الشمعة المطلوبة ما طلعت؟ TSLA 30دق")

sym = st.text_input("السهم", "TSLA")
code = st.selectbox("الفريم", ["30m","15m","1h","5m","1d"], index=0)
period_map = {"1m":"1d","5m":"5d","15m":"10d","30m":"10d","1h":"20d","1d":"60d"}

if st.button(f"افحص {sym} بالتفصيل"):
    tk = yf.Ticker(sym)
    df = tk.history(period=period_map[code], interval=code)
    st.write(f"آخر 5 شموع في الشارت - فريم {code}:")

    rows=[]
    for i in range(max(0,len(df)-5), len(df)):
        c = df.iloc[i]
        prev = df.iloc[i-1] if i>0 else c
        body = abs(c['Close']-c['Open'])
        upper = c['High'] - max(c['Close'],c['Open'])
        lower = min(c['Close'],c['Open']) - c['Low']
        total = c['High']-c['Low']
        tail_ratio = lower/body if body!=0 else 0
        vol_ratio = c['Volume']/prev['Volume'] if prev['Volume']!=0 else 0

        rows.append({
            "وقت": str(c.name)[5:16],
            "إغلاق": f"{c['Close']:.2f}",
            "ذيل سفلي": f"{lower:.2f} ({tail_ratio:.1f}x)",
            "جسم": f"{body:.2f}",
            "فوليوم": f"{c['Volume']:,.0f}",
            "فوليوم/السابق": f"{vol_ratio:.2f}x {'✅' if vol_ratio>1 else '❌'}",
            "هل مطرقة؟": "✅" if tail_ratio>=1.5 and body<=total*0.5 else "❌",
            "قمة": f"{c['High']:.2f}",
            "قاع": f"{c['Low']:.2f}"
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # فحص آخر 3 شموع حسب شرطك
    c_prev = df.iloc[-3]; c_ham = df.iloc[-2]; c_next = df.iloc[-1]
    body = abs(c_ham['Close']-c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    total = c_ham['High']-c_ham['Low']

    st.markdown("### فحص شرطك على آخر 3 شموع مغلقة:")
    st.write(f"1- شمعة المطرقة: {c_ham.name} إغلاق {c_ham['Close']:.2f} ذيل سفلي {lower/body:.1f}x")
    st.write(f" - شرط ذيل طويل >=1.5x: {'✅' if lower/body>=1.5 else '❌'} ({lower/body:.1f}x)")
    st.write(f" - شرط فوليوم أعلى من السابق: {'✅' if c_ham['Volume']>c_prev['Volume'] else '❌'} ({c_ham['Volume']:,.0f} vs {c_prev['Volume']:,.0f})")

    st.write(f"2- شمعة التأكيد: {c_next.name} إغلاق {c_next['Close']:.2f}")
    st.write(f" - شرطك الحالي (إغلاق فوق قمة المطرقة {c_ham['High']:.2f}): {'✅' if c_next['Close']>c_ham['High'] else '❌'} ({c_next['Close']:.2f} vs {c_ham['High']:.2f})")
    st.write(f" - شرط مخفف (إغلاق فوق إغلاق المطرقة {c_ham['Close']:.2f}): {'✅' if c_next['Close']>c_ham['Close'] else '❌'}")

    st.warning("صورتك TSLA 30دق: شمعة التأكيد ما قفلت فوق قمة المطرقة 388.50، قفلت 384.14 عشان كذا ما طلعت في النتائج")

    st.markdown("### تبغى أخفف شرط التأكيد؟")
    st.info("الحل: بدل ما يكون التأكيد فوق القمة، نخليه فوق الإغلاق فقط + نسمح أن التأكيد يجي خلال شمعتين مو شمعة وحدة. قل لي نطبقها؟")
