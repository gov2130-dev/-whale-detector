import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import urllib.parse

st.set_page_config(layout="wide", page_title="Whale Scanner ALL MARKET")
st.title("Whale V8.0 - كاشف كل السوق")
st.markdown('<meta http-equiv="refresh" content="120">', unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_sp500():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df = pd.read_html(url)[0]
        return df['Symbol'].tolist()
    except:
        # لو ويكيبيديا ما اشتغل، نستخدم أهم 100 سهم
        return ["AAPL","MSFT","NVDA","AMZN","META","GOOGL","TSLA","BRK-B","LLY","AVGO","JPM","UNH","V","XOM","MA","COST","HD","PG","JNJ","MRK","ABBV","CVX","ADBE","PEP","CRM","KO","WMT","BAC","NFLX","ORCL","AMD","TMO","ACN","CSCO","MCD","LIN","ABT","DIS","WFC","DHR","VZ","QCOM","INTC","INTU","AMGN","TXN","PFE","CAT","AMAT","IBM","GE","NOW","UNP","MS","SPG","LOW","BLK","BA","HON"]

stocks_list = get_sp500()
st.sidebar.info(f"سيتم فحص {len(stocks_list)} سهم")

min_premium = st.sidebar.slider("أقل مبلغ للحوت $", 500000, 5000000, 1000000, step=250000)
limit = st.sidebar.slider("كم حوت تبي تشوف؟", 10, 100, 30)

if st.button(f"🚀 ابدأ فحص {len(stocks_list)} سهم (يأخذ 2-3 دقايق)"):
    all_data = []
    progress = st.progress(0)
    status = st.empty()

    for i, t in enumerate(stocks_list):
        try:
            status.text(f"يفحص: {t} ({i+1}/{len(stocks_list)})")
            s = yf.Ticker(t)
            if not s.options:
                progress.progress((i+1)/len(stocks_list))
                continue
            chain = s.option_chain(s.options[0])
            for typ, df in [("CALL BUY", chain.calls), ("PUT SELL", chain.puts)]:
                if df.empty: continue
                df["premium"] = df["lastPrice"] * df["volume"] * 100
                # الشرط: المبلغ + الحجم فوق 500 عقد
                f = df[(df["premium"] >= min_premium) & (df["volume"] >= 300)].copy()
                if not f.empty:
                    f["ticker"]=t
                    f["signal"]=typ
                    all_data.append(f)
        except:
            pass
        progress.progress((i+1)/len(stocks_list))

    status.empty()
    progress.empty()

    if all_data:
        final = pd.concat(all_data).sort_values("premium", ascending=False).head(limit)

        call_sum = final[final["signal"].str.contains("CALL")]["premium"].sum()
        put_sum = final[final["signal"].str.contains("PUT")]["premium"].sum()
        is_bearish = put_sum > call_sum

        if is_bearish:
            st.error(f"🔴 السوق كله BEARISH - PUT ${put_sum/1e6:.1f}M > CALL ${call_sum/1e6:.1f}M")
        else:
            st.success(f"🟢 السوق كله BULLISH - CALL ${call_sum/1e6:.1f}M > PUT ${put_sum/1e6:.1f}M")

        def get_decision(r):
            prem, is_put = r['premium'], 'PUT' in r['signal']
            if is_bearish:
                return "✅ ادخل مع الحوت" if is_put and prem>1500000 else "✔️ ادخل" if is_put else "⚠️ عكس السوق" if prem>3000000 else "❌ لا تدخل"
            else:
                return "✅ ادخل مع الحوت" if not is_put and prem>1500000 else "✔️ ادخل" if not is_put else "❌ لا تدخل"

        final['القرار'] = final.apply(get_decision, axis=1)

        # حيتان فوق 5 مليون صفارة
        if not final[final['premium']>5000000].empty:
            st.balloons()
            st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/button-10.mp3"></audio><h2 style='color:red;text-align:center'>🚨 حوت ضخم فوق 5M! 🚨</h2>""", unsafe_allow_html=True)

        for _, w in final.head(5).iterrows():
            if w['premium']>2000000:
                msg = f"🐋 {w['ticker']} {w['signal']} ${w['premium']:,.0f} Strike {w['strike']}"
                st.warning(f"{msg} - {w['القرار']}")
                st.link_button(f"📱 واتساب {w['ticker']}", f"https://wa.me/?text={urllib.parse.quote(msg)}", key=f"wa_{w['ticker']}_{w['strike']}")

        st.dataframe(final[["ticker","signal","strike","lastPrice","volume","premium","القرار","expirationDate"] if "expirationDate" in final.columns else ["ticker","signal","strike","lastPrice","volume","premium","القرار"]], use_container_width=True)
        st.success(f"تم العثور على {len(final)} حوت منطبق عليه الشروط من أصل {len(stocks_list)} سهم")
    else:
        st.warning("ما لقي حيتان بهذا الشرط - قلل المبلغ في القائمة اليسار")
else:
    st.info("👈 اضغط الزر فوق عشان يبدأ يفحص السوق كله")
    st.caption(f"آخر تحديث: {datetime.now().strftime('%H:%M:%S')}")
