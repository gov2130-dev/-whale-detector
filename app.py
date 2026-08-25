import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="Whale Detector V6", layout="wide")
st.markdown('<meta http-equiv="refresh" content="60">', unsafe_allow_html=True)

st.title("Whale Detector V6")
st.caption(f"Last update: {datetime.now().strftime('%H:%M:%S')}")

ACTIVE_STOCKS = ["TSLA", "NVDA", "AAPL", "SPY", "QQQ", "MSFT", "AMZN", "META", "AMD", "NFLX"]

min_premium = st.sidebar.slider("Min Premium $", 50000, 500000, 100000, step=10000)

all_whales = []
progress = st.progress(0)
for i, ticker in enumerate(ACTIVE_STOCKS):
    progress.progress((i+1)/len(ACTIVE_STOCKS))
    try:
        stock = yf.Ticker(ticker)
        if not stock.options:
            continue
        for exp in stock.options[:2]:
            chain = stock.option_chain(exp)
            for df_type, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty:
                    continue
                df = df.copy()
                df['premium'] = df['lastPrice'] * df['volume'] * 100
                whales = df[(df['volume'] > 300) & (df['premium'] >= min_premium)].copy()
                if not whales.empty:
                    whales['ticker'] = ticker
                    whales['signal'] = df_type
                    whales['expiry'] = exp
                    all_whales.append(whales)
    except:
        continue
progress.empty()

if all_whales:
    final_df = pd.concat(all_whales).sort_values('premium', ascending=False).head(50)
    
    call_sum = final_df[final_df['signal'].str.contains("CALL")]['premium'].sum()
    put_sum = final_df[final_df['signal'].str.contains("PUT")]['premium'].sum()
    
    if call_sum > put_sum:
        st.success(f"Market Mood: BULLISH - CALL ${call_sum:,.0f} > PUT ${put_sum:,.0f}")
    else:
        st.error(f"Market Mood: BEARISH - PUT ${put_sum:,.0f} > CALL ${call_sum:,.0f}")

    top = final_df.iloc[0]
    st.metric("Biggest Whale", f"{top['ticker']} {top['signal']}", f"${top['premium']:,.0f}")

    wa_text = f"Whale V6 - Mood: {'BULL' if call_sum>put_sum else 'BEAR'}\n"
    for _, r in final_df.head(5).iterrows():
        wa_text += f"{r['ticker']} {r['signal']} {r['strike']} = ${r['premium']:,.0f}\n"
    wa_text += "https://kashf-hetan-2130.streamlit.app/"
    
    st.link_button("Send to WhatsApp", f"https://wa.me/?text={urllib.parse.quote(wa_text)}", use_container_width=True, type="primary")
    st.dataframe(final_df[['ticker','signal','strike','lastPrice','volume','premium','expiry']], use_container_width=True, height=600)
else:
    st.warning("Market closed - opens 4:30 PM KSA time")                    whales['signal'] = df_type
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
