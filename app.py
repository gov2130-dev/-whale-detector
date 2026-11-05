# --- قائمة المفضلة للأوبشنز - تنفحص أولاً ---
# هذي الأسهم اللي فيها سيولة أوبشنز عالية
# صانع السوق يلعب فيها دايم: سبريد ضيق + عقود كثيرة + فوليوم عالي

FAVORITE_OPTIONS = [
    # المؤشرات والـ ETF - الأهم للأوبشنز
    "SPY", "QQQ", "IWM", "DIA", "VXX", "UVXY",
    "GLD", "SLV", "GDX", "GDXJ", "USO", "TLT", "XLF", "XLE", "XLK",
    # التكنولوجيا الكبار - سيولة أوبشنز عالية
    "AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN", "GOOGL", "NFLX", "AVGO",
    "PLTR", "COIN", "MSTR", "SMCI", "MU", "INTC", "ORCL", "CRM",
    # الطاقة والذهب والفضة
    "XOM", "CVX", "OXY", "NEM", "WMT", "COST",
    # أسهم الميم والحركة السريعة - حيتان الأوبشنز تحبها
    "AMC", "GME", "BBBY",
    # الطاقة النظيفة والشمسية
    "FSLR", "ENPH", "SEDG",
    # الصين والأسواق الناشئة
    "BABA", "BIDU", "PDD", "JD",
    # البنوك والمالية
    "JPM", "BAC", "GS",
]

def get_universe():
    # 1. أولاً: المفضلة للأوبشنز
    # 2. بعدها: باقي S&P 500
    try:
        tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
        sp500 = [str(s).replace('.', '-').strip() for s in tables[0]['Symbol'].tolist()]
    except Exception:
        sp500 = []
    # المفضلة أولاً، وبعدين الباقي بدون تكرار
    universe = FAVORITE_OPTIONS.copy()
    for s in sp500:
        if s not in universe:
            universe.append(s)
    return universe

def scan():
    universe = get_universe()
    results = []
    progress = st.progress(0)
    status = st.empty()
    total = len(universe)
    for i, ticker in enumerate(universe):
        try:
            status.text(f"يفحص: {ticker} - {i+1}/{total}")
            progress.progress((i + 1) / total)
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=False)
            if df is None or df.empty or len(df) < 60:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            close_s = get_series(df, "Close")
            low_s = get_series(df, "Low")
            high_s = get_series(df, "High")
            vol_s = get_series(df, "Volume")
            if close_s.empty:
                continue
            low_ok, low_52w, high_52w = check_low(close_s, low_s, vol_s)
            high_ok, _, _ = check_high(close_s, high_s)
            breakout_ok, ma20, ma50 = check_breakout(close_s)
            opt = get_option_whale(ticker)
            close = num(close_s)
            low_today = num(low_s)
            high_today = num(high_s)
            last_vol = num(vol_s)
            avg_vol = float(vol_s.tail(20).mean()) if len(vol_s) > 0 else 0
            is_buy_block = avg_vol > 0 and last_vol > avg_vol * 2.0 and close > num(df["Open"]) if "Open" in df.columns else False
            is_sell_block = avg_vol > 0 and last_vol > avg_vol * 2.0 and close < num(df["Open"]) if "Open" in df.columns else False

            # هل هو من المفضلة؟ عشان يطلع لك أول ونجمة
            is_fav = ticker in FAVORITE_OPTIONS
            fav_tag = "⭐ مفضلة أوبشنز" if is_fav else "سوق عام"

            # شرط 1: CALL في القاع
            if low_ok and breakout_ok:
                if opt.get("type") == "CALL" and opt.get("is_maker"):
                    results.append({"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": f"حوت أوبشن CALL - {fav_tag}", "price": round(close, 2), "condition": "قاع قوي + كسر مقاومة + حوت CALL", "entry": round(high_today, 2), "stop": round(low_52w, 2), "is_fav": is_fav})
                elif is_buy_block:
                    results.append({"ticker": ticker, "signal": "CALL - دخول صانع سوق", "kind": f"حوت سهم شراء - {fav_tag}", "price": round(close, 2), "condition": "قاع قوي + بلوك شراء + فوليوم غير عادي", "entry": round(high_today, 2), "stop": round(low_52w, 2), "is_fav": is_fav})

            # شرط 2: PUT في القمة
            if high_ok:
                if opt.get("type") == "PUT" and opt.get("is_maker"):
                    results.append({"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": f"حوت أوبشن PUT - {fav_tag}", "price": round(close, 2), "condition": "قمة ضعيفة + حوت PUT", "entry": round(low_today, 2), "stop": round(high_52w, 2), "is_fav": is_fav})
                elif is_sell_block:
                    results.append({"ticker": ticker, "signal": "PUT - دخول صانع سوق", "kind": f"حوت سهم بيع - {fav_tag}", "price": round(close, 2), "condition": "قمة ضعيفة + بلوك بيع", "entry": round(low_today, 2), "stop": round(high_52w, 2), "is_fav": is_fav})

        except Exception as e:
            continue
    progress.empty()
    status.empty()
    # رتب: المفضلة أولاً
    results = sorted(results, key=lambda x: not x.get("is_fav", False))
    return results
