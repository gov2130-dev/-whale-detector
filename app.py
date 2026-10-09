import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V77 اختيار الأسهم", layout="wide")
st.title("🔥 V77 - اختار الأسهم + جميع الفريمات")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=15)
    except: pass

# قوائم جاهزة
LISTS = {
    "🔥 الأكثر تذبذباً (31 سهم)": ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM","INTC"],
    "💥 ميم وبتكوين (20 سهم)": ["GME","AMC","MARA","RIOT","CLSK","COIN","MSTR","BITX","SOXL","TQQQ","SQQQ","SPY","QQQ","IWM","UVXY","TSLA","NVDA","PLTR","SOFI","NIO"],
    "🏦 أسهمك الخاصة": []
}

list_name = st.selectbox("اختار قائمة الأسهم", list(LISTS.keys()))
custom_input = st.text_area("أو اكتب أسهمك (مفصولة بفاصلة) مثال: NVDA, TSLA, AAPL", "")

if custom_input.strip():
    universe = [s.strip().upper() for s in custom_input.split(",") if s.strip()]
else:
    universe = LISTS[list_name]

if list_name == "🏦 أسهمك الخاصة" and not custom_input.strip():
    st.warning("اكتب أسهمك في المربع فوق")
    universe = []

st.write(f"سيتم فحص **{len(universe)} سهم**: {', '.join(universe[:15])} {'...' if len(universe)>15 else ''}")

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("4h","4 ساعات","30d"),("1d","يومي","60d")]
selected_tfs = st.multiselect("اختار الفريمات", [t[1] for t in TIMEFRAMES], default=["5 دقايق","15 دقيقة","ساعة","يومي"])
tf_map = {name: (code, period) for code, name, period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

# تخفيف الشرط
tail_min = st.slider("أقل طول ذيل (كم ضعف الجسم)", 1.0, 3.0, 1.5)

def check_pattern(df, tail_min):
    if len(df) < 4: return None
    c_prev = df.iloc[-3]; c_ham = df.iloc[-2]; c_next = df.iloc[-1]
    body = abs(c_ham['Close']-c_ham['Open'])
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0 or body==0: return None
    vol_ok = c_ham['Volume'] > c_prev['Volume']*0.9 # خففت شرط الفوليوم لـ 90%

    is_bull = lower >= body*tail_min
    if is_bull and vol_ok and c_next['Close'] > c_ham['High']:
        return {"dir":"CALL", "type":f"CALL 🟢 ذيل سفلي {lower/body:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next}
    is_bear = upper >= body*tail_min
    if is_bear and vol_ok and c_next['Close'] < c_ham['Low']:
        return {"dir":"PUT", "type":f"PUT 🔴 ذيل علوي {upper/body:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next}
    return None

if st.button(f"🚀 افحص {len(universe)} سهم في جميع الفريمات"):
    if not universe: st.stop()
    all_results = []
    prog = st.progress(0)
    total = len(universe)*len(selected_codes)
    cnt=0
    for sym in universe:
        tk = yf.Ticker(sym)
        for (code, period), name in zip(selected_codes, selected_tfs):
            cnt+=1; prog.progress(cnt/total)
            try:
                df = tk.history(period=period, interval=code)
                pat = check_pattern(df, tail_min)
                if pat:
                    all_results.append({"سهم":sym, "فريم":name, "اتجاه":pat['type'], "سعر":f"${df.iloc[-1]['Close']:.2f}", "فوليوم":f"{pat['ham']['Volume']:,.0f}>{pat['prev']['Volume']:,.0f}", "وقت":str(pat['ham'].name)})
            except: continue
    prog.empty()

    if not all_results:
        st.error(f"فحصت {len(universe)} سهم في {len(selected_codes)} فريمات = {total} شارت، ما فيه مطرقة في آخر شمعة الآن")
        st.info("الحل: خفف الذيل لـ 1.0x أو اختار فريم 1m - أو اكتب في المربع فوق 50 سهم مرة وحدة")
    else:
        st.dataframe(pd.DataFrame(all_results), use_container_width=True)
        for r in all_results:
            send_telegram(f"{r['اتجاه']} {r['سهم']} فريم {r['فريم']} سعر {r['سعر']} فوليوم {r['فوليوم']}")
        st.success(f"لقيت {len(all_results)} اشارة حية")
        st.balloons()
