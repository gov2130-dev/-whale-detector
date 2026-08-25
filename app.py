import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time

st.set_page_config(layout="wide", page_title="Whale V25 Ultimate Decision", initial_sidebar_state="expanded")

# إزالة الوميض - لا يوجد reload للصفحة كاملة

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:380px!important; max-width:400px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:13px!important;}
.stButton>button {width:100%!important; height:44px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:12px!important; font-weight:800!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:9px 3px; text-align:center; font-size:9px; font-weight:800;}
.whale-table td {background:#fff!important; padding:9px 3px; text-align:center; font-weight:700; font-size:10px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#ef4444!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-0 {background:#64748b!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-size:10px;}
.itm {background:#dcfce7!important; color:#166534!important; padding:2px 5px; border-radius:6px; font-size:9px; font-weight:800;}
.otm {background:#fef3c7!important; color:#92400e!important; padding:2px 5px; border-radius:6px; font-size:9px; font-weight:800;}
.live-price {background:#eff6ff!important; color:#1d4ed8!important; padding:3px 6px; border-radius:6px; font-weight:900; border:1px solid #bfdbfe;}
.decision-box {background:#f0fdf4; border:3px solid #22c55e; border-radius:14px; padding:12px; margin:6px 0;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V25 - بدون وميض + 6 عناصر قرار قوية 🧠")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "auto_run" not in st.session_state: st.session_state.auto_run=True

st.sidebar.markdown("## 🎛️ تحكم - بدون وميض")
# تحكم يدوي بدون reload تلقائي للصفحة
auto_check=st.sidebar.checkbox("⚡ فحص تلقائي (بدون وميض)", True, key="auto25")
st.session_state.auto_run=auto_check
refresh_interval=st.sidebar.select_slider("⏱️ كل كم يفحص؟", options=["15 ثانية","30 ثانية","1 دقيقة","2 دقيقة","5 دقائق"], value="1 دقيقة", key="int25")
map_sec={"15 ثانية":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300}
interval_sec=map_sec[refresh_interval]

min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="m25")
time_filter=st.sidebar.select_slider("⏰ فلتر الحيتان", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf25")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد", True, key="s25")

st.sidebar.markdown("### 🔧 حل مشكلة الوميض")
st.sidebar.info("✅ V25 بدون تحديث كامل للصفحة - الجدول يتحدث بسلاسة بدون وميض. تقدر تضغط وتقرأ براحتك.")

if st.sidebar.button("🔄 فحص الآن", key="man25"): st.session_state.current_idx=0; st.rerun()
if st.sidebar.button("🔄 مسح", key="clr25"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_minutes_filter():
    return {"آخر 15 دقيقة":15,"آخر ساعة":60,"آخر 3 ساعات":180,"اليوم كامل":1440}.get(time_filter,60)

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

def get_stock_data(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="5d")
        if hist.empty: return None
        curr=hist['Close'].iloc[-1]
        prev=hist['Close'].iloc[-2] if len(hist)>1 else curr
        chg=(curr-prev)/prev*100
        # RSI بسيط
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100 - (100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        return {"price":curr, "chg":chg, "rsi":rsi}
    except: return None

def calc_strong_score(row, stock_info):
    score=0; reasons=[]; warnings=[]

    # عنصر 1: تاريخ الانتهاء
    days=row.get("days_left",0)
    if days<0: score-=5; warnings.append("⛔ منتهي")
    elif days==0: score+=0; warnings.append("⚠️ 0DTE خطير 90% خسارة")
    elif 3<=days<=7: score+=3; reasons.append("✅ 3-7 أيام مثالي")
    elif 8<=days<=14: score+=2; reasons.append("✅ أسبوعين جيد")
    elif days<=2: score+=1; warnings.append("⚠️ يومين فقط")
    else: score+=1

    # عنصر 2: قيمة الحوت + VOL
    prem=row["premium_M"]
    vol=row["volume"]
    if prem>=20 and vol>=100000: score+=3; reasons.append(f"🐋🔥 حوت ضخم ${prem:.0f}M + VOL {vol/1000:.0f}K")
    elif prem>=5: score+=2; reasons.append(f"🐋 ${prem:.0f}M قوي")
    elif prem>=1: score+=1

    # عنصر 3: سعر السهم vs STRIKE (ITM/OTM)
    if stock_info:
        curr=stock_info["price"]
        strike=row["strike"]
        is_call="CALL" in row["signal"]
        if is_call:
            dist=(strike-curr)/curr*100
            if -2<=dist<=3: score+=2; reasons.append(f"🎯 قريب من السعر {dist:+.1f}%")
            elif dist< -5: warnings.append(f"⚠️ ITM عميق {dist:.1f}% غالي")
            elif dist>10: warnings.append(f"⚠️ OTM بعيد {dist:.1f}%")
        else:
            dist=(curr-strike)/curr*100
            if -2<=dist<=3: score+=2; reasons.append(f"🎯 قريب {dist:+.1f}%")
            elif dist< -5: warnings.append(f"⚠️ ITM عميق")

    # عنصر 4: اتجاه السهم + RSI
    if stock_info:
        rsi=stock_info["rsi"]
        chg=stock_info["chg"]
        is_call="CALL" in row["signal"]
        if is_call:
            if rsi<70 and chg>-1: score+=1; reasons.append(f"📈 RSI {rsi:.0f} صاعد")
            elif rsi>=75: warnings.append(f"⚠️ RSI {rsi:.0f} متشبع")
        else:
            if rsi>30 and chg<1: score+=1; reasons.append(f"📉 RSI {rsi:.0f} هابط")
            elif rsi<=25: warnings.append(f"⚠️ RSI {rsi:.0f} تشبع بيع")

    # عنصر 5: وقت الدخول
    if row["minutes_ago"]<=15: score+=2; reasons.append("🔥 دخل الآن")
    elif row["minutes_ago"]<=60: score+=1

    # عنصر 6: سعر الأوبشن منطقي
    if 0.5<=row["opt_price"]<=4: score+=1; reasons.append(f"💵 ${row['opt_price']:.2f} منطقي")
    elif row["opt_price"]>8: warnings.append(f"⚠️ غالي ${row['opt_price']:.2f}")

    if score>=8: dec="⭐⭐⭐ قوي جدا"; css="score-3"; action="✅ ادخل 2-3 عقود"; stop="وقف -30%"; target="+50-100%"
    elif score>=6: dec="⭐⭐ قوي"; css="score-2"; action="✅ ادخل 1-2 عقد"; stop="-35%"; target="+40-80%"
    elif score>=4: dec="⭐ متوسط"; css="score-2"; action="👀 راقب"; stop="-30%"; target="+30%"
    elif score>=2: dec="⚠️ ضعيف"; css="score-1"; action="⛔ لا تدخل"; stop="-"; target="-"
    else: dec="⛔ خطر"; css="score-0"; action="⛔ اتركه"; stop="-"; target="-"

    return score, dec, css, action, stop, target, reasons, warnings

# فحص بدون وميض - تحديث جزئي
all_tickers=get_tickers()
if st.session_state.auto_run and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+4, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    placeholder=st.empty()
    placeholder.info(f"🔴 يفحص {all_tickers[start:end]} | فلتر {mins} د | فحص كل {refresh_interval} | بدون وميض ✅")

    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            days_left, exp_short, exp_full=parse_exp(exp)
            stock_info=get_stock_data(t)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=20)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                    except: minutes_ago=9999
                    curr_price=stock_info["price"] if stock_info else 0
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"exp_full":exp_full,"days_left":days_left,"minutes_ago":minutes_ago,"stock_price":curr_price,"stock_info":stock_info})
        except: pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=get_minutes_filter()] if get_minutes_filter()<1440 else new_df
        # ترتيب بالسكور القوي
        scored=[]
        for _, r in filtered.iterrows():
            sc, dec, css, action, stop, target, rs, warns=calc_strong_score(r, r.get("stock_info"))
            scored.append((sc, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        fresh_df=pd.DataFrame([x[1] for x in scored[:2]]) if scored else pd.DataFrame()
        fresh=[]
        for _, w in fresh_df.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                fresh.append(w)
                st.session_state.sent.add(key)
        if fresh: st.session_state.new_whales=fresh
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined

    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers):
        st.session_state.current_idx=0
        st.session_state.last_refresh=datetime.now()
        time.sleep(interval_sec)
        st.rerun()
    else:
        time.sleep(0.6)
        st.rerun()

if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    final_time=final_raw[final_raw["minutes_ago"]<=get_minutes_filter()].copy() if get_minutes_filter()<1440 else final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        info=r.get("stock_info") or get_stock_data(r["ticker"])
        sc, dec, css, action, stop, target, rs, warns=calc_strong_score(r, info)
        r2=r.copy()
        r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["stop"]=stop; r2["target"]=target; r2["reasons"]=rs; r2["warnings"]=warns
        r2["stock_info"]=info
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)

    if smart_filter:
        best=[]
        for ticker in enriched_df["ticker"].unique():
            t_df=enriched_df[enriched_df["ticker"]==ticker]
            best.append(t_df.sort_values("score", ascending=False).iloc[0])
        final=pd.DataFrame(best).sort_values("score", ascending=False).head(15)
    else:
        final=enriched_df.head(15)

    if st.session_state.new_whales:
        st.markdown("### 🔔 أفضل حوت - مع 6 عناصر قرار")
        for w in st.session_state.new_whales[:1]:
            sc, dec, css, action, stop, target, rs, warns=calc_strong_score(w, w.get("stock_info"))
            curr=w.get("stock_price",0)
            dist=f"{((w['strike']-curr)/curr*100):+.1f}%" if curr else ""
            st.markdown(f"<div class='decision-box'><b>🔔 {w['ticker']} | {dec} ⭐{sc}</b> | {w['signal']} {w['strike']} | السهم ${curr:.2f} ({dist})<br>📅 {w['exp_short']} ({w['days_left']}ي) | ${w['opt_price']:.2f} | ${w['premium_M']:.1f}M<br><b>{action}</b> | وقف {stop} | هدف {target}<br><small>✅ {' | '.join(rs[:3])}</small><br><small style='color:#ef4444'>{' | '.join(warns)}</small></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="h25"): st.session_state.new_whales=[]; st.rerun()

    st.success(f"🧠 V25 بدون وميض | 6 عناصر قرار | {len(final)} حوت | آخر تحديث {st.session_state.last_refresh.strftime('%H:%M:%S')} | فحص كل {refresh_interval}")

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار</th><th>الشركة + السعر الحي</th><th>النوع</th><th>STRIKE + المسافة</th><th>📅 انتهاء</th><th>الأوبشن</th><th>الحوت</th><th>6 عناصر</th><th>✅ ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            info=w.get("stock_info")
            curr=w.get("stock_price",0)
            if info and curr:
                price_html=f'<span class="live-price">${curr:.2f}</span><br><small style="color:{"#22c55e" if info["chg"]>=0 else "#ef4444"}">{info["chg"]:+.1f}% RSI {info["rsi"]:.0f}</small>'
                is_call="CALL" in w["signal"]
                if is_call: dist=(w["strike"]-curr)/curr*100
                else: dist=(curr-w["strike"])/curr*100
                dist_str=f"{dist:+.1f}%"
                dist_class="itm" if abs(dist)<=2 else "otm"
                strike_html=f'{w["strike"]}<br><span class="{dist_class}">{dist_str}</span>'
            else:
                price_html=f'${curr:.2f}' if curr else "-"
                strike_html=f'{w["strike"]}'
            days=w.get("days_left",0)
            exp_html=f'<span style="background:#fee2e2; color:#991b1b; padding:2px 5px; border-radius:6px; font-size:9px;">⛔ منتهي</span>' if days<0 else f'<span style="background:#fee2e2; color:#991b1b; padding:2px 5px; border-radius:6px;">⚠️ اليوم</span>' if days==0 else f'{w["exp_short"]}<br><small>({days}ي)</small>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}/10</small>'
            reasons_html="<br>".join(w["reasons"][:2]) if w["reasons"] else "-"
            if w["warnings"]: reasons_html+=f"<br><small style='color:#ef4444'>{w['warnings'][0]}</small>"
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{strike_html}</td><td>{exp_html}</td><td>${w['opt_price']:.2f}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M<br><small>VOL {w['volume']/1000:.0f}K</small></td><td style='font-size:8px; text-align:right'>{reasons_html}</td><td style='font-size:9px'><b>{w['action']}</b><br><small>وقف {w['stop']}</small><br><small>هدف {w['target']}</small></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)

    with st.expander("🧠 شرح 6 عناصر القرار القوية - كيف تختار؟"):
        st.markdown("""
        **V25 يحسب 6 عناصر قوية لكل حوت:**

        **1. 📅 تاريخ الانتهاء (أهم عنصر)**
                - منتهي (-1) = ⛔ لا تدخل أبدا - مثل اللي عندك بالفيديو
                - 0DTE = خطير 90% خسارة
                - 3-7 أيام = ⭐⭐⭐ مثالي

        **2. 🐋 قوة الحوت + VOL**
                - $20M + 100K VOL = حوت ضخم مع سيولة = ثقة عالية
                - $1M فقط = ضعيف

        **3. 🎯 المسافة بين سعر السهم والسترايك**
                - مثال: AAPL سعره $230 و STRIKE 232 = +0.8% قريب جدا = ممتاز
                - STRIKE 300 بعيد +30% = مستحيل يوصل = لا تدخل

        **4. 📈 سعر السهم الحي + RSI**
                - CALL + RSI 60 + السهم صاعد +1% = قوي
                - CALL + RSI 80 متشبع = خطر

        **5. 🔥 وقت دخول الحوت**
                - قبل 5 دقائق = لحظي
                - قبل 5 ساعات = قديم

        **6. 💵 سعر الأوبشن منطقي**
                - $0.5-$4 تقدر تشتري 10 عقود
                - $15 غالي

        **القرار:**
                - ⭐⭐⭐ 8-10 = ادخل 2-3 عقود، وقف -30%، هدف +50-100%
                - ⭐⭐ 6-7 = ادخل 1-2 عقد
                - ⭐ متوسط = راقب فقط
                - ⛔ = اتركه (مثل كل الحيتان اللي بالفيديو منتهية)

        **حل الوميض:** أزلت تحديث الصفحة الكامل - الآن يفحص في الخلفية بدون وميض ✅
        """)

else:
    st.warning("⏳ يفحص... اضغط فحص الآن")

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V25 Ultimate - بدون وميض + 6 عناصر قرار")
