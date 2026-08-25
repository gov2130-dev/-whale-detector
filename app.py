import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(page_title="كاشف الحيتان V5", page_icon="🐋", layout="wide")

# تحديث تلقائي كل 60 ثانية
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

st.title("🐋 كاشف الحيتان V5 - جميع الأسهم النشطة")
st.caption(f"آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - يتحدث كل 60 ثانية تلقائياً")

# كل الأسهم النشطة بقوة
ACTIVE_STOCKS = ["TSLA", "NVDA", "AAPL", "SPY", "QQQ", "MSFT", "AMZN", "META", "AMD", "NFLX", "GOOGL", "SPX", "IWM", "DIA"]

with st.sidebar:
    st.header("الإعدادات")
    min_premium = st.slider("أقل قيمة للحوت $", 50000, 500000, 100000, step=10000)
    st.success(f"يراقب {len(ACTIVE_STOCKS)} سهم نشط الآن")

all_whales = []
progress_text = st.empty()
progress = st.progress(0)

for i, ticker in enumerate(ACTIVE_STOCKS):
    progress_text.text(f"يفحص: {ticker} ({i+1}/{len(ACTIVE_STOCKS)})")
    progress.progress((i+1)/len(ACTIVE_STOCKS))
    try:
        stock = yf.Ticker(ticker)
        if not stock.options: continue
        for exp in stock.options[:2]: # نفحص تاريخين
            chain = stock.option_chain(exp)
            for df_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if df.empty or 'volume' not in df.columns: continue
                df = df.copy()
                df['premium'] = df['lastPrice'] * df['volume'] * 100
                whales = df[(df['volume'] > 300) & (df['premium'] >= min_premium)].copy()
                if not whales.empty:
                    whales['ticker'] = ticker
                    whales['type'] = df_type
                    whales['expiry'] = exp
                    all_whales.append(whales)
    except: continue

progress.empty()
progress_text.empty()

if all_whales:
    final_df = pd.concat(all_whales).sort_values('premium', ascending=False).head(100)
    
    # أكبر حوت
    top = final_df.iloc[0]
    st.error(f"🚨 أكبر حوت الآن: {top['ticker']} {top['type']} | ${top['premium']:,.0f} | سترايك {top['strike']} | انتهاء {top['expiry']}")

    # زر واتساب شامل
    wa_msg = f"🐋 تنبيه كاشف الحيتان V5\n\n"
    for idx, row in final_df.head(5).iterrows():
        wa_msg += f"• {row['ticker']} {row['type']} {row['strike']} = ${row['premium']:,.0f}\n"
    wa_msg += f"\nرابط الموقع: https://kashf-hetan-2130.streamlit.app/"
    
    st.link_button(f"📲 أرسل أهم {min(5, len(final_df))} حيتان لواتساب", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}", use_container_width=True, type="primary")

    st.dataframe(
        final_df[['ticker','type','strike','lastPrice','volume','premium','expiry']].style.format({'premium': '${:,.0f}', 'lastPrice': '${:.2f}'}),
        use_container_width=True, height=700
    )
    st.bar_chart(final_df.head(10).set_index('ticker')['premium'])
else:
    st.warning("السوق هادي حاليا، لا يوجد حيتان فوق الفلتر. قلل الفلتر أو انتظر الافتتاح الأمريكي (4:30 عصراً بتوقيت السعودية)")

st.divider()
st.info("💡 يعمل تلقائياً 24/7 ويراقب 14 سهم نشط + SPX. اضغط زر الواتساب لإرسال التنبيه لقروبك")
