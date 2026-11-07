import yfinance as yf
print("بدأ الفحص...")

# نجرب على 3 اسهم بس عشان نتأكد انه شغال
for symbol in ["AAPL", "BABA", "AMZN"]:
    print(f"افحص {symbol}...")
    ticker = yf.Ticker(symbol)
    print(f"سعر {symbol}: {ticker.info.get('currentPrice')}")
    print(f"تواريخ الانتهاء: {ticker.options[:2]}")

print("✅ خلص! الكود شغال تمام")
