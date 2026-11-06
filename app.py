# V14 - كامل - تتبع صانع السوق من فلو الأوبشن، مو من سعر السهم
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V14")
st.caption("نبحث عن أثر صانع السوق في الأوبشن: فوليوم غير طبيعي + OI - التوصية ثابتة، ما تتغير كل نص ساعة")

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

def get_mm_flow(ticker):
    """
    نبحث عن صانع السوق: وين ضرب أكبر فوليوم؟
    القاعدة: صانع السوق = Volume أكبر من Open Interest + Volume كبير + بريميوم كبير
    هذا هو دخوله، مو سعر السهم.
    """
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return None
        # نفحص اكسبايريات 1-14 يوم فقط - هذا وين يلعب صانع السوق
        best_call = None
        best_put = None
        best_call_score = 0
        best_put_score = 0
        stock_price = 0
        try:
            # سعر السهم من fast_info - ثابت تقريباً بعد الإغلاق
            stock_price = float(tk.fast_info.get("lastPrice", 0) or 0)
            if stock_price == 0:
                df_hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
                if df_hist is not None and not df_hist.empty:
                    stock_price = num(df_hist["Close"])
        except Exception:
            pass
        if stock_price == 0:
            return None

        for exp in exps[:6]:  # أول 6 اكسبايريات فقط - عشان السرعة والثبات
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                if days < 0 or days > 14:
                    continue
                chain = tk.option_chain(exp)
                # --- CALLs ---
                if chain.calls is not None and not chain.calls.empty:
                    for _, row in chain.calls.iterrows():
                        try:
                            vol = float(row["volume"]) if pd.notna(row["volume"]) else 0
                            oi = float(row["openInterest"]) if pd.notna(row["openInterest"]) else 0
                            bid = float(row["bid"]) if pd.notna(row["bid"]) else 0
                            ask = float(row["ask"]) if pd.notna(row["ask"]) else 0
                            strike = float(row["strike"])
                            if vol < 200:  # أقل من 200 عقد، مو صانع سوق، هذا ريتيل
                                continue
                            if bid <= 0:
                                continue
                            # نسبة الفوليوم للـ OI: إذا الفوليوم أكبر من OI، معناها دخول جديد، مو تصفية قديمة
                            ratio = vol / (oi + 1)
                            if ratio < 0.8:  # لازم يكون دخول جديد قوي
                                continue
                            # قوة التدفق = فوليوم × بريميوم - هذا هو حجم فلوس صانع السوق
                            mid = (bid + ask) / 2 if ask > 0 else bid
                            premium = vol * mid * 100  # قيمة العقود بالدولار
                            # نفضل السترايك القريب من سعر السهم - صانع السوق يلعب ATM
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 8:  # أبعد من 8% عن السعر، مو صانع سوق
                                continue
                            score = premium * ratio
                            if score > best_call_score:
                                best_call_score = score
                                best_call = {"ticker": ticker, "direction": "CALL", "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(mid, 2), "bid": round(bid, 2), "ask": round(ask, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium)}
                        except Exception:
                            continue
                # --- PUTs ---
                if chain.puts is not None and not chain.puts.empty:
                    for _, row in chain.puts.iterrows():
                        try:
                            vol = float(row["volume"]) if pd.notna(row["volume"]) else 0
                            oi = float(row["openInterest"]) if pd.notna(row["openInterest"]) else 0
                            bid = float(row["bid"]) if pd.notna(row["bid"]) else 0
                            ask = float(row["ask"]) if pd.notna(row["ask"]) else 0
                            strike = float(row["strike"])
                            if vol < 200:
                                continue
                            if bid <= 0:
                                continue
                            ratio = vol / (oi + 1)
                            if ratio < 0.8:
                                continue
                            mid = (bid + ask) / 2 if ask > 0 else bid
                            premium = vol * mid * 100
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 8:
                                continue
                            score = premium * ratio
                            if score > best_put_score:
                                best_put_score = score
                                best_put = {"ticker": ticker, "direction": "PUT", "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(mid, 2), "bid": round(bid, 2), "ask": round(ask, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium)}
                        except Exception:
                            continue
            except Exception:
                continue

        # --- القرار: وين دخل صانع السوق أكثر؟ ---
        if best_call is None and best_put is None:
            return None
        if best_call is not None and best_put is None:
            return best_call
        if best_put is not None and best_call is None:
            return best_put
        # إذا فيه الاثنين، نأخذ الأقوى - اللي فلوسه أكبر
        # لازم يكون أقوى بـ 1.5 مرة على الأقل، عشان ما نعطي توصية متذبذبة
        if best_call_score > best_put_score * 1.5:
            return best_call
        if best_put_score > best_call_score * 1.5:
            return best_put
        # إذا الاثنين متقاربين، معناها صانع السوق محايد، ما نعطي توصية
        return None
    except Exception:
        return None

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")
st.info("💡 V14: ما نعتمد على سعر السهم. نعتمد على وين ضرب صانع السوق أكبر فوليوم في الأوبشن. عشان كذا التوصية ثابتة، تبحث 7 مرات يعطيك نفس الشي، سواء السوق فاتح ولا مسكر.")

if st.button("🔍 اكتشف وين دخل صانع السوق", use_container_width=True):
    results = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص فلو صانع السوق: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        reco = get_mm_flow(t)
        if reco is not None:
            # نحسب الوقف والأهداف من الدخول - نفس معادلة بوتك
            entry = reco["entry"]
            reco["stop"] = round(entry * 0.5, 2)
            reco["t1"] = round(entry * 1.5, 2)
            reco["t2"] = round(entry * 2.3, 2)
            reco["t3"] = round(entry * 3.2, 2)
            results.append(reco)
    bar.empty()
    txt.empty()
    # نرتب حسب قوة الفلوس - الأقوى أولاً
    results = sorted(results, key=lambda x: x["premium"], reverse=True)[:5]
    if len(results) == 0:
        st.warning("مافيه دخول واضح لصانع السوق الحين - الفوليوم كله ريتيل، مو حوت. لا تدخل شي.")
    else:
        st.success(f"صانع السوق دخل في {len(results)} سهم - هذي هي التوصيات الثابتة")
        msg_lines = []
        for m in results:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            msg_lines.append(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋")
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}")
            msg_lines.append(f"Entry: ${m['entry']} Bid: ${m['bid']} Vol: {m['vol']} OI: {m['oi']} Flow: ${m['premium']:,}")
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
            st.markdown(f"""
**{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋**  
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}  
Entry: ${m['entry']} Bid: ${m['bid']} Ask: ${m['ask']}  
**صانع السوق: Vol: {m['vol']} | OI: {m['oi']} | نسبة الدخول: {m['ratio']}x | فلوس التدفق: ${m['premium']:,}**  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)
""")
            st.divider()

st.divider()
st.caption("V14: صانع السوق = Vol > 200 عقد + Vol/OI > 0.8 + سترايك قريب من السعر + أكبر Premium. إذا CALL أقوى من PUT بـ 1.5 مرة، نعطي CALL، والعكس. إذا متقاربين، ما نعطي شي.")
