import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V75 آخر الشارت + اتجاهين", layout="wide")
st.title("🔨 V75 - مطرقة آخر الشارت (صعود ونزول)")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM","INTC"]

def check_last_candles(df):
    if len(df) < 3: return None
    c_prev = df.iloc[-3] # قبل المطرقة
    c_ham = df.iloc[-2] # شمعة المطرقة
    c_next = df.iloc[-1] # شمعة التأكيد (آخر شمعة في الشارت)

    body = abs(c_ham['Close']-c_ham['Open'])
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0 or body==0: return None

    # شرط الفوليوم المشترك
    vol_ok = c_ham['Volume'] > c_prev['Volume']

    # 1- مطرقة صاعدة - ذيل تحت طويل = CALL
    is_bull_hammer = lower >= body*2.0 and body <= total*0.4 and lower >= total*0.5
    bull_confirm = c_next['Close'] > c_ham['High']

    if is_bull_hammer and vol_ok and bull_confirm:
        return {"type":"CALL 🟢 صاعد", "dir":"CALL", "hammer":c_ham, "prev":c_prev, "next":c_next, "tail_ratio": lower/body, "tail":"سفلي"}

    # 2- مطرقة هابطة (شوتينق ستار) - ذيل فوق طويل = PUT
    is_bear_hammer = upper >= body*2.0 and body <= total*0.4 and upper >= total*0.5
    bear_confirm = c_next['Close'] < c_ham['Low']

    if is_bear_hammer and vol_ok and bear_confirm:
        return {"type":"PUT 🔴 نازل", "dir":"PUT", "hammer":c_ham, "prev":c_prev, "next":c_next, "tail_ratio": upper/body, "tail":"علوي"}

    return None

def get_whale(tk, direction):
    try:
        exps = tk.options[:2]
        for exp in exps:
            chain = tk.option_chain(exp)
            df = chain.calls if direction=="CALL" else chain.puts
            df = df.copy()
            df['premium'] = df['volume']*df['lastPrice']*100
            filt = df[(df['volume']>500) & (df['premium']>100000) & (df['bid']>0.2)]
            if len(filt)>0:
                top = filt.sort_values('premium', ascending=False).iloc[0]
                return top, exp
    except: return None

if st.button("🚀 افحص آخر الشارت فقط - صعود ونزول"):
    results = []
    prog = st.progress(0)
    for i, sym in enumerate(UNIVERSE):
        prog.progress((i+1)/len(UNIVERSE))
        try:
            tk = yf.Ticker(sym)
            df = tk.history(period="20d", interval="1d")
            sig = check_last_candles(df)
            if sig:
                whale = get_whale(tk, sig['dir'])
                if whale:
                    results.append({"سهم":sym, **sig, "whale":whale[0], "exp":whale[1], "price":df.iloc[-1]['Close']})
        except: continue
    prog.empty()

    if not results:
        st.warning("ما فيه أي سهم محقق شرط المطرقة في آخر شمعتين اليوم - السوق ما عطى إشارة حية الآن")
        st.info("الكود الآن يفحص فقط آخر 3 شموع: [قبل المطرقة - المطرقة - تأكيد] وكلها لازم تكون في نهاية الشارت")
    else:
        st.success(f"لقيت {len(results)} إشارة حية في آخر الشارت 🔥")
        for r in results:
            msg = f"""
{'🟢' if r['dir']=='CALL' else '🔴'} <b>{r['سهم']} {r['type']} - آخر الشارت</b>
📍 المطرقة: ذيل {r['tail']} {r['tail_ratio']:.1f}x
📊 فوليوم {r['hammer']['Volume']:,.0f} > السابق {r['prev']['Volume']:,.0f}
✅ تأكيد: {r['next']['Close']:.2f} {' فوق قمة ' if r['dir']=='CALL' else ' تحت قاع '} {r['hammer']['High'] if r['dir']=='CALL' else r['hammer']['Low']:.2f}
💲 سعر الآن: ${r['price']:.2f}
💰 عقد الحوت {r['dir']}: Strike {r['whale']['strike']} Exp {r['exp']} Vol {r['whale']['volume']:,} Prem ${r['whale']['premium']:,.0f}
فريم: يومي 1D | اتجاه: {r['type']}
"""
            send_telegram(msg)
            st.markdown(f"### {r['سهم']} - {r['type']} | ذيل {r['tail']} {r['tail_ratio']:.1f}x")
            st.write(f"فوليوم {r['hammer']['Volume']:,.0f} > {r['prev']['Volume']:,.0f} | تأكيد {r['next']['Close']:.2f} | عقد {r['whale']['strike']} Vol {r['whale']['volume']:,}")

        st.balloons()
else:
    st.info("V75: يفحص فقط آخر 3 شموع في الشارت. لو تحققت المطرقة (ذيل سفلي) = CALL، ولو شوتينق ستار (ذيل علوي) = PUT. اضغط الزر")
