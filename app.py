def is_strong_both(ticker):
    """يرجع اتجاه"""
    try:
        curr, daily, _ = get_data(ticker)
        if daily.empty: return False, "", "no data"
        daily['EMA20'] = daily['Close'].ewm(span=20).mean()
        ema20=float(daily['EMA20'].iloc[-1])
        open_t=float(daily['Open'].iloc[-1])
        chg=(curr/open_t-1)*100
        
        # اتجاه صاعد = CALL
        if curr > ema20*0.998 and chg > -1.5:
            return True, "CALL", f"فوق EMA20 + {chg:.1f}%"
        # اتجاه هابط = PUT  
        elif curr < ema20*1.002 and chg < 1.5:
            return True, "PUT", f"تحت EMA20 + {chg:.1f}%"
        else:
            return False, "", f"حيادي {chg:.1f}%"
    except: return False, "", "error"

def get_contract_dir(ticker, direction):
    opt_ticker = "SPY" if ticker=="SPX" else "QQQ" if ticker=="NDX" else ticker
    try:
        curr_real,_,tk = get_data(ticker)
        try: curr_opt=float(tk.fast_info['last_price'])
        except: curr_opt=curr_real
        today=datetime.now(NY).date()
        exps=[e for e in tk.options if datetime.strptime(e,"%Y-%m-%d").date()>=today][:2]
        for exp in exps:
            days=(datetime.strptime(exp,"%Y-%m-%d").date()-today).days
            if not (1 <= days <= 10): continue
            chain=tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            if direction=="CALL":
                opts=opts[(opts['strike']>=curr_opt*1.001) & (opts['strike']<=curr_opt*1.04)]
            else:
                opts=opts[(opts['strike']>=curr_opt*0.96) & (opts['strike']<=curr_opt*0.999)]
            
            for _, r in opts.sort_values('strike', ascending=(direction=="CALL")).iterrows():
                last=float(r['lastPrice'] or 0)
                if 1.0 <= last <= 4.0:
                    bid=float(r['bid'] or 0); ask=float(r['ask'] or 0)
                    if bid < 0.6: continue
                    return {"ticker":ticker,"curr":curr_real,"exp":exp,"days":days,"strike":int(r['strike']),"last":last,"bid":bid,"ask":ask,"type":direction}
    except: pass
    return None

def build_msg(c):
    base=c['curr']
    if c['type']=="CALL":
        tg=f"{base*1.01:.1f} → {base*1.03:.1f} → {base*1.05:.1f}"
        emoji="🟢"
    else:
        tg=f"{base*0.99:.1f} → {base*0.97:.1f} → {base*0.95:.1f}"
        emoji="🔴"
    
    return f"""{emoji} ${c['ticker']} - {c['strike']} {c['type']} 🔥
📅 {c['exp']} ({c['days']} يوم)
💵 السعر: ${c['curr']:.2f}

💰 دخول: ${c['last']:.2f} (Bid ${c['bid']:.2f} / Ask ${c['ask']:.2f})
🛑 وقف: ${c['last']*0.55:.2f}

🎯 اهداف السهم:
{tg}

🎯 اهداف العقد:
T1 ${c['last']*1.5:.2f} (+50%) | T2 ${c['last']*2.3:.2f} (+130%)"""
