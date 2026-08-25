import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V27 Tuesday Live", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:385px!important; max-width:405px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:13px!important;}
.stButton>button {width:100%!important; height:44px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:10px!important; font-weight:800!important; margin-bottom:6px!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 6px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:10px 4px; text-align:center; font-size:10px; font-weight:800;}
.whale-table td {background:#fff!important; padding:10px 4px; text-align:center; font-weight:700; font-size:11px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 8px; border-radius:8px; font-size:10px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 8px; border-radius:8px; font-size:10px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:5px 10px; border-radius:10px; font-weight:900; font-size:11px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:5px 10px; border-radius:10px; font-weight:900; font-size:11px;}
.score-1 {background:#ef4444!important; color:#fff!important; padding:5px 10px; border-radius:10px; font-weight:900; font-size:11px;}
.score-0 {background:#64748b!important; color:#fff!important; padding:5px 10px; border-radius:10px; font-size:10px;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V27 - الثلاثاء مباشر + كل الأزرار ✅")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

def play_bell(t=2):
    components.html(f"<script>const c=new (window.AudioContext||window.webkitAudioContext)(); for(let i=0;i<{t};i++){{setTimeout(()=>{{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;g.gain.setValueAtTime(0.8,c.currentTime);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.8);o.start();o.stop(c.currentTime+0.8);}},i*350);}}</script>", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()
if "page" not in st.session_state: st.session_state.page="ALL"

# ===== السايد بار الكامل - كل الأزرار رجعت =====
st.sidebar.markdown("## 🎛️ لوحة التحكم V27 - الثلاثاء")

refresh_interval=st.sidebar.select_slider("⏱️ فحص كل كم؟", options=["15 ثانية","30 ثانية","1 دقيقة","2 دقيقة","5 دقائق"], value="1 دقيقة", key="int27")
map_sec={"15 ثانية":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"5 دقائق":300}
interval_sec=map_sec[refresh_interval]

min_prem=st.sidebar.slider("💰 اقل حوت", 100000, 5000000, 500000, 100000, key="m27")
st.sidebar.caption("⬇️ نزلت الحد لـ 500k عشان تشوف حيتان أكثر الثلاثاء")

time_filter=st.sidebar.select_slider("⏰ فلتر الحيتان", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="اليوم كامل", key="tf27")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد (يطفي تقلب IWM)", False, key="s27")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد لكل شركة", True, key="o27")
bell_on=st.sidebar.checkbox("🔔 جرس حوت جديد", True, key="bell27")
auto=st.sidebar.checkbox("⚡ فحص تلقائي بدون وميض", True, key="a27")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 عرض الجداول")

# أزرار الجنب اللي اختفت - رجعت كلها
if st.sidebar.button("🔥 آخر 15 دقيقة", key="b15_27"):
    st.session_state.page="15MIN"; st.rerun()
if st.sidebar.button("⏰ آخر ساعة فقط", key="b60_27"):
    st.session_state.page="LASTHOUR"; st.rerun()
if st.sidebar.button("🏆 أقوى 20 شركة", key="b20_27"):
    st.session_state.page="TOP20"; st.rerun()
if st.sidebar.button("📋 كل اليوم - الثلاثاء", key="bAll_27"):
    st.session_state.page="ALL"; st.rerun()
if st.sidebar.button("🐋 أقوى 10 حيتان فقط", key="b10_27"):
    st.session_state.page="TOP10"; st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔔 جرب الجرس", key="bBell_27"):
    play_bell(2); st.sidebar.success("🔔 Ding! الجرس شغال")
if st.sidebar.button("🔄 تحديث الآن", key="bNow_27"):
    st.session_state.current_idx=0; st.rerun()
if st.sidebar.button("🗑️ مسح وابدأ من جديد", key="bClear_27"):
    st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان محفوظة {len(st.session_state.results)}")

def get_minutes_filter():
    if st.session_state.page=="15MIN": return 15
    if st.session_state.page=="LASTHOUR": return 60
    if st.session_state.page=="ALL": return 1440
    if st.session_state.page in ["TOP10","TOP20"]: return 1440
    return {"آخر 15 دقيقة":15,"آخر ساعة":60,"آخر 3 ساعات":180,"اليوم كامل":1440}.get(time_filter,1440)

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d"), exp_str
    except: return 999, exp_str, exp_str

def calc_score(row):
    score=0; reasons=[]
    days=row.get("days_left",0)
    if days<0: score-=5; reasons.append("⛔ منتهي")
    elif days==0: score+=1; reasons.append("⚠️ اليوم 0DTE")
    elif 3<=days<=7: score+=3; reasons.append("✅ 3-7 أيام")
    elif days<=14: score+=2; reasons.append("✅ أسبوعين")
    else: score+=1

    prem=row["premium_M"]
    if prem>=20: score+=3; reasons.append(f"🐋 ${prem:.0f}M ضخم")
    elif prem>=5: score+=2; reasons.append(f"🐋 ${prem:.0f}M")
    elif prem>=0.5: score+=1

    if row["volume"]>=50000: score+=2; reasons.append(f"🔥 VOL {row['volume']/1000:.0f}K")
    elif row["volume"]>=10000: score+=1

    if row["minutes_ago"]<=15: score+=2; reasons.append("🔥 الآن")
    elif row["minutes_ago"]<=60: score+=1

    if 0.3<=row["opt_price"]<=5: score+=1

    if score>=7: dec="⭐⭐⭐ قوي"; css="score-3"; action="✅ ادخل"
    elif score>=5: dec="⭐⭐ جيد"; css="score-2"; action="✅ ادخل"
    elif score>=3: dec="⭐ مراقبة"; css="score-2"; action="👀 راقب"
    else: dec="⛔ لا"; css="score-0"; action="⛔ اتركه"
    return score, dec, css, action, " | ".join(reasons)

# ===== عرض الجدول أولا - حتى لو الفحص شغال =====
def show_table():
    if st.session_state.results.empty:
        st.warning("⏳ ما فيه حيتان بعد - الفحص شغال... لو طول، نزل فلتر الحوت لـ 100k")
        return

    final_raw=st.session_state.results.copy()
    mins=get_minutes_filter()

    if st.session_state.page=="15MIN": final_time=final_raw[final_raw["minutes_ago"]<=15].copy()
    elif st.session_state.page=="LASTHOUR": final_time=final_raw[final_raw["minutes_ago"]<=60].copy()
    else: final_time=final_raw.copy() if mins>=1440 else final_raw[final_raw["minutes_ago"]<=mins].copy()

    if final_time.empty:
        st.warning(f"⏳ لا يوجد حيتان في فلتر {st.session_state.page} - أعرض كل اليوم")
        final_time=final_raw.copy()

    # احسب السكور
    enriched=[]
    for _, r in final_time.iterrows():
        sc, dec, css, action, why=calc_score(r)
        r2=r.copy(); r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["action"]=action; r2["why"]=why
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)

    if st.session_state.page=="TOP10": final=enriched_df.head(10)
    elif st.session_state.page=="TOP20": final=enriched_df.head(20)
    elif smart_filter:
        best=[]
        for ticker in enriched_df["ticker"].unique():
            t_df=enriched_df[enriched_df["ticker"]==ticker]
            best.append(t_df.sort_values("score", ascending=False).iloc[0])
        final=pd.DataFrame(best).sort_values("score", ascending=False).head(20)
    else:
        final=enriched_df.head(30)

    if st.session_state.new_whales:
        st.markdown("### 🔔 حيتان دخلت الآن - الثلاثاء")
        cols=st.columns(min(3, len(st.session_state.new_whales)))
        for i, w in enumerate(st.session_state.new_whales[:3]):
            with cols[i]:
                sc, dec, css, action, why=calc_score(w)
                ago=int(w["minutes_ago"]); txt=f"{ago}د" if ago<60 else f"{ago//60}س"
                # ثبت النوع - لا يقلب
                st.markdown(f"<div style='background:#fefce8; border:3px solid #22c55e; padding:10px; border-radius:12px; text-align:center;'><b>🔔 {w['ticker']} {w['signal']}</b><br>STRIKE {w['strike']} | 📅 {w['exp_short']} ({w['days_left']}ي)<br>${w['opt_price']:.2f} | ${w['premium_M']:.1f}M | قبل {txt}<br><span class='{css}'>{dec}</span><br><small>{w['signal']} ثابت</small></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="hide27"): st.session_state.new_whales=[]; st.rerun()

    st.success(f"✅ V27 الثلاثاء مباشر | {st.session_state.page} | {len(final)} حوت | آخر تحديث {st.session_state.last_refresh.strftime('%H:%M:%S')} | فلتر الحوت ${min_prem/1000:.0f}k")

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار</th><th>الشركة</th><th>النوع ثابت</th><th>STRIKE</th><th>📅 الانتهاء</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>VOL</th><th>⏰ دخل</th><th>ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            days=w.get("days_left",0)
            exp_html=f'<span style="background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:6px; font-size:9px;">⛔ منتهي {w["exp_short"]}</span>' if days<0 else f'<span style="background:#fee2e2; color:#991b1b; padding:3px 6px; border-radius:6px; font-size:9px;">⚠️ اليوم</span>' if days==0 else f'{w["exp_short"]} ({days}ي)'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐{w["score"]}</small>'
            ago=int(w["minutes_ago"]); time_html=f'{ago}د' if ago<60 else f'{ago//60}س'
            # وضح أن النوع ثابت
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}</td><td>{badge}<br><small style='font-size:8px'>ثابت</small></td><td>{w['strike']}</td><td>{exp_html}<br><small>{w['exp_full']}</small></td><td>${w['opt_price']:.2f}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M</td><td>{w['volume']}</td><td>{time_html}</td><td><b>{w['action']}</b><br><small style='font-size:8px'>{w['why'][:35]}</small></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)

# اعرض الجدول أولا
show_table()

# بعدين افحص في الخلفية - بدون وميض
all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+4, len(all_tickers))
    st.progress(end/len(all_tickers), text=f"🔴 يفحص {all_tickers[start:end]} - الثلاثاء مباشر")
    mins=get_minutes_filter()

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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=5)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                    except: minutes_ago=9999
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"exp_full":exp_full,"days_left":days_left,"minutes_ago":minutes_ago})
        except: pass

    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=mins] if mins<1440 and st.session_state.page not in ["TOP10","TOP20","ALL"] else new_df

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
            play_bell(2)
            st.session_state.new_whales=fresh

        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined

    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers):
        st.session_state.current_idx=0
        st.session_state.last_refresh=datetime.now()
        time.sleep(interval_sec)
        st.rerun()
    else:
        time.sleep(0.8)
        st.rerun()
else:
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0

st.caption(f"Last {st.session_state.last_refresh.strftime('%H:%M:%S')} | V27 Tuesday Live | السوق مفتوح الثلاثاء - كل الأزرار رجعت")
