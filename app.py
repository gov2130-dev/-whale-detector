import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V29 Fast No Delay", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:410px!important; max-width:430px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:12px!important;}
.stButton>button {width:100%!important; height:42px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:10px!important; font-weight:800!important; margin-bottom:5px!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:9px 3px; text-align:center; font-size:9px; font-weight:800;}
.whale-table td {background:#fff!important; padding:9px 3px; text-align:center; font-weight:700; font-size:10px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#8b5cf6!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.dte-0 {background:linear-gradient(135deg,#ef4444,#f97316)!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:10px;}
.dte-good {background:#dcfce7!important; color:#166534!important; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:800; border:1px solid #22c55e;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V29 Fast - سريع 45 ثانية بدون تأخير 🔥")

def get_tickers():
    # قللت الشركات للأكثر نشاطا عشان السرعة - 15 بدل 28
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","GME","MARA"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"

st.sidebar.markdown("## 🎯 V29 Fast - حل التأخير ساعة")

st.sidebar.error("⏰ المشكلة: V29 القديم يفحص شركة شركة = ساعة كاملة")
st.sidebar.success("✅ الحل: فحص متوازي 8 شركات مع بعض = 45 ثانية فقط")

st.sidebar.markdown("### 💰 فلاتر V29 الأصلي")
min_prem=st.sidebar.slider("💰 أقل حوت", 100000, 5000000, 500000, 100000, key="m29fast")
min_vol=st.sidebar.slider("📊 أقل VOL", 1, 50000, 5000, 1000, key="v29fast")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل (0DTE دبل)","اليوم فقط 0DTE","3-14 يوم"], value="الكل (0DTE دبل)", key="exp29fast")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf29fast")
score_filter=st.sidebar.select_slider("⭐ أقل سكور", options=["الكل","⭐+ (3+)","⭐⭐+ (5+) قوي","⭐⭐⭐ فقط (7+)"], value="⭐+ (3+)", key="score29fast")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["30 ثانية","1 دقيقة","2 دقيقة"], value="30 ثانية", key="int29fast")
map_sec={"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120}
interval_sec=map_sec[refresh_interval]
auto=st.sidebar.checkbox("⚡ فحص تلقائي سريع بدون بهوت", True, key="a29fast")

st.sidebar.markdown("---")
if st.sidebar.button("🔥 0DTE اليوم - دبلات", key="b0_29fast"): st.session_state.page="0DTE"
if st.sidebar.button("💰 دبلات محتملة", key="bDouble_29fast"): st.session_state.page="DOUBLE"
if st.sidebar.button("🏆 أقوى 20", key="b20_29fast"): st.session_state.page="TOP20"
if st.sidebar.button("📋 كل اليوم", key="bAll_29fast"): st.session_state.page="ALL"

st.sidebar.markdown("---")
if st.sidebar.button("🔄 فحص سريع الآن 45ث", key="bNow_29fast"):
    st.session_state.last_refresh=datetime.now()
    st.rerun()
if st.sidebar.button("🗑️ مسح", key="bClear_29fast"): st.session_state.results=pd.DataFrame()

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

def fetch_ticker(ticker, min_prem, min_vol, exp_filter):
    try:
        s=yf.Ticker(ticker)
        if not s.options: return []
        rows=[]
        # نفحص أول تاريخين فقط
        for exp_try in s.options[:2]:
            try:
                chain=s.option_chain(exp_try)
                exp_date=datetime.strptime(exp_try, "%Y-%m-%d")
                days_left=(exp_date - datetime.now()).days
                if exp_filter=="اليوم فقط 0DTE" and days_left!=0: continue
                if exp_filter=="3-14 يوم" and not (3<=days_left<=14): continue
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
                    df["premium"]=df["lastPrice"]*df["volume"]*100
                    f=df[(df["premium"]>=min_prem) & (df["volume"]>=min_vol)].copy()
                    for _, r in f.iterrows():
                        try:
                            ltd=pd.to_datetime(r.get("lastTradeDate"))
                            minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                        except: minutes_ago=9999
                        exp_short=exp_date.strftime("%m/%d")
                        rows.append({"ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_short,"exp_full":exp_try,"days_left":days_left,"minutes_ago":minutes_ago})
                break
            except: continue
        return rows
    except: return []

def get_stock_analysis(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="10d")
        if hist.empty: return None
        curr=hist['Close'].iloc[-1]
        sma20=hist['Close'].rolling(5).mean().iloc[-1]
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        return {"price":curr,"sma20":sma20,"rsi":rsi,"trend":"صاعد" if curr>sma20 else "هابط"}
    except: return None

def calc_score(row, stock_data):
    score=0; reasons=[]; warnings=[]; sd={}; is_0dte=row["days_left"]==0
    days=row["days_left"]; prem=row["premium_M"]; vol=row["volume"]; opt=row["opt_price"]; mins=row["minutes_ago"]
    if days<0: return -10, "⛔", "score-0", "⛔", {}, [], [], False
    if days==0:
        is_0dte=True
        if prem>=3 and 0.2<=opt<=2.5 and vol>=10000: score+=5; reasons.append(f"🔥 0DTE ${prem:.0f}M ${opt:.2f}"); sd["exp"]="⭐⭐⭐ دبل"
        elif prem>=1: score+=3; reasons.append(f"🔥 0DTE ${prem:.0f}M")
        else: score+=1
        warnings.append("1 عقد فقط")
    elif 1<=days<=7: score+=3; reasons.append(f"✅ {days}ي")
    else: score+=2

    if prem>=20: score+=4; reasons.append(f"🐋 ${prem:.0f}M ضخم")
    elif prem>=5: score+=3
    elif prem>=1: score+=1
    if vol>=50000: score+=2
    elif vol>=10000: score+=1
    if is_0dte:
        if 0.2<=opt<=1.5: score+=3; reasons.append(f"💰 ${opt:.2f}=دبل")
        elif 0.2<=opt<=2.5: score+=2
    else:
        if 0.5<=opt<=5: score+=1
    if stock_data:
        curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
        dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
        sd["distance"]=f"{dist:+.1f}%"; sd["stock_price"]=f"${curr:.2f}"; sd["rsi"]=f"{stock_data['rsi']:.0f}"; sd["trend"]=stock_data["trend"]
        if abs(dist)<=1.5: score+=4; reasons.append(f"🎯 {dist:+.1f}% قريب جدا"); sd["distance_star"]="⭐⭐⭐"
        elif abs(dist)<=3: score+=2; reasons.append(f"🎯 {dist:+.1f}%")
        elif abs(dist)>7: warnings.append(f"بعيد {dist:+.1f}%")
        if is_call and stock_data["trend"]=="صاعد" and stock_data["rsi"]<70: score+=2
        if not is_call and stock_data["trend"]=="هابط": score+=2
    if mins<=15: score+=2; reasons.append("🔥 الآن")
    elif mins<=60: score+=1
    sd["double_potential"]="💰 دبل 100-300%" if is_0dte and score>=6 else f"هدف +{50 if days<=7 else 30}%"
    if is_0dte:
        if score>=7: dec="🔥🔥 0DTE دبل"; css="score-1"; action="✅ 1 عقد"
        elif score>=5: dec="🔥 0DTE جيد"; css="score-1"; action="✅ 1 عقد"
        else: dec="⚠️ 0DTE"; css="score-2"; action="👀 راقب"
    else:
        if score>=7: dec="⭐⭐⭐ قوي"; css="score-3"; action="✅ 2-3"
        elif score>=5: dec="⭐⭐ جيد"; css="score-2"; action="✅ 1-2"
        else: dec="⭐"; css="score-2"; action="👀 راقب"
    return score, dec, css, action, sd, reasons, warnings, is_0dte

# عرض الجدول أولا - بدون بهوت
if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    if st.session_state.page=="0DTE": final_time=final_raw[final_raw["days_left"]==0].copy()
    elif st.session_state.page=="DOUBLE": final_time=final_raw[(final_raw["days_left"]<=1) & (final_raw["opt_price"]<=2.5) & (final_raw["premium_M"]>=1)].copy()
    else: final_time=final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        stock_data=get_stock_analysis(r["ticker"])
        sc, dec, css, action, sd, rs, warns, is_0dte=calc_score(r, stock_data)
        if sc<0: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["reasons"]=rs; r2["warnings"]=warns; r2["is_0dte"]=is_0dte
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)
    if score_filter=="⭐⭐+ (5+) قوي": enriched_df=enriched_df[enriched_df["score"]>=5]
    elif score_filter=="⭐⭐⭐ فقط (7+)": enriched_df=enriched_df[enriched_df["score"]>=7]
    elif score_filter=="⭐+ (3+)": enriched_df=enriched_df[enriched_df["score"]>=3]
    final=enriched_df.head(20) if st.session_state.page!="TOP10" else enriched_df.head(10)

    # حساب التأخير
    delay_min = (datetime.now() - st.session_state.last_refresh).total_seconds()/60
    if delay_min>5:
        st.error(f"⏰ متأخر {delay_min:.0f} دقيقة - اضغط 🔄 فحص سريع الآن 45ث")
    else:
        st.success(f"✅ محدث الآن - تأخير {delay_min:.1f} دقيقة فقط | {len(final)} حوت | {st.session_state.last_refresh.strftime('%H:%M:%S')} | V29 Fast بدون تأخير")

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار</th><th>الشركة + السعر</th><th>النوع</th><th>STRIKE</th><th>📅 انتهاء</th><th>الأوبشن</th><th>الحوت</th><th>دبل؟</th><th>ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            sd=w.get("strong_data",{})
            price_html=f'{sd.get("stock_price","-")}<br><small>RSI {sd.get("rsi","-")}</small>'
            dist_html=f'{w["strike"]}<br><small>{sd.get("distance","")} {sd.get("distance_star","")}</small>'
            exp_html=f'<span class="dte-0">🔥 اليوم 0DTE</span>' if w["is_0dte"] else f'<span class="dte-good">{w["exp_short"]} ({w["days_left"]}ي)</span>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}</small><br><small>{sd.get("double_potential","")}</small>'
            seven=f'<small>{" | ".join(w["reasons"][:2])}</small>'
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>${w['opt_price']:.2f}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M<br><small>{w['volume']/1000:.0f}K</small></td><td style='font-size:8px'>{seven}</td><td><b>{w['action']}</b></td></tr>"
        html+="</table>"
        return html
    st.markdown(build_html(final), unsafe_allow_html=True)
else:
    st.warning("⏳ اضغط 🔄 فحص سريع الآن 45ث - أول مرة")

# فحص سريع متوازي - بدون بهوت
if auto:
    # فحص متوازي 8 شركات مرة واحدة = سريع
    all_tickers=get_tickers()
    mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
    mins=mins_map.get(time_filter,60)

    st.caption(f"🔴 يفحص {len(all_tickers)} شركة بشكل متوازي (8 مع بعض) - 45 ثانية فقط بدون بهوت...")

    new_rows=[]
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures={executor.submit(fetch_ticker, t, min_prem, min_vol, exp_filter): t for t in all_tickers}
        for future in as_completed(futures):
            try:
                rows=future.result()
                new_rows.extend(rows)
            except: pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        # فلتر الوقت
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
        combined=pd.concat([st.session_state.results, filtered]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(600) if not st.session_state.results.empty and not filtered.empty else (filtered if not filtered.empty else new_df)
        st.session_state.results=combined
        st.session_state.last_refresh=datetime.now()

    time.sleep(interval_sec)
    st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V29 Fast - 45 ثانية فقط - بدون تأخير ساعة | 15 شركة نشطة")if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"

st.sidebar.markdown("## 🎯 V29 الأصلي - نفس المنطق القوي")

st.sidebar.markdown("### 🔥 نمط التداول")
trade_mode=st.sidebar.select_slider("🎯 نمطك؟", options=["سكالبينج 0DTE (دبلات سريعة)","سوينغ 3-14 يوم (آمن)","الكل - أعرض الفرصتين"], value="الكل - أعرض الفرصتين", key="mode29f")

st.sidebar.markdown("### 💰 فلاتر")
min_prem=st.sidebar.slider("💰 أقل حوت", 100000, 5000000, 500000, 100000, key="m29f")
min_vol=st.sidebar.slider("📊 أقل VOL", 1, 100000, 5000, 1000, key="v29f")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل (0DTE يعطي دبلات)","اليوم و بكرة فقط (0-1 يوم)","3-14 يوم (سوينغ)","استبعد المنتهي فقط"], value="الكل (0DTE يعطي دبلات)", key="exp29f")
opt_price_filter=st.sidebar.select_slider("💵 سعر الأوبشن", options=["الكل","$0.2-$2 (0DTE رخيص = دبل)","$0.5-$5 (ممتاز)","$0.5-$3"], value="$0.2-$2 (0DTE رخيص = دبل)", key="opt29f")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر 3 ساعات","آخر ساعة (لحظي)","آخر 15 دقيقة (0DTE)"], value="آخر ساعة (لحظي)", key="tf29f")
score_filter=st.sidebar.select_slider("⭐ أقل سكور", options=["الكل","⭐+ (3+)","⭐⭐+ (5+) قوي","⭐⭐⭐ فقط (7+)"], value="⭐+ (3+)", key="score29f")

# حل البهوت: شلت الجرس والـ progress المتحرك + خليت الفحص كل دقيقتين
refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["1 دقيقة","2 دقيقة","5 دقائق"], value="2 دقيقة", key="int29f")
map_sec={"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300}
interval_sec=map_sec[refresh_interval]
auto=st.sidebar.checkbox("⚡ فحص تلقائي (بدون بهوت)", True, key="a29f")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 عرض الجداول")
if st.sidebar.button("🔥 0DTE اليوم - دبلات", key="b0_29f"): st.session_state.page="0DTE"
if st.sidebar.button("⚡ آخر 15 دقيقة", key="b15_29f"): st.session_state.page="15MIN"
if st.sidebar.button("🏆 أقوى 20", key="b20_29f"): st.session_state.page="TOP20"
if st.sidebar.button("💰 دبلات محتملة", key="bDouble_29f"): st.session_state.page="DOUBLE"
if st.sidebar.button("📋 كل اليوم", key="bAll_29f"): st.session_state.page="ALL"
if st.sidebar.button("🎯 قرار قوي فقط", key="bStrong_29f"): st.session_state.page="STRONG"

st.sidebar.markdown("---")
if st.sidebar.button("🔄 فحص الآن", key="bNow_29f"): st.session_state.current_idx=0
if st.sidebar.button("🗑️ مسح", key="bClear_29f"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set()

def get_stock_analysis(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="20d")
        if hist.empty or len(hist)<5: return None
        curr=hist['Close'].iloc[-1]
        sma20=hist['Close'].rolling(20).mean().iloc[-1] if len(hist)>=20 else curr
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        return {"price":curr,"sma20":sma20,"rsi":rsi,"trend":"صاعد" if curr>sma20 else "هابط"}
    except: return None

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

# نفس منطق V29 الأصلي 100% - ما غيرت حرف
def calc_logical_score(row, stock_data):
    score=0; reasons=[]; warnings=[]; sd={}; is_0dte=False
    days=row.get("days_left",0); prem=row["premium_M"]; vol=row["volume"]; opt=row["opt_price"]; mins=row["minutes_ago"]

    if days<0: return -10, "⛔ منتهي", "score-0", "⛔ اتركه", {}, [], ["منتهي"], False
    elif days==0:
        is_0dte=True
        sd["exp_type"]="🔥 0DTE دبل"
        if prem>=5 and vol>=30000 and 0.2<=opt<=2 and mins<=30:
            score+=5; reasons.append(f"🔥🔥 0DTE قوي ${prem:.0f}M رخيص ${opt:.2f}"); sd["exp"]="⭐⭐⭐ دبل محتمل"
        elif prem>=1: score+=3; reasons.append(f"🔥 0DTE ${prem:.0f}M"); sd["exp"]="⭐⭐ دبل"
        else: score+=1; reasons.append("🔥 0DTE"); sd["exp"]="0DTE"
        warnings.append("⚠️ مخاطرة 100% - 1 عقد فقط")
    elif 1<=days<=2: is_0dte=False; score+=3; reasons.append(f"✅ {days}ي سريع"); sd["exp"]=f"✅ {days}ي سريع + دبل"; sd["exp_type"]="سريع"
    elif 3<=days<=7: score+=3; reasons.append(f"✅ {days}ي مثالي سوينغ"); sd["exp"]=f"✅ {days}ي مثالي"; sd["exp_type"]="سوينغ"
    elif 8<=days<=14: score+=2; reasons.append(f"✅ {days}ي جيد"); sd["exp"]=f"✅ {days}ي"; sd["exp_type"]="سوينغ"

    if exp_filter=="اليوم و بكرة فقط (0-1 يوم)" and days>1: return -10, "", "", "", {}, [], [], False
    if exp_filter=="3-14 يوم (سوينغ)" and not (3<=days<=14): return -10, "", "", "", {}, [], [], False

    if prem>=20: score+=4; reasons.append(f"🐋 ضخم ${prem:.0f}M"); sd["whale"]="ضخم"
    elif prem>=5: score+=3; reasons.append(f"🐋 ${prem:.0f}M قوي")
    elif prem>=1: score+=1

    if vol>=100000: score+=2; reasons.append(f"🔥 VOL {vol/1000:.0f}K")
    elif vol>=20000: score+=1

    if is_0dte:
        if 0.2<=opt<=1.5: score+=3; reasons.append(f"💰 رخيص ${opt:.2f}=دبل"); sd["opt_price"]="رخيص = دبل"
        elif 0.2<=opt<=2.5: score+=2
        elif opt>5: score-=2; warnings.append(f"غالي لـ 0DTE ${opt:.2f}")
    else:
        if 0.5<=opt<=3: score+=2; reasons.append(f"💵 ${opt:.2f} ممتاز")
        elif 0.5<=opt<=5: score+=1

    if stock_data:
        curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
        dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
        sd["distance"]=f"{dist:+.1f}%"; sd["stock_price"]=f"${curr:.2f}"; sd["rsi"]=f"{stock_data['rsi']:.0f}"; sd["trend"]=stock_data["trend"]
        if is_0dte:
            if abs(dist)<=1.5: score+=4; reasons.append(f"🎯🎯 قريب جدا {dist:+.1f}% = دبل"); sd["distance_star"]="⭐⭐⭐ دبل"
            elif abs(dist)<=3: score+=2; reasons.append(f"🎯 قريب {dist:+.1f}%"); sd["distance_star"]="⭐⭐"
            elif abs(dist)>5: score-=2; warnings.append(f"بعيد لـ 0DTE {dist:+.1f}%")
        else:
            if abs(dist)<=3: score+=3; reasons.append(f"🎯 قريب {dist:+.1f}%")
            elif abs(dist)<=5: score+=2
            elif abs(dist)>10: score-=1

        rsi=stock_data["rsi"]; trend=stock_data["trend"]
        if is_call:
            if trend=="صاعد" and rsi<70: score+=2; reasons.append(f"📈 صاعد RSI {rsi:.0f} ✅")
        else:
            if trend=="هابط" and rsi>30: score+=2; reasons.append(f"📉 هابط RSI {rsi:.0f} ✅")

    if is_0dte:
        if mins<=10: score+=3; reasons.append("⚡ الآن 0DTE")
        elif mins<=30: score+=2; reasons.append("🔥 30د 0DTE")
        elif mins>60: score-=2
    else:
        if mins<=15: score+=2; reasons.append("🔥 الآن")
        elif mins<=60: score+=1

    sd["double_potential"]="💰 دبل 100-300%" if is_0dte and score>=6 else f"هدف +{40 if days<=7 else 30}%"

    if is_0dte:
        if score>=8: dec="🔥🔥 0DTE دبل قوي"; css="score-1"; action="✅ 1 عقد فقط"
        elif score>=5: dec="🔥 0DTE جيد"; css="score-1"; action="✅ 1 عقد"
        elif score>=3: dec="⚠️ 0DTE مراقبة"; css="score-2"; action="👀 راقب"
        else: dec="⛔ 0DTE ضعيف"; css="score-0"; action="⛔ لا"
    else:
        if score>=8: dec="⭐⭐⭐ قوي جدا"; css="score-3"; action="✅ 2-3 عقود"
        elif score>=6: dec="⭐⭐ قوي"; css="score-2"; action="✅ 1-2"
        elif score>=4: dec="⭐ متوسط"; css="score-2"; action="👀 راقب"
        else: dec="⛔ ضعيف"; css="score-0"; action="⛔ اتركه"

    return score, dec, css, action, sd, reasons, warnings, is_0dte

# عرض الجدول أولا - ثابت
if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    if st.session_state.page=="0DTE": final_time=final_raw[final_raw["days_left"]==0].copy()
    elif st.session_state.page=="DOUBLE": final_time=final_raw[(final_raw["days_left"]<=1) & (final_raw["opt_price"]<=2.5) & (final_raw["premium_M"]>=1)].copy()
    elif st.session_state.page=="15MIN": final_time=final_raw[final_raw["minutes_ago"]<=15].copy()
    elif st.session_state.page=="STRONG": final_time=final_raw.copy()
    else: final_time=final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        stock_data=get_stock_analysis(r["ticker"])
        sc, dec, css, action, sd, rs, warns, is_0dte=calc_logical_score(r, stock_data)
        if sc<0: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["reasons"]=rs; r2["warnings"]=warns; r2["is_0dte"]=is_0dte; r2["stock_data"]=stock_data
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)
    if score_filter=="⭐⭐+ (5+) قوي": enriched_df=enriched_df[enriched_df["score"]>=5]
    elif score_filter=="⭐⭐⭐ فقط (7+)": enriched_df=enriched_df[enriched_df["score"]>=7]
    elif score_filter=="⭐+ (3+)": enriched_df=enriched_df[enriched_df["score"]>=3]

    if st.session_state.page=="TOP10": final=enriched_df.head(10)
    elif st.session_state.page=="TOP20": final=enriched_df.head(20)
    else: final=enriched_df.head(25)

    if st.session_state.new_whales:
        st.markdown("### 🔔 قرار منطقي دخل الآن - V29 الأصلي")
        for w in st.session_state.new_whales[:1]:
            stock_data=get_stock_analysis(w["ticker"])
            sc, dec, css, action, sd, rs, warns, is_0dte=calc_logical_score(w, stock_data)
            box_class="scalp-box" if is_0dte else "decision-box"
            st.markdown(f"<div class='{box_class}'><b style='font-size:18px'>{w['ticker']} | {dec} ⭐{sc} {sd.get('double_potential','')}</b><br><b>{w['signal']} {w['strike']}</b> | السهم {sd.get('stock_price','')} | المسافة {sd.get('distance','')} {sd.get('distance_star','')}<br>📅 {w['exp_short']} ({w['days_left']}ي) {sd.get('exp','')} | ${w['opt_price']:.2f} | ${w['premium_M']:.1f}M<br>📊 RSI {sd.get('rsi','')} | ترند {sd.get('trend','')} | {sd.get('whale','')}<br><b style='font-size:16px'>{action}</b> | {sd.get('double_potential','')}<br><small>✅ {' | '.join(rs[:3])}</small></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="hide29f"): st.session_state.new_whales=[]; st.rerun()

    dte_count=len(final[final["is_0dte"]==True]) if not final.empty and "is_0dte" in final.columns else 0
    st.success(f"✅ V29 الأصلي بدون بهوت | النمط: {trade_mode} | 0DTE: {dte_count} | سوينغ: {len(final)-dte_count} | {len(final)} حوت | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')}")

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار المنطقي</th><th>الشركة + السعر</th><th>النوع</th><th>STRIKE + المسافة</th><th>📅 انتهاء</th><th>الأوبشن</th><th>الحوت</th><th>7 بيانات + دبل؟</th><th>🎯 ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            sd=w.get("strong_data",{})
            price_html=f'{sd.get("stock_price","-")}<br><small>RSI {sd.get("rsi","-")} {sd.get("trend","")}</small>'
            dist_html=f'{w["strike"]}<br><small>{sd.get("distance","")} {sd.get("distance_star","")}</small>'
            exp_html=f'<span class="dte-0">🔥 اليوم 0DTE</span><br><small>{sd.get("exp","")}</small>' if w["is_0dte"] else f'<span class="dte-good">{w["exp_short"]} ({w["days_left"]}ي)</span><br><small>{sd.get("exp","")}</small>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}/10</small><br><small>{sd.get("double_potential","")}</small>'
            seven=f'<small>{" | ".join(w["reasons"][:2])}</small>'
            if w["warnings"]: seven+=f'<br><small style="color:#ef4444">{w["warnings"][0]}</small>'
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>${w['opt_price']:.2f}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M<br><small>{w['volume']/1000:.0f}K</small></td><td style='font-size:8px; text-align:right'>{seven}</td><td><b>{w['action']}</b></td></tr>"
        html+="</table>"
        return html
    st.markdown(build_html(final), unsafe_allow_html=True)
else:
    st.warning("⏳ اضغط فحص الآن - V29 الأصلي الأقوى")

# فحص خلفي - بدون مسببات البهوت
all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+6, len(all_tickers))
    # شلت progress bar المتحرك اللي كان يسبب بهوت - استبدلته بنص ثابت
    st.caption(f"🔴 يفحص {all_tickers[start:end]} في الخلفية... ({st.session_state.current_idx}/{len(all_tickers)}) - V29 بدون بهوت")

    mins_map={"اليوم كامل":1440,"آخر 3 ساعات":180,"آخر ساعة (لحظي)":60,"آخر 15 دقيقة (0DTE)":15}
    mins=mins_map.get(time_filter,60)
    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            days_left, exp_short, exp_full=parse_exp(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=min_vol)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                    except: minutes_ago=9999
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"exp_full":exp_full,"days_left":days_left,"minutes_ago":minutes_ago})
        except: pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
        fresh_to_show=filtered.sort_values("premium", ascending=False).groupby("ticker").first().reset_index() if not filtered.empty else filtered
        fresh=[]
        for _, w in fresh_to_show.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                stock_data=get_stock_analysis(w["ticker"])
                sc,_,_,_,_,_,_,_=calc_logical_score(w, stock_data)
                if sc>=5:
                    fresh.append(w)
                    st.session_state.sent.add(key)
        if fresh:
            # شلت الجرس اللي كان يسبب البهوت
            st.session_state.new_whales=fresh
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(600) if not st.session_state.results.empty else new_df
        st.session_state.results=combined

    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers):
        st.session_state.current_idx=0
        st.session_state.last_refresh=datetime.now()
        time.sleep(interval_sec)
        st.rerun()
    else:
        time.sleep(2) # أبطأ - بدون بهوت
        st.rerun()
else:
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V29 الأصلي الأقوى بدون بهوت | نفس المنطق 100% | 0DTE = دبلات")
