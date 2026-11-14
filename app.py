# ============================================================
# حيتان ابو راكان - V22 - القائد SPX و NDX
# التصحيح: SPY و QQQ مو قادة، هم تابعين
# القائد: SPX (^GSPC) و NDX (^NDX)
# والأسهم اللي تخالف السوق بقوة نسبية، ما نحذفها، نعطيها أولوية
# لأن السهم اللي يطلع والسوق نازل، فيه قوة حقيقية
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

# ===== 1. قراءة القائد الحقيقي: SPX و NDX =====
def get_leaders_regime():
    """القائد: SPX (^GSPC) و NDX (^NDX) - هم اللي يحركون السوق، مو SPY و QQQ"""
    try:
        leaders = {}
        for sym, name in [("^GSPC","SPX"), ("^NDX","NDX")]:
            tk = yf.Ticker(sym)
            hist = tk.history(period="1mo", interval="1d")
            if hist.empty or len(hist) < 10:
                continue
            last = float(hist['Close'].iloc[-1])
            lows = hist['Low'].tail(10).values
            highs = hist['High'].tail(10).values
            vwap = (hist['Close'] * hist['Volume']).sum() / hist['Volume'].sum()
            higher_lows = lows[-1] > lows[0]
            higher_highs = highs[-1] > highs[0]
            lower_lows = lows[-1] < lows[0]
            lower_highs = highs[-1] < highs[0]
            above_vwap = last > vwap
            if higher_lows and higher_highs and above_vwap:
                leaders[name] = "CALL"
            elif lower_lows and lower_highs and not above_vwap:
                leaders[name] = "PUT"
            else:
                leaders[name] = "NEUTRAL"
            leaders[f"{name}_chg"] = float((hist['Close'].iloc[-1] - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6] * 100)
        spx = leaders.get("SPX", "NEUTRAL")
        ndx = leaders.get("NDX", "NEUTRAL")
        spx_chg = leaders.get("SPX_chg", 0)
        ndx_chg = leaders.get("NDX_chg", 0)
        # إذا SPX و NDX متفقين، السوق له اتجاه واضح. إذا مختلفين، السوق منقسم
        if spx == ndx and spx != "NEUTRAL":
            regime = spx
            text = f"SPX {spx} ({spx_chg:+.2f}%) و NDX {ndx} ({ndx_chg:+.2f}%) متفقين"
        elif spx != ndx:
            regime = "MIXED"
            text = f"SPX {spx} ({spx_chg:+.2f}%) و NDX {ndx} ({ndx_chg:+.2f}%) مختلفين - السوق منقسم"
        else:
            regime = "NEUTRAL"
            text = f"SPX {spx} و NDX {ndx} - بدون اتجاه واضح"
        return regime, text, spx_chg, ndx_chg, leaders
    except Exception as e:
        return "NEUTRAL", "ما قدرنا نقرأ SPX و NDX", 0, 0, {}

def calc_max_pain(calls, puts, last):
    try:
        strikes = sorted(set(calls['strike'].tolist()) | set(puts['strike'].tolist()))
        best = last
        min_pain = float('inf')
        for s in strikes:
            call_pain = ((s - calls['strike']).clip(lower=0) * calls['openInterest']).sum()
            put_pain = ((puts['strike'] - s).clip(lower=0) * puts['openInterest']).sum()
            total = call_pain + put_pain
            if total < min_pain:
                min_pain = total
                best = s
        return float(best)
    except:
        return last

def get_whale(symbol, market_regime, spx_chg, ndx_chg):
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

        # ===== 2. بنية السعر للسهم نفسه =====
        lows = hist_long['Low'].tail(10).values
        highs = hist_long['High'].tail(10).values
        vwap = (hist_long['Close'] * hist_long['Volume']).sum() / hist_long['Volume'].sum()
        higher_lows = lows[-1] > lows[0]
        higher_highs = highs[-1] > highs[0]
        lower_lows = lows[-1] < lows[0]
        lower_highs = highs[-1] < highs[0]
        above_vwap = last > vwap

        if higher_lows and higher_highs and above_vwap:
            stock_trend = "CALL"
        elif lower_lows and lower_highs and not above_vwap:
            stock_trend = "PUT"
        else:
            return None

        # ===== 3. القوة النسبية: هل السهم يمشي مع السوق ولا يخالفه؟ =====
        # هذا هو التصحيح الأساسي: السهم المخالف ما نحذفه، نفحص قوته
        stock_chg_5d = float((hist_long['Close'].iloc[-1] - hist_long['Close'].iloc[-6]) / hist_long['Close'].iloc[-6] * 100)
        # القائد اللي يخص السهم: أسهم التكنولوجيا تقارن مع NDX، الباقي مع SPX
        tech = symbol in ["NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL","AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX","PLTR","SNOW","CRWD","PANW","SHOP","SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","QQQ"]
        leader_chg = ndx_chg if tech else spx_chg
        leader_name = "NDX" if tech else "SPX"
        # القوة النسبية = أداء السهم - أداء القائد
        rs = stock_chg_5d - leader_chg
        # هل السهم يمشي مع القائد ولا يخالفه؟
        follows = (stock_trend == market_regime) or market_regime in ["NEUTRAL","MIXED"]
        diverges = not follows

        # إذا السهم يخالف السوق، لازم تكون قوته النسبية قوية جدا عشان نقبله
        # مثال: السوق PUT -2% والسهم CALL +3%، معناه RS = +5%، هذا سهم قوي، نقبله
        # أما إذا السوق PUT -2% والسهم CALL +0.2%، معناه RS = +2.2% بس، هذا مو مخالف حقيقي، هذا متذبذب، نرفضه
        if diverges:
            if abs(rs) < 3.0:
                return None  # مخالف ضعيف، مو مخالف حقيقي، نرفضه
            # مخالف قوي، نكمل ونعطيه أولوية، لأن فيه قوة شراء حقيقية

        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        calls, puts = chain.calls, chain.puts
        if calls.empty or puts.empty:
            return None

        # ===== 4. صانع السوق للتأكيد، مو للقلب =====
        max_pain = calc_max_pain(calls, puts, last)
        # إذا صانع السوق يسحب السعر عكس اتجاه السهم بقوة، نرفض، ما ننقلب
        if stock_trend == "CALL" and max_pain < last * 0.98:
            return None
        if stock_trend == "PUT" and max_pain > last * 1.02:
            return None

        call_vol = calls['volume'].fillna(0).sum()
        put_vol = puts['volume'].fillna(0).sum()
        pcr_vol = put_vol / call_vol if call_vol > 0 else 1
        if stock_trend == "CALL" and pcr_vol > 1.3:
            return None
        if stock_trend == "PUT" and pcr_vol < 0.7:
            return None

        direction = stock_trend
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
                if vol < 500 or oi < 500:
                    continue
                strength = oi * vol
                candidates.append({"strike": strike, "entry": entry, "volume": int(vol), "oi": int(oi),
                                   "bid": bid, "strength": strength, "type": direction})
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
                "days_left": days_left, "max_pain": max_pain, "pcr_vol": round(pcr_vol, 2),
                "oi": whale['oi'], "stock_trend": stock_trend, "market_regime": market_regime,
                "rs": round(rs, 2), "leader_name": leader_name, "diverges": diverges,
                "stock_chg": round(stock_chg_5d, 2), "leader_chg": round(leader_chg, 2),
                "dist": f"{abs(strike-last)/last*100:.2f}%"}
    except Exception:
        return None

def make_msg(r):
    emoji = "🔴" if r['type'] == 'PUT' else "🟢"
    strike_str = f"{r['strike']:.0f}" if r['strike'] == int(r['strike']) else f"{r['strike']:.1f}"
    tag = " ⚡ مخالف للسوق" if r['diverges'] else ""
    return f"""{emoji} {r['symbol']} {strike_str} {r['type']} 🐋{tag}
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
    market_regime, market_text, spx_chg, ndx_chg, leaders = get_leaders_regime()
    st.session_state['market_regime'] = market_regime
    st.session_state['market_text'] = market_text
    with st.spinner(f"جار قراءة القائد SPX و NDX: {market_text}..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym, market_regime, spx_chg, ndx_chg)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        # الأسهم المخالفة بقوة نسبية عالية تطلع أول، لأنها الأقوى
        # بعدين الأسهم اللي تمشي مع السوق
        results = sorted(results, key=lambda x: (x['diverges'], abs(x['rs']), x['volume'] * x['oi']), reverse=True)[:10]
        st.session_state['results'] = results
        st.success(f"✅ القائد: {market_text} | لقيت {len(results)} توصية")

if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل وأقوى 10 توصيات - القائد SPX و NDX")
    if 'search_time' in st.session_state:
        st.caption(f"{get_search_time_text()}")
    if 'market_text' in st.session_state:
        st.info(f"📊 القائد: {st.session_state['market_text']}")

    all_msg = make_all_msg(st.session_state['results'])
    whatsapp_button(all_msg, f"📤 أرسل الجميع ({len(st.session_state['results'])}) واتساب - اختر أي شخص", bg="#1E88E5")
    st.divider()

    for idx, r in enumerate(st.session_state['results'], start=1):
        emoji = "🔴" if r['type'] == 'PUT' else "🟢"
        single = make_single_msg(r)
        with st.container():
            tag = " ⚡ مخالف للسوق - قوة نسبية" if r['diverges'] else " ✅ مع السوق"
            st.markdown(f"### {idx}. {emoji} {r['symbol']} {r['strike']:.0f} {r['type']} 🐋{tag}")
            st.write(f"Exp: {r['expiry']} ({r['days_left']}d) Stock: ${r['last']:.2f} | Entry: ${r['entry']} Bid: ${r['bid']} | Stop: ${r['stop']} | حجم: {r['volume']} | OI: {r['oi']}")
            st.write(f"📊 Max Pain ${r['max_pain']:.0f} | P/C Vol {r['pcr_vol']} | السهم {r['stock_chg']:+.2f}% vs {r['leader_name']} {r['leader_chg']:+.2f}% | قوة نسبية {r['rs']:+.2f}%")
            st.write(f"Target: ${r['t1']} (+50%) | ${r['t2']} (+130%) | ${r['t3']} (+220%)")
            whatsapp_button(single, f"📤 أرسل {r['symbol']} واتساب - اختر أي شخص", bg="#25D366")
            st.divider()
