import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(page_title="كاشف الحيتان V7", page_icon="🐋", layout="wide")
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

st.title("🐋 كاشف الحيتان V7 - رادار تنبيه الحوت الجديد")
st.caption(f"اخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

ACTIVE_STOCKS = ["TSLA", "NVDA", "AAPL", "SPY", "QQQ", "MSFT", "AMZN", "META", "AMD", "NFLX", "GOOGL", "SPX"]

min_premium = st.sidebar.slider("اقل قيمة للتنبيه $", 1000000, 50000000, 20000000, step=1000000)
st.sidebar.info(f"سيرسل تنبيه اذا دخل حوت فوق ${min_premium:,.0f}")

# تخزين الحيتان القديمة لمعرفة الجديد
if 'old_whales' not in st.session_state:
    st.session_state.old_whales = set()

all_whales = []
for ticker in ACTIVE_STOCKS:
    try:
        stock = yf.Ticker(ticker)
        if not stock.options: continue
        for exp in stock.options[:1]:
            chain = stock.option_chain(exp)
            for df_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if df.empty: continue
                df = df.copy()
                df['premium'] = df['lastPrice'] * df['volume'] * 100
                whales = df[(df['volume'] > 300) & (df['premium'] >= 100000)].copy()
                if not whales.empty:
                    whales['ticker'] = ticker
                    whales['signal'] = df_type
                    whales['expiry'] = exp
                    whales['id'] = whales['ticker'] + whales['strike'].astype(str) + whales['expiry']
                    all_whales.append(whales)
    except: continue

if all_whales:
    final_df = pd.concat(all_whales).sort_values('premium', ascending=False)
    
    # كشف الحيتان الجديدة
    current_ids = set(final_df['id'].tolist())
    new_ids = current_ids - st.session_state.old_whales
    
    if new_ids and len(st.session_state.old_whales) > 0:
        new_whales = final_df[final_df['id'].isin(new_ids)]
        big_new = new_whales[new_whales['premium'] >= min_premium]
        
        if not big_new.empty:
            # تنبيه صوتي ومرئي
            st.markdown("""
            <audio autoplay>
            <source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg">
            </audio>
            <script>
            navigator.vibrate([1000, 500, 1000]);
            </script>
            """, unsafe_allow_html=True)
            
            st.balloons()
            st.error(f"🚨 تنبيه: دخل {len(big_new)} حوت جديد فوق ${min_premium:,.0f} !!")
            
            for _, row in big_new.iterrows():
                wa_msg = f"🚨 حوت جديد دخل الان!\n{row['ticker']} {row['signal']} {row['strike']} = ${row['premium']:,.0f}\nhttps://kashf-hetan-2130.streamlit.app/"
                st.link_button(f"📲 ارسل تنبيه {row['ticker']} ${row['premium']:,.0f} لواتساب", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}", type="primary")

    st.session_state.old_whales = current_ids

    # عرض الجدول
    top = final_df.iloc[0]
    st.metric("اكبر حوت الان", f"{top['ticker']} {top['signal']}", f"${top['premium']:,.0f}")
    st.dataframe(final_df[['ticker','signal','strike','lastPrice','volume','premium','expiry']].head(20), use_container_width=True)
else:
    st.warning("السوق هادي")

st.info("اترك الموقع مفتوح في الجوال، اول ما يدخل حوت جديد فوق 20 مليون بيصفر ويهتز ويعطيك زر واتساب فورا")

# زر تفعيل التنبيهات
st.sidebar.markdown("---")
st.sidebar.markdown("**لتفعيل تنبيه تلقائي حتى لو قفلت الموقع:**")
st.sidebar.code("استخدم Telegram Bot - اسهل")
if st.sidebar.button("كيف افعل تليجرام بوت؟"):
    st.sidebar.success("ارسل لي: ابغى كود تليجرام")                    all_whales.append(whales)
    except:
        continue
progress.empty()

if all_whales:
    final_df = pd.concat(all_whales).sort_values('premium', ascending=False).head(100)

    call_premium = final_df[final_df['signal'].str.contains("CALL")]['premium'].sum()
    put_premium = final_df[final_df['signal'].str.contains("PUT")]['premium'].sum()
    
    if call_premium > put_premium:
        mood = f"السوق متفائل - سيولة الشراء ${call_premium:,.0f} > البيع"
        st.success(f"المزاج العام: {mood} - CALL")
    else:
        mood = f"السوق متشائم - سيولة البيع ${put_premium:,.0f} > الشراء"
        st.error(f"المزاج العام: {mood} - PUT")

    top = final_df.iloc[0]
    st.markdown(f"<div style='background:#333;padding:15px;border-radius:10px;color:white;text-align:center;font-size:22px'>اكبر حوت: {top['ticker']} {top['signal']} | ${top['premium']:,.0f}</div>", unsafe_allow_html=True)

    wa_msg = f"كاشف الحيتان V6 - {mood}\n\n"
    for _, row in final_df.head(5).iterrows():
        wa_msg += f"{row['ticker']} {row['signal']} {row['strike']} = ${row['premium']:,.0f}\n"
    wa_msg += f"\nhttps://kashf-hetan-2130.streamlit.app/"
    
    st.link_button(f"ارسل الاشارات لواتساب", f"https://wa.me/?text={urllib.parse.quote(wa_msg)}", use_container_width=True, type="primary")

    st.dataframe(final_df[['ticker','signal','strike','lastPrice','volume','premium','expiry']], use_container_width=True, height=700)
else:
    st.warning("السوق مغلق حاليا - يفتح 4:30 العصر بتوقيت السعودية")

st.info("V6: CALL = الحيتان تشتري (يتوقعون صعود) | PUT = الحيتان تبيع (يتوقعون هبوط)")
