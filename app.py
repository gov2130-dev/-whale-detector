# ============================================================
# حيتان ابو راكان - V20 - قراءة صناع السوق من البيانات
# الفكرة: ما نحط شروط على مزاجنا
# نحسب: Max Pain + Gamma Exposure + Put/Call OI + Volume Profile
# وبعدين السوق نفسه هو اللي يقول وين صانع السوق، ونتبعه
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

# ===== 1. قراءة صناع السوق: Max Pain =====
def calc_max_pain(calls, puts, last):
    """السعر اللي صانع السوق يبي يوصله عشان أكبر عدد عقود تنتهي بدون قيمة"""
    try:
        strikes = sorted(set(calls['strike'].tolist()) | set(puts['strike'].tolist()))
        best_strike = last
        min_pain = float('inf')
        for s in strikes:
            # خسارة الكول إذا السعر = s
            call_pain = ((s - calls['strike']).clip(lower=0) * calls['openInterest']).sum()
            # خسارة البوت إذا السعر = s
            put_pain = ((puts['strike'] - s).clip(lower=0) * puts['openInterest']).sum()
            total = call_pain + put_pain
            if total < min_pain:
                min_pain = total
                best_strike = s
        return float(best_strike)
    except:
        return last

# ===== 2. قراءة صناع السوق: Gamma Exposure =====
def calc_gex(calls, puts, last):
    """وين أكبر تجمع جاما؟ هذا هو المغناطيس اللي صانع السوق يدافع عنه"""
    try:
        # جاما تقريبية من الدلتا والسترايك - بدون بلاك شولز معقد
        # نستخدم openInterest * gamma التقريبي
        # إذا ما فيه gamma في البيانات، نحسبها من IV والوقت
        gex_by_strike = {}
        for df, sign in [(calls, 1), (puts, -1)]:
            for _, row in df.iterrows():
                try:
                    strike = float(row['strike'])
                    oi = float(row['openInterest']) if pd.notna(row['openInterest']) else 0
                    iv = float(row['impliedVolatility']) if pd.notna(row['impliedVolatility']) else 0.3
                    gamma = row['gamma'] if 'gamma' in row and pd.notna(row['gamma']) else None
                    if gamma is None:
                        # تقدير جاما من IV - كل ما IV أعلى، الجاما أقل
                        # هذه معادلة تقريبية، مو رقم على مزاجنا، بل من سلوك الأوبشن نفسه
                        if iv <= 0:
                            iv = 0.3
                        gamma = 0.02 / (iv * 10)  # تقريب يعتمد على بيانات السوق نفسها
                    gex = sign * gamma * oi * 100 * last
                    gex_by_strike[strike] = gex_by_strike.get(strike, 0) + gex
                except:
                    continue
        if not gex_by_strike:
            return last, 0, 0
        # أكبر سترايك من ناحية الجاما المطلقة = جدار الجاما
        gamma_wall = max(gex_by_strike, key=lambda k: abs(gex_by_strike[k]))
        total_gex = sum(gex_by_strike.values())
        # Gamma Flip: السعر اللي ينقلب عنده سلوك صانع السوق
        # إذا السعر فوق الجدار، صانع السوق يشتري النزول. إذا تحته، يبيع الصعود
        return float(gamma_wall), float(total_gex), gex_by_strike.get(gamma_wall, 0)
    except:
        return last, 0, 0

# ===== 3. قراءة سلوك السعر: Volume Profile =====
def calc_volume_profile(hist):
    """وين تداولت أكبر كمية؟ هذا هو السعر العادل اللي السوق نفسه اختاره"""
    try:
        # نقسم السعر لـ 20 منطقة، ونشوف وين أكبر فوليوم
        prices = hist['Close'].values
        vols = hist['Volume'].values
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
        return float(hist['Close'].iloc[-1])

def get_whale(symbol):
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

        # ===== قراءة صناع السوق من البيانات نفسها، بدون شروط مزاجية =====
        max_pain = calc_max_pain(calls, puts, last)
        gamma_wall, total_gex, wall_gex = calc_gex(calls, puts, last)
        poc = calc_volume_profile(hist_long)

        # Put/Call OI - قراءة تمركز صناع السوق
        call_oi = calls['openInterest'].fillna(0).sum()
        put_oi = puts['openInterest'].fillna(0).sum()
        pcr_oi = put_oi / call_oi if call_oi > 0 else 1
        call_vol = calls['volume'].fillna(0).sum()
        put_vol = puts['volume'].fillna(0).sum()
        pcr_vol = put_vol / call_vol if call_vol > 0 else 1

        # ===== القرار يجي من البيانات، مو منا =====
        # نعطي كل إشارة وزن حسب قوتها في البيانات نفسها
        # ما نقول "إذا RSI > 50"، نقول "وين السعر بالنسبة للمكان اللي صانع السوق يدافع عنه؟"
        score = 0
        reasons = []

        # 1. السعر مقابل Max Pain - صانع السوق يسحب السعر له
        if last > max_pain:
            score -= 1.5
            reasons.append(f"السعر فوق Max Pain ${max_pain:.0f} -> صانع السوق يضغطه تحت")
        else:
            score += 1.5
            reasons.append(f"السعر تحت Max Pain ${max_pain:.0f} -> صانع السوق يسحبه فوق")

        # 2. السعر مقابل جدار الجاما - سلوك صانع السوق ينقلب هنا
        if last > gamma_wall:
            score += 1.0
            reasons.append(f"السعر فوق جدار جاما ${gamma_wall:.0f} -> صانع السوق يشتري النزول")
        else:
            score -= 1.0
            reasons.append(f"السعر تحت جدار جاما ${gamma_wall:.0f} -> صانع السوق يبيع الصعود")

        # 3. السعر مقابل POC - السلوك الحقيقي للسعر
        if last > poc:
            score += 1.0
            reasons.append(f"السعر فوق POC ${poc:.0f} -> السلوك صاعد")
        else:
            score -= 1.0
            reasons.append(f"السعر تحت POC ${poc:.0f} -> السلوك هابط")

        # 4. GEX الكلي - هل السوق في وضع استقرار ولا انفجار؟
        # إذا GEX موجب كبير، السوق مستقر. إذا سالب، السوق قابل للانفجار
        if total_gex > 0:
            score += 0.5
        else:
            score -= 0.5

        # 5. Put/Call Volume - وين الفلوس داخلة الحين؟ مو وين كانت
        if pcr_vol > 1.2:
            score -= 1.0
            reasons.append(f"فوليوم البوت أعلى {pcr_vol:.2f}x -> فلوس داخلة بوت")
        elif pcr_vol < 0.8:
            score += 1.0
            reasons.append(f"فوليوم الكول أعلى {1/pcr_vol:.2f}x -> فلوس داخلة كول")

        # إذا السكور قريب من صفر، معناه البيانات متضاربة، صانع السوق ما له اتجاه واضح
        # نترك السهم، ما نعطي توصية شكلية
        if abs(score) < 1.5:
            return None

        direction = "CALL" if score > 0 else "PUT"
        df = calls if direction == "CALL" else puts

        # ===== اختيار العقد: نختار العقد اللي صانع السوق متواجد فيه فعلا =====
        # مو أعلى فوليوم بس، بل العقد اللي عنده أكبر OI قريب من السعر
        # لأن صانع السوق يكون متواجد في العقود اللي عليها أكبر OI
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
                ask = float(row['ask']) if pd.notna(row['ask']) else 0
                if abs(strike - last) / last > 0.015:
                    continue
                if not (min_prem <= entry <= max_prem):
                    continue
                if vol < 500 or oi < 500:
                    continue
                # قوة العقد = OI * Volume - هذا يبين وين صانع السوق متواجد فعلا
                # مو فوليوم لحاله، لأن الفوليوم ممكن يكون تصفية
                strength = oi * vol
                candidates.append({"strike": strike, "entry": entry, "volume": int(vol), "oi": int(oi),
                                   "bid": bid, "ask": ask, "strength": strength, "type": direction})
            except:
                continue
        if not candidates:
            return None

        candidates = sorted(candidates, key=lambda x: x['strength'], reverse=True)
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
                "days_left": days_left, "max_pain": max_pain, "gamma_wall": gamma_wall,
                "poc": poc, "pcr_vol": round(pcr_vol, 2), "score": round(score, 1),
                "oi": whale['oi'], "reasons": reasons,
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
    with st.spinner(f"جار قراءة صناع السوق في {len(STOCKS_150)} سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        results = sorted(results, key=lambda x: abs(x['score']), reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ لقيت {len(results)} توصية - كلها مبنية على قراءة صناع السوق، مو على شروط مزاجية")

if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل وأقوى 10 توصيات - قراءة صناع السوق")
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
            st.write(f"📊 صانع السوق: Max Pain ${r['max_pain']:.0f} | جدار جاما ${r['gamma_wall']:.0f} | POC ${r['poc']:.0f} | P/C Vol {r['pcr_vol']} | قوة الإشارة {r['score']}")
            st.write(f"Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)")
            with st.expander("🔍 ليش اخترنا هالاتجاه؟ قراءة البيانات"):
                for reason in r['reasons']:
                    st.write(f"- {reason}")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
