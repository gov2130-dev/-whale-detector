import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V72 مطرقة ذكي", layout="wide")
st.title("🔨 V72 - يكشف المطرقة حتى لو قريبة")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=15)
    except: pass

def analyze_candle(candle, prev, nxt):
    body = abs(candle['Close'] - candle['Open'])
    upper = candle['High'] - max(candle['Close'], candle['Open'])
    lower = min(candle['Close'], candle['Open']) - candle['Low']
    total = candle['High'] - candle['Low']
    if total == 0: return None
    tail_ratio = lower / body if body>0 else 0
    body_ratio = body / total
    vol_ok = candle['Volume'] > prev['Volume']
    close_ok = nxt['Close'] > candle['High']
    is_hammer = tail_ratio >= 2.0 and body_ratio <= 0.4 and lower >= total*0.5
    return {
        "tail_ratio": tail_ratio, "body_ratio": body_ratio,
        "vol_ok": vol_ok, "close_ok": close_ok, "is_hammer": is_hammer,
        "hammer_vol": candle['Volume'], "prev_vol": prev['Volume'],
        "high": candle['High'], "close_next": nxt['Close']
    }

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM"]

def scan(sym):
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period="15d", interval="1d")
        if len(df) < 5: return None
        # آخر 7 أيام
        candidates = []
        for i in range(-7, -1):
            c_prev = df.iloc[i-1]; c_ham = df.iloc[i]; c_next = df.iloc[i+1]
            info = analyze_candle(c_ham, c_prev, c_next)
            if info: candidates.append((c_ham, info))

        # خذ أقوى شمعة مطرقة
        if not candidates: return None
        best_candle, best_info = max(candidates, key=lambda x: x[1]['tail_ratio'])

        # شرط الاوبشن مخفف ل V72
        whale = None
        try:
            exps = tk.options[:2]
            for exp in exps:
                chain = tk.option_chain(exp)
                calls = chain.calls
                calls['premium'] = calls['volume'] * calls['lastPrice'] * 100
                # فلتر مخفف: 300 عقد + 50k
                filt = calls[(calls['volume']>300) & (calls['premium']>50000)]
                if len(filt)>0:
                    top = filt.sort_values('premium', ascending=False).iloc[0]
                    whale = (top, exp)
                    break
        except: pass

        return {
            "symbol": sym, "price": df.iloc[-1]['Close'],
            "best": best_info, "candle_date": str(best_candle.name.date()),
            "whale": whale, "df": df.tail(5)
        }
    except: return None

if st.button("🚀 افحص المطرقة + الحوت الآن"):
    rows = []
    prog = st.progress(0)
    for idx, sym in enumerate(UNIVERSE):
        prog.progress((idx+1)/len(UNIVERSE))
        r = scan(sym)
        if r: rows.append(r)
    prog.empty()

    if not rows:
        st.warning("ما فيه بيانات")
    else:
        # جدول تشخيصي
        table = []
        for r in rows:
            table.append({
                "سهم": r['symbol'],
                "ذيل/جسم": f"{r['best']['tail_ratio']:.1f}x",
                "جسم/شمعة": f"{r['best']['body_ratio']:.2f}",
                "فوليوم اعلى؟": "✅" if r['best']['vol_ok'] else "❌",
                "اغلاق فوق القمة؟": "✅" if r['best']['close_ok'] else "❌",
                "مطرقة؟": "✅" if r['best']['is_hammer'] else "❌",
                "حوت؟": f"Vol {r['whale'][0]['volume']:,}" if r['whale'] else "❌",
                "تاريخ": r['candle_date']
            })
        df_show = pd.DataFrame(table)
        st.dataframe(df_show, use_container_width=True)

        # الآن الفلترة النهائية اللي طلبتها بالحرف
        final = [r for r in rows if r['best']['is_hammer'] and r['best']['vol_ok'] and r['best']['close_ok'] and r['whale']]

        if not final:
            st.warning(f"ما فيه أسهم تحقق 4 شروط مع بعض حالياً. أقرب أسهم هي اللي فوق 👆")
            st.info("شوف الجدول: اللي عنده ✅ في كل الخانات هو المطرقة الكاملة. حالياً السوق هادي، جرب تفحص على فريم ساعة؟")
        else:
            st.success(f"لقيت {len(final)} مطرقة كاملة 🔨🐋")
            for r in final:
                msg = f"🔨🐋 <b>{r['symbol']}</b> {r['candle_date']}\nذيل {r['best']['tail_ratio']:.1f}x | فوليوم {r['best']['hammer_vol']:,.0f}>{r['best']['prev_vol']:,.0f} | اغلاق {r['best']['close_next']:.2f}>{r['best']['high']:.2f}\n💰 حوت {r['whale'][0]['strike']} Vol {r['whale'][0]['volume']:,} Prem ${r['whale'][0]['premium']:,.0f}"
                send_telegram(msg)
                st.success(f"{r['symbol']} - ارسل لتليجرام ✅")
            st.balloons()

    # زر اضافي للساعة
    st.markdown("---")
    if st.button("⏰ افحص على فريم الساعة (فرص أكثر)"):
        st.info("على الساعة تطلع مطارق كثيرة يومياً - تبي أحول الكود لفريم 1H؟")
else:
    st.info("V72 يعرض لك جدول تشخيصي: ذيل/جسم، هل الفوليوم اعلى، هل اغلق فوق القمة، وهل فيه حوت. اضغط الزر")
