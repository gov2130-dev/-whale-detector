import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
import pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 FINAL")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM"]

def is_market_open():
    now_ny = datetime.now(NY)
    if now_ny.weekday() >=5: return False
    return 570 <= now_ny.hour*60 + now_ny.minute <= 960

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg,'parse_mode':'Markdown'}, timeout=15)
        return r.status_code==200
    except: return False

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
        close=df['Close']; vol=df['Volume']; open_=df['Open']; high=df['High']; low=df['Low']
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
        for exp in tk.options[:2]:
            chain=tk.option_chain(exp)
            opts=chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            for _, row in opts.iterrows():
                strike=row['strike']
                dist=abs(strike-curr)/curr
                if dist>0.015: continue
                bid=row.get('bid',0) or 0
                ask=row.get('ask',0) or 0
                if bid==0 or ask==0: continue
                spread=(ask-bid)/ask*100
                if spread>5: continue
                vol=row.get('volume',0) or 0
                oi=row.get('openInterest',0) or 0
                qty=vol if vol>0 else oi
                if qty<200: continue
                mid=(bid+ask)/2
                premium=mid*qty*100
                if premium<100000: continue
                return {
                    "ticker":ticker, "dir":direction, "strike":strike, "exp":exp,
                    "premium":int(premium), "mid":round(mid,2), "spread":round(spread,1),
                    "dist":round(dist*100,2), "curr":round(curr,2), "qty":int(qty)
                }
        return None
    except: return None

st.title("🐋 V99 - العقود فقط")

if st.button("🚀 فحص وإرسال العقود"):
    sent=load()
    all_contracts=[]
    for t in WATCHLIST:
        direction=get_technical_direction(t)
        if not direction or direction=="NEUTRAL":
            continue

        contract=find_matching_contract(t, direction)
        if contract:
            all_contracts.append(contract)
            key=f"{contract['ticker']}_{contract['strike']}_{contract['exp']}_{datetime.now(RIYADH).date()}"
            if key not in sent:
                msg=(
                    f"🐋 *{contract['ticker']} {contract['dir']}*\n"
                    f"Strike: {contract['strike']} | Exp: {contract['exp']}\n"
                    f"Premium: ${contract['premium']:,} | Qty: {contract['qty']}\n"
                    f"Mid: ${contract['mid']} | Spread: {contract['spread']}% | Dist: {contract['dist']}%\n"
                    f"Price: ${contract['curr']}"
                )
                send(msg)
                sent.append(key)
                save(sent)
        time.sleep(0.5)

    if all_contracts:
        st.dataframe(pd.DataFrame(all_contracts).sort_values("premium", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد عقود مطابقة حاليا")

st.divider()
if is_market_open(): st.success("السوق مفتوح")
else: st.warning("السوق مغلق - نتائج تجريبية")
