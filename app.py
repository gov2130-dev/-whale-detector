import streamlit as st, yfinance as yf, requests, io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def create_big_image(ticker, o_type, strike, opt_price, stop, curr, tg_list):
    # صورة 1080x1350 خط كبير جدا
    W, H = 1080, 1350
    img = Image.new('RGB', (W, H), (14, 22, 33)) # كحلي غامق فخم
    draw = ImageDraw.Draw(img)
    
    # نحاول خط كبير
    try:
        # استخدم خط افتراضي كبير
        font_big = ImageFont.truetype("arial.ttf", 65)
        font_mid = ImageFont.truetype("arial.ttf", 45)
        font_small = ImageFont.truetype("arial.ttf", 36)
    except:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # خلفية
    draw.rectangle([0,0,W,180], fill=(0, 212, 170)) # هيدر اخضر
    draw.text((50, 40), "حيتان ابو راكان 🐋", font=font_big, fill=(0,0,0))
    draw.text((50, 110), f"{(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')}", font=font_small, fill=(0,0,0))

    y=240
    draw.text((50, y), f"${ticker} - {strike} {o_type}", font=font_big, fill=(255,255,255))
    y+=100
    draw.text((50, y), f"السعر الحالي: ${curr:.2f}", font=font_mid, fill=(160,170,180))
    
    y+=100
    draw.rectangle([40, y, W-40, y+120], fill=(30,40,55), outline=(0,212,170), width=3)
    draw.text((60, y+15), f"💰 الدخول: ${opt_price:.2f}", font=font_big, fill=(0,255,150))
    draw.text((60, y+70), f"🛑 الوقف: ${stop:.2f}", font=font_mid, fill=(255,80,80))
    
    y+=180
    draw.text((50, y), "🎯 اهداف السهم:", font=font_mid, fill=(255,215,0))
    y+=60
    tg_text = " → ".join([str(int(x)) for x in tg_list])
    # لف النص لو طويل
    draw.text((50, y), tg_text, font=font_mid, fill=(255,255,255))
    
    y+=120
    draw.text((50, y), "🎯 اهداف العقد:", font=font_mid, fill=(255,215,0))
    y+=60
    draw.text((50, y), f"T1 ${opt_price*1.5:.2f} (+50%)", font=font_big, fill=(255,255,255))
    y+=70
    draw.text((50, y), f"T2 ${opt_price*2.2:.2f} (+120%)", font=font_big, fill=(0,255,150))

    y+=150
    draw.text((50, y), "⚠️ ليست توصية - للتعليم فقط", font=font_small, fill=(120,130,140))
    y+=50
    draw.text((50, y), "TrkHrTrading | GOLDEN 6/7 🔥", font=font_mid, fill=(0,212,170))

    buf=io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf

def send_image(buf, caption):
    url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    files={'photo': ('signal.png', buf, 'image/png')}
    data={'chat_id':CHAT_ID,'caption':caption}
    r=requests.post(url, files=files, data=data, timeout=20)
    return r.status_code==200

st.set_page_config(layout="wide")
st.title("V79 - خط عملاق FULL HD")

# معاينة
if st.button("👁️ معاينة الصورة الكبيرة"):
    tg=[207,209,211,214,217,221,225]
    buf=create_big_image("NVDA","CALL",209,4.50,2.70,205.30,tg)
    st.image(buf, caption="هذا شكل الصورة في تلجرام - خط كبير واضح", use_column_width=True)
    # حفظ للارسال
    st.session_state['buf']=buf
    st.session_state['cap']="""تحديث العقد والاهداف والدخول
$NVDA - 209 CALL 🎯
💰 الدخول: $4.50 | 🛑 الوقف: $2.70
🐋 حيتان ابو راكان"""

if st.button("📩 ارسل للتلجرام - صورة واضحة"):
    if 'buf' in st.session_state:
        if send_image(st.session_state['buf'], st.session_state['cap']):
            st.success("✅ انرسلت - افتح تلجرام الآن - بتشوف خط كبير جدا واضح")
        else: st.error("فشل")
    else:
        st.warning("اضغط معاينة اول")
