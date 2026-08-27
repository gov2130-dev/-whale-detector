import streamlit as st, yfinance as yf, requests
from datetime import datetime
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

st.set_page_config(layout="wide")
st.markdown("""
<style>
.telegram-box {
    background: #182533; border: 3px solid #00e6a8; border-radius: 18px;
    padding: 26px; max-width: 540px; margin: 20px auto; color: white;
    font-size: 19px; line-height: 1.9; white-space: pre-wrap; direction: ltr; text-align: left;
}
</style>
""", unsafe_allow_html=True)

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={'chat_id':CHAT_ID,'text':msg}, timeout=10)

def get_future_contract(ticker="NVDA", typ="CALL", otm=1.0):
    tk = yf.Ticker(ticker)
    try:
        curr = float(tk.fast_info['last_price'])
    except:
        curr = float(tk.history(period="1d")['Close'].iloc[-1])

    exps = tk.options
    if not exps:
        return None, f"ما فيه expiries لـ {ticker}"

    ny = pytz.timezone('America/New_York')
    today = datetime.now(ny).date()
    future = []
    for e in exps:
        d = datetime.strptime(e, "%Y-%m-%d").date()
        if d >= today:
            future.append(e)
    
    if not future:
        return None, "كل التواريخ منتهية"
    
    # جرب اول 3 تواريخ لين نلقى سيولة
    for exp in future[:3]:
        try:
            chain = tk.option_chain(exp)
            opts = chain.calls if typ=="CALL" else chain.puts
            if opts.empty: continue
            
            # اقرب سترايك للسعر الحالي + OTM
            target = curr * (1+otm/100) if typ=="CALL" else curr * (1-otm/100)
            opts['diff'] = abs(opts['strike'] - target)
            opts = opts.sort_values('diff').head(10)
            
            # خذ اول واحد فيه سعر
            for _, row in opts.iterrows():
                last = float(row['lastPrice']) if row['lastPrice'] else 0
                bid = float(row['bid']) if row['bid'] else 0
                if last > 0.2:  # عقد حي
                    days = (datetime.strptime(exp, "%Y-%m-%d").date() - today).days
                    return {
                        "ticker":ticker,"curr":curr,"exp":exp,"days":days,
                        "strike":int(row['strike']),"type":typ,
                        "last":last,"bid":bid,"ask":float(row['ask']) if row['ask'] else 0,
                        "vol":int(row['volume']) if str(row['volume'])!='nan' else 0,
                        "oi":int(row['openInterest']) if str(row['openInterest'])!='nan' else 0,
                    }, "OK"
        except Exception as e:
            continue
    
    return None, f"فشل جلب chain لـ {future[:2]}"

def build_msg(c):
    base=c['curr']
    tg=" → ".join([str(int(base*1.01)), str(int(base*1.02)), str(int(base*1.03)), str(int(base*1.04)), str(int(base*1.06)), str(int(base*1.08)), str(int(base*1.10))])
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

st.title("V88 - عقود مستقبلية حية FIXED")

col1,col2=st.columns(2)
with col1:
    ticker=st.selectbox("السهم", ["NVDA","SPY","QQQ","AAPL","TSLA","MSFT","AMD"], index=0)
with col2:
    typ=st.selectbox("النوع", ["CALL","PUT"], index=0)

otm=st.slider("OTM %", 0.0, 3.0, 1.0, step=0.5)

if st.button(f"🔍 جيب عقد {ticker} مستقبلي حي", type="primary"):
    with st.spinner(f"نجيب {ticker} {typ}..."):
        c, msg = get_future_contract(ticker, typ, otm)
        if c:
            st.success(f"✅ عقد مستقبلي - ينتهي {c['exp']} بعد {c['days']} يوم - قابل للتنفيذ")
            st.markdown(f'<div class="telegram-box">{build_msg(c)}</div>', unsafe_allow_html=True)
            st.write(f"Bid: {c['bid']} | Ask: {c['ask']} | Last: {c['last']} | Vol: {c['vol']}")
            
            if st.button("📩 ارسل لتلجرام الآن"):
                send(build_msg(c))
                st.success("انرسل - هذا عقد حقيقي تقدر تدخل عليه في البروكر")
        else:
            st.error(f"❌ {msg}")
            st.info("جرب SPY أو QQQ - سيولتهم اعلى - NVDA احيانا yfinance يعلق")

st.write("---")
st.caption("V88 يجيب اقرب expiry مستقبلي + فيه lastPrice حقيقي + Bid/Ask حي - مش سعر وهمي ثابت")
