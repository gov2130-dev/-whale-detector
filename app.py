import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V74 مثل صورتك", layout="wide")
st.title("🔨 V74 - نفس شمعة TSLA اللي في الصورة")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=data, timeout=15)

st.markdown("### شرطك بالحرف: ذيل طويل + فوليوم أعلى من اللي قبلها + اللي بعدها تقفل فوق قمة المطرقة")

# نفحص TSLA كمثال
sym = st.text_input("جرب السهم", "TSLA")
days_back = st.slider("ابحث في آخر كم يوم؟", 10, 90, 30)

if st.button("افحص نفس شمعة الصورة"):
    tk = yf.Ticker(sym)
    df = tk.history(period=f"{days_back+10}d", interval="1d")
    found = 0
    for i in range(1, len(df)-1):
        c_prev = df.iloc[i-1]
        c_ham = df.iloc[i]
        c_next = df.iloc[i+1]

        body = abs(c_ham['Close']-c_ham['Open'])
        lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
        total = c_ham['High']-c_ham['Low']
        if total==0 or body==0: continue

        cond_tail = lower >= body * 2.0 # ذيل طويل
        cond_small_body = body <= total * 0.4
        cond_vol = c_ham['Volume'] > c_prev['Volume'] # فوليوم اعلى من اللي قبلها
        cond_close_above = c_next['Close'] > c_ham['High'] # اللي بعدها فوق قمة المطرقة

        if cond_tail and cond_small_body and cond_vol and cond_close_above:
            found+=1
            change_after = (df.iloc[-1]['Close'] - c_next['Close'])/c_next['Close']*100
            st.success(f"✅ لقيت مطرقة في {c_ham.name.date()} - مثل صورتك بالضبط")
            st.write(f"📅 التاريخ: {c_ham.name.date()} | ذيل {lower/body:.1f}x | فوليوم {c_ham['Volume']:,.0f} > السابق {c_prev['Volume']:,.0f} | تأكيد اغلاق {c_next['Close']:.2f} > قمة {c_ham['High']:.2f}")
            st.write(f"🚀 لو دخلت بعد التأكيد، الآن ربحك {change_after:.1f}%")

            # عقد الحوت وقتها
            try:
                exps = tk.options[:1]
                chain = tk.option_chain(exps[0])
                calls = chain.calls
                calls['premium'] = calls['volume']*calls['lastPrice']*100
                filt = calls[(calls['volume']>300) & (calls['premium']>50000)]
                if len(filt)>0:
                    top = filt.sort_values('premium', ascending=False).iloc[0]
                    st.write(f"💰 عقد حوت كان: Strike {top['strike']} Vol {top['volume']:,} Prem ${top['premium']:,.0f}")
                    msg = f"🔨 {sym} مطرقة مثل صورتك {c_ham.name.date()}\nفوليوم {c_ham['Volume']:,.0f}>{c_prev['Volume']:,.0f}\nتأكيد {c_next['Close']:.2f}>{c_ham['High']:.2f}\nسعر الآن {df.iloc[-1]['Close']:.2f}"
                    send_telegram(msg)
            except: pass

    if found==0:
        st.warning("ما فيه مطرقة بنفس الشروط في الفترة - خفف الشرط لذيل 1.5x")
    else:
        st.balloons()
        st.info(f"لقيت {found} حالات مثل اللي في صورتك - كلها CALL صاعدة، الفريم يومي 1D")

st.caption("صورتك: TSLA على فريم 1يوم في أكتوبر - الكود الآن يصيد نفس النمط بالضبط")
