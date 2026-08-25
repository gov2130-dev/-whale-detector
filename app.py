import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="كاشف الحيتان V4", page_icon="🐋", layout="wide")

st.markdown("""
<style>
.big-whale {background:#ff4b4b; color:white; padding:15px; border-radius:10px; font-size:20px; text-align:center; margin:10px 0}
.stock-card {border:1px solid #333; padding:10px; border-radius:10px; background:#0e1117}
</style>
""", unsafe_allow_html=True)

st.title("🐋 كاشف الحيتان V4 - جميع الأسهم النشطة")
st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - يتحدث كل 60 ثانية")

# قائمة الأسهم النشطة
ACTIVE_STOCKS = ["TSLA", "NVDA", "AAPL", "SPY", "QQQ", "MSFT", "AMZN", "META", "AMD", "NFLX", "GOOGL", "SPX"]

selected_stocks = st.multiselect("اختر الأسهم للمراقبة:", ACTIVE_STOCKS, default=["TSLA","NVDA","AAPL","SPY","QQQ"])

min_premium = st.slider("أقل قيمة للحوت (بالدولار):", 50000, 500000, 100000, step=10000)

all_whales = []

progress = st.progress(0)
for i, ticker in enumerate(selected_stocks):
    progress.progress((i+1)/len(selected_stocks))
    try:
        stock = yf.Ticker(ticker)
        # ناخذ اقرب تاريخ انتهاء
        if not stock.options: continue
        exp = stock.options[0]
        chain = stock.option_chain(exp)

        for df in [chain.calls, chain.puts]:
            if df.empty: continue
            df['premium'] = df['lastPrice'] * df['volume'] * 100
            whales = df[(df['volume'] > 500) & (df['premium'] >= min_premium)].copy()
            whales['ticker'] = ticker
            whales['expiry'] = exp
            all_whales.append(whales)
    except: continue
progress.empty()

if all_whales:
    final_df = pd.concat(all_whales).sort_values('premium', ascending=False).head(50)

    # تنبيه كبير
    top_whale = final_df.iloc[0]
    st.markdown(f'<div class="big-whale">🚨 أكبر حوت الآن: {top_whale["ticker"]} | قيمة ${top_whale["premium"]:,.0f} | سترايك {top_whale["strike"]}</div>', unsafe_allow_html=True)

    # زر واتساب
    msg = f"🐋 كاشف الحيتان تنبيه:\nأكبر حوت: {top_whale['ticker']} Strike {top_whale['strike']} قيمته ${top_whale['premium']:,.0f}\nالموقع: https://kashf-hetan-2130.streamlit.app/"
    wa_link = f"https://wa.me/?text={urllib.parse.quote(msg)}"
    st.link_button("📲 أرسل التنبيه لواتساب الآن", wa_link, use_container_width=True)

    st.dataframe(final_df[['ticker','strike','lastPrice','volume','premium','expiry','contractSymbol']], use_container_width=True, height=600)

    # رسم
    st.bar_chart(final_df.head(10).set_index('ticker')['premium'])
else:
    st.warning("لا يوجد حيتان حاليا بهذا الفلتر، جرب تقلل قيمة الفلتر")

st.button("🔄 تحديث الآن")
