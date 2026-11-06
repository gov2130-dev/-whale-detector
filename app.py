# V16.1 - كامل - يصلح فخ فوليوم اليوم = صفر في البري ماركت
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date, time
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V16.1")
st.caption("في البري ماركت: نفحص OI حق أمس، مو فوليوم اليوم - لأن فوليوم اليوم صفر والسوق مسكر")

GROUPS = {
    "🔵 الكبار - Mega": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","BRK-B","JPM","V","MA"],
    "🟣 أشباه الموصلات - Semis": ["AMD","SMCI","ARM","MU","QCOM","INTC","ASML","AMAT","LRCX","KLAC","AVGO"],
    "🟢 التكنولوجيا والنمو": ["PLTR","COIN","HOOD","NFLX","SHOP","SQ","CRWD","NET","DDOG","SNOW","AI","RBLX","UBER","LYFT"],
    "🟡 الطاقة والذهب": ["CVX","XOM","FSLR","ENPH","GDX","GLD","SLV","NEM","OXY","COP","DVN"],
    "🔴 الصحة والصناعة": ["LLY","UNH","BA","CAT","DE","GE","LMT","RTX","HON"],
    "🟠 الصين والميم": ["BABA","BIDU","PDD","JD","NIO","XPEV","GME","AMC","BB"],
}
ALL_TICKERS = list(dict.fromkeys([t for lst in GROUPS.values() for t in lst]))

# هل السوق فاتح ولا بري ماركت؟
sa_tz = pytz.timezone("Asia/Riyadh")
now_sa = datetime.now(sa_tz)
weekday = now_sa.weekday()
t_now = now_sa.time()
is_open = (weekday < 5) and (time(17,30) <= t_now <= time(23,59))

if is_open:
    st.success(f"✅ السوق فاتح - الساعة {now_sa.strftime('%H:%M')} - نفحص فوليوم اليوم")
    MODE = "LIVE"
else:
    st.error(f"⛔ السوق مسكر / بري ماركت - الساعة {now_sa.strftime('%H:%M')}")
    st.info("💡 فوليوم اليوم = صفر لأن السوق ما فتح. عشان كذا في V16.1 نفحص OI حق أمس، مو فوليوم اليوم. لو فحصنا فوليوم اليوم، بيطلع لك 0 تدفق مثل صورتك.")
    MODE = "OI"

def get_flows(ticker):
    cands = []
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return cands
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
            return cands
        for exp in exps[:8]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                if days < 1 or days > 7:  # وسعنا من 2-5 إلى 1-7 عشان الجمعة ما يضيع علينا الاثنين
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
                            if last <= 0:
                                continue
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 5:
                                continue
                            # --- هنا التصحيح ---
                            if MODE == "LIVE":
                                # السوق فاتح: نستخدم فوليوم اليوم
                                if vol < 300:
                                    continue
                                strength = vol
                                premium = vol * last * 100
                                label = f"Vol {int(vol)}"
                                # شروط اللايف
                                vol_ok = vol >= 1000
                                ratio = vol / (oi + 1)
                                ratio_ok = ratio >= 1.5
                            else:
                                # السوق مسكر: نستخدم OI حق أمس - فوليوم اليوم صفر، لا نستخدمه
                                if oi < 2000:  # OI أقل من 2000، هذا ريتيل
                                    continue
                                strength = oi
                                premium = oi * last * 100
                                label = f"OI {int(oi)}"
                                vol_ok = oi >= 5000  # OI كبير = حوت أمس
                                ratio_ok = True  # في البري ماركت ما نحسب Ratio، لأن Vol صفر
                                ratio = 0
                            if bid > 0 and ask > 0:
                                mid = (bid + ask) / 2
                                spread = (ask - bid) / (mid + 0.01) * 100
                            else:
                                spread = 0
                            premium_ok = premium >= 2000000
                            dist_ok = dist <= 2.0
                            spread_ok = spread <= 20 if MODE == "LIVE" else True  # في البري ماركت السبريد وهمي، لا نحاسبه
                            checks = []
                            checks.append(f"{label} {'✅' if vol_ok else '❌'}")
                            if MODE == "LIVE":
                                checks.append(f"Ratio {ratio:.1f} {'✅' if ratio_ok else '❌'}")
                            checks.append(f"Premium ${premium:,.0f} {'✅' if premium_ok else '❌'}")
                            checks.append(f"ATM {dist:.1f}% {'✅' if dist_ok else '❌'}")
                            if MODE == "LIVE":
                                checks.append(f"سبريد {spread:.1f}% {'✅' if spread_ok else '❌'}")
                            # النقاط: في البري ماركت 3 شروط، في اللايف 5 شروط
                            if MODE == "LIVE":
                                score = sum([vol_ok, ratio_ok, premium_ok, dist_ok, spread_ok])
                                max_score = 5
                            else:
                                score = sum([vol_ok, premium_ok, dist_ok])
                                max_score = 3
                            group_name = ""
                            for gn, gl in GROUPS.items():
                                if ticker in gl:
                                    group_name = gn
                                    break
                            cands.append({"ticker": ticker, "group": group_name, "direction": direction, "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(last, 2), "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium), "spread": round(spread, 1), "dist": round(dist, 2), "score": score, "max_score": max_score, "checks": " | ".join(checks), "mode": MODE})
                        except Exception:
                            continue
            except Exception:
                continue
        return cands
    except Exception:
        return cands

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")
selected_groups = st.multiselect("اختر المجموعات:", list(GROUPS.keys()), default=list(GROUPS.keys()))
tickers_to_scan = list(dict.fromkeys([t for g in selected_groups for t in GROUPS[g]]))
st.write(f"بنكمل فحص: **{len(tickers_to_scan)} سهم** | الوضع: **{'لايف - فوليوم اليوم' if MODE=='LIVE' else 'بري ماركت - OI أمس'}**")

if st.button(f"🔍 افحص {len(tickers_to_scan)} سهم", use_container_width=True):
    all_cands = []
    bar = st.progress(0)
    txt = st.empty()
    done = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(get_flows, t): t for t in tickers_to_scan}
        for fut in as_completed(futures):
            done += 1
            txt.text(f"فحصنا: {done}/{len(tickers_to_scan)}")
            bar.progress(done / len(tickers_to_scan))
            try:
                all_cands.extend(fut.result())
            except Exception:
                pass
    bar.empty()
    txt.empty()
    # نرتب حسب Premium
    all_cands = sorted(all_cands, key=lambda x: (x["score"], x["premium"]), reverse=True)
    if MODE == "LIVE":
        strong = [c for c in all_cands if c["score"] == 5][:5]
        near = [c for c in all_cands if c["score"] == 4][:8]
    else:
        strong = [c for c in all_cands if c["score"] == 3][:5]
        near = [c for c in all_cands if c["score"] == 2][:8]

    st.info(f"فحصنا {len(tickers_to_scan)} سهم | لقينا {len(all_cands)} تدفق | {len(strong)} حوت كامل | {len(near)} قريب")

    if len(strong) > 0:
        label = "5/5" if MODE=="LIVE" else "3/3 - OI أمس"
        st.success(f"🔥 حوت {label} في {len(strong)} سهم")
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
            msg_lines.append(f"Entry: ${m['entry']} (إغلاق أمس) OI: {m['oi']} Vol اليوم: {m['vol']} Flow: ${m['premium']:,}")
            msg_lines.append(f"Stop: ${m['stop']}")
            msg_lines.append(f"Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)")
            msg_lines.append("")
        msg_text = "\n".join(msg_lines)
        encoded = urllib.parse.quote(msg_text)
        if phone.strip() != "":
            st.link_button("📲 ارسل التوصيات واتساب", f"https://wa.me/{phone.strip()}?text={encoded}", use_container_width=True)
        else:
            st.link_button("📲 ارسل التوصيات واتساب", f"https://wa.me/?text={encoded}", use_container_width=True)
        st.code(msg_text, language="text")
        st.divider()
        for m in strong:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.markdown(f"""
**{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋 | {m['group']}**  
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}  
Entry: ${m['entry']} (إغلاق أمس) | OI: {m['oi']} | Vol اليوم: {m['vol']} | Flow: ${m['premium']:,}  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)  
**{m['checks']}**
""")
            st.divider()
    else:
        st.warning("مافيه حوت كامل - شوف القريب تحت.")

    if len(near) > 0:
        st.subheader("👀 أقرب حوت - مراقبة فقط")
        for m in near:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.warning(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} | {m['group']} | Exp: {m['exp']} ({m['days']}d) | Stock: ${m['stock']} | Entry: ${m['entry']} | OI: {m['oi']} | Premium: ${m['premium']:,} | {m['checks']}")

    if len(strong) == 0 and len(near) == 0:
        st.info("مافيه شي - كل التدفقات ضعيفة.")
        for m in all_cands[:3]:
            st.write(f"- {m['ticker']} {m['strike']} {m['direction']} | {m['checks']}")

st.divider()
st.caption("V16.1: في البري ماركت نستخدم OI أمس. في اللايف نستخدم Vol اليوم. عشان ما يطلع لك 0 تدفق مثل صورتك.")
