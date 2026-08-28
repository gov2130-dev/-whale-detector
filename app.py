import yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz
BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
SENT_FILE="/home/yourusername/sent.json"
WATCHLIST=["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","AAPL","MSFT","GOOGL","AMZN","NFLX","SPY","QQQ"]
RIYADH=pytz.timezone('Asia/Riyadh')
NY=pytz.timezone('America/New_York')

def send(m):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",data={'chat_id':CHAT_ID,'text':m},timeout=15)
    except: pass
def load(): return json.load(open(SENT_FILE)) if os.path.exists(SENT_FILE) else []
def save(d): json.dump(d, open(SENT_FILE,'w'))

def get_contract(ticker, direction):
    try:
        tk=yf.Ticker(ticker)
        curr=float(tk.fast_info['last_price'])
        daily=tk.history(period="20d")
        if daily.empty: return None
        today=datetime.now(NY).date()
        for exp in [e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1<=days<=10): continue
            opts=tk.option_chain(exp).calls if direction=="CALL" else tk.option_chain(exp).puts
            for _,r in opts.iterrows():
                last=float(r['lastPrice'] or 0)
                if 1.0<=last<=4.0 and float(r['bid'] or 0)>0.6:
                    return {"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"type":direction}
    except: pass
    return None

while True:
    try:
        sent=load()
        today_str=datetime.now(RIYADH).strftime('%Y-%m-%d')
        for t in WATCHLIST:
            try:
                tk=yf.Ticker(t)
                curr=float(tk.fast_info['last_price'])
                daily=tk.history(period="20d"); daily['EMA20']=daily['Close'].ewm(20).mean()
                ema20=float(daily['EMA20'].iloc[-1]); chg=(curr/float(daily['Open'].iloc[-1])-1)*100
                direction="CALL" if curr>ema20 and chg>-0.8 else "PUT" if curr<ema20 and chg<0.8 else None
                if direction:
                    c=get_contract(t,direction)
                    if c:
                        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{today_str}"
                        if key not in sent:
                            msg=f"{'🟢' if c['type']=='CALL' else '🔴'} ${c['ticker']} - {c['strike']} {c['type']} 🔥\n📅 {c['exp']} ({c['days']} يوم) 💵 ${c['curr']:.2f}\n💰 دخول ${c['last']:.2f} 🛑 وقف ${c['last']*0.55:.2f}"
                            send(msg); sent.append(key); save(sent); time.sleep(1)
            except: continue
        time.sleep(300)
    except: time.sleep(60)
