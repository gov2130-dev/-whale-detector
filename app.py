import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]
SENT_FILE="sent_today.json"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V99.2 STRONG")
TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX"}
WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM","SPX","NDX"]

def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def is_strong_confirmed(ticker):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real)
        daily=tk.history(period="50d", interval="1d")
        if daily.empty or len(daily)<30: return False, "", 0
        
        curr=float(daily['Close'].iloc[-1])
        # مؤشرات قوية
        daily['EMA20']=daily['Close'].ewm(span=20).mean()
        daily['EMA50']=daily['Close'].ewm(span=50).mean()
        daily['VOL_AVG']=daily['Volume'].rolling(20).mean()
        
        ema20=float(daily['EMA20'].iloc[-1])
        ema50=float(daily['EMA50'].iloc[-1])
        vol=float(daily['Volume'].iloc[-1])
        vol_avg=float(daily['VOL_AVG'].iloc[-1])
        high=float(daily['High'].iloc[-1])
        low=float(daily['Low'].iloc[-1])
        open_p=float(daily['Open'].iloc[-1])
        
        chg = (curr/open_p-1)*100
        vol_ratio = vol/vol_avg if vol_avg>0 else 0
        
        # شروط CALL القوي المؤكد
        if curr > ema20 and ema20 > ema50 and curr >= high*0.985 and vol_ratio > 1.3 and chg > 0.5:
            score = vol_ratio + chg
            return True, "CALL", score
        # شروط PUT القوي المؤكد  
        elif curr < ema20 and ema20 < ema50 and curr <= low*1.015 and vol_ratio > 1.3 and chg < -0.5:
            score = vol_ratio + abs(chg)
            return True, "PUT", score
        return False, "", 0
    except:
        return False, "", 0

def get_strong_contract(ticker, direction):
    try:
        real=TICKER_MAP.get(ticker,ticker)
        tk=yf.Ticker(real)
        daily=tk.history(period="1d")
        curr=float(daily['Close'].iloc[-1]) if not daily.empty else 0
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if (datetime.strptime(e,"%Y-%m-%d").date()-today).days in range(3,8)][:2]
        
        best=None
        best_score=0
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr*1.005) & (opts['strike']<=curr*1.03)]
            else:
                opts=opts[(opts['strike']>=curr*0.97) & (opts['strike']<=curr*0.995)]
            
            for _, r in opts.iterrows():
                last=float(r['lastPrice'] or 0)
                bid=float(r['bid'] or 0)
                ask=float(r['ask'] or 0)
                vol=int(r['volume'] or 0)
                oi=int(r['openInterest'] or 0)
                spread = ask-bid if ask>0 and bid>0 else 99
                
                # فلتر العقود القوية فقط
                if not (1.2 <= last <= 3.8): continue
                if bid < 0.90: continue
                if spread > 0.15: continue
                if vol < 800 and oi < 3000: continue
                if oi < 1500: continue
                
                score = vol*0.3 + oi*0.2 + (1/spread)*100
                if score > best_score:
                    best_score=score
                    best={"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi,"type":direction,"score":score}
        return best
    except: return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.015:.1f} → {base*1.03:.1f} → {base*1.05:.1f}"; emoji="🟢🔥"
    else:
        tg=f"{base*0.985:.1f} → {base*0.97:.1f} → {base*0.95:.1f}"; emoji="🔴🔥"
    return f"""{emoji} عقد قوي مؤكد ${c['ticker']} - {c['strike']} {c['type']}
📅 {c['exp']} ({c['days']} يوم) | قوة {c['score']:.0f}
💵 السهم: ${c['curr']:.2f}
💰 دخول: ${c['last']:.2f} | Bid ${c['bid']:.2f} Ask ${c['ask']:.2f}
📊 سيولة: Vol {c['vol']} | OI {c['oi']}
🛑 وقف: ${c['last']*0.60:.2f}
🎯 أهداف السهم: {tg}
🎯 هدف العقد: +70% = ${c['last']*1.7:.2f} | +150% = ${c['last']*2.5:.2f}"""

st.title("V99.2 - العقود القوية المؤكدة فقط 💎")
ksa_now=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | فلتر قوي: Vol>800 OI>3000 Spread<0.15")

if st.button("🔍 افحص العقود القوية الآن 54", type="primary"):
    sent=load(SENT_FILE)
    found=0
    prog=st.progress(0)
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, score = is_strong_confirmed(t)
        if ok and score > 2:
            c=get_strong_contract(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    st.code(build_msg(c))
                    if send(build_msg(c)):
                        sent.append(key); save(SENT_FILE, sent); found+=1
        prog.progress((i+1)/len(WATCHLIST_54))
    if found==0:
        st.warning("⏸️ السوق ما فيه عقود قوية مؤكدة حالياً (هذا ممتاز - الفلتر يحميك من الخسارة)")
    else:
        st.success(f"✅ تم إرسال {found} عقد قوي مؤكد")

auto=st.checkbox("🚀 تشغيل تلقائي كل 5 دقايق (عقود قوية فقط)", value=False)
if auto:
    time.sleep(300)
    st.rerun()
