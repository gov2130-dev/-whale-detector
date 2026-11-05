def analyze(ticker, df):
    try:
        close = df["Close"]
        low = df["Low"]
        high = df["High"]
        vol = df["Volume"]
        opn = df["Open"]
        c = num(close)
        if c == 0 or len(close) < 50:
            return None
        low_90 = float(low.tail(90).min())
        high_90 = float(high.tail(90).max())
        if high_90 == low_90:
            return None

        # موقع السعر: 0% = قاع، 100% = قمة
        pos = (c - low_90) / (high_90 - low_90) * 100

        # --- القاعدة الجديدة المشددة ---
        # CALL بس إذا كان 0% - 20% : في القاع تماماً
        # PUT بس إذا كان 80% - 100% : في القمة تماماً
        # 20% - 80% = منطقة محرمة، ما نعطي إشارة
        # CVX اللي في صورتك 67.2% بيختفي الحين، لأنه في المنطقة المحرمة
        if 20 < pos < 80:
            return None

        ma20 = float(close.tail(20).mean())
        ma50 = float(close.tail(50).mean())
        last_vol = num(vol)
        avg_vol = float(vol.tail(20).mean())
        o = num(opn)
        h = num(high)
        l = num(low)
        uptrend = c > ma50
        downtrend = c < ma50
        c1 = float(close.iloc[-1])
        c2 = float(close.iloc[-2])
        o1 = float(opn.iloc[-1])
        o2 = float(opn.iloc[-2])
        two_green = (c1 > o1) and (c2 > o2)
        two_red = (c1 < o1) and (c2 < o2)

        # CALL: في القاع تماماً + ترند صاعد + شمعتين خضراء
        if pos <= 20 and uptrend:
            score = 0
            reasons = []
            score += 40
            reasons.append("في القاع تماماً")
            if two_green:
                score += 30
                reasons.append("شمعتين خضراء تأكيد")
            else:
                return None  # بدون شمعتين، لا نعطي CALL
            if avg_vol > 0 and last_vol > avg_vol * 1.4:
                score += 20
                reasons.append("فوليوم حوت")
            else:
                return None  # بدون فوليوم، لا نعطي CALL
            if c > ma20:
                score += 10
                reasons.append("فوق MA20")
            if score >= 80:  # قبل كان 60، الحين 80
                return {"ticker": ticker, "signal": "CALL", "kind": "قاع - ترند صاعد", "price": round(c, 2), "entry": round(h, 2), "stop": round(low_90, 2), "condition": " + ".join(reasons), "score": score, "strength": "🔥 قوي", "pos": round(pos, 1)}

        # PUT: في القمة تماماً + ترند هابط + شمعتين حمراء
        if pos >= 80 and downtrend:
            score = 0
            reasons = []
            score += 40
            reasons.append("في القمة تماماً")
            if two_red:
                score += 30
                reasons.append("شمعتين حمراء تأكيد")
            else:
                return None
            if avg_vol > 0 and last_vol > avg_vol * 1.4:
                score += 20
                reasons.append("فوليوم حوت")
            else:
                return None
            if c < ma20:
                score += 10
                reasons.append("تحت MA20")
            if score >= 80:
                return {"ticker": ticker, "signal": "PUT", "kind": "قمة - ترند هابط", "price": round(c, 2), "entry": round(l, 2), "stop": round(high_90, 2), "condition": " + ".join(reasons), "score": score, "strength": "🔥 قوي", "pos": round(pos, 1)}

        return None
    except Exception:
        return None
