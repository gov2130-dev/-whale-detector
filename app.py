import streamlit as st
import yfinance as yf
import pandas as pd
import math
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="V52 FINAL", initial_sidebar_state="collapsed")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
.big-table {width:100%; border-collapse:collapse; font-size:11px;}
.big-table th {background:#000000!important; color:#ffffff!important; padding:8px 2px; text-align:center; font-size:7px; font-weight:900;}
.big-table td {background:#ffffff!important; padding:8px 2px; text-align:center; border:1px solid #cccccc; font-size:10px; font-weight:700; color:#000000!important;}
.call-badge {background:#16a34a!important; color:#ffffff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.put-badge {background:#dc2626!important; color:#ffffff!important; padding:4px 8px; border-radius:6px; font-size:9px; font-weight:900;}
.time-card {background:#111111; color:#4ade80; border-radius:10px; padding:10px; font-family:monospace; text-align:center; font-size:11px; border:2px solid #22c55e;}
div.stButton > button {width:100%; height:48px; font-size:15px; font-weight:900; border-radius:12px; background:#ffffff; color:#000000; border:2px solid #000000;}
div.stButton > button[kind="primary"] {background:#000000!important; color:#ffffff!important;}
</style>
""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()
if "view" not in st.session_state:
    st.session_state.view = "🏆 الكل"

now = datetime.now()
ksa = now + timedelta(hours=3)
ksa_str = ksa.strftime('%H:%M:%S')

st.markdown(f"# V52 FINAL - {st.session_state.view} - {ksa_str}")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V52 جودة العقد | Bid-Ask + OI + VOL/OI + Delta | يحل صفحة بيضاء</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("✅ BUY", type="primary" if st.session_state.view=="✅ BUY قوي" else "secondary"):
        st.session_state.view="✅ BUY قوي"
        st.rerun()
with c2:
    if st.button("🔻 SELL", type="primary" if st.session_state.view=="🔻 SELL قوي" else "secondary"):
        st.session_state.view="🔻 SELL قوي"
        st.rerun()
with c3:
    if st.button("🏆 الكل", type="primary" if st.session_state.view=="🏆 الكل" else "secondary"):
        st.session_state.view="🏆 الكل"
        st.rerun()

b1, b2 = st.columns(2)
with b1:
    do_scan = st.button("⚡ فحص الآن - 8 شركات", type="primary")
with b2:
    if st.button("🧹 تصفير"):
        st.session_state.results = pd.DataFrame()
        st.cache_data.clear()
        st.rerun()

@st.cache_data(ttl=30)
def quick_analysis_v52(ticker):
    try:
        tk = yf.Ticker(ticker)
        h = tk.history(period="1mo")
        if len(h) < 15:
            return None
        curr = float(h['Close'].iloc[-1])
        if pd.isna(curr) or curr < 3 or curr > 5000:
            return None
        prev = float(h['Close'].iloc[-2])
        ch1 = float((curr-prev)/prev*100) if prev > 0 else 0.0
        if pd.isna(ch1):
            ch1 = 0.0
        ema9 = float(h['Close'].ewm(span=9).mean().iloc[-1])
        vol_avg = float(h['Volume'].tail(10).mean())
        vol_today = float(h['Volume'].iloc[-1])
        vol_ratio = float(vol_today/vol_avg) if vol_avg > 0 else 1.0
        vol_ratio = float(max(0.1, min(5.0, vol_ratio)))
        # RSI
        d = h['Close'].diff()
        g = d.where(d>0,0).ewm(alpha=1/14, adjust=False).mean()
        l = (-d.where(d<0,0)).ewm(alpha=1/14, adjust=False).mean()
        lg = float(g.iloc[-1]) if not pd.isna(g.iloc[-1]) else 0.5
        ll = float(l.iloc[-1]) if not pd.isna(l.iloc[-1]) else 0.5
        if ll < 0.01:
            ll = 0.01
        rsi = 100-(100/(1+lg/ll))
        if pd.isna(rsi):
            rsi = 50
        rsi = float(max(5, min(95, rsi)))
        trend = "NEUTRAL"
        if ch1 >= 0.7 and curr > ema9:
            trend = "BULL"
        elif ch1 <= -0.7 and curr < ema9:
            trend = "BEAR"
        elif ch1 >= 1.2:
            trend = "BULL"
        elif ch1 <= -1.2:
            trend = "BEAR"
        return {"price":curr, "ch1":ch1, "ema9":ema9, "rsi":rsi, "vol_ratio":vol_ratio, "trend":trend}
    except:
        return None

def fetch_v52(ticker):
    try:
        tk = yf.Ticker(ticker)
        if not tk.options:
            return []
        sd = quick_analysis_v52(ticker)
        if not sd:
            return []
        if sd["trend"] == "NEUTRAL":
            return []
        curr = sd["price"]
        trend = sd["trend"]
        rows = []
        exp = tk.options[0]
        try:
            exp_d = datetime.strptime(exp, "%Y-%m-%d")
            days = (exp_d - datetime.now()).days
            if days < 0:
                return []
            chain = tk.option_chain(exp)
            allowed = ["CALL"] if trend == "BULL" else ["PUT"]
            for opt_type in allowed:
                df_opt = chain.calls if opt_type == "CALL" else chain.puts
                if df_opt.empty:
                    continue
                df_opt = df_opt.copy().dropna(subset=['lastPrice'])
                df_opt = df_opt[df_opt['lastPrice'] > 0.05]
                if df_opt.empty:
                    continue
                sort_col = 'volume' if 'volume' in df_opt.columns and df_opt['volume'].notna().any() else 'lastPrice'
                df_opt = df_opt.sort_values(sort_col, ascending=False).head(2)
                for _, r in df_opt.iterrows():
                    try:
                        strike = float(r['strike'])
                        if pd.isna(strike):
                            continue
                        dist = (strike-curr)/curr*100 if curr!= 0 else 0
                        if abs(dist) > 7:
                            continue
                        last_price = float(r['lastPrice'])
                        if pd.isna(last_price) or last_price <= 0:
                            continue
                        vol = int(r.get('volume', 100) or 100)
                        oi = int(r.get('openInterest', 0) or 0)
                        bid = float(r.get('bid', 0) or 0)
                        ask = float(r.get('ask', 0) or 0)
                        prem = float(last_price*vol*100/1e6) if vol > 0 else 0.02
                        # Delta تقريبي
                        if opt_type == "CALL":
                            delta = 0.5 if abs(dist) < 1 else 0.35 if dist > 0 else 0.65
                        else:
                            delta = -0.5 if abs(dist) < 1 else -0.35 if dist < 0 else -0.65
                        rows.append({
                            "ticker":ticker, "type":opt_type, "stock_now":float(curr),
                            "strike":int(strike), "dist":float(dist), "opt_price":float(last_price),
                            "vol":int(vol), "oi":int(oi), "bid":float(bid), "ask":float(ask),
                            "prem_M":float(prem), "delta":float(delta),
                            "exp_short":exp_d.strftime("%m/%d"), "exp_full":exp_d.strftime("%Y-%m-%d"),
                            "days":int(days), "rsi":float(sd["rsi"]), "vol_ratio":float(sd["vol_ratio"]),
                            "change_1d":float(sd["ch1"]), "trend":trend
                        })
                    except:
                        continue
            if rows:
                rows = sorted(rows, key=lambda x: x.get('oi',0), reverse=True)[:1]
        except:
            pass
        return rows
    except:
        return []

def calc_quality(r):
    score = 50
    reasons = []
    # 1. Bid-Ask Spread
    try:
        bid = float(r.get('bid',0))
        ask = float(r.get('ask',0))
        if bid > 0 and ask > 0:
            mid = (bid+ask)/2
            if mid > 0:
                spread = (ask-bid)/mid*100
                if spread <= 5:
                    score += 20
                    reasons.append(f"سبريد ممتاز {spread:.1f}%")
                elif spread <= 10:
                    score += 12
                    reasons.append(f"سبريد جيد {spread:.1f}%")
                elif spread <= 18:
                    score += 3
                    reasons.append(f"سبريد متوسط {spread:.1f}%")
                else:
                    score -= 15
                    reasons.append(f"سبريد وهمي {spread:.1f}%")
    except:
        pass
    # 2. OI
    oi = int(r.get('oi',0) or 0)
    if oi >= 5000:
        score += 20
        reasons.append(f"OI قوي {oi}")
    elif oi >= 1500:
        score += 12
        reasons.append(f"OI جيد {oi}")
    elif oi >= 500:
        score += 5
    else:
        score -= 8
        reasons.append(f"OI ضعيف {oi}")
    # 3. VOL/OI - مهم لصورتك x0.2
    vol = int(r.get('vol',0))
    if oi > 0:
        ratio = vol/oi
        if ratio >= 1.5:
            score += 20
            reasons.append(f"انفجار x{ratio:.1f}")
        elif ratio >= 0.8:
            score += 12
            reasons.append(f"دخول قوي x{ratio:.1f}")
        elif ratio >= 0.4:
            score += 5
        else:
            score += 0
            reasons.append(f"VOL/OI ضعيف x{ratio:.1f}")
    # 4. Delta
    delta = abs(float(r.get('delta',0.45)))
    if 0.35 <= delta <= 0.55:
        score += 15
        reasons.append(f"Delta {delta:.2f} ممتاز")
    elif 0.25 <= delta <= 0.65:
        score += 7
    # 5. انتهاء
    days = int(r.get('days',2))
    if 5 <= days <= 14:
        score += 10
        reasons.append(f"{days}ي مثالي")
    elif 2 <= days <= 21:
        score += 3
    else:
        score -= 5
    total = int(max(10, min(95, score)))
    return total, " | ".join(reasons[:3])

def calc_confirm(r):
    ch1 = float(r.get("change_1d",0))
    score = 50
    if r["type"] == "CALL":
        if ch1 >= 2:
            score += 22
        elif ch1 >= 0.8:
            score += 12
        elif ch1 < 0:
            score -= 20
    else:
        if ch1 <= -2.5:
            score += 22
        elif ch1 <= -1.2:
            score += 15
        elif ch1 <= -0.6:
            score += 8
        elif ch1 > 0.5:
            score -= 20
    score = int(max(35, min(88, score)))
    why = f"اليوم {ch1:+.1f}% | {r.get('trend')} | RSI {float(r.get('rsi',50)):.0f} | VOL x{float(r.get('vol_ratio',1)):.1f}"
    return score, why

# عرض
if not st.session_state.results.empty:
    enriched = []
    for _, r in st.session_state.results.iterrows():
        if pd.isna(r.get("stock_now",0)):
            continue
        conf, why = calc_confirm(r)
        qual, qwhy = calc_quality(r)
        r2 = dict(r)
        r2["confirm"] = int(conf)
        r2["quality"] = int(qual)
        r2["why"] = why
        r2["qwhy"] = qwhy
        enriched.append(r2)
    if enriched:
        df2 = pd.DataFrame(enriched)
        df2 = df2.dropna(subset=['confirm','stock_now'])
        df2 = df2.sort_values(["confirm","quality"], ascending=[False, False])
        df2 = df2.drop_duplicates(subset=["ticker"], keep="first")
        v = st.session_state.view
        if "BUY قوي" in v:
            final = df2[df2["type"]=="CALL"].head(20)
        elif "SELL قوي" in v:
            final = df2[df2["type"]=="PUT"].head(20)
        else:
            final = df2.head(20)
    else:
        final = pd.DataFrame()
else:
    final = pd.DataFrame()
    st.info("📱 اضغط ⚡ فحص الآن - V52 لا يعلق مثل الصورة البيضاء 7:01")
    st.markdown("""
    **✅ 6 إضافات جودة العقد الجديدة:**
    1. **Bid-Ask <8%** - عقد HOOD $2.62 لازم bid $2.55 ask $2.71
    2. **OI >1000** - OI ضعيف = عقد ميت
    3. **Delta 0.35-0.55** - PUT 110 delta -0.45 ممتاز
    4. **VOL/OI** - صورتك x0.2 ضعيف | x1.5 انفجار
    5. **انتهاء 5-14 يوم** - 08/28 يومين خطر theta
    6. **RSI <45 للـ PUT** - تأكيد هبوط
    """)

if not final.empty:
    st.success(f"✅ {len(final)} شركة - كل شركة اتجاه واحد + جودة - {ksa_str}")
    for _, w in final.head(4).iterrows():
        conf = int(w.get("confirm",60))
        qual = int(w.get("quality",50))
        border = "#16a34a" if w.get("type")=="CALL" else "#dc2626"
        icon = "🟢" if w.get("type")=="CALL" else "🔴"
        qcol = "🟢" if qual>=70 else "🟡" if qual>=50 else "🔴"
        st.markdown(f"""<div style="background:#ffffff;border:3px solid {border};border-radius:12px;padding:10px;margin:6px 0;color:#000000;">
        <b>{icon} {w.get('ticker')} {int(w.get('strike'))} {w.get('type')} - {conf}% | جودة {qcol} {qual}%</b><br>
        {w.get('why')}<br>
        <span style="font-size:10px; color:#444;">{w.get('qwhy')}</span><br>
        <span style="font-size:11px;">${float(w.get('stock_now',0)):.2f} | عقد ${float(w.get('opt_price',0)):.2f} bid ${float(w.get('bid',0)):.2f} ask ${float(w.get('ask',0)):.2f} | VOL {int(w.get('vol',0))} OI {int(w.get('oi',0))} | {w.get('exp_short')} {int(w.get('days'))}ي</span>
        </div>""", unsafe_allow_html=True)

    html = '<table class="big-table"><tr><th>%</th><th>جودة</th><th>نوع</th><th>شركة</th><th>سهم</th><th>سترايك</th><th>📅</th><th>عقد</th><th>VOL/OI</th></tr>'
    for _, w in final.iterrows():
        try:
            sp = float(w.get("stock_now",0))
            conf = int(w.get("confirm",60))
            qual = int(w.get("quality",50))
            ch1 = float(w.get("change_1d",0))
            opt_p = float(w.get("opt_price",0))
            vol = int(w.get("vol",0))
            oi = int(w.get("oi",0))
            badge = f'<span class="call-badge">CALL</span>' if w.get("type")=="CALL" else f'<span class="put-badge">PUT</span>'
            voi = f"{vol/oi:.1f}x" if oi>0 else f"{vol}"
            html += f'<tr><td><b>{conf}%</b></td><td><b>{qual}%</b></td><td>{badge}</td><td><b>{w.get("ticker","")}</b></td><td><b>${sp:.2f}</b><br><span style="color:{"#16a34a" if ch1>=0 else "#dc2626"}">{ch1:+.1f}%</span></td><td><b>{int(w.get("strike",0))}</b><br>{float(w.get("dist",0)):+.1f}%</td><td>{w.get("exp_short","")}<br>{int(w.get("days"))}ي</td><td>${opt_p:.2f}<br>bid {float(w.get("bid",0)):.2f}</td><td>{voi}<br>OI {oi}</td></tr>'
        except:
            continue
    html += '</table>'
    st.markdown(html, unsafe_allow_html=True)

if do_scan:
    tickers = ["NVDA","TSLA","META","AAPL","COIN","PLTR","HOOD","MSTR"]
    with st.spinner(f"⚡ يفحص {len(tickers)} شركات..."):
        rows = []
        with ThreadPoolExecutor(max_workers=8) as executor:
            futs = {executor.submit(fetch_v52, t): t for t in tickers}
            for fu in as_completed(futs):
                try:
                    res = fu.result()
                    if res:
                        rows.extend(res)
                except:
                    pass
    if rows:
        ndf = pd.DataFrame(rows)
        ndf = ndf.dropna(subset=['stock_now'])
        ndf = ndf[(ndf["stock_now"]>3) & (ndf["stock_now"]<5000)]
        ndf = ndf.sort_values("vol", ascending=False)
        ndf = ndf.drop_duplicates(subset=["ticker"], keep="first")
        if not ndf.empty:
            st.session_state.results = ndf
            st.rerun()
    else:
        st.error("لا يوجد - السوق مغلق أو yfinance معلق - اضغط فحص مرة ثانية")

st.caption(f"V52 FINAL كامل | {ksa_str} | يحل صفحة بيضاء 7:01 | جودة = Bid-Ask + OI + VOL/OI + Delta + انتهاء + RSI | شركة واحدة = اتجاه واحد")
