import streamlit as st, yfinance as yf, pandas as pd, numpy as np
from datetime import datetime, timezone
import time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V28 Ultimate Decision Engine", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:400px!important; max-width:420px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:12px!important;}
.stButton>button {width:100%!important; height:42px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:10px!important; font-weight:800!important; margin-bottom:5px!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:9px 3px; text-align:center; font-size:9px; font-weight:800;}
.whale-table td {background:#fff!important; padding:9px 3px; text-align:center; font-weight:700; font-size:10px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#ef4444!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-0 {background:#1f2937!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-size:10px;}
.decision-box {background:linear-gradient(135deg,#f0fdf4,#dcfce7); border:3px solid #22c55e; border-radius:16px; padding:14px; margin:8px 0;}
.filter-box {background:#fffbeb; border:2px solid #f59e0b; border-radius:12px; padding:10px; margin:6px 0;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V28 - محرك القرار القوي النهائي 🎯")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM","SMH","XLF","TNA"]

def play_bell(t=2):
    components.html(f"<script>const c=new (window.AudioContext||window.webkitAudioContext)(); for(let i=0;i<{t};i++){{setTimeout(()=>{{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;g.gain.setValueAtTime(0.8,c.currentTime);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.8);o.start();o.stop(c.currentTime+0.8);}},i*350);}}</script>", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="TOP20"

# ===== 7 فلاتر قوية تدعم القرار =====
st.sidebar.markdown("## 🎯 V28 - 7 فلاتر قرار قوي")

st.sidebar.markdown("### 1️⃣ فلتر الحوت الأساسي")
min_prem=st.sidebar.slider("💰 أقل قيمة حوت", 100000, 5000000, 800000, 100000, key="m28")
min_vol=st.sidebar.slider("📊 أقل VOL", 1, 100000, 10000, 1000, key="v28")

st.sidebar.markdown("### 2️⃣ فلتر تاريخ الانتهاء")
exp_filter=st.sidebar.select_slider("📅 فلتر الانتهاء", options=["الكل","استبعد المنتهي","3-14 يوم فقط (الأقوى)","أسبوع فقط"], value="3-14 يوم فقط (الأقوى)", key="exp28")

st.sidebar.markdown("### 3️⃣ فلتر سعر الأوبشن")
opt_price_filter=st.sidebar.select_slider("💵 سعر الأوبشن", options=["الكل","$0.5-$5 (الأفضل)","$0.5-$3 (رخيص)","$1-$8"], value="$0.5-$5 (الأفضل)", key="opt28")

st.sidebar.markdown("### 4️⃣ فلتر المسافة STRIKE")
distance_filter=st.sidebar.select_slider("🎯 مسافة السترايك", options=["الكل","قريب ±5% (الأقوى)","قريب ±3% (سكالبينج)","±10% (سوينغ)"], value="قريب ±5% (الأقوى)", key="dist28")

st.sidebar.markdown("### 5️⃣ فلتر تقني للسهم")
rsi_filter=st.sidebar.checkbox("📈 فلتر RSI (CALL<70 PUT>30)", True, key="rsi28")
trend_filter=st.sidebar.checkbox("📊 فلتر الترند (SMA20)", True, key="trend28")

st.sidebar.markdown("### 6️⃣ فلتر وقت دخول الحوت")
time_filter=st.sidebar.select_slider("⏰ متى دخل الحوت", options=["اليوم كامل","آخر 3 ساعات","آخر ساعة (لحظي)","آخر 15 دقيقة (سكالبينج)"], value="آخر ساعة (لحظي)", key="tf28")

st.sidebar.markdown("### 7️⃣ فلتر القرار النهائي")
score_filter=st.sidebar.select_slider("⭐ أقل سكور", options=["الكل","⭐+ (3+)","⭐⭐+ (5+) قوي","⭐⭐⭐ فقط (7+) الأقوى"], value="⭐⭐+ (5+) قوي", key="score28")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["30 ثانية","1 دقيقة","2 دقيقة","5 دقائق"], value="1 دقيقة", key="int28")
map_sec={"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300}
interval_sec=map_sec[refresh_interval]

auto=st.sidebar.checkbox("⚡ فحص تلقائي بدون وميض", True, key="a28")
bell_on=st.sidebar.checkbox("🔔 جرس", True, key="bell28")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 عرض الجداول")
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b15_28"): st.session_state.page="15MIN"; st.rerun()
if st.sidebar.button("⏰ آخر ساعة", key="b60_28"): st.session_state.page="LASTHOUR"; st.rerun()
if st.sidebar.button("🏆 أقوى 20", key="b20_28"): st.session_state.page="TOP20"; st.rerun()
if st.sidebar.button("🐋 أقوى 10", key="b10_28"): st.session_state.page="TOP10"; st.rerun()
if st.sidebar.button("📋 كل اليوم", key="bAll_28"): st.session_state.page="ALL"; st.rerun()
if st.sidebar.button("🎯 قرار قوي فقط ⭐⭐⭐", key="bStrong_28"): st.session_state.page="STRONG"; st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 فحص الآن", key="bNow_28"): st.session_state.current_idx=0; st.rerun()
if st.sidebar.button("🗑️ مسح", key="bClear_28"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_stock_analysis(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="20d")
        if hist.empty or len(hist)<10: return None
        curr=hist['Close'].iloc[-1]
        sma20=hist['Close'].rolling(20).mean().iloc[-1]
        sma5=hist['Close'].rolling(5).mean().iloc[-1]
        # RSI
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        chg= (curr-hist['Close'].iloc[-2])/hist['Close'].iloc[-2]*100
        vol_avg=hist['Volume'].rolling(10).mean().iloc[-1]
        vol_today=hist['Volume'].iloc[-1]
        trend="صاعد" if curr>sma20 and sma5>sma20 else "هابط" if curr<sma20 else "عرضي"
        return {"price":curr,"sma20":sma20,"rsi":rsi,"chg":chg,"trend":trend,"vol_avg":vol_avg,"vol_today":vol_today,"vol_ratio":vol_today/(vol_avg if vol_avg>0 else 1)}
    except: return None

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

def calc_ultimate_score(row, stock_data):
    score=0; reasons=[]; warnings=[]; strong_data={}

    days=row.get("days_left",0)
    # فلتر 2: انتهاء
    if exp_filter=="استبعد المنتهي" and days<0: return -10, "⛔ منتهي", "score-0", "⛔ اتركه", {}, [], ["منتهي"]
    if exp_filter=="3-14 يوم فقط (الأقوى)" and not (3<=days<=14):
        if days<0: return -10, "⛔ منتهي", "score-0", "⛔ اتركه", {}, [], ["منتهي"]
        if not (3<=days<=14): score-=1; warnings.append(f"⚠️ {days}ي خارج 3-14")
    if exp_filter=="أسبوع فقط" and not (1<=days<=7):
        if days<0: return -10, "⛔", "score-0", "⛔", {}, [], ["منتهي"]

    # عنصر 1: تاريخ
    if days<0: score-=5; warnings.append("⛔ منتهي")
    elif days==0: score+=0; warnings.append("⚠️ 0DTE")
    elif 3<=days<=7: score+=3; reasons.append(f"✅ {days}ي مثالي"); strong_data["exp"]="⭐⭐⭐ مثالي"
    elif 8<=days<=14: score+=2; reasons.append(f"✅ {days}ي جيد"); strong_data["exp"]="⭐⭐ جيد"
    elif days<=2: score+=1; warnings.append(f"⚠️ {days}ي قليل")

    # عنصر 2: حوت + VOL
    prem=row["premium_M"]; vol=row["volume"]
    if prem>=20 and vol>=50000: score+=4; reasons.append(f"🐋🔥 ${prem:.0f}M+{vol/1000:.0f}K"); strong_data["whale"]="حوت ضخم + سيولة"
    elif prem>=5: score+=3; reasons.append(f"🐋 ${prem:.0f}M قوي"); strong_data["whale"]="حوت قوي"
    elif prem>=1: score+=1; reasons.append(f"💰 ${prem:.1f}M")

    # عنصر 3: سعر الأوبشن - فلتر 3
    opt=row["opt_price"]
    if opt_price_filter=="$0.5-$5 (الأفضل)" and not (0.5<=opt<=5):
        if opt>8: score-=1; warnings.append(f"⚠️ غالي ${opt}")
    if opt_price_filter=="$0.5-$3 (رخيص)" and not (0.5<=opt<=3): score-=1
    if 0.5<=opt<=3: score+=2; reasons.append(f"💵 ${opt:.2f} رخيص ممتاز"); strong_data["opt_price"]="سعر رخيص"
    elif 0.5<=opt<=5: score+=1; reasons.append(f"💵 ${opt:.2f} منطقي")

    # عنصر 4,5,6: بيانات السهم الحية - أقوى إضافة
    if stock_data:
        curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
        # المسافة
        if is_call: dist=(strike-curr)/curr*100
        else: dist=(curr-strike)/curr*100
        strong_data["distance"]=f"{dist:+.1f}%"
        strong_data["stock_price"]=f"${curr:.2f}"
        strong_data["rsi"]=f"{stock_data['rsi']:.0f}"
        strong_data["trend"]=stock_data["trend"]
        strong_data["vol_ratio"]=f"{stock_data['vol_ratio']:.1f}x"

        # فلتر 4: المسافة
        if distance_filter=="قريب ±5% (الأقوى)" and abs(dist)>5: score-=1; warnings.append(f"⚠️ بعيد {dist:+.1f}%")
        if distance_filter=="قريب ±3% (سكالبينج)" and abs(dist)>3: score-=2; warnings.append(f"⚠️ بعيد للسكالبينج {dist:+.1f}%")
        if abs(dist)<=3: score+=3; reasons.append(f"🎯 قريب جدا {dist:+.1f}%"); strong_data["distance_star"]="⭐⭐⭐ قريب"
        elif abs(dist)<=5: score+=2; reasons.append(f"🎯 قريب {dist:+.1f}%"); strong_data["distance_star"]="⭐⭐ قريب"
        elif abs(dist)>10: warnings.append(f"⚠️ بعيد {dist:+.1f}%")

        # فلتر 5: RSI
        if rsi_filter:
            rsi=stock_data["rsi"]
            if is_call:
                if rsi>=75: score-=2; warnings.append(f"⚠️ RSI {rsi:.0f} متشبع بيع CALL خطر")
                elif rsi<=60: score+=1; reasons.append(f"📈 RSI {rsi:.0f} ممتاز للـ CALL")
            else:
                if rsi<=25: score-=2; warnings.append(f"⚠️ RSI {rsi:.0f} تشبع بيع - PUT خطر")
                elif rsi>=40: score+=1; reasons.append(f"📉 RSI {rsi:.0f} جيد للـ PUT")

        # فلتر 5: ترند
        if trend_filter:
            trend=stock_data["trend"]
            if is_call and trend=="صاعد": score+=2; reasons.append(f"📊 ترند {trend} مع CALL ✅"); strong_data["trend_match"]="✅ ترند مع الاتجاه"
            elif not is_call and trend=="هابط": score+=2; reasons.append(f"📊 ترند {trend} مع PUT ✅"); strong_data["trend_match"]="✅ ترند مع الاتجاه"
            elif is_call and trend=="هابط": warnings.append(f"⚠️ CALL ضد ترند {trend}"); score-=1
            elif not is_call and trend=="صاعد": warnings.append(f"⚠️ PUT ضد ترند صاعد"); score-=1

        # عنصر إضافي: VOL السهم
        if stock_data["vol_ratio"]>=1.5: score+=1; reasons.append(f"🔥 حجم اليوم {stock_data['vol_ratio']:.1f}x")

    # عنصر 6: وقت دخول الحوت
    mins=row["minutes_ago"]
    if time_filter=="آخر 15 دقيقة (سكالبينج)" and mins>15: return -10, "⛔ قديم", "score-0", "⛔", {}, [], ["قديم"]
    if time_filter=="آخر ساعة (لحظي)" and mins>60: score-=2; warnings.append(f"⚠️ قديم {int(mins)}د")
    if mins<=15: score+=2; reasons.append("🔥 دخل الآن لحظي")
    elif mins<=60: score+=1; reasons.append("⏰ قبل ساعة")

    # القرار النهائي
    if score>=8: dec="⭐⭐⭐ قرار قوي جدا"; css="score-3"; action="✅ ادخل 2-3 عقود"; strong_data["final"]="ادخل بقوة"
    elif score>=6: dec="⭐⭐ قوي"; css="score-2"; action="✅ ادخل 1-2"; strong_data["final"]="ادخل"
    elif score>=4: dec="⭐ متوسط"; css="score-2"; action="👀 راقب"; strong_data["final"]="راقب"
    elif score>=2: dec="⚠️ ضعيف"; css="score-1"; action="⛔ لا تدخل"; strong_data["final"]="لا"
    else: dec="⛔ خطر"; css="score-0"; action="⛔ اتركه"; strong_data["final"]="اتركه"

    return score, dec, css, action, strong_data, reasons, warnings

# ===== عرض الجدول أولا =====
def show_table():
    if st.session_state.results.empty:
        st.warning("⏳ يفحص السوق الثلاثاء... نزل فلتر الحوت لـ 100k لو ما ظهر شيء")
        st.info("💡 السوق فاتح الآن - سيظهر حيتان خلال دقائق")
        return

    final_raw=st.session_state.results.copy()

    if st.session_state.page=="15MIN": final_time=final_raw[final_raw["minutes_ago"]<=15].copy()
    elif st.session_state.page=="LASTHOUR": final_time=final_raw[final_raw["minutes_ago"]<=60].copy()
    elif st.session_state.page=="STRONG": final_time=final_raw.copy()
    else: final_time=final_raw.copy()

    if final_time.empty:
        final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        stock_data=get_stock_analysis(r["ticker"])
        sc, dec, css, action, strong_data, reasons, warns=calc_ultimate_score(r, stock_data)
        if sc<0: continue # فلترة المنتهي والقديم
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=strong_data; r2["reasons"]=reasons; r2["warnings"]=warns; r2["stock_data"]=stock_data
        enriched.append(r2)

    if not enriched:
        st.warning("⏳ كل الحيتان تفلترت بسبب الفلاتر القوية - خفف فلتر تاريخ الانتهاء أو المسافة")
        enriched=[]
        for _, r in final_raw.iterrows():
            stock_data=get_stock_analysis(r["ticker"])
            sc, dec, css, action, strong_data, reasons, warns=calc_ultimate_score(r, stock_data)
            r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=strong_data; r2["reasons"]=reasons; r2["warnings"]=warns; r2["stock_data"]=stock_data
            enriched.append(r2)

    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)

    # فلتر السكور النهائي
    if score_filter=="⭐⭐+ (5+) قوي": enriched_df=enriched_df[enriched_df["score"]>=5]
    elif score_filter=="⭐⭐⭐ فقط (7+) الأقوى": enriched_df=enriched_df[enriched_df["score"]>=7]
    elif score_filter=="⭐+ (3+)": enriched_df=enriched_df[enriched_df["score"]>=3]

    if st.session_state.page=="TOP10": final=enriched_df.head(10)
    elif st.session_state.page=="TOP20": final=enriched_df.head(20)
    elif st.session_state.page=="STRONG": final=enriched_df[enriched_df["score"]>=7].head(20)
    else: final=enriched_df.head(25)

    if final.empty:
        st.error("⛔ كل الحيتان تفلترت - خفف الفلاتر من اليسار (اختار الكل)")
        final=enriched_df.head(10) if not enriched_df.empty else pd.DataFrame(enriched).sort_values("score", ascending=False).head(10)

    # تنبيه
    if st.session_state.new_whales:
        st.markdown("### 🔔 قرار قوي دخل الآن - مع 7 بيانات")
        for w in st.session_state.new_whales[:1]:
            stock_data=get_stock_analysis(w["ticker"])
            sc, dec, css, action, sd, rs, warns=calc_ultimate_score(w, stock_data)
            if sc>=5:
                st.markdown(f"""
                <div class='decision-box'>
                <b style='font-size:18px'>🎯 {w['ticker']} | {dec} ⭐{sc}</b><br>
                <b>{w['signal']} {w['strike']}</b> | السهم {sd.get('stock_price','')} | المسافة {sd.get('distance','')} {sd.get('distance_star','')}<br>
                📅 {w['exp_short']} ({w['days_left']}ي) | {sd.get('exp','')} | ${w['opt_price']:.2f} | ${w['premium_M']:.1f}M<br>
                📊 RSI {sd.get('rsi','')} | ترند {sd.get('trend','')} {sd.get('trend_match','')} | VOL {sd.get('vol_ratio','')} | {sd.get('whale','')}<br>
                <b style='font-size:16px'>{action}</b> | وقف -30% | هدف +60%<br>
                <small>✅ {' | '.join(rs[:4])}</small>
                </div>
                """, unsafe_allow_html=True)

        if st.button("✖️ اخفاء", key="hide28"): st.session_state.new_whales=[]; st.rerun()

    # ملخص الفلاتر
    active_filters=[]
    if exp_filter!="الكل": active_filters.append(exp_filter)
    if opt_price_filter!="الكل": active_filters.append(opt_price_filter)
    if distance_filter!="الكل": active_filters.append(distance_filter)
    if rsi_filter: active_filters.append("RSI")
    if trend_filter: active_filters.append("ترند")
    st.markdown(f"<div class='filter-box'>🎯 <b>فلاتر نشطة:</b> {', '.join(active_filters)} | <b>فلتر الوقت:</b> {time_filter} | <b>السكور:</b> {score_filter} | يظهر {len(final)} حوت قوي</div>", unsafe_allow_html=True)

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار القوي</th><th>الشركة + السعر الحي</th><th>النوع</th><th>STRIKE + المسافة</th><th>📅 انتهاء</th><th>الأوبشن</th><th>الحوت</th><th>7 بيانات قوية</th><th>🎯 ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            sd=w.get("strong_data",{}); stock_data=w.get("stock_data")
            price_html=f'{sd.get("stock_price","-")}<br><small>RSI {sd.get("rsi","-")} {sd.get("trend","")}</small>' if stock_data else "-"
            dist_html=f'{w["strike"]}<br><small style="background:{"#dcfce7" if "⭐⭐⭐" in sd.get("distance_star","") else "#fef3c7"}; padding:2px 4px; border-radius:4px;">{sd.get("distance","")} {sd.get("distance_star","")}</small>'
            exp_html=f'{w["exp_short"]} ({w["days_left"]}ي)<br><small>{sd.get("exp","")}</small>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}/10</small>'
            seven_data=f'<small>{sd.get("whale","")}<br>VOL {sd.get("vol_ratio","")} {sd.get("trend_match","")}<br>{" | ".join(w["reasons"][:2])}</small>'
            if w["warnings"]: seven_data+=f'<br><small style="color:#ef4444">{w["warnings"][0]}</small>'
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>${w['opt_price']:.2f}<br><small>{sd.get('opt_price','')}</small></td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M<br><small>{w['volume']/1000:.0f}K</small></td><td style='font-size:8px; text-align:right'>{seven_data}</td><td><b>{w['action']}</b><br><small>وقف -30%</small><br><small>هدف +60%</small></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)

    with st.expander("🧠 كيف تتخذ قرار قوي - شرح 7 فلاتر"):
        st.markdown("""
        **القرار القوي = حوت + 7 بيانات:**

        **1. 💰 قيمة الحوت:** $20M+ مع VOL 50K+ = حوت حقيقي مو وهمي

        **2. 📅 تاريخ الانتهاء:** 3-14 يوم = أفضل منطقة - وقت كافي وحركة سريعة. استبعد المنتهي والـ 0DTE

        **3. 💵 سعر الأوبشن:** $0.5-$5 تقدر تشتري 10-20 عقد. $15+ غالي وخطير

        **4. 🎯 مسافة السترايك:** قريب ±5% من سعر السهم = يربح بسرعة. بعيد ±20% = مستحيل

        **5. 📈 RSI + ترند:**
        - CALL + RSI<70 + ترند صاعد = ⭐⭐⭐
        - CALL + RSI 80 + ترند هابط = ⛔ ضدك
        - PUT + RSI>30 + ترند هابط = ⭐⭐⭐
        - PUT + RSI 20 + ترند صاعد = ⛔

        **6. ⏰ وقت دخول الحوت:** قبل 15 دقيقة = لحظي قوي. قبل 5 ساعات = قديم

        **7. 📊 حجم السهم اليوم:** VOL 1.5x أعلى من المتوسط = الكل يدخل

        **النتيجة:**
        - ⭐⭐⭐ 8-10 = ادخل 2-3 عقود، وقف -30%، هدف +60-100%
        - ⭐⭐ 5-7 = ادخل 1-2
        - أقل من 5 = لا تدخل مهما كان الحوت كبير
        """)

# اعرض الجدول
show_table()

# افحص
all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+4, len(all_tickers))
    st.progress(end/len(all_tickers), text=f"🔴 يفحص {all_tickers[start:end]} - الثلاثاء مباشر + 7 فلاتر")
    mins_map={"آخر 15 دقيقة (سكالبينج)":15,"آخر ساعة (لحظي)":60,"آخر 3 ساعات":180,"اليوم كامل":1440}
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
        # فلتر أولي
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df

        fresh_to_show=filtered.sort_values("premium", ascending=False).groupby("ticker").first().reset_index() if not filtered.empty else filtered

        fresh=[]
        for _, w in fresh_to_show.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                stock_data=get_stock_analysis(w["ticker"])
                sc,_,_,_,_,_,_=calc_ultimate_score(w, stock_data)
                if sc>=5: # فقط القرار القوي
                    fresh.append(w)
                    st.session_state.sent.add(key)
        if fresh and bell_on:
            play_bell(2)
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
        time.sleep(0.8)
        st.rerun()
else:
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V28 Ultimate Decision Engine | 7 فلاتر قرار قوي | الثلاثاء مباشر")
