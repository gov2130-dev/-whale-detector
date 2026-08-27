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
.telegram-box {background:#182533; border:3px solid #00e6a8; border-radius:18px; padding:22px; max-width:540px; margin:15px auto; color:white; font-size:18px; line-height:1.9; white-space:pre-wrap; direction:ltr; text-align:left;}
</style>
""", unsafe_allow_html=True)

# 🔥 50 سهم اوبشن تذبذب عالي - مقسمة
WATCHLIST_HIGH_VOL = [
    # Magnificent 7 + AI تذبذب عالي
    "NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META",
    # Crypto & High Beta
    "MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST",
    # Meme & High IV
    "GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR",
    # Big Tech سيولة عالية
    "AAPL","MSFT","GOOGL","AMZN","NFLX","MSFT","ORCL",
    # ETFs تذبذب عالي للاوبشن
    "SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL",
    # Growth سريع
    "APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD"
]

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=10)

def load(f): return json.load(open(f)) if os.path.exists(f) else []
def save(f,d): json.dump(d, open(f,'w'))

def is_high_volatility(ticker):
    try:
        tk=yf.Ticker(ticker)
        hist=tk.history(period="10d", interval="1d")
        hist_5m=tk.history(period="1d", interval="5m")
        if hist.empty or len(hist)<5: return False, 0, "بيانات ناقصة"

        curr=float(hist['Close'].iloc[-1])
        # تذبذب 10 ايام
        vol_10d = (hist['High']/hist['Low'] -1).mean()*100
        # حركة اليوم
        change_today = (hist['Close'].iloc[-1]/hist['Close'].iloc[-2]-1)*100
        # ATR
        atr = float((hist['High']-hist['Low']).rolling(5).mean().iloc[-1])
        atr_pct = atr/curr*100

        # فلتر تذبذب عالي فقط
        if atr_pct < 1.5: return False, atr_pct, f"تذبذب {atr_pct:.1f}% ضعيف"
        if vol_10d < 2.0: return False, atr_pct, f"متوسط تذبذب {vol_10d:.1f}% قليل"

        score = 0
        if atr_pct > 3: score+=2
        if abs(change_today) > 1.5: score+=1
        if float(hist['Volume'].iloc[-1]) > float(hist['Volume'].mean())*1.3: score+=1

        return score>=2, atr_pct, f"ATR {atr_pct:.1f}% | حركة اليوم {change_today:.1f}% | Score {score}"
    except:
        return False, 0, "error"

def get_executable(ticker, typ="CALL"):
    try:
        tk=yf.Ticker(ticker)
        try: curr=float(tk.fast_info['last_price'])
        except: curr=float(tk.history(period="1d")['Close'].iloc[-1])
        ny=pytz.timezone('America/New_York'); today=datetime.now(ny).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 7): continue # اسبوعي فقط
            chain=tk.option_chain(exp)
            opts=chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue
            target=curr*1.02 if typ=="CALL" else curr*0.98
            opts=opts[abs(opts['strike']-target) < curr*0.05]
            for _, r in opts.sort_values('strike').iterrows():
                try:
                    last=float(r['lastPrice']) if r['lastPrice'] else 0
                    bid=float(r['bid']) if r['bid'] else 0
                    ask=float(r['ask']) if r['ask'] else 0
                    vol=int(r['volume']) if str(r['volume'])!='nan' else 0
                    oi=int(r['openInterest']) if str(r['openInterest'])!='nan' else 0
                    if last < 0.8: continue
                    if bid==0 or ask==0: continue
                    if (ask-bid)/last > 0.18: continue
                    if vol < 150 and oi < 800: continue
                    return {"ticker":ticker,"curr":curr,"exp":exp,"days":days,"strike":int(r['strike']),"type":typ,"last":last,"bid":bid,"ask":ask,"vol":vol,"oi":oi}
                except: continue
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    tg=f"{int(base*1.01)} → {int(base*1.025)} → {int(base*1.04)} → {int(base*1.06)} → {int(base*1.09)}"
    return f"""${c['ticker']} - {c['strike']} {c['type']} 🎯
📅 {c['exp']} ({c['days']} يوم) VOLATILE 🔥
💵 السعر الحالي: ${c['curr']:.2f}

💰 دخول العقد: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف العقد: ${c['last']*0.55:.2f}
📊 Vol {c['vol']} | OI {c['oi']} | تذبذب عالي

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.5:.2f} (+150%)

🐋 حيتان ابو راكان
🔥 GOLDEN HIGH VOL"""

st.title(f"V90 HIGH VOL SCANNER - {len(WATCHLIST_HIGH_VOL)} سهم تذبذب عالي")

sent_today=load(SENT_FILE)

col1,col2=st.columns(2)
with col1:
    if st.button(f"🔍 افحص {len(WATCHLIST_HIGH_VOL)} سهم الآن", type="primary"):
        logs=st.empty()
        for ticker in WATCHLIST_HIGH_VOL:
            logs.write(f"يفحص {ticker}...")
            is_vol, atr, reason = is_high_volatility(ticker)
            if not is_vol:
                continue
            c=get_executable(ticker)
            if not c: continue
            key=f"{ticker}_{c['exp']}_{c['strike']}"
            if key in sent_today: continue
            msg=build_msg(c)
            st.markdown(f'<div class="telegram-box">{msg}</div>', unsafe_allow_html=True)
            st.write(f"✅ {ticker} ATR {atr:.1f}% - {reason}")
            send(msg)
            sent_today.append(key)
            save(SENT_FILE, sent_today)
            active=load(FILE)
            active.append({**c, "last_price":c['curr'], "t1_hit":False, "targets_stock":[c['curr']*1.01, c['curr']*1.025, c['curr']*1.04]})
            save(FILE, active)
            time.sleep(0.5)

with col2:
    if st.button("🗑️ تصفير مرسلة اليوم"):
        save(SENT_FILE, [])
        st.success("تصفر")

st.write("---")
st.info(f"""
**القائمة الجديدة {len(WATCHLIST_HIGH_VOL)} سهم:**

🤖 AI تذبذب عالي: NVDA TSLA AMD SMCI PLTR ARM
₿ Crypto Beta: MSTR COIN MARA HOOD
🚀 Meme High IV: GME AMC ASTS RKLB SOUN IONQ
📈 ETFs متذبذبة: TQQQ SQQQ TSLL NVDL SMH

**الفلتر:**
- ATR >1.5% (تذبذب يومي عالي)
- متوسط تذبذب 10 ايام >2%
- عقود اسبوعية 1-7 ايام فقط
- Vol >150 و OI >800 وسبريد <18%
""")

auto=st.checkbox(f"🚀 بحث تلقائي كل 5 دقايق في {len(WATCHLIST_HIGH_VOL)} سهم")
if auto:
    while True:
        time.sleep(300)
        for ticker in WATCHLIST_HIGH_VOL:
            is_vol,_,_=is_high_volatility(ticker)
            if is_vol:
                c=get_executable(ticker)
                if c:
                    key=f"{ticker}_{c['exp']}_{c['strike']}"
                    if key not in sent_today:
                        send(build_msg(c))
                        sent_today.append(key)
                        save(SENT_FILE, sent_today)
