# V14.1 - كامل - نمنع Bid/Ask الوهمي في البري ماركت
import streamlit as st
import yfinance as yf
import pandas as pd
import urllib.parse
from datetime import datetime, date, time
import pytz

st.set_page_config(page_title="حيتان صانع السوق", layout="wide")
st.title("🐋 حيتان صانع السوق - V14.1")
st.caption("الدخول من إغلاق أمس فقط - ممنوع Bid/Ask في البري ماركت - لأن السبريد وهمي")

FAVORITE_OPTIONS = ["SPY","QQQ","AAPL","MSFT","NVDA","TSLA","AMD","META","AMZN","GOOGL","GDX","GLD","SLV","FSLR","ENPH","BABA","BIDU","CVX","COIN","PLTR"]

def get_market_status():
    sa_tz = pytz.timezone("Asia/Riyadh")
    now_sa = datetime.now(sa_tz)
    weekday = now_sa.weekday()
    t = now_sa.time()
    open_t = time(17, 30)
    close_t = time(23, 59)
    is_weekend = weekday >= 5
    is_open = (not is_weekend) and (open_t <= t <= close_t)
    return is_open, now_sa

is_open, now_sa = get_market_status()

if not is_open:
    st.error(f"⛔ السوق مسكر / بري ماركت - الساعة عندك {now_sa.strftime('%H:%M')}")
    st.warning("في البري ماركت، صانع السوق يوسع السبريد عشان يخدعك. مثال: Bid 1$ و Ask 19$، المنتصف يطلع 10$، وهذا وهم. عشان كذا في V14.1 نمنع استخدام Bid/Ask الحين، ونستخدم سعر إغلاق أمس فقط.")
    st.info("التوصيات اللي تحت هي على إغلاق أمس، مو على أسعار البري ماركت الوهمية. إذا دخلت، ادخل على سعر الافتتاح الحقيقي، مو على السعر المكتوب هنا.")
else:
    st.success(f"✅ السوق فاتح - الساعة {now_sa.strftime('%H:%M')} - الأسعار الحين حقيقية")

def get_mm_flow(ticker, use_live):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options
        if not exps:
            return None
        best_call = None
        best_put = None
        best_call_score = 0
        best_put_score = 0
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
            return None
        for exp in exps[:6]:
            try:
                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - date.today()).days
                if days < 0 or days > 14:
                    continue
                chain = tk.option_chain(exp)
                # CALLs
                if chain.calls is not None and not chain.calls.empty:
                    for _, row in chain.calls.iterrows():
                        try:
                            vol = float(row["volume"]) if pd.notna(row["volume"]) else 0
                            oi = float(row["openInterest"]) if pd.notna(row["openInterest"]) else 0
                            bid = float(row["bid"]) if pd.notna(row["bid"]) else 0
                            ask = float(row["ask"]) if pd.notna(row["ask"]) else 0
                            last = float(row["lastPrice"]) if pd.notna(row["lastPrice"]) else 0
                            strike = float(row["strike"])
                            if vol < 200:
                                continue
                            ratio = vol / (oi + 1)
                            if ratio < 0.8:
                                continue
                            # --- هنا التصحيح ---
                            # إذا السوق مسكر: نستخدم lastPrice فقط - سعر إغلاق أمس الحقيقي
                            # إذا السوق فاتح: نستخدم منتصف Bid/Ask - لأنه حقيقي الحين
                            if use_live:
                                if bid <= 0:
                                    continue
                                # في السوق الفاتح، إذا السبريد أكبر من 30% من السعر، نتجاهله - هذا تلاعب
                                spread = (ask - bid) / ((bid + ask)/2 + 0.01) * 100
                                if spread > 30:
                                    continue
                                entry_price = (bid + ask) / 2
                                bid_show = round(bid, 2)
                            else:
                                if last <= 0:
                                    continue
                                entry_price = last
                                bid_show = round(last, 2)  # في البري ماركت، نعرض إغلاق أمس كـ Bid، مو Bid الوهمي
                            premium = vol * entry_price * 100
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 8:
                                continue
                            score = premium * ratio
                            if score > best_call_score:
                                best_call_score = score
                                best_call = {"ticker": ticker, "direction": "CALL", "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(entry_price, 2), "bid": bid_show, "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium)}
                        except Exception:
                            continue
                # PUTs
                if chain.puts is not None and not chain.puts.empty:
                    for _, row in chain.puts.iterrows():
                        try:
                            vol = float(row["volume"]) if pd.notna(row["volume"]) else 0
                            oi = float(row["openInterest"]) if pd.notna(row["openInterest"]) else 0
                            bid = float(row["bid"]) if pd.notna(row["bid"]) else 0
                            ask = float(row["ask"]) if pd.notna(row["ask"]) else 0
                            last = float(row["lastPrice"]) if pd.notna(row["lastPrice"]) else 0
                            strike = float(row["strike"])
                            if vol < 200:
                                continue
                            ratio = vol / (oi + 1)
                            if ratio < 0.8:
                                continue
                            if use_live:
                                if bid <= 0:
                                    continue
                                spread = (ask - bid) / ((bid + ask)/2 + 0.01) * 100
                                if spread > 30:
                                    continue
                                entry_price = (bid + ask) / 2
                                bid_show = round(bid, 2)
                            else:
                                if last <= 0:
                                    continue
                                entry_price = last
                                bid_show = round(last, 2)
                            premium = vol * entry_price * 100
                            dist = abs(strike - stock_price) / stock_price * 100
                            if dist > 8:
                                continue
                            score = premium * ratio
                            if score > best_put_score:
                                best_put_score = score
                                best_put = {"ticker": ticker, "direction": "PUT", "strike": strike, "exp": exp, "days": days, "stock": round(stock_price, 2), "entry": round(entry_price, 2), "bid": bid_show, "vol": int(vol), "oi": int(oi), "ratio": round(ratio, 2), "premium": int(premium)}
                        except Exception:
                            continue
            except Exception:
                continue
        if best_call is None and best_put is None:
            return None
        if best_call is not None and best_put is None:
            return best_call
        if best_put is not None and best_call is None:
            return best_put
        if best_call_score > best_put_score * 1.5:
            return best_call
        if best_put_score > best_call_score * 1.5:
            return best_put
        return None
    except Exception:
        return None

st.subheader("📲 ارسال للواتساب")
phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")

if st.button("🔍 اكتشف وين دخل صانع السوق", use_container_width=True):
    results = []
    bar = st.progress(0)
    txt = st.empty()
    for i, t in enumerate(FAVORITE_OPTIONS):
        txt.text(f"يفحص فلو صانع السوق: {t} - {i+1}/{len(FAVORITE_OPTIONS)}")
        bar.progress((i + 1) / len(FAVORITE_OPTIONS))
        reco = get_mm_flow(t, use_live=is_open)
        if reco is not None:
            entry = reco["entry"]
            reco["stop"] = round(entry * 0.5, 2)
            reco["t1"] = round(entry * 1.5, 2)
            reco["t2"] = round(entry * 2.3, 2)
            reco["t3"] = round(entry * 3.2, 2)
            results.append(reco)
    bar.empty()
    txt.empty()
    results = sorted(results, key=lambda x: x["premium"], reverse=True)[:5]
    if len(results) == 0:
        st.warning("مافيه دخول واضح لصانع السوق الحين.")
    else:
        label = "سعر لايف" if is_open else "سعر إغلاق أمس - لا تدخل على هذا السعر، انتظر الافتتاح"
        st.success(f"صانع السوق دخل في {len(results)} سهم - الدخول محسوب على: {label}")
        msg_lines = []
        for m in results:
            emoji = "🟢" if m["direction"] == "CALL" else "🔴"
            msg_lines.append(f"{emoji} {m['ticker']} {m['strike']} {m['direction']} 🐋")
            msg_lines.append(f"Exp: {m['exp']} ({m['days']}d) Stock: ${m['stock']}")
            msg_lines.append(f"Entry: ${m['entry']} ({label}) Vol: {m['vol']} OI: {m['oi']} Flow: ${m['premium']:,}")
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
Entry: ${m['entry']} ({label}) | Vol: {m['vol']} | OI: {m['oi']} | Flow: ${m['premium']:,}  
Stop: ${m['stop']}  
Target: ${m['t1']} (+50%) | ${m['t2']} (+130%) | ${m['t3']} (+220%)
""")
            st.divider()

st.divider()
st.caption("V14.1: في البري ماركت نستخدم lastPrice فقط. في السوق الفاتح نستخدم Bid/Ask بشرط السبريد أقل من 30%. إذا السبريد وهمي، نتجاهل الأوبشن.")
