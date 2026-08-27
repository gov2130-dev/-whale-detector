def fmt_precise(ticker, o_type, strike, opt_entry, opt_stop, stock_price, tg_stock, score, vol):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    tg_str=" → ".join([str(int(x)) for x in tg_stock])
    
    # حساب نسبة كل هدف للعقد
    return f"""تحديث العقد والاهداف والدخول
${ticker} - {strike} {o_type} 🎯
📅 {date}
السعر الحالي: ${stock_price:.2f}

💰 دخول العقد: ${opt_entry:.2f}
🛑 وقف العقد: ${opt_stop:.2f}
📊 فوليوم: {vol}

🎯 أهداف السهم:
{tg_str}

🎯 أهداف العقد:
T1 ${opt_entry*1.5:.2f} (+50%) → T2 ${opt_entry*2.2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
{'🔥 GOLDEN 6/7' if score>=6 else '⭐ GOOD 5/7'}"""

# في اللوب - استخدم السعر الحقيقي:
# opt_entry = float(row['ask'])  # سعر العقد الحقيقي
# stock_price = float(hist['Close'].iloc[-1])  # سعر السهم الحقيقي
# tg_stock = [stock_price*1.01, stock_price*1.02, ...] # اهداف السهم
