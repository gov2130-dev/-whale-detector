import streamlit as st, yfinance as yf, requests, math, numpy as np, pandas as pd
from datetime import datetime
import pytz
from scipy.stats import norm

st.set_page_config(page_title="حوت 54 - النهائي المدمج", layout="wide")
st.markdown("<style>.stButton>button{width:100%;border-radius:12px;height:3.2em;font-weight:bold}</style>", unsafe_allow_html=True)

riyadh = pytz.timezone('Asia/Riyadh')
eastern = pytz.timezone('US/Eastern')
today_sa = datetime.now(riyadh).date()
now_et = datetime.now(eastern)

with st.sidebar:
    st.header("📤 التلجرام")
    BOT_TOKEN = st.text_input("BOT TOKEN", value=st.secrets.get("BOT_TOKEN",""), type="password")
    CHAT_ID = st.text_input("CHAT ID", value="13889370")
    if st.button("🧪 اختبار"):
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":"النهائي شغال 👑"}, timeout=10)
        st.success("شغال ✅" if r.status_code==200 else r.text)
    st.divider()
    st.header("📚 السجل")
    if 'history' not in st.session_state: st.session_state['history']=[]
    for h in reversed(st.session_state['history'][-8:]):
        with st.expander(f"{h['time']} - {h['count']}"):
            st.code(h['preview'])

STOCKS_54 = ["NVDA","TSLA","AAPL","MSFT","AMZN","META","NFLX","AMD","NVDL","TSLL","PLTR","COIN","MSTR","SMCI","AVGO","GOOGL","SPY","QQQ","IWM","TSM","ARM","MU","MRVL","CRWD","NOW","HOOD","SOFI","AFRM","UPST","DKNG","RBLX","U","SHOP","SQ","PYPL","INTC","QCOM","ADBE","CRM","ORCL","UBER","ABNB","NKE","DIS","BA","XOM","JPM","GS","MS","WMT","COST","PEP"]

# ========== اليونانيات + الوقت ==========
def calc_greeks(S,K,T,iv,side):
    try:
        if T<=0 or iv<=0: return None
        d1=(math.log(S/K)+(0.05+0.5*iv*iv)*T)/(iv*math.sqrt(T))
        d2=d1-iv*math.sqrt(T)
        delta=norm.cdf(d1) if side=="CALL" else norm.cdf(d1)-1
        gamma=norm.pdf(d1)/(S*iv*math.sqrt(T))
        vega=S*norm.pdf(d1)*math.sqrt(T)/100
        theta=(-S*norm.pdf(d1)*iv/(2*math.sqrt(T)) - 0.05*K*math.exp(-0.05*T)*(norm.cdf(d2) if side=="CALL" else norm.cdf(-d2)))/365
        return {"delta":delta,"gamma":gamma,"theta":theta,"vega":vega}
    except: return None

def analyze_all(df5, curr):
    close=df5['Close']; high=df5['High']; low=df5['Low']; vol=df5['Volume']
    if len(close)<60: return None
    ema9=close.ewm(span=9).mean().iloc[-1]
    ema20=close.ewm(span=20).mean().iloc[-1]
    typical=(high+low+close)/3
    vwap=(typical*vol).cumsum()/vol.cumsum()
    vwap_n=float(vwap.iloc[-1])
    delta_c=close.diff()
    gain=delta_c.where(delta_c>0,0).rolling(14).mean()
    loss=-delta_c.where(delta_c<0,0).rolling(14).mean()
    rsi=100-(100/(1+gain/loss.replace(0,0.001)))
    rsi_n=float(rsi.iloc[-1])
    sma20=close.rolling(20).mean()
    std20=close.rolling(20).std()
    bw=(sma20+2*std20 - (sma20-2*std20))/sma20
    bw_n=float(bw.iloc[-1])
    demand=float(low.tail(20).min())
    supply=float(high.tail(20).max())
    avg_v=vol.rolling(20).mean().iloc[-1]
    vol_exp=float(vol.iloc[-1]) > avg_v*1.7
    squeeze=bw_n<0.045
    elliott_bull=(curr>ema9>ema20) and (ema9>vwap_n) and (55<rsi_n<78)
    elliott_bear=(curr<ema9<ema20) and (ema9<vwap_n) and (22<rsi_n<45)
    direction="CALL" if elliott_bull else "PUT" if elliott_bear else None
    score=0; reasons=[]
    if elliott_bull or elliott_bear: score+=25; reasons.append("اليوت موجة 3")
    if squeeze: score+=20; reasons.append(f"Squeeze {bw_n*100:.1f}%")
    if vol_exp: score+=20; reasons.append("حجم انفجاري")
    if abs(curr-vwap_n)/curr<0.012: score+=10; reasons.append("قريب VWAP")
    return {"vwap":vwap_n,"ema9":ema9,"ema20":ema20,"rsi":rsi_n,"bw":bw_n,"demand":demand,"supply":supply,"direction":direction,"score":score,"reasons":reasons,"squeeze":squeeze,"vol_exp":vol_exp,"breakout":supply*1.002 if direction=="CALL" else demand*0.998,"reversal":vwap_n}

st.title("👑 بوت الحوت 54 - النهائي المدمج V500")
st.info(f"اليوم: {today_sa} | نيويورك: {now_et.strftime('%H:%M')} | مدمج: تاريخ+Vol+OI+يونانيات+وقت+انفجار+اليوت+عرض/طلب")

def get_final_merged(sym):
    try:
        tk=yf.Ticker(sym)
        hist5=tk.history(period="5d", interval="5m")
        hist1=tk.history(period="2d", interval="1d")
        if hist5.empty: return None
        curr=float(hist5['Close'].iloc[-1])
        prev=float(hist1['Close'].iloc[-2]) if len(hist1)>1 else curr
        pre=float((curr-prev)/prev*100)

        # ===== شروطك القديمة المدمجة 1: بري ماركت 0.2% الى 3.2% (مبكر) =====
        if abs(pre) < 0.20 or abs(pre) > 3.2: return None

        tech=analyze_all(hist5, curr)
        if not tech or not tech['direction']: return None
        # ===== شروطك القديمة 2: انفجار سكور 55+ =====
        if tech['score'] < 55: return None

        # ===== شروطك القديمة 3: تاريخ من بكره وطالع (مستحيل قديم) =====
        valid=[]
        for e in tk.options:
            try:
                d=datetime.strptime(e, "%Y-%m-%d").date()
                days=(d-today_sa).days
                # ===== حساب الوقت: 1 الى 14 يوم فقط (امثل للانفجار) =====
                if d > today_sa and 1 <= days <= 14:
                    valid.append((e,days))
            except: continue
        if not valid: return None
        valid.sort(key=lambda x: x[1])

        best=None
        for exp, days in valid[:2]:
            T=days/365.0
            chain=tk.option_chain(exp)
            df=chain.calls if tech['direction']=="CALL" else chain.puts
            df=df.copy()

            # ===== شروطك القديمة 4: Vol + OI =====
            df=df[(df['bid']>=0.45) & (df['bid']<=3.8) & (df['volume'].fillna(0)>=500) & (df['openInterest'].fillna(0)>=500)]
            if df.empty: continue
            # ===== شرط جديد: Vol انفجاري حوت حقيقي =====
            df=df[df['volume'] > df['openInterest']*0.65]
            if df.empty: continue
            # ===== شروطك القديمة 5: قريب من السعر 7% =====
            df['dist']=abs(df['strike']-curr)/curr
            df=df[df['dist']<=0.07]
            if df.empty: continue
            # ===== شرط جديد: رخيص ما ارتفع =====
            df=df[df['lastPrice'] <= df['bid']*1.9]
            if df.empty: continue
            df=df.nsmallest(10,'dist')

            for _,row in df.iterrows():
                iv=float(row['impliedVolatility'])
                if iv<0.18 or iv>2.5: continue
                greeks=calc_greeks(curr,float(row['strike']),T,iv,tech['direction'])
                if not greeks: continue

                # ===== حساب اليونانيات + الوقت المدمج =====
                # دلتا مثالية
                if not (0.38 <= abs(greeks['delta']) <= 0.64): continue
                # ثيتا خفيفة (حساب الوقت: ما يخسر كثير كل يوم)
                if greeks['theta'] < -0.12: continue
                # فيغا وغاما
                if greeks['vega'] < 0.02: continue
                if greeks['gamma'] < 0.008: continue
                # Spread ضيق
                spread=(float(row['ask'])-float(row['bid']))/float(row['bid']) if float(row['bid'])>0 else 1
                if spread>0.20: continue

                # ===== سكور نهائي يحسب كل شي + الوقت =====
                # كل ما قل الوقت زاد الثيتا خطر، نعطي افضلية 2-7 ايام
                time_bonus = 10 if 2 <= days <= 7 else 0
                final_score = tech['score'] + abs(greeks['delta'])*40 + greeks['gamma']*120 + greeks['vega']*10 - abs(greeks['theta'])*15 + (row['volume']/row['openInterest'])*12 + time_bonus - spread*30

                cand={
                    "symbol":sym,"side":tech['direction'],"pre":pre,"curr":curr,"exp":exp,"days":days,
                    "strike":row['strike'],"bid":float(row['bid']),"ask":float(row['ask']),"vol":int(row['volume']),"oi":int(row['openInterest']),
                    "iv":iv,"delta":greeks['delta'],"gamma":greeks['gamma'],"theta":greeks['theta'],"vega":greeks['vega'],
                    "spread":spread,"tech":tech,"score":final_score,
                    "status": "🔥 طالع 90%" if final_score>=88 else "🚀 صاعد 80%" if final_score>=75 else "⏳ مراقبة"
                }
                if best is None or cand['score'] > best['score']:
                    best=cand
        return best if best and best['score']>=72 else None
    except: return None

if st.button("🔍 فحص نهائي مدمج - 7 طبقات + يونانيات + وقت", type="primary", use_container_width=True):
    results=[]
    prog=st.progress(0)
    for i,s in enumerate(STOCKS_54):
        prog.progress((i+1)/len(STOCKS_54), text=s)
        d=get_final_merged(s)
        if d: results.append(d)
    prog.empty()
    results.sort(key=lambda x: x['score'], reverse=True)
    results=results[:5]
    st.session_state['res']=results

    if not results:
        st.error("اليوم ما فيه عقد يجمع كل الشروط - السوق هادي")
    else:
        st.success(f"لقي {len(results)} عقود تجمع كل شروطك ✅")
        msgs=[]
        for r in results:
            t=r['tech']
            emoji="🟢" if r['side']=="CALL" else "🔴"
            stxt=int(r['strike']) if r['strike']==int(r['strike']) else r['strike']
            # نفس ستايلك القديم + كل الاضافات
            msg=f"""{r['status']} {emoji} {r['symbol']} {stxt} {r['side']} PRE {r['pre']:.2f}% | Δ{abs(r['delta']):.2f} Γ{r['gamma']:.3f} Θ{r['theta']:.3f} V{r['vega']:.3f}
Exp: {r['exp']} ({r['days']}d) Stock: ${r['curr']:.2f} IV:{r['iv']*100:.0f}% Spread:{r['spread']*100:.0f}%
Entry: ${r['bid']:.2f} Bid: ${r['bid']:.2f} Vol: {r['vol']} OI: {r['oi']} Vol/OI:{r['vol']/r['oi']:.1f}x
{', '.join(t['reasons'])} | VWAP:${t['vwap']:.2f} RSI:{t['rsi']:.0f} {'SQUEEZE' if t['squeeze'] else ''}
طلب: ${t['demand']:.2f} | عرض: ${t['supply']:.2f} | انفجار: ${t['breakout']:.2f} | انعكاس: ${t['reversal']:.2f}
Stop: ${r['bid']*0.60:.2f} | Target: ${r['bid']*1.8:.2f} (+80%) | ${r['bid']*2.8:.2f} (+180%) | ${r['bid']*4.5:.2f} (+350%)
وقت مثالي: {r['days']} يوم - ثيتا {r['theta']:.3f}/يوم"""
            msgs.append(msg)
            st.code(msg)
            if r['score']>=88:
                st.balloons()
                st.success(f"✅ {r['symbol']} - هذا العقد طالع - كل الشروط مجتمعة + وقت مثالي")
        if msgs:
            st.session_state['history'].append({"time":datetime.now(riyadh).strftime("%m-%d %H:%M"),"count":len(msgs),"preview":msgs[0][:200],"msgs":msgs})

if 'res' in st.session_state and st.session_state['res']:
    st.divider()
    if st.button("📤 ارسل النهائي المدمج لتلجرام", type="primary", use_container_width=True):
        c=0
        for r in st.session_state['res']:
            emoji="🟢" if r['side']=="CALL" else "🔴"
            msg=f"{r['status']} {emoji} {r['symbol']} {r['strike']} {r['side']} Δ{abs(r['delta']):.2f} {r['days']}d Θ{r['theta']:.3f} نقاط {r['score']:.0f}"
            try:
                if requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id":CHAT_ID,"text":msg}, timeout=10).status_code==200: c+=1
            except: pass
        st.success(f"تم ارسال {c} ✅")
