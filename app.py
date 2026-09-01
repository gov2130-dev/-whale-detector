import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date
import pytz
import pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')
st.set_page_config(layout="wide", page_title="V99 FINAL")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM","SOFI","PLTR","COIN"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
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

                # حسابات الصيغة الجديدة
                bw = dist*100
                entry = round(mid,2)
                bid_p = round(bid,2)
                # Range من اليوم
                try:
                    day_range = tk.history(period="1d")
                    low_r = round(float(day_range['Low'].iloc[-1]),2)
                    high_r = round(float(day_range['High'].iloc[-1]),2)
                except:
                    low_r = entry
                    high_r = entry

                close_p = round(float(row.get('lastPrice', entry) or entry),2)
                stop = round(entry*0.5,2)

                # اهداف السهم والعقد
                if direction=="CALL":
                    t1_stock = round(strike + 0.3,2)
                    t2_stock = round(strike + 0.6,2)
                    t3_stock = round(strike + 1.0,2)
                else:
                    t1_stock = round(strike - 0.3,2)
                    t2_stock = round(strike - 0.6,2)
                    t3_stock = round(strike - 1.0,2)

                t1_cont = round(entry*1.5,2)
                t2_cont = round(entry*2.3,2)
                t3_cont = round(entry*3.2,2)

                return {
                    "ticker":ticker, "dir":direction, "strike":int(strike) if strike==int(strike) else strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":round(bw,2),
                    "range_low":low_r, "range_high":high_r, "close":close_p,
                    "entry":entry, "bid":bid_p, "stop":stop,
                    "t1_s":t1_stock, "t2_s":t2_stock, "t3_s":t3_stock,
                    "t1_c":t1_cont, "t2_c":t2_cont, "t3_c":t3_cont,
                    "premium":int(premium)
                }
        return None
    except: return None

st.title("🐋 V99 - صيغة SOFI")

if st.button("🚀 فحص وإرسال"):
    sent=load()
    all_contracts=[]
    for t in WATCHLIST:
        direction=get_technical_direction(t)
        if not direction or direction=="NEUTRAL":
            continue
        contract=find_matching_contract(t, direction)
        if contract:
            all_contracts.append(contract)
            key=f"{contract['ticker']}_{contract['strike']}_{contract['exp']}_{date.today()}"
            if key not in sent:
                # الصيغة الجديدة بدون الأصفر
                msg = (
                    f"🟢 {contract['ticker']} {contract['strike']} {contract['dir']} 🐋\n"
                    f"Exp: {contract['exp']} ({contract['dte']}d) Stock: ${contract['curr']} BW {contract['bw']}%\n"
                    f"Range: ${contract['range_low']} - ${contract['range_high']} Close: ${contract['close']}\n"
                    f"Entry: ${contract['entry']} Bid: ${contract['bid']}\n"
                    f"Stop: ${contract['stop']}\n"
                    f"Target Stock: {contract['t1_s']} > {contract['t2_s']} > {contract['t3_s']}\n"
                    f"Target Contract: ${contract['t1_c']} (+50%) | ${contract['t2_c']} (+130%) | ${contract['t3_c']} (+220%)"
                )
                send(msg)
                sent.append(key)
                save(sent)
        time.sleep(0.5)

    if all_contracts:
        st.dataframe(pd.DataFrame(all_contracts), use_container_width=True, hide_index=True)
    else:
        st.info("لا يوجد عقود")
