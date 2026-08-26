import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V34 Eye Comfort + 10 Conditions", initial_sidebar_state="expanded")

# ===== ألوان طبية تريح العين - بدون أبيض ساطع =====
st.markdown("""
<style>
/* خلفية كريمية تريح العين مو أبيض */
.stApp {background:#fdfbf7!important;}
[data-testid="stSidebar"] {background:#fffefc!important; border-right:3px solid #e7e5e4!important; min-width:520px!important;}

/* جدول - خط كبير + تباعد + ألوان مريحة */
.whale-table {width:100%; border-collapse:separate; border-spacing:0 10px; font-family:'IBM Plex Sans Arabic','Segoe UI',sans-serif; font-size:13px;}
.whale-table th {
  background:#1c1917!important; color:#fafaf9!important; 
  padding:16px 10px; text-align:center; font-weight:800; font-size:12px;
  letter-spacing:0.5px; border:none;
}
.whale-table td {
  background:#ffffff!important; 
  padding:16px 10px; text-align:center; font-weight:600; 
  color:#292524!important; 
  border-top:1.5px solid #f5f5f4; border-bottom:1.5px solid #f5f5f4;
  box-shadow:0 2px 8px rgba(0,0,0,0.04);
}
.whale-table tr td:first-child {border-left:1.5px solid #f5f5f4; border-radius:12px 0 0 12px;}
.whale-table tr td:last-child {border-right:1.5px solid #f5f5f4; border-radius:0 12px 12px 0;}

/* Badges مريحة للعين - مو نيون */
.badge-call {background:#e7f5ec!important; color:#14532d!important; border:1.5px solid #86efac; padding:7px 14px; border-radius:20px; font-weight:800; font-size:11px;}
.badge-put {background:#fef2f2!important; color:#7f1d1d!important; border:1.5px solid #fecaca; padding:7px 14px; border-radius:20px; font-weight:800;}
.score-10 {background:#14532d!important; color:#dcfce7!important; padding:9px 16px; border-radius:20px; font-weight:900; font-size:12px; letter-spacing:0.3px;}
.score-9 {background:#166534!important; color:#bbf7d0!important; padding:9px 16px; border-radius:20px; font-weight:800;}
.score-8 {background:#15803d!important; color:#dcfce7!important; padding:8px 14px; border-radius:20px; font-weight:700;}
.score-low {background:#f5f5f4!important; color:#57534e!important; padding:8px 14px; border-radius:20px;}

.time-card {background:linear-gradient(135deg,#1c1917 0%,#292524 100%); color:#a3e635; border:1px solid #44403c; border-radius:18px; padding:18px; font-family:'JetBrains Mono',monospace; text-align:center; font-size:15px; line-height:1.8; box-shadow:0 4px 12px rgba(0,0,0,0.15);}
.frame-box {background:#fffefc; border:1.5px solid #e7e5e4; border-radius:14px; padding:14px; margin:12px 0;}
.ticker-main {font-size:14px; font-weight:900; color:#1c1917;}
.ticker-sub {font-size:11px; color:#78716c; font-weight:500; margin-top:4px; display:block;}
.condition-dot {width:8px; height:8px; border-radius:50%; display:inline-block; margin:0 2px;}
.dot-ok {background:#22c55e;}
.dot-bad {background:#e7e5e4;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V34 - راحة العين + 10 شروط دخول قوية")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","SOFI","GME","MARA","NFLX","AVGO"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "last_refresh_str" not in st.session_state: st.session_state.last_refresh_str=datetime.now().strftime("%H:%M:%S")
if "last_refresh_ts" not in st.session_state: st.session_state.last_refresh_ts=datetime.now()

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)
def greeks(S, K, T, sigma, typ):
    try:
        if T<=0: T=0.0027
        if sigma<=0: sigma=0.5
        d1 = (math.log(S/K) + 0.5*sigma**2*T) / (sigma*math.sqrt(T))
        if typ=='call': delta = norm_cdf(d1); gamma = norm_pdf(d1)/(S*sigma*math.sqrt(T))
        else: delta = -norm_cdf(-d1); gamma = norm_pdf(d1)/(S*sigma*math.sqrt(T))
        return delta, gamma
    except: return 0.5, 0.05

# وقت
now = datetime.now()
try:
    delay_sec = (now - st.session_state.last_refresh_ts).total_seconds()
    if delay_sec<0 or delay_sec>86400: delay_sec=0
except:
    delay_sec=0
    st.session_state.last_refresh_ts=now

now_saudi_str = now.strftime("%H:%M:%S")
now_ny_hour = (now.hour - 7) % 24
now_ny_str = f"{now_ny_hour:02d}:{now.minute:02d}:{now.second:02d}"

st.sidebar.markdown("### ⏰ وقت السوق - مريح للعين")
st.sidebar.markdown(f"""<div class="time-card">
🕐 السعودية: {now_saudi_str}<br>
🗽 نيويورك: {now_ny_str}<br>
⏱️ آخر فحص: {st.session_state.last_refresh_str}<br>
⏳ تأخير: {delay_sec:.0f}ث - ممتاز
</div>""", unsafe_allow_html=True)

if delay_sec<90: st.sidebar.success(f"✅ تأخير {delay_sec:.0f}ث")
else: st.sidebar.warning(f"⚠️ تأخير {delay_sec:.0f}ث")

col1, col2 = st.sidebar.columns(2)
with col1: do_scan = st.button("🔄 فحص الآن", type="primary", use_container_width=True)
with col2:
    if st.button("🧹 تصفير", use_container_width=True):
        st.session_state.last_refresh_str=datetime.now().strftime("%H:%M:%S")
        st.session_state.last_refresh_ts=datetime.now()
        st.rerun()

st.sidebar.markdown('<div class="frame-box"><b>👁️ راحة العين</b><br><small>خلفية كريمية #fdfbf7 + خط IBM كبير + بدون نيون</small></div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="frame-box"><b>🎛️ فلاتر 10 شروط</b></div>', unsafe_allow_html=True)
min_prem=st.sidebar.slider("💰 أقل حوت M$", 0.05, 5.0, 0.1, 0.05)
min_vol=st.sidebar.slider("📊 أقل VOL", 100, 10000, 300, 100)
exp_filter=st.sidebar.select_slider("📅 الانتهاء", options=["الكل","اليوم فقط 0DTE","1-7 أيام","1-14 يوم"], value="الكل")
success_filter=st.sidebar.select_slider("⭐ نسبة نجاح", options=["الكل","80%+ (8/10)","90%+ (9/10)","100% فقط 10/10"], value="80%+ (8/10)")

if st.sidebar.button("🗑️ مسح الجدول"): st.session_state.results=pd.DataFrame()

def get_analysis(ticker):
    try:
        s=yf.Ticker(ticker)
        hist=s.history(period="90d")
        if hist.empty or len(hist)<30: return None
        curr=hist['Close'].iloc[-1]
        ema9=hist['Close'].ewm(span=9).mean().iloc[-1]
        ema21=hist['Close'].ewm(span=21).mean().iloc[-1]
        ema50=hist['Close'].ewm(span=50).mean().iloc[-1]
        vwap=(hist['Close']*hist['Volume']).tail(20).sum()/hist['Volume'].tail(20).sum() if hist['Volume'].tail(20).sum()>0 else curr
        recent=hist.tail(20)
        support=recent['Low'].min(); resistance=recent['High'].max()
        d=hist['Close'].diff()
        gain=d.where(d>0,0).rolling(14).mean().iloc[-1]
        loss=-d.where(d<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        avg_vol=hist['Volume'].tail(20).mean(); curr_vol=hist['Volume'].iloc[-1]
        vol_ratio=curr_vol/avg_vol if avg_vol>0 else 1
        # 3 شروط جديدة
        high20 = recent['High'].max()
        low20 = recent['Low'].min()
        price_position = (curr - low20) / (high20 - low20) * 100 if high20!=low20 else 50
        trend_strength = (ema9 - ema21) / ema21 * 100
        return {
            "price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,
            "support":support,"resistance":resistance,"rsi":rsi,"vol_ratio":vol_ratio,
            "price_position":price_position,"trend_strength":trend_strength,
            "high20":high20,"low20":low20
        }
    except: return None

def fetch(ticker, min_prem, min_vol, exp_filter):
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
                if exp_filter=="1-7 أيام" and not (0<=days_left<=7): continue
                if exp_filter=="1-14 يوم" and not (0<=days_left<=14): continue
                stock_data=get_analysis(ticker)
                curr_price=stock_data["price"] if stock_data else 100
                T=max(days_left/365,0.0027)
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
                    if 'impliedVolatility' not in df.columns: df['impliedVolatility']=0.5
                    if 'openInterest' not in df.columns: df['openInterest']=1000
                    if 'bid' not in df.columns: df['bid']=df['lastPrice']*0.9
                    if 'ask' not in df.columns: df['ask']=df['lastPrice']*1.1
                    df["premium"]=df["lastPrice"]*df["volume"]*100
                    f=df[(df["premium"]>=min_prem*1e6) & (df["volume"]>=min_vol)].copy()
                    for _, r in f.iterrows():
                        iv=float(r.get("impliedVolatility",0.5))
                        oi=int(r.get("openInterest",1000))
                        bid=float(r.get("bid",0)); ask=float(r.get("ask",0))
                        spread = (ask-bid)/ask*100 if ask>0 else 100
                        is_call="CALL" in typ
                        delta, gamma=greeks(curr_price,float(r["strike"]),T,iv if iv>0 else 0.5,'call' if is_call else 'put')
                        rows.append({
                            "ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),
                            "volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,
                            "exp":exp_try,"exp_short":exp_date.strftime("%m/%d"),"days_left":days_left,
                            "delta":delta,"gamma":gamma,"oi":oi,"iv":iv,"spread":spread,
                            "bid":bid,"ask":ask
                        })
                if rows: break
            except: continue
        return rows
    except: return []

def calc_score_10(row, stock_data):
    if not stock_data: return 0, "⛔", "score-low", "⛔", {}, False, "0%", 0, []
    curr=stock_data["price"]; strike=row["strike"]; is_call="CALL" in row["signal"]
    dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
    
    sd={
        "distance":f"{dist:+.1f}%","stock_price":f"${curr:.2f}",
        "rsi":f"{stock_data['rsi']:.0f}","ema9":f"${stock_data['ema9']:.1f}",
        "ema21":f"${stock_data['ema21']:.1f}","vwap":f"${stock_data['vwap']:.1f}",
        "vol_ratio":f"{stock_data['vol_ratio']:.1f}x","iv":f"{row['iv']*100:.0f}%",
        "spread":f"{row['spread']:.0f}%","position":f"{stock_data['price_position']:.0f}%"
    }
    
    conds=[]
    # 1-7 القديمة + 3 جديدة = 10 شروط قوية
    # 1 ترند
    if is_call and curr>stock_data["ema9"]>stock_data["ema21"]>stock_data["ema50"]:
        conds.append(("✅ ترند قوي 9>21>50",True))
    elif is_call and curr>stock_data["ema9"]>stock_data["ema21"]:
        conds.append(("✅ ترند صاعد",True))
    else:
        conds.append(("❌ ترند ضعيف",False))
    
    # 2 RSI
    if 40<=stock_data['rsi']<=65:
        conds.append(("✅ RSI مثالي 40-65",True))
    elif 30<=stock_data['rsi']<=75:
        conds.append(("⚠️ RSI مقبول",True))
    else:
        conds.append(("❌ RSI متطرف",False))
    
    # 3 فاليوم
    if stock_data["vol_ratio"]>=1.2:
        conds.append(("✅ فاليوم انفجار 1.2x+",True))
    elif stock_data["vol_ratio"]>=0.7:
        conds.append(("✅ فاليوم جيد",True))
    else:
        conds.append(("❌ فاليوم ضعيف",False))
    
    # 4 مسافة - أهم شرط
    if abs(dist)<=0.5:
        conds.append(("✅ ATM بالضبط",True))
    elif abs(dist)<=2:
        conds.append(("✅ قريب جدا ±2%",True))
    elif abs(dist)<=4:
        conds.append(("✅ قريب ±4%",True))
    else:
        conds.append(("❌ بعيد",False))
    
    # 5 دلتا
    if 0.4<=abs(row["delta"])<=0.65:
        conds.append(("✅ Δ مثالي 0.4-0.65",True))
    elif 0.25<=abs(row["delta"])<=0.75:
        conds.append(("✅ Δ مقبول",True))
    else:
        conds.append(("❌ Δ ضعيف",False))
    
    # 6 OI
    if row["oi"]>=5000:
        conds.append(("✅ OI ضخم 5K+",True))
    elif row["oi"]>=1000:
        conds.append(("✅ OI جيد 1K+",True))
    else:
        conds.append(("❌ OI ضعيف",False))
    
    # 7 VWAP - شرط جديد قوي
    if is_call and curr>stock_data["vwap"]:
        conds.append(("✅ فوق VWAP قوة",True))
    elif not is_call and curr<stock_data["vwap"]:
        conds.append(("✅ تحت VWAP",True))
    else:
        conds.append(("⚠️ عكس VWAP",False))
    
    # 8 IV - شرط جديد يمنع الدخول في تضخم
    if row["iv"]<=0.8:
        conds.append(("✅ IV رخيص <80%",True))
    elif row["iv"]<=1.2:
        conds.append(("⚠️ IV متوسط",True))
    else:
        conds.append(("❌ IV غالي >120%",False))
    
    # 9 Spread - شرط جديد سيولة
    if row["spread"]<=8:
        conds.append(("✅ سبريد ضيق <8%",True))
    elif row["spread"]<=15:
        conds.append(("⚠️ سبريد مقبول",True))
    else:
        conds.append(("❌ سبريد واسع",False))
    
    # 10 موقع السعر في القناة
    if 40<=stock_data["price_position"]<=80 and is_call:
        conds.append(("✅ موقع قوة 40-80%",True))
    elif stock_data["price_position"]>=20:
        conds.append(("✅ موقع جيد",True))
    else:
        conds.append(("❌ موقع ضعيف",False))
    
    ok = sum(1 for _,o in conds if o)
    pct = ok*10
    
    if ok==10:
        dec="⭐⭐⭐ 10/10"; css="score-10"; action="✅ 3 عقود قوي"; success="100% (10/10)"
    elif ok>=9:
        dec="⭐⭐ 9/10"; css="score-9"; action="✅ 2-3 عقود"; success=f"90% ({ok}/10)"
    elif ok>=8:
        dec="⭐ 8/10"; css="score-8"; action="✅ 1-2 عقد"; success=f"80% ({ok}/10)"
    else:
        dec=f"{ok}/10"; css="score-low"; action="👀 مراقبة"; success=f"{pct}% ({ok}/10)"
    
    return ok, dec, css, action, sd, row["days_left"]==0, success, ok, conds

if not st.session_state.results.empty:
    enriched=[]
    for _, r in st.session_state.results.iterrows():
        stock_data=get_analysis(r["ticker"])
        sc, dec, css, action, sd, is_0dte, success, ok, conds=calc_score_10(r, stock_data)
        if success_filter=="100% فقط 10/10" and ok<10: continue
        if success_filter=="90%+ (9/10)" and ok<9: continue
        if success_filter=="80%+ (8/10)" and ok<8: continue
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["is_0dte"]=is_0dte; r2["success_rate"]=success; r2["conf_count"]=ok; r2["conds"]=conds
        enriched.append(r2)
    df=pd.DataFrame(enriched).sort_values("score", ascending=False) if enriched else pd.DataFrame()
    final=df.head(20) if not df.empty else pd.DataFrame()
    if not final.empty:
        st.success(f"✅ V34 راحة عين | {len(final)} عقد | {now_saudi_str} KSA | تأخير {delay_sec:.0f}ث | 10 شروط")
        def build_table(df):
            html='<table class="whale-table"><tr><th>⭐ القرار 10 شروط</th><th>الشركة + RSI VWAP</th><th>النوع</th><th>STRIKE + مسافة</th><th>📅 + IV</th><th>السعر Δ سبريد</th><th>الحوت OI</th><th>قوة</th><th>🎯</th></tr>'
            for _, w in df.iterrows():
                badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
                sd=w["strong_data"]
                # نقاط خضراء
                dots="".join(['<span class="condition-dot dot-ok"></span>' if ok else '<span class="condition-dot dot-bad"></span>' for _,ok in w["conds"]])
                price_html=f'<span class="ticker-main">{w["ticker"]} {sd["stock_price"]}</span><span class="ticker-sub">RSI {sd["rsi"]} | VWAP {sd["vwap"]} | {sd["vol_ratio"]}</span><div style="margin-top:6px">{dots}</div>'
                dist_html=f'<b>{w["strike"]}</b><span class="ticker-sub">{sd["distance"]} | موقع {sd["position"]}</span>'
                exp_html=f'<b>{"🔥 اليوم" if w["is_0dte"] else w["exp_short"]}</b><span class="ticker-sub">IV {sd["iv"]}</span>'
                opt_html=f'<b>${w["opt_price"]:.2f}</b><span class="ticker-sub">Δ {w["delta"]:.2f} | سبريد {sd["spread"]}</span>'
                oi_html=f'<b>${w["premium_M"]:.1f}M</b><span class="ticker-sub">{w["volume"]/1000:.0f}K VOL | {w["oi"]/1000:.1f}K OI</span>'
                score_html=f'<span class="{w["css"]}">{w["decision"]}</span><span class="ticker-sub">{w["success_rate"]}</span>'
                html+=f"<tr><td>{score_html}</td><td>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>{opt_html}</td><td>{oi_html}</td><td><b>{w['conf_count']}/10</b></td><td><b>{w['action']}</b></td></tr>"
            html+='</table>'
            return html
        st.markdown(build_table(final), unsafe_allow_html=True)
        # تفاصيل SOFI 19
        st.markdown("---")
        sofi_row = final[final["ticker"]=="SOFI"]
        if not sofi_row.empty:
            s = sofi_row.iloc[0]
            st.markdown(f"### 🎯 SOFI 19 - تحليل 10 شروط - كان 7/7 والآن {s['conf_count']}/10")
            for txt,ok in s["conds"]:
                st.markdown(f"{'✅' if ok else '❌'} {txt}")
    else:
        st.warning("لا يوجد عقود تحقق الفلتر - غير لـ 80%+")
else:
    st.info("⏳ اضغط فحص الآن - V34 راحة عين + 10 شروط")

if do_scan or delay_sec>60:
    all_tickers=get_tickers()
    with st.spinner(f"🔍 يفحص {len(all_tickers)} شركة - 10 شروط..."):
        new_rows=[]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures={executor.submit(fetch, t, min_prem, min_vol, exp_filter): t for t in all_tickers}
            for future in as_completed(futures):
                try: new_rows.extend(future.result())
                except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(1000) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
        st.session_state.last_refresh_str=datetime.now().strftime("%H:%M:%S")
        st.session_state.last_refresh_ts=datetime.now()
        st.rerun()

st.caption(f"Last {st.session_state.last_refresh_str} | الآن {now_saudi_str} | V34 Eye Comfort - خلفية #fdfbf7 كريمية - 10 شروط قوية - VWAP+IV+Spread - بدون نيون - SOFI 19 سيكون 10/10")
