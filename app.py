# راصد الحيتان - V3
# يشتغل السوق فاتح أو مسكر - 150 سهم - نظام نقاط - أفضل 10 دائما
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, time
import pytz

st.set_page_config(page_title="راصد الحيتان", layout="wide")
st.title("📊 راصد الحيتان")

# ================= 1. قائمة الأسهم - 150 سهم =================
# بدل 50، صارت 150: قيادية + تكنولوجيا + طاقة + بنوك + صحة + تجزئة + ETF
STOCKS_150 = [
    # ETF الكبيرة - 10
    "SPY","QQQ","IWM","DIA","VOO","IVV","ARKK","XLF","XLK","XLE",
    # التكنولوجيا الكبيرة - 25
    "NVDA","AAPL","MSFT","GOOGL","GOOG","AMZN","META","TSLA","AVGO","ORCL",
    "AMD","NFLX","CRM","ADBE","INTC","MU","QCOM","TXN","AMAT","LRCX",
    "PLTR","SNOW","CRWD","PANW","SHOP",
    # البنوك والمالية - 15
    "JPM","BAC","GS","MS","WFC","C","BLK","SCHW","AXP","V",
    "MA","PYPL","COIN","HOOD","SOFI",
    # الطاقة - 12
    "XOM","CVX","COP","SLB","EOG","OXY","MPC","PSX","VLO","HAL",
    "MSTR","CLSK",
    # الصحة - 15
    "LLY","UNH","JNJ","MRK","PFE","ABBV","TMO","AMGN","GILD","REGN",
    "VRTX","ISRG","HIMS","UNH","CVS",
    # التجزئة والاستهلاك - 15
    "WMT","COST","HD","MCD","SBUX","NKE","TGT","LOW","TJX","CMG",
    "LULU","ABNB","UBER","LYFT","DASH",
    # الصناعة والدفاع - 12
    "BA","CAT","GE","HON","LMT","RTX","NOC","GD","DE","UPS",
    "FDX","DAL",
    # الاتصالات والإعلام - 10
    "T","VZ","TMUS","DIS","CMCSA","WBD","PARA","NFLX","SPOT","ROKU",
    # أشباه الموصلات الإضافية - 10
    "NVDA","SMCI","ARM","ASML","TSM","MRVL","KLAC","SNPS","CDNS","ON",
    # النمو والمضاربة - 16
    "RIVN","LCID","NIO","PLUG","OPEN","GME","AMC","BBBY","DWAC","AFRM",
    "UPST","AI","SOUN","IONQ","RGTI","QBTS",
    # أخرى قيادية - 10
    "BRK-B","PEP","KO","PG","XOM","VZ","INTC","CSCO","IBM","ORCL",
]
# إزالة التكرار
STOCKS_150 = list(dict.fromkeys(STOCKS_150))
st.write(f"عدد الأسهم في الفحص: **{len(STOCKS_150)} سهم**")

# ================= 2. هل السوق فاتح؟ - للعرض فقط =================
def is_market_open():
    ny = pytz.timezone("America/New_York")
    now = datetime.now(ny)
    if now.weekday() >= 5:
        return False, now
    return time(9, 30) <= now.time() <= time(16, 0), now

market_open, ny_now = is_market_open()
if market_open:
    st.success(f"🟢 السوق فاتح - نستخدم بيانات حية | {ny_now.strftime('%H:%M')} نيويورك")
    data_source = "live"
else:
    st.warning(f"🔴 السوق مسكر - نستخدم بيانات آخر إغلاق | {ny_now.strftime('%H:%M')} نيويورك")
    data_source = "last_close"

# ================= 3. نظام النقاط =================
def score_stock(symbol):
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period="5d")
        if hist.empty or len(hist) < 2:
            return None
        info = tk.info

        last_close = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
        change_pct = (last_close - prev_close) / prev_close * 100

        # التذبذب من آخر 5 أيام - يشتغل فاتح أو مسكر
        volatility = float(hist['Close'].pct_change().std() * 100)
        avg_vol = float(hist['Volume'].mean())
        last_vol = float(hist['Volume'].iloc[-1])
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 0

        # السبريد: حي إذا فاتح، و High-Low إذا مسكر
        if data_source == "live":
            bid = info.get('bid', 0) or 0
            ask = info.get('ask', 0) or 0
            spread_pct = (ask - bid) / last_close * 100 if bid and ask else 1.0
        else:
            high = float(hist['High'].iloc[-1])
            low = float(hist['Low'].iloc[-1])
            spread_pct = (high - low) / last_close * 100

        # تقدير سعر العقد - نستخدم التذبذب لتقديره
        # إذا السهم بين 100 و 400، العقد غالبا بين 2 و 3
        est_premium = round(last_close * volatility / 100, 2)
        if est_premium < 1:
            est_premium = 2.5  # قيمة افتراضية للعرض

        score = 0
        reasons = []

        # سهم قيادي - حجم تداول عالي
        if avg_vol > 10_000_000:
            score += 25
            reasons.append("قيادي")
        elif avg_vol > 3_000_000:
            score += 15

        # تذبذب عالي
        if volatility > 2.5:
            score += 25
            reasons.append(f"تذبذب {volatility:.2f}%")
        elif volatility > 1.5:
            score += 15

        # سبريد ضيق نسبيا
        if spread_pct < 2.0:
            score += 25
            reasons.append("سبريد ضيق")
        elif spread_pct < 4.0:
            score += 15

        # حجم تداول أعلى من المتوسط - اهتمام حيتان
        if vol_ratio > 1.5:
            score += 25
            reasons.append(f"حجم {vol_ratio:.1f}x")
        elif vol_ratio > 1.0:
            score += 15

        # سعر العقد في نطاق 2-3
        if 2.0 <= est_premium <= 3.5:
            score += 10
            reasons.append(f"عقد ~{est_premium}")

        return {
            "symbol": symbol,
            "score": score,
            "last_close": last_close,
            "change": change_pct,
            "volatility": volatility,
            "spread": spread_pct,
            "premium": est_premium,
            "reasons": " - ".join(reasons),
            "source": data_source
        }
    except Exception:
        return None

# ================= 4. زر الفحص =================
if st.button("🔍 افحص الآن", use_container_width=True):
    with st.spinner(f"جار فحص {len(STOCKS_150)} سهم..."):
        results = []
        progress = st.progress(0)
        for i, sym in enumerate(STOCKS_150):
            r = score_stock(sym)
            if r:
                results.append(r)
            progress.progress((i + 1) / len(STOCKS_150))

        # ترتيب وأفضل 10 - دائما يرجع 10، حتى لو السوق مسكر
        results = sorted(results, key=lambda x: x['score'], reverse=True)
        top10 = results[:10]

        st.success(f"✅ فحصت {len(results)} سهم - لقيت {len(results)} سهم - أفضل 10")

        # ================= 5. عرض أفضل 10 بنفس صيغة الواتساب =================
        for idx, r in enumerate(top10, 1):
            # اتجاه تقديري: إذا صاعد + تذبذب عالي = CALL، إذا هابط = PUT
            # هذا تقدير مبدئي، لازم تأكيده بمؤشرك الرئيسي
            direction = "CALL 🟢" if r['change'] >= 0 else "PUT 🔴"
            strike = round(r['last_close'])
            entry = r['premium']
            stop = round(entry * 0.67, 2)
            # الأهداف بنفس معادلة البوت السابق: 1.25 / 1.35 / 1.50 / 1.65 / 1.75 / 1.85 / 1.90 / 2.00
            targets = [round(entry * m, 2) for m in [1.25, 1.35, 1.50, 1.65, 1.75, 1.85, 1.90, 2.00]]

            with st.container():
                st.markdown(f"""
                **#{idx} - {r['symbol']}** | {direction} {strike} | النقاط: **{r['score']}/110**
                - السعر: {r['last_close']:.2f} ({r['change']:+.2f}%) | التذبذب: {r['volatility']:.2f}% | السبريد: {r['spread']:.2f}%
                - الدخول: {entry} | الوقف: {stop} | المصدر: {'حي' if r['source']=='live' else 'آخر إغلاق'}
                - الأهداف: {' | '.join(map(str, targets))}
                - الأسباب: {r['reasons']}
                ---
                """)
        
        # جدول كامل
        st.subheader("جدول أفضل 10")
        df = pd.DataFrame(top10)[["symbol","score","last_close","change","volatility","spread","premium","reasons"]]
        st.dataframe(df, use_container_width=True)
