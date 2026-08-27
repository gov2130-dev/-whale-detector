import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
FILE="active_contracts.json"
SENT_FILE="sent_today.json"

RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="V93 - 54 شركة تحت $4")
st.markdown("""
<style>
.telegram-box {background:#182533; border:3px solid #00e6a8; border-radius:18px; padding:22px; max-width:540px; margin:12px auto; color:white; font-size:18px; line-height:1.9; white-space:pre-wrap; direction:ltr; text-align:left;}
.stBox {background:#0f1f33; border-radius:12px; padding:10px; margin:5px 0;}
</style>
""", unsafe_allow_html=True)

TICKER_MAP = {"SPX":"^SPX","NDX":"^NDX","RUT":"^RUT"}

WATCHLIST_54 = [
    "NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META",
    "MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST",
    "GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR",
    "AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL",
    "SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL",
    "APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM",
    "SPX","NDX"
]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return True
    except: return False

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_price(ticker):
    real=TICKER_MAP.get(ticker,ticker)
    tk=yf.Ticker(real)
    try:
        curr=float(tk.fast_info['last_price'])
    except:
        hist=tk.history(period="1d")
        curr=float(hist['Close'].iloc[-1]) if not hist.empty else 0
    daily=tk.history(period="10d", interval="1d")
    intraday=tk.history(period="1d", interval="5m")
    return curr, daily, intraday

def is_valid(ticker):
    try:
        curr,daily,intraday=get_price(ticker)
        if curr==0 or daily.empty: return False, "no data", 0
        open_today=float(daily['Open'].iloc[-1])
        day_chg=(curr/open_today-1)*100
        atr=float((daily['High']-daily['Low']).tail(5).mean())
        atr_pct=atr/curr*100 if curr>0 else 0

        if ticker in ["SPX","NDX","SPY","QQQ","RUT"]:
            if atr_pct < 0.35: return False, f"تذبذب {atr_pct:.1f}% ضعيف", atr_pct
            if abs(day_chg) > 3.2: return False, f"طار {day_chg:.1f}% - انتهت", atr_pct
        else:
            if day_chg > 4.2: return False, f"طار {day_chg:.1f}%", atr_pct
            if day_chg < -3.5: return False, f"نازل {day_chg:.1f}%", atr_pct
            if atr_pct < 1.1: return False, f"تذبذب {atr_pct:.1f}% ضعيف", atr_pct

        vol=float(daily['Volume'].iloc[-1]); avg=float(daily['Volume'].tail(5).mean())
        if vol < avg*1.0: return False, "فوليوم ضعيف", atr_pct
        return True, f"صالح {day_chg:.1f}% ATR {atr_pct:.1f}%", atr_pct
    except Exception as e:
        return False, str(e), 0

def get_contract_under_4(ticker, typ="CALL"):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,_=get_price(ticker)
        tk=yf.Ticker(opt_ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=float(tk.history(period="1d")['Close'].iloc[-1])

        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 7): continue
            chain=tk.option_chain(exp)
            opts=chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue
            opts=opts[(opts['strike']>=curr_opt*0.97) & (opts['strike']<=curr_opt*1.07)]
            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0
                    if last < 0.6 or last > 4.0: continue
                    if bid < 0.35 or ask==0: continue
                    if (ask-bid)/last > 0.20: continue
                    if vol < 150 and oi < 700: continue
                    return {"ticker":ticker,"opt_ticker":opt_ticker,"curr":curr_real,"curr_opt":curr_opt,"exp":exp,"days":days,"strike":int(r['strike']),"type":typ,"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi}
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

# UI
st.title(f"V93 - 54 شركة - عقد تحت $4 - وقت الرياض")
ksa_now = datetime.now(RIYADH).strftime("%H:%M:%S")
ny_now = datetime.now(NY).strftime("%H:%M:%S")
st.caption(f"⏰ الآن: الرياض {ksa_now} | نيويورك {ny_now} | القائمة {len(WATCHLIST_54)} شركة")

sent=load(SENT_FILE)
active=load(FILE)

c1,c2,c3=st.columns(3)
with c1:
    if st.button(f"🔍 افحص {len(WATCHLIST_54)} الآن", type="primary"):
        for t in WATCHLIST_54:
            valid, reason, atr = is_valid(t)
            if not valid:
                st.write(f"⏸️ {t}: {reason}")
                continue
            c=get_contract_under_4(t)
            if not c:
                st.write(f"❌ {t}: {reason} - لا يوجد عقد تحت $4")
                continue
            key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
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
with c2:
    if st.button("🗑️ تصفير المرسلة"):
        save(SENT_FILE, []); st.success("تصفر - بكرا يرسل من جديد")
with c3:
    if st.button("📋 عرض النشطة"):
        st.json(active)

st.divider()
st.subheader("🔄 تحديث تلقائي كل 5 دقايق - بدون تكرار - وقت الرياض")
auto=st.checkbox(f"🚀 شغل - يفحص {len(WATCHLIST_54)} شركة كل 5 دقايق")

if auto:
    status=st.empty()
    log_box=st.empty()
    while True:
        ksa = datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
        ny = datetime.now(NY).strftime("%H:%M:%S")
        status.markdown(f"**⏰ الرياض:** {ksa} | **نيويورك:** {ny} | **مرسلة اليوم:** {len(sent)} | **يبحث في 54 شركة**")

        # 1. متابعة العقود
        for c in active:
            try:
                curr,_,_=get_price(c['ticker'])
                if curr and curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                    send(f"🔥 تحديث العقد ${c['ticker']}\n✅ تحقق الهدف الأول\nالآن ${curr:.2f}\nالعقد +50%")
                    c['t1_hit']=True
                    log_box.write(f"✅ {c['ticker']} حقق هدف")
            except: pass
        save(FILE, active)

        # 2. بحث جديد
        for t in WATCHLIST_54:
            valid,_,_=is_valid(t)
            if valid:
                c=get_contract_under_4(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
                        active.append({**c, "last_price":c['curr'], "t1_hit":False, "targets_stock":[c['curr']*1.01]})
                        save(FILE, active)
                        log_box.write(f"🚀 جديد {t} ${c['last']:.2f} انرسل {ksa}")

        time.sleep(300)
