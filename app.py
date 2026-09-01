import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime, date
import pytz, pandas as pd

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
st.set_page_config(layout="wide", page_title="V99 + النتائج")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM","SOFI","PLTR","COIN","HOOD"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def get_current_option_price(ticker, exp, strike, direction):
    try:
        real = TICKER_MAP.get(ticker,ticker)
        tk = yf.Ticker(real)
        chain = tk.option_chain(exp)
        opts = chain.calls if direction=="CALL" else chain.puts
        row = opts[opts['strike']==strike]
        if row.empty:
            # اقرب سترايك
            row = opts.iloc[(opts['strike']-strike).abs().argsort()[:1]]
        bid = float(row['bid'].iloc[0] or 0)
        ask = float(row['ask'].iloc[0] or 0)
        last = float(row['lastPrice'].iloc[0] or 0)
        mid = (bid+ask)/2 if bid and ask else last
        return round(mid,2), round(last,2), round(bid,2)
    except:
        return None, None, None

def check_result(entry, stop, t1, t2, t3, current_price):
    if current_price is None:
        return "⏳ انتظار", 0
    pnl = (current_price - entry)/entry*100
    if current_price <= stop:
        return f"🔴 ضرب وقف {pnl:.1f}%", pnl
    if current_price >= t3:
        return f"🟢 هدف 3 {pnl:.1f}%", pnl
    if current_price >= t2:
        return f"🟢 هدف 2 {pnl:.1f}%", pnl
    if current_price >= t1:
        return f"🟢 هدف 1 {pnl:.1f}%", pnl
    return f"⚪ شغال {pnl:.1f}%", pnl

# باقي دوال التحليل نفسها
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
        curr=tk.fast_info.get('last_price') or float(tk.history(period="1d")['Close'].iloc[-1])
        curr=float(curr)
        for exp_str in tk.options[:3]:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - date.today()).days
            if dte < 1 or dte > 30: continue
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
                day_range = tk.history(period="1d")
                low_r = round(float(day_range['Low'].iloc[-1]),2)
                high_r = round(float(day_range['High'].iloc[-1]),2)
                entry = round(mid,2)
                return {
                    "ticker":ticker, "dir":direction, "strike":int(strike) if strike==int(strike) else strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":round(abs(strike-curr)/curr*100,2),
                    "range_low":low_r, "range_high":high_r, "close":round(float(row.get('lastPrice', mid) or mid),2),
                    "entry":entry, "bid":round(bid,2), "stop":round(entry*0.5,2),
                    "t1_s":round(strike+0.3,2) if direction=="CALL" else round(strike-0.3,2),
                    "t2_s":round(strike+0.6,2) if direction=="CALL" else round(strike-0.6,2),
                    "t3_s":round(strike+1.0,2) if direction=="CALL" else round(strike-1.0,2),
                    "t1_c":round(entry*1.5,2), "t2_c":round(entry*2.3,2), "t3_c":round(entry*3.2,2),
                }
        return None
    except: return None

st.title("🐋 V99 - مع النتائج المباشرة")

if st.button("🚀 فحص"):
    all_contracts=[]
    for t in WATCHLIST:
        d=get_technical_direction(t)
        if not d or d=="NEUTRAL": continue
        c=find_matching_contract(t,d)
        if c: all_contracts.append(c)
        time.sleep(0.2)

    if not all_contracts:
        st.info("لا يوجد")
    else:
        for c in all_contracts:
            curr_price, last_price, curr_bid = get_current_option_price(c['ticker'], c['exp'], c['strike'], c['dir'])
            status, pnl = check_result(c['entry'], c['stop'], c['t1_c'], c['t2_c'], c['t3_c'], curr_price)

            emoji = "🟢" if c['dir']=="CALL" else "🔴"
            msg = (
                f"{emoji} {c['ticker']} {c['strike']} {c['dir']} 🐋\n"
                f"Exp: {c['exp']} ({c['dte']}d) Stock: ${c['curr']} BW {c['bw']}%\n"
                f"Range: ${c['range_low']} - ${c['range_high']} Close: ${c['close']}\n"
                f"Entry: ${c['entry']} Bid: ${c['bid']} | Now: ${curr_price} ({status})\n"
                f"Stop: ${c['stop']}\n"
                f"Target Stock: {c['t1_s']} > {c['t2_s']} > {c['t3_s']}\n"
                f"Target Contract: ${c['t1_c']} (+50%) | ${c['t2_c']} (+130%) | ${c['t3_c']} (+220%)"
            )
            # في الصفحة مع لون حسب النتيجة
            if "هدف" in status: st.success(msg)
            elif "وقف" in status: st.error(msg)
            else: st.code(msg)

            if st.button(f"ارسال {c['ticker']}", key=f"s_{c['ticker']}_{c['strike']}"):
                send(msg)
