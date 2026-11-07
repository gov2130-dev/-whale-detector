import streamlit as st
import yfinance as yf
from datetime import datetime

st.title("🇺🇸 راصد الحيتان")
st.write("اضغط الزر عشان يفحص الأسهم الحين")

if st.button("🔍 افحص الآن"):
    with st.spinner("جاري فحص الأسهم... انتظر 30 ثانية"):
        for symbol in ["AAPL", "BABA", "AMZN", "NVDA", "TSLA", "GDX"]:
            try:
                ticker = yf.Ticker(symbol)
                price = ticker.info.get('currentPrice')
                st.write(f"**{symbol}**: ${price}")
                
                # نجيب اقرب انتهاء
                exp = ticker.options[0]
                chain = ticker.option_chain(exp)
                # نعرض اعلى 3 عقود من ناحية الفوليوم
                top = chain.calls.sort_values('volume', ascending=False).head(3)
                for _, row in top.iterrows():
                    if row['volume'] > 300:
                        st.success(f"{symbol} CALL {row['strike']} | سعر: ${row['lastPrice']:.2f} | فوليوم: {int(row['volume'])} | انتهاء: {exp}")
            except Exception as e:
                st.error(f"خطأ في {symbol}")

    st.success("✅ خلص الفحص")
