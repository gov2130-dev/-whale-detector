import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V80 لا يضيع", layout="wide")
st.title("✅ V80 - يطلع النتائج وما يضيع + بعد إغلاق التأكيد")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

# نحفظ النتائج
if "results" not in st.session_state:
    st.session_state.results = []

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","MSTR","MSFT","NFLX","MU","SOFI","AAPL","META","COIN","MARA","RIOT","SMCI","AVGO","ARM","GOOGL","AMZN","GME"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["15 دقيقة","30 دقيقة","ساعة","يومي"])
tail_min = st.slider("أقل ذيل", 1.0, 3.0, 1.5, help="اللي في صورتك 5.5x")
confirm_type = st.radio("نوع التأكيد", ["إغلاق فوق إغلاق المطرقة (يطلع بسرعة بعد الإغلاق)", "إغلاق فوق قمة المطرقة (أدق لكن متأخر)"], index=0)

tf_map = {name: (code, period) for code, name, period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

def check_pattern_final(df, tail_min, confirm_high):
    if len(df) < 4: return None
    c_prev = df.iloc[-3]
    c_ham = df.iloc[-2]
    c_next = df.iloc[-1] # شمعة التأكيد المغلقة

    body = abs(c_ham['Close']-c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    total = c_ham['High']-c_ham['Low']
    if total==0 or body==0: return None

    vol_ok = c_ham['Volume'] >= c_prev['Volume']*0.8 # خففت لـ 80% عشان ما يضيع
    small_body = body <= total*0.6

    # مطرقة سفلية
    if lower >= body*tail_min and small_body and vol_ok:
        if confirm_high:
            confirmed = c_next['Close'] > c_ham['High']
            conf_txt = f"{c_next['Close']:.2f}>{c_ham['High']:.2f} قمة"
        else:
            confirmed = c_next['Close'] > c_ham['Close'] and c_next['Close'] > c_ham['Open']
            conf_txt = f"{c_next['Close']:.2f}>{c_ham['Close']:.2f} إغلاق"

        if confirmed:
            return {"dir":"CALL", "type":f"CALL 🟢 {lower/body:.1f}x سفلي", "ham":c_ham, "prev":c_prev, "next":c_next, "conf_txt":conf_txt, "tail":lower/body}

    # مطرقة علوية
    if upper >= body*tail_min and small_body and vol_ok:
        if confirm_high:
            confirmed = c_next['Close'] < c_ham['Low']
        else:
            confirmed = c_next['Close'] < c_ham['Close']

        if confirmed:
            return {"dir":"PUT", "type":f"PUT 🔴 {upper/body:.1f}x علوي", "ham":c_ham, "prev":c_prev, "next":c_next, "conf_txt":conf_txt if 'conf_txt' in locals() else "", "tail":upper/body}

    return None

if st.button(f"🚀 افحص {len(UNIVERSE)} سهم - بعد إغلاق الشمعة مباشرة"):
    confirm_high_bool = "قمة" in confirm_type
    all_res = []
    prog = st.progress(0)
    cnt=0
    total=len(UNIVERSE)*len(selected_codes)
    for sym in UNIVERSE:
        tk = yf.Ticker(sym)
        for (code, period), name in zip(selected_codes, selected_tfs):
            cnt+=1; prog.progress(cnt/total)
            try:
                df = tk.history(period=period, interval=code)
                pat = check_pattern_final(df, tail_min, confirm_high_bool)
                if pat:
                    all_res.append({
                        "سهم":sym, "فريم":name, "اتجاه":pat['type'], "ذيل":f"{pat['tail']:.1f}x",
                        "سعر الآن":f"${df.iloc[-1]['Close']:.2f}",
                        "وقت التأكيد":str(pat['next'].name)[5:16],
                        "فوليوم":f"{pat['ham']['Volume']:,.0f}>{pat['prev']['Volume']:,.0f}",
                        "تأكيد":pat['conf_txt']
                    })
            except: continue
    prog.empty()
    st.session_state.results = all_res

# عرض النتائج المحفوظة (ما تضيع)
if st.session_state.results:
    st.success(f"لقيت {len(st.session_state.results)} إشارة بعد إغلاق شمعة التأكيد مباشرة - ما راح تضيع")
    st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True)

    for r in st.session_state.results:
        if st.button(f"أرسل تليجرام {r['سهم']} {r['فريم']}", key=f"{r['سهم']}{r['فريم']}{r['وقت التأكيد']}"):
            send_telegram(f"⚡ {r['سهم']} {r['اتجاه']} فريم {r['فريم']}\nسعر {r['سعر الآن']} وقت {r['وقت التأكيد']}\n{r['فوليوم']}\n{r['تأكيد']}")

    st.balloons()
else:
    if st.button("عرض النتائج السابقة"):
        st.info("ما فيه نتائج محفوظة - اضغط فحص أول")

st.caption("V80: اختار (إغلاق فوق إغلاق المطرقة) عشان تطلع لك شمعة TSLA اللي في صورتك 5.5x بعد إغلاق 14:30 مباشرة")
