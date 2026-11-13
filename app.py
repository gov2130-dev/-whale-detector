# ============================================================
# راصد الحيتان - V9 - إرسال مفتوح لأي شخص من الواتساب
# بدون apikey - بدون رقم ثابت - بدون CallMeBot
# تضغط زر الإرسال -> يفتح لك الواتساب -> تختار أي شخص من جهات اتصالك
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")
st.success("✅ الإرسال الحين مفتوح - بدون apikey وبدون رقم ثابت. تضغط زر الإرسال ويفتح لك الواتساب وتختار أي شخص.")

# ============================================================
# 1. هل السوق فاتح؟ - للعرض فقط
# ============================================================
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح - بيانات حية | {ny_now.strftime('%H:%M')} نيويورك")
else:
    st.warning(f"🔴 السوق مسكر - بيانات آخر إغلاق | {ny_now.strftime('%H:%M')} نيويورك")

# ============================================================
# 2. الأسهم - 150 سهم
# ============================================================
STOCKS_150 = [
    "SPY","QQQ","IWM","DIA","VOO","IVV","ARKK","XLF","XLK","XLE",
    "NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL",
    "AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX",
    "PLTR","SNOW","CRWD","PANW","SHOP",
    "JPM","BAC","GS","MS","WFC","C","BLK","SCHW","AXP","V",
    "MA","PYPL","COIN","HOOD","SOFI",
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","HAL","MSTR","CLSK",
    "LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","REGN",
    "VRTX","ISRG","HIMS","CVS","ZTS",
    "WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG",
    "LULU","ABNB","UBER","LYFT","DASH",
    "BA","CAT","GE","HON","LMT","RTX","NOC","GD","DE","UPS","FDX","DAL",
    "T","VZ","TMUS","DIS","CMCSA","WBD","PARA","SPOT","ROKU",
    "SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","SWKS",
    "RIVN","LCID","NIO","PLUG","OPEN","GME","AMC","AFRM",
    "UPST","AI","SOUN","IONQ","RGTI","QBTS","DNA","BBAI",
    "BRK-B","PEP","KO","PG","CSCO","IBM",
]
STOCKS_150 = list(dict.fromkeys(STOCKS_150))
st.write(f"عدد الأسهم: **{len(STOCKS_150)} سهم**")

# ============================================================
# 3. جلب عقد الحوت
# ============================================================
def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None
        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            f = df[(df['lastPrice'] >= min_prem) & (df['lastPrice'] <= max_prem) &
                   (df['volume'].fillna(0) > 500) &
                   (abs(df['strike'] - last) / last < 0.05)]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]

        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')
        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        if change >= 0:
            whale = best_call if best_call is not None else best_put
            reason = "السهم صاعد، تجاهلنا PUT التحوط"
        else:
            whale = best_put if best_put is not None else best_call
            reason = "السهم هابط، تجاهلنا CALL التحوط"
        if whale is None:
            return None
        entry = float(whale['lastPrice'])
        strike = float(whale['strike'])
        volume = int(whale['volume'])
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]
        return {"symbol": symbol, "type": whale['type'], "strike": strike, "expiry": expiry,
                "entry": entry, "stop": stop, "targets": targets, "volume": volume,
                "last": last, "change": change, "reason": reason,
                "prem_range": f"{min_prem:.2f} - {max_prem:.2f}"}
    except Exception:
        return None

def make_msg(r):
    emoji = "🟢" if r['type'] == 'CALL' else "🔴"
    return f"""🔍 راصد الحيتان
{r['symbol']}
{emoji} شراء مرجح {r['type']} {r['strike']:.1f}
الانتهاء: {r['expiry']} 📅
سعر التنفيذ: {r['entry']} ({int(r['entry']*100)} دولار للعقد) 💰
الوقف: {r['stop']} 🔴 | الكمية: {r['volume']} عقد 📦
الأهداف بالترتيب 🎯
{' | '.join(map(str, r['targets']))}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""

def whatsapp_share_link(msg):
    # هذا هو الرابط المفتوح - يفتح الواتساب ويخليك تختار أي شخص من جهات اتصالك
    encoded = urllib.parse.quote(msg)
    return f"https://wa.me/?text={encoded}"

# ============================================================
# 4. الفحص
# ============================================================
if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    with st.spinner(f"جار فحص {len(STOCKS_150)} سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        st.session_state['results'] = results
        st.session_state['selected'] = [r['symbol'] for r in results]
        st.success(f"✅ فحصت {len(STOCKS_150)} سهم - لقيت {len(results)} توصية")

# ============================================================
# 5. عرض التوصيات + الإرسال المفتوح حسب التحديد
# ============================================================
if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل 10 توصيات - حدد اللي تبي ترسله")

    all_symbols = [r['symbol'] for r in st.session_state['results']]
    selected = st.multiselect(
        "✅ حدد الأسهم اللي تبي ترسلها - اللي تختاره بس هو اللي بينرسل",
        options=all_symbols,
        default=st.session_state.get('selected', all_symbols),
        key="selected_multiselect"
    )
    st.session_state['selected'] = selected
    st.write(f"المحدد حاليا: **{len(selected)}** توصية: {', '.join(selected) if selected else 'ما حددت شي'}")

    # زر إرسال المحدد - يفتح الواتساب وتختار أي شخص
    if selected:
        combined = "\n\n------------------------\n\n".join([make_msg(r) for r in st.session_state['results'] if r['symbol'] in selected])
        link = whatsapp_share_link(combined)
        st.link_button(f"📤 أرسل المحدد ({len(selected)}) واتساب - اختر أي شخص من جهات اتصالك", link, use_container_width=True, type="primary")
        st.caption("بيفتح لك الواتساب، وانت تختار أي شخص: ترسلها لي، أو لأي شخص ثاني، أو لقروب، أو لنفسك.")

    st.divider()

    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        is_selected = r['symbol'] in selected
        tick = "✅ محدد للإرسال" if is_selected else "⬜ غير محدد"
        msg = make_msg(r)
        link = whatsapp_share_link(msg)
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']} - {tick}")
            st.write(f"السعر: {r['last']:.2f} ({r['change']:+.2f}%) | حجم: {r['volume']} | الانتهاء: {r['expiry']}")
            st.write(f"نطاق البريميوم: {r['prem_range']} | {r['reason']}")
            st.code(msg, language="text")
            # زر مفتوح - يفتح الواتساب وتختار أي شخص
            st.link_button(f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", link, use_container_width=True)
            st.divider()
