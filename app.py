import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime, timezone
import time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V23 EXP Date", initial_sidebar_state="expanded")

if "refresh_sec" not in st.session_state: st.session_state.refresh_sec=60
components.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {st.session_state.refresh_sec*1000});</script>", height=0)

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
[data-testid="stHeader"] {background:#ffffff!important;}
h1, h2, h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:380px!important; max-width:400px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:13px!important;}
.stButton>button {width:100%!important; height:44px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:12px!important; font-weight:800!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#0f172a!important; color:#ffffff!important; padding:10px 5px; text-align:center; font-size:11px; font-weight:800;}
.whale-table td {background:#ffffff!important; padding:10px 5px; text-align:center; font-weight:700; font-size:12px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-size:10px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 8px; border-radius:10px; font-size:10px; font-weight:800;}
.optprice {color:#7c3aed!important; font-weight:900!important; background:#f5f3ff!important; padding:4px 6px; border-radius:6px;}
.premium {color:#1d4ed8!important; font-weight:900!important;}
.time-new {background:#22c55e!important; color:#fff!important; padding:3px 6px; border-radius:8px; font-size:10px; font-weight:800;}
.time-old {background:#64748b!important; color:#fff!important; padding:3px 6px; border-radius:8px; font-size:10px;}
.exp-badge {background:#f59e0b!important; color:#fff!important; padding:4px 8px; border-radius:8px; font-size:11px; font-weight:800;}
.exp-urgent {background:#ef4444!important; color:#fff!important; padding:4px 8px; border-radius:8px; font-size:11px; font-weight:800; animation: blink 1s infinite;}
@keyframes blink {50%{opacity:0.7}}
.alert-card {background:#fefce8!important; border:3px solid #22c55e!important; padding:12px!important; border-radius:14px!important; text-align:center!important;}
.alert-card * {color:#0f172a!important; font-weight:800!important;}
.countdown {background:#0f172a!important; color:#fff!important; padding:10px; border-radius:10px; text-align:center; font-weight:900; font-size:14px;}
.countdown * {color:#fff!important;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V23 - مع تاريخ انتهاء السترايك 📅")

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
    </script>""", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="LASTHOUR"
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()

st.sidebar.markdown("## 🎛️ لوحة التحكم")
st.sidebar.markdown("### ⏱️ وقت التحديث")
refresh_option=st.sidebar.select_slider("اختر كل كم يحدث؟", options=["15 ثانية","30 ثانية","1 دقيقة","2 دقيقة","3 دقائق","5 دقائق","10 دقائق","يدوي فقط"], value="1 دقيقة", key="refresh23")
map_sec={"15 ثانية":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"3 دقائق":180,"5 دقائق":300,"10 دقائق":600,"يدوي فقط":999999}
st.session_state.refresh_sec=map_sec[refresh_option]
if refresh_option=="يدوي فقط": st.sidebar.warning("⏸️ يدوي - اضغط تحديث الآن")
else: st.sidebar.success(f"⏱️ يحدث كل {refresh_option}")

min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min23")
time_filter=st.sidebar.select_slider("⏰ فلتر الحيتان", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf23")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد", True, key="bell23")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد لكل شركة", True, key="sm23")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد لكل شركة", True, key="one23")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au23")

components.html(f"""
<div id="countdown" style="background:#0f172a; color:#fff; padding:10px; border-radius:10px; text-align:center; font-weight:900; font-size:16px; font-family:monospace;">
⏱️ التحديث بعد <span id="timer">{st.session_state.refresh_sec}</span> ث
</div>
<script>
let sec={st.session_state.refresh_sec};
let el=document.getElementById('timer');
let interval=setInterval(()=>{{ sec--; if(el) el.textContent=sec; if(sec<=0) clearInterval(interval); }},1000);
</script>
""", height=50)

if st.sidebar.button("🔄 تحديث الآن يدويا", key="manual23"):
    st.session_state.current_idx=0
    st.session_state.last_refresh=datetime.now()
    st.rerun()

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
if st.sidebar.button("⏰ آخر ساعة", key="b0_23"): st.session_state.page="LASTHOUR"
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b1_23"): st.session_state.page="15MIN"
if st.sidebar.button("📋 كل اليوم", key="b3_23"): st.session_state.page="ALL"
if st.sidebar.button("🔔 جرب الجرس", key="btest23"): play_bell(times=2)
if st.sidebar.button("🔄 مسح", key="b7_23"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_minutes_filter():
    mapping={"آخر 15 دقيقة":15, "آخر ساعة":60, "آخر 3 ساعات":180, "اليوم كامل":1440}
    if st.session_state.page=="15MIN": return 15
    if st.session_state.page=="LASTHOUR": return 60
    if st.session_state.page=="ALL": return 1440
    return mapping.get(time_filter, 60)

def parse_exp_days(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        today=datetime.now()
        days=(exp_date - today).days
        return days, exp_date.strftime("%m/%d")
    except:
        return 999, exp_str

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+6, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    st.info(f"🔴 LIVE يفحص {start}-{end} | فلتر {mins} د | تحديث كل {refresh_option}")
    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            days_left, exp_short=parse_exp_days(exp)
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
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"days_left":days_left,"lastTrade":ltd,"minutes_ago":minutes_ago})
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
            play_bell(times=2)
            st.toast(f"🔔 حوت جديد {fresh[0]['ticker']} {fresh[0]['exp_short']}", icon="🐋")
            st.session_state.new_whales=fresh
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers):
        st.session_state.current_idx=0
        st.session_state.last_refresh=datetime.now()
    else:
        time.sleep(0.5)
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
                txt=f"{ago}د" if ago<60 else f"{ago//60}س"
                st.markdown(f"<div class='alert-card'><b>🔔 {w['ticker']} جديد!</b><br>{w['signal']} {w['strike']}<br><span style='background:#f59e0b; color:#fff; padding:2px 6px; border-radius:6px;'>📅 {w['exp_short']} ({w['days_left']} يوم)</span><br>${w['opt_price']:.2f} | ${w['premium_M']:.2f}M<br>قبل {txt}</div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="hide23"): st.session_state.new_whales=[]; st.rerun()

    st.markdown(f"<div class='countdown'>⏱️ تحديث كل {refresh_option} | آخر {st.session_state.last_refresh.strftime('%H:%M:%S')} | فلتر {mins} د</div>", unsafe_allow_html=True)

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>📅 تاريخ الانتهاء</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ متى دخل</th><th>القرار</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            ago=int(w["minutes_ago"])
            time_badge=f'<span class="time-new">🔥 {ago}د</span>' if ago<=15 else f'<span class="time-new">⏰ {ago}د</span>' if ago<=60 else f'<span class="time-old">{ago//60}س</span>'
            days=w.get("days_left",999)
            exp_s=w.get("exp_short", w.get("exp",""))
            exp_full=w.get("exp","")
            if days<=1: exp_badge=f'<span class="exp-urgent">📅 {exp_s} اليوم!</span>'
            elif days<=3: exp_badge=f'<span class="exp-urgent">📅 {exp_s} ({days}يوم)</span>'
            else: exp_badge=f'<span class="exp-badge">📅 {exp_s} ({days}يوم)</span>'
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            html+=f"<tr><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{exp_badge}<br><small style='color:#64748b'>{exp_full}</small></td><td>{opt}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{time_badge}</td><td><span style='background:#22c55e; color:#fff; padding:4px 10px; border-radius:10px; font-size:11px; font-weight:800;'>✅ ادخل</span></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)
    st.success("✅ **تمت إضافة تاريخ الانتهاء:** عمود 📅 يوضح التاريخ (مثل 08/26 = 26 أغسطس) وكم يوم باقي. اللون الأحمر = ينتهي اليوم أو بكرة (خطير - لا تدخل). الأصفر = ينتهي خلال أيام (مضاربة سريعة).")
else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V23 مع تاريخ السترايك EXP")
