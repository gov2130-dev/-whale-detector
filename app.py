import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V81 صارم - شروط أصلية", layout="wide")
st.title("🎯 V81 - الشروط الأصلية الصارمة + بعد إغلاق التأكيد")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

if "results" not in st.session_state:
    st.session_state.results = []

TIMEFRAMES = [("1m","1دقيقة","1d"),("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM","INTC","GME","AMC"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["5 دقايق","15 دقيقة","30 دقيقة","ساعة","يومي"])

# الشروط الأصلية اللي انت كتبتها أول مرة
st.markdown("### ✅ شروطك الأصلية (الصارمة):")
st.info("""
**CALL صاعد (ذيل سفلي):**
1- الذيل السفلي >= 2 * الجسم
2- الجسم <= 40% من طول الشمعة كامل
3- الذيل السفلي >= 50% من طول الشمعة
4- الفوليوم > السابق * 1.1
5- إغلاق شمعة التأكيد > قمة المطرقة

**PUT نازل (ذيل علوي) نفس الشروط بالعكس**
""")

def is_strict_hammer(c_ham, c_prev, direction):
    body = abs(c_ham['Close']-c_ham['Open'])
    if body==0: return False, 0

    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0: return False, 0

    # شرطك الأصلي الصارم
    if direction=="CALL":
        cond1 = lower >= body*2.0
        cond2 = body <= total*0.4
        cond3 = lower >= total*0.5
        cond4 = c_ham['Volume'] > c_prev['Volume']*1.1
        ok = cond1 and cond2 and cond3 and cond4
        return ok, lower/body

    else: # PUT
        cond1 = upper >= body*2.0
        cond2 = body <= total*0.4
        cond3 = upper >= total*0.5
        cond4 = c_ham['Volume'] > c_prev['Volume']*1.1
        ok = cond1 and cond2 and cond3 and cond4
        return ok, upper/body

def check_final(df):
    if len(df) < 4: return None
    c_prev = df.iloc[-3]
    c_ham = df.iloc[-2]
    c_next = df.iloc[-1] # تأكيد مغلقة

    # فحص CALL
    ok_call, ratio = is_strict_hammer(c_ham, c_prev, "CALL")
    if ok_call and c_next['Close'] > c_ham['High']:
        return {"dir":"CALL", "type":f"CALL 🟢 ذيل سفلي {ratio:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":ratio, "tail":"سفلي"}

    # فحص PUT
    ok_put, ratio = is_strict_hammer(c_ham, c_prev, "PUT")
    if ok_put and c_next['Close'] < c_ham['Low']:
        return {"dir":"PUT", "type":f"PUT 🔴 ذيل علوي {ratio:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":ratio, "tail":"علوي"}

    return None

if st.button(f"🚀 افحص {len(UNIVERSE)} سهم بالشروط الصارمة"):
    all_res=[]
    prog=st.progress(0)
    cnt=0
    total=len(UNIVERSE)*len(selected_tfs)
    tf_map={name:(code,period) for code,name,period in TIMEFRAMES}
    selected_codes=[tf_map[name] for name in selected_tfs]

    for sym in UNIVERSE:
        tk=yf.Ticker(sym)
        for (code,period),name in zip(selected_codes,selected_tfs):
            cnt+=1; prog.progress(cnt/total)
            try:
                df=tk.history(period=period, interval=code)
                pat=check_final(df)
                if pat:
                    all_res.append({
                        "سهم":sym, "فريم":name, "اتجاه":pat['type'],
                        "ذيل":f"{pat['ratio']:.1f}x {pat['tail']}",
                        "سعر":f"${df.iloc[-1]['Close']:.2f}",
                        "وقت إغلاق التأكيد":str(pat['next'].name)[5:16],
                        "فوليوم":f"{pat['ham']['Volume']:,.0f} > {pat['prev']['Volume']:,.0f} ({pat['ham']['Volume']/pat['prev']['Volume']:.1f}x)",
                        "تأكيد":f"{pat['next']['Close']:.2f} {'↑' if pat['dir']=='CALL' else '↓'} {pat['ham']['High'] if pat['dir']=='CALL' else pat['ham']['Low']:.2f}"
                    })
            except: continue
    prog.empty()
    st.session_state.results=all_res

# عرض النتائج - ما تضيع
if st.session_state.results:
    st.success(f"لقيت {len(st.session_state.results)} مطرقة حقيقية بالشروط الصارمة بعد إغلاق شمعة التأكيد")
    st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True)
    for r in st.session_state.results:
        send_telegram(f"🎯 {r['سهم']} {r['اتجاه']} فريم {r['فريم']} ذيل {r['ذيل']}\nوقت إغلاق {r['وقت إغلاق التأكيد']} سعر {r['سعر']}\n{r['فوليوم']}\nتأكيد {r['تأكيد']}")
    st.balloons()
else:
    st.warning("بالشروط الصارمة الأصلية ما فيه أي مطرقة في آخر الشارت الآن - وهذا طبيعي، المطرقة الحقيقية نادرة")
    st.info("AMD اللي في صورتك ما راح تطلع أبداً بهذا الكود لأن ذيلها 0.2x وفوليومها نازل - وهذا الصح")

# زر فحص سهم واحد بالتفصيل
st.divider()
sym_test = st.text_input("افحص سهم واحد بالتفصيل (مثال AMD)", "AMD")
code_test = st.selectbox("فريم الفحص التفصيلي", ["5m","15m","30m","1h","1d"], index=2)
if st.button(f"فحص {sym_test} لماذا لم تظهر؟"):
    df = yf.Ticker(sym_test).history(period="10d", interval=code_test)
    c_prev = df.iloc[-3]; c_ham = df.iloc[-2]; c_next = df.iloc[-1]
    body = abs(c_ham['Close']-c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    total = c_ham['High']-c_ham['Low']
    st.write(f"ذيل سفلي {lower/body:.1f}x (مطلوب >=2.0) - {'✅' if lower>=body*2 else '❌'}")
    st.write(f"جسم {body/total*100:.1f}% من الشمعة (مطلوب <=40%) - {'✅' if body<=total*0.4 else '❌'}")
    st.write(f"فوليوم {c_ham['Volume']:,.0f} vs السابق {c_prev['Volume']:,.0f} - {'✅' if c_ham['Volume']>c_prev['Volume']*1.1 else '❌'}")
    st.write(f"تأكيد {c_next['Close']:.2f} vs قمة {c_ham['High']:.2f} - {'✅' if c_next['Close']>c_ham['High'] else '❌'}")
