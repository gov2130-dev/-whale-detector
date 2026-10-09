import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="صياد التذبذب - ابو راكان V69", layout="wide")
st.title("🔥 كاشف الحيتان V69 - الأكثر تذبذباً + أوبشن حامي")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML", "disable_web_page_preview": True}
        requests.post(url, data=data, timeout=15)
    except Exception as e:
        st.error(f"Telegram Error: {e}")

def is_hammer(candle):
    body = abs(candle['Close'] - candle['Open'])
    upper = candle['High'] - max(candle['Close'], candle['Open'])
    lower = min(candle['Close'], candle['Open']) - candle['Low']
    range_c = candle['High'] - candle['Low']
    if range_c == 0: return False
    return body < (range_c * 0.35) and lower >= (body * 2.2) and lower >= (range_c * 0.55) and upper <= (body * 0.6)

# قائمة الأسهم المعروفة بتذبذبها العالي - تتحدث تلقائياً
MOST_VOLATILE_UNIVERSE = [
    "NVDA","TSLA","SMCI","AMD","META","AAPL","MSFT","AMZN","NFLX","MSTR",
    "COIN","MARA","RIOT","PLTR","SOFI","GME","AMC","NIO","UPST","AI",
    "ARM","AVGO","TSM","ORCL","CRWD","PANW","DDOG","SNOW","MRVL","MU"
]

def scan_stock(sym):
    try:
        tk = yf.Ticker(sym)
        df = tk.history(period="5d", interval="1d")
        if len(df) < 3: return None

        # 1- حساب التذبذب اليوم
        last = df.iloc[-1]
        prev = df.iloc[-2]
        volatility_pct = (last['High'] - last['Low']) / prev['Close'] * 100
        change_pct = (last['Close'] - prev['Close']) / prev['Close'] * 100

        # شرط التذبذب العالي > 3%
        if volatility_pct < 3.0: return None

        # 2- شروط شمعة المطرقة اللي طلبتها
        c_prev = df.iloc[-3]
        c_hammer = df.iloc[-2]
        c_confirm = df.iloc[-1]

        cond_hammer = is_hammer(c_hammer)
        cond_vol_candle = c_hammer['Volume'] > c_prev['Volume']
        cond_close_above = c_confirm['Close'] > c_hammer['High']

        hammer_ok = cond_hammer and cond_vol_candle and cond_close_above

        # 3- شروط الاوبشن عالي التداول (V52 مطور)
        exps = tk.options
        if not exps: return None
        # نفحص اول 2 انتهاء
        best_opt = None
        for exp in exps[:2]:
            chain = tk.option_chain(exp)
            calls = chain.calls
            # فلتر الاوبشن الحامي
            calls = calls[(calls['volume'] > 1000) & (calls['openInterest'] > 500)]
            calls['premium'] = calls['volume'] * calls['lastPrice'] * 100
            calls = calls[calls['premium'] > 200000] # سيولة عالية > 200 الف
            if len(calls) == 0: continue
            top = calls.sort_values('volume', ascending=False).iloc[0]
            if best_opt is None or top['volume'] > best_opt['volume']:
                best_opt = top
                best_opt['exp'] = exp

        if best_opt is None: return None

        # لو حقق شرط واحد على الأقل: تذبذب عالي + اوبشن عالي، ولو فيه مطرقة يكون ممتاز
        return {
            "symbol": sym,
            "volatility": volatility_pct,
            "change": change_pct,
            "price": last['Close'],
            "hammer": hammer_ok,
            "hammer_data": c_hammer,
            "confirm_close": c_confirm['Close'],
            "opt": best_opt
        }
    except Exception as e:
        return None

# ===== الواجهة =====
if st.button("🚀 افحص الأكثر تذبذباً الآن"):
    results = []
    progress = st.progress(0)
    for i, sym in enumerate(MOST_VOLATILE_UNIVERSE):
        progress.progress((i+1)/len(MOST_VOLATILE_UNIVERSE))
        res = scan_stock(sym)
        if res:
            results.append(res)

    progress.empty()

    if not results:
        st.warning("ما فيه أسهم تحقق شروط التذبذب + الأوبشن الحامي حالياً")
    else:
        # ترتيب حسب التذبذب
        results = sorted(results, key=lambda x: x['volatility'], reverse=True)
        st.success(f"لقيت {len(results)} سهم حامي 🔥")

        for r in results:
            hammer_icon = "🔨 مطرقة مؤكدة" if r['hammer'] else "⚡ تذبذب عالي فقط"
            msg = f"""
🐋 <b>{r['symbol']} - {hammer_icon}</b>
📈 التذبذب: {r['volatility']:.2f}% | التغير: {r['change']:+.2f}%
💲 السعر: ${r['price']:.2f}
💰 الأوبشن الأكثر تداولاً:
   Strike ${r['opt']['strike']} Exp {r['opt']['exp']}
   Volume {r['opt']['volume']:,} | Premium ${r['opt']['premium']:,.0f}
   Last ${r['opt']['lastPrice']} | OI {r['opt']['openInterest']:,}
{f"✅ شمعة مطرقة: فوليوم {r['hammer_data']['Volume']:,.0f} واغلاق التأكيد فوق القمة" if r['hammer'] else ""}
"""
            send_telegram(msg)
            st.markdown(f"**{r['symbol']}** - تذبذب {r['volatility']:.1f}% - اوبشن Vol {r['opt']['volume']:,} - {hammer_icon}")
            st.json(r['opt'].to_dict() if hasattr(r['opt'], 'to_dict') else str(r['opt']))

        st.balloons()
        st.success("تم الارسال كلها لتليجرام ✅")
else:
    st.info(f"جاهز | يفحص {len(MOST_VOLATILE_UNIVERSE)} سهم معروف بالتذبذب العالي | CHAT_ID: {CHAT_ID}")
    st.caption("الشروط: تذبذب يومي >3% + فوليوم اوبشن >1000 + Premium >200k + شرط المطرقة اضافة قوة")
