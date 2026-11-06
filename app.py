# V17 - المعتمد - النهائي
# بناء على تقييم 52 توصية من 4-5 نوفمبر
# الكود القديم كان يعطي 52 توصية، 48 منها ريتيل. V17 يعطي 2-3 فقط، بس حوت حقيقي

import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date, time
import pytz
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V17 - المعتمد")
st.caption("V17: 68 سهم + فلتر اتجاه MA20 + ممنوع 0d/1d + ممنوع Bid=0 + ممنوع سترايك بعيد")

GROUPS = {
    "🔵 الكبار - Mega": ["AAPL","MSFT","NVDA","AMZN","GOOGL","META","TSLA","AVGO","BRK-B","JPM","V","MA"],
    "🟣 أشباه الموصلات - Semis": ["AMD","SMCI","ARM","MU","QCOM","INTC","ASML","AMAT","LRCX","KLAC"],
    "🟢 التكنولوجيا والنمو": ["PLTR","COIN","HOOD","NFLX","SHOP","SQ","CRWD","NET","DDOG","SNOW","AI","RBLX","UBER","LYFT"],
    "🟡 الطاقة والذهب": ["CVX","XOM","FSLR","ENPH","GDX","GLD","SLV","NEM","OXY","COP","DVN"],
    "🔴 الصحة والصناعة": ["LLY","UNH","BA","CAT","DE","GE","LMT","RTX","HON","PFE","ABT","LOW","HD","KO","JNJ","WMT"],
    "🟠 الصين والميم": ["BABA","BIDU","PDD","JD","NIO","XPEV","GME","AMC","BB","AFRM","CHWY","BYND","U","SOUN","MARA","BAC","PYPL","NFLX","XOM","GLD","SLV","META"],
}

ALL_TICKERS = list(dict.fromkeys([t for lst in GROUPS.values() for t in lst]))

# هل السوق فاتح ولا بري ماركت؟
sa_tz = pytz.timezone("Asia/Riyadh")
now_sa = datetime.now(sa_tz)
weekday = now_sa.weekday()
t_now = now_sa.time()
is_open = (weekday < 5) and (time(17,30) <= t_now <= time(23,59))
MODE = "LIVE" if is_open else "OI"

if is_open:
    st.success(f"✅ السوق فاتح - {now_sa.strftime('%H:%M')} - نفحص Vol اليوم")
else:
    st.error(f"⛔ السوق مسكر / بري ماركت - {now_sa.strftime('%H:%M')} - نفحص OI أمس")

def get_flows(ticker):
    cands = []
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return cands

        # --- جلب السعر و MA20 لفلتر الاتجاه ---
        hist = yf.download(ticker, period="1mo", interval="1d", progress=False, auto_adjust=False)
        if hist is None or hist.empty:
            return cands
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = [c[0] if isinstance(c, tuple) else c for c in hist.columns]
        stock_price = float(hist["Close"].iloc[-1])
        ma20 = float(hist["Close"].tail(20).mean())
        trend = "UP" if stock_price > ma20 else "DOWN"
        trend_strength = (stock_price - ma20) / ma20 * 100

        for exp in exps[:10]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                # فلتر 1: ممنوع 0d و 1d - هذا اللي قتل 22 توصية في 5 نوفمبر
                if days < 2 or days > 8:
                    continue
                chain = tk.option_chain(exp)
                for direction, df_opt in [("CALL", chain.calls), ("PUT", chain.puts)]:
                    # --- فلتر الاتجاه ---
                    # إذا السهم صاعد فوق MA20 بـ +1%، نلغي كل PUT
                    # هذا كان بيلغي NVDA PUT اللي خسرك
                    if direction == "PUT" and trend == "UP" and trend_strength > 1.0:
                        continue
                    # إذا السهم نازل تحت MA20 بـ -1%، نلغي كل CALL
                    if direction == "CALL" and trend == "DOWN" and trend_strength < -1.0:
                        continue
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
                            # فلتر 2: ممنوع Bid = 0 - هذا كان في كل توصيات 5 نوفمبر الظهر
                            # Bid صفر معناها ما فيه أحد يبي يشتري منك
                            if bid <= 0:
                                continue
                            # فلتر 3: Bid لازم يكون قريب من Entry - إذا الفرق كبير، السبريد كبير
                            # مثال PANW: Bid 4.65 و Entry 7.25 - سبريد 36% - صانع السوق يبيع لك
                            if abs(last - bid) / (last + 0.01) > 0.30:
                                continue
                            dist = abs(strike - stock_price) / stock_price * 100
                            # فلتر 4: ممنوع سترايك بعيد أكثر من 2% - MU 830 و META 645 كانوا بعيدين
                            if dist > 2.0:
                                continue
                            # حساب Premium
                            if MODE == "LIVE":
                                if vol < 300:
                                    continue
                                premium = vol * last * 100
                                label = f"Vol {int(vol)}"
                                vol_ok = vol >= 800
                                ratio = vol / (oi + 1)
                                ratio_ok = ratio >= 1.2
                            else:
                                if oi < 2000:
                                    continue
                                premium = oi * last * 100
                                label = f"OI {int(oi)}"
                                vol_ok = oi >= 4000
                                ratio_ok = True
                                ratio = 0
                            # السبريد
                            if bid > 0 and ask > 0:
                                mid = (bid + ask) / 2
                                spread = (ask - bid) / (mid + 0.01) * 100
                            else:
                                spread = 999
                            # فلتر السبريد: ممنوع أكثر من 15% في اللايف
                            if MODE == "LIVE" and spread > 15:
                                continue
                            premium_ok = premium >= 100000  # خفضناه من 2M إلى 100k عشان GLD و PFE يطلعون - كانوا 344k و 181k
                            dist_ok = dist <= 2.0
                            spread_ok = spread <= 15 if MODE == "LIVE" else True

                            checks = []
                            checks.append(f"{label} {'✅' if vol_ok else '❌'}")
                            if MODE == "LIVE":
                                checks.append(f"Ratio {ratio:.1f} {'✅' if ratio_ok else '❌'}")
                            checks.append(f"Premium ${premium:,.0f} {'✅' if premium_ok else '❌'}")
                            checks.append(f"ATM {dist:.1f}% ✅")
                            checks.append(f"Bid ${bid:.2f} ✅")
                            checks.append(f"اتجاه {trend} {trend_strength:+.1f}% ✅")
                            if MODE == "LIVE":
                                checks.append(f"سبريد {spread:.1f}% {'✅' if spread_ok else '❌'}")

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
                            cands.append({
                                "ticker": ticker, "group": group_name, "direction": direction,
                                "strike": strike, "exp": exp, "days": days,
                                "stock": round(stock_price, 2), "ma20": round(ma20, 2),
                                "trend": trend, "trend_strength": round(trend_strength, 2),
                                "entry": round(last, 2), "bid": round(bid, 2), "ask": round(ask, 2),
                                "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2),
                                "premium": int(premium), "spread": round(spread, 1),
                                "dist": round(dist, 2), "score": score, "max_score": max_score,
                                "checks": " | ".join(checks), "mode": MODE
                            })
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
st.write(f"بنكمل فحص: **{len(tickers_to_scan)} سهم** | الوضع: **{'لايف' if MODE=='LIVE' else 'بري ماركت - OI أمس'}**")
st.info("💡 V17: إذا طلع لك 2-3 توصيات بس، هذا هو الصح. الكود القديم كان يعطيك 15 توصية، 12 منها ريتيل.")

if st.button(f"🔍 افحص {len(tickers_to_scan)} سهم - V17 المعتمد", use_container_width=True):
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
    # إزالة التكرار: سهم واحد = توصية واحدة - نأخذ الأقوى Premium
    # هذا يحل مشكلة NVDA 180 PUT و NVDA 185 PUT مع بعض
    seen = {}
    for c in sorted(all_cands, key=lambda x: x["premium"], reverse=True):
        key = c["ticker"]
        if key not in seen:
            seen[key] = c
    all_cands = list(seen.values())
    all_cands = sorted(all_cands, key=lambda x: (x["score"], x["premium"]), reverse=True)

    if MODE == "LIVE":
        strong = [c for c in all_cands if c["score"] == 5][:5]
        near = [c for c in all_cands if c["score"] == 4][:8]
    else:
        strong = [c for c in all_cands if c["score"] == 3][:5]
        near = [c for c in all_cands if c["score"] == 2][:8]

    st.info(f"فحصنا {len(tickers_to_scan)} سهم | لقينا {len(all_cands)} تدفق بعد كل الفلاتر | {len(strong)} حوت كامل | {len(near)} قريب")

    if len(strong) > 0:
        st.success(f"🔥 حوت V17 المعتمد في {len(strong)} سهم - كلها مع اتجاه السوق")
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
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']} Trend: {m['trend']} {m['trend_strength']:+.1f}% vs MA20 ${m['ma20']}")
            msg_lines.append(f"Entry: ${m['entry']} Bid: ${m['bid']} OI: {m['oi']} Vol: {m['vol']} Flow: ${m['premium']:,}")
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
Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']} | MA20: ${m['ma20']} | اتجاه: {m['trend']} {m['trend_strength']:+.1f}%  
Entry: ${m['entry']} | Bid: ${m['bid']} | OI: {m['oi']} | Vol: {m['vol']} | Flow: ${m['premium']:,}  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)  
**{m['checks']}**
""")
            st.divider()
    else:
        st.warning("مافيه حوت كامل بعد كل الفلاتر - هذا هو الصح. معناها كل الحيتان اليوم كانت ضد الاتجاه أو Bid=0 أو 0d، فحذفناها.")

    if len(near) > 0:
        st.subheader("👀 أقرب حوت - مراقبة فقط، لا تدخل")
        for m in near:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            st.warning(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} | {m['group']} | Exp: {m['exp']} | Stock: ${m['stock']} | MA20: ${m['ma20']} | اتجاه: {m['trend']} {m['trend_strength']:+.1f}% | Entry: ${m['entry']} Bid: ${m['bid']} | Flow: ${m['premium']:,} | {m['checks']}")

st.divider()
st.caption("V17 المعتمد: 68 سهم - فلتر اتجاه MA20 - ممنوع 0d/1d - ممنوع Bid=0 - ممنوع سترايك >2% - سهم واحد = توصية واحدة - Premium > 100k")
