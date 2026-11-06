# V13 - كامل - توصيات أوبشن بنفس ستايل بوت الحيتان
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V13")
st.caption("توصية أوبشن كاملة: سترايك + اكسبايري + دخول + وقف + أهداف - مثل بوت الحيتان")

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

def get_stock_signal(ticker, df):
    # نحدد الاتجاه فقط: CALL ولا PUT - من القاع / القمة + الترند
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
        ma50 = float(close.tail(50).mean())
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        two_green = (float(close.iloc[-1]) > float(opn.iloc[-1])) and (float(close.iloc[-2]) > float(opn.iloc[-2]))
        two_red = (float(close.iloc[-1]) < float(opn.iloc[-1])) and (float(close.iloc[-2]) < float(opn.iloc[-2]))
        vol_ok = avg_vol > 0 and last_vol > avg_vol * 1.2
        # CALL: في القاع + ترند صاعد + تأكيد
        if pos <= 30 and c > ma50 and (two_green or vol_ok):
            return "CALL"
        # PUT: في القمة + ترند هابط + تأكيد
        if pos >= 70 and c < ma50 and (two_red or vol_ok):
            return "PUT"
        # إذا في النص، نأخذ الاتجاه من الترند + آخر شمعتين - عشان ما يقول لك مافيه سهم
        # هذا هو الفرق: في V13 ما نوقف على النص، نعطيك اتجاه الحوت
        if c > ma50 and two_green:
            return "CALL"
        if c < ma50 and two_red:
            return "PUT"
        return None
    except Exception:
        return None

def get_option_reco(ticker, stock_price, direction):
    # نجيب سلسلة الأوبشن الحقيقية من Yahoo - نفس اللي يستخدمه بوت الحيتان
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps or len(exps) == 0:
            return None
        # نختار أقرب اكسبايري فيه 1-3 أيام - مثل صورتك: Exp 2026-09-02 (1d)
        # ناخذ أول اكسبايري متاح
        exp = exps[0]
        # نحسب كم يوم باقي
        try:
            exp_date = datetime.strptime(exp, "%Y-%m-%d")
            days = (exp_date - datetime.now()).days
            if days < 0:
                days = 0
        except Exception:
            days = 0
        chain = tk.option_chain(exp)
        df_opt = chain.calls if direction == "CALL" else chain.puts
        if df_opt is None or df_opt.empty:
            return None
        # نختار السترايك الأقرب لسعر السهم - هذا هو سترايك صانع السوق
        df_opt = df_opt.copy()
        df_opt["diff"] = abs(df_opt["strike"] - stock_price)
        df_opt = df_opt.sort_values("diff")
        row = df_opt.iloc[0]
        strike = float(row["strike"])
        # سعر الدخول = آخر سعر، والـ Bid = البيد الحقيقي
        last = float(row["lastPrice"]) if pd.notna(row["lastPrice"]) and float(row["lastPrice"]) > 0 else float(row["bid"]) if pd.notna(row["bid"]) else 0
        bid = float(row["bid"]) if pd.notna(row["bid"]) else last
        if last <= 0:
            return None
        # نفس معادلة بوت الحيتان في صورتك:
        # Stop = Entry * 0.5
        # Target1 = Entry * 1.5 (+50%)
        # Target2 = Entry * 2.3 (+130%)
        # Target3 = Entry * 3.2 (+220%)
        entry = round(last, 2)
        stop = round(entry * 0.5, 2)
        t1 = round(entry * 1.5, 2)
        t2 = round(entry * 2.3, 2)
        t3 = round(entry * 3.2, 2)
        return {"ticker": ticker, "direction": direction, "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": entry, "bid": round(bid, 2), "stop": stop, "t1": t1, "t2": t2, "t3": t3}
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
        if df is None:
            continue
        direction = get_stock_signal(t, df)
        if direction is None:
            continue
        stock_price = num(df["Close"])
        reco = get_option_reco(t, stock_price, direction)
        if reco is not None:
            results.append(reco)
            if len(results) >= 5:
                break
    bar.empty()
    txt.empty()

    if len(results) == 0:
        st.warning("مافيه سلسلة أوبشن متاحة الحين - جرب بعد افتتاح السوق")
    else:
        st.success(f"طلع لك {len(results)} توصية أوبشن - بنفس ستايل بوت الحيتان")
        # رسالة واتساب كاملة بنفس الستايل
        msg_lines = []
        for m in results:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            msg_lines.append(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋")
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}")
            msg_lines.append(f"Entry: ${m['entry']} Bid: ${m['bid']}")
            msg_lines.append(f"Stop: ${m['stop']}")
            msg_lines.append(f"Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)")
            msg_lines.append("")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)
        if phone.strip() != "":
            st.link_button("📲 ارسل كل التوصيات واتساب", f"https://wa.me/{phone.strip()}?text={encoded}", use_container_width=True)
        else:
            st.link_button("📲 ارسل كل التوصيات واتساب", f"https://wa.me/?text={encoded}", use_container_width=True)
        st.code(msg_text, language="text")
        st.divider()
        for m in results:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            color = "green" if m["direction"] == "CALL" else "red"
            st.markdown(f"""
**{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋**  
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}  
Entry: ${m['entry']} Bid: ${m['bid']}  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)
""")
            st.divider()

st.divider()
st.caption("V13: توصية أوبشن حقيقية من سلسلة Yahoo - سترايك قريب من سعر السهم - Stop = نصف الدخول - الأهداف +50% / +130% / +220% مثل بوت الحيتان")
