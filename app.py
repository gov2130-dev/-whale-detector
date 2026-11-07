# في داخل حلقة الفحص، بدل هذا الجزء:
# for _, row in df.iterrows():
#     vol = ...
# حط هذا بداله:

for _, row in df.iterrows():
    vol = row['volume'] if pd.notna(row['volume']) else 0
    oi = row['openInterest'] if pd.notna(row['openInterest']) else 0
    price = row['lastPrice'] if pd.notna(row['lastPrice']) else 0
    strike = row['strike']
    
    # ===== هذا هو الاصلاح الجديد =====
    # 1. السترايك لازم يكون قريب من سعر السهم +- 12% فقط
    # هذا يشيل AMD 610 و NFLX 65 نهائياً
    if abs(strike - stock_price) / stock_price > 0.12:
        continue
    # 2. سعر العقد لازم يكون بين 0.5 و 20 دولار - مو 192 دولار
    if price < 0.5 or price > 20:
        continue
    # 3. الكمية والبريميوم مثل قبل
    if vol < 200 or oi == 0:
        continue
    # ================================
    
    premium = vol * price * 100
    key = f"{symbol}-{opt_type}-{strike}-{exp}"
    if key in st.session_state.seen:
        continue
    if vol/oi >= MIN_RATIO and premium >= MIN_PREMIUM and premium > best_premium:
        best_premium = premium
        best = (opt_type, row, exp, price, vol, key)
