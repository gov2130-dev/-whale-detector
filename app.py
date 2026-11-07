import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import requests

st.set_page_config(page_title="الأمريكي تحت المجهر", layout="centered")
st.title("🇺🇸 الأمريكي تحت المجهر")

# ===== اعدادات الواتس - غيرها ببياناتك =====
ULTRAMSG_INSTANCE = "ضع_الـ Instance ID هنا"  # مثلا: instance12345
ULTRAMSG_TOKEN = "ضع_التوكن هنا"  # مثلا: abc123xyz
MY_WHATSAPP = "9665xxxxxxxx"  # رقمك بالواتس بدون + ، مثال: 966500000000

# شروط الحوت
MIN_PREMIUM = 50000
MIN_RATIO = 1.5

def get_targets(entry):
    return [round(entry*1.25,2), round(entry*1.35,2), round(entry*1.50,2), round(entry*1.65,2),
            round(entry*1.75,2), round(entry*1.85,2), round(entry*1.90,2), round(entry*2.00,2)]

def send_whatsapp(message):
    # ارسال عن طريق UltraMsg
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
        data = {"token": ULTRAMSG_TOKEN, "to": MY_WHATSAPP, "body": message}
        res = requests.post(url, data=data, timeout=15)
        if res.status_code == 200:
            return True, "تم الارسال للواتس ✅"
        else:
            return False, f"خطأ: {res.text[:200]}"
    except Exception as e:
        return False, f"خطأ: {e}"

def format_message(symbol, company, opt_type, strike, exp, entry, stop, vol):
    targets = get_targets(entry)
    type_txt = "🔴 شراء مرجح PUT" if opt_type == "PUT" else "🟢 شراء مرجح CALL"
    exp_fmt = datetime.strptime(exp, "%Y-%m-%d").strftime("%b %d %Y").upper()
    time_now = datetime.now().strftime("%H:%M:%S")
    total_cost = int(entry * 100)
    msg = f"""🇺🇸 الأمريكي تحت المجهر
🔍 الأمريكي تحت المجهر
{symbol} - {company}
{type_txt} {strike}
الانتهاء: {exp_fmt} 📅
سعر التنفيذ: {entry} ({total_cost} دولار للعقد) 💰
الوقف: {stop} 🔴 | الكمية: {int(vol)} عقد 📦
الأهداف بالترتيب 🎯
{targets[0]} | {targets[1]} | {targets[2]} | {targets[3]}
{targets[4]} | {targets[5]} | {targets[6]} | {targets[7]}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
وقت التنفيذ: {time_now} SA 🕐
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""
    return msg

# زر الفحص
if st.button("🔍 افحص الآن", use_container_width=True):
    tickers = ["AAPL","BABA","AMZN","MSFT","NVDA","TSLA","META","GOOGL","AMD","NFLX","GDX","SPY","QQQ","COIN","PLTR"]
    found = 0
    with st.spinner("جاري رصد الحيتان..."):
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                stock_price = info.get('currentPrice')
                company = info.get('shortName', symbol)
                if not stock_price:
                    continue
                for exp in ticker.options[:2]:
                    days = (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    if days < 0 or days > 7:
                        continue
                    chain = ticker.option_chain(exp)
                    for opt_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                        for _, row in df.iterrows():
                            vol = row['volume'] if pd.notna(row['volume']) else 0
                            oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
                            price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
                            if vol < 300 or oi == 0 or price < 0.5:
                                continue
                            ratio = vol / oi
                            premium = vol * price * 100
                            if ratio >= MIN_RATIO and premium >= MIN_PREMIUM:
                                found += 1
                                entry = round(float(price), 2)
                                stop = round(entry * 0.67, 2)
                                msg = format_message(symbol, company, opt_type, row['strike'], exp, entry, stop, vol)
                                
                                # عرض نفس صيغة القناة
                                st.markdown(f"""
                                <div dir="rtl" style="background-color:white; padding:18px; border-radius:18px; box-shadow:0 2px 10px rgba(0,0,0,0.1); margin-bottom:10px; text-align:right; font-size:17px; line-height:1.8; color:black; white-space:pre-line;">
                                {msg}
                                </div>
                                """, unsafe_allow_html=True)
                                
                                # زر ارسال للواتس لكل توصية
                                if st.button(f"📲 ارسل {symbol} {opt_type} للواتس", key=f"wa_{symbol}_{row['strike']}_{exp}"):
                                    ok, txt = send_whatsapp(msg)
                                    if ok:
                                        st.success(f"✅ تم ارسال {symbol} لواتسابك")
                                    else:
                                        st.error(txt)
                                
                                # زر ارسال تلقائي لكل التوصيات
                                st.divider()
            except:
                continue
    if found == 0:
        st.warning("ما فيه صفقات حيتان اليوم.")

# زر ارسال الكل للواتس مرة واحدة
st.markdown("---")
if st.button("📲 ارسل كل التوصيات للواتس دفعة واحدة", use_container_width=True):
    st.info("هذي الميزة تحتاج تشغيل الفحص أولاً، وبعدها بتكون الرسائل محفوظة")
