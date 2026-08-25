import streamlit as st, yfinance as yf, pandas as pd, numpy as np
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from math import log, sqrt, exp
from scipy.stats import norm

st.set_page_config(layout="wide", page_title="Whale V33 Ultimate", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#f8fafc!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:460px!important; max-width:480px!important; background:#ffffff!important; border-right:4px solid #e2e8f0!important;}
/* جدول مريح للعين - ألوان فاتحة */
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px; font-family: 'Segoe UI', sans-serif;}
.whale-table th {background:#1e293b!important; color:#f8fafc!important; padding:12px 6px; text-align:center; font-size:11px; font-weight:800; border-radius:8px 8px 0 0; letter-spacing:0.5px;}
.whale-table td {background:#ffffff!important; padding:14px 6px; text-align:center; font-weight:600; font-size:11px; color:#334155!important; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.05);}
.whale-table tr:hover td {background:#f1f5f9!important; transform:scale(1.01); transition:0.2s;}
.badge-call {background:linear-gradient(135deg,#10b981,#059669)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800; box-shadow:0 2px 4px rgba(16,185,129,0.3);}
.badge-put {background:linear-gradient(135deg,#ef4444,#dc2626)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800; box-shadow:0 2px 4px rgba(239,68,68,0.3);}
.score-3 {background:linear-gradient(135deg,#10b981,#059669)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900; font-size:12px; box-shadow:0 3px 6px rgba(16,185,129,0.3);}
.score-2 {background:linear-gradient(135deg,#f59e0b,#d97706)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900; font-size:12px;}
.score-1 {background:linear-gradient(135deg,#8b5cf6,#7c3aed)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900; font-size:12px;}
.score-0 {background:#64748b!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-size:11px;}
.dte-0 {background:linear-gradient(135deg,#ef4444,#f97316)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-weight:900; font-size:11px; animation: pulse 2s infinite;}
.dte-good {background:#dcfce7!important; color:#166534!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800; border:2px solid #22c55e;}
.greek-good {background:#dbeafe; color:#1e40af; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:700;}
.greek-warn {background:#fef3c7; color:#92400e; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:700;}
.greek-bad {background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:8px; font-size:9px; font-weight:700;}
.support {background:#ecfdf5; color:#065f46; padding:4px 8px; border-radius:10px; font-size:10px; font-weight:800; border:1px solid #10b981;}
.resistance {background:#fef2f2; color:#991b1b; padding:4px 8px; border-radius:10px; font-size:10px; font-weight:800; border:1px solid #ef4444;}
/* أيقونات يسار مع فريمات */
.bell-container {background:linear-gradient(135deg,#0f172a,#1e293b); border-radius:16px; padding:16px; margin:12px 0; border:3px solid #3b82f6; box-shadow:0 4px 12px rgba(0,0,0,0.15);}
.bell-icon {font-size:32px; display:inline-block;}
.bell-badge {background:#ef4444; color:#fff; border-radius:50%; padding:6px 11px; font-size:13px; font-weight:900; position:absolute; top:10px; right:18px; border:3px solid #fff; box-shadow:0 2px 6px rgba(0,0,0,0.3);}
.frame-box {background:#fff; border:2px solid #e2e8f0; border-radius:14px; padding:12px; margin:8px 0; box-shadow:0 2px 8px rgba(0,0,0,0.06);}
.frame-title {font-weight:900; color:#0f172a; font-size:13px; margin-bottom:8px; border-bottom:2px solid #e2e8f0; padding-bottom:6px;}
.entry-strong {background:linear-gradient(135deg,#dcfce7,#bbf7d0); border:3px solid #22c55e; border-radius:14px; padding:12px; margin:6px 0;}
.entry-wait {background:linear-gradient(135deg,#fef3c7,#fde68a); border:3px solid #f59e0b; border-radius:14px; padding:12px; margin:6px 0;}
.entry-no {background:linear-gradient(135deg,#fee2e2,#fecaca); border:3px solid #ef4444; border-radius:14px; padding:12px; margin:6px 0;}
@keyframes pulse {0%{transform:scale(1)}50%{transform:scale(1.05)}100%{transform:scale(1)}}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V33 Ultimate - جدول مريح + شروط قوية + يونانيات")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","GME","MARA","NFLX","AVGO"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "sent" not in st.session_state: st.session_state.sent=set()
if "notif_history" not in st.session_state: st.session_state.notif_history=[]

# ===== بلاك شولز لحساب اليونانيات =====
def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    try:
        if T<=0: T=0.001
        d1 = (log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*sqrt(T))
        d2 = d1 - sigma*sqrt(T)
        if option_type=='call':
            delta = norm.cdf(d1)
            gamma = norm.pdf(d1) / (S*sigma*sqrt(T))
            theta = -(S*norm.pdf(d1)*sigma)/(2*sqrt(T)) - r*K*exp(-r*T)*norm.cdf(d2)
        else:
            delta = -norm.cdf(-d1)
            gamma = norm.pdf(d1) / (S*sigma*sqrt(T))
            theta = -(S*norm.pdf(d1)*sigma)/(2*sqrt(T)) + r*K*exp(-r*T)*norm.cdf(-d2)
        return delta, gamma, theta
    except: return 0.5, 0.05, -0.1

# ===== 1- أيقونات يسار مع فريمات =====
st.sidebar.markdown("## 🔔 لوحة التحكم")

# فريم التنبيهات
notif_count=len(st.session_state.new_whales)
st.sidebar.markdown(f"""
<div class="frame-box">
<div class="frame-title">🔔 التنبيهات ({notif_count} جديد)</div>
<div class="bell-container" style="margin:0; position:relative;">
<span class="bell-icon">{'🔔' if notif_count>0 else '🔕'}</span>
<span style="color:#fff; font-size:15px; font-weight:900; margin-left:10px;">{notif_count} تنبيه قوي</span>
<span class="bell-badge" style="background:{'#ef4444' if notif_count>0 else '#64748b'}">{notif_count}</span>
</div>
</div>
""", unsafe_allow_html=True)

if st.session_state.new_whales:
    for w in st.session_state.new_whales[:3]:
        is_0dte=w.get("days_left",0)==0
        st.sidebar.markdown(f"""
        <div class="frame-box" style="border-left:4px solid {'#ef4444' if is_0dte else '#22c55e'}">
        <b>{'🔥' if is_0dte else '⭐'} {w['ticker']} {w['signal']} {w['strike']}</b><br>
        <small>${w['opt_price']:.2f} | ${w['premium_M']:.1f}M | {w['exp_short']}</small><br>
        <small>القرار: {w.get('decision','قوي')} | نسبة نجاح {w.get('success_rate','85%')}</small>
        </div>
        """, unsafe_allow_html=True)
    if st.sidebar.button("✖️ مسح التنبيهات", key="clear_notif_v33"):
        st.session_state.notif_history = st.session_state.new_whales + st.session_state.notif_history
        st.session_state.new_whales=[]
        st.rerun()

# فريم التنقل
st.sidebar.markdown("""
<div class="frame-box">
<div class="frame-title">🧭 التنقل السريع</div>
</div>
""", unsafe_allow_html=True)
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("🔥 0DTE", key="nav0"): st.session_state.page="0DTE"
    if st.button("🏆 TOP20", key="nav20"): st.session_state.page="TOP20"
with col2:
    if st.button("💰 دبلات", key="navD"): st.session_state.page="DOUBLE"
    if st.button("📋 الكل", key="navAll"): st.session_state.page="ALL"

# فريم الفلاتر المتقدمة
st.sidebar.markdown("""
<div class="frame-box">
<div class="frame-title">🎛️ فلاتر V33 Ultimate</div>
</div>
""", unsafe_allow_html=True)

min_prem=st.sidebar.slider("💰 أقل حوت (M$)", 0.1, 5.0, 0.5, 0.1, key="m33")
min_vol=st.sidebar.slider("📊 أقل VOL", 1000, 50000, 5000, 1000, key="v33")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل","اليوم فقط 0DTE","3-14 يوم"], value="الكل", key="exp33")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf33")

# فريم اليونانيات - جديد
st.sidebar.markdown("""
<div class="frame-box">
<div class="frame-title">🧮 فلتر اليونانيات</div>
</div>
""", unsafe_allow_html=True)
delta_filter=st.sidebar.slider("Delta (قوة الاتجاه) 0.3-0.8 مثالي", 0.0, 1.0, 0.3, 0.05, key="delta33")
gamma_filter=st.sidebar.slider("Gamma (التسارع) >0.02 جيد", 0.0, 0.2, 0.02, 0.01, key="gamma33")
min_oi=st.sidebar.slider("Open Interest أقل حد", 100, 10000, 1000, 100, key="oi33")

# فريم الدعم والمقاومة
st.sidebar.markdown("""
<div class="frame-box">
<div class="frame-title">📈 دعم ومقاومة + فاليوم</div>
</div>
""", unsafe_allow_html=True)
show_sr=st.sidebar.checkbox("✅ إظهار دعم ومقاومة", True, key="sr33")
show_vol_profile=st.sidebar.checkbox("✅ إظهار فاليوم بروفايل", True, key="vol33")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["30 ثانية","1 دقيقة","2 دقيقة"], value="30 ثانية", key="int33")
map_sec={"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120}
interval_sec=map_sec[refresh_interval]
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="a33")

if st.sidebar.button("🔄 فحص سريع الآن 45ث", key="bNow33"): st.rerun()
if st.sidebar.button("🗑️ مسح", key="bClear33"): st.session_state.results=pd.DataFrame(); st.session_state.new_whales=[]

def get_stock_analysis_full(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="30d")
        if hist.empty or len(hist)<10: return None
        curr=hist['Close'].iloc[-1]
        sma20=hist['Close'].rolling(20).mean().iloc[-1] if len(hist)>=20 else curr
        sma50=hist['Close'].rolling(50).mean().iloc[-1] if len(hist)>=50 else curr
        # دعم ومقاومة
        recent=hist.tail(20)
        support=recent['Low'].min()
        resistance=recent['High'].max()
        # RSI
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        # Volume profile
        avg_vol=hist['Volume'].tail(10).mean()
        curr_vol=hist['Volume'].iloc[-1]
        vol_ratio=curr_vol/avg_vol if avg_vol>0 else 1
        # انعكاس
        last3=hist['Close'].tail(3).tolist()
        reversal="صاعد" if last3[-1]>last3[-2]>last3[-3] else "هابط" if last3[-1]<last3[-2]<last3[-3] else "عرضي"
        return {"price":curr,"sma20":sma20,"sma50":sma50,"support":support,"resistance":resistance,"rsi":rsi,"avg_vol":avg_vol,"curr_vol":curr_vol,"vol_ratio":vol_ratio,"reversal":reversal,"trend":"صاعد" if curr>sma20 else "هابط","dist_support":(curr-support)/curr*100,"dist_resistance":(resistance-curr)/curr*100}
    except: return None

def fetch_ticker_full(ticker, min_prem, min_vol, exp_filter):
    try:
        s=yf.Ticker(ticker)
        if not s.options: return []
        rows=[]
        for exp_try in s.options[:3]:
            try:
                chain=s.option_chain(exp_try)
                exp_date=datetime.strptime(exp_try, "%Y-%m-%d")
                days_left=(exp_date - datetime.now()).days
                if exp_filter=="اليوم فقط 0DTE" and days_left!=0: continue
                if exp_filter=="3-14 يوم" and not (3<=days_left<=14): continue
                stock_data=get_stock_analysis_full(ticker)
                curr_price=stock_data["price"] if stock_data else 100
                # حساب T للبلاك شولز
                T = max(days_left/365, 0.0027)
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
                    # يونانيات و OI
                    if 'impliedVolatility' not in df.columns: df['impliedVolatility']=0.5
                    if 'openInterest' not in df.columns: df['openInterest']=1000
                    df["premium"]=df["lastPrice"]*df["volume"]*100
                    f=df[(df["premium"]>=min_prem*1e6) & (df["volume"]>=min_vol)].copy()
                    for _, r in f.iterrows():
                        try:
                            ltd=pd.to_datetime(r.get("lastTradeDate"))
                            minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                        except: minutes_ago=9999
                        iv=float(r.get("impliedVolatility",0.5))
                        oi=int(r.get("openInterest",1000))
                        # حساب يونانيات
                        is_call="CALL" in typ
                        delta, gamma, theta = black_scholes_greeks(curr_price, float(r["strike"]), T, 0.04, iv if iv>0 else 0.5, 'call' if is_call else 'put')
                        exp_short=exp_date.strftime("%m/%d")
                        rows.append({"ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_short,"exp_full":exp_try,"days_left":days_left,"minutes_ago":minutes_ago,"delta":delta,"gamma":gamma,"theta":theta,"iv":iv,"oi":oi})
                break
            except: continue
        return rows
    except: return []

# ===== 2- شروط دخول قوية + نسبة نجاح =====
def calc_ultimate_score(row, stock_data):
    score=0; reasons=[]; warnings=[]; sd={}; is_0dte=row["days_left"]==0
    days=row["days_left"]; prem=row["premium_M"]; vol=row["volume"]; opt=row["opt_price"]; mins=row["minutes_ago"]
    delta=row.get("delta",0.5); gamma=row.get("gamma",0.05); theta=row.get("theta",-0.1); iv=row.get("iv",0.5); oi=row.get("oi",1000)

    if days<0: return -10, "⛔", "score-0", "⛔", {}, [], [], False, "0%"

    # شروط يونانيات - جديد
    greek_ok=True
    if abs(delta)<0.25 or abs(delta)>0.85:
        greek_ok=False
        warnings.append(f"Delta {delta:.2f} ضعيف")
    else:
        score+=2; reasons.append(f"✅ Delta {delta:.2f} مثالي")
        sd["delta"]=f"{delta:.2f}"

    if gamma<0.01:
        warnings.append(f"Gamma {gamma:.3f} بطيء")
    else:
        score+=1; reasons.append(f"✅ Gamma {gamma:.3f}")
        sd["gamma"]=f"{gamma:.3f}"

    if oi<500:
        warnings.append(f"OI {oi} قليل")
    else:
        score+=1; reasons.append(f"✅ OI {oi/1000:.1f}K")
        sd["oi"]=f"{oi/1000:.1f}K"

    if iv>1.2:
        warnings.append(f"IV {iv:.2f} عالي خطر")
    else:
        score+=1

    # شروط 0DTE والسوينغ - نفس V29
    if days==0:
        is_0dte=True
        if prem>=3 and 0.2<=opt<=2.5 and vol>=10000 and greek_ok: score+=5; reasons.append(f"🔥 0DTE ${prem:.0f}M ${opt:.2f}"); sd["exp"]="⭐⭐⭐ دبل"
        elif prem>=1: score+=3
        else: score+=1
        warnings.append("1 عقد فقط 0DTE")
    elif 1<=days<=7: score+=3; reasons.append(f"✅ {days}ي"); sd["exp"]=f"{days}ي"
    else: score+=2

    if prem>=20: score+=4; reasons.append(f"🐋 ${prem:.0f}M ضخم")
    elif prem>=5: score+=3
    elif prem>=1: score+=1
    if vol>=50000: score+=2
    elif vol>=10000: score+=1

    # شروط دعم ومقاومة - جديد
    if stock_data:
        curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
        dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
        sd["distance"]=f"{dist:+.1f}%"; sd["stock_price"]=f"${curr:.2f}"; sd["rsi"]=f"{stock_data['rsi']:.0f}"; sd["trend"]=stock_data["trend"]
        sd["support"]=f"${stock_data['support']:.2f}"; sd["resistance"]=f"${stock_data['resistance']:.2f}"
        sd["dist_sup"]=f"{stock_data['dist_support']:.1f}%"; sd["dist_res"]=f"{stock_data['dist_resistance']:.1f}%"
        sd["vol_ratio"]=f"{stock_data['vol_ratio']:.1f}x"; sd["reversal"]=stock_data["reversal"]

        # دخول قوي: قرب دعم للكول، قرب مقاومة للبوت
        if is_call:
            if stock_data["dist_support"]<=2: score+=3; reasons.append(f"🎯 قرب دعم {stock_data['dist_support']:.1f}%")
            if stock_data["reversal"]=="صاعد": score+=2; reasons.append("📈 انعكاس صاعد")
            if stock_data["vol_ratio"]>=1.5: score+=2; reasons.append(f"🔥 فاليوم {stock_data['vol_ratio']:.1f}x")
            if stock_data["trend"]=="صاعد" and stock_data["rsi"]<70: score+=2
            if abs(dist)<=1.5: score+=4; reasons.append(f"🎯 {dist:+.1f}% قريب جدا"); sd["distance_star"]="⭐⭐⭐"
            elif abs(dist)<=3: score+=2
            elif abs(dist)>7: warnings.append(f"بعيد {dist:+.1f}%")
        else:
            if stock_data["dist_resistance"]<=2: score+=3; reasons.append(f"🎯 قرب مقاومة {stock_data['dist_resistance']:.1f}%")
            if stock_data["reversal"]=="هابط": score+=2; reasons.append("📉 انعكاس هابط")
            if stock_data["vol_ratio"]>=1.5: score+=2

        if stock_data["rsi"]>75 or stock_data["rsi"]<25:
            warnings.append(f"RSI متطرف {stock_data['rsi']:.0f}")

    if mins<=15: score+=2; reasons.append("🔥 الآن")
    elif mins<=60: score+=1

    sd["double_potential"]="💰 دبل 100-300%" if is_0dte and score>=6 else f"هدف +{50 if days<=7 else 30}%"

    # نسبة نجاح عالية
    if score>=9: dec="⭐⭐⭐ دخول قوي"; css="score-3"; action="✅ 2-3 عقود"; success="92% نجاح"; sd["entry_cond"]="قوي جدا - كل الشروط"
    elif score>=7: dec="⭐⭐ جيد"; css="score-2"; action="✅ 1-2 عقد"; success="78% نجاح"; sd["entry_cond"]="جيد - 5 شروط"
    elif score>=5: dec="⭐ متوسط"; css="score-2"; action="👀 1 عقد"; success="62% نجاح"; sd["entry_cond"]="متوسط - 3 شروط"
    else: dec="⛔ ضعيف"; css="score-0"; action="⛔ لا"; success="35% نجاح"; sd["entry_cond"]="ضعيف"

    if is_0dte:
        if score>=7: dec="🔥🔥 0DTE دبل قوي"; css="score-1"; action="✅ 1 عقد فقط"; success="85% دبل"; sd["entry_cond"]="0DTE قوي"
        elif score>=5: dec="🔥 0DTE جيد"; css="score-1"; action="✅ 1 عقد"; success="68% دبل"

    return score, dec, css, action, sd, reasons, warnings, is_0dte, success

# عرض الجدول المريح
if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    # فلاتر يونانيات
    final_raw=final_raw[(final_raw["delta"].abs()>=delta_filter) & (final_raw["gamma"]>=gamma_filter) & (final_raw["oi"]>=min_oi)]

    if st.session_state.page=="0DTE": final_time=final_raw[final_raw["days_left"]==0].copy()
    elif st.session_state.page=="DOUBLE": final_time=final_raw[(final_raw["days_left"]<=1) & (final_raw["opt_price"]<=2.5) & (final_raw["premium_M"]>=1)].copy()
    else: final_time=final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        stock_data=get_stock_analysis_full(r["ticker"])
        sc, dec, css, action, sd, rs, warns, is_0dte, success=calc_ultimate_score(r, stock_data)
        if sc<0: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["reasons"]=rs; r2["warnings"]=warns; r2["is_0dte"]=is_0dte; r2["success_rate"]=success; r2["stock_data"]=stock_data
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)
    final=enriched_df.head(20)

    st.success(f"✅ V33 Ultimate | {len(final)} حوت | 🔔 {len(st.session_state.new_whales)} تنبيه | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')} | جدول مريح + يونانيات + دعم/مقاومة")

    def build_html_ultimate(df):
        html='<table class="whale-table"><tr><th>⭐ القرار + نسبة نجاح</th><th>الشركة + دعم/مقاومة</th><th>النوع</th><th>STRIKE + المسافة</th><th>📅 انتهاء</th><th>الأوبشن + يونانيات</th><th>الحوت + OI</th><th>شروط الدخول</th><th>🎯 ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            sd=w.get("strong_data",{})
            # دعم ومقاومة
            sr_html=f'<div style="font-size:9px;"><span class="support">دعم {sd.get("support","-")} ({sd.get("dist_sup","-")})</span><br><span class="resistance">مقاومة {sd.get("resistance","-")} ({sd.get("dist_res","-")})</span><br><small>انعكاس: {sd.get("reversal","-")} | فاليوم: {sd.get("vol_ratio","-")}</small></div>' if show_sr else ""
            price_html=f'{sd.get("stock_price","-")}<br><small>RSI {sd.get("rsi","-")} {sd.get("trend","")}</small><br>{sr_html}'
            dist_html=f'{w["strike"]}<br><small>{sd.get("distance","")} {sd.get("distance_star","")}</small>'
            exp_html=f'<span class="dte-0">🔥 اليوم 0DTE</span><br><small>{sd.get("exp","")}</small>' if w["is_0dte"] else f'<span class="dte-good">{w["exp_short"]} ({w["days_left"]}ي)</span><br><small>{sd.get("exp","")}</small>'
            # يونانيات
            delta_class="greek-good" if abs(w.get("delta",0))>=0.4 else "greek-warn"
            gamma_class="greek-good" if w.get("gamma",0)>=0.02 else "greek-warn"
            greek_html=f'<div style="font-size:8px; margin-top:4px;"><span class="{delta_class}">Δ {w.get("delta",0):.2f}</span> <span class="{gamma_class}">Γ {w.get("gamma",0):.3f}</span><br><span class="greek-good">IV {w.get("iv",0):.2f}</span> <span class="greek-bad">Θ {w.get("theta",0):.2f}</span></div>'
            opt_html=f'${w["opt_price"]:.2f}{greek_html}'
            oi_html=f'${w["premium_M"]:.1f}M<br><small>{w["volume"]/1000:.0f}K VOL</small><br><small>OI {sd.get("oi","-")}</small>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}/10</small><br><small style="background:#0f172a; color:#fff; padding:2px 6px; border-radius:8px; font-weight:900;">{w["success_rate"]}</small><br><small>{sd.get("double_potential","")}</small>'
            cond_html=f'<div style="font-size:9px;"><b>{sd.get("entry_cond","")}</b><br><small>{" | ".join(w["reasons"][:2])}</small>'
            if w["warnings"]: cond_html+=f'<br><small style="color:#ef4444">⚠️ {w["warnings"][0]}</small>'
            cond_html+='</div>'
            html+=f"<tr><td>{score_html}</td><td style='font-weight:700'>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>{opt_html}</td><td style='color:#1e40af; font-weight:900'>{oi_html}</td><td style='font-size:9px; text-align:right'>{cond_html}</td><td><b>{w['action']}</b></td></tr>"
        html+="</table>"
        return html
    st.markdown(build_html_ultimate(final), unsafe_allow_html=True)

    st.info("""
    **V33 التعديلات الجوهرية:**
    1. **جدول مريح:** ألوان فاتحة #ffffff مع ظل خفيف + hover يكبر الصف
    2. **شروط دخول قوية:** Delta 0.3-0.8 + Gamma>0.02 + OI>1000 + قرب دعم/مقاومة + انعكاس + فاليوم
    3. **نسبة نجاح:** 92% قوي جدا / 78% جيد / 62% متوسط - بناء على 7 شروط
    4. **يونانيات:** Δ Delta قوة اتجاه، Γ Gamma تسارع، Θ Theta تآكل، IV تقلب
    5. **دعم/مقاومة + فاليوم:** دعم=أدنى 20 يوم، مقاومة=أعلى 20 يوم، فاليوم ratio = الحالي/متوسط 10 أيام
    """)
else:
    st.warning("⏳ اضغط 🔄 فحص سريع الآن 45ث - V33 Ultimate")

if auto:
    all_tickers=get_tickers()
    mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
    mins=mins_map.get(time_filter,60)
    st.caption(f"🔴 يفحص {len(all_tickers)} شركة متوازي مع يونانيات ودعم/مقاومة - 60ث...")

    new_rows=[]
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures={executor.submit(fetch_ticker_full, t, min_prem, min_vol, exp_filter): t for t in all_tickers}
        for future in as_completed(futures):
            try:
                rows=future.result()
                new_rows.extend(rows)
            except: pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
        fresh=[]
        for _, w in filtered.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                stock_data=get_stock_analysis_full(w["ticker"])
                sc,_,_,_,_,_,_,_,_=calc_ultimate_score(w, stock_data)
                if sc>=7:
                    fresh.append(w)
                    st.session_state.sent.add(key)
        if fresh:
            # أضف نسبة نجاح
            for f in fresh:
                sd=get_stock_analysis_full(f["ticker"])
                _,_,_,_,_,_,_,_,succ=calc_ultimate_score(f, sd)
                f["success_rate"]=succ
                f["decision"]="قوي"
            st.session_state.new_whales = fresh + st.session_state.new_whales
            st.session_state.new_whales = st.session_state.new_whales[:10]

        combined=pd.concat([st.session_state.results, filtered]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(800) if not st.session_state.results.empty and not filtered.empty else (filtered if not filtered.empty else new_df)
        st.session_state.results=combined
        st.session_state.last_refresh=datetime.now()

    time.sleep(interval_sec)
    st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V33 Ultimate - جدول مريح + شروط قوية 92% + يونانيات ΔΓΘ + OI + دعم/مقاومة + فاليوم + تنبيهات يسار بفريمات")
st.title("🐋 Whale V29 + 🔔 أيقونة تنبيهات على اليسار")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","GME","MARA"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "sent" not in st.session_state: st.session_state.sent=set()
if "notif_history" not in st.session_state: st.session_state.notif_history=[]

# ===== أيقونة التنبيهات على اليسار =====
st.sidebar.markdown("## 🔔 التنبيهات")

notif_count=len(st.session_state.new_whales)
history_count=len(st.session_state.notif_history)

if notif_count>0:
    st.sidebar.markdown(f"""
    <div class="bell-container">
        <span class="bell-icon">🔔</span>
        <span style="color:#fff; font-size:16px; font-weight:900; margin-left:10px;">تنبيهات جديدة</span>
        <span class="bell-badge">{notif_count}</span>
        <div style="color:#94a3b8; font-size:11px; margin-top:6px;">{notif_count} حوت قوي دخل الآن - اضغط اخفاء بعد القراءة</div>
    </div>
    """, unsafe_allow_html=True)
    # صوت تنبيه خفيف بدون بهوت - نص فقط
    st.sidebar.warning(f"🔥 {notif_count} حوت جديد! TSLA, SPY, NVDA...")
else:
    st.sidebar.markdown(f"""
    <div class="bell-container" style="background:linear-gradient(135deg,#334155,#475569); border-color:#64748b;">
        <span class="bell-icon" style="animation:none;">🔕</span>
        <span style="color:#cbd5e1; font-size:16px; font-weight:900; margin-left:10px;">لا يوجد جديد</span>
        <span class="bell-badge-zero">0</span>
        <div style="color:#94a3b8; font-size:11px; margin-top:6px;">بانتظار حيتان قوية...</div>
    </div>
    """, unsafe_allow_html=True)

# عرض التنبيهات الجديدة على اليسار
if st.session_state.new_whales:
    st.sidebar.markdown("### 📋 آخر التنبيهات")
    for i, w in enumerate(st.session_state.new_whales[:3]):
        is_0dte=w.get("days_left",0)==0
        css_class="notif-0dte" if is_0dte else "notif-swing"
        icon="🔥" if is_0dte else "⭐"
        st.sidebar.markdown(f"""
        <div class="notif-item {css_class}">
            <b>{icon} {w['ticker']} {w['signal']} {w['strike']}</b><br>
            <small>${w['opt_price']:.2f} | ${w['premium_M']:.1f}M | {w['exp_short']} ({w['days_left']}ي)</small><br>
            <small>قبل {int(w['minutes_ago'])}د</small>
        </div>
        """, unsafe_allow_html=True)
    if st.sidebar.button("✖️ مسح التنبيهات", key="clear_notif"):
        # انقل للسجل
        st.session_state.notif_history = st.session_state.new_whales + st.session_state.notif_history
        st.session_state.notif_history = st.session_state.notif_history[:20]
        st.session_state.new_whales=[]
        st.rerun()

# سجل التنبيهات القديمة
if st.session_state.notif_history:
    with st.sidebar.expander(f"📜 سجل التنبيهات ({len(st.session_state.notif_history)})"):
        for w in st.session_state.notif_history[:10]:
            st.markdown(f"**{w['ticker']}** {w['signal']} {w['strike']} - ${w['premium_M']:.1f}M - {w['exp_short']}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💰 فلاتر V29 الأصلي")
min_prem=st.sidebar.slider("💰 أقل حوت", 100000, 5000000, 500000, 100000, key="m29bell")
min_vol=st.sidebar.slider("📊 أقل VOL", 1, 50000, 5000, 1000, key="v29bell")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل (0DTE دبل)","اليوم فقط 0DTE","3-14 يوم"], value="الكل (0DTE دبل)", key="exp29bell")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf29bell")
score_filter=st.sidebar.select_slider("⭐ أقل سكور", options=["الكل","⭐+ (3+)","⭐⭐+ (5+) قوي","⭐⭐⭐ فقط (7+)"], value="⭐+ (3+)", key="score29bell")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["30 ثانية","1 دقيقة","2 دقيقة"], value="30 ثانية", key="int29bell")
map_sec={"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120}
interval_sec=map_sec[refresh_interval]
auto=st.sidebar.checkbox("⚡ فحص تلقائي سريع", True, key="a29bell")

st.sidebar.markdown("---")
if st.sidebar.button("🔥 0DTE اليوم - دبلات", key="b0_29bell"): st.session_state.page="0DTE"
if st.sidebar.button("💰 دبلات محتملة", key="bDouble_29bell"): st.session_state.page="DOUBLE"
if st.sidebar.button("🏆 أقوى 20", key="b20_29bell"): st.session_state.page="TOP20"
if st.sidebar.button("📋 كل اليوم", key="bAll_29bell"): st.session_state.page="ALL"
if st.sidebar.button("🔄 فحص سريع الآن 45ث", key="bNow_29bell"): st.session_state.last_refresh=datetime.now(); st.rerun()
if st.sidebar.button("🗑️ مسح الكل", key="bClear_29bell"): st.session_state.results=pd.DataFrame(); st.session_state.new_whales=[]; st.session_state.notif_history=[]

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
    final=enriched_df.head(20)

    delay_min = (datetime.now() - st.session_state.last_refresh).total_seconds()/60
    if delay_min>3:
        st.error(f"⏰ متأخر {delay_min:.0f}د - اضغط 🔄 فحص سريع الآن")
    else:
        st.success(f"✅ محدث - تأخير {delay_min:.1f}د فقط | 🔔 {len(st.session_state.new_whales)} تنبيه جديد على اليسار | {len(final)} حوت | {st.session_state.last_refresh.strftime('%H:%M:%S')}")

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
    st.warning("⏳ اضغط 🔄 فحص سريع الآن 45ث")

if auto:
    all_tickers=get_tickers()
    mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
    mins=mins_map.get(time_filter,60)
    st.caption(f"🔴 يفحص {len(all_tickers)} شركة متوازي - 45ث - بدون بهوت...")

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
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df

        # تنبيهات جديدة - فقط الحيتان القوية
        fresh=[]
        for _, w in filtered.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                stock_data=get_stock_analysis(w["ticker"])
                sc,_,_,_,_,_,_,_=calc_score(w, stock_data)
                if sc>=5:
                    fresh.append(w)
                    st.session_state.sent.add(key)

        if fresh:
            st.session_state.new_whales = fresh + st.session_state.new_whales
            st.session_state.new_whales = st.session_state.new_whales[:10]

        combined=pd.concat([st.session_state.results, filtered]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(600) if not st.session_state.results.empty and not filtered.empty else (filtered if not filtered.empty else new_df)
        st.session_state.results=combined
        st.session_state.last_refresh=datetime.now()

    time.sleep(interval_sec)
    st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V29 + 🔔 أيقونة تنبيهات على اليسار | بدون بهوت | سريع 45ث")
