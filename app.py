# V12.3 - Streamlit - مصحح
# مفتوح بكل وقت - عند كل بحث يفحص الكل ويعطيك بس المنطبق

import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V12.3")
st.caption("مفتوح بكل وقت - عند كل بحث، يفحص الكل ويعطيك بس اللي انطبقت عليه الشروط")

# --- دالة مساعدة: تاخذ رقم واحد مهما كان شكل الجدول ---
def num(x):
    try:
        # لو كان Series أو DataFrame خذ آخر قيمة
        if hasattr(x, "iloc"):
            x = x.iloc[-1]
        if hasattr(x, "item"):
            try:
                return float(x.item())
            except Exception:
                pass
        # لو كان list
        if isinstance(x, (list, tuple)):
            x = x[-1]
        return float(x)
    except Exception:
        return 0.0

def get_series(df, col):
    # yfinance الجديد يرجع أعمدة MultiIndex
    try:
        s = df[col]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s
    except Exception:
        return pd.Series(dtype=float)

def get_universe():
    # الكون - تقدر تكبره بعدين
    # الحين نبدأ بقائمة S&P 500 عشان الفحص يكون سريع
    try:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        syms = tables[0]['Symbol'].tolist()
        return [str(s).replace('.', '-').strip() for s in syms]
    except Exception:
        return ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN", "GOOGL"]

def check_low(close_s, low_s, vol_s):
    try:
        if len(close_s) < 60:
            return False, 0.0, 0.0
        low_52w = float(low_s.tail(252).min())
        high_52w = float(close_s.tail(252).max())
        close = num(close_s)
        low_today = num(low_s)
        if low_52w == 0:
            return False, 0.0, 0.0
        near_low = close <= low_52w * 1.10
        touches = int((low_s.tail(60) <= low_52w * 1.05).sum())
        tested = touches >= 2
        last_vol = num(vol_s)
        avg_vol = float(vol_s.tail(20).mean())
        vol_spike = last_vol > avg_vol * 1.5 if avg_vol > 0 else False
        bouncing = close > low_today
        return (near_low and tested and vol_spike and bouncing), low_52w, high_52w
    except Exception:
        return False, 0.0, 0.0

def check_high(close_s, high_s):
    try:
        if len(close_s) < 60:
            return False, 0.0, 0.0
        high_52w = float(high_s.tail(252).max())
        low_52w = float(close_s.tail(252).min())
        close = num(close_s)
        high_today = num(high_s)
        near_high = close >= high_52w * 0.90 if high_52w > 0 else False
        touches = int((high_s.tail(60) >= high_52w * 0.95).sum())
        tested = touches >= 2
        falling = close < high_today
        return (near_high and tested and falling), low_52w, high_52w
    except Exception:
        return False, 0.0, 0.0

def check_breakout(close_s):
    try:
        if len(close_s) < 20:
            return False, 0.0, 0.0
        ma20 = float(close_s.tail(20).mean())
        ma50 = float(close_s.tail(50).mean()) if len(close_s) >= 50 else ma20
        close = num(close_s)
        prev = float(close_s.iloc[-2]) if len(close_s) >= 2 else close
        above_ma = close > ma20 and prev <= ma20
        return above_ma, ma20, ma50
    except Exception:
        return False, 0.0, 0.0

def get_option_whale(ticker):
    # اربط هنا API الأوبشن حقك
    # الحين ترجع None عشان ما يكسر الكود
    return {"type": None, "premium": 0, "is_maker": False}

def scan():
    universe = get_universe()
    results = []
    progress = st.progress(0)
    status = st.empty()
    total = len(universe)
    for i, ticker in enumerate(universe):
        try:
            status.text(f"يفحص: {ticker} - {i+1}/{total}")
            progress.progress((i + 1) / total)
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=False)
            if df is None or df.empty or len(df) < 60:
                continue
            # سطّح الأعمدة لو كانت MultiIndex
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            close_s = get_series(df, "Close")
            low_s = get_series(df, "Low")
            high_s = get_series(df, "High")
            vol_s = get_series(df, "Volume")
            if close_s.empty:
                continue
            low_ok, low_52w, high_52w = check_low(close_s, low_s, vol_s)
            high_ok, _, _ = check_high(close_s, high_s)
            breakout_ok, ma20, ma50 = check_breakout(close_s)
            opt = get_option_whale(ticker)
            close = num(close_s)
            low_today = num(low_s)
            high_today = num(high_s)
            last_vol = num(vol_s)
            avg_vol = float(vol_s.tail(20).mean()) if len(vol_s) > 0 else 0
            is_buy_block = avg_vol > 0 and last_vol > avg_vol * 2.0 and close > num(df["Open"]) if "Open" in df.columns else False
            is_sell_block = avg_vol > 0 and last_vol > avg_vol * 2.0 and close < num(df["Open"]) if "Open" in df.columns else False

            # شرط 1: CALL في القاع
            if low_ok and breakout_ok:
                if opt.get("type") == "CALL" and opt.get("is_maker"):
                    results.append({"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": "حوت أوبشن CALL", "price": round(close, 2), "condition": "قاع قوي + كسر مقاومة + حوت CALL", "entry": round(high_today, 2), "stop": round(low_52w, 2)})
                elif is_buy_block:
                    results.append({"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": "حوت سهم شراء", "price": round(close, 2), "condition": "قاع قوي + بلوك شراء + فوليوم غير عادي", "entry": round(high_today, 2), "stop": round(low_52w, 2)})

            # شرط 2: PUT في القمة
            if high_ok:
                if opt.get("type") == "PUT" and opt.get("is_maker"):
                    results.append({"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": "حوت أوبشن PUT", "price": round(close, 2), "condition": "قمة ضعيفة + حوت PUT", "entry": round(low_today, 2), "stop": round(high_52w, 2)})
                elif is_sell_block:
                    results.append({"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": "حوت سهم بيع", "price": round(close, 2), "condition": "قمة ضعيفة + بلوك بيع", "entry": round(low_today, 2), "stop": round(high_52w, 2)})

        except Exception as e:
            # لا توقف الفحص كله عشان سهم واحد خرب
            continue
    progress.empty()
    status.empty()
    return results

# --- زر البحث - مفتوح بكل وقت ---
if st.button("🔍 اكتشف حيتان جديدة", use_container_width=True):
    with st.spinner("يفحص كل الأسهم الحين..."):
        matches = scan()
    if len(matches) == 0:
        st.warning("مافيه سهم انطبقت عليه الشروط الحين - لا تدخل شي، ارجع ابحث بعد شوي")
    else:
        st.success(f"طلع لك {len(matches)} سهم انطبقت عليه الشروط الحين")
        for m in matches:
            st.info(f"{m['ticker']} | {m['signal']} | {m['kind']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | الشرط: {m['condition']}")

st.divider()
st.caption("لا يعرض: حوت CALL في القمة - حوت PUT في القاع - سهم في النص")
