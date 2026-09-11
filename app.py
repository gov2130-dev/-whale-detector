import streamlit as st, yfinance as yf, requests, json, os, time
import pandas as pd
from datetime import datetime, date

BOT_TOKEN = st.secrets.get("BOT_TOKEN", "8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70")
CHAT_ID = st.secrets.get("CHAT_ID", "13889370")
BASE = "daily_results"
os.makedirs(BASE, exist_ok=True)

WATCHLIST = ["SPY","QQQ","AAPL","META","NVDA","TSLA","AMD","HOOD","COIN","SOFI","ORCL","NVO","MSFT","GOOGL","NFLX","AMZN"]

def send(msg):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg}, timeout=15)
        return True
    except:
        return False

def get_fibo(h, l, d):
    diff = (h - l) or 1.0
    if d == "PUT":
        return round(l - diff * 0.382, 2), round(l - diff * 0.618, 2), round(l - diff * 1.0, 2)
    return round(h + diff * 0.382, 2), round(h + diff * 0.618, 2), round(h + diff * 1.0, 2)

def get_strong_direction(ticker, timeframe="15m"):
    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period="20d", interval=timeframe, prepost=False, auto_adjust=True)
        df_daily = tk.history(period="200d", interval="1d", prepost=False, auto_adjust=True)
        spy = yf.Ticker("SPY").history(period="20d", interval=timeframe, prepost=False, auto_adjust=True)
        qqq = yf.Ticker("QQQ").history(period="20d", interval=timeframe, prepost=False, auto_adjust=True)

        if len(df) < 61 or df_daily.empty or len(df_daily) < 50:
            return None, None

        df_closed = df.iloc[:-1]
        if df_closed.empty:
            return None, None

        curr_closed = float(df_closed['Close'].iloc[-1])
        curr_live = float(df['Close'].iloc[-1])

        live_dev = abs(curr_live - curr_closed) / curr_closed * 100 if curr_closed else 0
        if live_dev > 0.8:
            return None, {"curr": curr_live, "closed": curr_closed, "dev": live_dev, "reason": "تذبذب"}

        ema9 = df_closed['Close'].ewm(span=9).mean().iloc[-1]
        ema9_prev = df_closed['Close'].ewm(span=9).mean().iloc[-2]
        ema20 = df_closed['Close'].ewm(span=20).mean().iloc[-1]
        ema20_prev = df_closed['Close'].ewm(span=20).mean().iloc[-2]
        ema50 = df_closed['Close'].ewm(span=50).mean().iloc[-1]
        ema200 = df_daily['Close'].ewm(span=200).mean().iloc[-1]

        spy_close = float(spy['Close'].iloc[-2]) if len(spy) >= 2 else curr_closed
        spy_ema50 = float(spy['Close'].ewm(span=50).mean().iloc[-2]) if len(spy) >= 2 else spy_close
        qqq_close = float(qqq['Close'].iloc[-2]) if len(qqq) >= 2 else curr_closed
        qqq_ema50 = float(qqq['Close'].ewm(span=50).mean().iloc[-2]) if len(qqq) >= 2 else qqq_close

        spy_up = spy_close > spy_ema50
        spy_down = spy_close < spy_ema50
        qqq_up = qqq_close > qqq_ema50

        df5 = tk.history(period="5d", interval="5m", prepost=False, auto_adjust=True).iloc[:-1]
        if not df5.empty and df5['Volume'].sum() > 0:
            df5['TP'] = (df5['High'] + df5['Low'] + df5['Close']) / 3
            vwap = (df5['TP'] * df5['Volume']).sum() / df5['Volume'].sum()
        else:
            vwap = df_closed['Close'].mean()

        delta = df_closed['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        rsi_series = 100 - (100 / (1 + gain / loss.replace(0, 0.001)))
        rsi_now = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
        rsi_prev = float(rsi_series.iloc[-2]) if len(rsi_series) >= 2 and not pd.isna(rsi_series.iloc[-2]) else rsi_now

        prev_daily_close = float(df_daily['Close'].iloc[-2]) if len(df_daily) >= 2 else curr_closed
        gap_pct = ((curr_closed - prev_daily_close) / prev_daily_close * 100) if prev_daily_close else 0

        call_strong = (
            ema9 > ema20 and ema9_prev > ema20_prev and
            ema20 > ema50 and
            curr_closed > vwap and
            curr_closed > ema200 and
            42 < rsi_now < 71 and
            rsi_now >= rsi_prev and
            spy_up and
            gap_pct > -2.5
        )

        put_strong = (
            ema9 < ema20 and ema9_prev < ema20_prev and
            ema20 < ema50 and
            curr_closed < vwap and
            curr_closed < ema200 and
            29 < rsi_now < 58 and
            rsi_now <= rsi_prev and
            spy_down and
            gap_pct < 2.5
        )

        info = {
            "curr": curr_closed,
            "live": curr_live,
            "vwap": vwap,
            "ema9": ema9,
            "ema20": ema20,
            "ema50": ema50,
            "ema200": ema200,
            "rsi": rsi_now,
            "gap": gap_pct,
            "dev": live_dev,
            "spy_up": spy_up,
            "qqq_up": qqq_up
        }

        if call_strong:
            return "CALL", info
        if put_strong:
            return "PUT", info
        return None, info

    except Exception as e:
        return None, None

@st.cache_data(ttl=60)
def get_option_data(ticker, exp, curr_price):
    try:
        tk = yf.Ticker(ticker)
        chain = tk.option_chain(exp)
        result = {}
        for direction in ["CALL", "PUT"]:
            opts = chain.calls if direction == "CALL" else chain.puts
            if opts.empty:
                continue
            opts = opts.copy()
            opts['dist'] = abs(opts['strike'] - curr_price)
            opts = opts.sort_values('dist')
            for _, row in opts.head(5).iterrows():
                bid = float(row['bid'] or 0)
                ask = float(row['ask'] or 0)
                last = float(row['lastPrice'] or 0)
                entry = round((bid + ask) / 2, 2) if bid > 0 and ask > 0 else round(last, 2)
                if entry <= 0:
                    continue
                spread = (ask - bid) / entry if entry and bid > 0 else 1
                if spread > 0.60:
                    continue
                result[direction] = {
                    "strike": float(row['strike']),
                    "bid": bid,
                    "ask": ask,
                    "entry": entry,
                    "volume": int(row.get('volume', 0) or 0),
                    "oi": int(row.get('openInterest', 0) or 0)
                }
                break
        return result
    except:
        return None

st.set_page_config(layout="wide", page_title="بوت الحيتان PRO V2")
st.markdown("<style>.box{background:#1e1e1e;color:#fff;padding:16px;border-radius:10px;font-family:monospace;font-size:13px;line-height:1.6;border:1px solid #333;margin-bottom:10px;white-space:pre-wrap}.small{color:#888;font-size:11px}</style>", unsafe_allow_html=True)
st.title("🐳 بوت الحيتان PRO V2 - بدون شمعة مفتوحة")

c1, c2, c3, c4 = st.columns(4)
with c1:
    timeframe = st.selectbox("الفريم", ["5m", "15m", "30m", "1h"], index=1)
with c2:
    min_p = st.number_input("أقل سعر", 0.05, 5.0, 0.10, step=0.05)
    max_p = st.number_input("أعلى سعر", 0.10, 50.0, 10.0, step=0.10)
with c3:
    dte_min = st.number_input("DTE من", 0, 90, 0)
    dte_max = st.number_input("DTE إلى", 1, 90, 14)
with c4:
    show_all = st.checkbox("اظهر حتى الفاشلة")

watch_input = st.text_area("الأسهم", ",".join(WATCHLIST), height=60)
WATCHLIST = [x.strip().upper() for x in watch_input.split(",") if x.strip()]

if st.button("🚀 فحص", use_container_width=True, type="primary"):
    sent = 0
    for t in WATCHLIST:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="5d", prepost=False, auto_adjust=True)
            if hist.empty:
                continue

            curr_live = float(hist['Close'].iloc[-1])
            high = float(hist['High'].iloc[-1])
            low = float(hist['Low'].iloc[-1])

            direction, info = get_strong_direction(t, timeframe)

            if not direction:
                if show_all and info:
                    st.write(f"⚪ {t} ${curr_live:.2f} | RSI {info.get('rsi',0):.1f} | Gap {info.get('gap',0):+.2f}%")
                continue

            if not tk.options:
                continue

            valid_exp = None
            for exp in tk.options[:8]:
                try:
                    dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                    if dte_min <= dte <= dte_max:
                        valid_exp = exp
                        break
                except:
                    continue

            if not valid_exp:
                continue

            dte = (datetime.strptime(valid_exp, "%Y-%m-%d").date() - date.today()).days
            opts_map = get_option_data(t, valid_exp, info['curr'])
            if not opts_map or direction not in opts_map:
                continue

            opt = opts_map[direction]
            if not (min_p <= opt['entry'] <= max_p):
                continue

            ft1, ft2, ft3 = get_fibo(high, low, direction)
            emoji = "🟢" if direction == "CALL" else "🔴"

            txt = f"{emoji} {t} {int(opt['strike']) if opt['strike']==int(opt['strike']) else opt['strike']} {direction} 🐳\nExp: {valid_exp} ({dte}d) TF:{timeframe}\nStock Closed: ${info['curr']:.2f} Live: ${curr_live:.2f} Gap:{info['gap']:+.2f}%\nEntry: ${opt['entry']:.2f} B:{opt['bid']:.2f} A:{opt['ask']:.2f} V:{opt['volume']}\nStop: ${opt['entry']*0.5:.2f} | T1:${opt['entry']*1.5:.2f} T2:${opt['entry']*2.3:.2f} T3:${opt['entry']*3.2:.2f}\nStock TG: {ft1} > {ft2} > {ft3}\nRSI:{info['rsi']:.1f} VWAP:{'Above' if info['curr']>info['vwap'] else 'Below'} SPY:{'UP' if info['spy_up'] else 'DOWN'}\n{datetime.now().strftime('%H:%M:%S')}"

            st.markdown(f'<div class="box">{txt}<div class="small">EMA9 {info["ema9"]:.2f} > EMA20 {info["ema20"]:.2f} > EMA50 {info["ema50"]:.2f} | EMA200 {info["ema200"]:.2f}</div></div>', unsafe_allow_html=True)

            fpath = os.path.join(BASE, f"{date.today()}.json")
            try:
                data = json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            except:
                data = []

            key = f"{t}_{opt['strike']}_{direction}_{valid_exp}_{timeframe}_{date.today()}"
            if not any(d.get('key') == key for d in data):
                data.append({"key": key, "ticker": t, "strike": opt['strike'], "dir": direction, "exp": valid_exp, "entry": opt['entry'], "info": info, "text": txt})
                json.dump(data, open(fpath, "w", encoding='utf-8'), ensure_ascii=False, indent=2)

            if send(txt):
                sent += 1
            time.sleep(0.6)

        except Exception as e:
            st.write(f"❌ {t}: {e}")
            continue

    st.success(f"✅ تم ارسال {sent} عقد - الحساب على الشموع المقفلة فقط")
