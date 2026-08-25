import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(layout="wide")
st.title("Whale V8.2 - فحص تلقائي لكل السوق")
st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")

@st.cache_data(ttl=86400)
def get_all_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
        nasdaq = pd.read_csv(url, sep="\n", header=None)[0].tolist()
        url2 = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
        nyse = pd.read_csv(url2, sep="\n", header=None)[0].tolist()
        all_t = nasdaq + nyse
        all_t = [t for t in all_t if len(t)<=5 and '^' not in t and '/' not in t]
        return list(set(all_t))[:3000]
    except:
        return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","JPM","V","UNH","MA","HD","COST","PG","XOM","LLY","AVGO","CVX","ABBV","MRK","PEP","KO","ADBE","WMT","CRM","BAC","NFLX","ORCL","AMD","TMO","CSCO","ACN","MCD","ABT","DHR","LIN","VZ","QCOM","TXN","WFC","INTC","AMGN","CAT","UNP","MS","INTU","AMAT","IBM","GE","NOW","LOW","HON","BLK","BA","SPG","PFE","DIS"]*20

all_tickers = get_all_tickers()

if 'results' not in st.session_state:
    st.session_state.results = pd.DataFrame()
if 'current_idx' not in st.session_state:
    st.session_state.current_idx = 0

min_prem = st.sidebar.slider("أقل مبلغ حوت $", 500000, 5000000, 1000000, 250000)
batch = 100
auto = st.sidebar.checkbox("🔄 فحص تلقائي لكل السوق", value=True)
st.sidebar.write(f"فحصنا: {st.session_state.current_idx} / {len(all_tickers)}")
st.sidebar.write(f"حيتان محفوظة: {len(st.session_state.results)}")

if st.sidebar.button("🗑️ امسح وابدأ من جديد"):
    st.session_state.results = pd.DataFrame()
    st.session_state.current_idx = 0
    st.rerun()

# الفحص التلقائي
if auto and st.session_state.current_idx < len(all_tickers):
    start = st.session_state.current_idx
    end = min(start + batch, len(all_tickers))
    batch_list = all_tickers[start:end]

    st.info(f"🚀 يفحص تلقائي: {start} إلى {end} - باقي {len(all_tickers)-end}")
    prog = st.progress(start/len(all_tickers))

    all_data = []
    for t in batch_list:
        try:
            s = yf.Ticker(t)
            if not s.options: continue
            chain = s.option_chain(s.options[0])
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                f = df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    f["exp"]=s.options[0]
                    all_data.append(f)
        except:
            pass

    if all_data:
        new_df = pd.concat(all_data)
        st.session_state.results = pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(200)

    st.session_state.current_idx = end
    prog.progress(end/len(all_tickers))
    time.sleep(2)
    st.rerun()

# عرض النتائج
if not st.session_state.results.empty:
    final = st.session_state.results.sort_values("premium", ascending=False)

    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum

    if is_bearish:
        st.error(f"🔴 BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"🟢 BULLISH CALL ${call_sum/1e6:.1f}M - {len(final)} حوت")

    final['القرار'] = final.apply(lambda r: "✅ ادخل" if (('PUT' in r['signal']) == is_bearish) else "⚠️ عكس السوق" if r['premium']>3000000 else "❌ لا تدخل", axis=1)

    if not final[final['premium']>5000000].empty:
        st.balloons()
        st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-10.mp3"></audio><h3 style='color:red;text-align:center'>🚨 حوت فوق 5M! 🚨</h3>""", unsafe_allow_html=True)

    for _, w in final.head(5).iterrows():
        if w['premium']>2000000:
            msg = f"🐋 {w['ticker']} {w['signal']} {w['strike']} ${w['premium']:,.0f}"
            st.warning(f"{msg} - {w['القرار']}")
            st.link_button(f"📱 واتساب {w['ticker']}", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{w['ticker']}_{w['strike']}_{w['exp']}_{w['premium']}")

    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار","exp"]].head(100), use_container_width=True)

    if st.session_state.current_idx >= len(all_tickers):
        st.success("✅ خلص فحص كل السوق 3000 سهم!")
        st.sidebar.checkbox("🔄 فحص تلقائي", value=False)
else:
    if not auto:
        st.info("شغل 'فحص تلقائي' من اليسار عشان يبدأ")    st.session_state.results = pd.DataFrame()

col1, col2 = st.columns(2)
with col1:
    scan_btn = st.button(f"🚀 افحص من {start_idx} إلى {start_idx+batch_size}")
with col2:
    clear_btn = st.button("🗑️ امسح النتائج")

if clear_btn:
    st.session_state.results = pd.DataFrame()
    st.rerun()

if scan_btn:
    batch = all_tickers[start_idx:start_idx+batch_size]
    all_data = []
    prog = st.progress(0)
    stat = st.empty()

    for i, t in enumerate(batch):
        try:
            stat.text(f"يفحص {t} ({i+1}/{len(batch)}) - المجموع {start_idx+i}")
            s = yf.Ticker(t)
            if not s.options:
                prog.progress((i+1)/len(batch))
                continue
            # نفحص أول تاريخين فقط عشان السرعة
            for exp in s.options[:1]:
                chain = s.option_chain(exp)
                for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                    if df.empty: continue
                    df["premium"] = df["lastPrice"] * df["volume"] * 100
                    f = df[(df["premium"]>=min_prem) & (df["volume"]>=200)].copy()
                    if not f.empty:
                        f["ticker"]=t
                        f["signal"]=typ
                        f["exp"]=exp
                        all_data.append(f)
        except:
            pass
        prog.progress((i+1)/len(batch))

    stat.empty()
    prog.empty()

    if all_data:
        new_final = pd.concat(all_data).sort_values("premium", ascending=False)
        # نضيف للنتائج القديمة
        st.session_state.results = pd.concat([st.session_state.results, new_final]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(100)

# عرض النتائج التراكمية
if not st.session_state.results.empty:
    final = st.session_state.results

    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum

    if is_bearish:
        st.error(f"🔴 كل السوق BEARISH PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"🟢 كل السوق BULLISH CALL ${call_sum/1e6:.1f}M")

    def get_decision(r):
        return "✅ ادخل" if (('PUT' in r['signal']) == is_bearish) else "❌ لا تدخل" if r['premium']<2000000 else "⚠️ عكس السوق"

    final['القرار'] = final.apply(get_decision, axis=1)

    if not final[final['premium']>5000000].empty:
        st.balloons()
        st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-10.mp3"></audio>""", unsafe_allow_html=True)

    for _, w in final[final['premium']>2000000].head(5).iterrows():
        msg = f"🐋 {w['ticker']} {w['signal']} {w['strike']} ${w['premium']:,.0f}"
        st.warning(f"{msg} - {w['القرار']}")
        st.link_button(f"📱 {w['ticker']} واتساب", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{w['ticker']}_{w['strike']}_{w['exp']}")

    st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار","exp"]].head(50), use_container_width=True)
    st.caption(f"مجموع الحيتان المحفوظة: {len(final)} - آخر تحديث {datetime.now().strftime('%H:%M:%S')}")
    st.info(f"فحصت {start_idx+batch_size} من {len(all_tickers)} - اضغط فحص مرة ثانية عشان تكمل اللي بعده. غير الرقم في اليسار لـ {start_idx+batch_size}")
else:
    st.info("👈 اضغط 'افحص' عشان يبدأ يصيد من كل السوق. كل ضغطة يفحص 200 سهم ويحفظها. كررها لين تخلص 3000 سهم")
