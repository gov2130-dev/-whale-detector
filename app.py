import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V71 مطرقة + حوت", layout="wide")
st.title("🔨🐋 V71 - مطرقة + عقد حوت سريع")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
        requests.post(url, data=data, timeout=15)
    except: pass

def is_hammer_strict(candle):
    body = abs(candle['Close'] - candle['Open'])
    upper = candle['High'] - max(candle['Close'], candle['Open'])
    lower = min(candle['Close'], candle['Open']) - candle['Low']
    total = candle['High'] - candle['Low']
    if total == 0 or body == 0: return False
    # ذيل طويل 3 اضعاف الجسم + جسم صغير + ذيل علوي شبه معدوم
    cond1 = lower >= (body * 3)
    cond2 = body <= (total * 0.30)
    cond3 = upper <= (total * 0.15)
    cond4 = lower >= (total * 0.60)
    return cond1 and cond2 and cond3 and cond4

UNIVERSE = ["NVDA","TSLA","SMCI","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM","INTC"]

def check_whale_contract(tk):
    try:
        exps = tk.options[:2] # اقرب تاريخين فقط - اسرع تذبذب
        best = []
        for exp in exps:
            chain = tk.option_chain(exp)
            for df_opt in [chain.calls, chain.puts]:
                df = df_opt.copy()
                if len(df) == 0: continue
                df['premium'] = df['volume'] * df['lastPrice'] * 100
                df['spread_pct'] = (df['ask'] - df['bid']) / df['lastPrice'] * 100
                
                # شروط الحوت V52 الحقيقية
                cond_whale = (
                    (df['volume'] > df['openInterest'] * 0.8) &  # دخول حوت
                    (df['volume'] > 800) &                      # فوليوم عالي
                    (df['premium'] > 150000) &                  # فلوس كبيرة
                    (df['bid'] > 0.1) &                          # مو عقد ميّت
                    (df['spread_pct'] < 15)                      # نقدر ندخل ونطلع بسرعة
                )
                whales = df[cond_whale]
                for _, row in whales.iterrows():
                    best.append((row, exp))
        if not best: return None
        # رتب حسب البريميوم
        best = sorted(best, key=lambda x: x[0]['premium'], reverse=True)
        return best[0]
    except Exception as e:
        return None

def scan(sym):
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period="15d", interval="1d")
        if len(df) < 5: return None

        # نفحص كل شمعة في آخر 4 أيام اذا كانت مطرقة وتحقق الشروط
        for i in range(-4, -1): # -4, -3, -2
            c_prev = df.iloc[i-1]
            c_hammer = df.iloc[i]
            c_next = df.iloc[i+1]

            if not is_hammer_strict(c_hammer): continue
            if not (c_hammer['Volume'] > c_prev['Volume']): continue # فوليوم المطرقة اكبر من اللي قبلها
            if not (c_next['Close'] > c_hammer['High']): continue # اللي بعدها تقفل فوق قمة المطرقة

            # اذا تحقق شرط السهم، شيك شرط الأوبشن
            whale = check_whale_contract(tk)
            if not whale: continue

            row, exp = whale
            return {
                "symbol": sym,
                "hammer_date": str(c_hammer.name.date()),
                "hammer_high": c_hammer['High'],
                "hammer_low": c_hammer['Low'],
                "hammer_vol": c_hammer['Volume'],
                "prev_vol": c_prev['Volume'],
                "confirm_close": c_next['Close'],
                "price": df.iloc[-1]['Close'],
                "opt": row,
                "exp": exp
            }
        return None
    except: return None

if st.button("🚀 افحص شروط المطرقة + الحوت الآن"):
    results = []
    prog = st.progress(0)
    for idx, sym in enumerate(UNIVERSE):
        prog.progress((idx+1)/len(UNIVERSE))
        r = scan(sym)
        if r: results.append(r)
    prog.empty()

    if not results:
        st.warning("ما فيه أسهم تحقق شرط المطرقة + الحوت مع بعض في آخر 4 أيام")
        st.info("الشرط دقيق: مطرقة ذيل طويل + فوليوم اعلى من السابق + اغلاق فوق القمة + عقد حوت Premium >150k")
    else:
        st.success(f"لقيت {len(results)} حوت بمطرقة ✅")
        for r in results:
            msg = f"""
🔨🐋 <b>{r['symbol']} - مطرقة + حوت</b>
📅 تاريخ المطرقة: {r['hammer_date']}
✅ الشروط:
1- ذيل طويل: {r['hammer_low']:.2f} -> {r['hammer_high']:.2f}
2- فوليوم المطرقة {r['hammer_vol']:,.0f} > السابق {r['prev_vol']:,.0f}
3- تأكيد: اغلاق {r['confirm_close']:.2f} فوق قمة {r['hammer_high']:.2f}
💲 سعر الآن: ${r['price']:.2f}
💰 عقد الحوت:
Strike ${r['opt']['strike']} {r['exp']}
Vol {r['opt']['volume']:,} > OI {r['opt']['openInterest']:,}
Premium ${r['opt']['premium']:,.0f} | Last ${r['opt']['lastPrice']}
Spread {r['opt']['ask']-r['opt']['bid']:.2f} (دخول سريع)
"""
            send_telegram(msg)
            st.markdown(f"### {r['symbol']} 🔨 تاريخ {r['hammer_date']}")
            st.write(f"فوليوم مطرقة {r['hammer_vol']:,} > السابق {r['prev_vol']:,} | تأكيد {r['confirm_close']:.2f} > قمة {r['hammer_high']:.2f}")
            st.write(f"عقد: {r['opt']['strike']} Exp {r['exp']} Vol {r['opt']['volume']:,} Prem ${r['opt']['premium']:,.0f}")

        st.balloons()
else:
    st.info("V71: يفحص آخر 4 أيام لكل سهم: مطرقة بذيل 3x + فوليوم اعلى + اغلاق فوق القمة + عقد حوت سريع")
