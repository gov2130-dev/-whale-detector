import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime, timedelta
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V19 Last Hour", initial_sidebar_state="expanded")
components.html("<script>setTimeout(function(){window.parent.location.reload();}, 35000);</script>", height=0)

st.markdown("""
<style>
[data-testid="stSidebar"] {min-width:365px!important; max-width:385px!important; background:#fff!important;}
[data-testid="stSidebar"] * {color:#000!important; font-weight:700!important; font-size:14px!important;}
.stButton>button {width:100%!important; height:48px!important; background:#eef3ff!important; border:2px solid #3b82f6!important; border-radius:12px!important;}
.stApp {background:#0a0e27;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#1e293b; color:#94a3b8; padding:9px 6px; text-align:center; font-size:10px;}
.whale-table td {background:#fff; padding:10px 6px; text-align:center; font-weight:700; font-size:12px; color:#0f172a;}
.badge-call {background:#dcfce7; color:#166534; padding:3px 6px; border-radius:10px; font-size:10px;}
.badge-put {background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:10px; font-size:10px;}
.optprice {color:#7c3aed!important; font-weight:900!important; background:#f5f3ff; padding:3px 6px; border-radius:6px;}
.premium {color:#1d4ed8!important; font-weight:900!important;}
.time-new {background:#22c55e; color:#fff; padding:3px 6px; border-radius:10px; font-size:10px; animation: blink 1s infinite;}
.time-old {background:#64748b; color:#fff; padding:3px 6px; border-radius:10px; font-size:10px;}
@keyframes blink {0%{opacity:1} 50%{opacity:0.6} 100%{opacity:1}}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V19 - حيتان آخر ساعة فقط ⏰")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

def send_tg(msg):
    try:
        token=st.secrets.get("TELEGRAM_TOKEN",""); chat=st.secrets.get("TELEGRAM_CHAT_ID","")
        if not token or not chat: return False
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id":chat,"text":msg}, timeout=5)
        return True
    except: return False

def play_bell(times=1, big=False):
    html=f"""
    <script>
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    for(let i=0;i<{times};i++){{ setTimeout(()=>{{
        const o1=ctx.createOscillator(); const g1=ctx.createGain(); o1.connect(g1); g1.connect(ctx.destination);
        o1.frequency.value={880 if not big else 880}; g1.gain.setValueAtTime(0.8, ctx.currentTime);
        g1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+0.8); o1.start(); o1.stop(ctx.currentTime+0.8);
        const o2=ctx.createOscillator(); const g2=ctx.createGain(); o2.connect(g2); g2.connect(ctx.destination);
        o2.frequency.value={1318 if big else 660}; g2.gain.setValueAtTime(0.6, ctx.currentTime+0.1);
        g2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+1.0); o2.start(ctx.currentTime+0.1); o2.stop(ctx.currentTime+1.0);
    }}, i*350); }}
    if(navigator.vibrate) navigator.vibrate([200,100,200,100,400]);
    </script>"""
    components.html(html, height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="LASTHOUR"
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]

st.sidebar.markdown("## 🎛️ لوحة التحكم")
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min19")
time_filter=st.sidebar.select_slider("⏰ فلتر الوقت", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf19")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد", True, key="bell19")
big_bell=st.sidebar.checkbox("🔔🔔 جرس مضاعف >$5M", True, key="big19")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد لكل شركة", True, key="sm19")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au19")

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
if st.sidebar.button("⏰ آخر ساعة فقط", key="b0_19"): st.session_state.page="LASTHOUR"
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b1_19"): st.session_state.page="15MIN"
if st.sidebar.button("🏆 اقوى 10 اليوم", key="b2_19"): st.session_state.page="TOP10"
if st.sidebar.button("📋 كل اليوم", key="b3_19"): st.session_state.page="ALL"
if st.sidebar.button("🔔 جرب الجرس", key="btest19"): play_bell(times=2); st.sidebar.success("Ding Ding!")
if st.sidebar.button("🔄 مسح", key="b7_19"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

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
    st.info(f"🔴 LIVE يفحص {start}-{end} | فلتر: آخر {mins} دقيقة فقط")
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
                    # وقت آخر صفقة
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        minutes_ago=(datetime.now(tz=ltd.tzinfo) - ltd).total_seconds()/60 if ltd.tzinfo else (datetime.now() - ltd).total_seconds()/60)
                    except:
                        minutes_ago=9999
                        ltd=datetime.now()
                    new_rows.append({
                        "ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),
                        "bid":float(r.get("bid",0)),"ask":float(r.get("ask",0)),"volume":int(r["volume"]),
                        "premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,
                        "lastTrade":ltd, "minutes_ago":minutes_ago
                    })
        except Exception as e:
            pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        mins=get_minutes_filter()
        # فلتر الوقت
        filtered=new_df[new_df["minutes_ago"]<=mins].copy() if mins<1440 else new_df.copy()
        # كشف الجديد
        fresh=[]
        for _, w in filtered.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}_{int(w['minutes_ago']/5)}"
            if key not in st.session_state.sent:
                fresh.append(w)
                st.session_state.sent.add(key)
        if fresh and bell_on:
            biggest=max([f["premium"] for f in fresh])
            if biggest>=5000000 and big_bell: play_bell(times=3, big=True); st.toast(f"🔔🔔🔔 حوت كبير ${biggest/1e6:.2f}M الآن!", icon="🐋")
            elif biggest>=2000000: play_bell(times=2); st.toast(f"🔔 حوت جديد ${biggest/1e6:.2f}M", icon="🐋")
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
    # فلتر الوقت للعرض
    if mins<1440:
        final_time=final_raw[final_raw["minutes_ago"]<=mins].copy()
    else:
        final_time=final_raw.copy()

    if final_time.empty:
        st.warning(f"⏳ لا يوجد حيتان في آخر {mins} دقيقة - السوق مقفل ويكند. جرب اختيار 'اليوم كامل' أو انتظر فتح السوق الإثنين 4:30م")
        final_time=final_raw.copy()

    # فلتر ذكي
    if smart_filter:
        smart_rows=[]
        for ticker in final_time["ticker"].unique():
            t_df=final_time[final_time["ticker"]==ticker]
            call_sum=t_df[t_df["signal"].str.contains("CALL")]["premium"].sum()
            put_sum=t_df[t_df["signal"].str.contains("PUT")]["premium"].sum()
            dominant="CALL" if call_sum>=put_sum else "PUT"
            keep=t_df[t_df["signal"].str.contains(dominant)].sort_values("premium", ascending=False).head(2)
            for _, r in keep.iterrows(): smart_rows.append(r)
        final=pd.DataFrame(smart_rows).sort_values("minutes_ago").head(30) if smart_rows else final_time.sort_values("minutes_ago").head(30)
    else:
        final=final_time.sort_values("minutes_ago").head(30)

    # تنبيه علوي للحيتان الجديدة
    if st.session_state.new_whales:
        st.markdown("### 🔔 حيتان دخلت الآن (آخر فحص)")
        cols=st.columns(min(3, len(st.session_state.new_whales)))
        for i, w in enumerate(st.session_state.new_whales[:3]):
            with cols[i % len(cols)]:
                ago=int(w["minutes_ago"])
                time_txt=f"{ago} دقيقة" if ago<60 else f"{ago//60} ساعة"
                st.markdown(f"<div style='background:#dcfce7; padding:10px; border-radius:12px; text-align:center; border:2px solid #22c55e;'><b>🔔 {w['ticker']} جديد!</b><br>{w['signal']}<br>${w['opt_price']:.2f} | ${w['premium_M']:.2f}M<br><span style='background:#22c55e; color:#fff; padding:2px 6px; border-radius:8px; font-size:11px'>⏰ قبل {time_txt}</span></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="hide19"): st.session_state.new_whales=[]; st.rerun()

    now_str=datetime.now().strftime('%H:%M:%S')
    if mins<60: st.success(f"⏰ فلتر: آخر {mins} دقيقة فقط | {len(final)} حوت | LIVE {now_str} | السوق {'مفتوح 🟢' if datetime.now().weekday()<5 else 'مقفل 🔴 ويكند'}")
    else: st.success(f"⏰ فلتر: آخر {mins//60} ساعة | {len(final)} حوت | LIVE {now_str}")

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ متى دخل</th><th>القرار</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            ago=int(w["minutes_ago"])
            if ago<=15: time_badge=f'<span class="time-new">🔥 الآن {ago}د</span>'
            elif ago<=60: time_badge=f'<span class="time-new">⏰ {ago} دقيقة</span>'
            elif ago<=180: time_badge=f'<span class="time-old">⏰ {ago//60} ساعة</span>'
            else: time_badge=f'<span class="time-old">{w["lastTrade"].strftime("%m-%d %H:%M") if hasattr(w["lastTrade"],"strftime") else ""}</span>'
            is_new=any(nw["ticker"]==w["ticker"] and nw["strike"]==w["strike"] for nw in st.session_state.new_whales)
            row_style=" style='background:#f0fdf4!important; border:2px solid #22c55e;'" if is_new else ""
            new_icon=" 🔔" if is_new else ""
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            html+=f"<tr{row_style}><td style='font-weight:900'>{w['ticker']}{new_icon}</td><td>{badge}</td><td>{w['strike']}</td><td>{opt}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{time_badge}</td><td><span style='background:#22c55e; color:#fff; padding:4px 8px; border-radius:12px; font-size:11px'>✅ ادخل</span></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)
    st.markdown(f"<div style='background:#1e293b; padding:12px; border-radius:10px; margin-top:12px; color:#94a3b8; font-size:11px;'>💡 <b>الفرق الآن:</b> قبل كنا نعرض كل حيتان اليوم. الآن فلتر <b>آخر ساعة</b> = يظهر فقط الحيتان اللي تداولت قبل {mins} دقيقة. عمود <b>⏰ متى دخل</b> يوضح: 🔥 الآن = دخل قبل أقل من 15 دقيقة (أقوى إشارة) | ⏰ 30 دقيقة = دخل قبل نص ساعة. بالويكند السوق مقفل فكلها قديمة.</div>", unsafe_allow_html=True)
else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V19 Last Hour Filter | الجرس بدون كلام")
