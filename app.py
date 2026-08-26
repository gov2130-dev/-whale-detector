def quality_check(r):
    score=0
    reasons=[]
    # 1. Bid-Ask
    try:
        bid=float(r.get('bid',0))
        ask=float(r.get('ask',0))
        if bid>0 and ask>0:
            spread=(ask-bid)/((ask+bid)/2)*100
            if spread<=5: score+=25; reasons.append(f"سبريد ممتاز {spread:.1f}%")
            elif spread<=10: score+=15; reasons.append(f"سبريد جيد {spread:.1f}%")
            elif spread<=20: score+=5; reasons.append(f"سبريد عالي {spread:.1f}%")
            else: score-=10; reasons.append(f"سبريد وهمي {spread:.1f}%")
        else:
            score+=10
    except: score+=10

    # 2. OI
    oi=int(r.get('oi',0) or 0)
    if oi>=5000: score+=20; reasons.append(f"OI قوي {oi}")
    elif oi>=1000: score+=12; reasons.append(f"OI جيد {oi}")
    elif oi>=300: score+=5
    else: score-=5; reasons.append(f"OI ضعيف {oi}")

    # 3. Delta
    delta=abs(float(r.get('delta',0.4)))
    if 0.30<=delta<=0.55: score+=20; reasons.append(f"Delta ممتاز {delta:.2f}")
    elif 0.25<=delta<=0.65: score+=10
    else: score-=5

    # 4. VOL vs OI
    vol=int(r.get('vol',0))
    if oi>0:
        ratio=vol/oi
        if ratio>=1.5: score+=20; reasons.append(f"انفجار VOL/OI x{ratio:.1f}")
        elif ratio>=0.8: score+=12; reasons.append(f"دخول قوي x{ratio:.1f}")
        elif ratio>=0.3: score+=5
        else: score+=0 # صورتك x0.2 x0.3 = ضعيف

    # 5. انتهاء
    days=int(r.get('days',2))
    if 5<=days<=14: score+=15; reasons.append(f"انتهاء مثالي {days}ي")
    elif 2<=days<=21: score+=5
    else: score-=5

    total=int(max(0,min(100,score)))
    return total, " | ".join(reasons[:3])

# في fetch_v51 أضف:
# "bid": float(r.get('bid',0)),
# "ask": float(r.get('ask',0)),
# "delta": float(r.get('delta',0)),
