import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date
import pytz
import pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370" # تأكد انه نفسه اللي في BotFather
SENT_FILE="sent_today.json"
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 FINAL")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM","SOFI","PLTR","COIN","HOOD"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        # شلت parse_mode عشان $ و % ما تخرب الرسالة
        data={'chat_id':CHAT_ID,'text':msg}
        r=requests.post(url, data=data, timeout=15)
        st.write(f"Telegram Status: {r.status_code} - {r.text[:200]}") # Debug
        return r.status_code==200
    except Exception as e:
        st.error(f"خطأ ارسال: {e}")
        return False

def load():
    if os.path.exists(SENT_FILE):
        try: return json.load(open(SENT_FILE))
        except: return []
    return []
def save(d): json.dump(d, open(SENT_FILE,'w'))

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

def find_matching_contract(ticker, direction):
    real=TICKER_MAP.get(ticker,ticker)
    try:
        tk=yf.Ticker(real)
        curr=tk.fast_info.get('last_price')
        if not curr:
            curr=float(tk.history(period="1d")['Close'].iloc[-1])
        else: curr=float(curr)
        for exp_str in tk.options[:3]:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - date.today()).days
            if dte < 1 or dte > 30: continue
            chain=tk.option_chain(exp_str)
            opts=chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            for _, row in opts.iterrows():
                strike=row['strike']
                dist=abs(strike-curr)/curr
                if dist>0.02: continue
                bid=row.get('bid',0) or 0
                ask=row.get('ask',0) or 0
                if bid==0 or ask==0: continue
                spread=(ask-bid)/ask*100 if ask>0 else 100
                if spread>6: continue
                vol=row.get('volume',0) or 0
                oi=row.get('openInterest',0) or 0
                qty=vol if vol>0 else oi
                if qty<100: continue
                mid=(bid+ask)/2
                if mid < 0.2: continue
                premium=mid*qty*100
                if premium<80000: continue
                try:
                    day_range = tk.history(period="1d")
                    low_r = round(float(day_range['Low'].iloc[-1]),2)
                    high_r = round(float(day_range['High'].iloc[-1]),2)
                except:
                    low_r = round(mid,2)
                    high_r = round(mid,2)
                close_p = round(float(row.get('lastPrice', mid) or mid),2)
                entry = round(mid,2)
                bid_p = round(bid,2)
                bw = round(dist*100,2)
                stop = round(entry*0.5,2)
                if direction=="CALL":
                    t1_s = round(strike + 0.3,2)
                    t2_s = round(strike + 0.6,2)
                    t3_s = round(strike + 1.0,2)
                else:
                    t1_s = round(strike - 0.3,2)
                    t2_s = round(strike - 0.6,2)
                    t3_s = round(strike - 1.0,2)
                t1_c = round(entry*1.5,2)
                t2_c = round(entry*2.3,2)
                t3_c = round(entry*3.2,2)
                return {
                    "ticker":ticker, "dir":direction, "strike":int(strike) if strike==int(strike) else strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":bw,
                    "range_low":low_r, "range_high":high_r, "close":close_p,
                    "entry":entry, "bid":bid_p, "stop":stop,
                    "t1_s":t1_s, "t2_s":t2_s, "t3_s":t3_s,
                    "t1_c":t1_c, "t2_c":t2_c, "t3_c":t3_c,
                }
        return None
    except: return None

st.title("🐋 V99 - اختبار التيليجرام")

# زر اختبار سريع
if st.button("📨 اختبار التيليجرام فقط"):
    if send("تجربة بوت V99 🐋"):
        st.success("انرسل - شيك التيليجرام")
    else:
        st.error("ما انرسل - شيك الـ CHAT_ID والبوت")

st.divider()

if st.button("🚀 فحص العقود وارسال"):
    sent=load()
    all_contracts=[]
    for t in WATCHLIST:
        direction=get_technical_direction(t)
        if not direction or direction=="NEUTRAL":
            continue
        contract=find_matching_contract(t, direction)
        if contract:
            all_contracts.append(contract)
        time.sleep(0.3)

    if not all_contracts:
        st.info("لا يوجد عقود")
    else:
        for c in all_contracts:
            emoji = "🟢" if c['dir']=="CALL" else "🔴"
            text = (
                f"{emoji} {c['ticker']} {c['strike']} {c['dir']} 🐋\n"
                f"Exp: {c['exp']} ({c['dte']}d) Stock: ${c['curr']} BW {c['bw']}%\n"
                f"Range: ${c['range_low']} - ${c['range_high']} Close: ${c['close']}\n"
                f"Entry: ${c['entry']} Bid: ${c['bid']}\n"
                f"Stop: ${c['stop']}\n"
                f"Target Stock: {c['t1_s']} > {c['t2_s']} > {c['t3_s']}\n"
                f"Target Contract: ${c['t1_c']} (+50%) | ${c['t2_c']} (+130%) | ${c['t3_c']} (+220%)"
            )
            st.code(text)
            # ارسال مباشر بدون شرط التكرار للاختبار
            send(text)
            time.sleep(1)
