import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime
import pytz, math, os, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "13889370"

def send_tg(text):
    try:
        if not BOT_TOKEN: return False
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return True
    except: return False

if "--scan" in os.sys.argv:
    tickers = ["NVDA","TSLA","AAPL","SPY","QQQ","AMD","META","MSFT","PLTR","COIN","MSTR","GOOGL"]
    msgs = []
    for t in tickers:
        try:
            tk = yf.Ticker(t)
            if not tk.options: continue
            for exp in tk.options[:2]:
                try:
                    chain = tk.option_chain(exp)
                    df = chain.calls
                    if df.empty: continue
                    for _, r in df.iterrows():
                        oi = r.get('openInterest',0)
                        vol = r.get('volume',0)
                        price = r.get('lastPrice',0)
                        if oi>0 and vol>0 and oi > vol*1.5 and vol>80 and price>0.3 and price<20:
                            msgs.append(f"💎 {t} {int(r['strike'])}C {exp} OI:{int(oi)} Vol:{int(vol)} ${price:.2f}")
                except: continue
        except: continue
    if msgs:
        txt = "👑 رادار الحوت V600 - تجميع:\n\n" + "\n".join(msgs[:15]) + "\n\nkashf-hetan-2130.streamlit.app"
        send_tg(txt)
    else:
        send_tg("👑 رادار الحوت فحص - لا يوجد تجميع قوي الآن (ويكند)")
    os._exit(0)

def norm_cdf(x): return 0.5 * (1 + math.erf(x / math.sqrt(2)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)
def calc_greeks(S,K,T,iv,side):
    try:
        if T<=0 or iv<=0: return 0,0,0,0
        d1=(math.log(S/K)+(0.05+0.5*iv*iv)*T)/(iv*math.sqrt(T))
        d2=d1-iv*math.sqrt(T)
        delta = norm_cdf(d1) if side=="call" else norm_cdf(d1)-1
        gamma = norm_pdf(d1)/(S*iv*math.sqrt(T))
        theta = -(S*iv*norm_pdf(d1))/(2*math.sqrt(T))
        vega = S*math.sqrt(T)*norm_pdf(d1)/100
        return round(delta,2), round(gamma,3), round(theta,2), round(vega,2)
    except: return 0,0,0,0

st.set_page_config(layout="wide", page_title="Whale V600 Radar")
st.title("👑 حوت 54 - V600 رادار التجميع")
st.caption("يشتغل قبل واثناء وبعد السوق - OI > Vol + BW ضيق = 💎")

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "idx" not in st.session_state: st.session_state.idx=0

min_oi = st.sidebar.slider("💎 اقل OI", 1000, 50000, 5000, 1000)
min_vol = st.sidebar.slider("📊 اقل Vol", 20, 1000, 80, 20)
auto = st.sidebar.checkbox("⚡ فحص تلقائي", True)

if st.sidebar.button("🚀 فحص الآن"):
    st.session_state.idx=0
    st.session_state.results=pd.DataFrame()
    st.rerun()

if not st.session_state.results.empty:
    st.dataframe(st.session_state.results, use_container_width=True)
