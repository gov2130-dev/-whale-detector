# V15.1 - كامل - يوريك ليش رفضنا، ووش أقرب حوت
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V15.1")
st.caption("إذا مافيه حوت حقيقي، نوريك أقرب حوت وليش رفضناه - مو فراغ")

FAVORITE_OPTIONS = ["AAPL","MSFT","NVDA","TSLA","AMD","META","AMZN","GOOGL","COIN","PLTR","BABA","CVX","FSLR","ENPH","GDX","GLD","SLV"]

def get_all_flows(ticker):
    # نجيب كل التدفقات، حتى الضعيفة، عشان نشرح لك ليش رفضنا
    candidates = []
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return candidates
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
            return candidates
        for exp in exps[:8]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                if days < 2 or days > 5:
                    continue
                chain = tk.option_chain(exp)
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
                            if vol < 300:  # أقل من 300، هذا ريتيل صغير، نتجاهله
                                continue
                            ratio = vol / (oi + 1)
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 5:
                                continue
                            if bid <= 0 or ask <= 0 or last <= 0:
                                continue
                            mid = (bid + ask) / 2
                            spread = (ask - bid) / (mid + 0.01) * 100
                            premium = vol * last * 100
                            # نحسب كم شرط تحقق من 5
                            checks = []
                            if vol >= 1000:
                                checks.append("Vol ✅")
                            else:
                                checks.append(f"Vol {int(vol)} < 1000 ❌")
                            if ratio >= 2.0:
                                checks.append("Ratio ✅")
                            else:
                                checks.append(f"Ratio {ratio:.1f} < 2.0 ❌")
                            if premium >= 2000000:
                                checks.append("Premium ✅")
                            else:
                                checks.append(f"Premium ${premium:,.0f} < 2M ❌")
                            if dist <= 2.0:
                                checks.append("ATM ✅")
                            else:
                                checks.append(f"بعيد {dist:.1f}% ❌")
                            if spread <= 10:
                                checks.append("سبريد ✅")
                            else:
                                checks.append(f"سبريد {spread:.1f}% ❌")
                            score = sum([1 for c in checks if "✅" in c])
                            candidates.append({"ticker": ticker, "direction": direction, "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(last, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium), "spread": round(spread, 1), "dist": round(dist, 2), "score": score, "checks": " | ".join(checks)})
                        except Exception:
                            continue
            except Exception:
                continue
        return candidates
    except Exception:
        return candidates

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")
st.info("💡 V15.1: إذا طلع لك حوت 5/5، هذا دخول حقيقي. إذا طلع 4/5، هذا قريب، راقبه. إذا طلع 3/5 وأقل، هذا ريتيل، لا تدخل.")

if st.button("🔍 اكتشف دخول صانع السوق الحقيقي", use_container_width=True):
    all_cands = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        cands = get_all_flows(t)
        all_cands.extend(cands)
    bar.empty()
    txt.empty()
    # نرتب حسب النقاط ثم Premium
    all_cands = sorted(all_cands, key=lambda x: (x["score"], x["premium"]), reverse=True)
    strong = [c for c in all_cands if c["score"] == 5][:3]
    near = [c for c in all_cands if c["score"] == 4][:5]

    if len(strong) > 0:
        st.success(f"🔥 صانع السوق داخل بقوة في {len(strong)} سهم - 5/5 شروط")
        for m in strong:
            entry = m["entry"]
            m["stop"] = round(entry * 0.5, 2)
            m["t1"] = round(entry * 1.5, 2)
            m["t2"] = round(entry * 2.3, 2)
            m["t3"] = round(entry * 3.2, 2)
        msg_lines = []
        for m in strong:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            msg_lines.append(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋")
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}")
            msg_lines.append(f"Entry: ${m['entry']} Vol: {m['vol']} OI: {m['oi']} Ratio: {m['ratio']}x Flow: ${m['premium']:,}")
            msg_lines.append(f"Stop: ${m['stop']}")
            msg_lines.append(f"Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)")
            msg_lines.append("")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)
        if phone.strip() != "":
            st.link_button("📲 ارسل التوصيات القوية واتساب", f"https://wa.me/{phone.strip()}?text={encoded}", use_container_width=True)
        else:
            st.link_button("📲 ارسل التوصيات القوية واتساب", f"https://wa.me/?text={encoded}", use_container_width=True)
        st.code(msg_text, language="text")
        st.divider()
        for m in strong:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.markdown(f"""
**{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋 - 5/5 ✅**  
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}  
Entry: ${m['entry']} | Vol: {m['vol']} | OI: {m['oi']} | Ratio: {m['ratio']}x | Flow: ${m['premium']:,} | سبريد: {m['spread']}%  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)  
**{m['checks']}**
""")
            st.divider()
    else:
        st.warning("مافيه حوت 5/5 اليوم - هذا هو الصح، مو فراغ. شوف أقرب حوت تحت، وليش رفضناه.")

    if len(near) > 0:
        st.subheader("👀 أقرب حوت - 4/5 شروط - مراقبة فقط، لا تدخل")
        st.caption("هذي الأسهم ناقصها شرط واحد بس. إذا تحقق الشرط الناقص بكرة، بتتحول لـ 5/5 وبتطلع لك فوق كتوصية قوية.")
        for m in near:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.warning(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} | Exp: {m['exp']} ({m['days']}d) | Stock: ${m['stock']} | Entry لو كان قوي: ${m['entry']} | Vol: {m['vol']} | Premium: ${m['premium']:,} | **ناقصه: {m['checks']}**")

    if len(strong) == 0 and len(near) == 0:
        st.info("كل التدفقات اليوم أقل من 4/5 - كلها ريتيل. لا تدخل شي اليوم. هذا أفضل من انك تدخل وتخسر 50% مثل QQQ أمس.")
        # نوريك أقوى 3 حتى لو 3/5، عشان تعرف وش صار
        top3 = all_cands[:3]
        for m in top3:
            st.write(f"- {m['ticker']} {m['strike']} {m['direction']} | نقاط: {m['score']}/5 | {m['checks']}")

st.divider()
st.caption("V15.1: 5/5 = دخول. 4/5 = مراقبة. أقل من 4 = ريتيل. نوريك ليش رفضنا، عشان ما تحس انه فراغ.")
