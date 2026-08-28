import streamlit as st
import yfinance as yf
import requests
from datetime import datetime
import pytz

st.set_page_config(page_title="حوت 54", layout="wide")

# --- CSS يصلح الجوال ---
st.markdown("""
<style>
[data-testid="stSidebar"] {min-width: 280px;}
.stButton>button {width:100%; border-radius:12px; height:3em;}
</style>
""", unsafe_allow_html=True)

eastern = pytz.timezone('US/Eastern')
today_et = datetime.now(eastern).date()

# --- الشريط الجانبي ---
with st.sidebar:
    st.header("📤 التلجرام")
    BOT_TOKEN = st.text_input("BOT TOKEN", value=st.secrets.get("BOT_TOKEN",""), type="password")
    CHAT_ID = st.text_input("CHAT ID", value="13889370")
    st.divider()

    st.header("📚 البحوث السابقة")
    if 'history' not in st.session_state:
        st.session_state['history'] = []

    if st.session_state['history']:
        for i, h in enumerate(reversed(st.session_state['history'][-10:])):
            with st.expander(f"{h['time']} - {h['count']} عقد"):
                st.code(h['preview'])
                if st.button(f"اعادة ارسال {i}", key=f"re_{i}"):
                    for msg in h['msgs'][:5]:
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": msg})
                    st.success("تم")
    else:
        st.caption("لا يوجد بحوث سابقة")

    st.divider()
    if st.button("🗑️ مسح السجل"):
        st.session_state['history'] = []
        st.session_state['res'] = []

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP"]

st.title("👑 بوت الحوت 54")
st.caption(f"اليوم بتوقيت نيويورك: {today_et} | يجيب عقود من بكره وطالع فقط (مستحيل قديم)")

def get_best(sym):
    try:
        tk = yf.Ticker(sym)
        hist = tk.history(period="2d", interval="5m")
        if hist.empty: return None
        curr = float(hist['Close'].iloc[-1])
        prev = float(hist['Close'].iloc[-20]) if len(hist)>20 else float(hist['Close'].iloc[0])
        pre = ((curr-prev)/prev)*100
        if abs(pre) < 0.3: return None # فلتر ضعيف

        # --- حل نهائي للتواريخ: اكبر من اليوم فقط ---
        valid = []
        for e in tk.options:
            try:
                d = datetime.strptime(e, "%Y-%m-%d").date()
                if d > today_et: # اهم سطر: اكبر من اليوم فقط، ما يجيب 0d
                    valid.append(e)
            except: continue
        if not valid: return None

        for exp in valid[:3]:
            try:
                chain = tk.option_chain(exp)
                df = chain.puts if pre < 0 else chain.calls
                df = df[(df['bid']>=0.3) & (df['bid']<=12)]
                if df.empty: continue
                df['diff'] = abs(df['strike'] - curr)
                row = df.sort_values('diff').iloc[0]
                exp_d = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_d - today_et).days
                return {"sym":sym,"side":"PUT" if pre<0 else "CALL","pre":pre,"curr":curr,"exp":exp,"days":days,"strike":row['strike'],"last":float(row['lastPrice']),"bid":float(row['bid']),"vol":int(row['volume'] or 0),"oi":int(row['openInterest'] or 0)}
            except: continue
    except: return None

if st.button("🔍 الفحص 54 الان", type="primary"):
    results = []
    seen = set()
    prog = st.progress(0)
    for i, s in enumerate(STOCKS_54):
        prog.progress((i+1)/len(STOCKS_54), text=f"{s}")
        d = get_best(s)
        if d:
            key = (d['sym'], d['strike'], d['exp'])
            if key not in seen:
                seen.add(key)
                results.append(d)
    prog.empty()
    results.sort(key=lambda x: abs(x['pre']), reverse=True)
    st.session_state['res'] = results

    # حفظ في السجل الجانبي
    msgs = []
    for r in results:
        emoji = "🔴" if r['side']=="PUT" else "🟢"
        stxt = int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
        msg = f"""{emoji} {r['sym']} {stxt} {r['side']} PRE - {r['side']} {r['pre']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
        msgs.append(msg)
        st.code(msg)

    if msgs:
        st.session_state['history'].append({
            "time": datetime.now(eastern).strftime("%m-%d %H:%M"),
            "count": len(msgs),
            "preview": msgs[0][:100],
            "msgs": msgs
        })

if 'res' in st.session_state and st.session_state['res']:
    st.divider()
    if st.button("📤 ارسل اقوى 5 لتلجرام", type="primary"):
        c=0
        for r in st.session_state['res'][:5]:
            emoji = "🔴" if r['side']=="PUT" else "🟢"
            stxt = int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
            msg = f"""{emoji} {r['sym']} {stxt} {r['side']} PRE - {r['side']} {r['pre']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
            try:
                rr = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":msg}, timeout=10)
                if rr.status_code==200: c+=1
            except: pass
        st.success(f"تم ارسال {c} ✅")
        st.balloons()
