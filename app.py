import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"

st.set_page_config(layout="wide")
st.markdown("""
<style>
.telegram-box {background:#182533; border:3px solid #00e6a8; border-radius:18px; padding:22px; max-width:540px; margin:12px auto; color:white; font-size:18px; line-height:1.9; white-space:pre-wrap; direction:ltr; text-align:left;}
</style>
""", unsafe_allow_html=True)

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX","RUT":"^RUT"}

# 52 شركة الأصلية + SPX + NDX = 54
WATCHLIST_54 = [
    # 1-10 AI & Chips تذبذب عالي
    "NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META",
    # 11-18 Crypto & Fintech
    "MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST",
    # 19-27 Meme High IV
    "GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR",
    # 28-33 Big Tech
    "AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL",
    # 34-44 ETFs عالية التذبذب
    "SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL",
    # 45-52 Growth سريع
    "APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","SMCI","INTC","WOLF","TEM",
    # +2 اللي طلبتها
    "SPX","NDX"
]

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
    except: pass

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_price(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try:
        curr=float(tk.fast_info['last_price'])
        daily=tk.history(period="10d", interval="1d")
        intraday=tk.history(period="1d", interval="5m")
    except:
        daily=tk.history(period="10d", interval="1d")
        curr=float(daily['Close'].iloc[-1]) if not daily.empty else 0
        intraday=tk.history(period="1d", interval="5m")
    return curr, daily, intraday

def is_valid(ticker):
    try:
        curr,daily,intraday=get_price(ticker)
        if curr==0 or daily.empty: return False, "no data"
        open_today=float(daily['Open'].iloc[-1])
        day_chg=(curr/open_today-1)*100
        if day_chg > 4.2: return False, f"طار {day_chg:.1f}%"
        if day_chg < -3: return False, f"نازل {day_chg:.1f}%"
        atr=float((daily['High']-daily['Low']).tail(5).mean())
        atr_pct=atr/curr*100
        if atr_pct < 1.2: return False, f"تذبذب {atr_pct:.1f}% ضعيف"
        vol=float(daily['Volume'].iloc[-1]); avg=float(daily['Volume'].tail(5).mean())
        if vol < avg*1.1: return False, "فوليوم ضعيف"
        return True, f"صالح {day_chg:.1f}% ATR {atr_pct:.1f}%"
    except: return False, "error"

def get_contract_under_4(ticker, typ="CALL"):
    """يجيب عقد تحت $4 فقط - خفيف وسريع"""
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    real_ticker = TICKER_MAP.get(ticker,ticker)
    try:
        curr_real,_,_=get_price(ticker)
        tk=yf.Ticker(opt_ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=float(tk.history(period="1d")['Close'].iloc[-1])

        ny=pytz.timezone('America/New_York'); today=datetime.now(ny).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 7): continue
            chain=tk.option_chain(exp)
            opts=chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue

            # نبحث عن عقود رخيصة تحت $4 - OTM 2-4%
            target=curr_opt*1.025 if typ=="CALL" else curr_opt*0.975
            opts=opts[(opts['strike']>=curr_opt*0.98) & (opts['strike']<=curr_opt*1.06)]

            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0

                    # فلتر تحت $4
                    if last < 0.6 or last > 4.0: continue
                    if bid==0 or ask==0: continue
                    if bid < 0.4: continue
                    if (ask-bid)/last > 0.18: continue
                    if vol < 200 and oi < 800: continue

                    return {
                        "ticker":ticker,"opt_ticker":opt_ticker,
                        "curr":curr_real,"curr_opt":curr_opt,
                        "exp":exp,"days":days,"strike":int(r['strike']),"type":typ,
                        "last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi
                    }
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    tg=f"{int(base*1.005)} → {int(base*1.012)} → {int(base*1.022)} → {int(base*1.035)}"
    return f"""${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['exp']} ({c['days']} يوم) تحت $4 💰
💵 السعر الحالي: ${c['curr']:.2f}

💰 دخول العقد: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف العقد: ${c['last']*0.5:.2f}
📊 Vol {c['vol']} | OI {c['oi']}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.5:.2f} (+150%)

🐋 حيتان ابو راكان
🔥 GOLDEN UNDER $4"""

st.title(f"V92 - 54 شركة + عقد تحت $4")

sent=load(SENT_FILE)
active=load(FILE)

st.write(f"القائمة: {len(WATCHLIST_54)} شركة - {', '.join(WATCHLIST_54[:10])}...")

if st.button(f"🔍 افحص {len(WATCHLIST_54)} شركة - عقد تحت $4 فقط", type="primary"):
    for t in WATCHLIST_54:
        valid, reason = is_valid(t)
        if not valid:
            st.write(f"⏸️ {t}: {reason}")
            continue
        c=get_contract_under_4(t)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد تحت $4")
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now().strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل اليوم")
            continue
        msg=build_msg(c)
        st.markdown(f'<div class="telegram-box">{msg}</div>', unsafe_allow_html=True)
        st.success(f"✅ {t} - {reason} - ${c['last']:.2f}")
        send(msg)
        sent.append(key); save(SENT_FILE, sent)
        active.append({**c, "last_price":c['curr'], "t1_hit":False, "targets_stock":[c['curr']*1.01, c['curr']*1.022]})
        save(FILE, active)
        time.sleep(0.3)

st.write("---")
auto=st.checkbox(f"🚀 تحديث تلقائي كل 5 دقايق - {len(WATCHLIST_54)} شركة - بدون تكرار")
if auto:
    status=st.empty()
    while True:
        now=datetime.now().strftime("%H:%M:%S")
        status.write(f"⏰ {now} - يفحص 54 شركة - المرسلة اليوم {len(sent)} - فقط عقود تحت $4")
        # متابعة
        for c in active:
            try:
                curr,_,_=get_price(c['ticker'])
                if curr and curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                    send(f"🔥 تحديث العقد ${c['ticker']}\n✅ حقق الهدف الأول\nالآن ${curr:.2f}\nالعقد +50%")
                    c['t1_hit']=True
            except: pass
        save(FILE, active)
        # بحث جديد
        for t in WATCHLIST_54:
            v,_=is_valid(t)
            if v:
                c=get_contract_under_4(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now().strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
        time.sleep(300)
