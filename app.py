import streamlit as st
import yfinance as yf
import requests
from datetime import datetime, timedelta
import pytz

st.set_page_config(page_title="حوت 54", layout="wide")
st.title("👑 بوت الحوت 54")

# --- 1. خانة التلجرام دائما موجودة فوق ---
st.sidebar.header("📤 اعدادات التلجرام")
BOT_TOKEN = st.sidebar.text_input("BOT TOKEN", value=st.secrets.get("BOT_TOKEN",""), type="password")
CHAT_ID = st.sidebar.text_input("CHAT ID", value="13889370")

# تاريخ الفحص - تتحكم فيه انت عشان ما يجيب تواريخ قديمة
eastern = pytz.timezone('US/Eastern')
today_et = datetime.now(eastern).date()
st.sidebar.date_input("📅 تاريخ الفحص (مفتوح)", value=today_et, key="check_date")
SELECTED_DATE = st.session_state.check_date
SELECTED_STR = SELECTED_DATE.strftime("%Y-%m-%d")

st.sidebar.info(f"بيجيب عقود من تاريخ {SELECTED_STR} وطالع (مفتوح)")

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP"]

def send_tg(text):
    if not BOT_TOKEN:
        st.error("حط توكن البوت في الشريط الجانبي!")
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": text}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(str(e))
        return False

def get_best(sym):
    try:
        tk = yf.Ticker(sym)
        hist = tk.history(period="2d", interval="5m")
        if hist.empty: return None
        curr = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-20]) if len(hist)>20 else float(hist['Close'].iloc[0])
        pre = ((curr-prev)/prev)*100

        # --- حل مشكلة التواريخ القديمة: مفتوح من تاريخك وطالع ---
        valid = []
        for e in tk.options:
            try:
                if e >= SELECTED_STR: # نصيا يقارن YYYY-MM-DD ويضمن مفتوح
                    valid.append(e)
            except: continue

        if not valid: return None
        exps = valid[:5] # اول 5 تواريخ من يوم الفحص وطالع

        for exp in exps:
            try:
                chain = tk.option_chain(exp)
                df = chain.puts if pre < 0 else chain.calls
                df = df[(df['bid']>=0.3) & (df['bid']<=10)]
                if df.empty: continue
                df['diff'] = abs(df['strike'] - curr)
                row = df.sort_values('diff').iloc[0]

                exp_d = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_d - SELECTED_DATE).days
                if days < 0: continue # مستحيل يجيب قديم

                return {
                    "sym": sym, "side": "PUT" if pre<0 else "CALL", "pre": pre, "curr": curr,
                    "exp": exp, "days": days, "strike": row['strike'],
                    "last": float(row['lastPrice']), "bid": float(row['bid']),
                    "vol": int(row['volume'] or 0), "oi": int(row['openInterest'] or 0)
                }
            except: continue
    except: return None
    return None

if st.button("🔍 افحص 54 الان", type="primary", use_container_width=True):
    results = []
    prog = st.progress(0)
    for i, s in enumerate(STOCKS_54):
        prog.progress((i+1)/len(STOCKS_54), text=s)
        d = get_best(s)
        if d: results.append(d)
    prog.empty()

    results.sort(key=lambda x: abs(x['pre']), reverse=True)
    st.session_state['res'] = results

    for r in results:
        emoji = "🔴" if r['side']=="PUT" else "🟢"
        strike_txt = int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
        msg = f"""{emoji} {r['sym']} {strike_txt} {r['side']} PRE - {r['side']} {r['pre']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target Stock: {r['curr']*0.993:.1f} > {r['curr']*0.985:.1f} > {r['curr']*0.975:.1f}
Target Contract: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
        st.code(msg)

# --- زر الارسال دائما موجود ---
if 'res' in st.session_state and st.session_state['res']:
    st.divider()
    st.subheader("📤 ارسال تلجرام")
    if st.button("ارسل اقوى 5", use_container_width=True, type="primary"):
        sent=0
        for r in st.session_state['res'][:5]:
            emoji = "🔴" if r['side']=="PUT" else "🟢"
            strike_txt = int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
            msg = f"""{emoji} {r['sym']} {strike_txt} {r['side']} PRE - {r['side']} {r['pre']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target Stock: {r['curr']*0.993:.1f} > {r['curr']*0.985:.1f} > {r['curr']*0.975:.1f}
Target Contract: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
            if send_tg(msg): sent+=1
        st.success(f"تم ارسال {sent} ✅")
