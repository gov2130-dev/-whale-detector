import streamlit as st
import requests

st.title("كاشف الحيتان - ابو راكان")

BOT_TOKEN = 8594574378:AAF2NQzIc1mutqj8lxjthMVoSR4p889JN4k
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return {"ok": False, "error": "ما حطيت التوكن في Secrets"}
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        r = requests.post(url, data=data, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

if st.button("فحص الآن وارسال لتليجرام"):
    curr = 1.75
    msg = f"حوت جديد!\nالسعر الآن: ${curr}\nالدخول: $1.75"
    result = send_telegram(msg)
    st.json(result)
    if result.get("ok"):
        st.success("تم الإرسال ✅ شيك تليجرام")
    else:
        st.error(f"فشل: {result}")
else:
    st.info(f"BOT_TOKEN موجود: {bool(BOT_TOKEN)} | CHAT_ID: {CHAT_ID}")
