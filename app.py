import streamlit as st, yfinance as yf, pandas as pd, time, urllib.request, urllib.parse, io
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta
import requests

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def create_card(ticker, o_type, strike, entry, stop, targets, company_name):
    # خلفية نيون
    W, H = 1080, 1920
    img = Image.new('RGB', (W,H), (5,10,20))
    d = ImageDraw.Draw(img)
    # إطار نيون
    d.rounded_rectangle([10,10,W-10,H-10], radius=40, outline=(0,255,255), width=4)
    # عنوان
    d.text((W//2,80), "الأمريكي تحت الفجر", fill=(0,255,255), anchor="mm", font=ImageFont.load_default())
    d.text((W//2,200), company_name, fill=(255,255,255), anchor="mm", font=ImageFont.load_default())
    # معلومات العقد
    y=600
    d.rectangle([30,y,500,y+350], outline=(0,255,150), width=3)
    d.text((50,y+20), f"الشركة {ticker}", fill=(255,255,255))
    d.text((50,y+80), f"نوع العقد {o_type}", fill=(0,255,100))
    d.text((50,y+140), f"السترايك {strike}", fill=(255,255,255))
    # دخول ووقف
    d.rectangle([30,y+380,500,y+580], outline=(0,255,100), width=3)
    d.text((50,y+400), f"سعر الدخول {entry:.2f}", fill=(0,255,100))
    d.rectangle([30,y+600,500,y+780], outline=(255,50,50), width=3)
    d.text((50,y+620), f"الوقف {stop:.2f}", fill=(255,80,80))
    # أهداف
    d.rectangle([540,600,1050,1550], outline=(0,255,255), width=3)
    d.text((560,620), "الأهداف", fill=(255,255,255))
    for i,t in enumerate(targets[:9]):
        d.text((580, 680+i*90), f"{i+1} -> {t:.2f}", fill=(0,255,150))
    d.text((W//2, H-80), "TrkHr Trading", fill=(0,255,255), anchor="mm")
    buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf

def send_photo_tg(photo_buf, caption):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files={'photo': ('card.png', photo_buf, 'image/png')}
        data={'chat_id':CHAT_ID, 'caption':caption}
        requests.post(url, data=data, files=files, timeout=15)
        return True
    except: return False

# ... باقي كود الفحص V68 نفسه ...
# عند ما يلقى عقد ذهبي:
# targets = [t1, t1*1.05, t1*1.1 ...]
# card = create_card(ticker, type, strike, ask, sl, targets, ticker)
# send_photo_tg(card, f"🔥 {ticker} {strike} {type} 6/7 92%")
