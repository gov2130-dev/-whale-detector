# ============================================================
# راصد الحيتان - V13 - الكود الكامل بعد التعديل
# التعديل: رجعنا تاريخ الانتهاء في زر الجميع - كان ناقص
# زر الجميع: مختصر + مع التاريخ - زر كل واحدة: مفصل + مع التاريخ
# الإرسال: مفتوح، يفتح الواتساب وتختار أي شخص
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")
st.success("✅ زرين شغالين: زر الجميع فوق مع التاريخ، وزر كل توصية لحالها تحت.")

def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح | {ny_now.strftime('%H:%M')} نيويورك")
else:
    st.warning(f"🔴 السوق مسكر | {ny_now.strftime('%H:%M')} نيويورك")

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
        MAX_DISTANCE = 0.015
        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            df['dist'] = abs(df['strike'] - last) / last
            f = df[(df['lastPrice'] >= min_prem) & (df['lastPrice'] <= max_prem) &
                   (df['volume'].fillna(0) > 500) & (df['dist'] <= MAX_DISTANCE)]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]
        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')
        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        if change >= 0:
            whale = best_call if best_call is not None else best_put
        else:
            whale = best_put if best_put is not None else best_call
        if whale is None:
            return None
        strike = float(whale['strike'])
        if abs(strike - last) / last > 0.015:
            return None
        entry = float(whale['lastPrice'])
        volume = int(whale['volume'])
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]
        return {"symbol": symbol, "type": whale['type'], "strike": strike, "expiry": expiry,
                "entry": entry, "stop": stop, "targets": targets, "volume": volume,
                "last": last, "change": change,
                "prem_range": f"{min_prem:.2f} - {max_prem:.2f}",
                "dist": f"{abs(strike-last)/last*100:.2f}%"}
    except Exception:
        return None

def make_msg(r):
    emoji = "🟢" if r['type'] == 'CALL' else "🔴"
    return f"""🔍 راصد الحيتان
{r['symbol']} {emoji} {r['type']} {r['strike']:.1f}
الانتهاء: {r['expiry']}
دخول: {r['entry']} | وقف: {r['stop']} | حجم: {r['volume']}
أهداف: {' | '.join(map(str, r['targets']))}
📌 للمتابعة فقط، ليست توصية بيع أو شراء"""

# ===== التعديل V13 هنا - رجعنا التاريخ في زر الجميع =====
def make_compact_all(results, selected):
    lines = ["🔍 راصد الحيتان - أفضل 10"]
    for r in results:
        if r['symbol'] in selected:
            emoji = "🟢" if r['type'] == 'CALL' else "🔴"
            # نختصر التاريخ: 2026-11-13 -> 11-13 عشان الرابط يبقى قصير
            expiry_short = r['expiry'][5:] if len(r['expiry']) >= 10 else r['expiry']
            lines.append(f"{r['symbol']} {emoji} {r['type']} {r['strike']:.0f} انتهاء {expiry_short} دخول {r['entry']} وقف {r['stop']} أهداف {' | '.join(map(str, r['targets'][:3]))}")
    lines.append("📌 للمتابعة فقط")
    return "\n".join(lines)

def whatsapp_button(msg, label, bg="#25D366"):
    encoded = urllib.parse.quote(msg)
    url = f"https://api.whatsapp.com/send?text={encoded}"
    st.markdown(
        f"""<a href="{url}" target="_blank" style="display:block; text-align:center; background-color:{bg}; color:white; padding:14px 20px; border-radius:12px; text-decoration:none; font-weight:bold; font-size:18px; margin:10px 0;">{label}</a>""",
        unsafe_allow_html=True
    )

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
        st.success(f"✅ لقيت {len(results)} توصية")

if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل 10 توصيات")

    all_symbols = [r['symbol'] for r in st.session_state['results']]
    selected = st.multiselect(
        "✅ حدد الأسهم اللي تبي ترسلها - اللي تختاره بس هو اللي بينرسل في زر الجميع",
        options=all_symbols,
        default=st.session_state.get('selected', all_symbols),
        key="selected_multiselect"
    )
    st.session_state['selected'] = selected
    st.write(f"المحدد حاليا: **{len(selected)}** توصية")

    # ===== زر إرسال الجميع - مع التاريخ الحين =====
    if selected:
        compact_msg = make_compact_all(st.session_state['results'], selected)
        st.caption(f"زر الجميع بيرسل نسخة مختصرة مع تاريخ الانتهاء. الطول: {len(compact_msg)} حرف.")
        whatsapp_button(compact_msg, f"📤 أرسل الجميع ({len(selected)}) واتساب - اختر أي شخص", bg="#1E88E5")
        st.code(compact_msg, language="text")

    st.divider()
    st.subheader("📤 أو أرسل كل واحدة لحالها - رسالة كاملة مفصلة")

    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        msg = make_msg(r)
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']}")
            st.write(f"السعر: {r['last']:.2f} ({r['change']:+.2f}%) | حجم: {r['volume']} | الانتهاء: {r['expiry']} | بعد السترايك: {r['dist']}")
            st.code(msg, language="text")
            whatsapp_button(msg, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
