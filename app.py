# ============================================================
# راصد الحيتان - V8 - الإرسال حسب التحديد
# لا يوجد رقم ثابت - انت تختار الرقم + تختار أي توصية ترسلها
# ============================================================
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("🔍 راصد الحيتان")

# ============================================================
# 1. الإرسال حسب التحديد - لا يوجد رقم ثابت
# ============================================================
st.subheader("📱 إرسال الواتساب - حسب تحديدك")

# خانة الرقم - تقدر تغيره في أي وقت، مو ثابت
# تقدر تحط رقم واحد، أو أكثر من رقم مفصول بفاصلة
recipients_text = st.text_input(
    "أرقام الواتساب - تقدر تحط رقم واحد أو أكثر مفصول بفاصلة ,",
    value=st.session_state.get("recipients", "966555371577"),
    help="مثال: 966555371577 أو 966555371577,966500000000",
    key="recipients_input"
)
st.session_state["recipients"] = recipients_text

apikey_input = st.text_input(
    "apikey من CallMeBot",
    value=st.session_state.get("apikey", ""),
    type="password",
    help="ارسل واتساب 'I allow callmebot to send me messages' لرقم +34 644 10 47 73 عشان يجيك الـ apikey"
)
st.session_state["apikey"] = apikey_input

def clean_phone(raw):
    p = str(raw).strip()
    p = p.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if p.startswith("00"):
        p = p[2:]
    if p.startswith("0"):
        p = "966" + p[1:]
    if len(p) == 9 and p.startswith("5"):
        p = "966" + p
    return p

def get_recipients():
    # يفصل الأرقام بالفاصلة، وينظف كل واحد
    raw_list = str(st.session_state.get("recipients", "")).split(",")
    clean_list = []
    for r in raw_list:
        c = clean_phone(r)
        if len(c) == 12 and c.startswith("966"):
            clean_list.append(c)
    return clean_list

def send_to_selected(msg, phone_list, apikey):
    # يرسل لنفس الرسالة لكل رقم حددته، مو رقم ثابت واحد
    if not phone_list:
        st.error("حط رقم واحد على الأقل بصيغة 966 + رقمك بدون +")
        return False
    if not apikey:
        st.error("حط الـ apikey في الخانة اللي فوق")
        return False
    ok = True
    for phone in phone_list:
        try:
            url = "https://api.callmebot.com/whatsapp.php"
            params = {"phone": phone, "text": msg, "apikey": apikey}
            r = requests.get(url, params=params, timeout=15)
            st.write(f"📤 أرسل لـ {phone}: {r.status_code} - {r.text[:150]}")
            if "ERROR" in r.text:
                st.error(f"فشل لـ {phone}: {r.text[:200]}")
                ok = False
        except Exception as e:
            st.error(f"خطأ لـ {phone}: {e}")
            ok = False
    return ok

# عرض الأرقام المحددة حاليا
phones_now = get_recipients()
if phones_now:
    st.success(f"✅ الأرقام المحددة حاليا للإرسال: {', '.join(phones_now)}")
else:
    st.warning("⚠️ ما فيه رقم صحيح محدد - حط رقم بصيغة 966555371577")

if st.button("📱 جرب الإرسال الآن - للأرقام المحددة", use_container_width=True):
    if send_to_selected("تجربة راصد الحيتان - إذا وصلتك معناها الإرسال شغال ✅", phones_now, st.session_state["apikey"]):
        st.success("تم الإرسال للأرقام المحددة ✅")

st.divider()

# ============================================================
# 2. هل السوق فاتح؟ - للعرض فقط
# ============================================================
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح - بيانات حية | {ny_now.strftime('%H:%M')} نيويورك")
else:
    st.warning(f"🔴 السوق مسكر - بيانات آخر إغلاق | {ny_now.strftime('%H:%M')} نيويورك")

# ============================================================
# 3. الأسهم - 150 سهم
# ============================================================
STOCKS_150 = [
    "SPY","QQQ","IWM","DIA","VOO","IVV","ARKK","XLF","XLK","XLE",
    "NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL",
    "AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX",
    "PLTR","SNOW","CRWD","PANW","SHOP",
    "JPM","BAC","GS","MS","WFC","C","BLK","SCHW","AXP","V",
    "MA","PYPL","COIN","HOOD","SOFI",
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","HAL","MSTR","CLSK",
    "LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","REGN",
    "VRTX","ISRG","HIMS","CVS","ZTS",
    "WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG",
    "LULU","ABNB","UBER","LYFT","DASH",
    "BA","CAT","GE","HON","LMT","RTX","NOC","GD","DE","UPS","FDX","DAL",
    "T","VZ","TMUS","DIS","CMCSA","WBD","PARA","SPOT","ROKU",
    "SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON","SWKS",
    "RIVN","LCID","NIO","PLUG","OPEN","GME","AMC","AFRM",
    "UPST","AI","SOUN","IONQ","RGTI","QBTS","DNA","BBAI",
    "BRK-B","PEP","KO","PG","CSCO","IBM",
]
STOCKS_150 = list(dict.fromkeys(STOCKS_150))
st.write(f"عدد الأسهم: **{len(STOCKS_150)} سهم**")

# ============================================================
# 4. جلب عقد الحوت
# ============================================================
def get_whale(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        last = float(hist['Close'].iloc[-1])
        if last < 20:
            return None
        expiries = tk.options
        if not expiries:
            return None
        expiry = expiries[0]
        chain = tk.option_chain(expiry)
        if last > 500:
            min_prem, max_prem = last * 0.003, last * 0.01
        elif last > 200:
            min_prem, max_prem = last * 0.005, last * 0.015
        else:
            min_prem, max_prem = 2.0, 3.0

        def best_in(df, opt_type):
            df = df.copy()
            df['type'] = opt_type
            f = df[(df['lastPrice'] >= min_prem) & (df['lastPrice'] <= max_prem) &
                   (df['volume'].fillna(0) > 500) &
                   (abs(df['strike'] - last) / last < 0.05)]
            if f.empty:
                return None
            return f.sort_values('volume', ascending=False).iloc[0]

        best_call = best_in(chain.calls, 'CALL')
        best_put = best_in(chain.puts, 'PUT')
        change = (last - float(hist['Close'].iloc[-2])) / float(hist['Close'].iloc[-2]) * 100
        if change >= 0:
            whale = best_call if best_call is not None else best_put
            reason = "السهم صاعد، تجاهلنا PUT التحوط"
        else:
            whale = best_put if best_put is not None else best_call
            reason = "السهم هابط، تجاهلنا CALL التحوط"
        if whale is None:
            return None
        entry = float(whale['lastPrice'])
        strike = float(whale['strike'])
        volume = int(whale['volume'])
        stop = round(entry * 0.67, 2)
        targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]
        return {"symbol": symbol, "type": whale['type'], "strike": strike, "expiry": expiry,
                "entry": entry, "stop": stop, "targets": targets, "volume": volume,
                "last": last, "change": change, "reason": reason,
                "prem_range": f"{min_prem:.2f} - {max_prem:.2f}"}
    except Exception:
        return None

def make_msg(r):
    emoji = "🟢" if r['type'] == 'CALL' else "🔴"
    return f"""🔍 راصد الحيتان
{r['symbol']}
{emoji} شراء مرجح {r['type']} {r['strike']:.1f}
الانتهاء: {r['expiry']} 📅
سعر التنفيذ: {r['entry']} ({int(r['entry']*100)} دولار للعقد) 💰
الوقف: {r['stop']} 🔴 | الكمية: {r['volume']} عقد 📦
الأهداف بالترتيب 🎯
{' | '.join(map(str, r['targets']))}
⚠️ إدارة الوقف
بعد الهدف الأول، ارفع الوقف إلى سعر الدخول. وبعد كل هدف جديد، ارفعه إلى سعر الهدف السابق.
📌 رصد البوت هذه الصفقة للمتابعة فقط. ليست توصية بالبيع أو الشراء."""

# ============================================================
# 5. الفحص
# ============================================================
if st.button("🔍 افحص الآن - 150 سهم", use_container_width=True):
    with st.spinner(f"جار فحص {len(STOCKS_150)} سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = get_whale(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))
        results = sorted(results, key=lambda x: x['volume'], reverse=True)[:10]
        st.session_state['results'] = results
        st.session_state['selected'] = [r['symbol'] for r in results]  # كلها محددة مبدئيا، انت تشيل اللي ما تبيه
        st.success(f"✅ فحصت {len(STOCKS_150)} سهم - لقيت {len(results)} توصية")

# ============================================================
# 6. عرض التوصيات + التحديد + الإرسال حسب التحديد
# ============================================================
if 'results' in st.session_state and st.session_state['results']:
    st.subheader("🏆 أفضل 10 توصيات - حدد اللي تبي ترسله")

    # تحديد جماعي - تختار أي أسهم ترسلها، مو كلها
    all_symbols = [r['symbol'] for r in st.session_state['results']]
    selected = st.multiselect(
        "✅ حدد الأسهم اللي تبي ترسلها للواتساب - اللي تختاره بس هو اللي بينرسل",
        options=all_symbols,
        default=st.session_state.get('selected', all_symbols),
        key="selected_multiselect"
    )
    st.session_state['selected'] = selected
    st.write(f"المحدد حاليا للإرسال: **{len(selected)}** توصية: {', '.join(selected) if selected else 'ما حددت شي'}")

    # زر إرسال المحدد فقط - للأرقام المحددة فوق
    if st.button(f"📤 أرسل المحدد فقط ({len(selected)}) للأرقام المحددة", use_container_width=True, type="primary"):
        if not selected:
            st.error("حدد توصية واحدة على الأقل من القائمة اللي فوق")
        else:
            phones = get_recipients()
            for r in st.session_state['results']:
                if r['symbol'] in selected:
                    send_to_selected(make_msg(r), phones, st.session_state["apikey"])
            st.success(f"تم إرسال {len(selected)} توصية للأرقام: {', '.join(phones)} ✅")

    st.divider()

    # عرض كل توصية مع زر إرسال فردي - يرسل للأرقام المحددة فوق
    for r in st.session_state['results']:
        emoji = "🟢" if r['type'] == 'CALL' else "🔴"
        is_selected = r['symbol'] in selected
        tick = "✅ محدد للإرسال" if is_selected else "⬜ غير محدد - ما بينرسل"
        msg = make_msg(r)
        with st.container():
            st.markdown(f"### {emoji} {r['symbol']} - {r['type']} {r['strike']:.1f} - دخول {r['entry']} - {tick}")
            st.write(f"السعر: {r['last']:.2f} ({r['change']:+.2f}%) | حجم: {r['volume']} | الانتهاء: {r['expiry']}")
            st.write(f"نطاق البريميوم: {r['prem_range']} | {r['reason']}")
            st.code(msg, language="text")
            # زر فردي يرسل هالتوصية فقط، للأرقام المحددة فوق
            if st.button(f"📤 أرسل {r['symbol']} فقط للأرقام المحددة", key=f"send_{r['symbol']}", use_container_width=True):
                phones = get_recipients()
                if send_to_selected(msg, phones, st.session_state["apikey"]):
                    st.success(f"تم إرسال {r['symbol']} لـ {', '.join(phones)} ✅")
            st.divider()
