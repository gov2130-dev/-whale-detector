import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V14.1 Clean")

components.html("<script>setTimeout(function(){window.parent.location.reload();}, 60000);</script>", height=0)

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);}
h1 {color:#fff!important; font-weight:800;}
.stButton>button {width:100%; border-radius:10px; color:#fff!important; border:1px solid #00f2ff66;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V14.1 - نظيف وواضح")

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

def speak(txt):
    components.html(f"<script>var m=new SpeechSynthesisUtterance();m.text=`{txt}`;m.lang='ar-SA';speechSynthesis.speak(m);</script>", height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="TOP10"
if "sent" not in st.session_state: st.session_state.sent=set()
if "last_spoken" not in st.session_state: st.session_state.last_spoken=set()

st.sidebar.title("لوحة التحكم")
min_prem=st.sidebar.slider("اقل حوت $", 500000, 5000000, 1000000, 250000, key="m1")
auto=st.sidebar.checkbox("فحص تلقائي", True, key="a1")
voice_on=st.sidebar.checkbox("🔊 يتكلم بصوت", True, key="v1")
mob_on=st.sidebar.checkbox("📲 تنبيه جوال", True, key="mo1")
st.sidebar.write(f"فحص {st.session_state.current_idx}/{len(get_tickers())} | حيتان {len(st.session_state.results)}")

if st.sidebar.button("🏆 اقوى 10", key="t1"): st.session_state.page="TOP10"
if st.sidebar.button("🟢 CALL", key="c1"): st.session_state.page="CALL"
if st.sidebar.button("🔴 PUT", key="p1"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان", key="al1"): st.session_state.page="ALL"
if st.sidebar.button("📱 واتساب", key="w1"): st.session_state.page="WA"
if st.sidebar.button("🔊 جرب الصوت", key="vs1"): speak("حوت جديد انفيديا كول")
if st.sidebar.button("RESET", key="r1"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.rerun()

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+8, len(all_tickers))
    st.info(f"يفحص {start} الى {end} - يتحدث كل 60 ثانية - الشركات بتزيد لحالها")
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
                        "ticker": t,
                        "signal": typ,
                        "strike": r["strike"],
                        "lastPrice": r["lastPrice"],
                        "volume": r["volume"],
                        "premium": r["premium"],
                        "premium_M": f"${r['premium']/1e6:.2f}M",
                        "exp": exp
                    })
        except: pass
    if new_rows:
        new_df=pd.DataFrame(new_rows)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
        for _, w in new_df.sort_values("premium", ascending=False).head(2).iterrows():
            key=f"{w['ticker']}_{w['strike']}_{int(w['premium'])}"
            if mob_on and key not in st.session_state.sent and w['premium']>=2000000:
                send_tg(f"🐋 {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M")
                st.session_state.sent.add(key)
            if voice_on and key not in st.session_state.last_spoken and w['premium']>=3000000:
                speak(f"حوت جديد {w['ticker']}")
                st.session_state.last_spoken.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers):
        st.session_state.current_idx=0

if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False).copy()
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار الدخول"]=final.apply(lambda r: f"✅ ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "❌ لا تدخل", axis=1)
    
    if is_bearish: st.error(f"🔴 BEARISH هابط - PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M - {len(final)} حوت")
    else: st.success(f"🟢 BULLISH صاعد - CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت - ✅ ادخل CALL فقط")

    # دالة تلوين القرار
    def color_decision(val):
        if "✅" in str(val): return 'background-color: #00ff8844; color: #00ff88; font-weight: bold'
        if "❌" in str(val): return 'background-color: #ff004044; color: #ff8888; font-weight: bold'
        return ''

    p=st.session_state.page
    if p=="TOP10":
        st.subheader("🏆 اقوى 10 حيتان - مع قرار الدخول")
        show=final.head(10)[["ticker","signal","strike","premium_M","قرار الدخول","exp"]].copy()
        st.dataframe(show.style.map(color_decision, subset=["قرار الدخول"]), use_container_width=True, height=450)
    elif p=="CALL":
        show=final[final["signal"].str.contains("CALL")].head(20)[["ticker","signal","strike","premium_M","قرار الدخول","exp"]]
        st.dataframe(show.style.map(color_decision, subset=["قرار الدخول"]), use_container_width=True)
    elif p=="PUT":
        show=final[final["signal"].str.contains("PUT")].head(20)[["ticker","signal","strike","premium_M","قرار الدخول","exp"]]
        st.dataframe(show.style.map(color_decision, subset=["قرار الدخول"]), use_container_width=True)
    elif p=="ALL":
        show=final[["ticker","signal","strike","premium_M","قرار الدخول","exp","volume"]]
        st.dataframe(show.style.map(color_decision, subset=["قرار الدخول"]), use_container_width=True, height=700)
    elif p=="WA":
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(12).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} {w['premium_M']} Strike {w['strike']} {w['قرار الدخول']}"
            with cols[i%2]:
                bg="#00ff8822" if "✅" in w["قرار الدخول"] else "#ff004022"
                st.markdown(f"<div style='background:{bg}; padding:12px; border-radius:12px; margin:5px;'><b>{w['ticker']} {w['signal']} {w['premium_M']}</b><br>{w['قرار الدخول']}</div>", unsafe_allow_html=True)
                c1,c2=st.columns(2)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{i}_{w['premium']}_1")
                if c2.button("🔊", key=f"sp_{i}_{w['premium']}_1"): speak(f"{w['ticker']}")

else:
    st.warning("⏳ يفحص السوق...")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V14.1 Clean - يتحدث كل 60ث + يتكلم")
