import streamlit as st, yfinance as yf, pandas as pd, requests
from datetime import datetime
import urllib.parse, time
import streamlit.components.v1 as components

st.set_page_config(layout="wide", page_title="Whale V13.1 Fixed", page_icon="🐋")

# تحديث تلقائي كل 60 ثانية بدون مكتبة خارجية
components.html("""
<script>
setTimeout(function(){ window.parent.location.reload(); }, 60000);
</script>
""", height=0)

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@700;800&display=swap" rel="stylesheet">
<style>
html, body, [class*="css"] {font-family: 'Tajawal', sans-serif!important;}
.stApp {background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);}
h1 {color:#fff!important; font-weight:800; text-shadow: 0 2px 10px #00f2ff;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #1a1a2e, #16213e);}
.stButton>button {background:#00f2ff22; color:#fff!important; border:1px solid #00f2ff55; border-radius:12px; font-weight:700; width:100%; margin:3px 0;}
</style>
""", unsafe_allow_html=True)

st.title("🐋 Whale V13.1 - يتكلم ويتحدث - FIXED")
st.markdown("<p style='color:#00f2ff;'>🔄 يتحدث كل 60 ثانية تلقائيا + 🔊 يتكلم بصوت</p>", unsafe_allow_html=True)

@st.cache_data(ttl=86400)
def get_all_tickers():
    return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","SMCI","COIN","MSTR","PLTR","GME","MARA","SOFI","NIO","AAL","UAL","JPM","BAC","XOM","LLY","AVGO","ARM","DKNG","GLD","SLV","IWM","TLT","VIX","XLF","XLE","DIS","BA","SOFI","RIVN","LCID"]

HOT_OPTIONS=["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","COIN","MSTR","PLTR"]

def send_telegram(msg):
    try:
        token=st.secrets.get("TELEGRAM_TOKEN","")
        chat=st.secrets.get("TELEGRAM_CHAT_ID","")
        if not token or not chat: return False
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id":chat,"text":msg}, timeout=5)
        return True
    except: return False

def speak(text):
    js = f"""
    <script>
    var msg = new SpeechSynthesisUtterance();
    msg.text = `{text}`;
    msg.lang = 'ar-SA';
    msg.rate = 0.9;
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js, height=0)

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "current_idx" not in st.session_state: st.session_state.current_idx=0
if "page" not in st.session_state: st.session_state.page="TOP10"
if "sent" not in st.session_state: st.session_state.sent=set()
if "last_spoken" not in st.session_state: st.session_state.last_spoken=set()

st.sidebar.title("لوحة التحكم")
min_prem=st.sidebar.slider("اقل حوت $", 500000, 10000000, 1000000, 500000, key="min_prem_v13")
auto=st.sidebar.checkbox("فحص تلقائي", value=True, key="auto_v13")
voice_on=st.sidebar.checkbox("تكلم بصوت", value=True, key="voice_v13")
mob_on=st.sidebar.checkbox("تنبيه جوال", value=True, key="mob_v13")

st.sidebar.write(f"Scanned {st.session_state.current_idx}/{len(get_all_tickers())}")
st.sidebar.write(f"Whales {len(st.session_state.results)}")
st.sidebar.caption("يتحدث كل 60 ثانية تلقائيا")

st.sidebar.markdown("---")
st.sidebar.subheader("النوافذ اضغط")
if st.sidebar.button("🏆 اقوى 10", key="btn_top10"): st.session_state.page="TOP10"
if st.sidebar.button("🔥 الاكثر تذبذبا", key="btn_hot"): st.session_state.page="HOT"
if st.sidebar.button("🟢 CALL فقط", key="btn_call"): st.session_state.page="CALL"
if st.sidebar.button("🔴 PUT فقط", key="btn_put"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان", key="btn_all"): st.session_state.page="ALL"
if st.sidebar.button("📱 واتساب", key="btn_wa"): st.session_state.page="WA"

st.sidebar.markdown("---")
if st.sidebar.button("🔊 جرب الصوت", key="btn_test_voice"):
    speak("حوت جديد انفيديا كول باي تسعة وعشرين مليون")
    st.sidebar.success("سمعت؟")

if st.sidebar.button("RESET", key="btn_reset"):
    st.session_state.results=pd.DataFrame()
    st.session_state.current_idx=0
    st.session_state.sent=set()
    st.session_state.last_spoken=set()
    st.rerun()

# فحص
all_tickers=get_all_tickers()
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+40, len(all_tickers))
    st.info(f"يفحص {start} الى {end} من {len(all_tickers)} - يتحدث تلقائيا كل 60 ثانية")
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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=100)].copy()
                if not f.empty:
                    f["ticker"]=t; f["signal"]=typ; f["exp"]=s.options[0]; all_data.append(f)
        except: pass
    if all_data:
        new_df=pd.concat(all_data)
        if not st.session_state.results.empty:
            combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        else:
            combined=new_df.sort_values("premium", ascending=False).head(300)
        st.session_state.results=combined
        # تنبيهات
        for _, w in new_df.sort_values("premium", ascending=False).head(2).iterrows():
            key=f"{w['ticker']}_{w['strike']}_{int(w['premium'])}"
            if mob_on and key not in st.session_state.sent and w['premium']>=2000000:
                send_telegram(f"حوت {w['ticker']} {w['signal']} ${w['premium']/1e6:.1f}M")
                st.session_state.sent.add(key)
            if voice_on and key not in st.session_state.last_spoken and w['premium']>=4000000:
                speak(f"حوت جديد {w['ticker']} {w['signal']} {w['premium']/1e6:.1f} مليون")
                st.session_state.last_spoken.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()
else:
    if st.session_state.current_idx >= len(all_tickers):
        st.session_state.current_idx=0

# عرض الشركات
if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False)
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: f"✅ ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "❌ لا تدخل", axis=1)

    if is_bearish:
        st.error(f"🔴 BEARISH هابط PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M - {len(final)} حوت")
    else:
        st.success(f"🟢 BULLISH صاعد CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    page=st.session_state.page
    st.subheader(page)

    if page=="TOP10":
        top10=final.head(10)
        st.dataframe(top10[["ticker","signal","strike","premium","قرار","exp"]], use_container_width=True)
    elif page=="HOT":
        st.dataframe(final[final["ticker"].isin(HOT_OPTIONS)].head(20), use_container_width=True)
    elif page=="CALL":
        st.dataframe(final[final["signal"].str.contains("CALL")].head(20), use_container_width=True)
    elif page=="PUT":
        st.dataframe(final[final["signal"].str.contains("PUT")].head(20), use_container_width=True)
    elif page=="ALL":
        st.dataframe(final, use_container_width=True, height=700)
    elif page=="WA":
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M Strike {w['strike']}"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M - {w['قرار']}")
                c1,c2=st.columns(2)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_main_{i}_{w['ticker']}_{w['premium']}")
                if c2.button("🔊", key=f"speak_main_{i}_{w['ticker']}_{w['premium']}"):
                    speak(f"{w['ticker']} {w['signal']}")

else:
    st.warning("⏳ يفحص السوق... الشركات بتظهر بعد ثواني - الصفحة تتحدث كل 60 ثانية تلقائيا")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V13.1 FIXED")        all_t=[t for t in nasdaq+nyse if len(t)<=5 and "^" not in t and "/" not in t]
        return list(set(all_t))[:2500]
    except:
        return ["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD"]

HOT_OPTIONS=["SPY","QQQ","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","COIN","MSTR","PLTR","GME"]

def send_telegram(msg):
    try:
        token=st.secrets.get("TELEGRAM_TOKEN","")
        chat=st.secrets.get("TELEGRAM_CHAT_ID","")
        if not token or not chat: return False
        url=f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={"chat_id":chat,"text":msg, "parse_mode":"Markdown"}, timeout=5)
        return True
    except: return False

def speak(text, lang="ar-SA"):
    # يتكلم بصوت في المتصفح
    js = f"""
    <script>
    var msg = new SpeechSynthesisUtterance();
    msg.text = "{text}";
    msg.lang = "{lang}";
    msg.rate = 0.9;
    msg.volume = 1;
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js, height=0)

all_tickers=get_all_tickers()
for k, default in [("results", pd.DataFrame()), ("current_idx",0), ("page","TOP10"), ("hot_results", pd.DataFrame()), ("sent", set()), ("last_spoken", set()), ("voice_enabled", True)]:
    if k not in st.session_state:
        st.session_state[k]=default

st.sidebar.title("🎛️ لوحة التحكم")
min_prem=st.sidebar.slider("💰 أقل حوت $", 500000, 10000000, 1000000, 500000)
auto=st.sidebar.checkbox("⚡ فحص تلقائي", value=True)
enable_mob=st.sidebar.checkbox("📲 تنبيه جوال", value=True)
st.session_state.voice_enabled=st.sidebar.checkbox("🔊 تكلم بصوت", value=True)

st.sidebar.write(f"Scanned: {st.session_state.current_idx}/{len(all_tickers)} | Whales: {len(st.session_state.results) if isinstance(st.session_state.results, pd.DataFrame) else 0}")
st.sidebar.write(f"🔄 يتحدث كل 60 ثانية")

st.sidebar.markdown("---")
st.sidebar.subheader("📂 النوافذ")
if st.sidebar.button("🏆 أقوى 10"): st.session_state.page="TOP10"
if st.sidebar.button("🔥 الأكثر تذبذباً"): st.session_state.page="HOT"
if st.sidebar.button("🟢 CALL فقط"): st.session_state.page="CALL"
if st.sidebar.button("🔴 PUT فقط"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان"): st.session_state.page="ALL"
if st.sidebar.button("📱 واتساب وتليجرام"): st.session_state.page="WA"

st.sidebar.markdown("---")
if st.sidebar.button("🔊 جرب الصوت الآن"):
    speak("حوت جديد! انفيديا كول باي تسعة وعشرين مليون دولار", "ar-SA")
    st.sidebar.success("هل سمعت الصوت؟")

if st.sidebar.button("🧪 جرب تنبيه الجوال"):
    send_telegram("🐋 تجربة V13 يتكلم 🔊")
    st.sidebar.success("تم الإرسال!")

if st.sidebar.button("RESET"):
    st.session_state.results=pd.DataFrame(); st.session_state.current_idx=0; st.session_state.sent=set(); st.session_state.last_spoken=set(); st.rerun()

# فحص تلقائي
if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+80, len(all_tickers))
    st.markdown(f"<div style='background:#00f2ff22; padding:10px; border-radius:10px; color:#00f2ff; border:1px solid #00f2ff;'>⚡ يفحص {start} إلى {end} - تحديث تلقائي كل 60 ثانية</div>", unsafe_allow_html=True)
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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                if not f.empty:
                    f["ticker"]=t; f["signal"]=typ; f["exp"]=s.options[0]; all_data.append(f)
        except: pass
    if all_data:
        new_df=pd.concat(all_data)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300) if not st.session_state.results.empty else new_df
        st.session_state.results=combined
        # تنبيه جوال + صوت للحيتان الكبيرة
        for _, w in new_df.sort_values("premium", ascending=False).head(3).iterrows():
            key=f"{w['ticker']}_{w['strike']}_{int(w['premium'])}"
            # جوال
            if enable_mob and key not in st.session_state.sent and w['premium']>=3000000:
                send_telegram(f"🐋 *حوت جديد!* {w['ticker']} {w['signal']} ${w['premium']/1e6:.1f}M")
                st.session_state.sent.add(key)
            # صوت
            if st.session_state.voice_enabled and key not in st.session_state.last_spoken and w['premium']>=5000000:
                txt=f"حوت جديد! {w['ticker']} {w['signal']} بقيمة {w['premium']/1e6:.1f} مليون دولار"
                speak(txt, "ar-SA")
                st.session_state.last_spoken.add(key)
                st.toast(f"🔊 يتكلم: {w['ticker']} ${w['premium']/1e6:.1f}M")
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()
else:
    # إذا خلص الفحص يرجع من البداية تلقائيا
    if st.session_state.current_idx >= len(all_tickers):
        st.session_state.current_idx=0
        st.rerun()

# عرض
if isinstance(st.session_state.results, pd.DataFrame) and not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False)
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: f"✅ ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "❌ لا تدخل", axis=1)

    if is_bearish:
        st.markdown(f"<div style='background:linear-gradient(90deg,#ff004022,#ff000044); padding:20px; border-radius:15px; border:2px solid #ff0040; text-align:center;'><h2 style='color:#ff5577;'>🔴 BEARISH هابط - PUT ${put_sum/1e6:.1f}M</h2></div>", unsafe_allow_html=True)
        if st.session_state.voice_enabled:
            speak("السوق هابط. الحيتان تبيع. ادخل بوت فقط", "ar-SA")
    else:
        st.markdown(f"<div style='background:linear-gradient(90deg,#00ff8822,#00ff8844); padding:20px; border-radius:15px; border:2px solid #00ff88; text-align:center;'><h2 style='color:#00ff88;'>🟢 BULLISH صاعد - CALL ${call_sum/1e6:.1f}M - {len(final)} حوت</h2></div>", unsafe_allow_html=True)
        if st.session_state.voice_enabled:
            speak("السوق صاعد. الحيتان تشتري. ادخل كول فقط", "ar-SA")

    page=st.session_state.page
    if page=="TOP10":
        st.subheader("🏆 أقوى 10")
        st.dataframe(final.head(10), use_container_width=True)
    elif page=="CALL":
        st.dataframe(final[final["signal"].str.contains("CALL")].head(20), use_container_width=True)
    elif page=="PUT":
        st.dataframe(final[final["signal"].str.contains("PUT")].head(20), use_container_width=True)
    elif page=="ALL":
        st.dataframe(final, use_container_width=True, height=700)
    elif page=="WA":
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M - {w['قرار']}")
                c1,c2,c3=st.columns(3)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa13_{i}")
                if c2.button("تليجرام", key=f"tg13_{i}"):
                    send_telegram(msg)
                if c3.button("🔊 تكلم", key=f"sp13_{i}"):
                    speak(f"{w['ticker']} {w['signal']} {w['premium']/1e6:.1f} مليون", "ar-SA")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V13 يتحدث كل 60 ثانية + يتكلم بصوت")
if "current_idx" not in st.session_state:
    st.session_state.current_idx=0
if "page" not in st.session_state:
    st.session_state.page="TOP10"
if "hot_results" not in st.session_state:
    st.session_state.hot_results=pd.DataFrame()
if "sent" not in st.session_state:
    st.session_state.sent=set()

st.sidebar.title("لوحة التحكم")
min_prem=st.sidebar.slider("Min Whale $", 500000, 10000000, 2000000, 500000)
auto=st.sidebar.checkbox("AUTO SCAN ALL MARKET", value=True)
enable_mob=st.sidebar.checkbox("📲 فعل تنبيه الجوال", value=True)
st.sidebar.write(f"Scanned: {st.session_state.current_idx}/{len(all_tickers)} | Whales: {len(st.session_state.results)}")

st.sidebar.markdown("---")
st.sidebar.subheader("النوافذ")
if st.sidebar.button("🏆 اقوى 10 CALL و PUT"): st.session_state.page="TOP10"
if st.sidebar.button("🔥 الاكثر تذبذبا"): st.session_state.page="HOT"
if st.sidebar.button("🟢 اقوى CALL فقط"): st.session_state.page="CALL"
if st.sidebar.button("🔴 اقوى PUT فقط"): st.session_state.page="PUT"
if st.sidebar.button("📋 كل الحيتان"): st.session_state.page="ALL"
if st.sidebar.button("📱 تنبيهات واتساب"): st.session_state.page="WA"

st.sidebar.markdown("---")
if st.sidebar.button("🧪 جرب تنبيه الجوال الآن"):
    ok=send_telegram("🐋 *تجربة تنبيه الحيتان*\nNVDA CALL BUY $29.5M ✅\nنظام التنبيه شغال!")
    if ok:
        st.sidebar.success("تم الإرسال لجوالك!")
    else:
        st.sidebar.error("حط TOKEN و CHAT_ID في Secrets")

if st.sidebar.button("RESET"):
    st.session_state.results=pd.DataFrame()
    st.session_state.current_idx=0
    st.session_state.hot_results=pd.DataFrame()
    st.session_state.sent=set()
    st.rerun()

if auto and st.session_state.current_idx < len(all_tickers):
    start=st.session_state.current_idx
    end=min(start+80, len(all_tickers))
    st.info(f"يفحص {start} الى {end}")
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
                f=df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["exp"]=s.options[0]
                    all_data.append(f)
        except:
            pass
    if all_data:
        new_df=pd.concat(all_data)
        combined=pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        st.session_state.results=combined
        # تنبيه جوال للحيتان الجديدة الكبيرة
        if enable_mob:
            for _, w in new_df.sort_values("premium", ascending=False).head(3).iterrows():
                key=f"{w['ticker']}_{w['strike']}_{w['exp']}_{int(w['premium'])}"
                if key not in st.session_state.sent and w['premium']>=3000000:
                    msg=f"🐋 *حوت جديد!* \n*{w['ticker']}* {w['signal']}\nStrike: {w['strike']}\nPremium: ${w['premium']/1e6:.2f}M\nExp: {w['exp']}\nTime: {datetime.now().strftime('%H:%M:%S')}"
                    if send_telegram(msg):
                        st.session_state.sent.add(key)
    st.session_state.current_idx=end
    time.sleep(1)
    st.rerun()

if not st.session_state.results.empty:
    final=st.session_state.results.sort_values("premium", ascending=False)
    call_sum=final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum=final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish=put_sum>call_sum
    final["قرار"]=final.apply(lambda r: f"ادخل {r['signal']}" if (("PUT" in r["signal"])==is_bearish) else "REVERSE لا تدخل", axis=1)

    if is_bearish: st.error(f"BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else: st.success(f"BULLISH CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    page=st.session_state.page
    if page=="TOP10":
        st.subheader("🏆 اقوى 10 حيتان")
        st.dataframe(final.head(10), use_container_width=True)
    elif page=="HOT":
        st.subheader("🔥 الاكثر تذبذبا")
        st.dataframe(st.session_state.hot_results, use_container_width=True)
    elif page=="CALL":
        st.subheader("🟢 CALL فقط")
        st.dataframe(final[final["signal"].str.contains("CALL")].head(20), use_container_width=True)
    elif page=="PUT":
        st.subheader("🔴 PUT فقط")
        st.dataframe(final[final["signal"].str.contains("PUT")].head(20), use_container_width=True)
    elif page=="ALL":
        st.subheader("📋 كل الحيتان")
        st.dataframe(final, use_container_width=True, height=700)
    elif page=="WA":
        st.subheader("📱 واتساب + تليجرام")
        cols=st.columns(2)
        for i, (_, w) in enumerate(final.head(10).iterrows()):
            msg=f"WHALE {w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M Strike {w['strike']}"
            with cols[i%2]:
                st.warning(f"{w['ticker']} {w['signal']} ${w['premium']/1e6:.2f}M")
                c1,c2=st.columns(2)
                c1.link_button("واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{i}")
                if c2.button("تليجرام", key=f"tg_{i}"):
                    send_telegram(f"🐋 {msg}\nقرار: {w['قرار']}")
                    st.success("تم الإرسال!")

st.caption(f"Last {datetime.now().strftime('%H:%M:%S')} | V11 Mobile Alert - فعل التنبيه من اليسار")
