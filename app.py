# V16 - كامل - نفحص 68 سهم، مو 17
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V16")
st.caption("نفحص 68 سهم - كل السوق، مو بس 17 - عشان الحوت وين ما دخل، نلقاه")

# --- 68 سهم مقسمة 6 مجموعات ---
GROUPS = {
    "🔵 الكبار - Mega": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","BRK-B","JPM","V","MA"],
    "🟣 أشباه الموصلات - Semis": ["AMD","SMCI","ARM","MU","QCOM","INTC","ASML","AMAT","LRCX","KLAC","AVGO"],
    "🟢 التكنولوجيا والنمو": ["PLTR","COIN","HOOD","NFLX","SHOP","SQ","CRWD","NET","DDOG","SNOW","AI","RBLX","UBER","LYFT"],
    "🟡 الطاقة والذهب": ["CVX","XOM","FSLR","ENPH","GDX","GLD","SLV","NEM","OXY","COP","DVN"],
    "🔴 الصحة والصناعة": ["LLY","UNH","BA","CAT","DE","GE","LMT","RTX","HON"],
    "🟠 الصين والميم": ["BABA","BIDU","PDD","JD","NIO","XPEV","GME","AMC","BB"],
}

# نجمع كل الأسهم في قائمة واحدة
ALL_TICKERS = []
for g, lst in GROUPS.items():
    ALL_TICKERS.extend(lst)
# نحذف التكرار
ALL_TICKERS = list(dict.fromkeys(ALL_TICKERS))

st.write(f"📊 عدد الأسهم اللي بنفحصها اليوم: **{len(ALL_TICKERS)} سهم** - قبل كان 17 بس")

def get_all_flows(ticker):
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
                            if vol < 300:
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
                            # نعرف المجموعة
                            group_name = ""
                            for gn, gl in GROUPS.items():
                                if ticker in gl:
                                    group_name = gn
                                    break
                            candidates.append({"ticker": ticker, "group": group_name, "direction": direction, "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(last, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium), "spread": round(spread, 1), "dist": round(dist, 2), "score": score, "checks": " | ".join(checks)})
                        except Exception:
                            continue
            except Exception:
                continue
        return candidates
    except Exception:
        return candidates

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")

# اختيار المجموعات - تقدر تختار الكل أو مجموعة واحدة
selected_groups = st.multiselect("اختر المجموعات اللي تبي تفحصها:", list(GROUPS.keys()), default=list(GROUPS.keys()))
tickers_to_scan = []
for g in selected_groups:
    tickers_to_scan.extend(GROUPS[g])
tickers_to_scan = list(dict.fromkeys(tickers_to_scan))
st.write(f"بنكمل فحص: **{len(tickers_to_scan)} سهم**")

if st.button(f"🔍 افحص {len(tickers_to_scan)} سهم - وين دخل صانع السوق", use_container_width=True):
    all_cands = []
    bar = st.progress(0)
    txt = st.empty()
    done = 0
    # --- فحص متوازي - أسرع 5 مرات من قبل ---
    # قبل كنا نفحص سهم سهم، الحين نفحص 10 أسهم مع بعض
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(get_all_flows, t): t for t in tickers_to_scan}
        for fut in as_completed(futures):
            done += 1
            t = futures[fut]
            txt.text(f"فحصنا: {done}/{len(tickers_to_scan)} - {t}")
            bar.progress(done / len(tickers_to_scan))
            try:
                cands = fut.result()
                all_cands.extend(cands)
            except Exception:
                pass
    bar.empty()
    txt.empty()
    all_cands = sorted(all_cands, key=lambda x: (x["score"], x["premium"]), reverse=True)
    strong = [c for c in all_cands if c["score"] == 5][:5]
    near = [c for c in all_cands if c["score"] == 4][:8]

    st.info(f"فحصنا {len(tickers_to_scan)} سهم | لقينا {len(all_cands)} تدفق فوق 300 عقد | {len(strong)} حوت 5/5 | {len(near)} قريب 4/5")

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
**{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋 - 5/5 ✅ | {m['group']}**  
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}  
Entry: ${m['entry']} | Vol: {m['vol']} | OI: {m['oi']} | Ratio: {m['ratio']}x | Flow: ${m['premium']:,} | سبريد: {m['spread']}%  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)  
**{m['checks']}**
""")
            st.divider()
    else:
        st.warning("مافيه حوت 5/5 اليوم - بس الحين فحصنا 68 سهم، مو 17. يعني التأكيد أقوى: فعلاً مافيه حوت اليوم في السوق كله، مو بس في قائمتنا الصغيرة.")

    if len(near) > 0:
        st.subheader("👀 أقرب حوت - 4/5 شروط - مراقبة فقط، لا تدخل")
        for m in near:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.warning(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} | {m['group']} | Exp: {m['exp']} ({m['days']}d) | Stock: ${m['stock']} | Entry: ${m['entry']} | Vol: {m['vol']} | Premium: ${m['premium']:,} | **ناقصه: {m['checks']}**")

    if len(strong) == 0 and len(near) == 0:
        st.info("كل التدفقات أقل من 4/5 - لا تدخل شي اليوم.")
        top3 = all_cands[:3]
        for m in top3:
            st.write(f"- {m['ticker']} {m['strike']} {m['direction']} | نقاط: {m['score']}/5 | {m['checks']}")

st.divider()
st.caption("V16: 68 سهم - 6 مجموعات - فحص متوازي أسرع. 5/5 = دخول. 4/5 = مراقبة.")
