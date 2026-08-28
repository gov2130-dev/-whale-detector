import streamlit as st, requests

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data, timeout=10)
    return r.status_code == 200

st.title("V99 TEST")

if st.button("test telegram"):
    if send_telegram("test ok"):
        st.success("SUCCESS")
    else:
        st.error("FAIL")

st.write("code is clean")
