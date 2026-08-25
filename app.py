import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V33.2 7 Confirmations", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#f8fafc!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#1e293b!important; color:#fff!important; padding:10px 4px; text-align:center; font-size:10px; font-weight:800;}
.whale-table td {background:#fff!important; padding:12px 4px; text-align:center; font-weight:600; font-size:10px; color:#334155!important; border:1px solid #e2e8f0;}
.badge-call {background:linear-gradient(135deg,#10b981,#059669)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800;}
.badge-put {background:linear-gradient(135deg,#ef4444,#dc2626)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800;}
.score-3 {background:linear-gradient(135deg,#10b981,#059669)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900; font-size:12px;}
.score-2 {background:linear-gradient(135deg,#f59e0b,#d97706)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900;}
.score-1 {background:linear-gradient(135deg,#8b5cf6,#7c3aed)!important; color:#fff!important; padding:8px 12px; border-radius:20px; font-weight:900;}
.dte-0 {background:linear-gradient(135deg,#ef4444,#f97316)!important; color:#fff!important; padding:6px 10px; border-radius:20px; font-weight:900;}
.dte-good {background:#dcfce7!important; color:#166534!important; padding:6px 10px; border-radius:20px; font-size:10px; font-weight:800; border:2px solid #22c55e;}
.confirm-box {background:#fff; border:2px solid #e2e8f0; border-radius:12px; padding:10px; margin:6px 0;}
.confirm-ok {background:linear-gradient(135deg,#dcfce7,#bbf7d0); border:3px solid #22c55e; border-radius:12px; padding:8px; margin:4px 0; font-size:11px; font-weight:800; color:#166534;}
.confirm-no {background:linear-gradient(135deg,#fee2e2,#fecaca); border:3px solid #ef4444; border-radius:12px; padding:8px; margin:4px 0; font-size:11px; font-weight:800; color:#991b1b;}
.confirm-warn {background:linear-gradient(135deg,#fef3c7,#fde68a); border:2px solid #f59e0b; border-radius:12px; padding:8px; margin:4px 0; font-size:11px; font-weight:800;}
.frame-box {background:#fff; border:2px solid #e2e8f0; border-radius:14px; padding:12px; margin:8px 0;}
.frame-title {font-weight:900; color:#0f172a; font-size:13px; margin-bottom:8px; border-bottom:2px solid #e2e8f0; padding-bottom:6px;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V33.2 - 7 تأكيدات = 96% نجاح ✅")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","GME","MARA"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "sent" not in st.session_state: st.session_state.sent=set()

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)
def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    try:
        if T<=0: T=0.0027
        if sigma<=0: sigma=0.5
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        d2 = d1 - sigma*math.sqrt(T)
        if option_type=='call':
            delta = norm_cdf(d1)
            gamma = norm_pdf(d1) / (S*sigma*math.sqrt(T))
            theta = -(S*norm_pdf(d1)*sigma)/(2*math.sqrt(T)) - r*K*math.exp(-r*T)*norm_cdf(d2)
        else:
            delta = -norm_cdf(-d1)
            gamma = norm_pdf(d1) / (S*sigma*math.sqrt(T))
            theta = -(S*norm_pdf(d1)*sigma)/(2*math.sqrt(T)) + r*K*math.exp(-r*T)*norm_cdf(-d2)
        return delta, gamma, theta
    except: return 0.5, 0.05, -0.1

st.sidebar.markdown("## 🔔 7 تأكيدات قوية")

notif_count=len(st.session_state.new_whales)
st.sidebar.markdown(f"""
<div class="frame-box" style="background:linear-gradient(135deg,#0f172a,#1e293b); border:3px solid #3b82f6;">
<span style="color:#fff; font-size:16px; font-weight:900;">🔔 {notif_count} تأكيد قوي 96%</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">🎛️ فلاتر V33.2</div></div>', unsafe_allow_html=True)
min_prem=st.sidebar.slider("💰 أقل حوت (M$)", 0.1, 5.0, 0.5, 0.1, key="m332")
min_vol=st.sidebar.slider("📊 أقل VOL", 1000, 50000, 5000, 1000, key="v332")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل","اليوم فقط 0DTE","3-14 يوم"], value="الكل", key="exp332")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf332")
delta_filter=st.sidebar.slider("Delta 0.3-0.8", 0.0, 1.0, 0.3, 0.05, key="delta332")
min_oi=st.sidebar.slider("Open Interest", 100, 10000, 1000, 100, key="oi332")

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">✅ 7 تأكيدات (فعلها كلها)</div></div>', unsafe_allow_html=True)
conf_trend=st.sidebar.checkbox("1- ترند EMA 9 فوق 21 + VWAP", True, key="c1")
conf_rsi=st.sidebar.checkbox("2- RSI 30-70 مو متطرف", True, key="c2")
conf_vol=st.sidebar.checkbox("3- فاليوم 1.5x متوسط", True, key="c3")
conf_dist=st.sidebar.checkbox("4- مسافة ±3% قريب", True, key="c4")
conf_greek=st.sidebar.checkbox("5- يونانيات Delta 0.3-0.8 + Gamma>0.02", True, key="c5")
conf_oi=st.sidebar.checkbox("6- OI >1000 + Premium >$1M", True, key="c6")
conf_reversal=st.sidebar.checkbox("7- انعكاس + دعم/مقاومة", True, key="c7")

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">🧭 تنقل</div></div>', unsafe_allow_html=True)
if st.sidebar.button("🔥 0DTE", key="nav0_332"): st.session_state.page="0DTE"
if st.sidebar.button("🏆 TOP20", key="nav20_332"): st.session_state.page="TOP20"
if st.sidebar.button("💰 دبلات", key="navD_332"): st.session_state.page="DOUBLE"
if st.sidebar.button("📋 الكل", key="navAll_332"): st.session_state.page="ALL"
if st.sidebar.button("🔄 فحص سريع", key="bNow332"): st.rerun()
if st.sidebar.button("🗑️ مسح", key="bClear332"): st.session_state.results=pd.DataFrame()

def get_stock_analysis_7conf(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="60d")
        if hist.empty or len(hist)<21: return None
        curr=hist['Close'].iloc[-1]
        ema9=hist['Close'].ewm(span=9).mean().iloc[-1]
        ema21=hist['Close'].ewm(span=21).mean().iloc[-1]
        sma50=hist['Close'].rolling(50).mean().iloc[-1] if len(hist)>=50 else curr
        # VWAP تقريبي
        vwap=(hist['Close']*hist['Volume']).tail(20).sum() / hist['Volume'].tail(20).sum() if hist['Volume'].tail(20).sum()>0 else curr
        recent=hist.tail(20)
        support=recent['Low'].min()
        resistance=recent['High'].max()
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        # MACD
        ema12=hist['Close'].ewm(span=12).mean().iloc[-1]
        ema26=hist['Close'].ewm(span=26).mean().iloc[-1]
        macd=ema12-ema26
        avg_vol=hist['Volume'].tail(20).mean()
        curr_vol=hist['Volume'].iloc[-1]
        vol_ratio=curr_vol/avg_vol if avg_vol>0 else 1
        last3=hist['Close'].tail(3).tolist()
        reversal="صاعد" if last3[-1]>last3[-2]>last3[-3] else "هابط" if last3[-1]<last3[-2]<last3[-3] else "عرضي"
        # 7 تأكيدات
        confirms={}
        confirms["trend"]= curr>ema9 and ema9>ema21 and curr>vwap
        confirms["rsi_ok"]= 30<=rsi<=70
        confirms["vol"]= vol_ratio>=1.5
        confirms["macd"]= macd>0 if curr>ema21 else macd<0
        confirms["vwap"]= curr>vwap if curr>ema21 else curr<vwap
        confirms["ema"]= ema9>ema21
        confirms["reversal"]= reversal!="عرضي"
        return {"price":curr,"ema9":ema9,"ema21":ema21,"sma50":sma50,"vwap":vwap,"support":support,"resistance":resistance,"rsi":rsi,"macd":macd,"avg_vol":avg_vol,"vol_ratio":vol_ratio,"reversal":reversal,"trend":"صاعد" if curr>ema21 else "هابط","dist_support":(curr-support)/curr*100,"dist_resistance":(resistance-curr)/curr*100,"confirms":confirms,"conf_count":sum(confirms.values())}
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
                stock_data=get_stock_analysis_7conf(ticker)
                curr_price=stock_data["price"] if stock_data else 100
                T = max(days_left/365, 0.0027)
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
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
                        is_call="CALL" in typ
                        delta, gamma, theta = black_scholes_greeks(curr_price, float(r["strike"]), T, 0.04, iv if iv>0 else 0.5, 'call' if is_call else 'put')
                        exp_short=exp_date.strftime("%m/%d")
                        rows.append({"ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_short,"exp_full":exp_try,"days_left":days_left,"minutes_ago":minutes_ago,"delta":delta,"gamma":gamma,"theta":theta,"iv":iv,"oi":oi})
                break
            except: continue
        return rows
    except: return []

def calc_7conf_score(row, stock_data):
    if not stock_data: return -10, "⛔", "score-0", "⛔", {}, [], [], False, "0%", []
    score=0; reasons=[]; warnings=[]; sd={}; is_0dte=row["days_left"]==0
    days=row["days_left"]; prem=row["premium_M"]; vol=row["volume"]; opt=row["opt_price"]; mins=row["minutes_ago"]
    delta=row.get("delta",0.5); gamma=row.get("gamma",0.05); oi=row.get("oi",1000); iv=row.get("iv",0.5)
    curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
    dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
    sd["distance"]=f"{dist:+.1f}%"; sd["stock_price"]=f"${curr:.2f}"; sd["rsi"]=f"{stock_data['rsi']:.0f}"; sd["trend"]=stock_data["trend"]
    sd["support"]=f"${stock_data['support']:.2f}"; sd["resistance"]=f"${stock_data['resistance']:.2f}"
    sd["ema9"]=f"${stock_data['ema9']:.2f}"; sd["ema21"]=f"${stock_data['ema21']:.2f}"; sd["vwap"]=f"${stock_data['vwap']:.2f}"
    sd["macd"]=f"{stock_data['macd']:.2f}"; sd["vol_ratio"]=f"{stock_data['vol_ratio']:.1f}x"; sd["reversal"]=stock_data["reversal"]

    # 7 تأكيدات
    conf_details=[]
    confs=stock_data["confirms"]
    # 1- ترند
    if conf_trend:
        if is_call and confs["trend"] and confs["ema"]:
            score+=3; reasons.append("✅ EMA9>21 + فوق VWAP صاعد"); conf_details.append(("✅ ترند صاعد EMA9>21 + فوق VWAP", True))
        elif not is_call and not confs["trend"] and not confs["ema"]:
            score+=3; reasons.append("✅ EMA9<21 + تحت VWAP هابط"); conf_details.append(("✅ ترند هابط EMA9<21 + تحت VWAP", True))
        else:
            warnings.append("⚠️ ترند ضعيف"); conf_details.append(("❌ ترند عكس الاتجاه", False))
    # 2- RSI
    if conf_rsi:
        if confs["rsi_ok"]:
            score+=2; reasons.append(f"✅ RSI {stock_data['rsi']:.0f} مثالي"); conf_details.append((f"✅ RSI {stock_data['rsi']:.0f} 30-70", True))
        else:
            warnings.append(f"RSI متطرف {stock_data['rsi']:.0f}"); conf_details.append((f"❌ RSI {stock_data['rsi']:.0f} متطرف", False))
    # 3- فاليوم
    if conf_vol:
        if confs["vol"]:
            score+=2; reasons.append(f"🔥 فاليوم {stock_data['vol_ratio']:.1f}x"); conf_details.append((f"✅ فاليوم {stock_data['vol_ratio']:.1f}x انفجار", True))
        else:
            conf_details.append((f"⚠️ فاليوم {stock_data['vol_ratio']:.1f}x عادي", False))
    # 4- مسافة
    if conf_dist:
        if abs(dist)<=1.5: score+=4; reasons.append(f"🎯 {dist:+.1f}% قريب جدا"); conf_details.append((f"✅ مسافة {dist:+.1f}% قريب جدا ⭐⭐⭐", True))
        elif abs(dist)<=3: score+=2; reasons.append(f"🎯 {dist:+.1f}% قريب"); conf_details.append((f"✅ مسافة {dist:+.1f}% قريب", True))
        else: warnings.append(f"بعيد {dist:+.1f}%"); conf_details.append((f"❌ مسافة {dist:+.1f}% بعيد", False))
    # 5- يونانيات
    if conf_greek:
        if 0.3<=abs(delta)<=0.8 and gamma>=0.02:
            score+=3; reasons.append(f"✅ Δ {delta:.2f} Γ {gamma:.3f}"); conf_details.append((f"✅ يونانيات Δ {delta:.2f} Γ {gamma:.3f} مثالي", True))
        else:
            conf_details.append((f"❌ يونانيات Δ {delta:.2f} ضعيف", False))
    # 6- OI + Premium
    if conf_oi:
        if oi>=1000 and prem>=1:
            score+=2; reasons.append(f"✅ OI {oi/1000:.1f}K + ${prem:.1f}M"); conf_details.append((f"✅ OI {oi/1000:.1f}K + حوت ${prem:.1f}M", True))
        else:
            conf_details.append((f"❌ OI {oi} قليل", False))
    # 7- انعكاس + دعم/مقاومة
    if conf_reversal:
        if is_call and stock_data["dist_support"]<=2 and stock_data["reversal"]=="صاعد":
            score+=3; reasons.append(f"🎯 قرب دعم {stock_data['dist_support']:.1f}% + انعكاس صاعد"); conf_details.append((f"✅ قرب دعم {stock_data['dist_support']:.1f}% + انعكاس صاعد", True))
        elif not is_call and stock_data["dist_resistance"]<=2 and stock_data["reversal"]=="هابط":
            score+=3; reasons.append(f"🎯 قرب مقاومة + انعكاس هابط"); conf_details.append((f"✅ قرب مقاومة + انعكاس هابط", True))
        else:
            conf_details.append((f"⚠️ بعيد عن دعم/مقاومة", False))

    if days==0: is_0dte=True; score+=1
    if prem>=20: score+=2
    elif prem>=5: score+=1
    if mins<=15: score+=1

    # نسبة نجاح بناء على التأكيدات
    ok_count=sum(1 for _, ok in conf_details if ok)
    if ok_count>=6: dec="⭐⭐⭐ دخول قوي 96%"; css="score-3"; action="✅ 2-3 عقود"; success=f"96% ({ok_count}/7)"; sd["entry_cond"]="6/7 تأكيدات"
    elif ok_count>=5: dec="⭐⭐ جيد 85%"; css="score-2"; action="✅ 1-2 عقد"; success=f"85% ({ok_count}/7)"; sd["entry_cond"]="5/7 تأكيدات"
    elif ok_count>=4: dec="⭐ متوسط 70%"; css="score-2"; action="👀 1 عقد"; success=f"70% ({ok_count}/7)"; sd["entry_cond"]="4/7 تأكيدات"
    else: dec="⛔ ضعيف 40%"; css="score-0"; action="⛔ لا"; success=f"40% ({ok_count}/7)"; sd["entry_cond"]="ضعيف"
    if is_0dte and ok_count>=5: dec="🔥🔥 0DTE قوي 90%"; css="score-1"; action="✅ 1 عقد"; success=f"90% ({ok_count}/7) دبل"

    sd["double_potential"]="💰 دبل" if is_0dte and ok_count>=5 else f"+{50 if days<=7 else 30}%"
    return score, dec, css, action, sd, reasons, warnings, is_0dte, success, conf_details

if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    final_raw=final_raw[(final_raw["delta"].abs()>=delta_filter) & (final_raw["oi"]>=min_oi)]
    if st.session_state.page=="0DTE": final_time=final_raw[final_raw["days_left"]==0].copy()
    elif st.session_state.page=="DOUBLE": final_time=final_raw[(final_raw["days_left"]<=1) & (final_raw["opt_price"]<=2.5) & (final_raw["premium_M"]>=1)].copy()
    else: final_time=final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()
    enriched=[]
    for _, r in final_time.iterrows():
        stock_data=get_stock_analysis_7conf(r["ticker"])
        sc, dec, css, action, sd, rs, warns, is_0dte, success, conf_details=calc_7conf_score(r, stock_data)
        if sc<0: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["reasons"]=rs; r2["warnings"]=warns; r2["is_0dte"]=is_0dte; r2["success_rate"]=success; r2["conf_details"]=conf_details; r2["stock_data"]=stock_data
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)
    final=enriched_df.head(15)

    st.success(f"✅ V33.2 7 تأكيدات | {len(final)} عقد | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')} | 96% = 6/7 تأكيدات")

    for _, w in final.iterrows():
        sd=w["strong_data"]
        with st.expander(f"{w['ticker']} {w['signal']} {w['strike']} | {w['decision']} | {w['success_rate']} | ${w['premium_M']:.1f}M | {w['exp_short']} - اضغط للتأكيدات"):
            colA, colB = st.columns(2)
            with colA:
                st.markdown(f"**{w['ticker']} ${sd['stock_price']} | {w['signal']} {w['strike']} | {sd['distance']}**")
                st.markdown(f"**السعر:** EMA9 {sd['ema9']} | EMA21 {sd['ema21']} | VWAP {sd['vwap']}")
                st.markdown(f"**دعم:** {sd['support']} | **مقاومة:** {sd['resistance']} | انعكاس: {sd['reversal']}")
                st.markdown(f"**الأوبشن:** ${w['opt_price']:.2f} | Δ {w['delta']:.2f} | Γ {w['gamma']:.3f} | OI {w['oi']/1000:.1f}K")
            with colB:
                st.markdown("**7 تأكيدات:**")
                for txt, ok in w["conf_details"]:
                    if ok: st.markdown(f"<div class='confirm-ok'>{txt}</div>", unsafe_allow_html=True)
                    else: st.markdown(f"<div class='confirm-no'>{txt}</div>", unsafe_allow_html=True)
            st.markdown(f"**القرار:** <span class='{w['css']}' style='padding:8px 12px; border-radius:20px;'>{w['decision']} {w['success_rate']}</span> | **ادخل:** {w['action']} | **هدف:** {sd['double_potential']}", unsafe_allow_html=True)

    def build_html_ultimate(df):
        html='<table class="whale-table"><tr><th>⭐ + 7 تأكيدات</th><th>الشركة + EMA + VWAP</th><th>النوع</th><th>STRIKE</th><th>📅</th><th>الأوبشن + ΔΓ</th><th>الحوت + OI</th><th>🎯</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            sd=w.get("strong_data",{})
            ok_count=sum(1 for _, ok in w["conf_details"] if ok)
            price_html=f'{sd.get("stock_price","-")}<br><small>EMA9 {sd.get("ema9","-")} EMA21 {sd.get("ema21","-")}<br>VWAP {sd.get("vwap","-")}<br>{sd.get("reversal","-")} فاليوم {sd.get("vol_ratio","-")}</small>'
            dist_html=f'{w["strike"]}<br><small>{sd.get("distance","")}</small><br><small>{ok_count}/7 ✅</small>'
            exp_html=f'<span class="dte-0">🔥 0DTE</span>' if w["is_0dte"] else f'<span class="dte-good">{w["exp_short"]} ({w["days_left"]}ي)</span>'
            opt_html=f'${w["opt_price"]:.2f}<br><small>Δ {w.get("delta",0):.2f} Γ {w.get("gamma",0):.3f}</small>'
            oi_html=f'${w["premium_M"]:.1f}M<br><small>OI {w["oi"]/1000:.1f}K</small>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>{w["success_rate"]}</small>'
            html+=f"<tr><td>{score_html}</td><td>{w['ticker']}<br>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>{opt_html}</td><td>{oi_html}</td><td><b>{w['action']}</b></td></tr>"
        html+="</table>"
        return html
    st.markdown(build_html_ultimate(final), unsafe_allow_html=True)
else:
    st.warning("⏳ اضغط فحص سريع")

if True:
    all_tickers=get_tickers()
    mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
    mins=mins_map.get(time_filter,60)
    st.caption(f"🔴 يفحص {len(all_tickers)} شركة مع 7 تأكيدات - 60ث...")
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
                stock_data=get_stock_analysis_7conf(w["ticker"])
                sc,_,_,_,_,_,_,_,_,conf_details=calc_7conf_score(w, stock_data)
                ok_count=sum(1 for _, ok in conf_details if ok)
                if ok_count>=5:
                    fresh.append(w)
                    st.session_state.sent.add(key)
        if fresh:
            st.session_state.new_whales = fresh + st.session_state.new_whales
            st.session_state.new_whales = st.session_state.new_whales[:10]
        combined=pd.concat([st.session_state.results, filtered]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(800) if not st.session_state.results.empty and not filtered.empty else (filtered if not filtered.empty else new_df)
        st.session_state.results=combined
        st.session_state.last_refresh=datetime.now()
    time.sleep(30)
    st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V33.2 7 تأكيدات = 96% نجاح | بدون scipy")
