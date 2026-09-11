def get_early_direction(ticker, timeframe="15m"):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="10d", interval=timeframe, prepost=False, auto_adjust=True)
        df_daily = tk.history(period="50d", interval="1d", prepost=False, auto_adjust=True)
        if len(df) < 30:
            return None, None
        
        # نستخدم الشمعة الحية - لكن بفلتر ذكي
        curr = float(df['Close'].iloc[-1])
        prev = float(df['Close'].iloc[-2])
        
        ema9 = df['Close'].ewm(span=9).mean()
        ema20 = df['Close'].ewm(span=20).mean()
        ema50 = df['Close'].ewm(span=50).mean()
        
        ema9_now = float(ema9.iloc[-1])
        ema20_now = float(ema20.iloc[-1])
        ema9_prev = float(ema9.iloc[-2])
        ema20_prev = float(ema20.iloc[-2])
        ema50_now = float(ema50.iloc[-1])
        
        # RSI
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss.replace(0, 0.001)))
        rsi_now = float(rsi.iloc[-1])
        rsi_prev = float(rsi.iloc[-2])
        
        # Bollinger Squeeze
        sma20 = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        upper = sma20 + std*2
        lower = sma20 - std*2
        bandwidth = (upper - lower) / sma20 * 100
        bw_now = float(bandwidth.iloc[-1])
        bw_prev = float(bandwidth.iloc[-2])
        is_squeezing = bw_now < bw_prev and bw_now < 6  # انضغاط
        
        # قرب التقاطع
        distance = abs(ema9_now - ema20_now) / curr * 100
        is_approaching_call = ema9_now < ema20_now and ema9_now > ema9_prev and distance < 0.3
        is_approaching_put = ema9_now > ema20_now and ema9_now < ema9_prev and distance < 0.3
        
        # حجم
        vol_avg = df['Volume'].rolling(20).mean().iloc[-1]
        vol_now = df['Volume'].iloc[-1]
        vol_spike = vol_now > vol_avg * 1.2
        
        # VWAP
        df['TP'] = (df['High']+df['Low']+df['Close'])/3
        vwap = (df['TP']*df['Volume']).sum() / df['Volume'].sum()
        
        gap = (curr - float(df_daily['Close'].iloc[-2]))/float(df_daily['Close'].iloc[-2])*100 if len(df_daily)>=2 else 0
        
        info = {"curr": curr, "ema9": ema9_now, "ema20": ema20_now, "ema50": ema50_now, "rsi": rsi_now, "gap": gap, "vwap": vwap, "bw": bw_now, "dist": distance, "vol_spike": vol_spike}

        # إشارة مبكرة CALL
        early_call = (
            (ema9_now > ema20_now or is_approaching_call) and  # تقاطع صار أو قريب يصير
            rsi_now > rsi_prev and rsi_now > 38 and rsi_now < 72 and  # RSI صاعد
            curr > vwap * 0.999 and  # فوق VWAP
            (is_squeezing or vol_spike)  # انضغاط أو حجم
        )
        
        early_put = (
            (ema9_now < ema20_now or is_approaching_put) and
            rsi_now < rsi_prev and rsi_now < 62 and rsi_now > 28 and
            curr < vwap * 1.001 and
            (is_squeezing or vol_spike)
        )

        if early_call:
            return "CALL", info
        if early_put:
            return "PUT", info
        return None, info
    except:
        return None, None
