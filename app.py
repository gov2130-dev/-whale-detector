import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time

st.set_page_config(layout="wide", page_title="Whale V32 Background Control", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:420px!important; max-width:440px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:12px!important;}
.stButton>button {width:100%!important; height:44px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:10px!important; font-weight:800!important; margin-bottom:6px!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:9px 3px; text-align:center; font-size:9px; font-weight:800;}
.whale-table td {background:#fff!important; padding:9px 3px; text-align:center; font-weight:700; font-size:10px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:9px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#8b5cf6!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-weight:900; font-size:11px;}
.score-0 {background:#1f2937!important; color:#fff!important; padding:5px 9px; border-radius:10px; font-size:10px;}
.dte-0 {background:linear-gradient(135deg,#ef4444,#f97316)!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:10px;}
.dte-good {background:#dcfce7!important; color:#166534!important; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:800; border:1px solid #22c55e;}
.status-off {background:#fee2e2; border:2px solid #ef4444; border-radius:12px; padding:12px; text-align:center; font-weight:900; color:#991b1b;}
.status-on {background:#dcfce7; border:2px solid #22c55e; border-radius:12px; padding:12px; text-align:center; font-weight:900; color:#166534;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V32 - تحكم كامل في الخلفية + بدون بهوت ✅")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM","SMH"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"
if "bg_running" not in st.session_state: st.session_state.bg_running=False
if "current_idx" not in st.session_state: st.session_state.current_idx=0

# ===== تحكم كامل في الخلفية - حل البهوت =====
st.sidebar.markdown("## 🎛️ تحكم الخلفية - حل البهوت")

# زر كبير للتحكم
st.sidebar.markdown("### 🔴 / 🟢 الخلفية")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🟢 شغل الخلفية", key="on_bg"):
        st.session_state.bg_running=True
        st.session_state.current_idx=0
        st.rerun()
with col2:
    if st.button("🔴 طف الخلفية", key="off_bg"):
        st.session_state.bg_running=False
        st.rerun()

if st.session_state.bg_running:
    st.sidebar.markdown('<div class="status-on">🟢 الخلفية شغالة - تفحص تلقائيا<br>الجدول ممكن يبهت قليلا</div>', unsafe_allow_html=True)
else:
    st.sidebar.markdown('<div class="status-off">🔴 الخلفية مطفية - بدون بهوت نهائيا<br>الجدول ثابت 100%<br>اضغط فحص الآن يدويا</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💰 فلاتر (نفس V29)")
min_prem=st.sidebar.slider("💰 أقل حوت", 100000, 5000000, 500000, 100000, key="m32")
min_vol=st.sidebar.slider("📊 أقل VOL", 1, 50000, 5000, 1000, key="v32")
trade_mode=st.sidebar.select_slider("🎯 نمطك؟", options=["سكالبينج 0DTE (دبلات)","سوينغ 3-14 يوم","الكل - 0DTE = دبل"], value="الكل - 0DTE = دبل", key="mode32")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل (0DTE دبل)","اليوم فقط 0DTE","3-14 يوم"], value="الكل (0DTE دبل)", key="exp32")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf32")

# تحكم الفحص الخلفي - فقط لما الخلفية شغالة
if st.session_state.bg_running:
    refresh_interval=st.sidebar.select_slider("⏱️ فحص الخلفية كل كم؟", options=["1 دقيقة","2 دقيقة","5 دقائق","10 دقائق"], value="2 دقيقة", key="int32")
    map_sec={"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300,"10 دقائق":600}
    interval_sec=map_sec[refresh_interval]
    st.sidebar.info(f"الخلفية تفحص كل {refresh_interval} - لو فيه بهوت اختار 5 أو 10 دقائق")
else:
    interval_sec=9999

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 عرض الجداول")
if st.sidebar.button("🔥 0DTE اليوم - دبلات", key="b0_32"): st.session_state.page="0DTE"
if st.sidebar.button("💰 دبلات محتملة", key="bDouble_32"): st.session_state.page="DOUBLE"
if st.sidebar.button("🏆 أقوى 20", key="b20_32"): st.session_state.page="TOP20"
if st.sidebar.button("🐋 أقوى 10", key="b10_32"): st.session_state.page="TOP10"
if st.sidebar.button("📋 كل اليوم", key="bAll_32"): st.session_state.page="ALL"

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 فحص يدوي - بدون بهوت")
if st.sidebar.button("🔄 فحص السوق الآن (يدوي ثابت)", key="bNow_32"):
    with st.spinner("🔍 يفحص... 15 ثانية بدون بهوت - الجدول ثابت"):
        all_tickers=get_tickers()
        new_rows=[]
        mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
        mins=mins_map.get(time_filter,60)
        prog=st.sidebar.progress(0, text="يفحص...")
        for i, t in enumerate(all_tickers):
            try:
                s=yf.Ticker(t)
                if not s.options:
                    prog.progress((i+1)/len(all_tickers))
                    continue
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
                                if minutes_ago<=mins or mins>=1440:
                                    exp_short=exp_date.strftime("%m/%d")
                                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_short,"exp_full":exp_try,"days_left":days_left,"minutes_ago":minutes_ago})
                        break
                    except: continue
            except: pass
            prog.progress((i+1)/len(all_tickers))
        if new_rows:
            new_df=pd.DataFrame(new_rows)
            combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(600) if not st.session_state.results.empty else new_df
            st.session_state.results=combined
            st.session_state.last_refresh=datetime.now()
            st.sidebar.success(f"✅ {len(new_df)} حوت جديد - الجدول ثابت بدون بهوت")
        prog.empty()

if st.sidebar.button("🗑️ مسح", key="bClear_32"):
    st.session_state.results=pd.DataFrame()
    st.session_state.last_refresh=datetime.now()

# ===== نفس منطق V29 المنطقي =====
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
    elif 1<=days<=7: score+=3; reasons.append(f"✅ {days}ي"); sd["exp"]=f"{days}ي"
    else: score+=2

    if prem>=20: score+=4; reasons.append(f"🐋 ${prem:.0f}M ضخم")
    elif prem>=5: score+=3
    elif prem>=1: score+=1
    if vol>=50000: score+=2
    elif vol>=10000: score+=1

    if is_0dte:
        if 0.2<=opt<=1.5: score+=3; reasons.append(f"💰 رخيص ${opt:.2f}=دبل")
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

# عرض الجدول ثابت
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
    if st.session_state.page=="TOP10": final=enriched_df.head(10)
    elif st.session_state.page=="TOP20": final=enriched_df.head(20)
    else: final=enriched_df.head(25)

    # حالة الخلفية
    if st.session_state.bg_running:
        st.warning(f"🟢 الخلفية شغالة كل {refresh_interval} - لو فيه بهوت اضغط 🔴 طف الخلفية | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    else:
        st.success(f"🔴 الخلفية مطفية - الجدول ثابت 100% بدون بهوت ✅ | {len(final)} حوت | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')} | اضغط 🔄 فحص السوق الآن للفحص اليدوي")

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
    st.info("🔴 الخلفية مطفية افتراضيا - بدون بهوت نهائيا\nاضغط باليسار **🔄 فحص السوق الآن (يدوي ثابت)** أول مرة - الجدول بيظهر ثابت 100%\n\nلو تبي الخلفية تشتغل تلقائيا اضغط **🟢 شغل الخلفية**")
    st.success("✅ V32 حل البهوت: الخلفية مطفية افتراضيا - انت تتحكم")

# فحص خلفي فقط لو شغال
if st.session_state.bg_running:
    all_tickers=get_tickers()
    if st.session_state.current_idx < len(all_tickers):
        start=st.session_state.current_idx; end=min(start+3, len(all_tickers))
        # بدون progress متحرك يسبب بهوت
        st.caption(f"🔴 خلفية تفحص {all_tickers[start:end]}...")

        mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
        mins=mins_map.get(time_filter,60)
        new_rows=[]
        for t in all_tickers[start:end]:
            try:
                s=yf.Ticker(t)
                if not s.options: continue
                exp=s.options[0]
                chain=s.option_chain(exp)
                days_left, exp_short, _ = (lambda e: ((datetime.strptime(e, "%Y-%m-%d") - datetime.now()).days, datetime.strptime(e, "%Y-%m-%d").strftime("%m/%d"), e))(exp)
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
                    df["premium"]=df["lastPrice"]*df["volume"]*100
                    f=df[(df["premium"]>=min_prem) & (df["volume"]>=min_vol)].copy()
                    for _, r in f.iterrows():
                        try:
                            ltd=pd.to_datetime(r.get("lastTradeDate"))
                            minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                        except: minutes_ago=9999
                        new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"exp_full":exp,"days_left":days_left,"minutes_ago":minutes_ago})
            except: pass

        if new_rows:
            new_df=pd.DataFrame(new_rows)
            combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(600) if not st.session_state.results.empty else new_df
            st.session_state.results=combined
            st.session_state.last_refresh=datetime.now()

        st.session_state.current_idx=end
        if st.session_state.current_idx>=len(all_tickers):
            st.session_state.current_idx=0
            time.sleep(interval_sec)
            st.rerun()
        else:
            time.sleep(1.5)
            st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V32 Background Control | تحكم كامل في الخلفية")
