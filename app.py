import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V16 Live Price", initial_sidebar_state="expanded")
components.html("<script>setTimeout(function(){window.parent.location.reload();}, 45000);</script>", height=0)

st.markdown("""
<style>
[data-testid="stSidebar"] {min-width:360px!important; max-width:380px!important; background:#fff!important;}
[data-testid="stSidebar"] * {color:#000!important; font-size:15px!important; font-weight:700!important;}
.stButton>button {width:100%!important; height:50px!important; background:#eef3ff!important; border:2px solid #3b82f6!important; border-radius:12px!important; font-size:16px!important;}
.stApp {background:#0a0e27;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#1e293b; color:#94a3b8; padding:10px 8px; text-align:center; font-size:11px;}
.whale-table td {background:#fff; padding:12px 8px; text-align:center; font-weight:700; font-size:13px; color:#0f172a; border-top:1px solid #e2e8f0; border-bottom:1px solid #e2e8f0;}
.whale-table tr {box-shadow:0 2px 8px #0002; border-radius:10px;}
.whale-table td:first-child {border-radius:10px 0 0 10px;}
.whale-table td:last-child {border-radius:0 10px 10px 0;}
.badge-call {background:#dcfce7; color:#166534; padding:4px 8px; border-radius:12px; font-size:11px;}
.badge-put {background:#fee2e2; color:#991b1b; padding:4px 8px; border-radius:12px; font-size:11px;}
.premium {color:#1d4ed8!important; font-weight:900!important;}
.optprice {color:#7c3aed!important; font-weight:900!important; font-size:15px!important; background:#f5f3ff; padding:4px 8px; border-radius:8px;}
.decision-yes {background:linear-gradient(90deg,#22c55e,#16a34a)!important; color:#fff!important; border-radius:15px; padding:5px 10px; font-size:12px;}
.decision-no {background:#fee2e2!important; color:#991b1b!important; border-radius:15px; padding:5px 10px; font-size:12px;}
.live-dot {display:inline-block; width:10px; height:10px; background:#22c55e; border-radius:50%; animation: blink 1s infinite;}
@keyframes blink {0%{opacity:1} 50%{opacity:0.3} 100%{opacity:1}}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V16 - سعر الأوبشن لايف")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","JPM","BAC","XOM","LLY","AVGO","ARM","GLD","IWM"]

def send_tg(msg):
    try:
        token=st.secrets.get("TELEGRAM_TOKEN","")
        chat=st.secrets.get("TELEGRAM_CHAT_ID","")
        if not token or not chat: return False
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", data={"chat_id":chat,"text":msg}, timeout=5)
        return True
    except: return False
def speak(txt): components.html(f"<script>var m=new SpeechSynthesisUtterance();m.text=`{txt}`;m.lang='ar-SA';speechSynthesis.speak(m);</script>", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="TOP10"
if "sent" not in st.session_state: st.session_state.sent=set()
if "last_spoken" not in st.session_state: st.session_state.last_spoken=set()

st.sidebar.markdown("## 🎛️ لوحة التحكم")
min_prem=st.sidebar.slider("💰 اقل حوت", 500000, 5000000, 1000000, 250000, key="min16")
auto=st.sidebar.checkbox("⚡ فحص تلقائي", True, key="au16")
voice_on=st.sidebar.checkbox("🔊 تكلم بصوت", True, key="vo16")
mob_on=st.sidebar.checkbox("📲 تنبيه جوال", True, key="mo16")
st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")
st.sidebar.markdown("---")
if st.sidebar.button("🏆 اقوى 10", key="b1_16"): st.session_state.page="TOP10"
if st.sidebar.button("🟢 CALL فقط", key="b2_16"): st.session_state.page="CALL"
if st.sidebar.button("🔴 PUT فقط", key="b3_16"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان", key="b4_16"): st.session_state.page="ALL"
if st.sidebar.button("📱 واتساب", key="b5_16"): st.session_state.page="WA"
if st.sidebar.button("🔊 جرب الصوت", key="b6_16"): speak("حوت جديد")
if st.sidebar.button("🔄 مسح", key="b7_16"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.rerun()

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+8, len(all_tickers))
    st.info(f"🔴 LIVE يفحص {start} الى {end} - يتحدث كل 45 ثانية")
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
                    new_rows.append({
                        "ticker":t,
                        "signal":typ,
                        "strike":int(r["strike"]),
                        "opt_price":float(r["lastPrice"]),
                        "bid":float(r.get("bid",0)),
                        "ask":float(r.get("ask",0)),
                        "volume":int(r["volume"]),
                        "premium":r["premium"],
                        "premium_M":r["premium"]/1e6,
                        "exp":exp
                    })
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
        for _, w in new_df.sort_values("premium", ascending=False).head(2).iterrows():
            key=f"{w['ticker']}_{w['strike']}_{int(w['premium'])}"
            if mob_on and key not in st.session_state.sent and w['premium']>=2000000:
                send_tg(f"🐋 {w['ticker']} {w['signal']} سعر ${w['opt_price']} قيمة ${w['premium_M']:.2f}M"); st.session_state.sent.add(key)
            if voice_on and key not in st.session_state.last_spoken and w['premium']>=3000000:
                speak(f"حوت جديد {w['ticker']}"); st.session_state.last_spoken.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers): st.session_state.current_idx=0

if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False).copy()
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: "YES" if (("PUT" in r["signal"])==is_bearish) else "NO", axis=1)
    final["decision_text"]=final.apply(lambda r: f"✅ ادخل" if r["قرار"]=="YES" else "❌ لا تدخل", axis=1)

    now_str=datetime.now().strftime('%H:%M:%S')
    market_status="🟢 السوق مفتوح - لايف" if datetime.now().weekday()<5 else "🔴 السوق مقفل ويكند - أسعار الجمعة"
    if is_bearish: st.error(f"🔴 BEARISH PUT ${put_sum/1e6:.1f}M | {market_status} | {now_str}")
    else: st.success(f"🟢 BULLISH CALL ${call_sum/1e6:.1f}M | {market_status} | {now_str} - <span class='live-dot'></span> LIVE", )

    def build_html(df):
        html='<table class="whale-table"><tr><th>الشركة</th><th>النوع</th><th>STRIKE</th><th>سعر الأوبشن</th><th>BID/ASK</th><th>قيمة الحوت</th><th>VOL</th><th>القرار</th><th>الانتهاء</th><th>واتساب</th></tr>'
        for _, w in df.iterrows():
            badge=f'<span class="badge-call">{w["signal"]}</span>' if "CALL" in w["signal"] else f'<span class="badge-put">{w["signal"]}</span>'
            dec_class="decision-yes" if w["قرار"]=="YES" else "decision-no"
            dec=f'<span class="{dec_class}">{w["decision_text"]}</span>'
            bidask=f"{w['bid']:.2f}/{w['ask']:.2f}" if w['bid']>0 else "-"
            opt=f'<span class="optprice">${w["opt_price"]:.2f}</span>'
            msg=urllib.parse.quote(f"WHALE {w['ticker']} {w['signal']} Opt ${w['opt_price']:.2f} Total ${w['premium_M']:.2f}M Strike {w['strike']}")
            wa=f"<a href='https://wa.me/?text={msg}' target='_blank' style='background:#25D366; color:#fff; padding:5px 10px; border-radius:15px; text-decoration:none; font-size:12px;'>📱</a>"
            html+=f"<tr><td style='font-weight:900'>{w['ticker']}</td><td>{badge}</td><td>{w['strike']}</td><td>{opt}</td><td style='font-size:11px'>{bidask}</td><td class='premium'>${w['premium_M']:.2f}M</td><td>{w['volume']}</td><td>{dec}</td><td style='font-size:11px'>{w['exp']}</td><td>{wa}</td></tr>"
        html+="</table>"
        return html

    p=st.session_state.page
    if p=="TOP10": st.markdown("### 🏆 اقوى 10 - مع سعر الأوبشن لايف"); st.markdown(build_html(final.head(10)), unsafe_allow_html=True)
    elif p=="CALL": st.markdown(build_html(final[final["signal"].str.contains("CALL")].head(20)), unsafe_allow_html=True)
    elif p=="PUT": st.markdown(build_html(final[final["signal"].str.contains("PUT")].head(20)), unsafe_allow_html=True)
    else: st.markdown(build_html(final.head(40)), unsafe_allow_html=True)

    st.markdown(f"<div style='background:#1e293b; padding:12px; border-radius:10px; margin-top:15px; color:#94a3b8; font-size:12px;'>💡 <b>سعر الأوبشن:</b> هو سعر العقد الواحد الآن (مثلا $5.20) | <b>قيمة الحوت:</b> = سعر الأوبشن × الكمية × 100 | <b>LIVE:</b> يتحدث كل 45 ثانية من Yahoo Finance مباشر | السوق يفتح الإثنين 4:30 عصراً بتوقيت السعودية</div>", unsafe_allow_html=True)
else:
    st.warning("⏳ يفحص...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V16 مع سعر الأوبشن | LIVE من Yahoo Finance")
