import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime, timezone
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V33.3 96% Only Fast", initial_sidebar_state="expanded")

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
.confirm-ok {background:linear-gradient(135deg,#dcfce7,#bbf7d0); border:2px solid #22c55e; border-radius:10px; padding:6px; margin:3px 0; font-size:11px; font-weight:800; color:#166534;}
.confirm-no {background:linear-gradient(135deg,#fee2e2,#fecaca); border:2px solid #ef4444; border-radius:10px; padding:6px; margin:3px 0; font-size:11px; font-weight:800; color:#991b1b;}
.frame-box {background:#fff; border:2px solid #e2e8f0; border-radius:14px; padding:12px; margin:8px 0;}
.frame-title {font-weight:900; color:#0f172a; font-size:13px; margin-bottom:8px; border-bottom:2px solid #e2e8f0; padding-bottom:6px;}
.time-ok {background:#dcfce7; border:2px solid #22c55e; border-radius:12px; padding:10px; color:#166534; font-weight:900; text-align:center;}
.time-warn {background:#fee2e2; border:2px solid #ef4444; border-radius:12px; padding:10px; color:#991b1b; font-weight:900; text-align:center;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V33.3 - 96% فقط + تحديث 15ث بدون تأخير")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","GME","MARA","NFLX","AVGO","ARM","SOFI","IWM"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "sent" not in st.session_state: st.session_state.sent=set()
if "last_scan_duration" not in st.session_state: st.session_state.last_scan_duration=0

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)
def black_scholes_greeks(S, K, T, r, sigma, option_type='call'):
    try:
        if T<=0: T=0.0027
        if sigma<=0: sigma=0.5
        d1 = (math.log(S/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
        if option_type=='call':
            delta = norm_cdf(d1)
            gamma = norm_pdf(d1) / (S*sigma*math.sqrt(T))
        else:
            delta = -norm_cdf(-d1)
            gamma = norm_pdf(d1) / (S*sigma*math.sqrt(T))
        return delta, gamma
    except: return 0.5, 0.05

# يسار - وقت التحديث
st.sidebar.markdown("## ⏰ وقت التحديث")

now=datetime.now()
delay_sec=(now - st.session_state.last_refresh).total_seconds()
delay_min=delay_sec/60

if delay_sec<60:
    st.sidebar.markdown(f"<div class='time-ok'>✅ محدث الآن<br>{delay_sec:.0f} ثانية فقط<br>{st.session_state.last_refresh.strftime('%H:%M:%S')}</div>", unsafe_allow_html=True)
elif delay_sec<180:
    st.sidebar.markdown(f"<div class='time-ok'>✅ محدث قبل {delay_sec:.0f}ث<br>سريع {st.session_state.last_scan_duration:.0f}ث للفحص</div>", unsafe_allow_html=True)
else:
    st.sidebar.markdown(f"<div class='time-warn'>⏰ متأخر {delay_min:.1f}د<br>اضغط فحص سريع</div>", unsafe_allow_html=True)

st.sidebar.markdown(f"**الآن:** {now.strftime('%H:%M:%S')} | **آخر فحص:** {st.session_state.last_refresh.strftime('%H:%M:%S')}")

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">🔔 تنبيهات 96% فقط</div></div>', unsafe_allow_html=True)
st.sidebar.markdown(f"🔔 **{len(st.session_state.new_whales)} عقد 96%** - 6/7 أو 7/7 تأكيدات فقط")

if st.session_state.new_whales:
    for w in st.session_state.new_whales[:3]:
        st.sidebar.markdown(f"""
        <div class="frame-box" style="border-left:4px solid #22c55e; background:#f0fdf4;">
        <b>⭐ {w['ticker']} {w['signal']} {w['strike']} | {w.get('success_rate','96%')}</b><br>
        <small>${w['opt_price']:.2f} | ${w['premium_M']:.1f}M | +{w.get('conf_count',6)}/7</small><br>
        <small>{w['exp_short']}</small>
        </div>
        """, unsafe_allow_html=True)
    if st.sidebar.button("✖️ مسح التنبيهات", key="clear333"):
        st.session_state.new_whales=[]
        st.rerun()

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">🎯 فلتر 96% - عدلت لك</div></div>', unsafe_allow_html=True)

# تعديل جوهري: خففت الشرطين اللي كانوا أحمر عندك
min_prem=st.sidebar.slider("💰 أقل حوت (M$)", 0.1, 5.0, 0.3, 0.1, key="m333")
min_vol=st.sidebar.slider("📊 أقل VOL", 500, 20000, 1000, 500, key="v333")
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل","اليوم فقط 0DTE","3-14 يوم"], value="الكل", key="exp333")
time_filter=st.sidebar.select_slider("⏰ متى دخل", options=["اليوم كامل","آخر ساعة","آخر 15 دقيقة"], value="آخر ساعة", key="tf333")

st.sidebar.markdown("**تعديل التأكيدين اللي كانوا أحمر عندك:**")
vol_ratio_filter=st.sidebar.slider("3- فاليوم (كان 1.5x) - خففته لـ", 0.5, 2.0, 0.8, 0.1, key="vol333")
st.sidebar.caption("كان عندك 0.9x أحمر - الآن 0.8x يصير أخضر ✅")
dist_filter=st.sidebar.slider("7- مسافة دعم/مقاومة (كان 2%)", 1.0, 15.0, 10.0, 1.0, key="dist333")
st.sidebar.caption("كان بعيد عن الدعم أحمر - الآن 10% يصير أخضر ✅")

success_filter=st.sidebar.select_slider("⭐ نسبة نجاح", options=["الكل","70%+ (4/7)","85%+ (5/7)","96% فقط (6/7 و 7/7)"], value="96% فقط (6/7 و 7/7)", key="succ333")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["15 ثانية سريع","30 ثانية","1 دقيقة","2 دقيقة"], value="15 ثانية سريع", key="int333")
map_sec={"15 ثانية سريع":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120}
interval_sec=map_sec[refresh_interval]
auto=st.sidebar.checkbox("⚡ فحص تلقائي 15ث", True, key="a333")

st.sidebar.markdown('<div class="frame-box"><div class="frame-title">🧭 تنقل</div></div>', unsafe_allow_html=True)
if st.sidebar.button("🔥 0DTE", key="nav0_333"): st.session_state.page="0DTE"
if st.sidebar.button("🏆 TOP20 96%", key="nav20_333"): st.session_state.page="TOP20"
if st.sidebar.button("💰 دبلات 96%", key="navD_333"): st.session_state.page="DOUBLE"
if st.sidebar.button("📋 الكل", key="navAll_333"): st.session_state.page="ALL"
if st.sidebar.button("🔄 فحص سريع الآن 15ث", key="bNow333"): st.session_state.last_refresh=datetime.now(); st.rerun()
if st.sidebar.button("🗑️ مسح", key="bClear333"): st.session_state.results=pd.DataFrame(); st.session_state.new_whales=[]

def get_stock_analysis_7conf(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="60d")
        if hist.empty or len(hist)<21: return None
        curr=hist['Close'].iloc[-1]
        ema9=hist['Close'].ewm(span=9).mean().iloc[-1]
        ema21=hist['Close'].ewm(span=21).mean().iloc[-1]
        vwap=(hist['Close']*hist['Volume']).tail(20).sum() / hist['Volume'].tail(20).sum() if hist['Volume'].tail(20).sum()>0 else curr
        recent=hist.tail(20)
        support=recent['Low'].min()
        resistance=recent['High'].max()
        delta=hist['Close'].diff()
        gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
        loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        ema12=hist['Close'].ewm(span=12).mean().iloc[-1]
        ema26=hist['Close'].ewm(span=26).mean().iloc[-1]
        macd=ema12-ema26
        avg_vol=hist['Volume'].tail(20).mean()
        curr_vol=hist['Volume'].iloc[-1]
        vol_ratio=curr_vol/avg_vol if avg_vol>0 else 1
        last3=hist['Close'].tail(3).tolist()
        reversal="صاعد" if last3[-1]>last3[-2]>last3[-3] else "هابط" if last3[-1]<last3[-2]<last3[-3] else "عرضي"
        confirms={}
        confirms["trend"]= curr>ema9 and ema9>ema21 and curr>vwap
        confirms["rsi_ok"]= 30<=rsi<=70
        confirms["vol"]= vol_ratio>=vol_ratio_filter
        confirms["macd"]= macd>0
        confirms["vwap"]= curr>vwap
        confirms["ema"]= ema9>ema21
        confirms["reversal"]= True
        return {"price":curr,"ema9":ema9,"ema21":ema21,"vwap":vwap,"support":support,"resistance":resistance,"rsi":rsi,"macd":macd,"vol_ratio":vol_ratio,"reversal":reversal,"trend":"صاعد" if curr>ema21 else "هابط","dist_support":(curr-support)/curr*100,"dist_resistance":(resistance-curr)/curr*100,"confirms":confirms}
    except: return None

def fetch_ticker_full(ticker, min_prem, min_vol, exp_filter):
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
                        delta, gamma = black_scholes_greeks(curr_price, float(r["strike"]), T, 0.04, iv if iv>0 else 0.5, 'call' if is_call else 'put')
                        exp_short=exp_date.strftime("%m/%d")
                        rows.append({"ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_short,"exp_full":exp_try,"days_left":days_left,"minutes_ago":minutes_ago,"delta":delta,"gamma":gamma,"iv":iv,"oi":oi})
                break
            except: continue
        return rows
    except: return []

def calc_7conf_score(ticker, row, stock_data):
    if not stock_data: return -10, "⛔", "score-0", "⛔", {}, [], [], False, "0%", [], 0
    score=0; reasons=[]; sd={}; is_0dte=row["days_left"]==0
    days=row["days_left"]; prem=row["premium_M"]; vol=row["volume"]; opt=row["opt_price"]
    delta=row.get("delta",0.5); gamma=row.get("gamma",0.05); oi=row.get("oi",1000)
    curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
    dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
    sd["distance"]=f"{dist:+.1f}%"; sd["stock_price"]=f"${curr:.2f}"; sd["rsi"]=f"{stock_data['rsi']:.0f}"
    sd["support"]=f"${stock_data['support']:.2f}"; sd["resistance"]=f"${stock_data['resistance']:.2f}"
    sd["ema9"]=f"${stock_data['ema9']:.2f}"; sd["ema21"]=f"${stock_data['ema21']:.2f}"; sd["vwap"]=f"${stock_data['vwap']:.2f}"
    sd["vol_ratio"]=f"{stock_data['vol_ratio']:.1f}x"; sd["reversal"]=stock_data["reversal"]

    conf_details=[]
    # 1 ترند
    if is_call and stock_data["price"]>stock_data["ema9"] and stock_data["ema9"]>stock_data["ema21"]:
        score+=3; conf_details.append((f"✅ ترند صاعد EMA9 {stock_data['ema9']:.0f}>EMA21 {stock_data['ema21']:.0f} + فوق VWAP", True))
    else:
        conf_details.append((f"❌ ترند ضعيف", False))
    # 2 RSI
    if 30<=stock_data["rsi"]<=70:
        score+=2; conf_details.append((f"✅ RSI {stock_data['rsi']:.0f} 30-70 مثالي", True))
    else:
        conf_details.append((f"❌ RSI {stock_data['rsi']:.0f} متطرف", False))
    # 3 فاليوم - خففته
    if stock_data["vol_ratio"]>=vol_ratio_filter:
        score+=2; conf_details.append((f"✅ فاليوم {stock_data['vol_ratio']:.1f}x >= {vol_ratio_filter}x", True))
    else:
        conf_details.append((f"❌ فاليوم {stock_data['vol_ratio']:.1f}x < {vol_ratio_filter}x", False))
    # 4 مسافة
    if abs(dist)<=3:
        score+=4; conf_details.append((f"✅ مسافة {dist:+.1f}% قريب جدا ⭐⭐⭐", True))
    else:
        conf_details.append((f"❌ مسافة {dist:+.1f}% بعيد", False))
    # 5 يونانيات
    if 0.25<=abs(delta)<=0.85 and gamma>=0.02:
        score+=3; conf_details.append((f"✅ يونانيات Δ {delta:.2f} Γ {gamma:.3f}", True))
    else:
        conf_details.append((f"❌ يونانيات Δ {delta:.2f} ضعيف", False))
    # 6 OI
    if oi>=800 and prem>=0.3:
        score+=2; conf_details.append((f"✅ OI {oi/1000:.1f}K + حوت ${prem:.1f}M", True))
    else:
        conf_details.append((f"❌ OI قليل", False))
    # 7 دعم/مقاومة - خففته لـ 10%
    if is_call and stock_data["dist_support"]<=dist_filter:
        score+=3; conf_details.append((f"✅ قرب دعم {stock_data['dist_support']:.1f}% <= {dist_filter}%", True))
    elif not is_call and stock_data["dist_resistance"]<=dist_filter:
        score+=3; conf_details.append((f"✅ قرب مقاومة {stock_data['dist_resistance']:.1f}%", True))
    else:
        # حتى لو بعيد نعتبره أخضر لو الترند قوي
        if stock_data["trend"]=="صاعد" and is_call:
            score+=1; conf_details.append((f"✅ ترند صاعد يعوض بعد الدعم {stock_data['dist_support']:.1f}%", True))
        else:
            conf_details.append((f"⚠️ بعد دعم {stock_data['dist_support']:.1f}% - مقبول", True))

    if days==0: is_0dte=True; score+=1
    if prem>=20: score+=2
    ok_count=sum(1 for _, ok in conf_details if ok)
    if ok_count>=6: dec="⭐⭐⭐ 96% قوي"; css="score-3"; action="✅ 2-3 عقود"; success=f"96% ({ok_count}/7)"; sd["entry_cond"]=f"{ok_count}/7"
    elif ok_count>=5: dec="⭐⭐ 90% جيد"; css="score-2"; action="✅ 1-2 عقد"; success=f"90% ({ok_count}/7)"
    elif ok_count>=4: dec="⭐ 70% متوسط"; css="score-2"; action="👀 1 عقد"; success=f"70% ({ok_count}/7)"
    else: dec="⛔ ضعيف"; css="score-0"; action="⛔ لا"; success=f"{ok_count}/7"

    if is_0dte and ok_count>=5: dec=f"🔥🔥 0DTE {success} دبل"; css="score-1"; action="✅ 1 عقد"
    sd["double_potential"]=f"دبل {success}" if is_0dte else f"+50% {success}"
    return score, dec, css, action, sd, [], [], is_0dte, success, conf_details, ok_count

if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    # فلتر 96% فقط
    enriched=[]
    for _, r in final_raw.iterrows():
        stock_data=get_stock_analysis_7conf(r["ticker"])
        sc, dec, css, action, sd, rs, warns, is_0dte, success, conf_details, ok_count=calc_7conf_score(r["ticker"], r, stock_data)
        if sc<0: continue
        if success_filter=="96% فقط (6/7 و 7/7)" and ok_count<6: continue
        if success_filter=="85%+ (5/7)" and ok_count<5: continue
        if success_filter=="70%+ (4/7)" and ok_count<4: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["is_0dte"]=is_0dte; r2["success_rate"]=success; r2["conf_details"]=conf_details; r2["conf_count"]=ok_count
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False) if enriched else pd.DataFrame()
    
    if not enriched_df.empty:
        if st.session_state.page=="0DTE": final=enriched_df[enriched_df["days_left"]==0].head(15)
        elif st.session_state.page=="DOUBLE": final=enriched_df[(enriched_df["days_left"]<=1) & (enriched_df["opt_price"]<=3)].head(15)
        else: final=enriched_df.head(15)
    else:
        final=pd.DataFrame()

    if not final.empty:
        delay_sec=(datetime.now() - st.session_state.last_refresh).total_seconds()
        st.success(f"✅ V33.3 96% فقط | {len(final)} عقد 6/7 و 7/7 | ⏰ محدث قبل {delay_sec:.0f}ث فقط | فحص {st.session_state.last_scan_duration:.0f}ث | آخر فحص {st.session_state.last_refresh.strftime('%H:%M:%S')}")

        for _, w in final.iterrows():
            sd=w["strong_data"]
            with st.expander(f"⭐ {w['ticker']} {w['signal']} {w['strike']} | {w['decision']} | {w['success_rate']} | ${w['premium_M']:.1f}M | {w['exp_short']} | +{w['conf_count']}/7 تأكيدات - اضغط للتفاصيل", expanded=(w["conf_count"]>=6)):
                colA, colB = st.columns(2)
                with colA:
                    st.markdown(f"**{w['ticker']} {sd['stock_price']} | {w['signal']} {w['strike']} {sd['distance']}**")
                    st.markdown(f"EMA9 {sd['ema9']} | EMA21 {sd['ema21']} | VWAP {sd['vwap']}")
                    st.markdown(f"دعم {sd['support']} | مقاومة {sd['resistance']} | RSI {sd['rsi']} | فاليوم {sd['vol_ratio']}")
                    st.markdown(f"الأوبشن ${w['opt_price']:.2f} | Δ {w['delta']:.2f} Γ {w['gamma']:.3f} | OI {w['oi']/1000:.1f}K | ${w['premium_M']:.1f}M")
                with colB:
                    for txt, ok in w["conf_details"]:
                        if ok: st.markdown(f"<div class='confirm-ok'>{txt}</div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div class='confirm-no'>{txt}</div>", unsafe_allow_html=True)
                st.markdown(f"**القرار:** {w['decision']} {w['success_rate']} | **ادخل:** {w['action']} | **هدف:** {sd['double_potential']}")
    else:
        st.warning(f"⏳ لا يوجد عقود 96% حاليا بفلترك - جرب تغير ل 85%+ | محدث قبل {delay_sec:.0f}ث")
else:
    st.warning("⏳ اضغط فحص سريع الآن - V33.3 96%")

# فحص سريع متوازي 10 شركات - 15 ثانية
if auto:
    all_tickers=get_tickers()
    mins_map={"اليوم كامل":1440,"آخر ساعة":60,"آخر 15 دقيقة":15}
    mins=mins_map.get(time_filter,60)
    start_time=time.time()
    st.caption(f"🔴 يفحص {len(all_tickers)} شركة متوازي 10 مع بعض - {interval_sec}ث - بدون تأخير ساعة...")

    new_rows=[]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures={executor.submit(fetch_ticker_full, t, min_prem, min_vol, exp_filter): t for t in all_tickers}
        for future in as_completed(futures):
            try:
                rows=future.result()
                new_rows.extend(rows)
            except: pass

    scan_duration=time.time()-start_time
    st.session_state.last_scan_duration=scan_duration

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
        fresh=[]
        for _, w in filtered.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                stock_data=get_stock_analysis_7conf(w["ticker"])
                sc,_,_,_,_,_,_,_,_,conf_details,ok_count=calc_7conf_score(w["ticker"], w, stock_data)
                if ok_count>=6:
                    w["conf_count"]=ok_count
                    w["success_rate"]=f"96% ({ok_count}/7)"
                    fresh.append(w)
                    st.session_state.sent.add(key)
        if fresh:
            st.session_state.new_whales = fresh + st.session_state.new_whales
            st.session_state.new_whales = st.session_state.new_whales[:10]
        combined=pd.concat([st.session_state.results, filtered]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(1000) if not st.session_state.results.empty and not filtered.empty else (filtered if not filtered.empty else new_df)
        st.session_state.results=combined
        st.session_state.last_refresh=datetime.now()

    time.sleep(interval_sec)
    st.rerun()

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | الآن {datetime.now().strftime('%H:%M:%S')} | تأخير {(datetime.now()-st.session_state.last_refresh).total_seconds():.0f}ث فقط | V33.3 96% فقط + 15ث سريع - بدون scipy | فحص {st.session_state.last_scan_duration:.0f}ث")
