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

# SPX و NDX لها رموز خاصة في yfinance
TICKER_MAP = {
    "SPX": "^SPX", # S&P 500
    "NDX": "^NDX", # Nasdaq 100
    "RUT": "^RUT"
}

WATCHLIST = [
    "SPX","NDX", # المؤشرات اللي طلبتها
    "SPY","QQQ","IWM","TQQQ","SQQQ",
    "NVDA","TSLA","AMD","SMCI","AVGO","ARM","PLTR","META","AAPL","MSFT","GOOGL","AMZN",
    "MSTR","COIN","HOOD","MARA","APP","RDDT","ASTS","RKLB","SOUN","IONQ"
]

def send(msg):
    try: requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
    except: pass

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def get_price(ticker):
    real_ticker = TICKER_MAP.get(ticker, ticker)
    tk=yf.Ticker(real_ticker)
    try:
        curr=float(tk.fast_info['last_price'])
        hist=tk.history(period="1d", interval="5m")
    except:
        hist=tk.history(period="2d", interval="1d")
        curr=float(hist['Close'].iloc[-1]) if not hist.empty else 0
        hist_5m=tk.history(period="1d", interval="5m")
        return curr, hist, hist_5m
    hist_daily=tk.history(period="10d", interval="1d")
    return curr, hist_daily, hist

def is_valid_entry(ticker):
    """هل العقد لسه صالح وما طارت موجته؟"""
    try:
        curr, daily, intraday = get_price(ticker)
        if curr==0 or daily.empty: return False, "ما فيه سعر"

        # 1. لا ترسل اذا السهم طار اكثر من 4% اليوم - موجته انتهت
        open_today = float(daily['Open'].iloc[-1])
        day_change = (curr/open_today -1)*100
        if day_change > 4.5:
            return False, f"طار {day_change:.1f}% - متأخر"

        # 2. لا ترسل اذا قريب من قمة 10 ايام - بيصحح
        high_10 = float(daily['High'].tail(10).max())
        if curr >= high_10*0.99:
            return False, f"قريب من القمة {high_10:.1f}"

        # 3. لازم يكون عنده مساحة 1.5% على الاقل للهدف
        low_5m = float(intraday['Low'].min()) if not intraday.empty else curr*0.98
        distance_from_low = (curr/low_5m -1)*100
        if distance_from_low > 3.5:
            return False, f"بعيد عن القاع {distance_from_low:.1f}%"

        # 4. فوليوم اليوم اعلى من المتوسط
        vol_today = float(daily['Volume'].iloc[-1])
        avg_vol = float(daily['Volume'].tail(5).mean())
        if vol_today < avg_vol*1.1:
            return False, f"فوليوم ضعيف"

        # 5. ATR تذبذب عالي
        atr = float((daily['High']-daily['Low']).tail(5).mean())
        atr_pct = atr/curr*100
        if atr_pct < 1.2: return False, f"تذبذب {atr_pct:.1f}% قليل"

        return True, f"صالح - تغيير اليوم {day_change:.1f}% - ATR {atr_pct:.1f}% - مساحة للصعود"

    except Exception as e:
        return False, str(e)

def get_contract(ticker, typ="CALL"):
    real_ticker = TICKER_MAP.get(ticker, ticker)
    # للاوبشن: SPX و NDX نستخدم SPY و QQQ كبديل لان اوبشن SPX في yfinance ضعيف
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        tk=yf.Ticker(opt_ticker)
        curr_real,_,_ = get_price(ticker) # سعر المؤشر الحقيقي
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=float(tk.history(period="1d")['Close'].iloc[-1])

        ny=pytz.timezone('America/New_York'); today=datetime.now(ny).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 7): continue
            chain=tk.option_chain(exp)
            opts=chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue

            # استهداف OTM خفيف 1% فقط - عشان يكون صالح بعد الافتتاح
            target=curr_opt*1.01 if typ=="CALL" else curr_opt*0.99
            opts=opts[abs(opts['strike']-target) < curr_opt*0.04]

            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0
                    if last < 0.9: continue
                    if bid==0 or ask==0: continue
                    if (ask-bid)/last > 0.15: continue
                    if vol < 200 and oi < 1000: continue
                    # سعر العقد ما يكون طاير 80% اليوم
                    if last > float(r['strike'])*0.08: continue

                    return {
                        "ticker":ticker, "opt_ticker":opt_ticker,
                        "curr":curr_real, "curr_opt":curr_opt,
                        "exp":exp, "days":days,
                        "strike":int(r['strike']), "type":typ,
                        "last":last, "bid":bid, "ask":ask, "vol":vol, "oi":oi
                    }
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    tg=f"{int(base*1.005)} → {int(base*1.01)} → {int(base*1.02)} → {int(base*1.035)} → {int(base*1.05)}"
    return f"""${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['exp']} ({c['days']} يوم) صالح للتنفيذ
💵 السعر الحالي: ${c['curr']:.2f}

💰 دخول العقد: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف العقد: ${c['last']*0.55:.2f}
📊 Vol {c['vol']} | OI {c['oi']}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.5:.2f} (+150%)

🐋 حيتان ابو راكان
🔥 GOLDEN VALID"""

st.title(f"V91 VALID ONLY - SPX & NDX + فلتر موجة منتهية")

sent=load(SENT_FILE)
active=load(FILE)

col1,col2=st.columns(2)
with col1:
    if st.button(f"🔍 فحص {len(WATCHLIST)} سهم - فقط الصالح بعد الافتتاح", type="primary"):
        for t in WATCHLIST:
            valid, reason = is_valid_entry(t)
            if not valid:
                st.write(f"⏸️ {t}: {reason}")
                continue
            c=get_contract(t)
            if not c:
                st.write(f"❌ {t} - {reason} - بس ما فيه عقد سيولة")
                continue
            key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now().strftime('%Y-%m-%d')}"
            if key in sent:
                st.write(f"⏭️ {t} مرسل اليوم")
                continue
            msg=build_msg(c)
            st.markdown(f'<div class="telegram-box">{msg}</div>', unsafe_allow_html=True)
            st.success(f"✅ {t} {reason}")
            send(msg)
            sent.append(key); save(SENT_FILE, sent)
            active.append({**c, "last_price":c['curr'], "t1_hit":False, "targets_stock":[c['curr']*1.01, c['curr']*1.02]})
            save(FILE, active)
            time.sleep(0.5)

with col2:
    if st.button("🗑️ مسح المرسلة"):
        save(SENT_FILE, []); st.success("تم")

st.write("---")
st.subheader("🔄 تحديث تلقائي كل 5 دقايق - بدون تكرار")

auto=st.checkbox("شغل التحديث التلقائي")
if auto:
    status=st.empty()
    while True:
        now=datetime.now().strftime("%H:%M:%S")
        status.write(f"⏰ آخر تحديث: {now} - يفحص {len(WATCHLIST)} سهم - المرسلة اليوم: {len(sent)}")

        # 1. تابع العقود المفتوحة وارسل تحديث اذا تحقق هدف
        for c in active:
            try:
                curr,_,_=get_price(c['ticker'])
                if curr and abs(curr - c.get('last_price',curr))>0.2:
                    if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                        send(f"🔥 تحديث العقد ${c['ticker']}\n✅ تحقق الهدف الأول\nالآن ${curr:.2f}\nالعقد +50%")
                        c['t1_hit']=True
                    c['last_price']=curr
            except: pass
        save(FILE, active)

        # 2. ابحث عن عقود جديدة فقط - ما يكرر
        for t in WATCHLIST:
            valid,_=is_valid_entry(t)
            if valid:
                c=get_contract(t)
                if c:
                    key=f"{t}_{c['exp']}_{c['strike']}_{datetime.now().strftime('%Y-%m-%d')}"
                    if key not in sent:
                        send(build_msg(c))
                        sent.append(key); save(SENT_FILE, sent)
                        status.write(f"🚀 جديد {t} انرسل {now}")

        time.sleep(300) # 5 دقايق بالضبط
