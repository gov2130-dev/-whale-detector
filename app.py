# V12.9 - كامل - لا تلصق جزء، الصق الملف كله
import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.9")
st.caption("إذا تشوف هذي الشاشة، معناها التطبيق فتح صح.")

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري) - بدون + وبدون صفر، مثال: 9665XXXXXXXX", placeholder="9665XXXXXXXX")

if st.button("✅ جرب التطبيق", use_container_width=True):
    st.success("التطبيق شغال، الحين اضغط اكتشف")

FAVORITE_OPTIONS = ["SPY","QQQ","AAPL","MSFT","NVDA","TSLA","AMD","META","AMZN","GOOGL","GDX","GLD","SLV","FSLR","ENPH","BABA","BIDU","CVX","COIN","PLTR"]

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

def get_pos(df):
    try:
        c = num(df["Close"])
        low_90 = float(df["Low"].tail(90).min())
        high_90 = float(df["High"].tail(90).max())
        if high_90 == low_90:
            return None, None, None, None
        pos = (c - low_90) / (high_90 - low_90) * 100
        return c, low_90, high_90, pos
    except Exception:
        return None, None, None, None

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
        pos = (c - low_90) / (high_90 - low_90) * 100
        if 20 < pos < 80:
            return None
        ma20 = float(close.tail(20).mean())
        ma50 = float(close.tail(50).mean())
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        h = num(high)
        l = num(low)
        uptrend = c > ma50
        downtrend = c < ma50
        two_green = (float(close.iloc[-1]) > float(opn.iloc[-1])) and (float(close.iloc[-2]) > float(opn.iloc[-2]))
        two_red = (float(close.iloc[-1]) < float(opn.iloc[-1])) and (float(close.iloc[-2]) < float(opn.iloc[-2]))
        if pos <= 20 and uptrend and two_green and avg_vol > 0 and last_vol > avg_vol * 1.4:
            return {"ticker": ticker, "signal": "CALL", "price": round(c, 2), "entry": round(h, 2), "stop": round(low_90, 2), "condition": "قاع تماماً + شمعتين خضراء + فوليوم حوت", "score": 90, "strength": "🔥 قوي", "pos": round(pos, 1)}
        if pos >= 80 and downtrend and two_red and avg_vol > 0 and last_vol > avg_vol * 1.4:
            return {"ticker": ticker, "signal": "PUT", "price": round(c, 2), "entry": round(l, 2), "stop": round(high_90, 2), "condition": "قمة تماماً + شمعتين حمراء + فوليوم حوت", "score": 90, "strength": "🔥 قوي", "pos": round(pos, 1)}
        return None
    except Exception:
        return None

if st.button("🔍 اكتشف حيتان جديدة", use_container_width=True):
    import yfinance as yf
    results = []
    all_data = {}
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        try:
            df = yf.download(t, period="6mo", interval="1d", progress=False, auto_adjust=False)
            if df is not None and not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
                all_data[t] = df
                r = analyze(t, df)
                if r is not None:
                    results.append(r)
        except Exception:
            continue
    bar.empty()
    txt.empty()
    if len(results) == 0:
        st.warning("مافيه سهم في قاع تماماً أو قمة تماماً الحين - كل الأسهم في النص 20%-80% - لا تدخل شي، هذا هو الصح")
        st.info("CVX اللي كان 67.2% اختفى الحين، لأنه صار في المنطقة المحرمة.")
        st.subheader("👀 قائمة المراقبة - لا تدخل الحين، راقب بس")
        st.caption("هذي الأسهم قريبة من القاع أو القمة، باقي لها شوي وتدخل منطقة الحوت.")
        watch = []
        for t, dfw in all_data.items():
            c2, loww, highw, posw = get_pos(dfw)
            if c2 is None:
                continue
            if posw < 50:
                dist = abs(posw - 20)
                zone = "قريب من القاع"
                target = "CALL"
            else:
                dist = abs(80 - posw)
                zone = "قريب من القمة"
                target = "PUT"
            watch.append({"ticker": t, "price": round(c2, 2), "pos": round(posw, 1), "dist": round(dist, 1), "zone": zone, "target": target})
        watch = sorted(watch, key=lambda x: x["dist"])[:5]
        for w in watch:
            st.warning(f"{w['ticker']} | السعر: {w['price']} | موقع السعر: {w['pos']}% من القاع | {w['zone']} | باقي له {w['dist']}% ويوصل منطقة {w['target']} | 👀 مراقبة فقط، لا تدخل")
    else:
        st.success(f"أقوى {len(results)} سهم")
        msg_lines = ["🐋 حيتان صانع السوق - V12.9", ""]
        for m in results:
            msg_lines.append(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']}")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)
        if phone.strip() != "":
            st.link_button("📲 ارسل كل النتائج واتساب", f"https://wa.me/{phone.strip()}?text={encoded}", use_container_width=True)
        else:
            st.link_button("📲 ارسل كل النتائج واتساب", f"https://wa.me/?text={encoded}", use_container_width=True)
        st.code(msg_text, language="text")
        for m in results:
            st.info(f"{m['ticker']} | {m['signal']} | نقاط: {m['score']} | {m['strength']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | موقع السعر: {m['pos']}% | {m['condition']}")

st.divider()
st.caption("قاعدة: 0%-20% = قاع، 80%-100% = قمة، 20%-80% = نص، ما نعطي إشارة في النص")
