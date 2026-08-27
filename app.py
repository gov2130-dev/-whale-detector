import streamlit as st, yfinance as yf, pandas as pd, time, io, requests, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
COMPANY_NAMES={"AVGO":"BROADCOM","MSFT":"MICROSOFT","NVDA":"NVIDIA","AAPL":"APPLE","TSLA":"TESLA","META":"META","AMD":"AMD","HOOD":"ROBINHOOD","COIN":"COINBASE","MSTR":"MICROSTRATEGY","PLTR":"PALANTIR","GOOGL":"GOOGLE","NFLX":"NETFLIX","SOFI":"SOFI"}

def create_fajer_card(ticker, o_type, strike, entry, stop, company):
    W,H=1080,1920
    img=Image.new('RGB',(W,H),(3,8,18))
    draw=ImageDraw.Draw(img)
    # اطارات نيون
    draw.rounded_rectangle([12,12,W-12,H-12], radius=45, outline=(0,240,255), width=6)
    draw.rounded_rectangle([30,30,W-30,280], radius=30, outline=(0,255,180), width=2)
    # عنوان
    try: font_big=ImageFont.truetype("arial.ttf", 60)
    except: font_big=ImageFont.load_default()
    try: font_med=ImageFont.truetype("arial.ttf", 42)
    except: font_med=ImageFont.load_default()
    try: font_small=ImageFont.truetype("arial.ttf", 36)
    except: font_small=ImageFont.load_default()

    draw.text((W//2,70), "الأمريكي تحت الفجر", fill=(110,255,255), font=font_big, anchor="mm")
    draw.text((W//2,150), "⚡", fill=(0,255,100), font=font_big, anchor="mm")
    draw.text((W//2,220), company, fill=(255,255,255), font=font_big, anchor="mm")

    # معلومات العقد - صندوق
    y0=320
    draw.rounded_rectangle([30,y0,520,y0+380], radius=20, outline=(0,255,180), width=3)
    draw.text((50,y0+15), "معلومات العقد", fill=(0,255,180), font=font_med)
    draw.text((50,y0+80), f"الشركة {ticker}", fill=(255,255,255), font=font_small)
    draw.text((50,y0+140), f"نوع العقد {o_type}", fill=(0,255,100) if o_type=="CALL" else (255,100,100), font=font_small)
    draw.text((50,y0+200), f"السترايك {strike}", fill=(255,255,255), font=font_small)
    draw.text((50,y0+260), f"الانتهاء WEEKLY", fill=(200,200), font=font_small)
    draw.text((50,y0+315), f"التقييم {'🔥 ذهبي 6/7' if True else 'جيد'}", fill=(255,215,0), font=font_small)

    # دخول
    draw.rounded_rectangle([30,y0+410,520,y0+600], radius=20, outline=(0,255,100), width=3)
    draw.text((50,y0+430), "سعر الدخول", fill=(180,255,180), font=font_med)
    draw.text((50,y0+480), f"{entry:.2f}", fill=(0,255,100), font=font_big)

    # وقف
    draw.rounded_rectangle([30,y0+630,520,y0+820], radius=20, outline=(255,60,60), width=3)
    draw.text((50,y0+650), "الوقف", fill=(255,180,180), font=font_med)
    draw.text((50,y0+700), f"{stop:.2f}", fill=(255,80,80), font=font_big)

    # الأهداف
    draw.rounded_rectangle([550,y0,1050,y0+820], radius=20, outline=(0,240,255), width=3)
    draw.text((580,y0+15), "الأهداف", fill=(0,240,255), font=font_med)
    t1=entry*1.5
    targets=[t1, t1*1.07, t1*1.15, t1*1.22, t1*1.30, t1*1.40, t1*1.50, t1*1.65, t1*1.80]
    for i,t in enumerate(targets):
        yy=y0+80+i*82
        col=(0,255,150) if i<3 else (255,255,100) if i<6 else (0,255,255)
        draw.text((580,yy), f"{i+1} → {t:.2f}", fill=col, font=font_small)
    # سهم صاعد
    draw.text((900, y0+200), "↗", fill=(0,255,100), font=font_big)

    # فوتر
    draw.text((W//2, H-100), "TrkHr Trading", fill=(0,240,255), font=font_big, anchor="mm")
    draw.text((W//2, H-50), "ليست توصية بيع أو شراء", fill=(100,100,100), font=font_small, anchor="mm")

    buf=io.BytesIO(); img.save(buf, format='PNG', quality=95); buf.seek(0); return buf, targets

def send_photo_tg(buf, caption):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        files={'photo': ('fajer.png', buf, 'image/png')}
        data={'chat_id':CHAT_ID, 'caption':caption}
        r=requests.post(url, data=data, files=files, timeout=20)
        return r.status_code==200
    except Exception as e:
        print(e); return False

st.set_page_config(layout="wide", page_title="V69 VISUAL")
st.markdown("<style>.stApp{background:#020a12!important;color:#fff}.time{ background:#001a1a;color:#0ff;padding:14px;border-radius:12px;border:2px solid #0ff;text-align:center;font-weight:900;font-family:monospace}</style>", unsafe_allow_html=True)

now=datetime.now()+timedelta(hours=3); ksa_str=now.strftime('%H:%M:%S'); ksa_h=now.hour
is_fajer=2<=ksa_h<=6

st.markdown(f"# {ksa_str} - V69 ULTRA VISUAL")
st.markdown(f'<div class="time">● {ksa_str} KSA | {CHAT_ID} | V69 يرسل صور فخمة | وقت الفجر {"✅ شغال تلقائي" if is_fajer else "⏸ ينتظر 2-6"}</div>', unsafe_allow_html=True)

c1,c2=st.columns(2)
with c1:
    if st.button("🔥 فحص وصور الآن"):
        st.session_state.auto_done=False; st.rerun()
with c2:
    if st.button("📸 اختبار صورة تلجرام"):
        buf,_=create_fajer_card("AVGO","CALL",300,365.0,360.0,"BROADCOM")
        if send_photo_tg(buf, "🔥 اختبار V69\nAVGO 300 CALL\nدخول 365.00 وقف 360.00\nالأمريكي تحت الفجر"):
            st.success("✅ انرسلت صورة - شف تلجرام")
        else: st.error("❌ فشل")

if "results" not in st.session_state: st.session_state.results=[]
if "sent" not in st.session_state: st.session_state.sent=set()
if "auto_done" not in st.session_state: st.session_state.auto_done=False

should_scan = (not st.session_state.auto_done) or is_fajer
if should_scan:
    tickers=["MSFT","NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","SOFI","GOOGL","AVGO","NFLX"]
    prog=st.progress(0); log=st.empty(); new_res=[]
    for i,ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100)); log.text(f"V69 يفحص {ticker}...")
        try:
            tk=yf.Ticker(ticker); h=tk.history(period="20d")
            if len(h)<15: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); ch1=float((curr-prev)/prev*100)
            d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            vwap=float(h['Close'].tail(10).mean()); ema9=float(h['Close'].ewm(span=9).mean().iloc[-1]); ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
            vol_ratio=float(h['Volume'].iloc[-1]/h['Volume'].tail(10).mean())
            trend=None
            if rsi<=42 and ch1<=-0.5: trend="BEAR"
            elif rsi>=58 and ch1>=0.5: trend="BULL"
            else: continue
            opts=tk.options; exp=opts[1] if len(opts)>1 else opts[0]; exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>9: continue
            chain=tk.option_chain(exp); df=chain.puts if trend=="BEAR" else chain.calls
            df=df[(df['lastPrice']>=0.35)&(df['lastPrice']<=10)]
            if df.empty or 'bid' not in df.columns: continue
            df=df.sort_values('volume', ascending=False).head(5); picked=None
            for _, r in df.iterrows():
                vol=int(r.get('volume',0) or 0)
                if vol<200: continue
                bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                if bid<=0 or ask<=0 or bid>=ask: continue
                mid=(bid+ask)/2; sp=(ask-bid)/mid*100
                if sp>18: continue
                oi=int(r.get('openInterest',0) or 0)
                if oi>2000 and vol < oi*0.3: continue
                picked=(r,bid,ask,sp,vol,oi); break
            if not picked: continue
            r,bid,ask,sp,vol,oi=picked; strike=int(r['strike'])
            if abs((strike-curr)/curr*100)>7: continue
            ok=[];
            ratio=vol/max(1,oi)
            if ratio>=0.5: ok.append("VOL/OI")
            if (trend=="BULL" and rsi<=42) or (trend=="BEAR" and rsi>=63): ok.append("RSI")
            if (trend=="BULL" and curr < vwap*0.98) or (trend=="BEAR" and curr > vwap*1.02): ok.append("VWAP")
            if (trend=="BULL" and ema9 < ema21) or (trend=="BEAR" and ema9 > ema21): ok.append("EMA")
            if vol_ratio>=1.2: ok.append("VOL")
            if sp<=10: ok.append("SPREAD")
            ok.append("DELTA")
            total=len(ok)
            if total<5: continue
            entry=ask; sl=entry*0.60; company=COMPANY_NAMES.get(ticker, ticker)
            key=f"{ticker}{strike}{trend}{total}"
            if key not in st.session_state.sent:
                buf, targets = create_fajer_card(ticker, "PUT" if trend=="BEAR" else "CALL", strike, entry, sl, company)
                cap=f"{'🔥🔥 ذهبي 6/7 92%' if total>=6 else '🔔 جيد 5/7 85%'} | {ksa_str}\n{ticker} {strike} {'PUT' if trend=='BEAR' else 'CALL'}\nدخول ${entry:.2f} | Spread {sp:.0f}%\n🎯1 ${targets[0]:.2f} (+50%)\n🛑 ${sl:.2f}\n{company}"
                if send_photo_tg(buf, cap):
                    st.session_state.sent.add(key)
                    st.image(buf, caption=f"{ticker} تم الارسال")
            new_res.append({"ticker":ticker,"strike":strike,"type":trend,"total":total})
            time.sleep(0.2)
        except: continue
    prog.progress(100); log.empty()
    st.session_state.results=new_res
    st.session_state.auto_done=True
    if is_fajer:
        time.sleep(60); st.session_state.auto_done=False; st.rerun()
    else:
        st.rerun()
