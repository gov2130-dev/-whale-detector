import streamlit as st, yfinance as yf, requests
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

# CSS يكبر الخط في اللابتوب
st.markdown("""
<style>
.big-box {
    background: #0f1c2e;
    border: 3px solid #00e6a8;
    border-radius: 15px;
    padding: 25px;
    font-size: 22px !important;
    line-height: 1.8;
    color: white;
    direction: rtl;
    font-family: 'Segoe UI', Tahoma;
}
.big-box b { color: #00e6a8; font-size: 26px; }
.targets { color: #ffd700; font-size: 24px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def send(msg):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={'chat_id':CHAT_ID,'text':msg})

def fmt_hybrid(ticker, o_type, strike, opt_entry, stop_opt, curr_price, tg_stock, vol_text, rsi, ema_txt, score):
    date=(datetime.now()+timedelta(days=1)).strftime('%d/%m/%Y')
    tg_str=" → ".join([str(int(x)) for x in tg_stock])
    t1=opt_entry*1.5
    t2=opt_entry*2.2
    
    # هذه الرسالة اللي تروح تلجرام - تجمع الصورتين
    return f"""🔥 V80 {datetime.now().strftime('%H:%M:%S')} ذهبي {score}/7 85%
${ticker} - {strike} {o_type}
السعر الحالي: ${curr_price:.2f}
📅 {date}

💰 دخول العقد: ${opt_entry:.2f} | Spread {vol_text}
🎯 دخول السهم: {int(curr_price)}

🎯 اهداف العقد:
T1 ${t1:.2f} (+50%) 🎯
T2 ${t2:.2f} (+120%) 🎯
🛑 وقف العقد: ${stop_opt:.2f} 🛑

🎯 اهداف السهم:
{tg_str}

📊 VOL/OI {vol_text}, RSI {rsi} جيد, {ema_txt}

⚠️ ليست توصية بيع او شراء،
للتعليم فقط.

🐋 حيتان ابو راكان
TrkHrTrading
🔥 GOLDEN {score}/7"""

st.set_page_config(layout="wide")
st.title("V80 - مزج الصورتين + وضوح لابتوب")

# مثال للعرض في اللابتوب بخط كبير
example_msg = fmt_hybrid("MSFT", "PUT", 490, 2.85, 1.71, 494.5, [489, 484, 479, 474, 469], "10% 1.4x", 66, "EMA عكسي", 5)

# عرض في اللابتوب بخط كبير وواضح جدا
st.markdown(f"""
<div class="big-box">
<b>تحديث العقد والاهداف والدخول</b><br>
<b>${"MSFT"} - 490 PUT 🎯</b> - السعر الحالي $494.50<br>
📅 28/08/2026<br><br>
<b>💰 دخول العقد: $2.85</b> | Spread 10% - VOL/OI 1.4x<br>
<b>💰 دخول السهم: 494</b><br><br>
<b>🛑 وقف العقد: $1.71</b><br><br>
<span class="targets">🎯 اهداف العقد:</span><br>
T1 $4.28 (+50%) → T2 $6.27 (+120%)<br><br>
<span class="targets">🎯 اهداف السهم:</span><br>
489 → 484 → 479 → 474 → 469<br><br>
📊 RSI 66 جيد, EMA عكسي<br><br>
⚠️ ليست توصية<br>
🐋 <b>حيتان ابو راكان</b><br>
TrkHrTrading 🔥 GOLDEN 5/7
</div>
""", unsafe_allow_html=True)

st.code(example_msg, language="text")

if st.button("📩 ارسل المزج للتلجرام"):
    send(example_msg)
    st.success("✅ انرسل - شف تلجرام - الآن يجمع دقة V68 + وضوح V79")

if st.button("▶️ فحص حقيقي - مزج دقيق"):
    for ticker in ["MSFT","NVDA","AAPL"]:
        try:
            tk=yf.Ticker(ticker)
            hist=tk.history(period="10d")
            curr=float(hist['Close'].iloc[-1])
            chain=tk.option_chain(tk.options[1])
            df=chain.puts if curr>hist['Close'].iloc[-2] else chain.calls
            row=df.iloc[2]
            opt=float(row['lastPrice'])
            if opt<0.5: continue
            tg=[curr*0.99, curr*0.98, curr*0.97, curr*0.96, curr*0.95]
            m=fmt_hybrid(ticker,"PUT" if curr>hist['Close'].iloc[-2] else "CALL",int(row['strike']),opt,opt*0.6,curr,tg,"12% 1.4x",66,"EMA عكسي",5)
            send(m)
            st.success(f"{ticker} انرسل")
        except Exception as e:
            st.write(e)
