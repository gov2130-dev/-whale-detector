import streamlit as st, yfinance as yf, requests, io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def create_big_image(ticker, o_type, strike, opt_price, stop, curr, tg_list):
    W, H = 1080, 1400
    img = Image.new('RGB', (W, H), (15, 23, 36))
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("arial.ttf", 60)
        font_mid = ImageFont.truetype("arial.ttf", 40)
        font_small = ImageFont.truetype("arial.ttf", 32)
    except:
        font_big = ImageFont.load_default()
        font_mid = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.rectangle([0,0,W,170], fill=(0, 230, 170))
    draw.text((40, 35), "حيتان ابو راكان", font=font_big, fill=(0,0,0))
    draw.text((40, 105), f"{(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')}", font=font_small, fill=(0,0,0))

    y=220
    draw.text((40, y), f"${ticker} - {strike} {o_type}", font=font_big, fill=(255,255,255))
    y+=90
    draw.text((40, y), f"السعر الحالي: ${curr:.2f}", font=font_mid, fill=(180,180,180))
    
    y+=90
    draw.rectangle([30, y, W-30, y+110], fill=(35,50,70), outline=(0,230,170), width=3)
    draw.text((50, y+10), f"الدخول: ${opt_price:.2f}", font=font_big, fill=(0,255,160))
    draw.text((50, y+65), f"الوقف: ${stop:.2f}", font=font_small, fill=(255,90,90))
    
    y+=160
    draw.text((40, y), "اهداف السهم:", font=font_mid, fill=(255,220,0))
    y+=55
    tg_text = " -> ".join([str(int(x)) for x in tg_list])
    draw.text((40, y), tg_text, font=font_mid, fill=(255,255,255))
    
    y+=90
    draw.text((40, y), "اهداف العقد:", font=font_mid, fill=(255,220,0))
    y+=55
    draw.text((40, y), f"T1 ${opt_price*1.5:.2f} (+50%)", font=font_big, fill=(255,255,255))
    y+=70
    draw.text((40, y), f"T2 ${opt_price*2.2:.2f} (+120%)", font=font_big, fill=(0,255,160))

    y+=140
    draw.text((40, y), "ليست توصية - للتعليم فقط", font=font_small, fill=(130,130,130))
    y+=45
    draw.text((40, y), "TrkHrTrading | GOLDEN 6/7", font=font_mid, fill=(0,230,170))

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
st.title("V79.1 - خط عملاق FULL HD - مصحح")

if st.button("معاينة الصورة الكبيرة"):
    tg=[207,209,211,214,217,221,225]
    buf=create_big_image("NVDA","CALL",209,4.50,2.70,205.30,tg)
    st.image(buf, caption="شكل الصورة في تلجرام - خط كبير واضح")
    st.session_state['buf']=buf

if st.button("ارسل للتلجرام"):
    if 'buf' in st.session_state:
        cap="""تحديث العقد
$NVDA - 209 CALL
الدخول $4.50 | وقف $2.70
حيتان ابو راكان"""
        if send_image(st.session_state['buf'], cap):
            st.success("✅ انرسلت - شف تلجرام - خط كبير جدا واضح")
        else:
            st.error("فشل الارسال")
    else:
        st.warning("اضغط معاينة اول")
