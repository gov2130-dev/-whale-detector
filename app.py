# جيب سعر السهم الحي، مو من info القديم
try:
    stock_price = ticker.fast_info['lastPrice']
except:
    stock_price = ticker.history(period="1d")['Close'].iloc[-1]

# بعدين في الفلتر:
for _, row in df.iterrows():
    vol = row['volume'] if pd.notna(row['volume']) else 0
    oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
    price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
    strike = row['strike']

    if vol < 200 or oi == 0 or price < 0.5:
        continue

    premium = vol * price * 100
    
    # ===== هذا هو الصح =====
    # نحسب قرب السترايك من السعر، ونفضل القريب، بس ما نحذف البعيد
    # AMD 610 بعيد 35% عن 449، بس بريميومه عالي، فبيبقى
    # NFLX 65 قريب 3% عن 63، فبيكون ممتاز
    distance = abs(strike - stock_price) / stock_price
    # نقاط التفضيل: كل ما كان قريب، نقاطه أعلى
    score = premium * (1 - distance * 0.5)
    
    key = f"{symbol}-{opt_type}-{strike}-{exp}"
    if key in st.session_state.seen:
        continue
    if vol/oi >= MIN_RATIO and premium >= MIN_PREMIUM and score > best_premium:
        best_premium = score
        best = (opt_type, row, exp, price, vol, key)
