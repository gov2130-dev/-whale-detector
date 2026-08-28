import streamlit as st, requests

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

st.title("V99 TEST - Debug")

st.write(f"BOT_TOKEN starts with: {BOT_TOKEN[:10]}...")
st.write(f"CHAT_ID is: {CHAT_ID}")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg}
    r = requests.post(url, data=data, timeout=10)
    st.write(f"Status: {r.status_code}")
    st.write(f"Response: {r.text}")
    return r.status_code == 200

if st.button("test telegram"):
    if send_telegram("test ok"):
        st.success("SUCCESS")
    else:
        st.error("FAIL - شف السبب فوق")
