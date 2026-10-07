import streamlit as st
import requests
import time
from datetime import datetime
import pytz

# --- إعدادات آمنة - لا تضع التوكن هنا ---
BOT_TOKEN = st.secrets.get("8594574378:AAFvFChSUA2AfTgcd96sknCQkGyjwlJL12w", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")
BOT_USERNAME = "@v68_golden_555371577_bot"

st.set_page_config(page_title="V93 FINAL - Golden Detector", page_icon="🐋", layout="wide")

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False, "BOT_TOKEN أو CHAT_ID ناقص في Secrets"
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
        r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200, r.text
    except Exception as e:
        return False, str(e)

st.title("🐋 V93 FINAL - كاشف الحيتان GOLDEN UNDER $4")
st.caption(f"البوت: {BOT_USERNAME}")

# وقت
riyadh = pytz.timezone('Asia/Riyadh')
ny = pytz.timezone('America/New_York')
st.info(f"⏰ وقت الرياض: {datetime.now(riyadh).strftime('%Y-%m-%d %H:%M:%S')} | وقت نيويورك: {datetime.now(ny).strftime('%Y-%m-%d %H:%M:%S')}")

# --- قائمة الأسهم الرخيصة (مثال) ---
stocks = [
    {"symbol": "SMCI", "price": 1.00},
    {"symbol": "PEP", "price": 1.98},
    {"symbol": "ADBE", "price": 3.28},
    {"symbol": "MU", "price": 3.90},
]

if st.button("🚀 فحص الآن وإرسال لتليجرام", use_container_width=True):
    for s in stocks:
        if s["price"] < 4:
            target_stock_2 = s["price"] * 1.02
            target_stock_5 = s["price"] * 1.05
            target_opt_50 = 50
            target_opt_150 = 150
            
            msg = f"""🐋 *GOLDEN UNDER $4* 🐋
            
💎 السهم: *{s['symbol']}*
💰 السعر: ${s['price']}

🎯 أهداف السهم:
- 2%: ${target_stock_2:.2f}
- 5%: ${target_stock_5:.2f}

🔥 أهداف العقد:
- 50%
- 150%

⏰ وقت الفحص: {datetime.now(riyadh).strftime('%H:%M')}
"""
            ok, resp = send_telegram(msg)
            if ok:
                st.success(f"{s['symbol']} - ${s['price']} تم الإرسال ✅")
            else:
                st.error(f"{s['symbol']} فشل: {resp}")
            time.sleep(1)
