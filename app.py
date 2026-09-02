def get_strong_direction(ticker):
    try:
        tk = yf.Ticker(ticker)
        # نجيب بيانات اكثر عشان ما يصير فاضي
        df15 = tk.history(period="10d", interval="15m")
        df5 = tk.history(period="5d", interval="5m")
        df_daily = tk.history(period="20d")

        if df15.empty or len(df15) < 50:
            df15 = df_daily  # fallback على اليومي اذا 15m فاضي
        if df5.empty:
            df5 = df_daily

        curr = float(df15['Close'].iloc[-1])

        # EMA - حتى لو البيانات قليلة نحسبها
        ema9 = df15['Close'].ewm(span=9, min_periods=1).mean().iloc[-1]
        ema20 = df15['Close'].ewm(span=20, min_periods=1).mean().iloc[-1]
        ema50 = df15['Close'].ewm(span=50, min_periods=1).mean().iloc[-1]

        # VWAP - اذا فشل نستخدم متوسط اليوم
        try:
            df5['TP'] = (df5['High']+df5['Low']+df5['Close'])/3
            vwap = (df5['TP']*df5['Volume']).sum() / df5['Volume'].sum()
            if pd.isna(vwap): vwap = df15['Close'].mean()
        except:
            vwap = df15['Close'].mean()

        # RSI - مع حماية من الفاضي
        try:
            delta = df15['Close'].diff()
            gain = delta.where(delta>0,0).rolling(14, min_periods=5).mean()
            loss = -delta.where(delta<0,0).rolling(14, min_periods=5).mean()
            rs = gain / loss.replace(0, 0.001)
            rsi = 100 - (100 / (1+rs))
            rsi_now = float(rsi.iloc[-1])
            if pd.isna(rsi_now): rsi_now = 50
        except:
            rsi_now = 50

        # Volume
        try:
            avg_vol = df_daily['Volume'].mean()
            vol_now = df5['Volume'].sum() if not df5.empty else df_daily['Volume'].iloc[-1]
            vol_ok = vol_now > avg_vol * 0.5 # خففتها عشان ما يصير فاضي
        except:
            vol_ok = True

        trend_strength = abs(ema9 - ema20) / curr * 100 if curr else 0

        call_strong = (ema9 > ema20 and curr > vwap and 50 <= rsi_now <= 75 and vol_ok)
        put_strong = (ema9 < ema20 and curr < vwap and 25 <= rsi_now <= 50 and vol_ok)

        if call_strong: return "CALL"
        if put_strong: return "PUT"
        return None
    except Exception as e:
        print(f"{ticker} error: {e}")
        return None            curr > vwap and
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
