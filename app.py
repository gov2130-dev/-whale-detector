import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(layout="wide")
st.title("Whale V6.7 - تنبيه واتساب")
st.caption(f"Live: {datetime.now().strftime('%H:%M:%S')}")

stocks = ["TSLA","NVDA","AAPL","SPY","QQQ","MSFT","AMZN","META","AMD","NFLX"]
all_data = []
for t in stocks:
    try:
        s = yf.Ticker(t)
        if not s.options: continue
        for exp in s.options[:1]:
            chain = s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                f = df[df["premium"]>100000]
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    all_data.append(f)
    except: continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(30)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum

    if is_bearish:
        st.error(f"🔴 BEARISH PUT ${put_sum:,.0f}")
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

    # تنبيه الحيتان الكبار
    whales = final[final['premium'] > 2000000]
    if not whales.empty:
        st.balloons()
        for _, w in whales.head(3).iterrows():
            msg = f"🐋 تنبيه حوت: {w['ticker']} {w['signal']} Strike {w['strike']} بمبلغ ${w['premium']:,.0f} القرار: {w['القرار']}"
            wa_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
            st.warning(msg)
            st.link_button(f"ارسل تنبيه {w['ticker']} واتساب", wa_link, use_container_width=True)

    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار"]], use_container_width=True)
else:
    st.warning("Market Closed")
