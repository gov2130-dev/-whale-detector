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
.telegram-box {background:#182533; border:3px solid #00e6a8; border-radius:18px; padding:22px; max-width:520px; margin:15px auto; color:white; font-size:18px; line-height:1.9; white-space:pre-wrap; direction:ltr; text-align:left;}
.box-update {background:#1a2e1a; border:3px solid #ffcc00; border-radius:18px; padding:18px; max-width:520px; margin:10px auto; color:white; font-size:17px; white-space:pre-wrap;}
</style>
""", unsafe_allow_html=True)

WATCHLIST = ["NVDA","SPY","QQQ","AAPL","TSLA","MSFT","AMD","META","AVGO","SMCI"]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={'chat_id':CHAT_ID,'text':msg}, timeout=10)
        return True
    except: return False

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def is_strong_stock(ticker):
    """شروط السهم القوي"""
    try:
        tk=yf.Ticker(ticker)
        hist=tk.history(period="5d", interval="1d")
        hist_1m=tk.history(period="1d", interval="5m")
        if hist.empty or len(hist)<3: return False, "بيانات ناقصة"

        curr=float(hist['Close'].iloc[-1])
        prev=float(hist['Close'].iloc[-2])
        vol=float(hist['Volume'].iloc[-1])
        avg_vol=float(hist['Volume'].iloc[-4:-1].mean())

        # شروط قوية
        change = (curr-prev)/prev*100
        vol_ratio = vol/avg_vol if avg_vol>0 else 0

        # 1. سيولة عالية
        if vol < 500000: return False, f"سيولة ضعيفة {vol}"
        # 2. زخم
        if not (0.5 <= change <= 6): return False, f"حركة {change:.1f}% ضعيفة"
        # 3. حجم اعلى من المتوسط
        if vol_ratio < 1.2: return False, f"فوليوم {vol_ratio:.1f}x عادي"
        # 4. فوق اقل سعر اليوم
        low_today=float(hist_1m['Low'].min()) if not hist_1m.empty else curr*0.98
        if curr < low_today*1.01: return False, "قريب من القاع"

        score=0
        if vol_ratio>1.5: score+=1
        if 1 <= change <= 4: score+=1
        if curr > float(hist['Close'].rolling(20).mean().iloc[-1]): score+=1

        return score>=2, f"قوي {change:.1f}% Vol {vol_ratio:.1f}x Score {score}/3"
    except Exception as e:
        return False, str(e)

def get_executable_contract(ticker, typ="CALL"):
    """يجيب عقد مستقبلي قابل للتنفيذ فعلا"""
    try:
        tk=yf.Ticker(ticker)
        try: curr=float(tk.fast_info['last_price'])
        except: curr=float(tk.history(period="1d")['Close'].iloc[-1])

        ny=pytz.timezone('America/New_York')
        today=datetime.now(ny).date()

        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]
        if not exps: return None

        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue # عقود اسبوعية فقط 1-10 ايام

            chain=tk.option_chain(exp)
            opts=chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue

            target=curr*1.015 if typ=="CALL" else curr*0.985
            opts=opts[abs(opts['strike']-target) < curr*0.03] # قريب

            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0

                    if last < 1.0: continue
                    if bid==0 or ask==0: continue
                    if (ask-bid)/last > 0.20: continue # سبريد واسع = غير قابل للتنفيذ
                    if vol < 100 and oi < 500: continue # بدون سيولة

                    return {
                        "ticker":ticker,"curr":curr,"exp":exp,"days":days,
                        "strike":int(r['strike']),"type":typ,
                        "last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi
                    }
                except: continue
    except: pass
    return None

def build_entry(c):
    base=c['curr']
    tg=f"{int(base*1.01)} → {int(base*1.02)} → {int(base*1.03)} → {int(base*1.05)} → {int(base*1.08)}"
    return f"""${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['exp']} ({c['days']} يوم)
💵 السعر الحالي: ${c['curr']:.2f}

💰 دخول العقد: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف العقد: ${c['last']*0.6:.2f}
📊 Vol {c['vol']} | OI {c['oi']}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.2:.2f} (+120%)

🐋 حيتان ابو راكان
🔥 GOLDEN 6/7"""

# --- الواجهة ---
st.title("V89 AUTO SCANNER - يبحث ويرسل لحاله 🚀")
st.write(f"قائمة المتابعة: {', '.join(WATCHLIST)}")

sent_today=load(SENT_FILE)
st.write(f"مرسلة اليوم: {len(sent_today)}")

if st.button("🔍 افحص الآن - بحث قوي + قابل للتنفيذ", type="primary"):
    logs=st.empty()
    for ticker in WATCHLIST:
        logs.write(f"يفحص {ticker}...")
        strong, reason = is_strong_stock(ticker)
        if not strong:
            logs.write(f"⏸️ {ticker} - {reason}")
            continue

        logs.write(f"🔥 {ticker} قوي - {reason} - يجيب عقد...")
        contract = get_executable_contract(ticker, "CALL")
        if not contract:
            logs.write(f"❌ {ticker} ما فيه عقد سيولة")
            continue

        # لا ترسل نفس العقد مرتين بنفس اليوم
        key=f"{ticker}_{contract['exp']}_{contract['strike']}"
        if key in sent_today:
            logs.write(f"⏭️ {ticker} مرسل اليوم من قبل")
            continue

        # ارسل!
        msg=build_entry(contract)
        st.markdown(f'<div class="telegram-box">{msg}</div>', unsafe_allow_html=True)
        if send(msg):
            st.success(f"✅ {ticker} انرسل تلجرام - عقد حقيقي قابل للتنفيذ")
            sent_today.append(key)
            save(SENT_FILE, sent_today)

            active=load(FILE)
            active.append({**contract, "last_price":contract['curr'], "t1_hit":False, "targets_stock":[contract['curr']*1.01, contract['curr']*1.02, contract['curr']*1.03]})
            save(FILE, active)
        time.sleep(1)

st.write("---")
st.subheader("المتابعة التلقائية كل 5 دقايق")

auto=st.checkbox("🚀 شغل البحث التلقائي - يرسل لحاله اذا لقى عقد قوي")

if auto:
    st.warning("شغال... اترك الصفحة مفتوحة او ارفعه على السحابة - بيبحث كل 5 دقايق")
    placeholder=st.empty()
    while True:
        active=load(FILE)
        # 1. تابع العقود المرسلة
        for c in active:
            try:
                curr=float(yf.Ticker(c['ticker']).fast_info['last_price'])
                if abs(curr - c.get('last_price',curr))>0.1:
                    if curr >= c['targets_stock'][0] and not c.get('t1_hit'):
                        send(f"🔥 تحديث {c['ticker']}\n✅ حقق الهدف الأول\nالسعر الآن ${curr:.2f}\nالعقد +50% 💰")
                        c['t1_hit']=True
                    c['last_price']=curr
            except: pass
        save(FILE, active)

        # 2. ابحث عن عقود جديدة كل 5 دقايق
        with placeholder.container():
            st.write(f"آخر فحص: {datetime.now().strftime('%H:%M:%S')} - يبحث في {len(WATCHLIST)} سهم...")
            for ticker in WATCHLIST:
                strong,_=is_strong_stock(ticker)
                if strong:
                    contract=get_executable_contract(ticker)
                    if contract:
                        key=f"{ticker}_{contract['exp']}_{contract['strike']}"
                        if key not in sent_today:
                            send(build_entry(contract))
                            sent_today.append(key)
                            save(SENT_FILE, sent_today)
                            st.write(f"🚀 ارسل {ticker} جديد")

        time.sleep(300)
