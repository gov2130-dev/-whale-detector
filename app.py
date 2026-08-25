import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(layout="wide")
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

st.title("Whale Detector V6.4 - Live")
st.caption(f"Live: {datetime.now().strftime('%H:%M:%S')}")

stocks = ["TSLA","NVDA","AAPL","SPY","QQQ","MSFT","AMZN","META","AMD","NFLX"]
min_p = st.sidebar.slider("Min Premium $", 50000, 500000, 100000)

all_data = []
for t in stocks:
    try:
        s = yf.Ticker(t)
        price = s.fast_info.get('last_price', 0)
        if not s.options: continue
        for exp in s.options[:2]:
            chain = s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df = df.copy()
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                df["live_price"] = price
                f = df[(df["volume"]>200) & (df["premium"]>=min_p)]
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["expiry"]=exp
                    f["link"] = f"https://finance.yahoo.com/quote/{t}/options/{exp}"
                    all_data.append(f)
    except: continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(40)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    
    if call_sum > put_sum:
        st.success(f"🟢 السوق متفائل - سيولة الشراء ${call_sum:,.0f} > البيع ${put_sum:,.0f}")
    else:
        st.error(f"🔴 السوق متشائم - سيولة البيع ${put_sum:,.0f} > الشراء ${call_sum:,.0f}")

    top = final.iloc[0]
    # رسالة نفيديا ترجع
    if top['ticker'] == 'NVDA' and 'CALL' in top['signal']:
        st.warning(f"🐋 NVDA CALL شراء {top['strike']} = ${top['premium']:,.0f} - حوت كبير داخل!")
    else:
        st.info(f"Top Whale: {top['ticker']} {top['signal']} {top['strike']} = ${top['premium']:,.0f}")

    st.dataframe(
        final[["ticker","signal","strike","live_price","lastPrice","premium","expiry","link"]],
        use_container_width=True,
        column_config={"link": st.column_config.LinkColumn("Yahoo")}
    )
else:
    st.warning("Market Closed")    except: continue

if all_data:
    final = pd.concat(all_data).sort_values("premium", ascending=False).head(40)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    mood = "BULLISH" if call_sum>put_sum else "BEARISH"
    st.success(f"Mood: {mood} | Live Data | CALL ${call_sum:,.0f} vs PUT ${put_sum:,.0f}")

    # جدول مع روابط
    st.dataframe(
        final[["ticker","signal","strike","live_price","lastPrice","premium","expiry","link"]],
        use_container_width=True,
        column_config={"link": st.column_config.LinkColumn("Yahoo Link")}
    )
    
    top = final.iloc[0]
    wa = f"Whale V6.3 LIVE {mood} {top['ticker']} {top['signal']} ${top['premium']:,.0f} Live:${top['live_price']} {top['link']}"
    st.link_button("Send WhatsApp with Link", f"https://wa.me/?text={urllib.parse.quote(wa)}", type="primary", use_container_width=True)
else:
    st.warning("Market Closed - Opens 4:30 PM KSA - Prices are LIVE during market")
