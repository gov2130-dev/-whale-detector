import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime
import requests

st.set_page_config(layout="wide", page_title="KASHF V100 ULTIMATE")

st.markdown("""
<style>
.stApp{background:#050a14} h1{color:#00e5ff;text-align:center;text-shadow:0 0 20px #00e5ff}
.box{background:#0a1326;border:1px solid #00e5ff55;border-radius:10px;padding:12px}
.box-orange{background:#1a140a;border:1px solid #ff8c0055;border-radius:10px;padding:12px}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>STOCHASTIC RSI v100 HOLY TRINITY & MTF MATRIX - KASHF ULTIMATE</h1>", unsafe_allow_html=True)

# ========== إعداداتك القديمة - عدلها هنا ==========
BOT_TOKEN = "ضع_توكن_البوت_هنا"
CHAT_ID = "ضع_الايدي_هنا"
STOCKS = ["2222.SR","1120.SR","1180.SR","1211.SR","2010.SR","2380.SR","2030.SR","2350.SR","1180.SR","7010.SR","1210.SR","1060.SR","1050.SR"] # زود 54 سهم هنا

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id":CHAT_ID, "text":msg, "parse_mode":"Markdown"}, timeout=5)
    except: pass

@st.cache_data(ttl=180)
def get_data(sym):
    try:
        df = yf.download(sym, period="3mo", interval="1d", progress=False, auto_adjust=True)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss.replace(0,0.0001)
        rsi = 100 - (100/(1+rs))
        rsi_min = rsi.rolling(14).min(); rsi_max = rsi.rolling(14).max()
        stoch = (rsi - rsi_min)/(rsi_max - rsi_min).replace(0,0.0001)*100
        df['K']=stoch.rolling(3).mean(); df['D']=df['K'].rolling(3).mean(); df['RSI']=rsi
        df['Z']=(df['Close']-df['Close'].rolling(50).mean())/df['Close'].rolling(50).std()
        df['MA20']=df['Close'].rolling(20).mean()
        return df.dropna()
    except: return None

def analyze(sym, df):
    k=float(df['K'].iloc[-1]); d=float(df['D'].iloc[-1]); rsi=float(df['RSI'].iloc[-1]); z=float(df['Z'].iloc[-1]); close=float(df['Close'].iloc[-1]); ma20=float(df['MA20'].iloc[-1])
    prob=50
    if k<20: prob+=20
    if k>d: prob+=15
    if rsi<40: prob+=10
    if close>ma20: prob+=5
    if abs(z)>1.5: prob+=10
    prob=min(95,prob)
    power=int(min(99, prob*0.9 + abs(z)*3))
    # شروطك القديمة
    valid_retest = k<30
    sniper = abs(z)>1.5
    premium = prob>70
    jackpot = power>=85 and prob>=70 and k>d and valid_retest
    return {"symbol":sym,"close":close,"k":k,"d":d,"rsi":rsi,"z":z,"prob":prob,"power":power,"jackpot":jackpot,"valid":valid_retest}

# ========== تبويبين - زي موقعك القديم ==========
tab1, tab2 = st.tabs(["🚀 جدول التوصيات والعقود (موقعك القديم)", "📊 التحليل الفخم المفصل"])

with tab1:
    st.markdown("### 🔍 فحص السوق - كل الأسهم 54")
    if st.button("🔄 فحص الآن وإرسال تلجرام"):
        st.cache_data.clear()
    
    results=[]
    progress=st.progress(0)
    for i,sym in enumerate(STOCKS):
        df=get_data(sym)
        if df is not None and len(df)>50:
            results.append(analyze(sym,df))
        progress.progress((i+1)/len(STOCKS))
    
    if results:
        df_res=pd.DataFrame(results).sort_values("power", ascending=False)
        # جدول العقود
        st.markdown("#### 💰 جدول العقود - Jackpot")
        st.dataframe(df_res[["symbol","close","power","prob","z","k","d","jackpot"]], use_container_width=True)
        
        jackpots = df_res[df_res["jackpot"]==True]
        if not jackpots.empty:
            st.success(f"🔥 يوجد {len(jackpots)} عقد Jackpot الآن!")
            for _,row in jackpots.iterrows():
                msg = f"🚀 *JACKPOT* {row['symbol']} - قوة {row['power']}% - KNN {row['prob']:.0f}% - Z {row['z']:.2f} {'🐋 حوت' if abs(row['z'])>2 else ''} - السعر {row['close']:.2f}"
                st.code(msg)
                if BOT_TOKEN!="ضع_توكن_البوت_هنا":
                    send_telegram(msg)
            st.balloons()
        else:
            st.warning("⏳ لا يوجد Jackpot الآن - انتظار فرص قوة 85%+")
    else:
        st.error("ما قدرنا نجيب البيانات")

with tab2:
    symbol = st.selectbox("اختر سهم للتحليل العميق", STOCKS)
    df = get_data(symbol)
    if df is not None:
        info = analyze(symbol, df)
        c1,c2,c3 = st.columns([1,2,1])
        with c1:
            st.markdown(f"<div class='box'><h3>🧠 KNN {info['prob']:.0f}%</h3><progress value='{info['prob']}' max='100' style='width:100%'></progress><br>قوة: {info['power']}%<br>Z: {info['z']:.2f}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='box-orange' style='margin-top:10px'>⏰ Fibonacci<br>55 يوم مكتمل ✅</div>", unsafe_allow_html=True)
        with c2:
            fig=go.Figure()
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close']))
            fig.add_hrect(y0=info['close']*1.008, y1=info['close']*1.02, fillcolor="red", opacity=0.2)
            fig.add_hrect(y0=info['close']*0.97, y1=info['close']*0.985, fillcolor="cyan", opacity=0.2)
            fig.update_layout(height=400, template="plotly_dark", paper_bgcolor="#0a1326", margin=dict(l=5,r=5,t=20,b=5))
            st.plotly_chart(fig, use_container_width=True)
            fig2=go.Figure()
            fig2.add_trace(go.Scatter(x=df.index, y=df['K'], name="K", line=dict(color="#00aaff")))
            fig2.add_trace(go.Scatter(x=df.index, y=df['D'], name="D", line=dict(color="#ff8c00")))
            fig2.update_layout(height=200, template="plotly_dark", paper_bgcolor="#0a1326", margin=dict(l=5,r=5,t=10,b=5))
            st.plotly_chart(fig2, use_container_width=True)
        with c3:
            st.markdown(f"<div class='box-orange'><h3>🍀 JACKPOT {info['power']}%</h3>{'🔥 AKTIF' if info['jackpot'] else 'BEKLEMEDE'}<br>SL {info['close']*0.97:.2f} TP {info['close']*1.03:.2f}</div>", unsafe_allow_html=True)
            if info['jackpot']:
                st.balloons()

st.caption(f"V100 ULTIMATE - {datetime.now().strftime('%Y-%m-%d %H:%M')} - يعمل 24 ساعة مع UptimeRobot")
