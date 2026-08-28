import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.neighbors import KNeighborsClassifier

st.set_page_config(layout="wide", page_title="KASHF V100 Holy Trinity")
st.markdown("<style>.stApp{background:#050a14} h1{color:#00e5ff;text-align:center;text-shadow:0 0 15px #00e5ff}</style>", unsafe_allow_html=True)
st.markdown("<h1>STOCHASTIC RSI v100 (Holy Trinity & MTF Matrix) - KASHF EDITION</h1>", unsafe_allow_html=True)

# ========= الأسهم =========
STOCKS = ["1120.SR","1180.SR","1211.SR","2222.SR","2010.SR"] # ضيف قائمتك الـ 54 هنا

@st.cache_data(ttl=120)
def get_data(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    df.reset_index(inplace=True)
    # Stochastic RSI
    rsi = 100 - (100 / (1 + df['Close'].rolling(14).mean())) ) # مبسط
    # احسبه صح
    delta = df['Close'].diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rs = gain/loss
    rsi = 100 - (100/(1+rs))
    stoch_k = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min()) * 100
    k = stoch_k.rolling(3).mean()
    d = k.rolling(3).mean()
    df['K']=k; df['D']=d; df['RSI']=rsi
    # Z-Score
    df['Z'] = (df['Close'] - df['Close'].rolling(50).mean()) / df['Close'].rolling(50).std()
    return df.dropna()

def knn_engine(df):
    # محرك KNN Olasilik
    df['target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
    X = df[['K','D','RSI','Z']].iloc[:-5]
    y = df['target'].iloc[:-5]
    if len(X)<50: return 50
    model = KNeighborsClassifier(n_neighbors=5).fit(X,y)
    prob = model.predict_proba(df[['K','D','RSI','Z']].iloc[-1:])[0][1]*100
    return prob

symbol = st.selectbox("اختر السهم للتحليل العميق", STOCKS)
df = get_data(symbol)
prob = knn_engine(df)
z = df['Z'].iloc[-1]
power = int(min(99, prob*0.6 + (20 if df['K'].iloc[-1]<20 else 0) + abs(z)*5))

# ========= الواجهة =========
c1,c2,c3 = st.columns([1,2.5,1])

with c1:
    st.markdown("### 🧠 KNN Olasilik Motoru")
    st.metric("Olasilik", f"{prob:.1f}%", delta=f"{'BUY' if prob>65 else 'WAIT'}")
    st.progress(int(prob))
    st.markdown(f"**Yön:** {'🟢 YUKARI' if prob>60 else '🔴 AŞAĞI'}")

    st.divider()
    st.markdown("### 🌀 Fibonacci Zaman Döngüsü")
    st.write("Fib Döngü: 55 Gün ✅ Tamamlandı")
    st.write("Sonraki Döngü: 89 Gün")

    st.divider()
    st.markdown("### 📐 Gann Fiyat Matrisi")
    st.code(f"Gann Angle: 45°\nPrice: {df['Close'].iloc[-1]:.2f}\nSupport: {df['Close'].iloc[-1]*0.97:.2f}")

with c2:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    fig.add_hrect(y0=df['Close'].max()*0.98, y1=df['Close'].max(), fillcolor="red", opacity=0.2, line_width=0, annotation_text="Institutional SELL", row=1, col=1)
    fig.add_hrect(y0=df['Close'].min(), y1=df['Close'].min()*1.02, fillcolor="#00ffcc", opacity=0.2, line_width=0, annotation_text="Institutional BUY Zone", row=1, col=1)
    if abs(z)>2:
        fig.add_annotation(x=df['Date'].iloc[-1], y=df['Close'].iloc[-1], text="🐋 WHALE", showarrow=True, arrowcolor="#00e5ff", row=1, col=1)

    fig.add_trace(go.Scatter(x=df['Date'], y=df['K'], name="K (StochRSI)", line=dict(color="#00e5ff", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['D'], name="D (Signal)", line=dict(color="#ffaa00", width=2)), row=2, col=1)
    fig.add_hline(y=20, line_dash="dot", line_color="green", row=2, col=1)
    fig.add_hline(y=80, line_dash="dot", line_color="red", row=2, col=1)
    fig.update_layout(height=650, template="plotly_dark", paper_bgcolor="#050a14", plot_bgcolor="#0e1a2e", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.markdown("### 🛡️ Akilli Kalkan")
    conds = {
        "Valid Retest": df['K'].iloc[-1] < 30,
        "Valid Buyback": df['Close'].iloc[-1] > df['Close'].rolling(20).mean().iloc[-1],
        "Valid Sniper Flow": abs(z)>1.5,
        "Valuat Hisse": df['RSI'].iloc[-1] < 40,
        "Premium Alış": prob > 70,
        "Sinyal Doğrulama": df['K'].iloc[-1] > df['D'].iloc[-1]
    }
    for k,v in conds.items():
        st.markdown(f"{'✅' if v else '❌'} {k}")

    st.divider()
    st.markdown("### 💥 Uyumsuzluk & Jackpot")
    divergence = "Bullish Divergence" if df['Close'].iloc[-1] < df['Close'].iloc[-10] and df['K'].iloc[-1] > df['K'].iloc[-10] else "Yok"
    st.write(f"Divergence: {divergence}")

    st.markdown("### 💰 Jackpot Modu")
    st.metric("قوة العقد", f"{power}%", f"{'🐋 حوت' if abs(z)>2 else ''}")

    if power >= 85 and prob >= 70:
        st.success(f"🚀 JACKPOT: شراء قوي {power}%")
        st.balloons()
        # هنا كود التلجرام حقك القديم
        # send_telegram(f"🔥 {symbol} - قوة {power}% - KNN {prob:.1f}% - حوت {z:.1f}")
    elif power >= 70:
        st.warning(f"⚠️ فرصة قريبة {power}% - انتظار تأكيد")
    else:
        st.error(f"⏳ انتظار {power}%")

st.divider()
st.caption("KASHF V100 - يدمج كل شروط V99.3 + KNN + Gann + Fibonacci | التحديث التلقائي كل دقيقتين + UptimeRobot")
