import streamlit as st, yfinance as yf, pandas as pd
from datetime import datetime
import pytz, math, os, requests
import streamlit.components.v1 as components

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "13889370"

def send_tg(text):
    try:
        if not BOT_TOKEN: return False
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return True
    except:
        return False

# ========== وضع الفحص التلقائي للبوت ==========
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
                            msgs.append(f"💎 *{t} {int(r['strike'])}C {exp}* OI:{int(oi)} Vol:{int(vol)} ${price:.2f}")
                except: continue
        except: continue
    if msgs:
        txt = "👑 *رادار الحوت V600 - تجميع جاهز للانفجار:*\n\n" + "\n".join(msgs[:15]) + "\n\n🔗 kashf-hetan-2130.streamlit.app"
        send_tg(txt)
    else:
        send_tg("👑 رادار الحوت فحص 3 مرات يوميا - لا يوجد تجميع قوي الآن (ويكند) - kashf-hetan-2130.streamlit.app")
    os._exit(0)

# ========== V600 UI ==========
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
    except:
        return 0,0,0,0

st.set_page_config(layout="wide", page_title="Whale V600 Radar", initial_sidebar_state="expanded")

st.markdown("""
<style>
[data-testid="stSidebar"] {min-width:360px!important;}
.stButton>button {width:100%!important; height:50px!important; background:#eef3ff!important; border:2px solid #3b82f6!important; border-radius:12px!important; font-weight:800!important;}
.whale-table {width:100%; border-collapse:separate; border-spacing:0 8px;}
.whale-table th {background:#1e293b; color:#94a3b8; padding:8px; text-align:center; font-size:11px;}
.whale-table td {background:#fff; padding:10px 6px; text-align:center; font-weight:700; font-size:12px; color:#0f172a; border-radius:6px;}
.badge-o {background:#fef3c7; color:#92400e; padding:3px 8px; border-radius:10px; font-size:11px;}
.badge-bw {background:#dcfce7; color:#166534; padding:3px 8px; border-radius:10px; font-size:11px;}
</style>
""", unsafe_allow_html=True)

st.title("👑 حوت 54 - V600 رادار التجميع قبل الانفجار")
st.caption("يشتغل قبل واثناء وبعد السوق - OI > Vol + BW ضيق = 💎")

def get_tickers():
    return ["NVDA","TSLA","AAPL","SPY","QQQ","AMD","META","MSFT","PLTR","COIN","MSTR","GOOGL","AMZN","NFLX","AVGO"]

if "results" not in st.session_state: st.session_state.results=pd.DataFrame()
if "idx" not in st.session_state: st.session_state.idx=0

min_oi = st.sidebar.slider("💎 اقل OI", 1000, 50000, 5000, 1000)
min_vol = st.sidebar.slider("📊 اقل Vol", 20, 1000, 80, 20)
auto = st.sidebar.checkbox("⚡ فحص تلقائي", True)

if st.sidebar.button("🚀 فحص الآن"):
    st.session_state.idx=0
    st.session_state.results=pd.DataFrame()
    st.rerun()

if st.sidebar.button("📤 ارسال التجميع لتلجرام"):
    if not st.session_state.results.empty:
        txt = "👑 *V600 - من التطبيق:*\n\n"
        for _,r in st.session_state.results.head(10).iterrows():
            txt+=f"💎 {r['ticker']} {r['strike']}C OI:{r['OI']} Vol:{r['Vol']}\n"
        send_tg(txt)
        st.sidebar.success("ارسل ✅")
    else:
        st.sidebar.warning("لا يوجد نتائج")

all_t = get_tickers()
if auto and st.session_state.idx < len(all_t):
    batch = all_t[st.session_state.idx:st.session_state.idx+4]
    st.info(f"🔴 LIVE يفحص {batch} | {st.session_state.idx}/{len(all_t)}")
    rows=[]
    for t in batch:
        try:
            tk=yf.Ticker(t)
            price=tk.history(period="1d")['Close'].iloc[-1] if not tk.history(period="1d").empty else 100
            if not tk.options: continue
            for exp in tk.options[:2]:
                ch=tk.option_chain(exp)
                for _,r in ch.calls.iterrows():
                    oi=r.get('openInterest',0)
                    vol=r.get('volume',0)
                    if oi>=min_oi and vol>=min_vol and oi>vol*1.2:
                        iv=r.get('impliedVolatility',0.5)
                        T=0.1
                        d,g,th,v = calc_greeks(price, r['strike'], T, iv, "call")
                        bw = abs(r['strike']-price)/price
                        if bw<0.08:
                            rows.append({"ticker":t,"strike":int(r['strike']),"exp":exp,"OI":int(oi),"Vol":int(vol),"price":float(r['lastPrice']),"S":round(price,1),"BW":round(bw*100,1),"delta":d,"OI/Vol":round(oi/max(vol,1),1)})
        except: pass
    if rows:
        df=pd.DataFrame(rows)
        st.session_state.results = pd.concat([st.session_state.results, df]).sort_values("OI", ascending=False).drop_duplicates(subset=["ticker","strike","exp"]).head(100)
    st.session_state.idx+=4
    st.rerun()

if not st.session_state.results.empty:
    df=st.session_state.results.copy()
    df["حالة"] = df.apply(lambda x: "💎 تجميع جاهز للانفجار" if x['OI/Vol']>1.5 and x['BW']<5 else "👀 مراقبة", axis=1)
    st.success(f"✅ {len(df)} عقد تجميع | {datetime.now(pytz.timezone('Asia/Riyadh')).strftime('%H:%M:%S')}")
    st.dataframe(df, use_container_width=True)
    # ارسال تلقائي اذا فيه جواهر
    gems = df[df["حالة"].str.contains("💎")]
    if not gems.empty and st.sidebar.checkbox("🔔 ارسال تلقائي للجواهر", True):
        if "sent_today" not in st.session_state:
            txt = "💎 *جواهر V600:*\n\n"
            for _,r in gems.head(5).iterrows():
                txt+=f"{r['ticker']} {r['strike']}C OI:{r['OI']} Vol:{r['Vol']} BW:{r['BW']}%\n"
            send_tg(txt)
            st.session_state.sent_today=True
else:
    st.warning("⏳ اضغط فحص الآن - السوق ويكند النتائج تقل")

st.caption("V600 - رادار قبل واثناء وبعد السوق | BOT مربوط بتلجرام 13889370")
