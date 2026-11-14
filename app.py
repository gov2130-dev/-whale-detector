# ============================================================
# حيتان ابو راكان - لوحة قراءة صناع السوق
# الفكرة: ما نعطي CALL / PUT
# نعرض البيانات الخام مثل ما هي، وانت اللي تقرر
# إذا السوق مسكر، التطبيق يقول السوق مسكر، ما يعطي توصيات وهمية
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date
import pytz
import numpy as np

st.set_page_config(page_title="حيتان ابو راكان - لوحة البيانات", layout="wide")
st.title("📊 حيتان ابو راكان - لوحة قراءة صناع السوق")

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

# ===== هل السوق مفتوح ولا مسكر؟ =====
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    # السبت والأحد السوق مسكر
    if now.weekday() >= 5:
        return False, f"السوق مسكر - اليوم {now.strftime('%A')} - البيانات من إغلاق الجمعة، لا تعتمد عليها"
    # السوق يفتح 9:30 ويقفل 16:00 بتوقيت نيويورك
    open_time = now.replace(hour=9, minute=30, second=0)
    close_time = now.replace(hour=16, minute=0, second=0)
    if open_time <= now <= close_time:
        return True, f"السوق مفتوح - {now.strftime('%H:%M')} نيويورك"
    return False, f"السوق مسكر الآن - {now.strftime('%H:%M')} نيويورك - السوق يفتح 9:30"

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
    """نقرأ SPX و NDX، هم القادة، مو SPY و QQQ"""
    out = {}
    for sym, name in [("^GSPC","SPX"), ("^NDX","NDX")]:
        try:
            tk = yf.Ticker(sym)
            h = tk.history(period="1mo", interval="1d")
            if h.empty:
                continue
            chg_5d = float((h['Close'].iloc[-1] - h['Close'].iloc[-6]) / h['Close'].iloc[-6] * 100)
            chg_1d = float((h['Close'].iloc[-1] - h['Close'].iloc[-2]) / h['Close'].iloc[-2] * 100)
            out[name] = {"chg_5d": chg_5d, "chg_1d": chg_1d, "last": float(h['Close'].iloc[-1])}
        except:
            continue
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

        # ===== بيانات خام، بدون شروط، بدون CALL / PUT =====
        max_pain = calc_max_pain(calls, puts)
        gamma_wall, total_gex = calc_gex_wall(calls, puts, last)
        poc = calc_poc(hist_long)

        call_oi = calls['openInterest'].fillna(0).sum()
        put_oi = puts['openInterest'].fillna(0).sum()
        pcr_oi = put_oi / call_oi if call_oi > 0 else None
        call_vol = calls['volume'].fillna(0).sum()
        put_vol = puts['volume'].fillna(0).sum()
        pcr_vol = put_vol / call_vol if call_vol > 0 else None

        # أداء السهم
        chg_1d = float((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2] * 100)
        chg_5d = float((hist_long['Close'].iloc[-1] - hist_long['Close'].iloc[-6]) / hist_long['Close'].iloc[-6] * 100)

        # القوة النسبية مقابل القائد الصح
        tech = symbol in ["NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL","AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX","PLTR","SNOW","CRWD","PANW","SHOP","SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","QQQ"]
        leader_name = "NDX" if tech else "SPX"
        leader_chg = leaders.get(leader_name, {}).get("chg_5d", 0)
        rs = chg_5d - leader_chg

        # وين السعر بالنسبة لمستويات صانع السوق؟ مجرد وصف، مو توصية
        # إذا السعر فوق Max Pain، نكتب "فوق Max Pain"، ما نقول CALL ولا PUT
        def pos_vs(level):
            if level is None:
                return "-"
            diff = (last - level) / level * 100
            if diff > 0.5:
                return f"فوق بـ {diff:.2f}%"
            elif diff < -0.5:
                return f"تحت بـ {abs(diff):.2f}%"
            else:
                return "عند المستوى"

        # أكبر عقد من ناحية OI × Volume - وين صانع السوق متواجد؟ مجرد معلومة
        # نعرض أكبر عقد كول وأكبر عقد بوت، بدون ما نختار واحد
        def top_contract(df):
            try:
                best = None
                best_score = -1
                for _, row in df.iterrows():
                    vol = float(row['volume']) if pd.notna(row['volume']) else 0
                    oi = float(row['openInterest']) if pd.notna(row['openInterest']) else 0
                    score = vol * oi
                    if score > best_score:
                        best_score = score
                        best = row
                if best is None:
                    return "-"
                strike = float(best['strike'])
                entry = float(best['lastPrice'])
                vol = int(float(best['volume'])) if pd.notna(best['volume']) else 0
                oi = int(float(best['openInterest'])) if pd.notna(best['openInterest']) else 0
                return f"{strike:.0f} @ ${entry:.2f} (V:{vol} OI:{oi})"
            except:
                return "-"

        top_call = top_contract(calls)
        top_put = top_contract(puts)

        try:
            exp_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            days_left = (exp_date - date.today()).days
            if days_left < 0:
                days_left = 0
        except:
            days_left = 0

        return {
            "symbol": symbol,
            "last": last,
            "chg_1d": chg_1d,
            "chg_5d": chg_5d,
            "expiry": expiry,
            "days_left": days_left,
            "max_pain": max_pain,
            "max_pain_pos": pos_vs(max_pain),
            "gamma_wall": gamma_wall,
            "gamma_pos": pos_vs(gamma_wall),
            "poc": poc,
            "poc_pos": pos_vs(poc),
            "pcr_oi": pcr_oi,
            "pcr_vol": pcr_vol,
            "rs": rs,
            "leader_name": leader_name,
            "leader_chg": leader_chg,
            "total_gex": total_gex,
            "top_call": top_call,
            "top_put": top_put,
        }
    except:
        return None

# ===== عرض حالة السوق =====
is_open, market_msg = is_market_open()
if is_open:
    st.success(f"🟢 {market_msg}")
else:
    st.warning(f"🔴 {market_msg} - اللوحة تعرض بيانات إغلاق الجمعة للمراجعة فقط، لا تدخل على أساسها")

leaders = get_leaders_chg()
if leaders:
    cols = st.columns(2)
    for i, (name, d) in enumerate(leaders.items()):
        with cols[i]:
            st.metric(f"القائد {name}", f"${d['last']:,.2f}", f"{d['chg_5d']:+.2f}% (5 أيام) | {d['chg_1d']:+.2f}% (يوم)")

st.caption("القائد هو SPX و NDX. SPY يتبع SPX، و QQQ يتبع NDX. الأسهم اللي تخالف القائد بقوة نسبية عالية، هي الأسهم اللي فيها قوة حقيقية، مو أسهم نحذفها.")

if st.button("🔍 اقرأ بيانات 150 سهم", use_container_width=True):
    ny = pytz.timezone("America/New_York")
    st.session_state['search_time'] = datetime.now(ny)
    with st.spinner("جار قراءة بيانات صناع السوق..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_stock_data(sym, leaders)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        st.session_state['results'] = results
        st.success(f"✅ قرأنا {len(results)} سهم - بدون توصيات، بيانات فقط")

if 'results' in st.session_state and st.session_state['results']:
    df = pd.DataFrame(st.session_state['results'])
    # ترتيب حسب القوة النسبية المطلقة - الأسهم اللي تتحرك بقوة، سواء مع السوق ولا ضده
    df['abs_rs'] = df['rs'].abs()
    df = df.sort_values('abs_rs', ascending=False)

    st.subheader("📊 لوحة البيانات - اقرأ وانت اللي تقرر")

    # فلتر
    show_only = st.selectbox("عرض:", ["الكل", "أسهم أقوى من القائد (RS +)", "أسهم أضعف من القائد (RS -)", "أسهم قريبة من Max Pain", "أسهم قريبة من جدار الجاما"])
    if show_only == "أسهم أقوى من القائد (RS +)":
        df_show = df[df['rs'] > 0]
    elif show_only == "أسهم أضعف من القائد (RS -)":
        df_show = df[df['rs'] < 0]
    elif show_only == "أسهم قريبة من Max Pain":
        df_show = df[df['max_pain_pos'] == "عند المستوى"]
    elif show_only == "أسهم قريبة من جدار الجاما":
        df_show = df[df['gamma_pos'] == "عند المستوى"]
    else:
        df_show = df

    # جدول البيانات الخام
    table = []
    for _, r in df_show.iterrows():
        table.append({
            "السهم": r['symbol'],
            "السعر": f"${r['last']:.2f}",
            "يوم": f"{r['chg_1d']:+.2f}%",
            "5 أيام": f"{r['chg_5d']:+.2f}%",
            "RS vs " + r['leader_name']: f"{r['rs']:+.2f}%",
            "Max Pain": f"${r['max_pain']:.0f}" if r['max_pain'] else "-",
            "السعر vs Max Pain": r['max_pain_pos'],
            "جدار جاما": f"${r['gamma_wall']:.0f}" if r['gamma_wall'] else "-",
            "السعر vs جاما": r['gamma_pos'],
            "POC": f"${r['poc']:.0f}" if r['poc'] else "-",
            "السعر vs POC": r['poc_pos'],
            "P/C OI": f"{r['pcr_oi']:.2f}" if r['pcr_oi'] else "-",
            "P/C Vol": f"{r['pcr_vol']:.2f}" if r['pcr_vol'] else "-",
            "GEX": f"{r['total_gex']:,.0f}",
            "Exp": f"{r['expiry']} ({r['days_left']}d)",
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("🔍 تفاصيل العقود - وين صانع السوق متواجد؟")

    for _, r in df_show.head(20).iterrows():
        with st.expander(f"{r['symbol']} - ${r['last']:.2f} | RS {r['rs']:+.2f}% vs {r['leader_name']}"):
            st.write(f"**السعر:** ${r['last']:.2f} | **تغير يوم:** {r['chg_1d']:+.2f}% | **تغير 5 أيام:** {r['chg_5d']:+.2f}%")
            st.write(f"**القائد {r['leader_name']}:** {r['leader_chg']:+.2f}% (5 أيام) | **القوة النسبية:** {r['rs']:+.2f}%")
            st.write(f"**Max Pain:** ${r['max_pain']:.0f} - السعر {r['max_pain_pos']}" if r['max_pain'] else "**Max Pain:** -")
            st.write(f"**جدار الجاما:** ${r['gamma_wall']:.0f} - السعر {r['gamma_pos']}" if r['gamma_wall'] else "**جدار الجاما:** -")
            st.write(f"**POC (أكبر فوليوم):** ${r['poc']:.0f} - السعر {r['poc_pos']}" if r['poc'] else "**POC:** -")
            st.write(f"**Put/Call OI:** {r['pcr_oi']:.2f} | **Put/Call Vol:** {r['pcr_vol']:.2f} | **GEX:** {r['total_gex']:,.0f}")
            st.write(f"**أكبر عقد CALL (OI×Vol):** {r['top_call']}")
            st.write(f"**أكبر عقد PUT (OI×Vol):** {r['top_put']}")
            st.write(f"**انتهاء:** {r['expiry']} ({r['days_left']} يوم)")
            st.caption("هذا عرض بيانات، مو توصية. إذا السعر فوق Max Pain وجدار الجاما و POC، والسهم أقوى من القائد، هذي بيانات صاعدة. إذا تحتهم، بيانات هابطة. انت اللي تقرر.")
