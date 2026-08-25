import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(layout="wide")
st.title("Whale V7.0 - Fixed")

# تحديث تلقائي بدون ما يعلق الصفحة
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)
st.sidebar.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
st.sidebar.caption("يتحدث تلقائيا كل 60 ثانية")

stocks = ["TSLA","NVDA","AAPL","SPY","QQQ","MSFT","AMZN","META","AMD","NFLX"]
all_data = []

with st.spinner("جاري صيد الحيتان..."):
    for t in stocks:
        try:
            s = yf.Ticker(t)
            if not s.options: continue
            exp = s.options[0]
            chain = s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                f = df[df["premium"]>100000].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    all_data.append(f)
        except Exception as e:
            continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(30)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum

    if is_bearish:
        st.error(f"🔴 BEARISH PUT ${put_sum:,.0f} > CALL ${call_sum:,.0f}")
    else:
        st.success(f"🟢 BULLISH CALL ${call_sum:,.0f}")

    def get_decision(row):
        prem = row['premium']
        is_put = 'PUT' in row['signal']
        if is_bearish:
            if is_put and prem > 1500000: return "✅ ادخل مع الحوت"
            if is_put: return "✔️ ادخل"
            if not is_put and prem > 2500000: return "⚠️ حوت قوي عكس السوق"
            return "❌ لا تدخل"
        else:
            if not is_put and prem > 1500000: return "✅ ادخل"
            if not is_put: return "✔️ ادخل"
            return "❌ لا تدخل"

    final['القرار'] = final.apply(get_decision, axis=1)

    big_whales = final[final['premium'] > 5000000]
    if not big_whales.empty:
        st.balloons()
        st.markdown("""
        <audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-10.mp3" type="audio/mpeg"></audio>
        <h3 style='color:red;text-align:center'>🚨 حوت فوق 5 مليون! 🚨</h3>
        """, unsafe_allow_html=True)

    for _, w in final[final['premium']>2000000].head(3).iterrows():
        msg = f"🐋 {w['ticker']} {w['signal']} {w['strike']} ${w['premium']:,.0f}"
        wa = f"https://wa.me/?text={urllib.parse.quote(msg)}"
        st.warning(f"{msg} - {w['القرار']}")
        st.link_button(f"📱 واتساب {w['ticker']}", wa)

    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار"]], use_container_width=True)
else:
    st.warning("السوق مقفل الآن أو yfinance معلق - جرب تحديث الصفحة")
    st.info("السوق الأمريكي يفتح 4:30 العصر بتوقيت السعودية")
