# V12.5 - كامل - انسخه كله وامسح القديم
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.5")
st.caption("مفتوح بكل وقت - يفحص المفضلة بس - يعطيك بس المنطبق")

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
        opn = df["Open"]
        c = num(close)
        if c == 0 or len(close) < 30:
            return None
        low_90 = float(low.tail(90).min())
        high_90 = float(high.tail(90).max())
        ma20 = float(close.tail(20).mean())
        ma50 = float(close.tail(50).mean()) if len(close) >= 50 else ma20
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        o = num(opn)
        # شروط مشددة - عشان ما يطلع 22 سهم
        # CALL: قاع قوي + شمعة خضراء + فوليوم فوق المتوسط + فوق MA20
        near_low = c <= low_90 * 1.05
        green = c > o
        vol_ok = last_vol > avg_vol * 1.4 if avg_vol > 0 else False
        above_ma20 = c > ma20
        if near_low and green and vol_ok and above_ma20:
            return {"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": "⭐ مفضلة - قاع قوي", "price": round(c, 2), "entry": round(num(high), 2), "stop": round(low_90, 2), "condition": "قاع قوي + شمعة خضراء + فوليوم + فوق MA20"}
        # PUT: قمة + شمعة حمراء + فوليوم + تحت MA20
        near_high = c >= high_90 * 0.95
        red = c < o
        below_ma20 = c < ma20
        if near_high and red and vol_ok and below_ma20:
            return {"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": "⭐ مفضلة - قمة ضعيفة", "price": round(c, 2), "entry": round(num(low), 2), "stop": round(high_90, 2), "condition": "قمة ضعيفة + شمعة حمراء + فوليوم + تحت MA20"}
        return None
    except Exception:
        return None

# صندوق رقم الواتساب - فوق الزر، عشان ما يختفي
st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري) - بدون + وبدون صفر، مثال: 9665XXXXXXXX", placeholder="9665XXXXXXXX")

# زر البحث - كل شي جواه
if st.button("🔍 اكتشف حيتان جديدة", use_container_width=True):
    results = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        df = get_df(t)
        if df is not None:
            r = analyze(t, df)
            if r is not None:
                results.append(r)
    bar.empty()
    txt.empty()

    if len(results) == 0:
        st.warning("مافيه سهم من المفضلة انطبقت عليه الشروط الحين - لا تدخل شي")
    else:
        st.success(f"طلع لك {len(results)} سهم من المفضلة انطبقت عليه الشروط")

        # رسالة الواتساب كاملة - جوة الزر، مو برا
        msg_lines = ["🐋 حيتان صانع السوق - V12.5", ""]
        for m in results:
            msg_lines.append(f"{m['ticker']} | {m['signal']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']}")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)

        if phone.strip() != "":
            wa_link = f"https://wa.me/{phone.strip()}?text={encoded}"
            st.link_button("📲 ارسل كل النتائج لهذا الرقم واتساب", wa_link, use_container_width=True)
        else:
            wa_link_all = f"https://wa.me/?text={encoded}"
            st.link_button("📲 ارسل كل النتائج واتساب - اختر من ترسل له", wa_link_all, use_container_width=True)

        st.code(msg_text, language="text")
        st.divider()

        for m in results:
            single = f"🐋 {m['ticker']} | {m['signal']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}"
            single_enc = urllib.parse.quote(single)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"{m['ticker']} | {m['signal']} | {m['kind']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}")
            with col2:
                if phone.strip() != "":
                    st.link_button("واتساب", f"https://wa.me/{phone.strip()}?text={single_enc}")
                else:
                    st.link_button("واتساب", f"https://wa.me/?text={single_enc}")

st.divider()
st.caption("مفتوح بكل وقت - يعرض بس المنطبق - لا يعرض CALL في القمة ولا PUT في القاع")
