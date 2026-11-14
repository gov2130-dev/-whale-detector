# ============================================================
# حيتان ابو راكان - V17 - النسخة النهائية
# التعديل: إضافة تاريخ ووقت البحث أعلى رسالة الواتساب
# التاريخ يثبت لحظة الفحص، مو لحظة الإرسال
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date
import pytz

st.set_page_config(page_title="حيتان ابو راكان", layout="wide")
st.title("🔍 حيتان ابو راكان")

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
        try:
            raw_bid = float(whale['bid']) if pd.notna(whale['bid']) and float(whale['bid']) > 0 else round(entry * 0.95, 2)
        except:
            raw_bid = round(entry * 0.95, 2)
        bid = min(raw_bid, round(entry * 0.95, 2))
        volume = int(whale['volume'])
        stop = round(entry * 0.5, 2)
        t1 = round(entry * 1.5, 2)
        t2 = round(entry * 2.3, 2)
        t3 = round(entry * 3.2, 2)
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

def make_msg(r):
    emoji = "🔴" if r['type'] == 'PUT' else "🟢"
    strike_str = f"{r['strike']:.0f}" if r['strike'] == int(r['strike']) else f"{r['strike']:.1f}"
    return f"""{emoji} {r['symbol']} {strike_str} {r['type']} 🐋
Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f}
Entry: ${r['entry']} Bid: ${r['bid']}
Stop: ${r['stop']}
Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)"""

# ===== V17: نجيب وقت البحث المحفوظ ونحطه أعلى الرسالة =====
def get_search_time_text():
    # إذا فيه وقت فحص محفوظ، نستخدمه. إذا ما فيه، نستخدم الحين
    search_time = st.session_state.get('search_time', None)
    if search_time is None:
        ny = pytz.timezone("America/New_York")
        search_time = datetime.now(ny)
    # الصيغة: 📅 بحث: 2026-11-14 | ⏰ 16:05 نيويورك
    return f"📅 بحث: {search_time.strftime('%Y-%m-%d')} | ⏰ {search_time.strftime('%H:%M')} نيويورك"

def make_all_msg(results, selected):
    header = get_search_time_text()
    blocks = [header, "حيتان ابو راكان:"]
    for r in results:
        if r['symbol'] in selected:
            blocks.append(make_msg(r))
    return "\n\n".join(blocks)

def make_single_msg(r):
    header = get_search_time_text()
    return f"{header}\n\nحيتان ابو راكان:\n{make_msg(r)}"

def whatsapp_button(msg, label, bg="#25D366"):
    encoded = urllib.parse.quote(msg)
    url = f"https://api.whatsapp.com/send?text={encoded}"
    st.markdown(
        f"""<a href="{url}" target="_blank" style="display:block; text-align:center; background-color:{bg}; color:white; padding:14px 20px; border-radius:12px; text-decoration:none; font-weight:bold; font-size:18px; margin:10px 0;">{label}</a>""",
        unsafe_allow_html=True
    )

if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    # ===== V17: نسجل وقت البحث هنا، لحظة الضغط على الفحص =====
    ny = pytz.timezone("America/New_York")
    st.session_state['search_time'] = datetime.now(ny)
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
    st.subheader("🏆 أفضل وأقوى 10 توصيات")
    # نعرض وقت البحث في التطبيق بعد، عشان تعرف متى فحصت
    if 'search_time' in st.session_state:
        st.caption(f"{get_search_time_text()}")

    all_symbols = [r['symbol'] for r in st.session_state['results']]
    selected = st.multiselect(
        "✅ حدد الأسهم اللي تبي ترسلها في زر الجميع",
        options=all_symbols,
        default=st.session_state.get('selected', all_symbols),
        key="selected_multiselect"
    )
    st.session_state['selected'] = selected

    if selected:
        all_msg = make_all_msg(st.session_state['results'], selected)
        whatsapp_button(all_msg, f"📤 أرسل الجميع ({len(selected)}) واتساب - اختر أي شخص", bg="#1E88E5")

    st.divider()

    for idx, r in enumerate(st.session_state['results'], start=1):
        emoji = "🔴" if r['type'] == 'PUT' else "🟢"
        single = make_single_msg(r)
        with st.container():
            st.markdown(f"### {idx}. {emoji} {r['symbol']} {r['strike']:.0f} {r['type']} 🐋")
            st.write(f"Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f} | Entry: ${r['entry']} Bid: ${r['bid']} | Stop: ${r['stop']} | حجم: {r['volume']}")
            st.write(f"Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
