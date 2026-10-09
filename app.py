import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import time

st.set_page_config(page_title="V78 لحظي بعد الإغلاق", layout="wide")
st.title("⚡ V78 - تنبيه بعد إغلاق شمعة التأكيد مباشرة")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

TIMEFRAMES = [("1m","1دقيقة","1d"),("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("4h","4 ساعات","30d"),("1d","يومي","60d")]

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM","INTC","GME","AMC","SOXL","TQQQ"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["5 دقايق","15 دقيقة","30 دقيقة","ساعة"])
tail_min = st.slider("أقل ذيل", 1.0, 3.0, 1.5)

tf_map = {name: (code, period) for code, name, period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

def check_last_closed(df, tail_min):
    # نتأكد أن آخر شمعة في الداتا هي شمعة مغلقة تماماً
    # yfinance آخر صف دائماً شمعة مغلقة إلا اذا السوق مفتوح والفريم صغير
    # عشان كذا نفحص آخر 3 شموع مغلقة: prev, hammer, confirm
    if len(df) < 5: return None

    # نأخذ آخر 3 شموع مغلقة مؤكدة
    # لو آخر شمعة توها تكونت قبل ثواني، نتجاهلها ونأخذ اللي قبلها كـ تأكيد
    c_prev = df.iloc[-3]
    c_ham = df.iloc[-2]
    c_next = df.iloc[-1] # هذه شمعة التأكيد المغلقة

    body = abs(c_ham['Close']-c_ham['Open'])
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0 or body==0: return None

    vol_ok = c_ham['Volume'] > c_prev['Volume']*0.9

    # CALL
    is_bull = lower >= body*tail_min and body <= total*0.5
    if is_bull and vol_ok and c_next['Close'] > c_ham['High']:
        return {"dir":"CALL", "type":f"CALL 🟢 ذيل سفلي {lower/body:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "time":c_next.name}

    # PUT - ذيل علوي
    is_bear = upper >= body*tail_min and body <= total*0.5
    if is_bear and vol_ok and c_next['Close'] < c_ham['Low']:
        return {"dir":"PUT", "type":f"PUT 🔴 ذيل علوي {upper/body:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "time":c_next.name}

    return None

auto = st.checkbox("🔄 فحص تلقائي كل دقيقة (يرسل تليجرام لحظي بعد إغلاق الشمعة)")

if st.button(f"🚀 افحص الآن - بعد إغلاق الشمعة مباشرة") or auto:
    placeholder = st.empty()

    def do_scan():
        all_results = []
        for sym in UNIVERSE:
            tk = yf.Ticker(sym)
            for (code, period), name in zip(selected_codes, selected_tfs):
                try:
                    df = tk.history(period=period, interval=code)
                    pat = check_last_closed(df, tail_min)
                    if pat:
                        # نتأكد أن شمعة التأكيد قفلت قبل أقل من فترة الفريم نفسه (إشارة جديدة)
                        all_results.append({
                            "سهم":sym, "فريم":name, "كود":code,
                            "اتجاه":pat['type'], "dir":pat['dir'],
                            "سعر":f"${df.iloc[-1]['Close']:.2f}",
                            "وقت الإغلاق": str(pat['time'])[-8:-3] if code!="1d" else str(pat['time'].date()),
                            "فوليوم": f"{pat['ham']['Volume']:,.0f}>{pat['prev']['Volume']:,.0f}",
                            "تأكيد": f"{pat['next']['Close']:.2f} {'↑' if pat['dir']=='CALL' else '↓'} {pat['ham']['High']:.2f}" if pat['dir']=='CALL' else f"{pat['next']['Close']:.2f} ↓ {pat['ham']['Low']:.2f}",
                        })
                except: continue
        return all_results

    if auto:
        st.info("الفحص التلقائي شغال - كل دقيقة يفحص آخر شمعة مغلقة ويرسل تليجرام فور إغلاق شمعة التأكيد")
        while True:
            res = do_scan()
            if res:
                df_show = pd.DataFrame(res)
                placeholder.dataframe(df_show, use_container_width=True)
                for r in res:
                    msg = f"⚡ <b>{r['سهم']} {r['اتجاه']} - إغلاق الآن</b>\nفريم {r['فريم']} | وقت {r['وقت الإغلاق']}\nسعر {r['سعر']} | {r['فوليوم']}\nتأكيد {r['تأكيد']}\nتم بعد إغلاق الشمعة الثالثة مباشرة"
                    send_telegram(msg)
                st.success(f"إشارة جديدة بعد الإغلاق مباشرة: {len(res)}")
            time.sleep(60) # كل دقيقة
            placeholder.empty()
    else:
        res = do_scan()
        if not res:
            st.warning("ما فيه إشارة جديدة بعد إغلاق آخر شمعة - انتظر إغلاق الشمعة الحالية")
        else:
            st.dataframe(pd.DataFrame(res), use_container_width=True)
            for r in res:
                send_telegram(f"⚡ {r['سهم']} {r['اتجاه']} فريم {r['فريم']} وقت {r['وقت الإغلاق']} سعر {r['سعر']}")
            st.success(f"تم إرسال {len(res)} إشارة - كلها بعد إغلاق شمعة التأكيد الثالثة مباشرة")
            st.balloons()
