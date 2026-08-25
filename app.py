import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(layout="wide")
st.title("Whale Detector V6.6 - مع القرار")
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
                    f["expiry"]=exp
                    all_data.append(f)
    except: continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(30)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    
    is_bearish = put_sum > call_sum
    if is_bearish:
        st.error(f"🔴 BEARISH - السوق هابط PUT ${put_sum:,.0f}")
    else:
        st.success(f"🟢 BULLISH - السوق صاعد CALL ${call_sum:,.0f}")

    # عمود القرار الجديد
    def get_decision(row):
        prem = row['premium']
        is_put = 'PUT' in row['signal']
        if is_bearish:
            if is_put and prem > 1500000: return "✅ ادخل مع الحوت"
            if is_put: return "✔️ ادخل"
            if not is_put and prem > 2500000: return "⚠️ حوت قوي عكس السوق"
            return "❌ لا تدخل عكس السوق"
        else:
            if not is_put and prem > 1500000: return "✅ ادخل مع الحوت"
            if not is_put: return "✔️ ادخل"
            return "❌ لا تدخل عكس السوق"

    final['القرار'] = final.apply(get_decision, axis=1)
    
    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار"]], use_container_width=True)
else:
    st.warning("Market Closed")
