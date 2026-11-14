# ============================================================
# راصد الحيتان - V14 - بصيغة حيتان ابو راكان
# الصيغة الجديدة:
# حيتان ابو راكان:
# 🔴 QQQ 708 PUT 🐋
# Exp: 2026-09-01 (0d) Stock: $707.64
# Entry: $0.4 Bid: $0.38
# Stop: $0.2
# Target: $0.6 (+50%) | $0.92 (+130%) | $1.28 (+220%)
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 حيتان ابو راكان")
st.success("✅ بصيغة حيتان ابو راكان - زر الجميع + زر كل واحدة، الاثنين يفتحون الواتساب وتختار أي شخص.")

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

        # ===== بيانات بصيغة ابو راكان =====
        entry = float(whale['lastPrice'])
        # Bid: ناخذه من العقد نفسه، إذا ما كان موجود نحسبه 95% من الدخول
        try:
            bid = float(whale['bid']) if pd.notna(whale['bid']) and float(whale['bid']) > 0 else round(entry * 0.95, 2)
        except:
            bid = round(entry * 0.95, 2)
        volume = int(whale['volume'])
        # Stop: 50% من الدخول، مثل مثالك: دخول 0.4 وقف 0.2، دخول 1.8 وقف 0.9
        stop = round(entry * 0.5, 2)
        # Targets: +50% و +130% و +220% مثل مثالك بالضبط
        t1 = round(entry * 1.5, 2)   # +50%
        t2 = round(entry * 2.3, 2)   # +130%
        t3 = round(entry * 3.2, 2)   # +220%
        # الأيام المتبقية للانتهاء: (0d) (1d)
        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_left = (exp_date - date.today()).days
            if days_left < 0:
                days_left = 0
        except:
            days_left = 0

        return {"symbol": symbol, "type": whale['type'], "strike": strike, "expiry": expiry,
                "entry": entry, "bid": bid, "stop": stop,
                "t1": t1, "t2": t2, "t3": t3,
                "volume": volume, "last": last, "change": change,
                "days_left": days_left,
                "dist": f"{abs(strike-last)/last*100:.2f}%"}
    except Exception:
        return None

# ===== الصيغة الجديدة - مثل حيتان ابو راكان بالضبط =====
def make_msg(r):
    emoji = "🔴" if r['type'] == 'PUT' else "🟢"
    # نعرض السترايك بدون .0 إذا كان صحيح: 708 مو 708.0
    strike_str = f"{r['strike']:.0f}" if r['strike'] == int(r['strike']) else f"{r['strike']:.1f}"
    return f"""{emoji} {r['symbol']} {strike_str} {r['type']} 🐋
Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f}
Entry: ${r['entry']} Bid: ${r['bid']}
Stop: ${r['stop']}
Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)"""

def make_all_msg(results, selected):
    # زر الجميع: نفس الصيغة، بس كل التوصيات تحت بعض
    blocks = ["حيتان ابو راكان:"]
    for r in results:
        if r['symbol'] in selected:
            blocks.append(make_msg(r))
    return "\n\n".join(blocks)

def make_single_msg(r):
    # زر كل واحدة: نفس الصيغة + عنوان
    return f"حيتان ابو راكان:\n{make_msg(r)}"

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
    st.subheader("🏆 أفضل 10 توصيات - بصيغة حيتان ابو راكان")

    all_symbols = [r['symbol'] for r in st.session_state['results']]
    selected = st.multiselect(
        "✅ حدد الأسهم اللي تبي ترسلها",
        options=all_symbols,
        default=st.session_state.get('selected', all_symbols),
        key="selected_multiselect"
    )
    st.session_state['selected'] = selected
    st.write(f"المحدد حاليا: **{len(selected)}** توصية")

    # ===== زر إرسال الجميع - بنفس الصيغة =====
    if selected:
        all_msg = make_all_msg(st.session_state['results'], selected)
        whatsapp_button(all_msg, f"📤 أرسل الجميع ({len(selected)}) واتساب - اختر أي شخص", bg="#1E88E5")
        st.code(all_msg, language="text")

    st.divider()
    st.subheader("📤 أو أرسل كل واحدة لحالها")

    for r in st.session_state['results']:
        emoji = "🔴" if r['type'] == 'PUT' else "🟢"
        single = make_single_msg(r)
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} {r['strike']:.0f} {r['type']} 🐋")
            st.write(f"Stock: ${r['last']:.2f} | Exp: {r['expiry']} ({r['days_left']}d) | حجم: {r['volume']} | بعد السترايك: {r['dist']}")
            st.code(single, language="text")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
