@st.cache_data(ttl=180)
def get_data(sym):
    try:
        # الحل الجديد - يشتغل مع السوق السعودي
        ticker = yf.Ticker(sym)
        df = ticker.history(period="6mo", interval="1d", auto_adjust=True)
        if df.empty:
            # جرب بدون .SR
            sym2 = sym.replace(".SR","")
            ticker = yf.Ticker(sym2+".SR")
            df = ticker.history(period="6mo", interval="1d")
        if df.empty or len(df)<20:
            return None
        if isinstance(df.columns, pd.MultiIndex): 
            df.columns = df.columns.get_level_values(0)
        # باقي الحسابات نفسها
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rs = gain / loss.replace(0,0.0001)
        rsi = 100 - (100/(1+rs))
        rsi_min = rsi.rolling(14).min(); rsi_max = rsi.rolling(14).max()
        stoch = (rsi - rsi_min)/(rsi_max - rsi_min).replace(0,0.0001)*100
        df['K']=stoch.rolling(3).mean()
        df['D']=df['K'].rolling(3).mean()
        df['RSI']=rsi
        df['Z']=(df['Close']-df['Close'].rolling(50).mean())/df['Close'].rolling(50).std()
        df['MA20']=df['Close'].rolling(20).mean()
        return df.dropna()
    except Exception as e:
        st.write(f"خطأ {sym}: {e}")
        return None
