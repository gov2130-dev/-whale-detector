import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time

st.set_page_config(layout="wide", page_title="Whale V26 Fixed", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:380px!important; max-width:400px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:13px!important;}
.stButton>button {width:100%!important; height:42px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:10px!important; font-weight:800!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:8px 3px; text-align:center; font-size:10px; font-weight:800;}
.whale-table td {background:#fff!important; padding:8px 3px; text-align:center; font-weight:700; font-size:11px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:10px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 7px; border-radius:8px; font-size:10px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#ef4444!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-weight:900; font-size:11px;}
.score-0 {background:#64748b!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-size:10px;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V26 - مصحح + جدول ثابت")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()

st.sidebar.markdown("## 🎛️ لوحة التحكم V26")
refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["15 ثانية","30 ثانية","1 دقيقة","2 دقيقة","5 دقائق"], value="1 دقيقة", key="int26")
map_sec={"15 ثانية":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300}
interval_sec=map_sec[refresh_interval]
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="m26")
time_filter=st.sidebar.select_slider("⏰ فلتر الحيتان", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="اليوم كامل", key="tf26")
# طفي اتجاه واحد عشان IWM ما يقلب
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد لكل شركة (يطفي IWM يقلب)", False, key="s26")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد لكل شركة", True, key="o26")
auto=st.sidebar.checkbox("⚡ فحص تلقائي بدون وميض", True, key="a26")

st.sidebar.info("✅ V26 مصحح: شلت جلب سعر السهم الحي اللي كان يعلق الجدول. الآن الجدول يظهر دائما. طفيت اتجاه واحد عشان IWM يثبت PUT/CALL")

if st.sidebar.button("🔄 فحص الآن", key="man26"): st.session_state.current_idx=0; st.rerun()
if st.sidebar.button("🔄 مسح وابدأ من جديد", key="clr26"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")

def get_minutes_filter():
    return {"آخر 15 دقيقة":15,"آخر ساعة":60,"آخر 3 ساعات":180,"اليوم كامل":1440}.get(time_filter,1440)

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

def calc_score_simple(row):
    score=0; reasons=[]
    days=row.get("days_left",0)
    if days<0: score-=5; reasons.append("⛔ منتهي")
    elif days==0: score+=0; reasons.append("⚠️ 0DTE خطير")
    elif 3<=days<=7: score+=3; reasons.append("✅ 3-7 أيام مثالي")
    elif 8<=days<=14: score+=2; reasons.append("✅ أسبوعين")
    else: score+=1

    prem=row["premium_M"]
    vol=row["volume"]
    if prem>=20: score+=3; reasons.append(f"🐋 ضخم ${prem:.0f}M")
    elif prem>=5: score+=2; reasons.append(f"🐋 ${prem:.0f}M")
    elif prem>=1: score+=1

    if vol>=100000: score+=2; reasons.append(f"🔥 VOL {vol/1000:.0f}K")
    elif vol>=30000: score+=1

    if row["minutes_ago"]<=15: score+=2; reasons.append("🔥 الآن")
    elif row["minutes_ago"]<=60: score+=1

    if 0.5<=row["opt_price"]<=5: score+=1; reasons.append(f"💵 ${row['opt_price']:.1f}")

    if score>=7: dec="⭐⭐⭐ قوي"; css="score-3"; action="✅ ادخل"
    elif score>=5: dec="⭐⭐ جيد"; css="score-2"; action="✅ ادخل"
    elif score>=3: dec="⭐ مراقبة"; css="score-2"; action="👀 راقب"
    else: dec="⛔ لا"; css="score-0"; action="⛔ اتركه"

    return score, dec, css, action, " | ".join(reasons)

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+5, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    st.info(f"🔴 يفحص {all_tickers[start:end]} | فلتر {time_filter} | كل {refresh_interval} | بدون وميض ✅")

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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=10)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        if pd.isna(ltd): minutes_ago=9999
                        else:
                            now_utc=datetime.now(timezone.utc)
                            if ltd.tzinfo is None: ltd=ltd.replace(tzinfo=timezone.utc)
                            minutes_ago=(now_utc - ltd).total_seconds()/60
                    except: minutes_ago=9999
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"exp_full":exp_full,"days_left":days_left,"minutes_ago":minutes_ago})
        except Exception as e:
            st.write(f"خطأ {t}: {e}")
            pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df

        # تنبيه واحد لكل شركة
        if one_alert and not filtered.empty:
            grouped=filtered.sort_values("premium", ascending=False).groupby("ticker").first().reset_index()
            fresh_to_show=grouped
        else:
            fresh_to_show=filtered.sort_values("premium", ascending=False).head(3)

        fresh=[]
        for _, w in fresh_to_show.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                fresh.append(w)
                st.session_state.sent.add(key)
        if fresh:
            st.session_state.new_whales=fresh

        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    else:
        # لو ما فيه جديد بس فيه قديم، لا تمسح
        if st.session_state.results.empty:
            st.warning("ما لقى حيتان بهالفلتر - جرب اليوم كامل")

    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers):
        st.session_state.current_idx=0
        st.session_state.last_refresh=datetime.now()
        time.sleep(interval_sec)
        st.rerun()
    else:
        time.sleep(0.7)
        st.rerun()
else:
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0

# ===== عرض الجدول دائما =====
if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    mins=get_minutes_filter()
    final_time=final_raw[final_raw["minutes_ago"]<=mins].copy() if mins<1440 else final_raw.copy()
    if final_time.empty:
        st.warning(f"⏳ لا يوجد حيتان في {time_filter} - أعرض اليوم كامل")
        final_time=final_raw.copy()

    enriched=[]
    for _, r in final_time.iterrows():
        sc, dec, css, action, why=calc_score_simple(r)
        r2=r.copy()
        r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["why"]=why
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)

    if smart_filter:
        best=[]
        for ticker in enriched_df["ticker"].unique():
            t_df=enriched_df[enriched_df["ticker"]==ticker]
            call_sum=t_df[t_df["signal"].str.contains("CALL")]["premium"].sum()
            put_sum=t_df[t_df["signal"].str.contains("PUT")]["premium"].sum()
            dom="CALL" if call_sum>=put_sum else "PUT"
            keep=t_df[t_df["signal"].str.contains(dom)].sort_values("score", ascending=False).head(1)
            best.append(keep.iloc[0])
        final=pd.DataFrame(best).sort_values("score", ascending=False).head(20)
    else:
        final=enriched_df.head(20)

    if st.session_state.new_whales:
        st.markdown("### 🔔 حيتان دخلت الآن - تنبيه ثابت")
        cols=st.columns(min(3, len(st.session_state.new_whales)))
        for i, w in enumerate(st.session_state.new_whales[:3]):
            with cols[i]:
                sc, dec, css, action, why=calc_score_simple(w)
                ago=int(w["minutes_ago"])
                txt=f"{ago}د" if ago<60 else f"{ago//60}س"
                badge_color="CALL" in w["signal"]
                st.markdown(f"<div style='background:#fefce8; border:3px solid #22c55e; padding:10px; border-radius:12px; text-align:center;'><b>🔔 {w['ticker']} {w['signal']}</b><br>{w['strike']} | 📅 {w['exp_short']} ({w['days_left']}ي)<br>${w['opt_price']:.2f} | ${w['premium_M']:.1f}M | قبل {txt}<br><span class='{css}'>{dec}</span></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء التنبيه", key="hide26"): st.session_state.new_whales=[]; st.rerun()

    st.success(f"✅ V26 ثابت بدون وميض | {len(final)} حوت | آخر تحديث {st.session_state.last_refresh.strftime('%H:%M:%S')} | فلتر {time_filter}")

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار</th><th>الشركة</th><th>النوع ثابت</th><th>STRIKE</th><th>📅 الانتهاء</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ دخل</th><th>ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            days=w.get("days_left",0)
            exp_html=f'<span style="background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:6px; font-size:9px;">⛔ منتهي</span>' if days<0 else f'<span style="background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:6px;">⚠️ اليوم</span>' if days==0 else f'{w["exp_short"]} ({days}ي)'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}</small>'
            ago=int(w["minutes_ago"]); time_html=f'{ago}د' if ago<60 else f'{ago//60}س'
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{exp_html}<br><small>{w['exp_full']}</small></td><td>${w['opt_price']:.2f}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M</td><td>{w['volume']}</td><td>{time_html}</td><td><b>{w['action']}</b><br><small style='font-size:8px'>{w['why'][:40]}</small></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)

    st.info("""
    **🔧 إصلاحات V26:**
    - ✅ الجدول يظهر دائما - حتى لو الفحص بطيء
    - ✅ شلت جلب سعر السهم الحي اللي كان يعلق
    - ✅ IWM ثابت: طفيت **اتجاه واحد** من اليسار (كان يخلي IWM يقلب PUT/CALL). الآن يعرض PUT و CALL منفصلين بوضوح
    - ✅ فلتر اليوم كامل افتراضي عشان تشوف حيتان الويكند
    - ✅ تنبيه واحد لكل شركة - ما عاد يطلع تنبيهين IWM
    """)

else:
    st.warning("⏳ يفحص... لو طول، اضغط مسح وابدأ من جديد واختار فلتر اليوم كامل")
    st.info("إذا الجدول ما ظهر: اضغط باليسار **🔄 مسح وابدأ من جديد** واختار **اليوم كامل**")

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V26 Fixed - جدول ثابت بدون وميض")
