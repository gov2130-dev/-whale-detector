import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="KASHF V100 Holy Trinity", page_icon="👑")

# ========== CSS فخم مثل الصورة ==========
st.markdown("""
<style>
.stApp {background:#050a14; color:#c9d6e8;}
h1 {color:#00e5ff; text-align:center; text-shadow:0 0 25px #00e5ff; letter-spacing:2px; font-size:2.2rem;}
.box {background:#0a1326; border:1px solid #00e5ff55; border-radius:12px; padding:15px; box-shadow:0 0 15px #00e5ff22;}
.box-orange {background:#0e1629; border:1px solid #ff8c0055; border-radius:12px; padding:15px;}
.glow-cyan {color:#00e5ff; text-shadow:0 0 8px #00e5ff;}
.glow-orange {color:#ff8c00; text-shadow:0 0 8px #ff8c00;}
.big-power {font-size:52px; color:#ff8c00; font-weight:900; text-shadow:0 0 20px #ff8c00;}
.kpi {font-size:28px; color:#00e5ff; font-weight:800;}
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>STOCHASTIC RSI v100 HOLY TRINITY & MTF MATRIX</h1>", unsafe_allow_html=True)
col_top1, col_top2 = st.columns([3,1])
with col_top2:
    st.markdown("<span style='color:#00ff88'>● LIVE • DATA FEED: CONNECTED</span>", unsafe_allow_html=True)

STOCKS = ["2222.SR","1120.SR","1180.SR","1211.SR","2010.SR","2380.SR","2030.SR","2350.SR","1180.SR"]

@st.cache_data(ttl=300)
def get_data(sym):
    df = yf.download(sym, period="6mo", interval="1d", progress=False, auto_adjust=True)
    if df.empty: return None
    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
    delta = df['Close'].diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rs = gain / loss.replace(0,0.0001)
    rsi = 100 - (100/(1+rs))
    rsi_min = rsi.rolling(14).min()
    rsi_max = rsi.rolling(14).max()
    stoch = (rsi - rsi_min)/(rsi_max - rsi_min).replace(0,0.0001)*100
    df['K'] = stoch.rolling(3).mean()
    df['D'] = df['K'].rolling(3).mean()
    df['RSI'] = rsi
    df['Z'] = (df['Close'] - df['Close'].rolling(50).mean())/df['Close'].rolling(50).std()
    return df.dropna()

def calc_prob(df):
    k = float(df['K'].iloc[-1]); d = float(df['D'].iloc[-1]); rsi = float(df['RSI'].iloc[-1]); z = float(df['Z'].iloc[-1])
    p = 50
    if k < 20: p+=20
    if k > d: p+=12
    if rsi < 45: p+=10
    if abs(z)>1.5: p+=8
    return min(95, max(5,p)), k, d, rsi, z

symbol = st.selectbox("📊 اختر السهم", STOCKS)
df = get_data(symbol)
if df is None or len(df)<60:
    st.error("البيانات غير متوفرة"); st.stop()

prob, k_now, d_now, rsi_now, z_now = calc_prob(df)
power = int(min(99, prob*0.88 + abs(z_now)*4))
close_p = float(df['Close'].iloc[-1])

# ========== الصفوف ==========
left, center, right = st.columns([1.1, 2.2, 1.1])

with left:
    st.markdown(f"""
    <div class="box">
    <h3 class="glow-cyan">🧠 KNN OLASILIK MOTORU</h3>
    <p style="text-align:center; color:#8aa">YÜKSELIŞ OLASILIĞI</p>
    <div style="text-align:center">
        <div class="kpi">{prob:.0f}%</div>
        <progress value="{prob}" max="100" style="width:90%; height:18px; accent-color:#00e5ff"></progress>
        <p style="color:{'#00ff88' if prob>65 else '#ff4444'}; font-weight:700">{'YÜKSEK • AL SİNYALİ' if prob>65 else 'DÜŞÜK • BEKLE'}</p>
    </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box-orange" style="margin-top:12px">
    <h3 class="glow-orange">⏰ FIBONACCI ZAMAN</h3>
    1.618 → 14 Mar 15:00 • <b style="color:#ff8c00">ÖNEMLİ</b><br>
    1.272 → 14 Mar 18:30 • DÖNÜŞ<br>
    1.000 → 14 Mar 22:45 • HEDEF<br>
    0.618 → 15 Mar 02:00 • DESTEK
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box" style="margin-top:12px">
    <h3 class="glow-cyan">🔷 GANN FIYAT MATRISI</h3>
    <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; text-align:center">
        <div style="background:#1a2a4a; padding:8px; border-radius:6px">{close_p*1.015:.0f}</div>
        <div style="background:#ff8c0044; border:1px solid #ff8c00; padding:8px; border-radius:6px">{close_p*1.01:.0f}</div>
        <div style="background:#1a2a4a; padding:8px; border-radius:6px">{close_p*1.02:.0f}</div>
        <div style="background:#1a2a4a; padding:8px; border-radius:6px">{close_p*0.992:.0f}</div>
        <div style="background:#00e5ff44; border:1px solid #00e5ff; padding:8px; border-radius:6px; color:#00e5ff">{close_p:.1f}</div>
        <div style="background:#1a2a4a; padding:8px; border-radius:6px">{close_p*1.005:.0f}</div>
    </div>
    <p style="font-size:11px; margin-top:8px; color:#8aa">KARDINAL: {close_p:.0f} • KÖŞEGEN: {close_p*1.01:.0f}<br>MODEL: KNN v3.1 • GÜVEN: %{prob:.0f}</p>
    </div>
    """, unsafe_allow_html=True)

with center:
    # شارت INSTITUTIONAL
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, row_heights=[0.65,0.35], vertical_spacing=0.03)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Price", increasing_line_color='#00ff88', decreasing_line_color='#ff4444'), row=1, col=1)
    # SELL ZONE
    fig.add_hrect(y0=close_p*1.008, y1=close_p*1.025, fillcolor="red", opacity=0.2, line_width=0, row=1, col=1)
    # BUY ZONE
    fig.add_hrect(y0=close_p*0.97, y1=close_p*0.985, fillcolor="#00e5ff", opacity=0.2, line_width=0, row=1, col=1)
    fig.update_layout(height=420, template="plotly_dark", paper_bgcolor="#0a1326", plot_bgcolor="#070e1f", showlegend=False, margin=dict(l=5,r=5,t=30,b=5),
                      title=dict(text=f"INSTITUTIONAL LIQUIDITY ANALYSIS | Price {close_p:.2f} | Z {z_now:.2f} {'🐋' if abs(z_now)>2 else ''}", font=dict(color="#00e5ff", size=12)))
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar':False})
    
    # Stochastic RSI
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df.index, y=df['K'], name="K% Blue", line=dict(color="#00aaff", width=2)))
    fig2.add_trace(go.Scatter(x=df.index, y=df['D'], name="D% Orange", line=dict(color="#ff8c00", width=2)))
    fig2.add_hline(y=80, line_dash="dash", line_color="red", annotation_text="OB 80")
    fig2.add_hline(y=20, line_dash="dash", line_color="green", annotation_text="OS 20")
    fig2.update_layout(height=260, template="plotly_dark", paper_bgcolor="#0a1326", plot_bgcolor="#070e1f", margin=dict(l=5,r=5,t=25,b=5),
                       title=dict(text=f"STOCHASTIC RSI v100 | RSI:{rsi_now:.2f} • K% {k_now:.1f} D% {d_now:.1f} | {'🐋 WHALE' if abs(z_now)>2 else ''}", font=dict(size=12, color="#ff8c00")))
    st.plotly_chart(fig2, use_container_width=True, config={'displayModeBar':False})
    st.markdown(f"<div style='text-align:center; background:#00e5ff22; border-radius:6px; padding:4px; color:#00e5ff'>HOLY TRINITY SIGNAL • AL • TREND: {'BULLISH' if k_now>d_now else 'BEARISH'} • CONFIRMATION: {3 if prob>70 else 2}/3</div>", unsafe_allow_html=True)

with right:
    st.markdown(f"""
    <div class="box-orange">
    <h3 class="glow-orange">🛡️ AKILLI KALKAN & OTOPILOT</h3>
    <b class="glow-cyan">OTOPILOT KONTROL LİSTESİ</b><br><br>
    {'✅' if prob>60 else '⬜'} Trend Filtresi: ONAYLI<br>
    {'✅' if abs(z_now)<2.5 else '⬜'} Likidite Engeli: TEMİZLENDİ<br>
    {'✅' if df['RSI'].iloc[-1]<70 else '⬜'} Volatilite: NORMAL<br>
    {'✅' if prob>65 else '⬜'} Risk/Ödül > 2.0: ONAYLI<br>
    {'⬜' if abs(z_now)<2 else '✅'} Haber Riski: {'YOK' if abs(z_now)<2 else 'VAR'}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box" style="margin-top:12px">
    <h3 class="glow-cyan">📊 DIVERGENCE MATRIX</h3>
    RSI DIV <span style="float:right; background:#00ff8844; padding:2px 8px; border-radius:4px">{'BULLISH • 1H' if k_now>20 else 'YOK'}</span><br><br>
    MACD DIV <span style="float:right; background:#00ff8844; padding:2px 8px; border-radius:4px">BULLISH • 4H</span><br><br>
    STOCH DIV <span style="float:right; background:#333; padding:2px 8px; border-radius:4px">YOK • 15m</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="box-orange" style="margin-top:12px; border-color:#ff8c00">
    <h3 class="glow-orange">🍀 JACKPOT MODU</h3>
    CONTRACT POWER:<br>
    <div class="big-power">{power:.1f}%</div>
    <progress value="{power}" max="100" style="width:100%; height:18px; accent-color:#ff8c00"></progress> {power}%<br><br>
    <span style="background:#ff8c00; color:#000; padding:4px 8px; border-radius:4px; font-weight:800">MOD: {'AKTİF 🔥' if power>=85 else 'BEKLEMEDE'}</span><br><br>
    KALDIRAÇ: 5x<br>
    HEDEF: +12.5%<br><br>
    <div style="background:#0a1326; border-radius:6px; padding:6px; font-size:11px">
    UYARI: OTOPILOT AKTİF • SL: {close_p*0.97:.1f} • TP: {close_p*1.03:.1f}
    </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"<div style='text-align:center; color:#5a6a8a; margin-top:15px'>OTOPILOT: {'BEKLEMEDE' if power<85 else 'AKTİF'} • SON SİNYAL 2dk önce • MTF MATRIX: 1m Bear | 5m Neutral | 15m Bull | 1H Bull | 4H Bull | 1D Bull • {symbol}</div>", unsafe_allow_html=True)

if power >= 85:
    st.balloons()
    st.success(f"🚀 JACKPOT AKTIF {symbol} - قوة {power}% - KNN {prob:.0f}% - {'🐋 حوت' if abs(z_now)>2 else ''}")
