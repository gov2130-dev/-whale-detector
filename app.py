import streamlit as st, yfinance as yf, time, io, requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def create_blackgold_card(ticker, o_type, strike, entry, stop, company, score, curr_price, change):
    W,H = 1080, 1350
    img = Image.new('RGB', (W,H), (10,10,10))
    d = ImageDraw.Draw(img)
    try:
        f_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 65)
        f_big = ImageFont.truetype("DejaVuSans-Bold.ttf", 52)
        f_med = ImageFont.truetype("DejaVuSans.ttf", 36)
        f_small = ImageFont.truetype("DejaVuSans.ttf", 26)
        f_tiny = ImageFont.truetype("DejaVuSans.ttf", 22)
    except:
        f_title = f_big = f_med = f_small = f_tiny = ImageFont.load_default()

    # إطار ذهبي فخم
    d.rounded_rectangle([12,12,W-12,H-12], radius=32, outline=(212,175,55), width=3)
    d.rounded_rectangle([20,20,W-20,H-20], radius=29, outline=(60,45,15), width=1)

    # هيدر
    d.text((W//2, 70), "FAJR HUNTER", fill=(212,175,55), font=f_title, anchor="mm")
    d.text((W//2, 145), f"{company}", fill=(255,255,255), font=f_big, anchor="mm")
    d.text((W//2, 200), f"{ticker} ${curr_price:.2f} ({change:+.1f}%)", fill=(140,140,140), font=f_med, anchor="mm")

    # ENTRY
    d.rounded_rectangle([35,250,1045,460], radius=22, fill=(18,18,18), outline=(212,175,55), width=2)
    d.text((70,270), "ENTRY PRICE", fill=(212,175,55), font=f_small)
    d.text((70,305), f"${entry:.2f}", fill=(255,255,255), font=f_title)
    d.text((750,315), f"{o_type} {strike}", fill=(0,255,120) if o_type=="CALL" else (255,90,90), font=f_big, anchor="lm")
    d.text((70,390), f"TYPE: {'REAL MARKET DATA' if score>=5 else 'TEST'} • WEEKLY", fill=(90,90,90), font=f_tiny)

    # STOP & SCORE صف واحد
    d.rounded_rectangle([35,475,515,640], radius=20, fill=(18,18,18), outline=(50,50,50), width=1)
    d.text((70,495), "STOP LOSS", fill=(100,100,100), font=f_small)
    d.text((70,530), f"${stop:.2f}", fill=(255,70,70), font=f_big)

    d.rounded_rectangle([565,475,1045,640], radius=20, fill=(18,18,18), outline=(212,175,55) if score>=6 else (50,50,50), width=2 if score>=6 else 1)
    d.text((600,495), "SCORE", fill=(100,100,100), font=f_small)
    d.text((600,530), f"{score}/7", fill=(212,175,55), font=f_big)
    d.text((770,540), f"{'GOLDEN' if score>=6 else 'GOOD'}", fill=(255,215,0), font=f_med)

    # TARGETS
    d.rounded_rectangle([35,655,1045,1210], radius=22, fill=(18,18,18), outline=(212,175,55), width=2)
    d.text((70,675), "TARGETS", fill=(212,175,55), font=f_med)

    t1=entry*1.5
    targets=[t1, t1*1.15, t1*1.30, t1*1.50, t1*1.80, t1*2.10]
    percents=[50,72,95,125,170,215]
    for i in range(6):
        y=730+i*75
        d.rounded_rectangle([60,y,1040-40,y+60], radius=12, fill=(28,28,28))
        d.ellipse([75,y+10,110,y+45], fill=(212,175,55))
        d.text((92,y+27), f"{i+1}", fill=(0,0,0), font=f_small, anchor="mm")
        d.text((140,y+12), f"${targets[i]:.2f}", fill=(255,255,255), font=f_med)
        d.text((900,y+12), f"+{percents[i]}%", fill=(212,175,55), font=f_med, anchor="lm")

    d.text((W//2, 1250), "TRKHR • NOT FINANCIAL ADVICE • REAL DATA FROM YFINANCE", fill=(60,60,60), font=f_tiny, anchor="mm")
    buf=io.BytesIO(); img.save(buf, format='PNG', quality=95); buf.seek(0); return buf, targets

def send_photo(buf, cap):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        r=requests.post(url, data={'chat_id':CHAT_ID,'caption':cap}, files={'photo':('card.png',buf,'image/png')}, timeout=20)
        return r.status_code==200
    except: return False

st.set_page_config(page_title="V72 BLACK GOLD", layout="wide")
now=datetime.now()+timedelta(hours=3); s=now.strftime('%H:%M:%S'); h=now.hour
is_fajer=2<=h<=6
st.title(f"🕋 {s} KSA - V72 BLACK GOLD")
st.info(f"CHAT_ID {CHAT_ID} | {'🔥 FAJR AUTO ON 2-6 AM' if is_fajer else '⏳ WAIT FAJR'} | REAL DATA")

if st.button("📸 اختبار الأسود الذهبي"):
    buf,_=create_blackgold_card("COIN","PUT",175,4.30,2.58,"COINBASE",5, 412.5, -1.2)
    if send_photo(buf, "🔔 TEST BLACK GOLD\nCOIN 175 PUT 5/7 GOOD\nEntry $4.30 Stop $2.58\nREAL DATA"):
        st.success("✅ انرسل - شف تلجرام"); st.image(buf)
    else: st.error("فشل")

if "sent" not in st.session_state: st.session_state.sent=set()
if "auto" not in st.session_state: st.session_state.auto=False

# فحص حقيقي
if (not st.session_state.auto) or is_fajer:
    tickers=["MSFT","NVDA","AAPL","AVGO","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","GOOGL","AMZN"]
    prog=st.progress(0); log=st.empty(); found=st.empty()
    cnt=0
    for i,ticker in enumerate(tickers):
        prog.progress(int((i+1)/len(tickers)*100)); log.text(f"يفحص {ticker}... (حقيقي)")
        try:
            tk=yf.Ticker(ticker); hist=tk.history(period="20d")
            if len(hist)<15: continue
            curr=float(hist['Close'].iloc[-1]); prev=float(hist['Close'].iloc[-2]); ch=float((curr-prev)/prev*100)
            d=hist['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            trend="BEAR" if rsi>=63 and ch<=-0.3 else "BULL" if rsi<=40 and ch>=0.3 else None
            if not trend: continue
            opts=tk.options;
            if not opts: continue
            exp=opts[1] if len(opts)>1 else opts[0]
            chain=tk.option_chain(exp); df=chain.puts if trend=="BEAR" else chain.calls
            df=df[(df['lastPrice']>=0.4)&(df['lastPrice']<=9)]
            if df.empty: continue
            df=df.sort_values('volume', ascending=False).head(3)
            for _,rw in df.iterrows():
                vol=int(rw.get('volume',0)or 0)
                if vol<200: continue
                bid=float(rw.get('bid',0)or 0); ask=float(rw.get('ask',0)or 0)
                if bid<=0 or ask<=0: continue
                if (ask-bid)/((ask+bid)/2)*100>18: continue
                strike=int(rw['strike']); entry=ask; stop=entry*0.6; total=6 if vol>800 else 5
                key=f"{ticker}{strike}{trend}{exp}"
                if key in st.session_state.sent: continue
                try: comp=tk.info.get('shortName', ticker)[:20]
                except: comp=ticker
                buf,tg=create_blackgold_card(ticker, "PUT" if trend=="BEAR" else "CALL", strike, entry, stop, comp, total, curr, ch)
                emoji="🔥🔥 GOLDEN" if total>=6 else "🔔 GOOD"
                cap=f"{emoji} {s} REAL\n{ticker} {strike} {'PUT' if trend=='BEAR' else 'CALL'} {total}/7\nPrice ${curr:.2f} ({ch:+.1f}%) Vol {vol}\nEntry ${entry:.2f} Stop ${stop:.2f}\nT1 ${tg[0]:.2f} (+50%)"
                if send_photo(buf, cap):
                    st.session_state.sent.add(key); cnt+=1
                    found.success(f"✅ {ticker} انرسل {total}/7"); st.image(buf)
                break
        except Exception as e:
            continue
    prog.progress(100); log.empty()
    st.success(f"انتهى الفحص - انرسل {cnt} عقد حقيقي")
    st.session_state.auto=True
    if is_fajer:
        time.sleep(60); st.session_state.auto=False; st.rerun()
