import streamlit as st, yfinance as yf, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def send(msg):
    try:
        url=f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        r=requests.post(url, data={'chat_id':CHAT_ID,'text':msg,'parse_mode':'HTML'}, timeout=15)
        return r.status_code==200
    except Exception as e:
        st.error(f"خطأ ارسال: {e}")
        return False

def fmt_msg(ticker, o_type, strike, opt_price, stop, curr_price, score, vol, rsi):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    # اهداف السهم دقيقة على سعر الحالي
    tg=[curr_price*1.01, curr_price*1.02, curr_price*1.03, curr_price*1.045, curr_price*1.06, curr_price*1.08, curr_price*1.10]
    tg_str=" → ".join([f"{int(x)}" for x in tg])
    t1=opt_price*1.5
    t2=opt_price*2.2

    return f"""<b>تحديث العقد والاهداف والدخول</b>
<b>${ticker} - {strike} {o_type} 🎯</b>
📅 {date}
💵 السعر الحالي: ${curr_price:.2f}

<b>💰 دخول العقد: ${opt_price:.2f}</b>
<b>🛑 وقف العقد: ${stop:.2f}</b>
📊 Vol {vol} | RSI {int(rsi)}

<b>🎯 اهداف السهم:</b>
{tg_str}

<b>🎯 اهداف العقد:</b>
T1 ${t1:.2f} (+50%) | T2 ${t2:.2f} (+120%)

⚠️ ليست توصية بيع أو شراء،
للتعليم فقط.

🐋 <b>حيتان ابو راكان</b>
TrkHrTrading
{'🔥 GOLDEN 6/7' if score>=6 else '⭐ GOOD 5/7'}"""

st.set_page_config(page_title="V77 FINAL", layout="wide")
now=datetime.now()+timedelta(hours=3)
st.title(f"V77 حيتان - {now.strftime('%H:%M:%S')} KSA")
st.success("جاهز - هذا كتابة فقط + أسعار دقيقة حقيقية")

if st.button("📩 اختبار دقيق"):
    m=fmt_msg("NVDA","CALL",209,4.50,2.70,205.30,6,850,58)
    if send(m):
        st.success("✅ انرسل - شف جوالك"); st.code(m)
    else:
        st.error("فشل - تأكد من النت")

if st.button("▶️ فحص السوق - اسعار حقيقية"):
    tickers=["NVDA","AAPL","MSFT","AVGO","META","COIN","TSLA"]
    prog=st.progress(0)
    for i,ticker in enumerate(tickers):
        prog.progress(int((i+1)/len(tickers)*100))
        try:
            tk=yf.Ticker(ticker)
            hist=tk.history(period="10d")
            if len(hist)<5: continue
            curr=float(hist['Close'].iloc[-1])
            # RSI مبسط
            delta=hist['Close'].diff()
            gain=delta.where(delta>0,0).rolling(14).mean().iloc[-1]
            loss=-delta.where(delta<0,0).rolling(14).mean().iloc[-1]
            rsi=100-(100/(1+gain/(loss+0.01))) if loss!=0 else 50

            opts=tk.options
            if not opts: continue
            chain=tk.option_chain(opts[0])
            df=chain.calls.head(1)
            if df.empty: continue
            row=df.iloc[0]
            opt_price=float(row['lastPrice'])
            if opt_price<0.5: continue
            strike=int(row['strike'])
            stop=opt_price*0.6
            m=fmt_msg(ticker,"CALL",strike,opt_price,stop,curr,5,int(row.get('volume',0)),rsi)
            if send(m):
                st.code(m)
        except Exception as e:
            st.write(f"{ticker} خطأ: {e}")
            continue
    st.success("انتهى")
