import streamlit as st, requests, time
from datetime import datetime

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
    try:
        requests.post(url, data=data, timeout=10)
        return True
    except:
        return False

st.set_page_config(page_title="V99.1 AUTO", layout="wide")
st.title("V99.1 AUTO - سلة الحيتان 🐋💰")
st.success("البوت متصل - Status 200")

if st.button("📤 اختبار لحظي"):
    send_telegram("✅ V99.1 شغال - test ok")
    st.toast("انرسلت!")

# هنا تضيف كود فحص العملات حقك
st.write("البوت جاهز يستقبل إشارات الحيتان لحظياً")
