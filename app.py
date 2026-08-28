import yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
SENT_FILE="sent.json"
WATCHLIST=["NVDA","TSLA","AMD","AVGO","SMCI","PLTR","META","MSTR","COIN","HOOD","GME","AAPL","MSFT","GOOGL","AMZN","NFLX","SPY","QQQ","SMH","TQQQ","SQQQ"]
NY=pytz.timezone('America/New_York')
RIYADH=pytz.timezone('Asia/Riyadh')

def send(m):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id':CHAT_ID,'text':m},timeout=15)
    except: pass

def load(): return json.load(open(SENT_FILE)) if os.path.exists(SENT_FILE) else []
def save(d): json.dump(d, open(SENT_FILE,'w'))

print(f"فحص {datetime.now(RIYADH)}")
sent=load()
for t in WATCHLIST[:15]: # يفحص 15 كل 5 دقايق عشان ما يعلق
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
        for exp in [e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:1]:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1<=days<=10): continue
            opts=tk.option_chain(exp).calls if direction=="CALL" else tk.option_chain(exp).puts
            for _,r in opts.iterrows():
                last=float(r['lastPrice'] or 0)
                if 1.0<=last<=4.0 and float(r['bid'] or 0)>0.6:
                    key=f"{t}_{exp}_{int(r['strike'])}_{direction}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        msg=f"{'🟢' if direction=='CALL' else '🔴'} ${t} - {int(r['strike'])} {direction} 🔥\n📅 {exp} ({days} يوم) 💵 ${curr:.2f}\n💰 دخول ${last:.2f}"
                        send(msg); sent.append(key); save(sent)
                        print(f"ارسل {t}"); break
            break
    except Exception as e:
        print(e); continue
