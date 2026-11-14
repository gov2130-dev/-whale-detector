# ============================================================
# حيتان ابو راكان - V24 - ترتيب بالبيانات وناخذ 10 فقط
# الفكرة: ما نحذف أحد بشرط على مزاجنا
# نحسب لكل سهم: كم إشارة من البيانات تتفق على نفس الاتجاه؟
# ونرتب 150 سهم حسب قوة الاتفاق، وناخذ أقوى 10 بس
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date
import pytz
import numpy as np

st.set_page_config(page_title="حيتان ابو راكان", layout="wide")
st.title("🔍 حيتان ابو راكان - أقوى 10 من البيانات")

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

def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, f"السوق مسكر - اليوم {now.strftime('%A')} - البيانات من إغلاق الجمعة للمراجعة فقط"
    open_time = now.replace(hour=9, minute=30, second=0)
    close_time = now.replace(hour=16, minute=0, second=0)
    if open_time <= now <= close_time:
        return True, f"السوق مفتوح - {now.strftime('%H:%M')} نيويورك"
    return False, f"السوق مسكر الآن - {now.strftime('%H:%M')} نيويورك"

def calc_max_pain(calls, puts):
    try:
        strikes = sorted(set(calls['strike'].tolist()) | set(puts['strike'].tolist()))
        best = None
        min_pain = float('inf')
        for s in strikes:
            call_pain = ((s - calls['strike']).clip(lower=0) * calls['openInterest']).sum()
            put_pain = ((puts['strike'] - s).clip(lower=0) * puts['openInterest']).sum()
            total = call_pain + put_pain
            if total < min_pain:
                min_pain = total
                best = s
        return float(best) if best is not None else None
    except:
        return None

def calc_gex_wall(calls, puts, last):
    try:
        gex_by_strike = {}
        for df, sign in [(calls, 1), (puts, -1)]:
            for _, row in df.iterrows():
                try:
                    strike = float(row['strike'])
                    oi = float(row['openInterest']) if pd.notna(row['openInterest']) else 0
                    gamma = row['gamma'] if 'gamma' in row and pd.notna(row['gamma']) else None
                    if gamma is None:
                        iv = float(row['impliedVolatility']) if pd.notna(row['impliedVolatility']) else 0.3
                        if iv <= 0:
                            iv = 0.3
                        gamma = 0.02 / (iv * 10)
                    gex = sign * gamma * oi * 100 * last
                    gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex
                except:
                    continue
        if not gex_by_strike:
            return None, 0
        wall = max(gex_by_strike, key=lambda k: abs(gex_by_strike[k]))
        total = sum(gex_by_strike.values())
        return float(wall), float(total)
    except:
        return None, 0

def calc_poc(hist_long):
    try:
        prices = hist_long['Close'].values
        vols = hist_long['Volume'].values
        lo, hi = prices.min(), prices.max()
        if hi == lo:
            return float(prices[-1])
        bins = np.linspace(lo, hi, 20)
        idx = np.digitize(prices, bins)
        vol_by_bin = {}
        for i, v in zip(idx, vols):
            vol_by_bin[i] = vol_by_bin.get(i, 0) + v
        poc_bin = max(vol_by_bin, key=lambda k: vol_by_bin[k])
        poc = (bins[min(poc_bin, len(bins)-1)] + bins[max(poc_bin-1, 0)]) / 2
        return float(poc)
    except:
        return None

def get_leaders_chg():
    # القائد SPX و NDX - وإذا ما قدرنا نقراهم، نستخدم SPY و QQQ كبديل، عشان ما يطلع None مثل صورتك
    out = {}
    for sym, name, fallback in [("^GSPC","SPX","SPY"), ("^NDX","NDX","QQQ")]:
        try:
            tk = yf.Ticker(sym)
            h = tk.history(period="1mo", interval="1d")
            if h.empty or len(h) < 6:
                raise Exception("empty")
            chg_5d = float((h['Close'].iloc[-1] - h['Close'].iloc[-6]) / h['Close'].iloc[-6] * 100)
            out[name] = chg_5d
        except:
            try:
                tk2 = yf.Ticker(fallback)
                h2 = tk2.history(period="1mo", interval="1d")
                out[name] = float((h2['Close'].iloc[-1] - h2['Close'].iloc[-6]) / h2['Close'].iloc[-6] * 100)
            except:
                out[name] = 0.0
    return out

def get_stock_data(symbol, leaders):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None
        hist_long = tk.history(period="1mo")
        if hist_long.empty:
            return None
        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        calls, puts = chain.calls, chain.puts
        if calls.empty or puts.empty:
            return None

        max_pain = calc_max_pain(calls, puts)
        gamma_wall, total_gex = calc_gex_wall(calls, puts, last)
        poc = calc_poc(hist_long)
        call_oi = calls['openInterest'].fillna(0).sum()
        put_oi = puts['openInterest'].fillna(0).sum()
        pcr_oi = put_oi / call_oi if call_oi > 0 else 1
        call_vol = calls['volume'].fillna(0).sum()
        put_vol = puts['volume'].fillna(0).sum()
        pcr_vol = put_vol / call_vol if call_vol > 0 else 1
        chg_1d = float((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100)
        chg_5d = float((hist_long['Close'].iloc[-1] - hist_long['Close'].iloc[-6]) / hist_long['Close'].iloc[-6] * 100)

        tech = symbol in ["NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL","AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX","PLTR","SNOW","CRWD","PANW","SHOP","SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","QQQ"]
        leader_name = "NDX" if tech else "SPX"
        leader_chg = leaders.get(leader_name, 0)
        rs = chg_5d - leader_chg

        # ===== هنا الترتيب بالبيانات: كم إشارة تتفق على نفس الاتجاه؟ =====
        # ما نحط شرط "لازم RS > 3"، نحسب كم إشارة تقول صعود وكم تقول هبوط
        # والإشارة الأقوى هي اللي تتفق عليها أغلب البيانات
        bull = 0
        bear = 0
        details = []
        # 1. السعر vs Max Pain - صانع السوق يسحب السعر له
        if max_pain is not None:
            if last > max_pain:
                bear += 1
                details.append(f"تحت Max Pain ${max_pain:.0f} -> ضغط هابط")
            elif last < max_pain:
                bull += 1
                details.append(f"فوق Max Pain ${max_pain:.0f} -> سحب صاعد")
        # 2. السعر vs جدار الجاما
        if gamma_wall is not None:
            if last > gamma_wall:
                bull += 1
                details.append(f"فوق جدار جاما ${gamma_wall:.0f}")
            elif last < gamma_wall:
                bear += 1
                details.append(f"تحت جدار جاما ${gamma_wall:.0f}")
        # 3. السعر vs POC
        if poc is not None:
            if last > poc:
                bull += 1
                details.append(f"فوق POC ${poc:.0f}")
            elif last < poc:
                bear += 1
                details.append(f"تحت POC ${poc:.0f}")
        # 4. القوة النسبية vs القائد
        if rs > 0:
            bull += 1
            details.append(f"أقوى من {leader_name} بـ {rs:+.2f}%")
        elif rs < 0:
            bear += 1
            details.append(f"أضعف من {leader_name} بـ {rs:+.2f}%")
        # 5. وين الفلوس داخلة؟ Put/Call Volume
        if pcr_vol > 1.1:
            bear += 1
            details.append(f"فلوس داخلة بوت P/C {pcr_vol:.2f}")
        elif pcr_vol < 0.9:
            bull += 1
            details.append(f"فلوس داخلة كول P/C {pcr_vol:.2f}")

        # الاتجاه = اللي تتفق عليه أغلب البيانات، مو شرط واحد
        if bull > bear:
            direction = "CALL"
            agreement = bull  # كم إشارة اتفقت
            total_signals = bull + bear
        elif bear > bull:
            direction = "PUT"
            agreement = bear
            total_signals = bull + bear
        else:
            return None  # البيانات متعادلة، ما نرتبها في الأقوى

        # قوة الترتيب = كم إشارة اتفقت + قوة القوة النسبية + قوة العقد
        # كلها من البيانات، مو شرط على مزاجنا
        # مثال: سهم 5 إشارات اتفقت عليه، أقوى من سهم 3 إشارات اتفقت عليه
        score = agreement * 10 + abs(rs) + abs(chg_5d) * 0.5

        # اختيار العقد: أكبر OI × Volume في اتجاه البيانات
        df = calls if direction == "CALL" else puts
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0
        candidates = []
        for _, row in df.iterrows():
            try:
                strike = float(row['strike'])
                entry = float(row['lastPrice'])
                vol = float(row['volume']) if pd.notna(row['volume']) else 0
                oi = float(row['openInterest']) if pd.notna(row['openInterest']) else 0
                bid = float(row['bid']) if pd.notna(row['bid']) else 0
                if abs(strike - last) / last > 0.015:
                    continue
                if not (min_prem <= entry <= max_prem):
                    continue
                if vol < 100 or oi < 100:
                    continue
                strength = oi * vol
                candidates.append({"strike": strike, "entry": entry, "volume": int(vol), "oi": int(oi), "bid": bid, "strength": strength})
            except:
                continue
        if not candidates:
            return None
        candidates = sorted(candidates, key=lambda x: x['strength'], reverse=True)
        whale = candidates[0]
        strike = whale['strike']
        entry = whale['entry']
        bid = min(whale['bid'] if whale['bid'] > 0 else round(entry * 0.95, 2), round(entry * 0.95, 2))
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
        return {"symbol": symbol, "type": direction, "strike": strike, "expiry": expiry,
                "entry": entry, "bid": bid, "stop": stop, "t1": t1, "t2": t2, "t3": t3,
                "volume": whale['volume'], "last": last, "change": chg_1d,
                "days_left": days_left, "max_pain": max_pain, "gamma_wall": gamma_wall,
                "poc": poc, "pcr_vol": round(pcr_vol, 2), "oi": whale['oi'],
                "rs": round(rs, 2), "leader_name": leader_name, "leader_chg": round(leader_chg, 2),
                "stock_chg": round(chg_5d, 2), "score": round(score, 1), "agreement": agreement,
                "total_signals": total_signals, "details": details}
    except:
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
    st.markdown(f"""<a href="{url}" target="_blank" style="display:block; text-align:center; background-color:{bg}; color:white; padding:14px 20px; border-radius:12px; text-decoration:none; font-weight:bold; font-size:18px; margin:10px 0;">{label}</a>""", unsafe_allow_html=True)

is_open, market_msg = is_market_open()
if is_open:
    st.success(f"🟢 {market_msg}")
else:
    st.warning(f"🔴 {market_msg}")

leaders = get_leaders_chg()
st.info(f"📊 القائد: SPX {leaders.get('SPX',0):+.2f}% (5 أيام) | NDX {leaders.get('NDX',0):+.2f}% (5 أيام) - SPY يتبع SPX، و QQQ يتبع NDX")

if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    ny = pytz.timezone("America/New_York")
    st.session_state['search_time'] = datetime.now(ny)
    with st.spinner("جار ترتيب 150 سهم حسب قوة البيانات..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_stock_data(sym, leaders)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        # ترتيب، مو فلترة: الأقوى أول، وناخذ 10 بس
        results = sorted(results, key=lambda x: x['score'], reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ رتبنا {len(results)} - أقوى 10 من البيانات")

if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أقوى 10 - مرتبة بالبيانات")
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
            st.write(f"Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f} | Entry: ${r['entry']} Bid: ${r['bid']} | Stop: ${r['stop']} | حجم: {r['volume']} | OI: {r['oi']}")
            st.write(f"📊 قوة الاتفاق: {r['agreement']}/{r['total_signals']} إشارات اتفقت | RS {r['rs']:+.2f}% vs {r['leader_name']} | Max Pain ${r['max_pain']:.0f} | جاما ${r['gamma_wall']:.0f} | POC ${r['poc']:.0f} | P/C Vol {r['pcr_vol']}")
            st.write(f"Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)")
            with st.expander("🔍 ليش هالسهم طلع في الأقوى 10؟"):
                for d in r['details']:
                    st.write(f"- {d}")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
