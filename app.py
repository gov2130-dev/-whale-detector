def get_strong_direction(ticker):
    try:
        # فريم 15 دقيقة للاتجاه القوي
        df15 = yf.Ticker(ticker).history(period="5d", interval="15m")
        df5 = yf.Ticker(ticker).history(period="1d", interval="5m")
        if df15.empty or df5.empty: return None

        curr = float(df15['Close'].iloc[-1])
        
        # 1. EMA 9/20/50 على 15m
        ema9 = df15['Close'].ewm(span=9).mean().iloc[-1]
        ema20 = df15['Close'].ewm(span=20).mean().iloc[-1]
        ema50 = df15['Close'].ewm(span=50).mean().iloc[-1]
        
        # 2. VWAP على 5m
        df5['TP'] = (df5['High']+df5['Low']+df5['Close'])/3
        vwap = (df5['TP']*df5['Volume']).sum() / df5['Volume'].sum()
        
        # 3. RSI 14 على 15m
        delta = df15['Close'].diff()
        gain = (delta.where(delta>0,0)).rolling(14).mean()
        loss = (-delta.where(delta<0,0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1+rs))
        rsi_now = float(rsi.iloc[-1])

        # 4. Volume
        avg_vol = yf.Ticker(ticker).history(period="10d")['Volume'].mean()
        vol_ok = df5['Volume'].sum() > avg_vol * 0.9

        # 5. قوة الترند
        trend_strength = abs(ema9 - ema20) / curr * 100

        # توافق CALL قوي >90%
        call_strong = (
            ema9 > ema20 > ema50 and
            curr > vwap and
            curr > ema9 and
            55 <= rsi_now <= 72 and
            vol_ok and
            trend_strength > 0.15
        )
        # توافق PUT قوي >90%
        put_strong = (
            ema9 < ema20 < ema50 and
            curr < vwap and
            curr < ema9 and
            28 <= rsi_now <= 45 and
            vol_ok and
            trend_strength > 0.15
        )

        if call_strong: return "CALL"
        if put_strong: return "PUT"
        return None
    except:
        return None
