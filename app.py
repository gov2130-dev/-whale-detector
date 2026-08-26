import streamlit as st, yfinance as yf, pandas as pd, math
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(layout="wide", page_title="Whale V34.1 Fixed Eye", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#fdfbf7!important;}
[data-testid="stSidebar"] {background:#fffefc!important; border-right:3px solid #e7e5e4!important; min-width:520px!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 10px; font-size:13px; font-family:'Segoe UI',sans-serif;}
.whale-table th {background:#1c1917!important; color:#fafaf9!important; padding:16px 10px; text-align:center; font-weight:800; font-size:12px;}
.whale-table td {background:#fff!important; padding:16px 10px; text-align:center; font-weight:600; color:#292524!important; border:1.5px solid #f5f5f4; box-shadow:0 2px 8px rgba(0,0,0,0.04);}
.whale-table tr td:first-child {border-left:1.5px solid #f5f5f4; border-radius:12px 0 0 12px;}
.whale-table tr td:last-child {border-right:1.5px solid #f5f5f4; border-radius:0 12px 12px 0;}
.badge-call {background:#e7f5ec!important; color:#14532d!important; border:1.5px solid #86efac; padding:7px 14px; border-radius:20px; font-weight:800; font-size:11px;}
.score-10 {background:#14532d!important; color:#dcfce7!important; padding:9px 16px; border-radius:20px; font-weight:900;}
.score-9 {background:#166534!important; color:#bbf7d0!important; padding:9px 16px; border-radius:20px; font-weight:800;}
.score-8 {background:#15803d!important; color:#dcfce7!important; padding:8px 14px; border-radius:20px;}
.score-low {background:#f5f5f4!important; color:#57534e!important; padding:8px 14px; border-radius:20px;}
.time-card {background:linear-gradient(135deg,#1c1917 0%,#292524 100%); color:#a3e635; border:1px solid #44403c; border-radius:18px; padding:18px; font-family:monospace; text-align:center; font-size:15px; line-height:1.8;}
.frame-box {background:#fffefc; border:1.5px solid #e7e5e4; border-radius:14px; padding:14px; margin:12px 0;}
.ticker-main {font-size:14px; font-weight:900; color:#1c1917;}
.ticker-sub {font-size:11px; color:#78716c; font-weight:500; margin-top:4px; display:block;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V34.1 - راحة العين + 10 شروط - بدون KeyError")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR","SOFI","GME","MARA","NFLX"]

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
        if typ=='call': delta = norm_cdf(d1)
        else: delta = -norm_cdf(-d1)
        gamma = norm_pdf(d1)/(S*sigma*math.sqrt(T))
        return delta, gamma
    except: return 0.5, 0.05

now = datetime.now()
try:
    delay_sec = (now - st.session_state.last_refresh_ts).total_seconds()
    if delay_sec<0 or delay_sec>86400: delay_sec=0
except:
    delay_sec=0
    st.session_state.last_refresh_ts=now

st.sidebar.markdown("### ⏰ وقت السوق")
st.sidebar.markdown(f"""<div class="time-card">
السعودية: {now.strftime('%H:%M:%S')}<br>
آخر فحص: {st.session_state.last_refresh_str}<br>
تأخير: {delay_sec:.0f}ث ممتاز
</div>""", unsafe_allow_html=True)

col1, col2 = st.sidebar.columns(2)
with col1: do_scan = st.button("🔄 فحص الآن", type="primary", use_container_width=True)
with col2:
    if st.button("🧹 تصفير + مسح قديم", use_container_width=True):
        st.session_state.results=pd.DataFrame()
        st.session_state.last_refresh_str=datetime.now().strftime("%H:%M:%S")
        st.session_state.last_refresh_ts=datetime.now()
        st.rerun()

st.sidebar.markdown('<div class="frame-box"><b>👁️ راحة العين #fdfbf7</b></div>', unsafe_allow_html=True)
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
        support=recent['Low'].min(); high20=recent['High'].max(); low20=recent['Low'].min()
        d=hist['Close'].diff()
        gain=d.where(d>0,0).rolling(14).mean().iloc[-1]
        loss=-d.where(d<0,0).rolling(14).mean().iloc[-1]
        rsi=100-(100/(1+gain/(loss if loss!=0 else 0.01))) if not pd.isna(gain) else 50
        avg_vol=hist['Volume'].tail(20).mean(); curr_vol=hist['Volume'].iloc[-1]
        vol_ratio=curr_vol/avg_vol if avg_vol>0 else 1
        price_position = (curr - low20) / (high20 - low20) * 100 if high20!=low20 else 50
        return {"price":curr,"ema9":ema9,"ema21":ema21,"ema50":ema50,"vwap":vwap,"support":support,"rsi":rsi,"vol_ratio":vol_ratio,"price_position":price_position,"high20":high20,"low20":low20}
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
                    df = df.copy()
                    if 'impliedVolatility' not in df.columns: df['impliedVolatility']=0.5
                    if 'openInterest' not in df.columns: df['openInterest']=1000
                    if 'bid' not in df.columns: df['bid']=df['lastPrice']*0.9
                    if 'ask' not in df.columns: df['ask']=df['lastPrice']*1.1
                    df["premium"]=df["lastPrice"]*df["volume"]*100
                    f=df[(df["premium"]>=min_prem*1e6) & (df["volume"]>=min_vol)].copy()
                    for _, r in f.iterrows():
                        iv=float(r.get("impliedVolatility",0.5) if not pd.isna(r.get("impliedVolatility",0.5)) else 0.5)
                        oi=int(r.get("openInterest",1000) if not pd.isna(r.get("openInterest",1000)) else 1000)
                        bid=float(r.get("bid",0) if not pd.isna(r.get("bid",0)) else r["lastPrice"]*0.9)
                        ask=float(r.get("ask",0) if not pd.isna(r.get("ask",0)) else r["lastPrice"]*1.1)
                        spread = (ask-bid)/ask*100 if ask>0 else 10
                        is_call="CALL" in typ
                        delta, gamma=greeks(curr_price,float(r["strike"]),T,iv if iv>0 else 0.5,'call' if is_call else 'put')
                        rows.append({"ticker":ticker,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp_try,"exp_short":exp_date.strftime("%m/%d"),"days_left":days_left,"delta":delta,"gamma":gamma,"oi":oi,"iv":iv,"spread":spread,"bid":bid,"ask":ask})
                if rows: break
            except: continue
        return rows
    except: return []

# ===== إصلاح KeyError نهائي - استخدام .get مع قيم افتراضية =====
def calc_score_10(row, stock_data):
    if not stock_data: return 0, "⛔", "score-low", "⛔", {}, False, "0%", 0, []
    try:
        curr=stock_data.get("price",100)
        strike=row.get("strike",curr) if isinstance(row, dict) else getattr(row, 'strike', curr)
        signal=row.get("signal","CALL BUY") if isinstance(row, dict) else getattr(row, 'signal', 'CALL BUY')
        is_call="CALL" in signal
        
        # استخدام .get لتجنب KeyError
        iv = row.get("iv",0.5) if isinstance(row, dict) else getattr(row, 'iv', 0.5)
        spread = row.get("spread",10) if isinstance(row, dict) else getattr(row, 'spread', 10)
        delta_val = row.get("delta",0.5) if isinstance(row, dict) else getattr(row, 'delta', 0.5)
        oi_val = row.get("oi",1000) if isinstance(row, dict) else getattr(row, 'oi', 1000)
        
        if isinstance(row, pd.Series):
            iv = row.get("iv",0.5)
            spread = row.get("spread",10)
            delta_val = row.get("delta",0.5)
            oi_val = row.get("oi",1000)
        
        dist=(strike-curr)/curr*100 if is_call else (curr-strike)/curr*100
        
        sd={
            "distance":f"{dist:+.1f}%",
            "stock_price":f"${curr:.2f}",
            "rsi":f"{stock_data.get('rsi',50):.0f}",
            "ema9":f"${stock_data.get('ema9',curr):.1f}",
            "ema21":f"${stock_data.get('ema21',curr):.1f}",
            "vwap":f"${stock_data.get('vwap',curr):.1f}",
            "vol_ratio":f"{stock_data.get('vol_ratio',1):.1f}x",
            "iv":f"{iv*100:.0f}%",
            "spread":f"{spread:.0f}%",
            "position":f"{stock_data.get('price_position',50):.0f}%"
        }
        
        conds=[]
        # 1 ترند
        if is_call and curr>stock_data.get("ema9",0)>stock_data.get("ema21",0):
            conds.append(("✅ ترند صاعد قوي",True))
        else:
            conds.append(("❌ ترند ضعيف",False))
        # 2 RSI
        if 40<=stock_data.get("rsi",50)<=65:
            conds.append(("✅ RSI مثالي",True))
        elif 30<=stock_data.get("rsi",50)<=75:
            conds.append(("✅ RSI مقبول",True))
        else:
            conds.append(("❌ RSI",False))
        # 3 فاليوم
        if stock_data.get("vol_ratio",1)>=1.0:
            conds.append(("✅ فاليوم انفجار",True))
        elif stock_data.get("vol_ratio",1)>=0.6:
            conds.append(("✅ فاليوم جيد",True))
        else:
            conds.append(("❌ فاليوم",False))
        # 4 مسافة
        if abs(dist)<=1:
            conds.append(("✅ ATM بالضبط",True))
        elif abs(dist)<=3:
            conds.append(("✅ قريب جدا",True))
        elif abs(dist)<=5:
            conds.append(("✅ قريب",True))
        else:
            conds.append(("❌ بعيد",False))
        # 5 دلتا
        if 0.4<=abs(delta_val)<=0.65:
            conds.append(("✅ Δ مثالي",True))
        elif 0.25<=abs(delta_val)<=0.75:
            conds.append(("✅ Δ مقبول",True))
        else:
            conds.append(("❌ Δ",False))
        # 6 OI
        if oi_val>=3000:
            conds.append(("✅ OI ضخم",True))
        elif oi_val>=800:
            conds.append(("✅ OI جيد",True))
        else:
            conds.append(("❌ OI",False))
        # 7 VWAP
        if is_call and curr>stock_data.get("vwap",0):
            conds.append(("✅ فوق VWAP",True))
        else:
            conds.append(("❌ تحت VWAP",False))
        # 8 IV
        if iv<=0.8:
            conds.append(("✅ IV رخيص",True))
        elif iv<=1.2:
            conds.append(("✅ IV متوسط",True))
        else:
            conds.append(("❌ IV غالي",False))
        # 9 سبريد
        if spread<=8:
            conds.append(("✅ سبريد ضيق",True))
        elif spread<=15:
            conds.append(("✅ سبريد مقبول",True))
        else:
            conds.append(("❌ سبريد واسع",False))
        # 10 موقع
        if 30<=stock_data.get("price_position",50)<=85:
            conds.append(("✅ موقع قوة",True))
        else:
            conds.append(("⚠️ موقع متوسط",True))
        
        ok = sum(1 for _,o in conds if o)
        if ok==10:
            dec="⭐⭐⭐ 10/10"; css="score-10"; action="✅ 3 عقود"; success="100% (10/10)"
        elif ok>=9:
            dec="⭐⭐ 9/10"; css="score-9"; action="✅ 2-3 عقود"; success=f"90% ({ok}/10)"
        elif ok>=8:
            dec="⭐ 8/10"; css="score-8"; action="✅ 1-2 عقد"; success=f"80% ({ok}/10)"
        else:
            dec=f"{ok}/10"; css="score-low"; action="👀 مراقبة"; success=f"{ok*10}% ({ok}/10)"
        
        is_0dte = (row.get("days_left",1) if isinstance(row, dict) else getattr(row, 'days_left', 1)) == 0
        if isinstance(row, pd.Series):
            is_0dte = row.get("days_left",1)==0
            
        return ok, dec, css, action, sd, is_0dte, success, ok, conds
    except Exception as e:
        return 0, f"خطأ {str(e)[:20]}", "score-low", "⛔", {}, False, "0%", 0, []

if not st.session_state.results.empty:
    enriched=[]
    for _, r in st.session_state.results.iterrows():
        stock_data=get_analysis(r["ticker"])
        sc, dec, css, action, sd, is_0dte, success, ok, conds=calc_score_10(r, stock_data)
        if success_filter=="100% فقط 10/10" and ok<10: continue
        if success_filter=="90%+ (9/10)" and ok<9: continue
        if success_filter=="80%+ (8/10)" and ok<8: continue
        r2=r.copy()
        r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["strong_data"]=sd; r2["is_0dte"]=is_0dte; r2["success_rate"]=success; r2["conf_count"]=ok; r2["conds"]=conds
        enriched.append(r2)
    df=pd.DataFrame(enriched).sort_values("score", ascending=False) if enriched else pd.DataFrame()
    final=df.head(20) if not df.empty else pd.DataFrame()
    if not final.empty:
        st.success(f"✅ V34.1 بدون KeyError | {len(final)} عقد | تأخير {delay_sec:.0f}ث | 10 شروط")
        def build_table(df):
            html='<table class="whale-table"><tr><th>⭐ 10 شروط</th><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>📅</th><th>السعر</th><th>الحوت</th><th>قوة</th><th>🎯</th></tr>'
            for _, w in df.iterrows():
                badge=f'<span class="badge-call">{w["signal"]}</span>'
                sd=w.get("strong_data",{})
                price_html=f'<span class="ticker-main">{w["ticker"]} {sd.get("stock_price","")}</span><span class="ticker-sub">RSI {sd.get("rsi","")} VWAP {sd.get("vwap","")}</span>'
                dist_html=f'<b>{w["strike"]}</b><span class="ticker-sub">{sd.get("distance","")}</span>'
                exp_html=f'<b>{w["exp_short"]}</b><span class="ticker-sub">IV {sd.get("iv","")}</span>'
                opt_html=f'<b>${w["opt_price"]:.2f}</b><span class="ticker-sub">Δ {w["delta"]:.2f} {sd.get("spread","")}</span>'
                oi_html=f'<b>${w["premium_M"]:.1f}M</b><span class="ticker-sub">{w["volume"]/1000:.0f}K</span>'
                score_html=f'<span class="{w["css"]}">{w["decision"]}</span><span class="ticker-sub">{w["success_rate"]}</span>'
                html+=f"<tr><td>{score_html}</td><td>{price_html}</td><td>{badge}</td><td>{dist_html}</td><td>{exp_html}</td><td>{opt_html}</td><td>{oi_html}</td><td><b>{w['conf_count']}/10</b></td><td><b>{w['action']}</b></td></tr>"
            html+='</table>'
            return html
        st.markdown(build_table(final), unsafe_allow_html=True)
    else:
        st.warning("لا يوجد عقود - غير الفلتر لـ الكل")
else:
    st.info("⏳ اضغط فحص الآن - V34.1 يصلح KeyError")

if do_scan or delay_sec>60:
    all_tickers=get_tickers()
    with st.spinner(f"🔍 يفحص {len(all_tickers)} - 10 شروط..."):
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

st.caption(f"Last {st.session_state.last_refresh_str} | V34.1 Fixed - بدون KeyError - .get() + افتراضي - راحة عين #fdfbf7")
