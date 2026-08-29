import streamlit as st, yfinance as yf, requests, math, numpy as np, pandas as pd
from datetime import datetime
import pytz

def norm_cdf(x): return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
def norm_pdf(x): return math.exp(-0.5*x*x) / math.sqrt(2*math.pi)

def calc_greeks(S,K,T,iv,side):
    try:
        if T<=0 or iv<=0: return None
        d1=(math.log(S/K)+(0.05+0.5*iv*iv)*T)/(iv*math.sqrt(T))
        d2=d1-iv*math.sqrt(T)
        delta=norm_cdf(d1) if side=="CALL" else norm_cdf(d1)-1
        gamma=norm_pdf(d1)/(S*iv*math.sqrt(T))
        vega=S*norm_pdf(d1)*math.sqrt(T)/100
        theta=(-S*norm_pdf(d1)*iv/(2*math.sqrt(T)) - 0.05*K*math.exp(-0.05*T)*(norm_cdf(d2) if side=="CALL" else norm_cdf(-d2)))/365
        return {"delta":delta,"gamma":gamma,"theta":theta,"vega":vega}
    except: return None

def detect_accumulation(df5, curr):
    close=df5['Close']; high=df5['High']; low=df5['Low']; vol=df5['Volume']
    if len(close)<80: return None

    # 1- VWAP
    typical=(high+low+close)/3
    vwap=(typical*vol).cumsum()/vol.cumsum()
    vwap_n=float(vwap.iloc[-1])

    # 2- EMA
    ema9=close.ewm(span=9).mean().iloc[-1]
    ema20=close.ewm(span=20).mean().iloc[-1]
    ema50=close.ewm(span=50).mean().iloc[-1]

    # 3- Bollinger BandWidth - اهم شي للتجميع
    sma20=close.rolling(20).mean()
    std20=close.rolling(20).std()
    upper=sma20+2*std20
    lower=sma20-2*std20
    bw=(upper-lower)/sma20
    bw_n=float(bw.iloc[-1])
    bw_20ago=float(bw.iloc[-20]) if len(bw)>20 else bw_n

    # 4- RSI
    delta_c=close.diff()
    gain=delta_c.where(delta_c>0,0).rolling(14).mean()
    loss=-delta_c.where(delta_c<0,0).rolling(14).mean()
    rsi=100-(100/(1+gain/loss.replace(0,0.001)))
    rsi_n=float(rsi.iloc[-1])

    # 5- حجم التجميع - حجم ناشف ثم بداية دخول
    vol_sma20=vol.rolling(20).mean()
    vol_sma5=vol.rolling(5).mean()
    vol_now=float(vol.iloc[-1])
    vol_avg20=float(vol_sma20.iloc[-1])
    vol_ratio=vol_now/vol_avg20 if vol_avg20>0 else 1
    vol_dry = vol_ratio < 0.85 # حجم ناشف = تجميع
    vol_starting = 0.9 <= vol_ratio <= 1.6 # بداية انفجار

    # 6- نطاق ضيق
    range_20 = (high.tail(20).max() - low.tail(20).min()) / curr
    tight_range = range_20 < 0.06 # نطاق ضيق 6% في 20 شمعة = تجميع

    # 7- قريب من الدعم/المقاومة
    demand=float(low.tail(30).min())
    supply=float(high.tail(30).max())
    near_demand = abs(curr-demand)/curr < 0.03
    near_supply = abs(curr-supply)/curr < 0.03

    # تحديد الاتجاه
    if curr > ema9 > ema20 and curr > vwap_n and curr > ema50:
        direction="CALL"
        setup="تجميع صاعد"
    elif curr < ema9 < ema20 and curr < vwap_n and curr < ema50:
        direction="PUT"
        setup="تجميع هابط"
    elif curr > vwap_n and rsi_n > 45:
        direction="CALL"
        setup="فوق VWAP"
    else:
        direction="PUT"
        setup="تحت VWAP"

    # حساب نقاط الانفجار - كلما ضاق النطاق وزاد النشفان كلما قرب الانفجار
    score=0; reasons=[]
    if bw_n < 0.04:
        score+=30; reasons.append(f"🔥 Squeeze قوي {bw_n*100:.2f}%")
    elif bw_n < 0.06:
        score+=20; reasons.append(f"Squeeze {bw_n*100:.2f}%")

    if bw_n < bw_20ago*0.7:
        score+=15; reasons.append("BW يتقلص = قرب انفجار")

    if vol_dry:
        score+=20; reasons.append("حجم ناشف = تجميع")
    if vol_starting:
        score+=15; reasons.append("بداية دخول سيولة")

    if tight_range:
        score+=15; reasons.append(f"نطاق ضيق {range_20*100:.1f}%")

    if near_demand or near_supply:
        score+=10; reasons.append("عند منطقة انفجار")

    if abs(curr-vwap_n)/curr < 0.008:
        score+=10; reasons.append("ملتصق VWAP")

    explosion_ready = (bw_n < 0.05 and (vol_dry or vol_starting) and tight_range)

    return {
        "vwap":vwap_n,"ema9":ema9,"ema20":ema20,"ema50":ema50,"rsi":rsi_n,"bw":bw_n,
        "demand":demand,"supply":supply,"direction":direction,"score":score,
        "reasons":reasons,"vol_ratio":vol_ratio,"range_20":range_20,
        "setup":setup,"explosion_ready":explosion_ready,
        "breakout":supply*1.003,"breakdown":demand*0.997
    }

st.set_page_config(page_title="حوت 54 - رادار التجميع", layout="wide")
riyadh = pytz.timezone('Asia/Riyadh')
eastern = pytz.timezone('US/Eastern')
today_sa = datetime.now(riyadh).date()
now_et = datetime.now(eastern)
hour_et = now_et.hour + now_et.minute/60

# تحديد حالة السوق
if 4 <= hour_et < 9.5: market_status="🌙 قبل السوق - صيد التجميع"
elif 9.5 <= hour_et < 16: market_status="🔥 السوق مفتوح - انفجارات"
elif 16 <= hour_et < 20: market_status="🌆 بعد السوق - تحضير بكرة"
else: market_status="😴 الليل - تجميع هادئ"

with st.sidebar:
    st.header("📤 التلجرام")
    BOT_TOKEN = st.text_input("BOT TOKEN", value=st.secrets.get("BOT_TOKEN",""), type="password")
    CHAT_ID = st.text_input("CHAT ID", value="13889370")
    st.divider()
    st.header("🎯 رادار التجميع")
    mode = st.radio("نوع الصيد", ["💎 تجميع قبل الانفجار (الافضل)", "🔥 انفجار لحظي", "📦 الكل"], index=0)
    min_score = st.slider("اقل نقاط انفجار", 40, 90, 55)

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP"]

st.title("👑 بوت الحوت 54 - رادار التجميع قبل الانفجار V600")
st.success(f"اليوم: {today_sa} | نيويورك: {now_et.strftime('%I:%M %p')} | {market_status}")

def get_accumulation_contract(sym, mode_filter, min_score):
    try:
        tk=yf.Ticker(sym)
        hist5=tk.history(period="10d", interval="15m") # 15 دقيقة افضل للتجميع
        if hist5.empty or len(hist5)<80: return None
        curr=float(hist5['Close'].iloc[-1])
        tech=detect_accumulation(hist5, curr)
        if not tech: return None

        # فلترة حسب الوضع
        if mode_filter=="💎 تجميع قبل الانفجار (الافضل)" and not tech['explosion_ready']:
            if tech['score']<65: return None
        if tech['score'] < 35: return None

        valid=[]
        for e in tk.options:
            try:
                d=datetime.strptime(e, "%Y-%m-%d").date()
                days=(d-today_sa).days
                if 2 <= days <= 21: # من يومين الى 3 اسابيع - افضل مدة للانفجار
                    valid.append((e,days))
            except: continue
        if not valid: return None
        valid.sort(key=lambda x: x[1])
        best=None
        for exp, days in valid[:3]:
            T=days/365.0
            try: chain=tk.option_chain(exp)
            except: continue
            df=chain.calls if tech['direction']=="CALL" else chain.puts
            df=df.copy()
            # عقود رخيصة ومجمعة
            df=df[(df['bid']>=0.25) & (df['bid']<=4.5) & (df['volume'].fillna(0)>=150) & (df['openInterest'].fillna(0)>=400)]
            if df.empty: continue
            # اهم شرط للتجميع: OI اكبر من Vol = ناس مجمعة وما باعت
            df=df[df['openInterest'] > df['volume']*0.8]
            if df.empty: continue
            df['dist']=abs(df['strike']-curr)/curr
            df=df[df['dist']<=0.12] # قريب من السعر
            if df.empty: continue
            df=df.nsmallest(8,'dist')
            for _,row in df.iterrows():
                iv=float(row['impliedVolatility'])
                if iv>2.8: continue
                if iv<0.15: continue # IV ناشف = تجميع
                greeks=calc_greeks(curr,float(row['strike']),T,iv,tech['direction'])
                if not greeks: continue
                if not (0.25 <= abs(greeks['delta']) <= 0.70): continue
                spread=(float(row['ask'])-float(row['bid']))/float(row['bid']) if float(row['bid'])>0 else 1
                if spread>0.40: continue

                # نقاط اضافية للتجميع
                oi_vol_bonus = 15 if row['openInterest'] > row['volume']*2 else 8 if row['openInterest'] > row['volume'] else 0
                iv_bonus = 10 if iv < 0.50 else 0 # IV منخفض = فرصة
                time_bonus = 15 if 5 <= days <= 10 else 10 if 3 <= days <= 14 else 0

                final_score = tech['score'] + abs(greeks['delta'])*35 + greeks['gamma']*80 + oi_vol_bonus + iv_bonus + time_bonus - spread*15

                cand={
                    "symbol":sym,"side":tech['direction'],"curr":curr,"exp":exp,"days":days,
                    "strike":row['strike'],"bid":float(row['bid']),"vol":int(row['volume']),"oi":int(row['openInterest']),"iv":iv,
                    "delta":greeks['delta'],"gamma":greeks['gamma'],"theta":greeks['theta'],"vega":greeks['vega'],"spread":spread,
                    "tech":tech,"score":final_score,
                    "status": "💎 تجميع جاهز للانفجار" if tech['explosion_ready'] and final_score>=75 else "🔥 قرب انفجار" if final_score>=68 else "📦 تجميع"
                }
                if best is None or cand['score'] > best['score']: best=cand
        return best if best and best['score']>=min_score else None
    except: return None

if st.button(f"🔍 فحص رادار التجميع - {market_status}", type="primary", use_container_width=True):
    results=[]
    prog=st.progress(0)
    for i,s in enumerate(STOCKS_54):
        prog.progress((i+1)/len(STOCKS_54), text=f"يفحص تجميع {s}")
        d=get_accumulation_contract(s, mode, min_score)
        if d: results.append(d)
    prog.empty()
    results.sort(key=lambda x: (x['tech']['explosion_ready'], x['score']), reverse=True)
    results=results[:8]
    st.session_state['res']=results
    if not results:
        st.warning("ما فيه تجميع قوي الحين - نزل النقاط الى 45 وجرب")
    else:
        st.success(f"لقي {len(results)} عقد مجمع 💎")
        for r in results:
            t=r['tech']
            emoji="🟢" if r['side']=="CALL" else "🔴"
            stxt=int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
            explosion = "💥 جاهز ينفجر" if t['explosion_ready'] else f"BW {t['bw']*100:.2f}%"
            msg=f"""{r['status']} {emoji} {r['symbol']} {stxt} {r['side']} | {t['setup']} | {explosion}
سهم: ${r['curr']:.2f} | عقد: ${r['bid']:.2f} | {r['days']} يوم | Δ{abs(r['delta']):.2f} Γ{r['gamma']:.3f}
OI:{r['oi']} Vol:{r['vol']} {'OI>Vol تجميع' if r['oi']>r['vol'] else ''} IV:{r['iv']*100:.0f}% {'IV ناشف' if r['iv']<0.5 else ''}
{', '.join(t['reasons'])} | Vol {t['vol_ratio']:.2f}x | نطاق {t['range_20']*100:.1f}%
دخول: ${r['bid']:.2f} | هدف1: ${r['bid']*2:.2f} (100%) | هدف2: ${r['bid']*3.5:.2f} (250%) | هدف3: ${r['bid']*6:.2f} (500%)
وقف: -40% اذا كسر {t['demand'] if r['side']=='CALL' else t['supply']:.2f}"""
            st.code(msg)

if 'res' in st.session_state and st.session_state['res']:
    if st.button("📤 ارسل لتلجرام", type="primary", use_container_width=True):
        c=0
        for r in st.session_state['res']:
            t=r['tech']
            msg=f"{r['status']} {r['symbol']} {r['strike']} {r['side']} {r['days']}d Δ{abs(r['delta']):.2f} {'💥' if t['explosion_ready'] else ''} {', '.join(t['reasons'][:2])}"
            try:
                if requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":msg}, timeout=10).status_code==200: c+=1
            except: pass
        st.success(f"تم ارسال {c}")
