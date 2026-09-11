import streamlit as st, yfinance as yf, requests

st.set_page_config(layout="wide")
st.title("Whale Bot - Filtered + True Price")

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "")
CHAT_ID = st.secrets.get("CHAT_ID", "")

def send(m):
    try:
        if BOT_TOKEN and CHAT_ID:
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id':CHAT_ID,'text':m}, timeout=8)
    except: pass

def get_true_data(t, tf):
    try:
        tk = yf.Ticker(t)
        # السعر الحقيقي
        try:
            true_price = float(tk.fast_info['last_price'])
        except:
            true_price = float((tk.info.get('currentPrice') or tk.info.get('regularMarketPrice') or 0))
        
        df = yf.download(t, period="60d", interval=tf, auto_adjust=True, progress=False, threads=False)
        if df.empty: return None
        c = df['Close']
        if hasattr(c, 'columns'): c = c.iloc[:,0]
        c = c.dropna()
        if len(c) < 20: return None
        
        # تصحيح التضخم: لو السعر الحقيقي اصغر من سعر الهيستوري بـ 10% نصحح
        hist_price = float(c.iloc[-1])
        if true_price and true_price > 10 and abs(hist_price - true_price) / true_price > 0.08:
            ratio = true_price / hist_price
            c = c * ratio
            hist_price = true_price
        
        e9 = c.ewm(9).mean().iloc[-1]
        e20 = c.ewm(20).mean().iloc[-1]
        e50 = c.ewm(50).mean().iloc[-1]
        
        delta = c.diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100/(1+gain/loss.replace(0,0.0001)))
        r = float(rsi.iloc[-1])
        rp = float(rsi.iloc[-2])
        
        return {"price":hist_price, "e9":float(e9), "e20":float(e20), "e50":float(e50), "rsi":r, "rsi_prev":rp, "close":c}
    except:
        return None

tf = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=2)
WL = [x.strip().upper() for x in st.text_area("القائمة","SPY,QQQ,AAPL,META,NVDA,TSLA,AMD,HOOD,COIN,SOFI,ORCL,NVO,MSFT,GOOGL,AMZN,NFLX,PLTR,SHOP,UBER,BA", height=80).split(",")]

if st.button(f"RUN SCAN {tf} - FILTERED ONLY", use_container_width=True, type="primary"):
    found = 0
    for t in WL:
        d = get_true_data(t, tf)
        if not d: continue
        
        price, e9, e20, e50, r, rp = d['price'], d['e9'], d['e20'], d['e50'], d['rsi'], d['rsi_prev']
        
        # فلتر قوي - يطلع 2-5 فقط
        strong_call = price > e9 > e20 > e50 and 57 < r < 78 and r > rp and price > d['close'].rolling(20).mean().iloc[-1]
        strong_put = price < e9 < e20 < e50 and 22 < r < 43 and r < rp
        
        if strong_call:
            txt = f"{t} CALL STRONG | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.2f}>{e20:.2f}>{e50:.2f} | {tf}"
            st.code(txt); send(txt); found+=1
        elif strong_put:
            txt = f"{t} PUT STRONG | ${price:.2f} | RSI {r:.1f} | EMA9 {e9:.2f}<{e20:.2f}<{e50:.2f} | {tf}"
            st.code(txt); send(txt); found+=1
    
    if found == 0:
        st.warning(f"لا يوجد اشارة STRONG في {tf} - جرب فريم 15m او 1d")
    else:
        st.success(f"تم العثور على {found} فقط من {len(WL)} - هذي الفلترة الحقيقية")
