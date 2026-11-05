# V12.3 - ماسح صانع السوق - مفتوح بكل وقت
# المنطق: عند كل بحث، افحص الكل، اعطيني بس المنطبق

import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. الكون كله - مو قائمة ثابتة
# يجيب كل أسهم NASDAQ + NYSE + ARCA
def get_universe():
    # تقدر تبدلها بمصدرك، المهم انها كل الأسهم مو كم سهم
    tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    sp500 = tables[0]['Symbol'].tolist()
    # اضف باقي الأسهم من مصدرك هنا
    # مثال: nasdaq = ...
    # universe = list(set(sp500 + nasdaq + nyse))
    universe = list(set([s.replace('.', '-') for s in sp500]))
    return universe

# 2. شرط القاع القوي
def is_strong_low(df):
    # آخر 252 شمعة = سنة
    low_52w = df['Low'].tail(252).min()
    high_52w = df['High'].tail(252).max()
    close = df['Close'].iloc[-1]
    low_today = df['Low'].iloc[-1]
    
    # السعر قريب من قاع السنة (أقل من 10% فوقه)
    near_low = close <= low_52w * 1.10
    
    # القاع تم اختباره مرتين على الأقل وارتد منه
    touches = (df['Low'].tail(60) <= low_52w * 1.05).sum()
    tested_twice = touches >= 2
    
    # فوليوم شراء كبير في آخر شمعتين
    last_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].tail(20).mean()
    volume_spike = last_vol > avg_vol * 1.5
    
    # السعر فوق قاع اليوم وبدأ يرتد
    bouncing = close > low_today
    
    return near_low and tested_twice and volume_spike and bouncing, low_52w, high_52w

# 3. شرط القمة الضعيفة
def is_weak_high(df):
    low_52w = df['Low'].tail(252).min()
    high_52w = df['High'].tail(252).max()
    close = df['Close'].iloc[-1]
    high_today = df['High'].iloc[-1]
    
    near_high = close >= high_52w * 0.90
    touches = (df['High'].tail(60) >= high_52w * 0.95).sum()
    tested_twice = touches >= 2
    falling = close < high_today
    
    return near_high and tested_twice and falling, low_52w, high_52w

# 4. تأكيد انعكاس - CHoCH / كسر مقاومة
def is_breakout(df):
    # متوسط 20 و 50
    ma20 = df['Close'].tail(20).mean()
    ma50 = df['Close'].tail(50).mean()
    close = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    
    # كسر فوق متوسط 20
    above_ma20 = close > ma20 and prev_close <= ma20
    # أو كسر آخر قمة
    last_high = df['High'].tail(10).max()
    above_high = close > df['High'].iloc[-2]
    
    return above_ma20 or above_high, ma20, ma50

# 5. حوت أوبشن - صانع سوق دخل في الأوبشن
# تربطها بمصدر الأوبشن اللي تستخدمه (Unusual Whales / FlowAlgo / مصدرك)
def get_option_whale(ticker):
    """
    ترجع:
    {'type': 'CALL' أو 'PUT' أو None, 'premium': رقم, 'is_maker': True/False}
    الشرط: بريميوم كبير + حجم غير عادي + صانع سوق هو المشتري
    """
    # --- اربط هنا API الأوبشن حقك ---
    # مثال منطقي فقط:
    # flow = fetch_option_flow(ticker)
    # for trade in flow:
    #   if trade.premium > 50000 and trade.volume > trade.open_interest * 2:
    #       return {'type': trade.type, 'premium': trade.premium, 'is_maker': True}
    return {'type': None, 'premium': 0, 'is_maker': False}

# 6. حوت سهم - صانع سوق دخل في السهم نفسه
def get_stock_whale(df, ticker):
    last_vol = df['Volume'].iloc[-1]
    avg_vol = df['Volume'].tail(20).mean()
    close = df['Close'].iloc[-1]
    open_p = df['Open'].iloc[-1]
    
    # بلوك شراء كبير + شمعة خضراء + فوليوم غير عادي
    is_buy_block = last_vol > avg_vol * 2.0 and close > open_p
    # بلوك بيع كبير + شمعة حمراء
    is_sell_block = last_vol > avg_vol * 2.0 and close < open_p
    
    if is_buy_block:
        return {'type': 'BUY', 'volume_ratio': last_vol / avg_vol}
    if is_sell_block:
        return {'type': 'SELL', 'volume_ratio': last_vol / avg_vol}
    return {'type': None, 'volume_ratio': 0}

# 7. الفحص الرئيسي - عند كل ضغطة بحث
def scan():
    universe = get_universe()
    results = []
    
    # كل بحث يمسح القديم ويفحص من جديد - مافيه ذاكرة قديمة
    for ticker in universe:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False)
            if df.empty or len(df) < 60:
                continue
            
            # افحص الشروط
            low_ok, low_52w, high_52w = is_strong_low(df)
            high_ok, _, _ = is_weak_high(df)
            breakout_ok, ma20, ma50 = is_breakout(df)
            
            opt = get_option_whale(ticker)
            stock = get_stock_whale(df, ticker)
            
            close = float(df['Close'].iloc[-1])
