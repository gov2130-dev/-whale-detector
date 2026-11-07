import streamlit as st
import yfinance as yf
from datetime import datetime
import pandas as pd
import requests

st.set_page_config(page_title="راصد الحيتان", layout="centered")
st.title("📊 راصد الحيتان")

# ===== اعدادات الواتس =====
ULTRAMSG_INSTANCE = "ضع_الـ Instance ID هنا"
ULTRAMSG_TOKEN = "ضع_التوكن هنا"
MY_WHATSAPP = "9665xxxxxxxx"

# شروط الحوت - خففتها شوي عشان تطلع اسهم غير ابل
MIN_PREMIUM = 30000
MIN_RATIO = 1.2
MIN_VOLUME = 200

def get_targets(entry):
    return [round(entry*1.25,2), round(entry*1.35,2), round(entry*1.50,2), round(entry*1.65,2),
            round(entry*1.75,2), round(entry*1.85,2), round(entry*1.90,2), round(entry*2.00,2)]

def send_whatsapp(message):
    try:
        url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
        data = {"token": ULTRAMSG_TOKEN, "to": MY_WHATSAPP, "body": message}
        res = requests.post(url, data=data, timeout=15)
        return res.status_code == 200
    except:
        return False

# صيغة الرسالة الجديدة - بدون "الأمريكي تحت المجهر"
def format_message(symbol, company, opt_type, strike, exp, entry, stop, vol):
    targets = get_targets(entry)
    type_txt = "🔴 شراء مرجح PUT" if opt_type == "PUT" else "🟢 شراء مرجح CALL"
    exp_fmt = datetime.strptime(exp, "%Y-%m-%d").strftime("%b %d %Y").upper()
    time_now = datetime.now().strftime("%H:%M:%S")
    total_cost = int(entry * 100)
    msg = f"""🔍 راصد الحيتان
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

if st.button("🔍 افحص الآن - اسهم متنوعة", use_container_width=True):
    # قائمة متنوعة - مو بس ابل
    tickers = ["BABA","AMZN","MSFT","NVDA","TSLA","META","GOOGL","AMD","NFLX","GDX","SPY","QQQ","COIN","PLTR","AAPL","CRM","ORCL","AVGO","JPM","XOM"]
    found = 0
    with st.spinner("جاري الفحص... بيجيب سهم واحد لكل شركة"):
        for symbol in tickers:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                company = info.get('shortName', symbol)
                stock_price = info.get('currentPrice')
                if not stock_price:
                    continue
                
                best_for_this_stock = None
                best_premium = 0
                
                for exp in ticker.options[:3]:
                    days = (datetime.strptime(exp, "%Y-%m-%d") - datetime.now()).days
                    if days < 0 or days > 7:
                        continue
                    chain = ticker.option_chain(exp)
                    for opt_type, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                        for _, row in df.iterrows():
                            vol = row['volume'] if pd.notna(row['volume']) else 0
                            oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
                            price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
                            if vol < MIN_VOLUME or oi == 0 or price < 0.5:
                                continue
                            ratio = vol / oi
                            premium = vol * price * 100
                            # ناخذ اقوى صفقة بس لهذا السهم
                            if ratio >= MIN_RATIO and premium >= MIN_PREMIUM and premium > best_premium:
                                best_premium = premium
                                best_for_this_stock = (opt_type, row, exp, price, vol)
                
                # نعرض سهم واحد فقط لكل شركة - هذا هو الحل لمشكلة تكرار ابل
                if best_for_this_stock:
                    found += 1
                    opt_type, row, exp, price, vol = best_for_this_stock
                    entry = round(float(price), 2)
                    stop = round(entry * 0.67, 2)
                    msg = format_message(symbol, company, opt_type, row['strike'], exp, entry, stop, vol)
                    
                    st.markdown(f"""
                    <div dir="rtl" style="background-color:white; padding:18px; border-radius:18px; box-shadow:0 2px 10px rgba(0,0,0,0.1); margin-bottom:10px; text-align:right; font-size:17px; line-height:1.8; color:black; white-space:pre-line;">
                    {msg}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"📲 ارسل {symbol} للواتس", key=f"wa_{symbol}"):
                        if send_whatsapp(msg):
                            st.success(f"✅ تم ارسال {symbol} للواتس")
                        else:
                            st.error("تأكد من بيانات UltraMsg")
                    st.divider()
            except:
                continue
    if found == 0:
        st.warning("ما فيه صفقات اليوم. جرب بعد ساعة، السوق مقفل أو السيولة ضعيفة.")
    else:
        st.success(f"✅ طلعت لك {found} اسهم مختلفة، بدون تكرار")
