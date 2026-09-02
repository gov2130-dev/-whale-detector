import yfinance as yf
import pandas as pd
import requests, time
from datetime import datetime

# ===================== الاعدادات العامة =====================
TELEGRAM_BOT_TOKEN = "حط_توكنك"
TELEGRAM_CHAT_ID = "حط_ايديك"

# عام لكل الاسهم - تقدر تغيرها
TICKERS = ["SPY","QQQ","AAPL","TSLA","NVDA","AMD","META","AMZN","MSFT","GOOGL","NFLX","BA","SPX","IWM"]
TIMEFRAMES = ["1m","5m","15m"]  # كل الفريمات - يفحصها كلها
MIN_PRICE, MAX_PRICE = 0.20, 4.00

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                      data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}, timeout=10)
        print(msg)
    except:
        print(msg)

# ===================== 1. محرك 25 مصطلح - عام =====================
def analyze_stock_25_terms(ticker, timeframe="15m"):
    """
    يطبق 25 مصطلح على اي سهم واي فريم:
    PDL, PDH, PDC, PMH, PML, Market Open, ORH, ORL, VWAP, Support, Resistance,
    Volume, RVOL, HH, HL, LH, LL, Breakout, Breakdown, Retest, Liquidity,
    Consolidation, Pullback, Stop Loss, Confirmation
    """
    try:
        tk = yf.Ticker(ticker)
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "60m": "60m"}
        yf_interval = interval_map.get(timeframe, "15m")
        
        df = tk.history(period="10d", interval=yf_interval, auto_adjust=True)
        df_daily = tk.history(period="10d", interval="1d", auto_adjust=True)
        df_1m = tk.history(period="2d", interval="1m", auto_adjust=True)  # للـ PMH/PML الدقيق

        if df.empty or len(df) < 50 or df_daily.empty:
            return None

        curr = float(df['Close'].iloc[-1])
        curr_h = float(df['High'].iloc[-1])
        curr_l = float(df['Low'].iloc[-1])
        curr_vol = float(df['Volume'].iloc[-1])

        # --- 1-6: PDL, PDH, PDC, PMH, PML, Market Open
        pdh = float(df_daily['High'].iloc[-2])
        pdl = float(df_daily['Low'].iloc[-2])
        pdc = float(df_daily['Close'].iloc[-2])

        if not df_1m.empty:
            pre = df_1m.between_time("04:00","09:29")
            pmh = float(pre['High'].max()) if not pre.empty else float(df_daily['High'].iloc[-1])
            pml = float(pre['Low'].min()) if not pre.empty else float(df_daily['Low'].iloc[-1])
            open_range = df_1m.between_time("09:30","09:45")
            orh = float(open_range['High'].max()) if not open_range.empty else pmh
            orl = float(open_range['Low'].min()) if not open_range.empty else pml
        else:
            pmh, pml, orh, orl = pdh, pdl, pdh, pdl

        # --- 7-9: VWAP, Volume, RVOL, Liquidity
        tp = (df['High']+df['Low']+df['Close'])/3
        vwap = float((tp*df['Volume']).sum()/df['Volume'].sum()) if df['Volume'].sum()>0 else curr
        avg_vol = float(df['Volume'].tail(20).mean())
        rvol = curr_vol / avg_vol if avg_vol>0 else 1.0

        # --- 10-14: HH, HL, LH, LL, Support, Resistance, Consolidation
        ema9 = float(df['Close'].ewm(9).mean().iloc[-1])
        ema20 = float(df['Close'].ewm(20).mean().iloc[-1])
        ema50 = float(df['Close'].ewm(50).mean().iloc[-1])

        is_uptrend = ema9 > ema20 > ema50  # HH/HL
        is_downtrend = ema9 < ema20 < ema50  # LH/LL
        atr = float((df['High']-df['Low']).tail(14).mean())
        is_consolidation = atr < curr*0.004  # Consolidation <0.4%

        # --- 15-18: Breakout, Breakdown, Pullback, Retest
        breakout = curr > pmh and curr > orh and curr > pdh*0.998
        breakdown = curr < pml and curr < orl and curr < pdl*1.002

        # Retest: لمس المستوى اخر 5 شموع
        retest_up = any(df['Low'].iloc[-6:-1] <= pmh*1.002) and curr > pmh
        retest_down = any(df['High'].iloc[-6:-1] >= pml*0.998) and curr < pml

        # Pullback RSI
        delta = df['Close'].diff()
        gain = delta.where(delta>0,0).ewm(alpha=1/14).mean()
        loss = (-delta.where(delta<0,0)).ewm(alpha=1/14).mean()
        rsi = float(100 - (100/(1+gain/loss)).iloc[-1]) if loss.iloc[-1]!=0 else 50

        # --- 19-25: Confirmation, Stop Loss
        if is_consolidation:
            return None  # لا تدخل في تجميع

        put_score = sum([is_downtrend, curr < vwap, curr < pdc, breakdown, retest_down, rvol>1.1, rsi<60])
        call_score = sum([is_uptrend, curr > vwap, curr > pdc, breakout, retest_up, rvol>1.1, rsi>40])

        # عام لكل الفريمات: لازم 4/7 تأكيدات
        if put_score >= 4:
            return {"ticker":ticker, "tf":timeframe, "dir":"PUT", "score":put_score, "curr":curr, "pmh":pmh, "pml":pml, "pdh":pdh, "pdl":pdl, "pdc":pdc, "orh":orh, "orl":orl, "vwap":vwap, "rsi":rsi, "rvol":rvol, "ema9":ema9, "ema20":ema20, "ema50":ema50, "type":"BREAKDOWN" if breakdown else "PULLBACK"}
        if call_score >= 4:
            return {"ticker":ticker, "tf":timeframe, "dir":"CALL", "score":call_score, "curr":curr, "pmh":pmh, "pml":pml, "pdh":pdh, "pdl":pdl, "pdc":pdc, "orh":orh, "orl":orl, "vwap":vwap, "rsi":rsi, "rvol":rvol, "ema9":ema9, "ema20":ema20, "ema50":ema50, "type":"BREAKOUT" if breakout else "PULLBACK"}
        return None
    except Exception as e:
        print(f"{ticker} {timeframe} err {e}")
        return None

# ===================== 2. فلتر الحيتان مواكب لاتجاه السهم =====================
def get_matching_whale_contracts(signal):
    ticker = signal['ticker']
    direction = signal['dir']
    curr = signal['curr']
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options[:3]
        whales=[]
        for exp in exps:
            chain = tk.option_chain(exp)
            opts = chain.calls if direction=="CALL" else chain.puts
            for _, r in opts.iterrows():
                try:
                    bid=float(r['bid'] or 0); ask=float(r['ask'] or 0); last=float(r['lastPrice'] or 0)
                    price=(bid+ask)/2 if bid and ask else last
                    vol=int(r['volume'] or 0); oi=int(r['openInterest'] or 0); strike=float(r['strike'])
                    if not (MIN_PRICE <= price <= MAX_PRICE): continue
                    if vol < 200 or oi < 500: continue
                    if bid==0 or ask==0: continue
                    if (ask-bid)/price > 0.35: continue
                    premium=vol*price*100
                    if premium < 25000: continue  # حوت 25k+
                    if direction=="PUT" and not (curr*0.90 <= strike <= curr*1.03): continue
                    if direction=="CALL" and not (curr*0.97 <= strike <= curr*1.10): continue
                    is_sweep = last >= ask*0.96
                    whales.append((premium, exp, strike, price, vol, oi, is_sweep, bid, ask))
                except: continue
        whales.sort(reverse=True)
        return whales[:3]
    except:
        return []

# ===================== 3. لوب عام لكل الاسهم والفريمات =====================
def scan_all():
    print(f"\n===== SCAN {datetime.now().strftime('%H:%M:%S')} TFs {TIMEFRAMES} =====")
    for tf in TIMEFRAMES:
        for t in TICKERS:
            sig = analyze_stock_25_terms(t, tf)
            if not sig:
                continue
            print(f"✅ {t} {tf} {sig['dir']} Score {sig['score']}/7 {sig['type']} RVOL {sig['rvol']:.1f}x")
            whales = get_matching_whale_contracts(sig)
            if not whales:
                print(f"  -> {t} حقق شروط 25 مصطلح بس ما فيه عقد حوت مواكب 0.20-4$")
                continue
            for prem, exp, strike, price, vol, oi, sweep, bid, ask in whales:
                msg = f"""{'🔴 PUT' if sig['dir']=='PUT' else '🟢 CALL'} {sig['ticker']} [{sig['tf']}] Score {sig['score']}/7 {sig['type']}
💰 {strike} {exp} @ ${price:.2f} {'🔥SWEEP' if sweep else '🐳'}

📊 25-TERMS:
Price ${sig['curr']:.2f} | PML ${sig['pml']:.2f} PMH ${sig['pmh']:.2f} | ORL ${sig['orl']:.2f} ORH ${sig['orh']:.2f}
PDL ${sig['pdl']:.2f} PDH ${sig['pdh']:.2f} PDC ${sig['pdc']:.2f}
VWAP ${sig['vwap']:.2f} RSI {sig['rsi']:.0f} RVOL {sig['rvol']:.1f}x
EMA {sig['ema9']:.2f}/{sig['ema20']:.2f}/{sig['ema50']:.2f}

🐳 WHALE:
Vol {vol} OI {oi} Prem ${prem:,.0f} {bid:.2f}/{ask:.2f}"""
                send(msg)
                time.sleep(1)

while True:
    scan_all()
    time.sleep(45)
