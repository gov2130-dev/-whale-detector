import yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
    except: pass

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_data(ticker):
    tk=yf.Ticker("^SPX" if ticker=="SPX" else "^NDX" if ticker=="NDX" else ticker)
    try: curr=float(tk.fast_info['last_price'])
    except: curr=float(tk.history(period="1d")['Close'].iloc[-1])
    daily=tk.history(period="20d", interval="1d")
    return curr, daily, tk

def is_strong_both(ticker):
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty or len(daily)<10: return False, ""
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        chg=(curr/float(daily['Open'].iloc[-1])-1)*100
        if curr > ema20*0.998 and chg > -0.8: return True, "CALL"
        if curr < ema20*1.002 and chg < 0.8: return True, "PUT"
        return False, ""
    except: return False, ""

def get_contract(ticker, direction):
    try:
        curr_real,_,tk = get_data(ticker)
        curr_opt=curr_real
        today=datetime.now(NY).date()
        for exp in [e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            opts = tk.option_chain(exp).calls if direction=="CALL" else tk.option_chain(exp).puts
            if direction=="CALL": opts=opts[(opts['strike']>=curr_opt*1.002) & (opts['strike']<=curr_opt*1.04)]
            else: opts=opts[(opts['strike']>=curr_opt*0.96) & (opts['strike']<=curr_opt*0.998)]
            for _, r in opts.iterrows():
                last=float(r['lastPrice'] or 0)
                if 1.0 <= last <= 4.0 and float(r['bid'] or 0) > 0.6:
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":float(r['bid'] or 0),"ask":float(r['ask'] or 0),"type":direction}
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    emoji="🟢" if c['type']=="CALL" else "🔴"
    tg=f"{base*1.02:.1f} → {base*1.04:.1f}" if c['type']=="CALL" else f"{base*0.98:.1f} → {base*0.96:.1f}"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم) 💵 ${c['curr']:.2f}
💰 دخول ${c['last']:.2f} 🛑 وقف ${c['last']*0.55:.2f}
🎯 {tg} | T1 ${c['last']*1.5:.2f}"""

print("🚀 V100 CLOUD بدأ - يشتغل حتى لو سكرت الصفحة")
while True:
    try:
        sent=load(SENT_FILE)
        today_str=datetime.now(RIYADH).strftime('%Y-%m-%d')
        # تصفير تلقائي كل يوم جديد
        if len(sent)>0 and today_str not in str(sent): 
            save(SENT_FILE, []); sent=[]
        
        for t in WATCHLIST_54:
            ok, direction = is_strong_both(t)
            if ok:
                c=get_contract(t, direction)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{today_str}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
                        print(f"✅ أرسل {t} {direction} {datetime.now(RIYADH).strftime('%H:%M:%S')}")
                        time.sleep(1)
        
        print(f"⏰ فحص تم {datetime.now(RIYADH).strftime('%H:%M:%S')} - نوم 5 دقايق")
        time.sleep(300) # 5 دقايق
    except Exception as e:
        print(f"خطأ {e}"); time.sleep(60)
