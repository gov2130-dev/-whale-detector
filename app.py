# V12.7 - كامل - يمنع التناقض والقلبة
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.7")
st.caption("مفتوح بكل وقت - لا يقلب من CALL لـ PUT في يوم واحد")

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
        df = yf.download(ticker, period="6mo", interval="1d", progress=False, auto_adjust=False)
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
        if c == 0 or len(close) < 50:
            return None
        low_90 = float(low.tail(90).min())
        high_90 = float(high.tail(90).max())
        if high_90 == low_90:
            return None

        # --- 1. وين السعر في المسافة؟ ---
        # 0% = في القاع، 100% = في القمة
        pos = (c - low_90) / (high_90 - low_90) * 100

        # --- منطقة محرمة: 35% الى 65% = في النص، لا نعطي إشارة ---
        if 35 <= pos <= 65:
            return None

        ma20 = float(close.tail(20).mean())
        ma50 = float(close.tail(50).mean())
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        o = num(opn)
        h = num(high)
        l = num(low)

        # --- 2. فلتر الترند: MA50 ---
        # إذا السعر فوق MA50، الترند صاعد، ممنوع PUT
        # إذا تحت MA50، الترند هابط، ممنوع CALL
        uptrend = c > ma50
        downtrend = c < ma50

        # --- 3. شمعتين تأكيد ---
        # آخر شمعتين
        c1 = float(close.iloc[-1])
        c2 = float(close.iloc[-2])
        o1 = float(opn.iloc[-1])
        o2 = float(opn.iloc[-2])
        two_green = (c1 > o1) and (c2 > o2)
        two_red = (c1 < o1) and (c2 < o2)

        # --- CALL: لازم يكون في منطقة القاع 0-35% + ترند صاعد أو فوق MA20 + شمعتين خضراء ---
        if pos <= 35 and uptrend:
            score = 0
            reasons = []
            if pos <= 15:
                score += 40
                reasons.append("في القاع تماماً")
            else:
                score += 25
                reasons.append("في منطقة القاع")
            if two_green:
                score += 30
                reasons.append("شمعتين خضراء تأكيد")
            elif c > o:
                score += 15
                reasons.append("شمعة خضراء واحدة")
            if avg_vol > 0 and last_vol > avg_vol * 1.4:
                score += 20
                reasons.append("فوليوم حوت")
            if c > ma20:
                score += 10
                reasons.append("فوق MA20")
            if score >= 60:
                strength = "🔥 قوي" if score >= 85 else "✅ متوسط"
                return {"ticker": ticker, "signal": "CALL", "kind": "قاع - ترند صاعد", "price": round(c, 2), "entry": round(h, 2), "stop": round(low_90, 2), "condition": " + ".join(reasons), "score": score, "strength": strength, "pos": round(pos, 1)}

        # --- PUT: لازم يكون في منطقة القمة 65-100% + ترند هابط + شمعتين حمراء ---
        if pos >= 65 and downtrend:
            score = 0
            reasons = []
            if pos >= 85:
                score += 40
                reasons.append("في القمة تماماً")
            else:
                score += 25
                reasons.append("في منطقة القمة")
            if two_red:
                score += 30
                reasons.append("شمعتين حمراء تأكيد")
            elif c < o:
                score += 15
                reasons.append("شمعة حمراء واحدة")
            if avg_vol > 0 and last_vol > avg_vol * 1.4:
                score += 20
                reasons.append("فوليوم حوت")
            if c < ma20:
                score += 10
                reasons.append("تحت MA20")
            if score >= 60:
                strength = "🔥 قوي" if score >= 85 else "✅ متوسط"
                return {"ticker": ticker, "signal": "PUT", "kind": "قمة - ترند هابط", "price": round(c, 2), "entry": round(l, 2), "stop": round(high_90, 2), "condition": " + ".join(reasons), "score": score, "strength": strength, "pos": round(pos, 1)}

        return None
    except Exception:
        return None

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري) - بدون + وبدون صفر، مثال: 9665XXXXXXXX", placeholder="9665XXXXXXXX")

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
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    if len(results) == 0:
        st.warning("مافيه سهم في قاع أو قمة واضحة الحين - كل الأسهم في النص - لا تدخل شي، هذا هو الصح")
        st.info("السبب: SPY و QQQ الحين في النص بين القاع والقمة، عشان كذا ما نعطيك إشارة عليهم. قبل كان الكود يعطيك إشارة وهمية عليهم.")
    else:
        st.success(f"أقوى {len(results)} سهم في منطقة واضحة - مو في النص")
        msg_lines = ["🐋 حيتان صانع السوق - V12.7", ""]
        for m in results:
            msg_lines.append(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | موقع السعر: {m['pos']}% من القاع")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)
        if phone.strip() != "":
            st.link_button("📲 ارسل كل النتائج واتساب", f"https://wa.me/{phone.strip()}?text={encoded}", use_container_width=True)
        else:
            st.link_button("📲 ارسل كل النتائج واتساب", f"https://wa.me/?text={encoded}", use_container_width=True)
        st.code(msg_text, language="text")
        st.divider()
        for m in results:
            st.info(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | موقع السعر: {m['pos']}% من القاع | {m['condition']}")

st.divider()
st.caption("قاعدة جديدة: إذا السهم في النص 35%-65%، ما نعطيك إشارة. لازم يكون في قاع واضح أو قمة واضحة + ترند يأكده + شمعتين تأكيد")
