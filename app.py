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
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r = requests.post(url, data={'chat_id': CHAT_ID, 'text': msg}, timeout=15)
        print(f"Telegram status: {r.status_code} {r.text}")
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
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
        df_daily = tk.history(period="100d", interval="1d", prepost=False, auto_adjust=True)
        if len(df) < 20 or df_daily.empty:
            return None, None
        df_closed = df.iloc[:-1] if len(df) > 1 else df
        curr_closed = float(df_closed['Close'].iloc[-1])
        curr_live = float(df['Close'].iloc[-1])
        ema9 = df_closed['Close'].ewm(span=9).mean().iloc[-1]
        ema20 = df_closed['Close'].ewm(span=20).mean().iloc[-1]
        ema50 = df_closed['Close'].ewm(span=50).mean().iloc[-1]
        ema200 = df_daily['Close'].ewm(span=200).mean().iloc[-1]
        delta = df_closed['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi_series = 100 - (100 / (1 + gain / loss.replace(0, 0.001)))
        rsi_now = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50
        prev_close = float(df_daily['Close'].iloc[-2]) if len(df_daily)>=2 else curr_closed
        gap_pct = ((curr_closed - prev_close)/prev_close*100) if prev_close else 0
        df5 = tk.history(period="3d", interval="15m", prepost=False, auto_adjust=True)
        if len(df5) > 1:
            df5 = df5.iloc[:-1]
        if not df5.empty and df5['Volume'].sum()>0:
            df5['TP'] = (df5['High']+df5['Low']+df5['Close'])/3
            vwap = (df5['TP']*df5['Volume']).sum() / df5['Volume'].sum()
        else:
            vwap = ema20
        info = {"curr": curr_closed, "live": curr_live, "vwap": vwap, "ema9": ema9, "ema20": ema20, "ema50": ema50, "ema200": ema200, "rsi": rsi_now, "gap": gap_pct}
        if ema9 >= ema20:
            return "CALL", info
        else:
            return "PUT", info
    except Exception as e:
        return None, None

@st.cache_data(ttl=60)
def get_option_data(ticker, exp, curr_price, direction):
    try:
        tk = yf.Ticker(ticker)
        chain = tk.option_chain(exp)
        opts = chain.calls if direction=="CALL" else chain.puts
        if opts.empty:
            return None
        opts = opts.copy()
        opts['dist'] = abs(opts['strike']-curr_price)
        opts = opts.sort_values('dist')
        for _, row in opts.head(8).iterrows():
            bid = float(row['bid'] or 0)
            ask = float(row['ask'] or 0)
            last = float(row['lastPrice'] or 0)
            entry = round((bid+ask)/2,2) if bid>0 and ask>0 else round(last,2)
            if entry <= 0:
                continue
            result = {"strike": float(row['strike']), "bid": bid, "ask": ask, "entry": entry, "volume": int(row.get('volume',0) or 0), "oi": int(row.get('openInterest',0) or 0)}
            return result
        return None
    except Exception as e:
        return None

st.set_page_config(layout="wide", page_title="بوت الحيتان TURBO")
st.markdown("<style>.box{background:#1e1e1e;color:#fff;padding:14px;border-radius:10px;font-family:monospace;font-size:13px;line-height:1.6;border:1px solid #333;margin-bottom:8px;white-space:pre-wrap}.small{color:#888;font-size:11px}</style>", unsafe_allow_html=True)
st.title("🐳 بوت الحيتان TURBO - يحدد CALL/PUT إجباري")

c1,c2,c3 = st.columns(3)
with c1:
    timeframe = st.selectbox("الفريم", ["5m","15m","30m","1h","1d"], index=1)
with c2:
    min_p = st.number_input("أقل سعر", 0.01, 5.0, 0.05, step=0.05)
    max_p = st.number_input("أعلى سعر", 0.10, 100.0, 50.0, step=0.10)
with c3:
    dte_max = st.number_input("أقصى DTE", 1, 60, 21)

show_diag = st.checkbox("اظهر التشخيص", value=False)
watch_input = st.text_area("الأسهم", ",".join(WATCHLIST), height=60)
WATCHLIST = [x.strip().upper() for x in watch_input.split(",") if x.strip()]

if st.button("🚀 فحص وارسال تيليجرام", use_container_width=True, type="primary"):
    sent = 0
    st.write(f"جاري فحص {len(WATCHLIST)} سهم...")
    for t in WATCHLIST:
        try:
            tk = yf.Ticker(t)
            hist = tk.history(period="5d", prepost=False, auto_adjust=True)
            if hist.empty:
                if show_diag:
                    st.write(f"❌ {t}: لا بيانات")
                continue
            curr_live = float(hist['Close'].iloc[-1])
            high = float(hist['High'].iloc[-1])
            low = float(hist['Low'].iloc[-1])
            direction, info = get_strong_direction(t, timeframe)
            if not direction:
                if show_diag:
                    st.write(f"⚪ {t} ${curr_live:.2f} | لا اتجاه")
                continue
            if not tk.options:
                if show_diag:
                    st.write(f"⚪ {t}: لا عقود")
                continue
            valid_exp = None
            dte_val = 0
            for exp in tk.options[:6]:
                try:
                    dte = (datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
                    if 0 <= dte <= dte_max:
                        valid_exp = exp
                        dte_val = dte
                        break
                except:
                    continue
            if not valid_exp:
                continue
            opt = get_option_data(t, valid_exp, info['curr'], direction)
            if not opt:
                if show_diag:
                    st.write(f"⚪ {t} {direction}: لا عقد مناسب")
                continue
            if not (min_p <= opt['entry'] <= max_p):
                if show_diag:
                    st.write(f"⚪ {t} {direction} سعره ${opt['entry']} خارج النطاق")
                continue
            ft1, ft2, ft3 = get_fibo(high, low, direction)
            emoji = "🟢" if direction=="CALL" else "🔴"
            strike_s = int(opt['strike']) if opt['strike']==int(opt['strike']) else opt['strike']
            txt = f"{emoji} {t} {strike_s} {direction} 🐳\nExp: {valid_exp} ({dte_val}d) TF:{timeframe}\nStock: ${info['curr']:.2f} Live: ${curr_live:.2f} Gap:{info['gap']:+.2f}%\nEntry: ${opt['entry']:.2f} B:{opt['bid']:.2f} A:{opt['ask']:.2f} V:{opt['volume']}\nStop: ${opt['entry']*0.5:.2f} | T1:${opt['entry']*1.5:.2f} T2:${opt['entry']*2.3:.2f} T3:${opt['entry']*3.2:.2f}\nStock TG: {ft1} > {ft2} > {ft3}\nRSI:{info['rsi']:.1f} EMA9:{info['ema9']:.2f} EMA20:{info['ema20']:.2f}\n{datetime.now().strftime('%H:%M:%S')}"
            st.markdown(f'<div class="box">{txt.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            fpath = os.path.join(BASE, f"{date.today()}.json")
            try:
                data = json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            except:
                data = []
            key = f"{t}_{opt['strike']}_{direction}_{valid_exp}"
            if not any(d.get('key')==key for d in data):
                data.append({"key":key, "ticker":t, "strike":opt['strike'], "dir":direction, "exp":valid_exp, "entry":opt['entry']})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
            ok = send(txt)
            if ok:
                sent+=1
                st.toast(f"تم ارسال {t} {direction}")
            else:
                st.error(f"فشل ارسال {t} - تأكد من BOT_TOKEN و CHAT_ID")
            time.sleep(0.7)
        except Exception as e:
            st.write(f"❌ {t}: {e}")
            continue
    st.success(f"✅ تم ارسال {sent} عقد الى تيليجرام")
    if sent==0:
        st.warning("لم يتم الارسال! افتح هذا الرابط وتأكد من CHAT_ID: https://api.telegram.org/bot"+BOT_TOKEN+"/getUpdates")
