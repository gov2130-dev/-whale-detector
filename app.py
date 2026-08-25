import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V14")

components.html("<script>setTimeout(function(){window.parent.location.reload();}, 60000);</script>", height=0)

st.markdown("""
<style>
.stApp {background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);}
h1 {color:#fff!important;}
[data-testid="stSidebar"] {background:#1a1a2e;}
.stButton>button {width:100%; color:#fff!important; border:1px solid #00f2ff55; border-radius:10px; margin:3px 0;}
</style>
""", unsafe_allow_html=True)

st.title("Whale V14 FIXED - يظهر الشركات")

def get_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","AAL","JPM","BAC","XOM","LLY","AVGO"]

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
min_prem=st.sidebar.slider("اقل حوت $", 500000, 5000000, 1000000, 250000, key="min1")
auto=st.sidebar.checkbox("فحص تلقائي", True, key="auto1")
voice_on=st.sidebar.checkbox("تكلم بصوت", True, key="voice1")
mob_on=st.sidebar.checkbox("تنبيه جوال", True, key="mob1")
st.sidebar.write(f"فحص {st.session_state.current_idx} / {len(get_tickers())}")
st.sidebar.write(f"حيتان {len(st.session_state.results)}")

st.sidebar.markdown("---")
if st.sidebar.button("🏆 اقوى 10", key="b1"): st.session_state.page="TOP10"
if st.sidebar.button("🔥 الاكثر تذبذبا", key="b2"): st.session_state.page="HOT"
if st.sidebar.button("🟢 CALL فقط", key="b3"): st.session_state.page="CALL"
if st.sidebar.button("🔴 PUT فقط", key="b4"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان", key="b5"): st.session_state.page="ALL"
if st.sidebar.button("📱 واتساب", key="b6"): st.session_state.page="WA"
if st.sidebar.button("🔊 جرب الصوت", key="b7"): speak("حوت جديد انفيديا")
if st.sidebar.button("RESET", key="b8"): st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.sent=set(); st.session_state.last_spoken=set(); st.rerun()

all_tickers=get_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+10, len(all_tickers))
    st.info(f"يفحص {start} الى {end} - يتحدث كل 60 ثانية")
    st.progress(end/len(all_tickers))
    all_data=[]
    for t in all_tickers[start:end]:
        try:
            s=yf.Ticker(t)
            if not s.options: continue
            chain=s.option_chain(s.options[0])
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"]=df["lastPrice"]*df["volume"]*100
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=50)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["exp"]=s.options[0]
                    all_data.append(f)
        except: pass
    if all_data:
        new_df=pd.concat(all_data)
        if st.session_state.results.empty:
            combined=new_df.sort_values("premium", ascending=False).head(200)
        else:
            combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        st.session_state.results=combined
        for _, w in new_df.sort_values("premium", ascending=False).head(2).iterrows():
            key=f"{w['ticker']}_{w['strike']}_{int(w['premium'])}"
            if mob_on and key not in st.session_state.sent and w['premium']>=2000000:
                send_tg(f"حوت {w['ticker']} {w['signal']} ${w['premium']/1e6:.1f}M")
                st.session_state.sent.add(key)
            if voice_on and key not in st.session_state.last_spoken and w['premium']>=3000000:
                speak(f"حوت جديد {w['ticker']} {w['signal']}")
                st.session_state.last_spoken.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers):
        st.session_state.current_idx=0

if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False)
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: f"✅ ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "❌ لا تدخل", axis=1)
    if is_bearish:
        st.error(f"🔴 BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"🟢 BULLISH CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    p=st.session_state.page
    if p=="TOP10":
        st.subheader("🏆 اقوى 10")
        st.dataframe(final.head(10)[["ticker","signal","strike","premium","قرار","exp"]], use_container_width=True)
    elif p=="HOT":
        st.subheader("🔥 الاكثر تذبذبا")
        st.dataframe(final.head(20), use_container_width=True)
    elif p=="CALL":
        st.subheader("🟢 CALL")
        st.dataframe(final[final["signal"].str.contains("CALL")].head(20), use_container_width=True)
    elif p=="PUT":
        st.subheader("🔴 PUT")
        st.dataframe(final[final["signal"].str.contains("PUT")].head(20), use_container_width=True)
    elif p=="ALL":
        st.subheader("📋 كل الحيتان")
        st.dataframe(final, use_container_width=True, height=600)
    elif p=="WA":
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M {w['قرار']}")
                c1,c2=st.columns(2)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{i}_{w['premium']}")
                if c2.button("🔊", key=f"sp_{i}_{w['premium']}"): speak(f"{w['ticker']}")
else:
    st.warning("⏳ يفحص السوق... انتظر 10 ثواني بتظهر الشركات")
    st.write("يتحدث تلقائيا كل 60 ثانية")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V14 FIXED")
