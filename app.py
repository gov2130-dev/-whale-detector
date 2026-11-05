# V12.4 - خفيف وسريع - يفتح على طول
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.4")
st.caption("مفتوح بكل وقت - يفحص المفضلة بس عند كل بحث")

# --- قائمة المفضلة للأوبشنز فقط ---
# لا تفحص 500 سهم، افحص هذي بس، تخلص في 20 ثانية
FAVORITE_OPTIONS = [
    "SPY", "QQQ", "IWM", "DIA", "GLD", "SLV", "GDX", "GDXJ", "USO", "TLT",
    "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN", "GOOGL", "NFLX", "AVGO",
    "PLTR", "COIN", "MSTR", "MU", "INTC",
    "XOM", "CVX", "NEM",
    "FSLR", "ENPH",
    "BABA", "BIDU",
    "JPM", "BAC", "GS",
]

def num(x):
    try:
        if hasattr(x, "iloc"):
            x = x.iloc[-1]
        if hasattr(x, "item"):
            try:
                return float(x.item())
            except Exception:
                pass
        if isinstance(x, (list, tuple)):
            x = x[-1]
        return float(x)
    except Exception:
        return 0.0

@st.cache_data(ttl=300)
def get_df(ticker):
    try:
        df = yf.download(ticker, period="3mo", interval="1d", progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        return df
    except Exception:
        return None

def analyze(ticker, df):
    try:
        close = df["Close"]
        low = df["Low"]
        high = df["High"]
        vol = df["Volume"]
        c = num(close)
        if c == 0 or len(close) < 30:
            return None
        low_52 = float(low.tail(90).min())
        high_52 = float(high.tail(90).max())
        ma20 = float(close.tail(20).mean())
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        # قاع قوي: قريب من قاع 3 شهور + فوليوم عالي + فوق MA20
        near_low = c <= low_52 * 1.08
        vol_spike = last_vol > avg_vol * 1.3 if avg_vol > 0 else False
        above_ma = c > ma20
        # قمة ضعيفة: قريب من قمة 3 شهور + نازل من القمة
        near_high = c >= high_52 * 0.92
        falling = c < num(high)
        if near_low and (vol_spike or above_ma):
            return {"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": "⭐ مفضلة أوبشنز - قاع", "price": round(c, 2), "entry": round(num(high), 2), "stop": round(low_52, 2), "condition": "قاع قوي + فوليوم + فوق MA20"}
        if near_high and falling:
            return {"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": "⭐ مفضلة أوبشنز - قمة", "price": round(c, 2), "entry": round(num(low), 2), "stop": round(high_52, 2), "condition": "قمة ضعيفة + نازل من القمة"}
        return None
    except Exception:
        return None

# --- زر البحث ---
if st.button("🔍 اكتشف حيتان جديدة", use_container_width=True):
    results = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i+1)/len(FAVORITE_OPTIONS))
        df = get_df(t)
        if df is not None:
            r = analyze(t, df)
            if r:
                results.append(r)
    bar.empty()
    txt.empty()
    if len(results) == 0:
        st.warning("مافيه سهم من المفضلة انطبقت عليه الشروط الحين - لا تدخل شي")
    else:
        st.success(f"طلع لك {len(results)} سهم من المفضلة انطبقت عليه الشروط")
        for m in results:
            st.info(f"{m['ticker']} | {m['signal']} | {m['kind']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}")

st.divider()
st.caption("يفحص المفضلة بس - عشان يفتح بسرعة وما يعلق. لا يعرض: CALL في القمة - PUT في القاع")
