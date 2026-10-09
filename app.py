import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="صياد التذبذب V70", layout="wide")
st.title("🔥 كاشف الحيتان V70 - الأكثر تذبذباً")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=15)
    except: pass

def is_hammer(candle):
    body = abs(candle['Close'] - candle['Open'])
    upper = candle['High'] - max(candle['Close'], candle['Open'])
    lower = min(candle['Close'], candle['Open']) - candle['Low']
    range_c = candle['High'] - candle['Low']
    if range_c == 0: return False
    return body < (range_c * 0.4) and lower >= (body * 1.8) and lower >= (range_c * 0.45)

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","META","AAPL","MSFT","AMZN","NFLX","MSTR","COIN","MARA","RIOT","PLTR","SOFI","GME","AMC","NIO","UPST","AI","ARM","AVGO","TSM","MRVL","MU","INTC","GOOGL","MS","HOOD","DKNG","RBLX"]

def scan(sym, min_vol_pct, min_opt_vol, min_premium):
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period="10d", interval="1d")
        if len(df) < 4: return None
        last = df.iloc[-1]
        prev = df.iloc[-2]
        volatility_pct = (last['High'] - last['Low']) / prev['Close'] * 100
        if volatility_pct < min_vol_pct: return None

        # شرط المطرقة (اختياري - يعطي قوة)
        c_prev = df.iloc[-3]
        c_hammer = df.iloc[-2]
        c_confirm = df.iloc[-1]
        hammer_ok = is_hammer(c_hammer) and c_hammer['Volume'] > c_prev['Volume'] and c_confirm['Close'] > c_hammer['High']

        # شرط الاوبشن - نخفف الفلتر
        exps = tk.options
        if not exps: return None
        best = None
        for exp in exps[:3]:
            try:
                chain = tk.option_chain(exp)
                calls = chain.calls
                calls = calls[calls['volume'] > min_opt_vol]
                calls['premium'] = calls['volume'] * calls['lastPrice'] * 100
                calls = calls[calls['premium'] > min_premium]
                if len(calls)==0: continue
                top = calls.sort_values('premium', ascending=False).iloc[0]
                if best is None or top['premium'] > best['premium']:
                    best = top
                    best_exp = exp
            except: continue
        if best is None: return None

        return {
            "symbol": sym, "vol": volatility_pct, "price": last['Close'],
            "hammer": hammer_ok, "opt": best, "exp": best_exp,
            "opt_vol": best['volume'], "premium": best['premium']
        }
    except: return None

# واجهة تحكم
col1, col2, col3 = st.columns(3)
with col1: min_vol = st.slider("أقل تذبذب %", 0.5, 5.0, 1.5)
with col2: min_opt_v = st.slider("أقل فوليوم أوبشن", 100, 2000, 300)
with col3: min_prem = st.slider("أقل سيولة $", 10000, 300000, 50000, step=10000)

if st.button("🚀 افحص الأكثر تذبذباً الآن"):
    results = []
    prog = st.progress(0)
    for i, sym in enumerate(UNIVERSE):
        prog.progress((i+1)/len(UNIVERSE))
        r = scan(sym, min_vol, min_opt_v, min_prem)
        if r: results.append(r)
    prog.empty()

    if not results:
        st.warning(f"ما فيه أسهم فوق تذبذب {min_vol}% + اوبشن {min_opt_v}. خفف الفلتر من فوق")
        # عرض كل الاسهم حتى لو ما حققت عشان تعرف السوق
        st.info("جرب تخلي التذبذب 0.5% والاوبشن 100")
    else:
        results = sorted(results, key=lambda x: x['premium'], reverse=True)
        st.success(f"لقيت {len(results)} سهم 🔥")
        for r in results:
            icon = "⭐🔨 مطرقة + تذبذب + اوبشن" if r['hammer'] else "🔥 تذبذب + اوبشن حامي"
            msg = f"🐋 <b>{r['symbol']} {icon}</b>\n📈 تذبذب {r['vol']:.2f}% | ${r['price']:.2f}\n💰 {r['opt']['strike']} Exp {r['exp']} Vol {r['opt_vol']:,} Prem ${r['premium']:,.0f}"
            send_telegram(msg)
            st.write(f"**{r['symbol']}** {icon} | Vol {r['vol']:.2f}% | Opt Vol {r['opt_vol']:,} | Prem ${r['premium']:,.0f} | ${r['price']:.2f}")

        st.balloons()
else:
    st.info("خففت لك الفلتر: الآن يطلع من 1.5% تذبذب و 300 عقد اوبشن. اضغط الزر")
