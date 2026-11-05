# V12.6 - كامل - نظام نقاط - ما يقول لك مافيه سهم أبداً
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.6")
st.caption("مفتوح بكل وقت - نظام نقاط - يطلع لك أقوى 5 دايماً")

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
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        o = num(opn)
        h = num(high)
        l = num(low)

        # --- نظام النقاط: كل شرط يعطي نقاط ---
        score_call = 0
        reasons_call = []
        # 1. قريب من القاع (40 نقطة - أهم شي)
        if c <= low_90 * 1.05:
            score_call += 40
            reasons_call.append("قاع قوي")
        elif c <= low_90 * 1.10:
            score_call += 25
            reasons_call.append("قريب من القاع")
        # 2. شمعة خضراء (20 نقطة)
        if c > o:
            score_call += 20
            reasons_call.append("شمعة خضراء")
        # 3. فوليوم عالي (20 نقطة)
        if avg_vol > 0 and last_vol > avg_vol * 1.4:
            score_call += 20
            reasons_call.append("فوليوم حوت")
        elif avg_vol > 0 and last_vol > avg_vol * 1.0:
            score_call += 10
            reasons_call.append("فوليوم فوق المتوسط")
        # 4. فوق MA20 (20 نقطة)
        if c > ma20:
            score_call += 20
            reasons_call.append("فوق MA20")

        score_put = 0
        reasons_put = []
        if c >= high_90 * 0.95:
            score_put += 40
            reasons_put.append("قمة ضعيفة")
        elif c >= high_90 * 0.90:
            score_put += 25
            reasons_put.append("قريب من القمة")
        if c < o:
            score_put += 20
            reasons_put.append("شمعة حمراء")
        if avg_vol > 0 and last_vol > avg_vol * 1.4:
            score_put += 20
            reasons_put.append("فوليوم حوت")
        if c < ma20:
            score_put += 20
            reasons_put.append("تحت MA20")

        # نختار الأقوى: CALL ولا PUT
        if score_call >= score_put and score_call >= 50:
            strength = "🔥 قوي" if score_call >= 80 else "✅ متوسط" if score_call >= 65 else "⚠️ ضعيف - انتظر تأكيد"
            return {"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": "⭐ مفضلة - قاع", "price": round(c, 2), "entry": round(h, 2), "stop": round(low_90, 2), "condition": " + ".join(reasons_call), "score": score_call, "strength": strength}
        if score_put > score_call and score_put >= 50:
            strength = "🔥 قوي" if score_put >= 80 else "✅ متوسط" if score_put >= 65 else "⚠️ ضعيف - انتظر تأكيد"
            return {"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": "⭐ مفضلة - قمة", "price": round(c, 2), "entry": round(l, 2), "stop": round(high_90, 2), "condition": " + ".join(reasons_put), "score": score_put, "strength": strength}
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

    # رتب بالأقوى، وخذ أقوى 5 بس - عشان ما يطلع لك 22 ولا 0
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:5]

    if len(results) == 0:
        st.warning("حتى بالنقاط مافيه سهم وصل 50 - السوق هادي الحين، لا تدخل شي")
    else:
        st.success(f"أقوى {len(results)} سهم الحين - مرتبة من الأقوى للأضعف")

        msg_lines = ["🐋 حيتان صانع السوق - V12.6", ""]
        for m in results:
            msg_lines.append(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']}")
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
            single = f"🐋 {m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']}"
            single_enc = urllib.parse.quote(single)
            col1, col2 = st.columns([4, 1])
            with col1:
                st.info(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}")
            with col2:
                if phone.strip() != "":
                    st.link_button("واتساب", f"https://wa.me/{phone.strip()}?text={single_enc}")
                else:
                    st.link_button("واتساب", f"https://wa.me/?text={single_enc}")

st.divider()
st.caption("نظام نقاط: 100 = كامل. فوق 80 قوي، فوق 65 متوسط، تحت 65 انتظر تأكيد ولا تدخل بكامل المبلغ")
