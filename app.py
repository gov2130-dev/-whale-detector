import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V76 جميع الفريمات", layout="wide")
st.title("🔥 V76 - يفحص آخر الشارت في جميع الفريمات")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=15)
    except: pass

# جميع الفريمات اللي طلبتها
TIMEFRAMES = [
    ("1m", "1دقيقة - سكالب", "1d"),
    ("5m", "5 دقايق", "5d"),
    ("15m", "15 دقيقة", "10d"),
    ("30m", "30 دقيقة", "10d"),
    ("1h", "ساعة", "20d"),
    ("4h", "4 ساعات", "30d"),
    ("1d", "يومي", "60d"),
]

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM"]

def check_pattern(df):
    if len(df) < 4: return None
    c_prev = df.iloc[-3]
    c_ham = df.iloc[-2]
    c_next = df.iloc[-1]

    body = abs(c_ham['Close']-c_ham['Open'])
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0 or body==0: return None

    vol_ok = c_ham['Volume'] > c_prev['Volume']

    # مطرقة صاعدة ذيل سفلي = CALL
    is_bull = lower >= body*2.0 and body <= total*0.4
    bull_confirm = c_next['Close'] > c_ham['High']
    if is_bull and vol_ok and bull_confirm:
        return {"dir":"CALL", "type":"CALL 🟢 صاعد (ذيل سفلي)", "tail":f"{lower/body:.1f}x سفلي", "ham":c_ham, "prev":c_prev, "next":c_next}

    # شوتينق ستار ذيل علوي = PUT
    is_bear = upper >= body*2.0 and body <= total*0.4
    bear_confirm = c_next['Close'] < c_ham['Low']
    if is_bear and vol_ok and bear_confirm:
        return {"dir":"PUT", "type":"PUT 🔴 نازل (ذيل علوي)", "tail":f"{upper/body:.1f}x علوي", "ham":c_ham, "prev":c_prev, "next":c_next}

    return None

def get_whale(tk, direction):
    try:
        for exp in tk.options[:2]:
            chain = tk.option_chain(exp)
            df = chain.calls if direction=="CALL" else chain.puts
            df = df.copy()
            df['premium'] = df['volume']*df['lastPrice']*100
            filt = df[(df['volume']>300) & (df['premium']>50000) & (df['bid']>0.1)]
            if len(filt)>0:
                top = filt.sort_values('premium', ascending=False).iloc[0]
                return top, exp
    except: return None
    return None

selected_tfs = st.multiselect("اختار الفريمات اللي تبي تفحصها (تقدر تختار الكل)", [t[1] for t in TIMEFRAMES], default=["5 دقايق","15 دقيقة","ساعة","يومي"])
# تحويل الاسماء لاكواد
tf_map = {name: (code, period) for code, name, period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

if st.button("🚀 افحص جميع الفريمات - آخر الشارت فقط"):
    all_results = []
    prog = st.progress(0)
    total = len(UNIVERSE)*len(selected_codes)
    cnt=0
    for sym in UNIVERSE:
        tk = yf.Ticker(sym)
        for (code, period), name in zip(selected_codes, selected_tfs):
            cnt+=1
            prog.progress(cnt/total)
            try:
                df = tk.history(period=period, interval=code)
                pat = check_pattern(df)
                if pat:
                    whale = get_whale(tk, pat['dir'])
                    if whale:
                        all_results.append({
                            "سهم":sym, "فريم":name, "كود":code,
                            "اتجاه":pat['type'], "dir":pat['dir'],
                            "ذيل":pat['tail'],
                            "سعر":f"${df.iloc[-1]['Close']:.2f}",
                            "فوليوم": f"{pat['ham']['Volume']:,.0f}>{pat['prev']['Volume']:,.0f}",
                            "تأكيد": f"{pat['next']['Close']:.2f}",
                            "عقد":f"{whale[0]['strike']} Vol {whale[0]['volume']:,}",
                            "بريميوم":f"${whale[0]['premium']:,.0f}",
                            "whale":whale[0], "exp":whale[1]
                        })
            except: continue
    prog.empty()

    if not all_results:
        st.error("ما فيه أي مطرقة في آخر الشارت في جميع الفريمات اللي اخترتها حالياً")
        st.info("جرب تختار فريمات صغيرة 1m و 5m - تطلع اشارات اكثر")
    else:
        df_show = pd.DataFrame(all_results)[["سهم","فريم","اتجاه","ذيل","سعر","فوليوم","عقد","بريميوم"]]
        st.dataframe(df_show, use_container_width=True)

        for r in all_results:
            icon = "🟢" if r['dir']=="CALL" else "🔴"
            msg = f"{icon} <b>{r['سهم']} {r['اتجاه']}</b> فريم {r['فريم']}\nذيل {r['ذيل']} | {r['فوليوم']}\nتأكيد {r['تأكيد']} | سعر {r['سعر']}\n💰 {r['عقد']} Exp {r['exp']} {r['بريميوم']}"
            send_telegram(msg)

        st.success(f"لقيت {len(all_results)} اشارة حية في آخر الشارت عبر جميع الفريمات وتم ارسالها")
        st.balloons()
else:
    st.info("V76 يفحص آخر 3 شموع فقط في كل فريم تختاره: 1m,5m,15m,30m,1h,4h,1d. المطرقة السفلية=CALL والصاعدة=PUT")
