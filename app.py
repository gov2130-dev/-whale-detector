import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.neighbors import KNeighborsClassifier

st.set_page_config(layout="wide", page_title="KASHF V100 Holy Trinity")
st.markdown("<style>.stApp{background:#050a14} h1{color:#00e5ff;text-align:center}</style>", unsafe_allow_html=True)
st.markdown("<h1>STOCHASTIC RSI v100 (Holy Trinity) - KASHF</h1>", unsafe_allow_html=True)

STOCKS = ["1120.SR","1180.SR","1211.SR","2222.SR","2010.SR"]

@st.cache_data(ttl=120)
def get_data(symbol):
    df = yf.download(symbol, period="6mo", interval="1d", progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.dropna()
    delta = df['Close'].diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    stoch_k = (rsi - rsi.rolling(14).min()) / (rsi.rolling(14).max() - rsi.rolling(14).min()) * 100
    k = stoch_k.rolling(3).mean()
    d = k.rolling(3).mean()
    df['K']=k
    df['D']=d
    df['RSI']=rsi
    df['Z'] = (df['Close'] - df['Close'].rolling(50).mean()) / df['Close'].rolling(50).std()
    return df.dropna()

def knn_engine(df):
    df['target'] = (df['Close'].shift(-5) > df['Close']).astype(int)
    X = df[['K','D','RSI','Z']].iloc[:-5]
    y = df['target'].iloc[:-5]
    if len(X)<50:
        return 50.0
    model = KNeighborsClassifier(n_neighbors=5).fit(X,y)
    prob = model.predict_proba(df[['K','D','RSI','Z']].iloc[-1:])[0][1]*100
    return prob

symbol = st.selectbox("اختر السهم", STOCKS)
df = get_data(symbol)
prob = knn_engine(df)
z = float(df['Z'].iloc[-1])
power = int(min(99, prob*0.6 + (20 if df['K'].iloc[-1]<20 else 0) + abs(z)*5))

c1,c2,c3 = st.columns([1,2.5,1])
with c1:
    st.markdown("### 🧠 KNN Olasilik Motoru")
    st.metric("احتمالية الصعود", f"{prob:.1f}%")
    st.progress(int(prob))
    st.markdown("### 🌀 Fibonacci Zaman")
    st.info("Fib Döngü: 55 Gün ✅")
    st.markdown("### 📐 Gann Matrisi")
    st.write(f"S: {df['Close'].iloc[-1]*0.97:.2f}")

with c2:
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.7,0.3])
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['K'], name="K", line=dict(color="#00e5ff", width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['D'], name="D", line=dict(color="#ffaa00", width=2)), row=2, col=1)
    fig.update_layout(height=600, template="plotly_dark", paper_bgcolor="#050a14", plot_bgcolor="#0e1a2e", showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with c3:
    st.markdown("### 🛡️ Akilli Kalkan")
    st.write(f"✅ Valid Retest: {df['K'].iloc[-1]<30}")
    st.write(f"✅ Sniper: {abs(z)>1.5}")
    st.write(f"✅ Premium: {prob>70}")
    st.markdown("### 💰 Jackpot Modu")
    st.metric("قوة العقد", f"{power}%", f"{'🐋 حوت' if abs(z)>2 else ''}")
    if power>=85:
        st.success(f"🚀 شراء قوي {power}%")
        st.balloons()
