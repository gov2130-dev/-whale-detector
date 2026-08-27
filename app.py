import streamlit as st, yfinance as yf, time, io, requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import math

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def draw_chip(draw, cx, cy):
    # رسم شريحة هولوجرام 3D مثل AVGO
    for i in range(8):
        y = cy - i*4
        # جسم الشريحة
        draw.rounded_rectangle([cx-140, y-90, cx+140, y+90], radius=18, outline=(0,255,200), width=2)
        draw.rectangle([cx-100, y-60, cx+100, y+60], outline=(120,255,255), width=1)
    # توهج تحت
    for r in range(60, 20, -5):
        draw.ellipse([cx-r*2, cy+80-r, cx+r*2, cy+80+r], outline=(0,255,150, r*2), width=2)

def create_avgo_card(ticker, o_type, strike, entry, stop, company, score):
    W,H = 1080, 1920
    img = Image.new('RGB', (W,H), (2,5,15))
    d = ImageDraw.Draw(img, 'RGBA')
    f_big = ImageFont.load_default()
    f_med = ImageFont.load_default()

    # إطار خارجي نيون مثل الصورة الأصلية
    d.rounded_rectangle([8,8,W-8,H-8], radius=40, outline=(0,200,255), width=5)
    d.rounded_rectangle([18,18,W-18,H-18], radius=35, outline=(0,255,150), width=1)
    
    # هيدر - الأمريكي تحت الفجر + نبض
    d.rounded_rectangle([25,25,W-25,140], radius=20, outline=(0,255,200), width=2)
    d.line([(40,80),(100,80),(115,50),(130,110),(145,80),(W-145,80),(W-130,40),(W-115,110),(W-100,80),(W-40,80)], fill=(0,255,150), width=3)
    d.text((W//2,70), "AL-AMRIKI TAHT AL-FAJR", fill=(150,255,255), anchor="mm", font=f_big)
    
    # اسم الشركة BROADCOM STYLE
    d.text((W//2,200), company, fill=(255,255,255), anchor="mm", font=f_big)
    d.text((W//2,260), f"{ticker} • 1D", fill=(0,255,150), anchor="mm", font=f_med)

    # شارت صغير يسار مثل الأصلي
    d.rounded_rectangle([30,310,310,600], radius=15, outline=(0,255,150), width=2)
    # رسم شموع صاعدة
    for i in range(15):
        x = 50 + i*16
        h1 = 550 - i*8
        d.line([(x,h1),(x,h1-40)], fill=(0,255,100), width=3)
        d.rectangle([x-5,h1-25,x+5,h1-10], fill=(180,255,180))

    # الشريحة 3D في الوسط
    draw_chip(d, 700, 480)

    # معلومات العقد - نفس مكان الأصلي
    y0=650
    d.rounded_rectangle([25,y0,520,y0+420], radius=20, outline=(0,255,200), width=3, fill=(5,20,35,200))
    d.text((50,y0+15), "CONTRACT INFO", fill=(0,255,150), font=f_med)
    d.text((50,y0+70), f"TICKER", fill=(150,150,150), font=f_med)
    d.text((300,y0+70), f"{ticker}", fill=(255,255,255), font=f_med, anchor="lm")
    d.text((50,y0+130), f"TYPE", fill=(150,150,150), font=f_med)
    d.text((300,y0+130), f"{o_type}", fill=(0,255,100) if o_type=="CALL" else (255,80,80), font=f_med, anchor="lm")
    d.text((50,y0+190), f"STRIKE", fill=(150,150,150), font=f_med)
    d.text((300,y0+190), f"{strike}", fill=(255,255,255), font=f_med, anchor="lm")
    d.text((50,y0+250), f"EXPIRY", fill=(150,150,150), font=f_med)
    d.text((300,y0+250), f"WEEKLY", fill=(180,255,180), font=f_med, anchor="lm")
    d.text((50,y0+310), f"SCORE", fill=(150,150,150), font=f_med)
    d.text((300,y0+310), f"{score}/7 {'GOLDEN' if score>=6 else 'GOOD'}", fill=(255,215,0), font=f_med, anchor="lm")

    # دخول
    d.rounded_rectangle([25,y0+450,520,y0+630], radius=20, outline=(0,255,100), width=3, fill=(5,30,20,200))
    d.text((50,y0+470), "ENTRY", fill=(150,255,150), font=f_med)
    d.text((50,y0+510), f"${entry:.2f}", fill=(0,255,100), font=f_big)
    # خط صاعد صغير
    d.line([(350,580),(400,560),(450,540)], fill=(0,255,100), width=3)

    # وقف
    d.rounded_rectangle([25,y0+650,520,y0+830], radius=20, outline=(255,50,50), width=3, fill=(30,10,15,200))
    d.text((50,y0+670), "STOP LOSS", fill=(255,150,150), font=f_med)
    d.text((50,y0+710), f"${stop:.2f}", fill=(255,60,60), font=f_big)
    d.line([(350,780),(400,790),(450,800)], fill=(255,60,60), width=3)

    # الأهداف - يمين مثل الأصلي تماما
    d.rounded_rectangle([550,y0,1055,y0+830], radius=20, outline=(0,220,255), width=3, fill=(5,20,35,200))
    d.text((580,y0+15), "TARGETS", fill=(0,220,255), font=f_med)
    t1=entry*1.5
    targets=[t1, t1*1.07, t1*1.15, t1*1.22, t1*1.30, t1*1.40, t1*1.50, t1*1.65, t1*1.80]
    for i,t in enumerate(targets):
        yy=y0+80+i*80
        d.ellipse([580,yy+5,600,yy+25], fill=(0,255,150))
        d.text((620,yy), f"{i+1}", fill=(0,0,0), font=f_med)
        d.line([(650,yy+15),(760,yy+15)], fill=(100,255,150), width=2)
        d.ellipse([760,yy+10,770,yy+20], fill=(150,255,180))
        d.text((790,yy), f"${t:.2f}", fill=(200,255,255), font=f_med)
    # سهم كبير و Bars مثل الأصلي
    d.line([(900, y0+750),(920, y0+300)], fill=(0,255,100), width=6)
    d.polygon([(920,y0+280),(890,y0+340),(950,y0+340)], fill=(0,255,100))
    for i in range(7):
        h = 40 + i*25
        d.rectangle([860+i*12, y0+800-h, 870+i*12, y0+800], fill=(0,200+i*8,100))

    # فوتر
    d.text((W//2, y0+900), "Not financial advice", fill=(80,80,80), font=f_med, anchor="mm")
    d.text((W//2, y0+950), "TrkHr Trading", fill=(0,220,255), font=f_big, anchor="mm")

    buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf, targets

def send_photo(buf, cap):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        r=requests.post(url, data={'chat_id':CHAT_ID,'caption':cap}, files={'photo':('avgo.png',buf,'image/png')}, timeout=20)
        return r.status_code==200
    except: return False

# باقي كود الفحص V70 نفسه ...
st.set_page_config(layout="wide")
now=datetime.now()+timedelta(hours=3); s=now.strftime('%H:%M:%S'); h=now.hour
is_fajer=2<=h<=6
st.title(f"{s} - V71 AVGO EDITION")
st.success(f"{s} KSA | V71 FANCY 3D | {'FAJR AUTO ON' if is_fajer else 'WAIT'}")

if st.button("📸 اختبار كرت AVGO الفخم"):
    buf,_=create_avgo_card("COIN","PUT",175,4.30,2.58,"COINBASE",5)
    if send_photo(buf, "🔔 COIN 175 PUT 5/7\nEntry $4.30 Stop $2.58\nT1 $6.45 (+50%) - AVGO Style"):
        st.success("✅ انرسل الكرت الفخم - شف تلجرام"); st.image(buf)
    else: st.error("فشل")

# نفس لوب الفحص السابق - يرسل كروت فخمة تلقائي
