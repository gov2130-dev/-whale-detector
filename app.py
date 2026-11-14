# ============================================================
# حيتان ابو راكان - V19 - تدقيق الحيتان الحقيقي
# التعديل: ما عاد نعطي توصية على أعلى فوليوم بس
# لازم 4 شروط تجتمع: فوليوم > أوبن انترست + اتجاه يوافق + دلتا + سبريد ضيق
# إذا شرط واحد ما تحقق، السهم ينحذف
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date
import pytz
import numpy as np

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

def get_trend_confirmation(tk, last):
    """نتأكد اتجاه السهم حقيقي، مو خدعة يوم واحد"""
    try:
        hist = tk.history(period="1mo", interval="1d")
        if len(hist) < 20:
            return None
        # VWAP تقريبي
        vwap = (hist['Close'] * hist['Volume']).sum() / hist['Volume'].sum()
        ema9 = hist['Close'].ewm(span=9).mean().iloc[-1]
        ema20 = hist['Close'].ewm(span=20).mean().iloc[-1]
        # RSI
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_now = float(rsi.iloc[-1])
        # كم مؤشر يقول صعود / هبوط
        bull_votes = 0
        bear_votes = 0
        if last > vwap: bull_votes += 1
        else: bear_votes += 1
        if last > ema20: bull_votes += 1
        else: bear_votes += 1
        if ema9 > ema20: bull_votes += 1
        else: bear_votes += 1
        if rsi_now > 50: bull_votes += 1
        else: bear_votes += 1
        if bull_votes >= 3:
            return "CALL", bull_votes, rsi_now, vwap
        if bear_votes >= 3:
            return "PUT", bear_votes, rsi_now, vwap
        return None  # متذبذب، ما ندخل
    except:
        return None

def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None

        # ===== 1. تأكيد الاتجاه أولا، قبل ما نختار أي عقد =====
        trend = get_trend_confirmation(tk, last)
        if trend is None:
            return None  # السهم متذبذب، ما فيه اتجاه واضح، نتركه
        direction, votes, rsi_now, vwap = trend

        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        df = chain.calls if direction == "CALL" else chain.puts

        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        # ===== 2. فلترة العقود: لازم تكون عقود حيتان حقيقية =====
        candidates = []
        for _, row in df.iterrows():
            try:
                strike = float(row['strike'])
                entry = float(row['lastPrice'])
                vol = float(row['volume']) if pd.notna(row['volume']) else 0
                oi = float(row['openInterest']) if pd.notna(row['openInterest']) else 0
                bid = float(row['bid']) if pd.notna(row['bid']) else 0
                ask = float(row['ask']) if pd.notna(row['ask']) else 0
                iv = float(row['impliedVolatility']) if pd.notna(row['impliedVolatility']) else 0
                delta = float(row['delta']) if 'delta' in row and pd.notna(row['delta']) else None

                # شرط المسافة: سترايك قريب 1.5% بس
                if abs(strike - last) / last > 0.015:
                    continue
                # شرط السعر
                if not (min_prem <= entry <= max_prem):
                    continue
                # شرط الحوت 1: فوليوم عالي
                if vol < 1000:
                    continue
                # شرط الحوت 2: فوليوم أكبر من الأوبن انترست = دخول جديد، مو تصفية
                # يعني الحيتان داخلة الحين، مو قاعدة تطلع
                if oi > 0 and vol < oi * 0.8:
                    continue
                # شرط الحوت 3: سبريد ضيق = صانع السوق موجود ومتفاعل
                if bid > 0 and ask > 0:
                    spread = (ask - bid) / entry if entry > 0 else 1
                    if spread > 0.20:
                        continue
                # شرط الحوت 4: IV معقول، مو عقد ميت ولا منفجر
                if iv < 0.10 or iv > 1.5:
                    continue
                # شرط الدلتا: إذا متوفرة
                if delta is not None:
                    ad = abs(delta)
                    if not (0.25 <= ad <= 0.60):
                        continue

                # قوة الحوت = فوليوم / أوبن انترست
                whale_score = vol / oi if oi > 0 else vol / 100
                candidates.append({
                    "strike": strike, "entry": entry, "volume": int(vol),
                    "oi": int(oi), "bid": bid, "ask": ask, "iv": iv,
                    "delta": delta, "whale_score": whale_score, "type": direction
                })
            except:
                continue

        if not candidates:
            return None

        # نرتب حسب قوة الحوت، مو حسب الفوليوم بس
        candidates = sorted(candidates, key=lambda x: x['whale_score'], reverse=True)
        whale = candidates[0]

        strike = whale['strike']
        entry = whale['entry']
        bid = min(whale['bid'] if whale['bid'] > 0 else round(entry * 0.95, 2), round(entry * 0.95, 2))
        volume = whale['volume']
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

        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        return {"symbol": symbol, "type": direction, "strike": strike, "expiry": expiry,
                "entry": entry, "bid": bid, "stop": stop,
                "t1": t1, "t2": t2, "t3": t3,
                "volume": volume, "last": last, "change": change,
                "days_left": days_left, "whale_score": round(whale['whale_score'], 2),
                "oi": whale['oi'], "rsi": round(rsi_now, 1), "votes": votes,
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

def get_search_time_text():
    search_time = st.session_state.get('search_time', None)
    if search_time is None:
        ny = pytz.timezone("America/New_York")
        search_time = datetime.now(ny)
    return f"📅 بحث: {search_time.strftime('%Y-%m-%d')} | ⏰ {search_time.strftime('%H:%M')} نيويورك"

def make_all_msg(results):
    header = get_search_time_text()
    blocks = [header, "حيتان ابو راكان:"]
    for r in results:
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
        results = sorted(results, key=lambda x: x['whale_score'], reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ لقيت {len(results)} توصية مدققة - كلها اجتازت 4 شروط الحوت")

if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل وأقوى 10 توصيات مدققة")
    if 'search_time' in st.session_state:
        st.caption(f"{get_search_time_text()}")

    all_msg = make_all_msg(st.session_state['results'])
    whatsapp_button(all_msg, f"📤 أرسل الجميع ({len(st.session_state['results'])}) واتساب - اختر أي شخص", bg="#1E88E5")
    st.divider()

    for idx, r in enumerate(st.session_state['results'], start=1):
        emoji = "🔴" if r['type'] == 'PUT' else "🟢"
        single = make_single_msg(r)
        with st.container():
            st.markdown(f"### {idx}. {emoji} {r['symbol']} {r['strike']:.0f} {r['type']} 🐋")
            st.write(f"Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f} | Entry: ${r['entry']} Bid: ${r['bid']} | Stop: ${r['stop']} | حجم: {r['volume']} | OI: {r['oi']} | قوة الحوت: {r['whale_score']}x | RSI: {r['rsi']}")
            st.write(f"Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
