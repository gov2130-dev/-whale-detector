import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V18 Bell Alert", initial_sidebar_state="expanded")
components.html("<script>setTimeout(function(){window.parent.location.reload();}, 40000);</script>", height=0)

st.markdown("""
<style>
[data-testid="stSidebar"] {min-width:360px!important; max-width:380px!important; background:#fff!important;}
[data-testid="stSidebar"] * {color:#000!important; font-weight:700!important;}
.stButton>button {width:100%!important; height:48px!important; background:#eef3ff!important; border:2px solid #3b82f6!important; border-radius:12px!important;}
.stApp {background:#0a0e27;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#1e293b; color:#94a3b8; padding:10px 8px; text-align:center; font-size:11px;}
.whale-table td {background:#fff; padding:11px 8px; text-align:center; font-weight:700; font-size:13px; color:#0f172a;}
.badge-call {background:#dcfce7; color:#166534; padding:4px 8px; border-radius:12px; font-size:11px;}
.badge-put {background:#fee2e2; color:#991b1b; padding:4px 8px; border-radius:12px; font-size:11px;}
.optprice {color:#7c3aed!important; font-weight:900!important; background:#f5f3ff; padding:4px 8px; border-radius:8px;}
.premium {color:#1d4ed8!important; font-weight:900!important;}
.decision-yes {background:linear-gradient(90deg,#22c55e,#16a34a)!important; color:#fff!important; border-radius:15px; padding:5px 10px; font-size:12px;}
.new-whale {animation: pulse 1.5s infinite; border:2px solid #22c55e!important;}
@keyframes pulse {0%{box-shadow:0 0 0 0 #22c55eaa} 70%{box-shadow:0 0 0 10px #22c55e00} 100%{box-shadow:0 0 0 0 #22c55e00}}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V18 - جرس تنبيه حوت جديد 🔔")

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
    # جرس حقيقي بصوت عالي + اهتزاز + تنبيه بصري
    bell_type = "big" if big else "normal"
    html = f"""
    <script>
    function playBell() {{
        // صوت جرس قوي
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        for(let i=0; i<{times}; i++) {{
            setTimeout(() => {{
                // نغمة جرس مزدوجة
                const osc1 = ctx.createOscillator();
                const gain1 = ctx.createGain();
                osc1.connect(gain1);
                gain1.connect(ctx.destination);
                osc1.frequency.value = {880 if big else 880};
                gain1.gain.setValueAtTime(0.8, ctx.currentTime);
                gain1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.8);
                osc1.start(ctx.currentTime);
                osc1.stop(ctx.currentTime + 0.8);
                
                const osc2 = ctx.createOscillator();
                const gain2 = ctx.createGain();
                osc2.connect(gain2);
                gain2.connect(ctx.destination);
                osc2.frequency.value = {1318 if big else 660};
                gain2.gain.setValueAtTime(0.6, ctx.currentTime + 0.1);
                gain2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 1.0);
                osc2.start(ctx.currentTime + 0.1);
                osc2.stop(ctx.currentTime + 1.0);
            }}, i*400);
        }}
        // اهتزاز الجوال
        if(navigator.vibrate) navigator.vibrate([200,100,200,100,400]);
    }}
    playBell();
    // وميض الشاشة
    document.body.style.animation = "pulse 0.5s 3";
    </script>
    <style>@keyframes pulse {{0%{{background:#0a0e27}} 50%{{background:#1e3a2a}} 100%{{background:#0a0e27}}}}</style>
    """
    components.html(html, height=0)

def play_test_bell():
    components.html("""
    <script>
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc1 = ctx.createOscillator(); const g1 = ctx.createGain();
    osc1.connect(g1); g1.connect(ctx.destination);
    osc1.frequency.value=880; g1.gain.setValueAtTime(0.8, ctx.currentTime);
    g1.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+0.8);
    osc1.start(); osc1.stop(ctx.currentTime+0.8);
    const osc2 = ctx.createOscillator(); const g2 = ctx.createGain();
    osc2.connect(g2); g2.connect(ctx.destination);
    osc2.frequency.value=1318; g2.gain.setValueAtTime(0.6, ctx.currentTime+0.1);
    g2.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime+1.0);
    osc2.start(ctx.currentTime+0.1); osc2.stop(ctx.currentTime+1.0);
    if(navigator.vibrate) navigator.vibrate([200,100,200]);
    </script>
    """, height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="SMART"
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "bell_on" not in st.session_state: st.session_state.bell_on=True
if "last_bell" not in st.session_state: st.session_state.last_bell=""

st.sidebar.markdown("## 🎛️ لوحة التحكم")
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min18")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au18")
st.sidebar.markdown("### 🔔 التنبيهات")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد (بدون كلام)", True, key="bell18")
big_whale_sound=st.sidebar.checkbox("🔔🔔 جرس مضاعف للحيتان الكبيرة >$5M", True, key="bigbell18")
mob_on=st.sidebar.checkbox("📲 تنبيه جوال", True, key="mo18")
smart_filter=st.sidebar.checkbox("🧠 فلتر ذكي", True, key="sm18")
st.session_state.bell_on=bell_on

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
if st.sidebar.button("🧠 الذكي", key="b0_18"): st.session_state.page="SMART"
if st.sidebar.button("🏆 اقوى 10", key="b1_18"): st.session_state.page="TOP10"
if st.sidebar.button("📋 كل الحيتان", key="b4_18"): st.session_state.page="ALL"

st.sidebar.markdown("---")
st.sidebar.markdown("#### جرب الأصوات")
c1,c2=st.sidebar.columns(2)
if c1.button("🔔 جرس عادي", key="test1"): play_test_bell(); st.sidebar.success("Ding!")
if c2.button("🔔🔔 جرس كبير", key="test2"): play_bell(times=3, big=True); st.sidebar.success("DING DING DING!")
if st.sidebar.button("🔄 مسح", key="b7_18"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.rerun()

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+8, len(all_tickers))
    st.progress(end/len(all_tickers))
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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=50)].copy()
                for _, r in f.iterrows():
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"bid":float(r.get("bid",0)),"ask":float(r.get("ask",0)),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp})
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        # كشف الحيتان الجديدة
        fresh=[]
        for _, w in new_df.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                fresh.append(w)
                st.session_state.sent.add(key)
        if fresh:
            st.session_state.new_whales=fresh
            # تشغيل الجرس
            if bell_on:
                biggest=max([f["premium"] for f in fresh])
                if biggest>=5000000 and big_whale_sound:
                    play_bell(times=3, big=True)
                    st.toast(f"🔔🔔🔔 حوت كبير جدا ${biggest/1e6:.2f}M!", icon="🐋")
                elif biggest>=2000000:
                    play_bell(times=2, big=False)
                    st.toast(f"🔔 حوت جديد ${biggest/1e6:.2f}M", icon="🐋")
                else:
                    play_bell(times=1)
            if mob_on:
                for w in sorted(fresh, key=lambda x: x["premium"], reverse=True)[:2]:
                    if w["premium"]>=2000000:
                        send_tg(f"🔔 حوت جديد {w['ticker']} {w['signal']} ${w['premium_M']:.2f}M سعر ${w['opt_price']:.2f}")

        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(400) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    st.session_state.current_idx=end
    time.sleep(0.5)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers): st.session_state.current_idx=0

# عرض الحيتان الجديدة كتنبيه علوي
if st.session_state.new_whales:
    st.markdown("### 🔔 حيتان جديدة دخلت الآن!")
    cols=st.columns(len(st.session_state.new_whales[:3]))
    for i, w in enumerate(st.session_state.new_whales[:3]):
        with cols[i]:
            st.markdown(f"<div class='new-whale' style='background:#dcfce7; padding:12px; border-radius:12px; text-align:center;'><b style='font-size:18px'>🔔 {w['ticker']}</b><br>{w['signal']}<br><span style='color:#7c3aed'>${w['opt_price']:.2f}</span> | <span style='color:#1d4ed8'>${w['premium_M']:.2f}M</span><br>VOL {w['volume']}</div>", unsafe_allow_html=True)
    if st.button("✖️ اخفاء التنبيه", key="hide_new"): st.session_state.new_whales=[]; st.rerun()

if not st.session_state.results.empty:
    final_raw=st.session_state.results.sort_values("premium", ascending=False).copy()
    if smart_filter or st.session_state.page=="SMART":
        smart_rows=[]
        for ticker in final_raw["ticker"].unique():
            t_df=final_raw[final_raw["ticker"]==ticker]
            call_sum=t_df[t_df["signal"].str.contains("CALL")]["premium"].sum()
            put_sum=t_df[t_df["signal"].str.contains("PUT")]["premium"].sum()
            dominant="CALL" if call_sum>=put_sum else "PUT"
            keep=t_df[t_df["signal"].str.contains(dominant)].sort_values("premium", ascending=False).head(2)
            for _, r in keep.iterrows(): smart_rows.append(r)
        final=pd.DataFrame(smart_rows).sort_values("premium", ascending=False) if smart_rows else final_raw
    else:
        final=final_raw

    now_str=datetime.now().strftime('%H:%M:%S')
    st.caption(f"🔴 LIVE | {now_str} | 🔔 الجرس شغال" if bell_on else f"🔴 LIVE | {now_str} | 🔕 الجرس مطفي")

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>سعر الأوبشن</th><th>BID/ASK</th><th>قيمة الحوت</th><th>VOL</th><th>القرار</th><th>الانتهاء</th></tr>'
        for _, w in df.iterrows():
            is_new = any(nw["ticker"]==w["ticker"] and nw["strike"]==w["strike"] for nw in st.session_state.new_whales)
            row_style = " style='background:#f0fdf4!important; border:2px solid #22c55e;'" if is_new else ""
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            dec=f'<span class="decision-yes">✅ ادخل</span>'
            new_icon=" 🔔 جديد!" if is_new else ""
            bidask=f"{w['bid']:.2f}/{w['ask']:.2f}" if w['bid']>0 else "-"
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            html+=f"<tr{row_style}><td style='font-weight:900'>{w['ticker']}{new_icon}</td><td>{badge}</td><td>{w['strike']}</td><td>{opt}</td><td style='font-size:11px'>{bidask}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{dec}</td><td style='font-size:11px'>{w['exp']}</td></tr>"
        html+="</table>"
        return html

    p=st.session_state.page
    if p in ["SMART","TOP10"]:
        st.markdown("### 🏆 اقوى الحيتان - مع تنبيه جرس")
        st.markdown(build_html(final.head(15)), unsafe_allow_html=True)
    else:
        st.markdown(build_html(final.head(40)), unsafe_allow_html=True)

    st.info("🔔 **كيف يشتغل الجرس؟** كل ما يدخل حوت جديد (> $1M) تسمع Ding! حوت كبير >$5M تسمع DING DING DING 3 مرات + اهتزاز الجوال + وميض. بدون كلام. جرب الأزرار على اليسار.")

else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V18 Bell - جرس بدون كلام")
