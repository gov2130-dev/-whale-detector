import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime, timezone
import time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V21 Clear", initial_sidebar_state="expanded")
components.html("<script>setTimeout(function(){window.parent.location.reload();}, 35000);</script>", height=0)

# ===== إصلاح الألوان - خلفية بيضاء وكتابة سوداء واضحة =====
st.markdown("""
<style>
/* الخلفية كلها بيضاء */
.stApp {background:#ffffff!important;}
[data-testid="stHeader"] {background:#ffffff!important;}
h1, h2, h3, h4, p, div, span {color:#0f172a!important;}
/* العناوين كبيرة وواضحة */
h1 {color:#0f172a!important; font-weight:900!important; font-size:32px!important; background:#ffffff; padding:10px; border-radius:10px;}
h2, h3 {color:#1e293b!important; font-weight:800!important; background:#f1f5f9; padding:8px 12px; border-radius:8px; border-left:4px solid #3b82f6;}

/* السايد بار */
[data-testid="stSidebar"] {min-width:365px!important; max-width:385px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:14px!important;}
.stButton>button {width:100%!important; height:48px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:12px!important; font-weight:800!important;}

/* الجدول واضح جدا */
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#0f172a!important; color:#ffffff!important; padding:12px 8px; text-align:center; font-size:12px; font-weight:800;}
.whale-table td {background:#ffffff!important; padding:12px 8px; text-align:center; font-weight:700; font-size:13px; color:#0f172a!important; border:1px solid #e2e8f0;}
.whale-table tr {box-shadow:0 2px 8px #0001; border-radius:10px;}

.badge-call {background:#22c55e!important; color:#ffffff!important; padding:5px 10px; border-radius:12px; font-size:11px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#ffffff!important; padding:5px 10px; border-radius:12px; font-size:11px; font-weight:800;}
.optprice {color:#7c3aed!important; font-weight:900!important; background:#f5f3ff!important; padding:5px 10px; border-radius:8px; border:1px solid #ddd6fe;}
.premium {color:#1d4ed8!important; font-weight:900!important; font-size:14px!important;}
.time-new {background:#22c55e!important; color:#ffffff!important; padding:4px 8px; border-radius:10px; font-size:11px; font-weight:800;}
.time-old {background:#64748b!important; color:#ffffff!important; padding:4px 8px; border-radius:10px; font-size:11px;}

/* كرت التنبيه واضح */
.alert-card {background:#fefce8!important; border:3px solid #22c55e!important; padding:16px!important; border-radius:16px!important; text-align:center!important; box-shadow:0 4px 12px #0002;}
.alert-card b,.alert-card div {color:#0f172a!important; font-weight:800!important; font-size:14px!important;}

/* رسائل النجاح والتحذير */
.stSuccess,.stInfo,.stWarning {background:#f1f5f9!important; border:2px solid #3b82f6!important; color:#0f172a!important;}
.stSuccess *,.stInfo *,.stWarning * {color:#0f172a!important; font-weight:700!important;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V21 - واضح 100%")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

def play_bell(times=1):
    components.html(f"""
    <script>
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    for(let i=0;i<{times};i++){{ setTimeout(()=>{{
        const o1=ctx.createOscillator(); const g1=ctx.createGain(); o1.connect(g1); g1.connect(ctx.destination);
        o1.frequency.value=880; g1.gain.setValueAtTime(0.8, ctx.currentTime);
        g1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+0.8); o1.start(); o1.stop(ctx.currentTime+0.8);
    }}, i*350); }}
    if(navigator.vibrate) navigator.vibrate([200,100,200]);
    </script>""", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="LASTHOUR"
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]

st.sidebar.markdown("## 🎛️ لوحة التحكم - واضحة")
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min21")
time_filter=st.sidebar.select_slider("⏰ فلتر الوقت", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf21")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد", True, key="bell21")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد لكل شركة", True, key="sm21")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد لكل شركة", True, key="one21")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au21")

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
if st.sidebar.button("⏰ آخر ساعة", key="b0_21"): st.session_state.page="LASTHOUR"
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b1_21"): st.session_state.page="15MIN"
if st.sidebar.button("🏆 اقوى 10", key="b2_21"): st.session_state.page="TOP10"
if st.sidebar.button("📋 كل اليوم", key="b3_21"): st.session_state.page="ALL"
if st.sidebar.button("🔔 جرب الجرس", key="btest21"): play_bell(times=2); st.sidebar.success("Ding!")
if st.sidebar.button("🔄 مسح", key="b7_21"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_minutes_filter():
    mapping={"آخر 15 دقيقة":15, "آخر ساعة":60, "آخر 3 ساعات":180, "اليوم كامل":1440}
    if st.session_state.page=="15MIN": return 15
    if st.session_state.page=="LASTHOUR": return 60
    if st.session_state.page=="ALL": return 1440
    return mapping.get(time_filter, 60)

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+6, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    st.info(f"🔴 LIVE يفحص {start}-{end} | فلتر {mins} دقيقة")
    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=20)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        if pd.isna(ltd): minutes_ago=9999
                        else:
                            now_utc=datetime.now(timezone.utc)
                            if ltd.tzinfo is None: ltd=ltd.replace(tzinfo=timezone.utc)
                            minutes_ago=(now_utc - ltd).total_seconds()/60
                    except: minutes_ago=9999; ltd=datetime.now(timezone.utc)
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"lastTrade":ltd,"minutes_ago":minutes_ago})
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        mins=get_minutes_filter()
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
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
        if fresh and bell_on:
            biggest=max([f["premium"] for f in fresh])
            if biggest>=2000000: play_bell(times=2); st.toast(f"🔔 حوت جديد {fresh[0]['ticker']} ${biggest/1e6:.2f}M", icon="🐋")
            else: play_bell(times=1)
            st.session_state.new_whales=fresh
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    st.session_state.current_idx=end
    time.sleep(0.8)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers): st.session_state.current_idx=0

if not st.session_state.results.empty:
    mins=get_minutes_filter()
    final_raw=st.session_state.results.copy()
    final_time=final_raw[final_raw["minutes_ago"]<=mins].copy() if mins<1440 else final_raw.copy()
    if final_time.empty:
        st.warning(f"⏳ لا يوجد حيتان آخر {mins} دقيقة - اختار اليوم كامل")
        final_time=final_raw.copy()
    if smart_filter:
        smart_rows=[]
        for ticker in final_time["ticker"].unique():
            t_df=final_time[final_time["ticker"]==ticker]
            call_sum=t_df[t_df["signal"].str.contains("CALL")]["premium"].sum()
            put_sum=t_df[t_df["signal"].str.contains("PUT")]["premium"].sum()
            dominant="CALL" if call_sum>=put_sum else "PUT"
            keep=t_df[t_df["signal"].str.contains(dominant)].sort_values("premium", ascending=False).head(1)
            for _, r in keep.iterrows(): smart_rows.append(r)
        final=pd.DataFrame(smart_rows).sort_values("minutes_ago").head(30) if smart_rows else final_time.sort_values("minutes_ago").head(30)
    else:
        final=final_time.sort_values("minutes_ago").head(30)

    if st.session_state.new_whales:
        st.markdown("### 🔔 حيتان دخلت الآن")
        unique_tickers={}
        for w in st.session_state.new_whales:
            if w["ticker"] not in unique_tickers or w["premium"]>unique_tickers[w["ticker"]]["premium"]:
                unique_tickers[w["ticker"]]=w
        display_whales=list(unique_tickers.values())[:3]
        cols=st.columns(len(display_whales))
        for i, w in enumerate(display_whales):
            with cols[i]:
                ago=int(w["minutes_ago"])
                txt=f"{ago} دقيقة" if ago<60 else f"{ago//60} ساعة"
                st.markdown(f"<div class='alert-card'><b style='font-size:18px'>🔔 {w['ticker']} جديد!</b><br><div>{w['signal']} {w['strike']}</div><div style='color:#7c3aed!important;'>${w['opt_price']:.2f} | ${w['premium_M']:.2f}M</div><div>قبل {txt}</div></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء التنبيه", key="hide21"): st.session_state.new_whales=[]; st.rerun()

    st.success(f"⏰ فلتر: آخر {mins} دقيقة | {len(final)} حوت | {datetime.now().strftime('%H:%M:%S')} | خلفية بيضاء واضحة ✅")

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ متى دخل</th><th>القرار</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            ago=int(w["minutes_ago"])
            time_badge=f'<span class="time-new">🔥 الآن {ago}د</span>' if ago<=15 else f'<span class="time-new">⏰ {ago} د</span>' if ago<=60 else f'<span class="time-old">{ago//60} س</span>'
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            html+=f"<tr><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{opt}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{time_badge}</td><td><span style='background:#22c55e; color:#fff; padding:4px 10px; border-radius:12px; font-size:11px; font-weight:800;'>✅ ادخل</span></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)
else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V21 White Clear - خلفية بيضاء وكتابة واضحة")        const o1=ctx.createOscillator(); const g1=ctx.createGain(); o1.connect(g1); g1.connect(ctx.destination);
        o1.frequency.value=880; g1.gain.setValueAtTime(0.8, ctx.currentTime);
        g1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+0.8); o1.start(); o1.stop(ctx.currentTime+0.8);
    }}, i*350); }}
    if(navigator.vibrate) navigator.vibrate([200,100,200]);
    </script>""", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="LASTHOUR"
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]

st.sidebar.markdown("## 🎛️ لوحة التحكم")
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min20")
time_filter=st.sidebar.select_slider("⏰ فلتر الوقت", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf20")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد", True, key="bell20")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد لكل شركة", True, key="sm20")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد فقط لكل شركة (الأكبر)", True, key="one20")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au20")

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
if st.sidebar.button("⏰ آخر ساعة", key="b0_20"): st.session_state.page="LASTHOUR"
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b1_20"): st.session_state.page="15MIN"
if st.sidebar.button("🏆 اقوى 10", key="b2_20"): st.session_state.page="TOP10"
if st.sidebar.button("📋 كل اليوم", key="b3_20"): st.session_state.page="ALL"
if st.sidebar.button("🔔 جرب الجرس", key="btest20"): play_bell(times=2)
if st.sidebar.button("🔄 مسح", key="b7_20"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_minutes_filter():
    mapping={"آخر 15 دقيقة":15, "آخر ساعة":60, "آخر 3 ساعات":180, "اليوم كامل":1440}
    if st.session_state.page=="15MIN": return 15
    if st.session_state.page=="LASTHOUR": return 60
    if st.session_state.page=="ALL": return 1440
    return mapping.get(time_filter, 60)

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+6, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    st.info(f"🔴 LIVE يفحص {start}-{end} | فلتر {mins} دقيقة")
    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=20)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        if pd.isna(ltd): minutes_ago=9999
                        else:
                            now_utc=datetime.now(timezone.utc)
                            if ltd.tzinfo is None: ltd=ltd.replace(tzinfo=timezone.utc)
                            minutes_ago=(now_utc - ltd).total_seconds()/60
                    except: minutes_ago=9999; ltd=datetime.now(timezone.utc)
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"lastTrade":ltd,"minutes_ago":minutes_ago})
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        mins=get_minutes_filter()
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 else new_df
        # تجميع تنبيه واحد لكل شركة - الأكبر فقط
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
        if fresh and bell_on:
            biggest=max([f["premium"] for f in fresh])
            if biggest>=2000000: play_bell(times=2); st.toast(f"🔔 حوت جديد {fresh[0]['ticker']} ${biggest/1e6:.2f}M", icon="🐋")
            else: play_bell(times=1)
            st.session_state.new_whales=fresh

        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    st.session_state.current_idx=end
    time.sleep(0.8)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers): st.session_state.current_idx=0

if not st.session_state.results.empty:
    mins=get_minutes_filter()
    final_raw=st.session_state.results.copy()
    final_time=final_raw[final_raw["minutes_ago"]<=mins].copy() if mins<1440 else final_raw.copy()
    if final_time.empty:
        st.warning(f"⏳ لا يوجد حيتان آخر {mins} دقيقة - اختار اليوم كامل")
        final_time=final_raw.copy()

    if smart_filter:
        smart_rows=[]
        for ticker in final_time["ticker"].unique():
            t_df=final_time[final_time["ticker"]==ticker]
            call_sum=t_df[t_df["signal"].str.contains("CALL")]["premium"].sum()
            put_sum=t_df[t_df["signal"].str.contains("PUT")]["premium"].sum()
            dominant="CALL" if call_sum>=put_sum else "PUT"
            keep=t_df[t_df["signal"].str.contains(dominant)].sort_values("premium", ascending=False).head(1)
            for _, r in keep.iterrows(): smart_rows.append(r)
        final=pd.DataFrame(smart_rows).sort_values("minutes_ago").head(30) if smart_rows else final_time.sort_values("minutes_ago").head(30)
    else:
        final=final_time.sort_values("minutes_ago").head(30)

    if st.session_state.new_whales:
        st.markdown("### 🔔 حيتان دخلت الآن - تنبيه واحد لكل شركة")
        # عرض تنبيه واحد فقط لكل شركة
        unique_tickers={}
        for w in st.session_state.new_whales:
            if w["ticker"] not in unique_tickers or w["premium"]>unique_tickers[w["ticker"]]["premium"]:
                unique_tickers[w["ticker"]]=w
        display_whales=list(unique_tickers.values())[:3]
        cols=st.columns(len(display_whales))
        for i, w in enumerate(display_whales):
            with cols[i]:
                ago=int(w["minutes_ago"])
                txt=f"{ago} دقيقة" if ago<60 else f"{ago//60} ساعة"
                extra=f"+ عقد آخر" if len(st.session_state.new_whales)>len(unique_tickers) else ""
                st.markdown(f"<div style='background:#dcfce7; padding:12px; border-radius:12px; text-align:center; border:2px solid #22c55e;'><b>🔔 {w['ticker']} جديد!</b><br>{w['signal']} {w['strike']}<br>${w['opt_price']:.2f} | ${w['premium_M']:.2f}M<br>قبل {txt}<br><small>{extra}</small></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="hide20"): st.session_state.new_whales=[]; st.rerun()

    st.success(f"⏰ فلتر: آخر {mins} دقيقة | {len(final)} حوت | {datetime.now().strftime('%H:%M:%S')}")

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ متى دخل</th><th>القرار</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            ago=int(w["minutes_ago"])
            time_badge=f'<span class="time-new">🔥 الآن {ago}د</span>' if ago<=15 else f'<span class="time-new">⏰ {ago} د</span>' if ago<=60 else f'<span class="time-old">{ago//60} س</span>'
            is_new=any(nw["ticker"]==w["ticker"] for nw in st.session_state.new_whales)
            row_style=" style='background:#f0fdf4!important; border:2px solid #22c55e;'" if is_new else ""
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            html+=f"<tr{row_style}><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{opt}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{time_badge}</td><td><span style='background:#22c55e; color:#fff; padding:4px 8px; border-radius:12px; font-size:11px'>✅ ادخل</span></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)
    st.info("💡 **ليش كان يظهر تنبيهين IWM؟** لأن فيه حوتين بـ STRIKE مختلف. الآن فعلت **تنبيه واحد فقط لكل شركة** - يظهر أكبر حوت فقط. كل التفاصيل لسه موجودة بالجدول تحت.")
else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V20 One Alert Per Ticker")
