# راصد الحيتان - V5
# إصلاح الإرسال + إصلاح بريميوم SPY/QQQ + إصلاح PUT الغلط
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")

# ============ 1. إرسال واتساب - CallMeBot - يشتغل بدون توكن معقد ============
# الطريقة اللي تشتغل فعلا: روح واتساب وارسل "I allow callmebot to send me messages" لرقم +34 644 10 47 73
# بيرد عليك بكود apikey، حطه هنا
CALLMEBOT_APIKEY = st.secrets.get("CALLMEBOT_APIKEY", "حط_ال apikey هنا")
CALLMEBOT_PHONE = st.secrets.get("CALLMEBOT_PHONE", "9665xxxxxxxx")  # رقمك بدون +

def send_whatsapp(msg):
    # نطبع الخطأ عشان نعرف ليش مايرسل، مو نسكت
    try:
        url = "https://api.callmebot.com/whatsapp.php"
        params = {"phone": CALLMEBOT_PHONE, "text": msg, "apikey": CALLMEBOT_APIKEY}
        r = requests.get(url, params=params, timeout=15)
        st.write(f"رد الواتساب: {r.status_code} - {r.text[:200]}")  # للتشخيص
        return r.status_code == 200 and "Message queued" in r.text
    except Exception as e:
        st.error(f"خطأ إرسال: {e}")
        return False

# زر تجربة الإرسال - جربه قبل الفحص
if st.button("📱 جرب الإرسال الآن"):
    if send_whatsapp("تجربة راصد الحيتان - إذا وصلتك معناها الإرسال شغال ✅"):
        st.success("تم الإرسال - شيك واتسابك")
    else:
        st.error("ما أرسل - تأكد من apikey والرقم. شوف رسالة الخطأ فوق")

# ============ 2. الأسهم ============
STOCKS = ["SPY","QQQ","NVDA","AAPL","MSFT","GOOGL","AMZN","META","TSLA","AVGO","ORCL","AMD","NFLX","CRM","MU","PLTR","COIN","HOOD","SOFI","MSTR","LLY","UNH","WMT","COST","BA","CAT","DIS","SMCI","ARM","RIVN","BRK-B","JPM","BAC","GS","XOM","CVX"]
STOCKS = list(dict.fromkeys(STOCKS))

# ============ 3. التصحيح: بريميوم نسبي + فصل CALL عن PUT ============
def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None

        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)

        # التصحيح هنا: البريميوم كنسبة من سعر السهم، مو رقم ثابت
        # للأسهم الغالية SPY/QQQ: 0.3% إلى 1.0% من السعر = 2.2 إلى 7.5 لـ SPY
        # للأسهم الرخيصة: 1.0% إلى 2.0% = 2 إلى 3 لـ NVDA
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01  # SPY/QQQ
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            # سترايك قريب من السعر 5% فقط، مو 10% - عشان ما نجيب عقود بعيدة ميتة
            f = df[(df['lastPrice'] >= min_prem) & (df['lastPrice'] <= max_prem) &
                   (df['volume'].fillna(0) > 500) &
                   (abs(df['strike'] - last) / last < 0.05)]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]

        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')

        # التصحيح الثاني: لا نختار PUT تلقائيا لأنه أعلى حجم
        # نعرض الاثنين، ونختار الاتجاه حسب سعر السهم مقارنة بآخر إغلاق
        # إذا السهم صاعد اليوم، الحوت الأقوى هو CALL، حتى لو PUT حجمه أكبر لأنه تحوط
        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        if change >= 0:
            # السوق طالع، نفضل CALL
            whale = best_call if best_call is not None else best_put
            reason = "السهم صاعد، تجاهلنا PUT التحوط"
        else:
            whale = best_put if best_put is not None else best_call
            reason = "السهم هابط، تجاهلنا CALL التحوط"

        if whale is None:
            return None

        entry = float(whale['lastPrice'])
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]

        return {
            "symbol": symbol, "type": whale['type'], "strike": float(whale['strike']),
            "expiry": expiry, "entry": entry, "stop": stop, "targets": targets,
            "volume": int(whale['volume']), "last": last, "change": change,
            "reason": reason, "prem_range": f"{min_prem:.2f} - {max_prem:.2f}"
        }
    except Exception as e:
        return None

# ============ 4. الفحص والعرض كتوصيات ============
if st.button("🔍 افحص الآن", use_container_width=True):
    results = []
    prog = st.progress(0)
    for i, s in enumerate(STOCKS):
        r = get_whale(s)
        if r:
            results.append(r)
        prog.progress((i+1)/len(STOCKS))
    results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
    st.session_state['res'] = results
    st.success(f"لقيت {len(results)} توصية")

if 'res' in st.session_state:
    for r in st.session_state['res']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        msg = f"""🔍 راصد الحيتان
{r['symbol']}
{emoji} شراء مرجح {r['type']} {r['strike']:.1f}
الانتهاء: {r['expiry']} 📅
سعر التنفيذ: {r['entry']} ({int(r['entry']*100)} دولار للعقد) 💰
الوقف: {r['stop']} 🔴 | الكمية: {r['volume']} عقد 📦
الأهداف بالترتيب 🎯
{' | '.join(map(str, r['targets']))}
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""

        st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']}")
        st.write(f"السعر: {r['last']:.2f} ({r['change']:+.2f}%) | نطاق البريميوم الصح لهالسهم: {r['prem_range']} | {r['reason']}")
        st.code(msg)
        if st.button(f"📤 أرسل {r['symbol']} واتساب", key=f"s_{r['symbol']}"):
            if send_whatsapp(msg):
                st.success("تم الإرسال ✅ شيك واتسابك")
