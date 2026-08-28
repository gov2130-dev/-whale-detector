import streamlit as st
import yfinance as yf
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="حوت 54", layout="wide")

# --- الاعدادات ---
BOT_TOKEN = st.secrets["BOT_TOKEN"] if "BOT_TOKEN" in st.secrets else ""
CHAT_ID = "13889370"

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","AMD","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP"]

st.title("👑 فحص البري ماركت V99")

def send_tg(text):
    if not BOT_TOKEN:
        st.error("ما فيه BOT_TOKEN في Secrets")
        return
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text})
        if r.status_code == 200:
            st.success("تم الارسال ✅")
        else:
            st.error(f"خطأ تلجرام: {r.text}")
    except Exception as e:
        st.error(str(e))

def get_data(sym):
    try:
        tk = yf.Ticker(sym)
        hist = tk.history(period="2d", interval="1m")
        if len(hist) < 2: return None
        curr = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-100])
        pre_pct = ((curr - prev) / prev) * 100

        # جلب العقود
        exps = tk.options[:2]
        best = None
        for exp in exps:
            try:
                chain = tk.option_chain(exp)
                # نحاول نلقى PUT او CALL حسب الحركة
                df = chain.puts if pre_pct < -2 else chain.calls
                # فلترة عقود قريبة
                df = df[(df['bid']>0.5) & (df['bid']<5) & (df['volume']>100)]
                if not df.empty:
                    row = df.iloc[0]
                    best = (exp, row, pre_pct, curr)
                    break
            except:
                continue
        return best
    except:
        return None

# --- واجهة ---
if st.button("🔍 افحص 54 الان", type="primary"):
    results = []
    progress = st.progress(0)
    for i, sym in enumerate(STOCKS_54):
        progress.progress((i+1)/len(STOCKS_54))
        data = get_data(sym)
        if data:
            exp, row, pre_pct, curr = data
            # صياغة الرسالة بنفس ستايلك
            side = "PUT" if pre_pct < 0 else "CALL"
            emoji = "🔴" if side=="PUT" else "🟢"
            exp_dt = datetime.strptime(exp, "%Y-%m-%d")
            days = (exp_dt - datetime.now()).days

            msg = f"""{emoji} {sym} {int(row['strike'])} {side} PRE - {side} {pre_pct:.1f}%
Exp: {exp} ({days}d) Stock: ${curr:.2f}
Entry: ${row['lastPrice']:.2f} Bid: ${row['bid']:.2f} Vol: {int(row['volume'])} OI: {int(row['openInterest'])}
Stop: ${row['bid']*0.55:.2f}
Target Stock: {curr*0.99:.1f} > {curr*0.98:.1f} > {curr*0.97:.1f}
Target Contract: ${row['bid']*1.5:.2f} (+50%) | ${row['bid']*2.3:.2f} (+130%) | ${row['bid']*3.2:.2f} (+220%)"""
            results.append((abs(pre_pct), msg))
            st.code(msg)

    # ترتيب من الاقوى
    results.sort(reverse=True)
    if st.button("📤 ارسل الاقوى لتلجرام"):
        for _, m in results[:5]:
            send_tg(m)

st.divider()
st.header("📈 فحص هل تحقق الهدف؟")
sym_check = st.text_input("الرمز", "NVDL")
if st.button("افحص السعر"):
    try:
        p = yf.Ticker(sym_check.upper()).history(period="1d", interval="1m")['Close'].iloc[-1]
        st.metric(f"{sym_check.upper()} الان", f"${float(p):.2f}")
        st.info("قارن هذا السعر باهداف الرسالة - اذا وصل لاول هدف = +50% تحقق ✅")
    except:
        st.error("ما قدرت اجيب السعر")
