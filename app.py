import yfinance as yf, requests, json, os
from datetime import datetime
import pytz
BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
NY=pytz.timezone('America/New_York')
RIYADH=pytz.timezone('Asia/Riyadh')

def send(m):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id':CHAT_ID,'text':m},timeout=15)

WATCH=["NVDA","TSLA","AMD","PLTR","META","COIN","HOOD","AAPL","MSFT","SPY","QQQ"]

for t in WATCH:
    try:
        tk=yf.Ticker(t)
        curr=float(tk.fast_info['last_price'])
        daily=tk.history(period="20d")
        if daily.empty: continue
        daily['EMA20']=daily['Close'].ewm(20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        chg=(curr/float(daily['Open'].iloc[-1])-1)*100
        direction="CALL" if curr>ema20 and chg>-0.8 else "PUT" if curr<ema20 and chg<0.8 else None
        if not direction: continue
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:1]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1<=days<=10): continue
            opts=tk.option_chain(exp).calls if direction=="CALL" else tk.option_chain(exp).puts
            for _,r in opts.iterrows():
                last=float(r['lastPrice'] or 0)
                if 1.0<=last<=4.0 and float(r['bid'] or 0)>0.5:
                    msg=f"{'🟢' if direction=='CALL' else '🔴'} ${t} - {int(r['strike'])} {direction} 🔥\n💵 ${curr:.2f} | دخول ${last:.2f} | {exp}"
                    send(msg)
                    break
            break
    except: continue
