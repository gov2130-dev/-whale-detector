# V15 - كامل - شروط حازمة لصانع السوق
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V15 - شروط حازمة")
st.caption("لا توصية إلا إذا صانع السوق داخل بقوة: Vol > 2x OI + Premium > 2M + سترايك ATM + اكسبايري 2-5 أيام + سبريد < 10%")

# حذفنا SPY و QQQ - هذي تحوط، مو اتجاه، وهي اللي خسرتك أمس
FAVORITE_OPTIONS = ["AAPL","MSFT","NVDA","TSLA","AMD","META","AMZN","GOOGL","COIN","PLTR","BABA","CVX","FSLR","ENPH","GDX","GLD","SLV"]

def get_mm_flow_strict(ticker):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return None, ""
        stock_price = 0
        try:
            stock_price = float(tk.fast_info.get("lastPrice", 0) or 0)
            if stock_price == 0:
                df_hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
                if df_hist is not None and not df_hist.empty:
                    if isinstance(df_hist.columns, pd.MultiIndex):
                        df_hist.columns = [c[0] if isinstance(c, tuple) else c for c in df_hist.columns]
                    stock_price = float(df_hist["Close"].iloc[-1])
        except Exception:
            pass
        if stock_price == 0:
            return None, ""

        best = None
        best_score = 0
        best_reason = ""

        for exp in exps[:8]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                # شرط 4: اكسبايري 2-5 أيام فقط - ممنوع 0d و 1d اللي يقتل العقد
                if days < 2 or days > 5:
                    continue
                chain = tk.option_chain(exp)
                # نفحص CALL و PUT
                for direction, df_opt in [("CALL", chain.calls), ("PUT", chain.puts)]:
                    if df_opt is None or df_opt.empty:
                        continue
                    for _, row in df_opt.iterrows():
                        try:
                            vol = float(row["volume"]) if pd.notna(row["volume"]) else 0
                            oi = float(row["openInterest"]) if pd.notna(row["openInterest"]) else 0
                            bid = float(row["bid"]) if pd.notna(row["bid"]) else 0
                            ask = float(row["ask"]) if pd.notna(row["ask"]) else 0
                            last = float(row["lastPrice"]) if pd.notna(row["lastPrice"]) else 0
                            strike = float(row["strike"])
                            # شرط 1: Vol > 1000 عقد
                            if vol < 1000:
                                continue
                            # شرط 1: Vol > 2x OI - دخول جديد ضخم
                            ratio = vol / (oi + 1)
                            if ratio < 2.0:
                                continue
                            # شرط 3: سترايك قريب - أقل من 2% من السعر
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 2.0:
                                continue
                            # شرط 5: سبريد ضيق - أقل من 10%
                            if bid <= 0 or ask <= 0:
                                continue
                            mid_live = (bid + ask) / 2
                            spread = (ask - bid) / (mid_live + 0.01) * 100
                            if spread > 10:
                                continue
                            # سعر الدخول: نستخدم lastPrice إذا كان السوق مسكر، و Mid إذا كان فاتح والسبريد ضيق
                            # نستخدم lastPrice دائماً في V15 عشان ما ننخدع بالبري ماركت
                            if last <= 0:
                                continue
                            entry_price = last
                            # شرط 2: Premium > 2 مليون دولار
                            premium = vol * entry_price * 100
                            if premium < 2000000:
                                continue
                            # كل الشروط تحققت - هذا هو صانع السوق الحقيقي
                            score = premium * ratio
                            if score > best_score:
                                best_score = score
                                best = {"ticker": ticker, "direction": direction, "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(entry_price, 2), "bid": round(bid, 2), "ask": round(ask, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium), "spread": round(spread, 1), "dist": round(dist, 2)}
                                best_reason = f"Vol {int(vol)} = {ratio:.1f}x OI | Premium ${premium:,.0f} | سترايك {dist:.1f}% من السعر | سبريد {spread:.1f}%"
                        except Exception:
                            continue
            except Exception:
                continue

        # إذا لقينا CALL و PUT الاثنين، نأخذ الأقوى بفرق كبير
        # هنا نحن نأخذ الأقوى فقط من كل الاتجاهين في الحلقة فوق
        return best, best_reason
    except Exception:
        return None, ""

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")
st.error("⚠️ درس أمس: QQQ PUT و SPY PUT خسروا 50-70% لأن SPY و QQQ تحوط، مو اتجاه. صانع السوق كان يبيع لك، مو يشتري معك. في V15 حذفناهم.")
st.info("💡 قاعدة V15: إذا ما طلعت توصية، معناها صانع السوق ما دخل بقوة اليوم. لا تدخل شي. الدخول الضعيف هو اللي يصفر العقد.")

if st.button("🔍 اكتشف دخول صانع السوق الحقيقي", use_container_width=True):
    results = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص بشروط حازمة: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        reco, reason = get_mm_flow_strict(t)
        if reco is not None:
            entry = reco["entry"]
            reco["stop"] = round(entry * 0.5, 2)
            reco["t1"] = round(entry * 1.5, 2)
            reco["t2"] = round(entry * 2.3, 2)
            reco["t3"] = round(entry * 3.2, 2)
            reco["reason"] = reason
            results.append(reco)
    bar.empty()
    txt.empty()
    results = sorted(results, key=lambda x: x["premium"], reverse=True)[:3]  # نعطي 3 فقط، الأقوى
    if len(results) == 0:
        st.warning("مافيه دخول حقيقي لصانع السوق اليوم - كل الفوليوم ضعيف أو ريتيل أو تحوط. لا تدخل شي اليوم. هذا هو الصح.")
        st.caption("قبل V15 كنا نعطيك أي فوليوم، حتى لو ضعيف، عشان كذا كنت تدخل وتخسر. الحين إذا ما فيه حوت حقيقي، ما نعطيك شي.")
    else:
        st.success(f"صانع السوق داخل بقوة في {len(results)} سهم فقط - هذي توصيات حازمة، مو أي فوليوم")
        msg_lines = []
        for m in results:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            msg_lines.append(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋")
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}")
            msg_lines.append(f"Entry: ${m['entry']} (إغلاق أمس) Vol: {m['vol']} OI: {m['oi']} Ratio: {m['ratio']}x Flow: ${m['premium']:,}")
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
Entry: ${m['entry']} (إغلاق أمس)  
**🔥 إثبات صانع السوق: {m['reason']}**  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)
""")
            st.divider()
            st.caption("⚠️ قاعدة الدخول: لا تدخل في أول 15 دقيقة. انتظر السهم يثبت فوق سعر الدخول للـ CALL أو تحت سعر الدخول للـ PUT. إذا نزل 30% من الدخول، اخرج فوراً، لا تنتظر الوقف. صانع السوق إذا دخل صح، السهم ما ينزل 70% ثاني يوم.")

st.divider()
st.caption("V15: شروط حازمة - Vol > 1000 + Vol/OI > 2x + Premium > 2M + سترايك < 2% + اكسبايري 2-5 أيام + سبريد < 10%. حذف SPY و QQQ. نعطي 3 توصيات فقط.")
