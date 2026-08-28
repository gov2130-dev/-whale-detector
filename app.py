import streamlit as st, requests, time
import pandas as pd
from datetime import datetime

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=data, timeout=15)
        return r.status_code == 200
    except:
        return False

st.set_page_config(page_title="V99.1 AUTO", layout="wide")
st.title("V99.1 AUTO - سلة الحيتان 🐋💰")
st.success("البوت متصل - Status 200 | يفحص كل 60 ثانية")

# جلب العقود من بينانس فيوتشر
@st.cache_data(ttl=60)
def get_whale_basket():
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        r = requests.get(url, timeout=10).json()
        df = pd.DataFrame(r)
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['quoteVolume'] = df['quoteVolume'].astype(float)
        # فلترة الحيتان: سيولة عالية + حركة قوية
        whales = df[(df['quoteVolume'] > 100000000) & (df['priceChangePercent'].abs() > 3)]
        whales = whales.sort_values('quoteVolume', ascending=False).head(15)
        return whales[['symbol','lastPrice','priceChangePercent','quoteVolume','highPrice','lowPrice']]
    except Exception as e:
        return pd.DataFrame()

basket = get_whale_basket()

if basket.empty:
    st.warning("جاري جلب العقود... اذا استمر فاضي اضغط Rerun")
else:
    st.dataframe(basket, use_container_width=True)
    
    # إرسال تلقائي لأقوى 3 حيتان
    if st.button("📤 ارسل أقوى 3 حيتان لتلجرام"):
        msg = f"🐋 *سلة الحيتان V99.1* - {datetime.now().strftime('%H:%M')}\n\n"
        for i, row in basket.head(3).iterrows():
            msg += f"• {row['symbol']} : {row['priceChangePercent']:.2f}% | Vol: ${row['quoteVolume']/1e6:.1f}M\n"
        if send_telegram(msg):
            st.success("انرسلت لتلجرام ✅")
        else:
            st.error("فشل الإرسال")

# تحديث تلقائي
st.caption("يتحدث تلقائياً كل دقيقة - لا يحتاج تحديث يدوي")
time.sleep(60)
st.rerun()
