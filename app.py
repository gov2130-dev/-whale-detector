import streamlit as st, yfinance as yf, time, io, requests
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def create_card(ticker, o_type, strike, entry, stop, company, total):
    W,H=1080,1350
    img=Image.new('RGB',(W,H),(7,12,22))
    d=ImageDraw.Draw(img)
    # نيون
    d.rounded_rectangle([10,10,W-10,H-10], radius=30, outline=(0,255,200), width=4)
    d.rounded_rectangle([20,20,W-20,180], radius=20, outline=(0,255,150), width=2)

    # Fonts
    f1=ImageFont.load_default()
    # عنوان
    d.text((W//2,40), "AL-AMRIKI TAHT AL-FAJR", fill=(0,255,200), anchor="mm", font=f1)
    d.text((W//2,90), company, fill=(255,255,255), anchor="mm", font=f1)
    d.text((W//2,130), f"{'GOLDEN 6/7 92%' if total>=6 else 'GOOD 5/7 85%'}", fill=(255,215,0), anchor="mm", font=f1)

    # BOX LEFT
    d.rounded_rectangle([20,200,500,500], radius=15, outline=(0,255,120), width=3)
    d.text((40,220), f"TICKER: {ticker}", fill=(255,255,255), font=f1)
    d.text((40,270), f"TYPE: {o_type}", fill=(0,255,100), font=f1)
    d.text((40,320), f"STRIKE: {strike}", fill=(255,255,255), font=f1)
    d.text((40,370), f"EXP: WEEKLY", fill=(180,180,180), font=f1)
    d.text((40,420), f"SCORE: {total}/7", fill=(255,215,0), font=f1)

    # ENTRY
    d.rounded_rectangle([20,520,500,680], radius=15, outline=(0,255,80), width=3)
    d.text((40,540), "ENTRY", fill=(150,255,150), font=f1)
    d.text((40,580), f"${entry:.2f}", fill=(0,255,80), font=f1)

    # STOP
    d.rounded_rectangle([20,700,500,860], radius=15, outline=(255,70,70), width=3)
    d.text((40,720), "STOP LOSS", fill=(255,150,150), font=f1)
    d.text((40,760), f"${stop:.2f}", fill=(255,70,70), font=f1)

    # TARGETS
    d.rounded_rectangle([530,200,1060,860], radius=15, outline=(0,220,255), width=3)
    d.text((550,220), "TARGETS", fill=(0,220,255), font=f1)
    t1=entry*1.5
    tg=[t1, t1*1.07, t1*1.15, t1*1.22, t1*1.30, t1*1.40, t1*1.50, t1*1.65, t1*1.80]
    for i,t in enumerate(tg):
        y=270+i*60
        d.text((550,y), f"{i+1} -> ${t:.2f} (+{int((t/entry-1)*100)}%)", fill=(0,255,150), font=f1)

    d.text((W//2, 900), "TrkHr Trading - Not financial advice", fill=(0,200,200), anchor="mm", font=f1)
    buf=io.BytesIO(); img.save(buf, format='PNG'); buf.seek(0); return buf, tg

def send_photo(buf, cap):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
        r=requests.post(url, data={'chat_id':CHAT_ID,'caption':cap}, files={'photo':('card.png',buf,'image/png')}, timeout=20)
        return r.status_code==200
    except: return False

st.set_page_config(layout="wide")
now=datetime.now()+timedelta(hours=3); s=now.strftime('%H:%M:%S'); h=now.hour
is_fajer=2<=h<=6
st.title(f"{s} - V70 FINAL")
st.success(f"{s} KSA | {CHAT_ID} | V70 CLEAN ENGLISH | {'FAJR AUTO ON' if is_fajer else 'WAIT FAJR'}")

if st.button("📸 اختبار صورة نظيفة"):
    buf,_=create_card("AVGO","CALL",300,365,360,"BROADCOM",6)
    if send_photo(buf, "🔥 V70 TEST\nAVGO 300 CALL 6/7 GOLDEN\nEntry $365 Stop $360"):
        st.success("✅ انرسلت واضحة - شف تلجرام"); st.image(buf)
    else: st.error("فشل")

if "sent" not in st.session_state: st.session_state.sent=set()
if "auto" not in st.session_state: st.session_state.auto=False

if (not st.session_state.auto) or is_fajer:
    import pandas as pd
    tickers=["MSFT","NVDA","AAPL","AVGO","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD"]
    prog=st.progress(0); log=st.empty()
    for i,ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100)); log.text(f"يفحص {ticker}...")
        try:
            tk=yf.Ticker(ticker); hist=tk.history(period="20d")
            if len(hist)<15: continue
            curr=float(hist['Close'].iloc[-1]); prev=float(hist['Close'].iloc[-2]); ch=float((curr-prev)/prev*100)
            d=hist['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            trend="BEAR" if rsi>=63 and ch<=-0.3 else "BULL" if rsi<=40 and ch>=0.3 else None
            if not trend: continue
            opts=tk.options; exp=opts[1] if len(opts)>1 else opts[0]
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
                key=f"{ticker}{strike}{trend}"
                if key in st.session_state.sent: continue
                buf,tg=create_card(ticker, "PUT" if trend=="BEAR" else "CALL", strike, entry, stop, ticker, total)
                cap=f"{'🔥 GOLDEN 6/7' if total>=6 else '🔔 GOOD 5/7'} {s}\n{ticker} {strike} {trend}\nEntry ${entry:.2f} Stop ${stop:.2f}\nT1 ${tg[0]:.2f} (+50%)"
                if send_photo(buf, cap):
                    st.session_state.sent.add(key); st.image(buf, caption=f"{ticker} Sent")
                break
        except: continue
    prog.progress(100); log.empty()
    st.session_state.auto=True
    if is_fajer:
        time.sleep(60); st.session_state.auto=False; st.rerun()
