import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse
import time

st.set_page_config(layout="wide", page_title="Whale V9 PRO")
st.title("🐋 Whale V9.0 PRO - 3 قوائم ذكية")

@st.cache_data(ttl=86400)
def get_all_tickers():
    try:
        url = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nasdaq/nasdaq_tickers.txt"
        nasdaq = pd.read_csv(url, sep="\n", header=None)[0].tolist()
        url2 = "https://raw.githubusercontent.com/rreichel3/US-Stock-Symbols/main/nyse/nyse_tickers.txt"
        nyse = pd.read_csv(url2, sep="\n", header=None)[0].tolist()
        all_t = nasdaq + nyse
        all_t = [t for t in all_t if len(t)<=5 and "^" not in t and "/" not in t]
        return list(set(all_t))[:2500]
    except:
        return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","SPY","QQQ","IWM","AMD","NFLX","AVGO","SMCI","MSTR","COIN","PLTR","GME","AMC","ARM","LLY","JPM","BAC","XOM","AMZN","DIS","BA","MARA","RIOT","SOFI","NIO","AAL","UAL","DKNG"]

# قائمة الأسهم الأكثر تداولاً في الأوبشن يومياً (الأكثر تذبذباً ومشهورة)
HOT_OPTIONS = ["SPY","QQQ","IWM","TSLA","NVDA","AAPL","AMZN","META","MSFT","GOOGL","AMD","NFLX","AVGO","SMCI","COIN","MSTR","PLTR","GME","AMC","ARM","LLY","JPM","BAC","XOM","MARA","SOFI","NIO","AAL","UAL","DKNG","SPX","VIX","GLD","SLV","TLT","XLF","XLE"]

all_tickers = get_all_tickers()

if "results" not in st.session_state:
    st.session_state.results = pd.DataFrame()
if "current_idx" not in st.session_state:
    st.session_state.current_idx = 0
if "hot_results" not in st.session_state:
    st.session_state.hot_results = pd.DataFrame()

min_prem = st.sidebar.slider("Min Whale $", 500000, 5000000, 1000000, 250000)
auto = st.sidebar.checkbox("AUTO SCAN ALL MARKET", value=True)
st.sidebar.write(f"Scanned: {st.session_state.current_idx} / {len(all_tickers)}")
st.sidebar.write(f"Whales: {len(st.session_state.results)}")

# ===== القائمة الجانبية: تنبيهات واتساب مثل الصورة الأخيرة =====
st.sidebar.markdown("---")
st.sidebar.subheader("📱 تنبيهات واتساب - أقوى الحيتان")
if not st.session_state.results.empty:
    top_wa = st.session_state.results.sort_values("premium", ascending=False).head(5)
    for _, w in top_wa.iterrows():
        msg = f"WHALE {w['ticker']} {w['signal']} Strike {w['strike']} Premium ${w['premium']:,.0f} Exp {w['exp']}"
        st.sidebar.warning(f"{w['ticker']} ${w['premium']/1e6:.1f}M")
        st.sidebar.link_button(f"واتساب {w['ticker']}", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"side_wa_{w['ticker']}_{w['strike']}_{w['premium']}")

if st.sidebar.button("RESET"):
    st.session_state.results = pd.DataFrame()
    st.session_state.current_idx = 0
    st.session_state.hot_results = pd.DataFrame()
    st.rerun()

# الفحص التلقائي للسوق كله
if auto and st.session_state.current_idx < len(all_tickers):
    start = st.session_state.current_idx
    end = min(start+80, len(all_tickers))
    batch_list = all_tickers[start:end]
    st.info(f"يفحص: {start} الى {end} - باقي {len(all_tickers)-end}")
    st.progress(end/len(all_tickers))
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
        combined = pd.concat([st.session_state.results, new_df]).sort_values("premium", ascending=False).drop_duplicates(subset=["ticker","strike","exp","signal"]).head(300)
        st.session_state.results = combined
    st.session_state.current_idx = end
    time.sleep(1)
    st.rerun()

# فحص الأسهم الحارة الأكثر تذبذباً
if st.button("🔥 افحص الأسهم الأكثر تذبذباً (30 سهم مشهور)"):
    hot_data = []
    prog = st.progress(0)
    for i, t in enumerate(HOT_OPTIONS):
        try:
            s = yf.Ticker(t)
            if not s.options: continue
            chain = s.option_chain(s.options[0])
            for typ, df in [("CALL", chain.calls), ("PUT", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                df["total_volume"] = df["volume"]
                top = df.sort_values("premium", ascending=False).head(1)
                if not top.empty and top.iloc[0]["premium"]>500000:
                    top["ticker"]=t
                    top["signal"]=typ
                    top["exp"]=s.options[0]
                    hot_data.append(top)
        except:
            pass
        prog.progress((i+1)/len(HOT_OPTIONS))
    if hot_data:
        st.session_state.hot_results = pd.concat(hot_data).sort_values("premium", ascending=False)

# ===== العرض =====
if not st.session_state.results.empty:
    final = st.session_state.results.sort_values("premium", ascending=False)
    call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
    put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
    is_bearish = put_sum > call_sum

    if is_bearish:
        st.error(f"🔴 BEARISH السوق هابط - PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
    else:
        st.success(f"🟢 BULLISH السوق صاعد - CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M - {len(final)} حوت")

    final["قرار الدخول"] = final.apply(lambda r: f"✅ ادخل {r['signal']}" if (("PUT" in r["signal"]) == is_bearish) else "❌ لا تدخل REVERSE", axis=1)

    col1, col2 = st.columns([2,1])

    with col1:
        # قائمة 1: أقوى 10 شركات
        st.subheader("🏆 أقوى 10 حيتان - قرار الدخول CALL او PUT")
        top10 = final.head(10)[["ticker","signal","strike","premium","قرار الدخول","exp"]].copy()
        top10["premium"] = top10["premium"].apply(lambda x: f"${x/1e6:.2f}M")
        st.dataframe(top10, use_container_width=True)

        st.subheader(f"📋 كل الحيتان ({len(final)})")
        st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","قرار الدخول","exp"]].head(100), use_container_width=True)

    with col2:
        # قائمة 2: الأسهم الأكثر تذبذباً ومشهورة
        st.subheader("🔥 الأكثر تذبذباً في الأوبشن")
        st.caption("أسهم مشهورة متداولة باستمرار")
        if not st.session_state.hot_results.empty:
            hot = st.session_state.hot_results
            hot["قرار"] = hot.apply(lambda r: "CALL صاعد" if "CALL" in r["signal"] else "PUT هابط", axis=1)
            st.dataframe(hot[["ticker","signal","strike","premium","قرار"]].head(30), use_container_width=True)
        else:
            st.info("اضغط زر 'افحص الأسهم الأكثر تذبذباً' فوق")
            st.write("القائمة:")
            for t in HOT_OPTIONS:
                st.text(f"• {t}")

    if st.session_state.current_idx >= len(all_tickers):
        st.success("✅ خلص فحص 2500 سهم!")

st.caption(f"Last update {datetime.now().strftime('%H:%M:%S')}")
