import streamlit as st, yfinance as yf, requests, json, os, time
import pandas as pd
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
BASE="daily_results"
os.makedirs(BASE, exist_ok=True)
WATCHLIST=["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI"]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return True
    except:
        return False

def get_fibo(h,l,d):
    diff = (h-l) or 1.0
    if d=="PUT":
        return round(l-diff*0.382,2), round(l-diff*0.618,2), round(l-diff*1.0,2)
    return round(h+diff*0.382,2), round(h+diff*0.618,2), round(h+diff*1.0,2)

def get_strong_direction(ticker):
    try:
        tk = yf.Ticker(ticker)
        df15 = tk.history(period="10d", interval="15m")
        df5 = tk.history(period="5d", interval="5m")
        df_daily = tk.history(period="20d")
        if df15.empty or len(df15) < 30:
            df15 = df_daily
        if df5.empty:
            df5 = df_daily
        curr = float(df15['Close'].iloc[-1])
        ema9 = df15['Close'].ewm(span=9, min_periods=1).mean().iloc[-1]
        ema20 = df15['Close'].ewm(span=20, min_periods=1).mean().iloc[-1]
        ema50 = df15['Close'].ewm(span=50, min_periods=1).mean().iloc[-1]
        try:
            df5['TP'] = (df5['High']+df5['Low']+df5['Close'])/3
            vwap = (df5['TP']*df5['Volume']).sum() / df5['Volume'].sum()
            if pd.isna(vwap):
                vwap = df15['Close'].mean()
        except:
            vwap = df15['Close'].mean()
        try:
            delta = df15['Close'].diff()
            gain = delta.where(delta>0,0).rolling(14, min_periods=5).mean()
            loss = -delta.where(delta<0,0).rolling(14, min_periods=5).mean()
            rs = gain / loss.replace(0,0.001)
            rsi = 100 - (100/(1+rs))
            rsi_now = float(rsi.iloc[-1])
            if pd.isna(rsi_now):
                rsi_now = 50
        except:
            rsi_now = 50
        try:
            avg_vol = df_daily['Volume'].mean()
            vol_now = df5['Volume'].sum() if not df5.empty else df_daily['Volume'].iloc[-1]
            vol_ok = vol_now > avg_vol * 0.5
        except:
            vol_ok = True
        call_strong = ema9 > ema20 and ema9 > ema50 and curr > vwap and 50 <= rsi_now <= 75 and vol_ok
        put_strong = ema9 < ema20 and ema9 < ema50 and curr < vwap and 25 <= rsi_now <= 50 and vol_ok
        if call_strong:
            return "CALL"
        if put_strong:
            return "PUT"
        return None
    except:
        return None

@st.cache_data(ttl=20)
def get_now_fast(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==float(strike)]
        if row.empty:
            return None
        bid=float(row['bid'].iloc[0] or 0)
        ask=float(row['ask'].iloc[0] or 0)
        if bid>0 and ask>0:
            return round((bid+ask)/2,2)
        return round(float(row['lastPrice'].iloc[0]),2)
    except:
        return None

st.set_page_config(layout="wide")
st.markdown("<style>.box{background:#1e1e1e;color:#fff;padding:18px;border-radius:12px;font-family:monospace;font-size:15px;line-height:1.8;border:1px solid #333;margin-bottom:12px;white-space:pre-wrap}</style>", unsafe_allow_html=True)

if st.button("🚀 فحص توافق 90%+ وارسال (0.2$-4$)", use_container_width=True, type="primary"):
    sent=0
    for t in WATCHLIST:
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="5d")
            if hist.empty:
                continue
            curr=round(float(hist['Close'].iloc[-1]),2)
            high=round(float(hist['High'].iloc[-1]),2)
            low=round(float(hist['Low'].iloc[-1]),2)
            direction=get_strong_direction(t)
            if not direction:
                continue
            exp=tk.options[0] if tk.options else None
            if not exp:
                continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if dte<0 and len(tk.options)>1:
                exp=tk.options[1]
                dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if not (0 <= dte <= 7):
                continue
            chain=tk.option_chain(exp)
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            bid=float(row['bid'] or 0)
            ask=float(row['ask'] or 0)
            entry=round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row.get('lastPrice',0) or 0),2)
            if entry < 0.20 or entry > 4.00:
                continue
            if bid>0 and ask>0 and (ask-bid)/entry > 0.40:
                continue
            strike=float(row['strike'])
            strike_s=int(strike) if strike==int(strike) else strike
            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now_fast(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            emoji="🟢" if direction=="CALL" else "🔴"
            txt=f"{emoji} {t} {strike_s} {direction} 🐳\nExp: {exp} ({dte}d) Stock: ${curr:.2f}\nEntry: ${entry:.2f} Bid: ${bid:.2f}\nStop: ${entry*0.5:.2f}\nTarget: ${entry*1.5:.2f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\nTarget Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p:.2f} | {pnl:+.1f}% شغال\n{datetime.now().strftime('%H:%M:%S')}"
            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)
            fpath=os.path.join(BASE, f"{date.today()}.json")
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d.get('key')==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
            if send(txt):
                sent+=1
            time.sleep(1)
        except:
            continue
    st.success(f"تم ارسال {sent} عقد")
