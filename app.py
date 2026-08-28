import streamlit as st
import yfinance as yf
import requests
from datetime import datetime

st.set_page_config(page_title="حوت 54 - بري ماركت", layout="wide")
st.title("👑 بوت الحوت 54 - فحص البري ماركت")

# --- الاعدادات ---
BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = "13889370"

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP","SMH","XLF"]

def send_tg(text):
    if not BOT_TOKEN:
        st.error("ما فيه BOT_TOKEN في Secrets")
        return False
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": text}
        r = requests.post(url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        st.error(f"خطأ: {e}")
        return False

def get_best_contract(sym):
    try:
        tk = yf.Ticker(sym)
        hist = tk.history(period="2d", interval="5m")
        if hist.empty or len(hist) < 2:
            return None
        curr = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-20]) if len(hist) > 20 else float(hist['Close'].iloc[0])
        pre_pct = ((curr - prev_close) / prev_close) * 100

        # --- فتح التاريخ: يوم الفحص او بعده ---
        today = datetime.now().date()
        all_exps = tk.options
        valid_exps = []
        for e in all_exps:
            try:
                d = datetime.strptime(e, "%Y-%m-%d").date()
                if d >= today:
                    valid_exps.append(e)
            except:
                continue

        if not valid_exps:
            return None

        exps = valid_exps[:4] # يفحص اول 4 تواريخ جاية

        best = None
        for exp in exps:
            try:
                chain = tk.option_chain(exp)
                df = chain.puts if pre_pct < 0 else chain.calls
                # عقود رخيصة وفيها سيولة
                df = df[(df['bid']>=0.40) & (df['bid']<=8) & (df['volume'].fillna(0) > 50)]
                if df.empty:
                    continue
                # اقرب سترايك للسعر الحالي
                df['diff'] = abs(df['strike'] - curr)
                df = df.sort_values('diff')
                row = df.iloc[0]

                exp_date = datetime.strptime(exp, "%Y-%m-%d").date()
                days = (exp_date - today).days

                best = {
                    "symbol": sym,
                    "side": "PUT" if pre_pct < 0 else "CALL",
                    "pre_pct": pre_pct,
                    "curr": curr,
                    "exp": exp,
                    "days": days,
                    "strike": int(row['strike']) if row['strike'] == int(row['strike']) else row['strike'],
                    "last": float(row['lastPrice']),
                    "bid": float(row['bid']),
                    "vol": int(row['volume']) if row['volume'] else 0,
                    "oi": int(row['openInterest']) if row['openInterest'] else 0
                }
                break
            except:
                continue
        return best
    except:
        return None

# --- واجهة الفحص ---
if st.button("🔍 الفحص 54 الان", type="primary", use_container_width=True):
    results = []
    progress = st.progress(0, text="جاري الفحص...")
    status_text = st.empty()

    for i, sym in enumerate(STOCKS_54):
        progress.progress((i+1)/len(STOCKS_54), text=f"يفحص {sym}...")
        data = get_best_contract(sym)
        if data:
            results.append(data)

    progress.empty()
    status_text.empty()

    if not results:
        st.warning("ما لقى عقود - جرب وقت البري ماركت 4-9 صباحا بتوقيت نيويورك")
    else:
        # ترتيب الاقوى حسب حركة البري ماركت
        results.sort(key=lambda x: abs(x['pre_pct']), reverse=True)
        st.success(f"لقي {len(results)} عقد")

        # حفظ النتائج في الجلسة عشان الارسال
        st.session_state['last_results'] = results

        for r in results:
            emoji = "🔴" if r['side']=="PUT" else "🟢"
            msg = f"""{emoji} {r['symbol']} {r['strike']} {r['side']} PRE - {r['side']} {r['pre_pct']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target Stock: {r['curr']*0.993:.1f} > {r['curr']*0.985:.1f} > {r['curr']*0.975:.1f}
Target Contract: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
            st.code(msg, language="text")

# --- زر الارسال ---
if 'last_results' in st.session_state and st.session_state['last_results']:
    st.divider()
    if st.button("📤 ارسل اقوى 5 لتلجرام", type="primary", use_container_width=True):
        count = 0
        for r in st.session_state['last_results'][:5]:
            emoji = "🔴" if r['side']=="PUT" else "🟢"
            msg = f"""{emoji} {r['symbol']} {r['strike']} {r['side']} PRE - {r['side']} {r['pre_pct']:.1f}%
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f}
Entry: ${r['last']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']}
Stop: ${r['bid']*0.55:.2f}
Target Stock: {r['curr']*0.993:.1f} > {r['curr']*0.985:.1f} > {r['curr']*0.975:.1f}
Target Contract: ${r['bid']*1.5:.2f} (+50%) | ${r['bid']*2.3:.2f} (+130%) | ${r['bid']*3.2:.2f} (+220%)"""
            if send_tg(msg):
                count += 1
        st.success(f"تم ارسال {count} عقود لتلجرام ✅")
        st.balloons()

st.divider()
st.caption("التواريخ مفتوحة: يجيب عقود اليوم او اي يوم بعده | اذا ما ارسل تأكد من BOT_TOKEN في Secrets")
