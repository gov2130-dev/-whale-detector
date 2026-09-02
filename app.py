import yfinance as yf
import time
import requests
from datetime import datetime
import pandas as pd

# ================== الاعدادات ==================
TELEGRAM_BOT_TOKEN = "ضع_توكن_البوت_هنا"
TELEGRAM_CHAT_ID = "ضع_الايدي_هنا"

TICKERS = ["SPY","QQQ","AAPL","TSLA","NVDA","AMD","MSFT","META","AMZN","GOOGL"]
MIN_PRICE = 0.20
MAX_PRICE = 4.00
MIN_PREMIUM = 75000  # اقل بريميوم حوت
SCAN_INTERVAL = 60  # كل دقيقة

def send_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ================== 1. استراتيجية 25 مصطلح - اتجاه السهم المؤكد ==================
def get_confirmed_stock_signal(ticker):
    """
    يطبق كل المصطلحات:
    PDL, PDH, PDC, PMH, PML, Market Open, ORH, ORL, VWAP, Support, Resistance,
    Volume, RVOL, HH, HL, LH, LL, Breakout, Breakdown, Retest, Liquidity,
    Consolidation, Pullback, Stop Loss, Confirmation
    """
    try:
        tk = yf.Ticker(ticker)
        df15 = tk.history(period="10d", interval="15m", auto_adjust=True)
        df_daily = tk.history(period="10d", interval="1d", auto_adjust=True)
        df1m_today = tk.history(period="1d", interval="1m", auto_adjust=True)

        if df15.empty or len(df15) < 60 or df_daily.empty or len(df_daily) < 3:
            return None

        curr = float(df15['Close'].iloc[-1])
        curr_high = float(df15['High'].iloc[-1])
        curr_low = float(df15['Low'].iloc[-1])
        curr_vol = float(df15['Volume'].iloc[-1])

        # --- PDL / PDH / PDC (Previous Day)
        pdh = float(df_daily['High'].iloc[-2])
        pdl = float(df_daily['Low'].iloc[-2])
        pdc = float(df_daily['Close'].iloc[-2])

        # --- PMH / PML + ORH / ORL + Market Open
        if not df1m_today.empty:
            pre = df1m_today.between_time("04:00", "09:29")  # Premarket
            or_data = df1m_today.between_time("09:30", "09:44")  # Opening Range 15m
            
            pmh = float(pre['High'].max()) if not pre.empty else float(df_daily['High'].iloc[-1])
            pml = float(pre['Low'].min()) if not pre.empty else float(df_daily['Low'].iloc[-1])
            orh = float(or_data['High'].max()) if not or_data.empty else pmh
            orl = float(or_data['Low'].min()) if not or_data.empty else pml
        else:
            pmh = float(df15['High'].tail(26).max())
            pml = float(df15['Low'].tail(26).min())
            orh = pmh
            orl = pml

        # --- VWAP 15m
        tp = (df15['High'] + df15['Low'] + df15['Close']) / 3
        vwap = float((tp * df15['Volume']).sum() / df15['Volume'].sum())

        # --- Volume / RVOL / Liquidity
        avg_vol_20 = float(df15['Volume'].tail(20).mean())
        rvol = curr_vol / avg_vol_20 if avg_vol_20 > 0 else 0

        # --- HH/HL/LH/LL + EMA (Trend Structure)
        ema9 = float(df15['Close'].ewm(span=9).mean().iloc[-1])
        ema20 = float(df15['Close'].ewm(span=20).mean().iloc[-1])
        ema50 = float(df15['Close'].ewm(span=50).mean().iloc[-1])

        # HH = Higher High, HL = Higher Low (Uptrend)
        # LL = Lower Low, LH = Lower High (Downtrend)
        is_uptrend = ema9 > ema20 > ema50 and curr > ema20  # HH/HL
        is_downtrend = ema9 < ema20 < ema50 and curr < ema20  # LL/LH

        # --- RSI (Pullback)
        delta = df15['Close'].diff()
        gain = delta.where(delta > 0, 0).ewm(alpha=1/14).mean()
        loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/14).mean()
        rs = gain / loss
        rsi = float(100 - (100 / (1 + rs)).iloc[-1])

        # --- Support / Resistance + Breakout / Breakdown
        # نعتبر PMH/PML هي المقاومة والدعم
        breakdown = curr < pml and curr < orl  # Breakdown تحت PML و ORL
        breakout = curr > pmh and curr > orh   # Breakout فوق PMH و ORH

        # --- Retest (تأكيد الكسر مو كاذب)
        # هل لمس المستوى في اخر 3 شموع ورجع
        recent_highs = df15['High'].iloc[-4:-1]
        recent_lows = df15['Low'].iloc[-4:-1]
        retest_short = any(recent_highs >= pml * 0.999) and curr < pml
        retest_long = any(recent_lows <= pmh * 1.001) and curr > pmh

        # --- Consolidation Filter (ما ندخل اذا السوق عرضي)
        atr = float((df15['High'] - df15['Low']).tail(14).mean())
        is_consolidation = atr < (curr * 0.003)  # تذبذب اقل من 0.3%

        if is_consolidation:
            return None

        # --- تجميع نقاط التأكيد (Confirmation Score)
        # PUT Score
        put_conditions = [
            is_downtrend,           # 1. LL/LH
            curr < vwap,            # 2. تحت VWAP
            curr < pdc,             # 3. تحت اغلاق امس
            breakdown,              # 4. Breakdown
            retest_short,           # 5. Retest
            rvol > 1.3,             # 6. Volume/RVOL
            rsi < 55                # 7. Pullback
        ]
        put_score = sum(put_conditions)

        # CALL Score
        call_conditions = [
            is_uptrend,             # 1. HH/HL
            curr > vwap,            # 2. فوق VWAP
            curr > pdc,             # 3. فوق اغلاق امس
            breakout,               # 4. Breakout
            retest_long,            # 5. Retest
            rvol > 1.3,             # 6. Volume/RVOL
            rsi > 45                # 7. Pullback
        ]
        call_score = sum(call_conditions)

        # القرار - لازم 4 من 7 على الاقل
        if put_score >= 4:
            return {
                "ticker": ticker, "dir": "PUT", "score": put_score,
                "curr": curr, "pmh": pmh, "pml": pml, "pdh": pdh, "pdl": pdl,
                "pdc": pdc, "orh": orh, "orl": orl, "vwap": vwap,
                "rsi": rsi, "rvol": rvol, "ema9": ema9, "ema20": ema20, "ema50": ema50,
                "break_type": "BREAKDOWN" if breakdown else "PULLBACK"
            }
        if call_score >= 4:
            return {
                "ticker": ticker, "dir": "CALL", "score": call_score,
                "curr": curr, "pmh": pmh, "pml": pml, "pdh": pdh, "pdl": pdl,
                "pdc": pdc, "orh": orh, "orl": orl, "vwap": vwap,
                "rsi": rsi, "rvol": rvol, "ema9": ema9, "ema20": ema20, "ema50": ema50,
                "break_type": "BREAKOUT" if breakout else "PULLBACK"
            }

        return None
    except Exception as e:
        print(f"[{ticker}] Stock Signal Error: {e}")
        return None

# ================== 2. فلتر الحيتان للعقود مواكب لاتجاه السهم ==================
def get_whale_contracts_for_direction(ticker, signal):
    try:
        tk = yf.Ticker(ticker)
        exps = tk.options[:4]  # اقرب 4 اسابيع
        direction = signal['dir']
        curr_price = signal['curr']
        
        all_whales = []

        for exp in exps:
            try:
                chain = tk.option_chain(exp)
                opts = chain.calls if direction == "CALL" else chain.puts
                if opts.empty:
                    continue

                for _, row in opts.iterrows():
                    try:
                        bid = float(row['bid'] or 0)
                        ask = float(row['ask'] or 0)
                        last = float(row['lastPrice'] or 0)
                        vol = int(row['volume'] or 0)
                        oi = int(row['openInterest'] or 0)
                        strike = float(row['strike'])

                        price = (bid + ask) / 2 if bid and ask else last
                        if price < MIN_PRICE or price > MAX_PRICE:
                            continue
                        if vol < 250 or oi < 600:
                            continue
                        if bid == 0 or ask == 0:
                            continue

                        spread_pct = (ask - bid) / price if price > 0 else 1
                        if spread_pct > 0.35:  # Stop Loss - سبريد واسع
                            continue

                        # Liquidity - سيولة الحيتان
                        premium = vol * price * 100
                        if premium < MIN_PREMIUM:
                            continue

                        rvol_contract = vol / max(oi, 1)
                        if rvol_contract < 0.20:
                            continue

                        # العقد لازم يكون قريب (ATM/OTM خفيف) مو بعيد
                        # PUT: strike تحت سعر السهم بـ 0-5%
                        # CALL: strike فوق سعر السهم بـ 0-5%
                        if direction == "PUT":
                            if not (curr_price * 0.92 <= strike <= curr_price * 1.02):
                                continue
                        else:
                            if not (curr_price * 0.98 <= strike <= curr_price * 1.08):
                                continue

                        is_sweep = last >= ask * 0.97  # Sweep شراء ماركت
                        is_block = premium > 150000

                        # نقاط الحوت
                        whale_score = (premium / 1000) + (vol * 0.2) + (rvol_contract * 50)
                        if is_sweep: whale_score += 30
                        if is_block: whale_score += 30

                        all_whales.append({
                            "score": whale_score, "exp": exp, "strike": strike,
                            "price": price, "vol": vol, "oi": oi,
                            "premium": premium, "is_sweep": is_sweep,
                            "is_block": is_block, "bid": bid, "ask": ask,
                            "rvol_c": rvol_contract
                        })
                    except:
                        continue
            except:
                continue

        all_whales.sort(key=lambda x: x['score'], reverse=True)
        return all_whales[:2]  # اقوى عقدين فقط مواكبين للاتجاه
    except Exception as e:
        print(f"[{ticker}] Whale Error: {e}")
        return []

# ================== 3. اللوب الرئيسي ==================
def main_loop():
    print("🚀 Bot Started - 25 Terms + Whale Filter")
    while True:
        for ticker in TICKERS:
            try:
                signal = get_confirmed_stock_signal(ticker)
                if not signal:
                    continue

                print(f"✅ {ticker} {signal['dir']} Score {signal['score']}/7 RVOL {signal['rvol']:.1f}x {signal['break_type']}")

                whales = get_whale_contracts_for_direction(ticker, signal)
                if not whales:
                    print(f"   No whale contracts matching direction")
                    continue

                for w in whales:
                    dir_emoji = "🔴 PUT" if signal['dir'] == "PUT" else "🟢 CALL"
                    setup_type = "🔥 A+ SETUP" if signal['score'] >= 6 else "✅ CONFIRMED"
                    sweep_txt = "🔥 SWEEP" if w['is_sweep'] else "🐳 BLOCK" if w['is_block'] else "🐳 WHALE"

                    msg = f"""{dir_emoji} {ticker} {setup_type}
💰 {w['strike']} {w['exp']} @ ${w['price']:.2f} {sweep_txt}

📊 STOCK 25-TERMS:
Price: ${signal['curr']:.2f} | {signal['break_type']}
PML: ${signal['pml']:.2f} | PMH: ${signal['pmh']:.2f} | PDC: ${signal['pdc']:.2f}
PDL: ${signal['pdl']:.2f} | PDH: ${signal['pdh']:.2f}
ORL: ${signal['orl']:.2f} | ORH: ${signal['orh']:.2f}
VWAP: ${signal['vwap']:.2f} | RSI: {signal['rsi']:.0f} | RVOL: {signal['rvol']:.1f}x
EMA: {signal['ema9']:.2f}/{signal['ema20']:.2f}/{signal['ema50']:.2f} | Score: {signal['score']}/7

🐳 WHALE CONTRACT:
Vol: {w['vol']} | OI: {w['oi']} | RVOL: {w['rvol_c']:.2f}x
Premium: ${w['premium']:,.0f} | Bid/Ask: {w['bid']:.2f}/{w['ask']:.2f}
Entry: ${w['price']:.2f} Range {MIN_PRICE}-{MAX_PRICE}"""

                    send_telegram(msg)
                    time.sleep(2)

            except Exception as e:
                print(f"Loop {ticker} error: {e}")
                continue

        print(f"--- Scan done {datetime.now().strftime('%H:%M:%S')} sleeping {SCAN_INTERVAL}s ---")
        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main_loop()
