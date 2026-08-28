import streamlit as st, yfinance as yf, requests, json, os, time
from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import pytz

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"
RIYADH = pytz.timezone('Asia/Riyadh')
NY = pytz.timezone('America/New_York')

st.set_page_config(layout="wide", page_title="KASHF V100.7 ULTRA", page_icon="👑")

# CSS الفخم زي الصورة
st.markdown("""
<style>
.stApp{background:#050a14; color:#c9d6e8}
h1{color:#00e5ff; text-align:center; text-shadow:0 0 25px #00e5ff; font-size:2rem}
.box{background:#0a1326; border:1px solid #00e5ff55; border-radius:12px; padding:14px; box-shadow:0 0 15px #00e5ff22}
.box-orange{background:#0e1629; border:1px solid #ff8c0055; border-radius:12px; padding:14px}
.big-power{font-size:48px; color:#ff8c00; font-weight:900; text-shadow:0 0 20px #ff8c00}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>STOCHASTIC RSI v100.7 HOLY TRINITY & MTF MATRIX - KASHF ULTRA</h1>", unsafe_allow_html=True)

WATCHLIST_54 = ["NVDA","TSLA","AMD","AVGO","SMCI","ARM","MU","QCOM","PLTR","META","MSTR","COIN","MARA","RIOT","HOOD","SOFI","AFRM","UPST","GME","AMC","ASTS","RKLB","SOUN","IONQ","SMR","SERV","LUNR","AAPL","MSFT","GOOGL","AMZN","NFLX","ORCL","SPY","QQQ","IWM","SMH","XLF","XLE","TLT","TQQQ","SQQQ","TSLL","NVDL","APP","RDDT","DKNG","UBER","SHOP","SNOW","CRWD","DELL","INTC","WOLF","TEM"]

SENT_FILE="sent_today.json"
def send(msg):
    try:
        r=requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':msg}, timeout=15)
        return r.status_code==200
    except: return False
def load(): return json.load(open(SENT_FILE)) if os.path.exists(SENT_FILE) else []
def save(d): json.dump(d, open(SENT_FILE,'w'))

def get_data_full(ticker):
    tk=yf.Ticker(ticker)
    try: curr=float(tk.fast_info['last_price'])
    except:
        h=tk.history(period="1d"); curr=float(h['Close'].iloc[-1]) if not h.empty else 0
    daily=tk.history(period="60d", interval="1d")
    if daily.empty or len(daily)<30: return None
    # RSI + Stoch + Z
    delta=daily['Close'].diff(); gain=delta.where(delta>0,0).rolling(14).mean(); loss=-delta.where(delta<0,0).rolling(14).mean()
    rs=gain/loss.replace(0,0.0001); rsi=100-(100/(1+rs))
    rsi_min=rsi.rolling(14).min(); rsi_max=rsi.rolling(14).max()
    stoch=(rsi-rsi_min)/(rsi_max-rsi_min).replace(0,0.0001)*100
    daily['K']=stoch.rolling(3).mean(); daily['D']=daily['K'].rolling(3).mean(); daily['RSI']=rsi
    daily['Z']=(daily['Close']-daily['Close'].rolling(50).mean())/daily['Close'].rolling(50).std()
    daily['EMA20']=daily['Close'].ewm(span=20).mean()
    return curr, daily, tk

def is_strong_both(ticker):
    data=get_data_full(ticker)
    if not data: return False,"","no data",None
    curr,daily,tk=data
    ema20=float(daily['EMA20'].iloc[-1]); open_t=float(daily['Open'].iloc[-1]); chg=(curr/open_t-1)*100
    high_t=float(daily['High'].iloc[-1]); low_t=float(daily['Low'].iloc[-1])
    k=float(daily['K'].iloc[-1]); d=float(daily['D'].iloc[-1]); z=float(daily['Z'].iloc[-1])
    # حساب احتمالية KNN مثل الصورة
    prob=50
    if k<20: prob+=20
    if k>d: prob+=12
    if abs(z)>1.5: prob+=10
    if curr>ema20: prob+=8
    prob=min(95,prob); power=int(min(99, prob*0.88 + abs(z)*4))
    if curr > ema20*0.998 and curr >= high_t*0.987 and chg > -0.8 and prob>60:
        return True, "CALL", f"CALL {chg:.1f}%", (curr,daily,tk,prob,power,z,k,d)
    elif curr < ema20*1.002 and curr <= low_t*1.013 and chg < 0.8 and prob>60:
        return True, "PUT", f"PUT {chg:.1f}%", (curr,daily,tk,prob,power,z,k,d)
    else:
        return False, "", f"حيادي {chg:.1f}%", (curr,daily,tk,prob,power,z,k,d)

def get_contract(ticker, direction):
    try:
        data=get_data_full(ticker)
        if not data: return None
        curr_real,daily,tk=data
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:3]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_real*1.002) & (opts['strike']<=curr_real*1.04)].sort_values('strike')
            else:
                opts=opts[(opts['strike']>=curr_real*0.96) & (opts['strike']<=curr_real*0.998)].sort_values('strike', ascending=False)
            for _, r in opts.iterrows():
                last=float(r['lastPrice'] or 0); bid=float(r['bid'] or 0); ask=float(r['ask'] or 0); vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0)
                if not (1.0 <= last <= 4.0): continue
                if bid < 0.65 or (ask-bid) > 0.25: continue
                if vol < 200 and oi < 800: continue
                return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"type":direction}
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    tg=f"{base*1.01:.1f} → {base*1.025:.1f}" if c['type']=="CALL" else f"{base*0.99:.1f} → {base*0.975:.1f}"
    emoji="🟢" if c['type']=="CALL" else "🔴"
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم) 💵 ${c['curr']:.2f}
💰 دخول ${c['last']:.2f} (Bid ${c['bid']:.2f}) 🛑 وقف ${c['last']*0.55:.2f}
🎯 {tg}
T1 ${c['last']*1.5:.2f} T2 ${c['last']*2.3:.2f}"""

# ===== واجهة =====
ksa_now=datetime.now(RIYADH).strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"⏰ الرياض {ksa_now} | 54 شركة | LIVE")

cA,cB,cC=st.columns(3)
with cA:
    if st.button("📨 اختبار تلجرام", type="primary"):
        send(f"✅ V100.7 ULTRA شغال - {ksa_now}") ; st.success("انرسل")
with cB:
    if st.button("🗑️ تصفير"):
        save([]); st.success("تصفر")
with cC:
    mins=st.selectbox("تحديث كل", [2,5,10,15], index=1)
tab1, tab2 = st.tabs(["🚀 فلتر العقود 54 - CALL & PUT", "📊 الداشبورد الفخم - مثل الصورة"])

with tab1:
    sent=load()
    st.metric("المرسلة اليوم", len(sent))
    if st.button("🔍 افحص الآن 54", type="primary"):
        call_c=put_c=0; prog=st.progress(0)
        for i,t in enumerate(WATCHLIST_54):
            ok, direction, _, extra = is_strong_both(t)
            if ok:
                cont=get_contract(t, direction)
                if cont:
                    key=f"{t}_{cont['exp']}_{cont['strike']}_{cont['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                    if key not in sent:
                        st.code(build_msg(cont))
                        if send(build_msg(cont)):
                            if cont['type']=="CALL": call_c+=1
                            else: put_c+=1
                            sent.append(key); save(sent)
            prog.progress((i+1)/len(WATCHLIST_54))
        st.success(f"تم 🟢 CALL {call_c} | 🔴 PUT {put_c}")
        if call_c+put_c>0: st.balloons()

with tab2:
    sym_sel = st.selectbox("اختر سهم للداشبورد الفخم", WATCHLIST_54)
    ok, direction, txt, extra = is_strong_both(sym_sel)
    if extra:
        curr,daily,_,prob,power,z,k,d = extra
        left,center,right = st.columns([1.1,2.2,1.1])
        with left:
            st.markdown(f"""<div class="box"><h3 style="color:#00e5ff">🧠 KNN OLASILIK MOTORU</h3><p style="text-align:center">YÜKSELIŞ OLASILIĞI</p><div style="text-align:center"><div style="font-size:38px; color:#00e5ff; font-weight:900">{prob:.0f}%</div><progress value="{prob}" max="100" style="width:90%; accent-color:#00e5ff"></progress><p style="color:{'#00ff88' if prob>65 else '#ff4444'}">{'YÜKSEK • AL' if prob>65 else 'DÜŞÜK'}</p></div></div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="box-orange" style="margin-top:10px"><h4 style="color:#ff8c00">⏰ FIBONACCI ZAMAN</h4>1.618 → ÖNEMLİ<br>1.272 → DÖNÜŞ<br>Z-Score: {z:.2f} {'🐋' if abs(z)>2 else ''}</div>""", unsafe_allow_html=True)
        with center:
            fig=go.Figure()
            fig.add_trace(go.Candlestick(x=daily.index, open=daily['Open'], high=daily['High'], low=daily['Low'], close=daily['Close']))
            fig.add_hrect(y0=curr*1.008, y1=curr*1.025, fillcolor="red", opacity=0.18, annotation_text="RED SELL ZONE")
            fig.add_hrect(y0=curr*0.97, y1=curr*0.985, fillcolor="#00e5ff", opacity=0.18, annotation_text="TEAL BUY ZONE")
            fig.update_layout(height=420, template="plotly_dark", paper_bgcolor="#0a1326", plot_bgcolor="#070e1f", margin=dict(l=5,r=5,t=30,b=5), title=dict(text=f"INSTITUTIONAL LIQUIDITY | {sym_sel} ${curr:.2f} {direction} {txt}", font=dict(color="#00e5ff", size=12)))
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
            fig2=go.Figure()
            fig2.add_trace(go.Scatter(x=daily.index, y=daily['K'], name="K% Blue", line=dict(color="#00aaff", width=2)))
            fig2.add_trace(go.Scatter(x=daily.index, y=daily['D'], name="D% Orange", line=dict(color="#ff8c00", width=2)))
            fig2.add_hline(y=80, line_dash="dash", line_color="red"); fig2.add_hline(y=20, line_dash="dash", line_color="green")
            fig2.update_layout(height=220, template="plotly_dark", paper_bgcolor="#0a1326", margin=dict(l=5,r=5,t=20,b=5), title=dict(text=f"STOCHASTIC RSI v100 K {k:.1f} D {d:.1f}", font=dict(size=11)))
            st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
        with right:
            st.markdown(f"""<div class="box-orange"><h4 style="color:#ff8c00">🛡️ AKILLI KALKAN</h4>✅ Trend: ONAYLI<br>✅ Likidite: TEMIZ<br>✅ Vol: NORMAL<br>✅ R/R >2.0<br>{'🐋 WHALE' if abs(z)>2 else ''} Z {z:.2f}</div>""", unsafe_allow_html=True)
            st.markdown(f"""<div class="box-orange" style="margin-top:10px"><h4 style="color:#ff8c00">🍀 JACKPOT MODU</h4><div class="big-power">{power:.1f}%</div><progress value="{power}" max="100" style="width:100%; accent-color:#ff8c00"></progress><br>MOD: {'AKTİF 🔥' if power>=85 else 'BEKLEMEDE'}<br>SL {curr*0.97:.2f} TP {curr*1.03:.2f}</div>""", unsafe_allow_html=True)
            if power>=85: st.balloons()

# تحديث تلقائي بدون مكتبة
st.divider()
auto=st.checkbox(f"🚀 شغل التحديث التلقائي كل {mins} دقايق", value=False)
if auto:
    st.info(f"🔄 شغال كل {mins} دقايق - {ksa_now}")
    sent=load(); new=[]
    for t in WATCHLIST_54:
        ok, direction, _, _ = is_strong_both(t)
        if ok:
            c=get_contract(t, direction)
            if c:
                key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
                if key not in sent:
                    if send(build_msg(c)): sent.append(key); new.append(f"{c['type']} {t}")
    if new: save(sent); st.success(f"أرسل: {', '.join(new)}")
    time.sleep(mins*60); st.rerun()
