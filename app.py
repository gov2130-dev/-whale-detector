import streamlit as st, yfinance as yf, requests, time
from datetime import datetime, date

BOT_TOKEN="8594574378:AAGcCOmuUyNOv3M5IWf0ROCEn1d5xpncp70"
CHAT_ID="13889370"
st.set_page_config(layout="wide", page_title="V99 CLEAN FINAL")
WATCHLIST = ["NVDA","TSLA","SPY","QQQ","AAPL","MSFT","META","AMD","SMH","IWM","SOFI","PLTR","COIN","HOOD"]

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg}, timeout=20)
        return r.status_code==200
    except: return False

def get_current_price(ticker, exp, strike, direction):
    try:
        tk=yf.Ticker(ticker)
        chain=tk.option_chain(exp)
        opts=chain.calls if direction=="CALL" else chain.puts
        row=opts[opts['strike']==strike]
        if row.empty: return None
        bid=float(row['bid'].iloc[0] or 0)
        ask=float(row['ask'].iloc[0] or 0)
        mid=(bid+ask)/2 if bid and ask else float(row['lastPrice'].iloc[0] or 0)
        return round(mid,2)
    except: return None

def get_direction(ticker):
    try:
        df=yf.download(ticker, period="10d", interval="30m", progress=False, auto_adjust=True)
        if len(df)<40: return None
        if hasattr(df.columns, 'get_level_values'):
            try: df.columns=df.columns.get_level_values(0)
            except: pass
        close=df['Close']
        vol=df['Volume']
        vwap=(close*vol).cumsum()/vol.cumsum()
        ema200=close.ewm(200).mean()
        ema20=close.ewm(20).mean()
        ema50=close.ewm(50).mean()
        score=0
        score+= 1 if close.iloc[-1]>vwap.iloc[-1] else -1
        score+= 1 if close.iloc[-1]>ema200.iloc[-1] else -1
        score+= 1 if ema20.iloc[-1]>ema50.iloc[-1] else -1
        if score>=2: return "CALL"
        if score<=-2: return "PUT"
        return None
    except: return None

def find_contract(ticker, direction):
    try:
        tk=yf.Ticker(ticker)
        curr=float(tk.fast_info.get('last_price') or tk.history(period="1d")['Close'].iloc[-1])
        for exp_str in tk.options[:3]:
            dte=(datetime.strptime(exp_str, "%Y-%m-%d").date() - date.today()).days
            if dte<1 or dte>14: continue
            chain=tk.option_chain(exp_str)
            opts=chain.calls if direction=="CALL" else chain.puts
            if opts.empty: continue
            for _, row in opts.iterrows():
                strike=row['strike']
                if abs(strike-curr)/curr>0.02: continue
                bid=row.get('bid',0) or 0
                ask=row.get('ask',0) or 0
                if bid==0 or ask==0: continue
                if (ask-bid)/ask*100>6: continue
                qty=(row.get('volume',0) or 0) or (row.get('openInterest',0) or 0)
                if qty<100: continue
                mid=(bid+ask)/2
                if mid<0.2 or mid*qty*100<80000: continue
                dr=tk.history(period="1d")
                return {
                    "ticker":ticker, "dir":direction, "strike":strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":round(abs(strike-curr)/curr*100,2),
                    "low":round(float(dr['Low'].iloc[-1]),2), "high":round(float(dr['High'].iloc[-1]),2),
                    "close":round(float(row.get('lastPrice', mid) or mid),2),
                    "entry":round(mid,2), "bid":round(bid,2), "stop":round(mid*0.5,2),
                    "t1":round(mid*1.5,2), "t2":round(mid*2.3,2), "t3":round(mid*3.2,2),
                    "s1":round(strike+0.3,2) if direction=="CALL" else round(strike-0.3,2),
                    "s2":round(strike+0.6,2) if direction=="CALL" else round(strike-0.6,2),
                    "s3":round(strike+1.0,2) if direction=="CALL" else round(strike-1.0,2),
                }
        return None
    except: return None

# CSS لكتابة أوضح
st.markdown("""
<style>
.contract-box {
    background:#111; color:#00ff9d; padding:18px; border-radius:12px;
    font-family: monospace; font-size:17px; line-height:1.6;
    border:1px solid #333; margin-bottom:15px; white-space: pre-wrap;
}
.result-box {
    background:#1e1e1e; color:#fff; padding:12px; border-radius:8px;
    font-size:16px; margin-top:8px; border-left:4px solid #00ff9d;
}
</style>
""", unsafe_allow_html=True)

st.title("🐋 V99 FINAL")

if st.button("🚀 فحص وارسال للتيليجرام", use_container_width=True):
    count=0
    for t in WATCHLIST:
        direction=get_direction(t)
        if not direction: continue
        c=find_contract(t,direction)
        if not c: continue

        # السعر الحالي للعقد
        now_price=get_current_price(c['ticker'], c['exp'], c['strike'], c['dir'])
        if now_price:
            pnl=(now_price-c['entry'])/c['entry']*100
            if now_price <= c['stop']: result=f"🔴 وقف {pnl:+.1f}%"
            elif now_price >= c['t3']: result=f"🟢 هدف 3 {pnl:+.1f}%"
            elif now_price >= c['t2']: result=f"🟢 هدف 2 {pnl:+.1f}%"
            elif now_price >= c['t1']: result=f"🟢 هدف 1 {pnl:+.1f}%"
            else: result=f"⚪ شغال {pnl:+.1f}%"
            result_line=f"Now: ${now_price} | {result}"
        else:
            result_line="Now: -- | ⏳ انتظار"

        emoji="🟢" if c['dir']=="CALL" else "🔴"
        text = (
            f"{emoji} {c['ticker']} {c['strike']} {c['dir']} 🐋\n"
            f"Exp: {c['exp']} ({c['dte']}d) Stock: ${c['curr']} BW {c['bw']}%\n"
            f"Range: ${c['low']} - ${c['high']} Close: ${c['close']}\n"
            f"Entry: ${c['entry']} Bid: ${c['bid']}\n"
            f"Stop: ${c['stop']}\n"
            f"Target Stock: {c['s1']} > {c['s2']} > {c['s3']}\n"
            f"Target Contract: ${c['t1']} (+50%) | ${c['t2']} (+130%) | ${c['t3']} (+220%)\n"
            f"{result_line}"
        )

        # عرض أوضح في الصفحة
        st.markdown(f'<div class="contract-box">{text}</div>', unsafe_allow_html=True)

        # ارسال للتيليجرام بدون عرض اي سطر اضافي
        send(text)
        count+=1
        time.sleep(0.8)

    st.toast(f"تم ارسال {count} عقد", icon="✅")

if st.button("📨 اختبار تيليجرام"):
    send("تجربة V99 ✅")
    st.toast("تم الارسال", icon="✅")
