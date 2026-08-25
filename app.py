import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime, timezone
import time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V24 Smart Decision", initial_sidebar_state="expanded")

if "refresh_sec" not in st.session_state: st.session_state.refresh_sec=60
components.html(f"<script>setTimeout(function(){{window.parent.location.reload();}}, {st.session_state.refresh_sec*1000});</script>", height=0)

st.markdown("""
<style>
.stApp {background:#ffffff!important;}
h1,h2,h3 {color:#0f172a!important; font-weight:900!important;}
[data-testid="stSidebar"] {min-width:380px!important; max-width:400px!important; background:#f8fafc!important; border-right:3px solid #e2e8f0!important;}
[data-testid="stSidebar"] * {color:#0f172a!important; font-weight:700!important; font-size:13px!important;}
.stButton>button {width:100%!important; height:44px!important; background:#3b82f6!important; color:#fff!important; border:none!important; border-radius:12px!important; font-weight:800!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#0f172a!important; color:#fff!important; padding:10px 4px; text-align:center; font-size:10px; font-weight:800;}
.whale-table td {background:#fff!important; padding:10px 4px; text-align:center; font-weight:700; font-size:11px; color:#0f172a!important; border:1px solid #e2e8f0;}
.badge-call {background:#22c55e!important; color:#fff!important; padding:4px 7px; border-radius:10px; font-size:10px; font-weight:800;}
.badge-put {background:#ef4444!important; color:#fff!important; padding:4px 7px; border-radius:10px; font-size:10px; font-weight:800;}
.score-3 {background:#22c55e!important; color:#fff!important; padding:5px 10px; border-radius:12px; font-weight:900; font-size:13px;}
.score-2 {background:#f59e0b!important; color:#fff!important; padding:5px 10px; border-radius:12px; font-weight:900; font-size:13px;}
.score-1 {background:#ef4444!important; color:#fff!important; padding:5px 10px; border-radius:12px; font-weight:900; font-size:13px;}
.score-0 {background:#64748b!important; color:#fff!important; padding:5px 10px; border-radius:12px; font-weight:800; font-size:11px;}
.exp-good {background:#dcfce7!important; color:#166534!important; padding:3px 6px; border-radius:8px; font-size:10px; font-weight:800; border:1px solid #22c55e;}
.exp-bad {background:#fee2e2!important; color:#991b1b!important; padding:3px 6px; border-radius:8px; font-size:10px; font-weight:800; border:1px solid #ef4444;}
.decision-box {background:#f0fdf4; border:2px solid #22c55e; border-radius:14px; padding:14px; margin:8px 0;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V24 - محرك القرار الذكي 🧠⭐")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

def play_bell(t=1):
    components.html(f"<script>const c=new (window.AudioContext||window.webkitAudioContext)(); for(let i=0;i<{t};i++){{setTimeout(()=>{{const o=c.createOscillator(),g=c.createGain();o.connect(g);g.connect(c.destination);o.frequency.value=880;g.gain.setValueAtTime(0.8,c.currentTime);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.8);o.start();o.stop(c.currentTime+0.8);}},i*350);}}</script>", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "sent" not in st.session_state: st.session_state.sent=set()
if "new_whales" not in st.session_state: st.session_state.new_whales=[]
if "last_refresh" not in st.session_state: st.session_state.last_refresh=datetime.now()

st.sidebar.markdown("## 🎛️ تحكم")
refresh_option=st.sidebar.select_slider("⏱️ وقت التحديث", options=["15 ثانية","30 ثانية","1 دقيقة","2 دقيقة","3 دقائق","5 دقائق","10 دقائق","يدوي فقط"], value="1 دقيقة", key="r24")
map_sec={"15 ثانية":15,"30 ثانية":30,"1 دقيقة":60,"2 دقيقة":120,"3 دقائق":180,"5 دقائق":300,"10 دقائق":600,"يدوي فقط":999999}
st.session_state.refresh_sec=map_sec[refresh_option]
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="m24")
time_filter=st.sidebar.select_slider("⏰ فلتر الحيتان", options=["آخر 15 دقيقة","آخر ساعة","آخر 3 ساعات","اليوم كامل"], value="آخر ساعة", key="tf24")
bell_on=st.sidebar.checkbox("🔔 جرس", True, key="b24")
smart_filter=st.sidebar.checkbox("🧠 اتجاه واحد", True, key="s24")
one_alert=st.sidebar.checkbox("🔕 تنبيه واحد", True, key="o24")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="a24")

components.html(f"<div style='background:#0f172a; color:#fff; padding:10px; border-radius:10px; text-align:center; font-weight:900;'>⏱️ التحديث بعد <span id='t'>{st.session_state.refresh_sec}</span>ث</div><script>let s={st.session_state.refresh_sec};setInterval(()=>{{s--;document.getElementById('t').textContent=s;}},1000);</script>", height=50)

if st.sidebar.button("🔄 تحديث الآن", key="man24"): st.session_state.current_idx=0; st.rerun()
if st.sidebar.button("🔄 مسح", key="clr24"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.new_whales=[]; st.session_state.sent=set(); st.rerun()

def get_minutes_filter():
    return {"آخر 15 دقيقة":15,"آخر ساعة":60,"آخر 3 ساعات":180,"اليوم كامل":1440}.get(time_filter,60)

def parse_exp(exp_str):
    try:
        exp_date=datetime.strptime(exp_str, "%Y-%m-%d")
        days=(exp_date - datetime.now()).days
        return days, exp_date.strftime("%m/%d")
    except: return 999, exp_str

def calc_score(row):
    score=0; reasons=[]
    # 1. تاريخ الانتهاء (أهم شيء)
    days=row.get("days_left",0)
    if days<0: score-=5; reasons.append("⛔ منتهي")
    elif days==0: score+=0; reasons.append("⚠️ 0DTE خطير")
    elif days<=2: score+=1; reasons.append("⚠️ يومين فقط")
    elif 3<=days<=7: score+=3; reasons.append("✅ 3-7 أيام ممتاز")
    elif 8<=days<=21: score+=2; reasons.append("✅ أسبوعين جيد")
    else: score+=1; reasons.append("⏳ أكثر من 21 يوم")

    # 2. قيمة الحوت
    prem=row["premium_M"]
    if prem>=20: score+=3; reasons.append(f"🐋 حوت ضخم ${prem:.1f}M")
    elif prem>=5: score+=2; reasons.append(f"🐋 كبير ${prem:.1f}M")
    elif prem>=1: score+=1; reasons.append(f"💰 ${prem:.1f}M")

    # 3. وقت الدخول
    mins=row["minutes_ago"]
    if mins<=15: score+=2; reasons.append("🔥 دخل الآن")
    elif mins<=60: score+=1; reasons.append("⏰ قبل ساعة")

    # 4. VOL عالي
    if row["volume"]>=100000: score+=2; reasons.append("📈 VOL عالي جدا")
    elif row["volume"]>=30000: score+=1; reasons.append("📈 VOL عالي")

    # 5. سعر الأوبشن منطقي
    if 0.5<=row["opt_price"]<=5: score+=1; reasons.append("💵 سعر منطقي")

    # القرار
    if score>=7: decision="⭐⭐⭐ ادخل بقوة"; css="score-3"; risk="مخاطرة متوسطة"
    elif score>=5: decision="⭐⭐ ادخل"; css="score-2"; risk="مخاطرة متوسطة"
    elif score>=3: decision="⭐ مراقبة"; css="score-2"; risk="مخاطرة عالية"
    elif score>=0: decision="⚠️ لا تدخل"; css="score-1"; risk="خطير"
    else: decision="⛔ منتهي/وهمي"; css="score-0"; risk="لا تدخل"

    return score, decision, css, risk, " | ".join(reasons)

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx; end=min(start+6, len(all_tickers))
    st.progress(end/len(all_tickers))
    mins=get_minutes_filter()
    st.info(f"🔴 LIVE {start}-{end} | فلتر {mins} د | كل {refresh_option}")
    new_rows=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            exp=s.options[0]
            chain=s.option_chain(exp)
            days_left, exp_short=parse_exp(exp)
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=20)].copy()
                for _, r in f.iterrows():
                    try:
                        ltd=pd.to_datetime(r.get("lastTradeDate"))
                        minutes_ago=(datetime.now(timezone.utc) - (ltd.replace(tzinfo=timezone.utc) if ltd.tzinfo is None else ltd)).total_seconds()/60 if not pd.isna(ltd) else 9999
                    except: minutes_ago=9999; ltd=datetime.now(timezone.utc)
                    new_rows.append({"ticker":t,"signal":typ,"strike":int(r["strike"]),"opt_price":float(r["lastPrice"]),"volume":int(r["volume"]),"premium":r["premium"],"premium_M":r["premium"]/1e6,"exp":exp,"exp_short":exp_short,"days_left":days_left,"lastTrade":ltd,"minutes_ago":minutes_ago})
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        filtered=new_df[new_df["minutes_ago"]<=get_minutes_filter()] if get_minutes_filter()<1440 else new_df
        # احسب السكور
        scores=[]
        for _, r in filtered.iterrows():
            sc, dec, css, risk, why=calc_score(r)
            scores.append((sc, r))
        scores.sort(key=lambda x: x[0], reverse=True)
        fresh_to_show=pd.DataFrame([x[1] for x in scores[:3]]) if scores else pd.DataFrame()
        fresh=[]
        for _, w in fresh_to_show.iterrows():
            key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{w['signal']}"
            if key not in st.session_state.sent:
                fresh.append(w)
                st.session_state.sent.add(key)
        if fresh and bell_on: play_bell(2); st.session_state.new_whales=fresh
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(500) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
    st.session_state.current_idx=end
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0; st.session_state.last_refresh=datetime.now()
    else: time.sleep(0.5); st.rerun()
else:
    if st.session_state.current_idx>=len(all_tickers): st.session_state.current_idx=0

if not st.session_state.results.empty:
    final_raw=st.session_state.results.copy()
    final_time=final_raw[final_raw["minutes_ago"]<=get_minutes_filter()].copy() if get_minutes_filter()<1440 else final_raw.copy()
    if final_time.empty: final_time=final_raw.copy()

    # احسب السكور لكل واحد
    enriched=[]
    for _, r in final_time.iterrows():
        sc, dec, css, risk, why=calc_score(r)
        r2=r.copy()
        r2["score"]=sc; r2["decision"]=dec; r2["css"]=css; r2["risk"]=risk; r2["why"]=why
        enriched.append(r2)
    enriched_df=pd.DataFrame(enriched).sort_values("score", ascending=False)

    if smart_filter:
        # اتجاه واحد + أعلى سكور
        best=[]
        for ticker in enriched_df["ticker"].unique():
            t_df=enriched_df[enriched_df["ticker"]==ticker]
            best.append(t_df.sort_values("score", ascending=False).iloc[0])
        final=pd.DataFrame(best).sort_values("score", ascending=False).head(20)
    else:
        final=enriched_df.head(20)

    if st.session_state.new_whales:
        st.markdown("### 🔔 أفضل حوت دخل الآن - حسب القرار الذكي")
        for w in st.session_state.new_whales[:1]:
            sc, dec, css, risk, why=calc_score(w)
            st.markdown(f"<div class='decision-box'><b style='font-size:18px'>🔔 {w['ticker']} | {dec}</b><br> {w['signal']} {w['strike']} | 📅 {w['exp_short']} ({w['days_left']} يوم)<br>${w['opt_price']:.2f} | ${w['premium_M']:.2f}M | VOL {w['volume']}<br><small>{why}</small><br><b>المخاطرة: {risk}</b></div>", unsafe_allow_html=True)
        if st.button("✖️ اخفاء", key="h24"): st.session_state.new_whales=[]; st.rerun()

    st.markdown(f"<div style='background:#0f172a; color:#fff; padding:10px; border-radius:10px; text-align:center; font-weight:900;'>🧠 محرك القرار | مرتب حسب ⭐ الأفضل | تحديث كل {refresh_option}</div>", unsafe_allow_html=True)

    def build_html(df):
        html='<table class="whale-table"><tr><th>⭐ القرار</th><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>📅 الانتهاء</th><th>سعر الأوبشن</th><th>قيمة الحوت</th><th>لماذا؟</th><th>ادخل؟</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            days=w.get("days_left",0)
            exp_badge=f'<span class="exp-bad">⛔ {w["exp_short"]} منتهي</span>' if days<0 else f'<span class="exp-bad">⚠️ {w["exp_short"]} اليوم</span>' if days==0 else f'<span class="exp-good">📅 {w["exp_short"]} ({days}ي)</span>' if days<=7 else f'<span class="exp-good">{w["exp_short"]} ({days}ي)</span>'
            score_html=f'<span class="{w["css"]}">{w["decision"]}</span><br><small>⭐ {w["score"]}</small>'
            opt=f'${w["opt_price"]:.2f}'
            why_short=w["why"].split(" | ")[:2]
            why_html="<br>".join(why_short)
            action="✅ ادخل" if w["score"]>=5 else "👀 راقب" if w["score"]>=3 else "⛔ لا"
            html+=f"<tr><td>{score_html}</td><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{exp_badge}</td><td>{opt}</td><td style='color:#1d4ed8; font-weight:900'>${w['premium_M']:.1f}M</td><td style='font-size:9px; text-align:right'>{why_html}</td><td style='font-weight:900'>{action}<br><small>{w['risk']}</small></td></tr>"
        html+="</table>"
        return html

    st.markdown(build_html(final), unsafe_allow_html=True)

    st.markdown("""
    ### 🧠 كيف تتخذ القرار؟ (محرك V24)

    **السكور يحسب 5 أشياء:**

    **1. 📅 تاريخ الانتهاء (أهم شيء)**
    - `⛔ منتهي (-1 يوم)` مثل IWM عندك = سكور -5 = لا تدخل أبدا
    - `⚠️ 0DTE اليوم` = خطير جدا - ينتهي اليوم، ممكن تخسر 100% بسرعة
    - `✅ 3-7 أيام` = **أفضل وقت** = حركة قوية ووقت كافي
    - `8-21 يوم` = جيد للسوينغ

    **2. 🐋 قيمة الحوت**
    - $20M+ = حوت ضخم = ثقة عالية = +3
    - $5M+ = كبير = +2
    - $1M+ = متوسط

    **3. 🔥 متى دخل**
    - قبل 15 دقيقة = لحظي = +2
    - قبل ساعة = +1

    **4. 📈 VOL**
    - 100k+ = الكل يدخل مع الحوت = +2

    **5. 💵 سعر الأوبشن**
    - $0.5-$5 منطقي - تقدر تشتري 10-20 عقد
    - $20+ غالي جدا - لا تدخل

    **القرار النهائي:**
    - ⭐⭐⭐ (7+) = **ادخل بقوة** - كل الشروط ممتازة
    - ⭐⭐ (5-6) = **ادخل** - جيد
    - ⭐ (3-4) = **راقب فقط**
    - ⛔ (<3) = **لا تدخل** - مثل صورتك كلها PUT 0DTE منتهية

    **نصيحة لصورتك:** IWM و QQQ و SPY كلها PUT و تنتهي 08/25 (منتهية) - **لا تدخل**. انتظر السوق يفتح الإثنين وابحث عن CALL بـ 3-7 أيام و سكور ⭐⭐⭐
    """)

else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V24 Smart Decision Engine")
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
