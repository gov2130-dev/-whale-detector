import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date
import pytz, pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
st.set_page_config(layout="wide", page_title="V99 CLEAN")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM","SOFI","PLTR","COIN","HOOD"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data={'chat_id': CHAT_ID, 'text': msg}
        r=requests.post(url, data=data, timeout=20)
        if r.status_code==200:
            return True
        else:
            st.error(f"Telegram Error: {r.text}")
            return False
    except Exception as e:
        st.error(f"خطأ: {e}")
        return False

def get_technical_direction(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    try:
        df=yf.download(real, period="10d", interval="30m", progress=False, auto_adjust=True)
        if len(df)<40: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns=df.columns.get_level_values(0)
        close=df['Close']; vol=df['Volume']
        vwap=(close*vol).cumsum()/vol.cumsum()
        ema200=close.ewm(200).mean()
        ema20=close.ewm(20).mean()
        ema50=close.ewm(50).mean()
        score=0
        score+= 1 if close.iloc[-1]>vwap.iloc[-1] else -1
        score+= 1 if close.iloc[-1]>ema200.iloc[-1] else -1
        score+= 1 if ema20.iloc[-1]>ema50.iloc[-1] else -1
        delta=close.diff()
        gain=delta.where(delta>0,0).rolling(14).mean()
        loss=-delta.where(delta<0,0).rolling(14).mean()
        rsi=100-(100/(1+gain/loss))
        score+= 1 if rsi.iloc[-1]>60 else -1 if rsi.iloc[-1]<40 else 0
        if score>=3: return "CALL"
        if score<=-3: return "PUT"
        return "NEUTRAL"
    except: return None

def find_contract(ticker, direction):
    real=TICKER_MAP.get(ticker,ticker)
    try:
        tk=yf.Ticker(real)
        curr=float(tk.fast_info.get('last_price') or tk.history(period="1d")['Close'].iloc[-1])
        for exp_str in tk.options[:3]:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - date.today()).days
            if dte < 1 or dte > 14: continue
            chain=tk.option_chain(exp_str)
            opts=chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            for _, row in opts.iterrows():
                strike=row['strike']
                if abs(strike-curr)/curr>0.02: continue
                bid=row.get('bid',0) or 0
                ask=row.get('ask',0) or 0
                if bid==0 or ask==0: continue
                if (ask-bid)/ask*100>6: continue
                vol=row.get('volume',0) or 0
                oi=row.get('openInterest',0) or 0
                qty=vol if vol>0 else oi
                if qty<100: continue
                mid=(bid+ask)/2
                if mid<0.2 or mid*qty*100<80000: continue
                dr=tk.history(period="1d")
                low_r=round(float(dr['Low'].iloc[-1]),2)
                high_r=round(float(dr['High'].iloc[-1]),2)
                entry=round(mid,2)
                return {
                    "ticker":ticker, "dir":direction, "strike":int(strike) if strike==int(strike) else strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":round(abs(strike-curr)/curr*100,2),
                    "range_low":low_r, "range_high":high_r, "close":round(float(row.get('lastPrice', mid) or mid),2),
                    "entry":entry, "bid":round(bid,2), "stop":round(entry*0.5,2),
                    "t1_c":round(entry*1.5,2), "t2_c":round(entry*2.3,2), "t3_c":round(entry*3.2,2),
                    "t1_s":round(strike+0.3,2) if direction=="CALL" else round(strike-0.3,2),
                    "t2_s":round(strike+0.6,2) if direction=="CALL" else round(strike-0.6,2),
                    "t3_s":round(strike+1.0,2) if direction=="CALL" else round(strike-1.0,2),
                }
        return None
    except: return None

st.title("🐋 V99 - ارسال تلقائي")

if st.button("🚀 فحص وارسال للتيليجرام تلقائي"):
    sent_count=0
    for t in WATCHLIST:
        direction=get_technical_direction(t)
        if not direction or direction=="NEUTRAL": continue
        c=find_contract(t,direction)
        if not c: continue
        
        emoji = "🟢" if c['dir']=="CALL" else "🔴"
        # صيغة نظيفة 100% بدون سطر فيه اسم السهم لحاله
        text = (
            f"{emoji} {c['ticker']} {c['strike']} {c['dir']} 🐋\n"
            f"Exp: {c['exp']} ({c['dte']}d) Stock: ${c['curr']} BW {c['bw']}%\n"
            f"Range: ${c['range_low']} - ${c['range_high']} Close: ${c['close']}\n"
            f"Entry: ${c['entry']} Bid: ${c['bid']}\n"
            f"Stop: ${c['stop']}\n"
            f"Target Stock: {c['t1_s']} > {c['t2_s']} > {c['t3_s']}\n"
            f"Target Contract: ${c['t1_c']} (+50%) | ${c['t2_c']} (+130%) | ${c['t3_c']} (+220%)"
        )
        
        st.code(text) # عرض فقط
        
        # ارسال تلقائي
        if send(text):
            st.success(f"✅ انرسل {c['ticker']} للتيليجرام")
            sent_count+=1
        else:
            st.error(f"❌ فشل ارسال {c['ticker']}")
        time.sleep(1)
    
    st.info(f"تم ارسال {sent_count} عقد للتيليجرام")

# زر اختبار سريع
if st.button("📨 اختبار تيليجرام"):
    if send("تجربة V99 - اذا وصلك يعني شغال ✅"):
        st.success("تم الارسال - شيك التيليجرام")
