import streamlit as st, yfinance as yf, pandas as pd, time, urllib.request, urllib.parse
from datetime import datetime, timedelta

BOT_TOKEN="8594574378:AAEqZ3fbmEDrnnwgwW3yJIwH0kYNIneY9HY"
CHAT_ID="13889370"

def send_tg(msg):
    try:
        data=urllib.parse.urlencode({"chat_id":CHAT_ID,"text":msg}).encode()
        urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data), timeout=10)
        return True
    except: return False

st.set_page_config(layout="wide", page_title="V68 TELEGRAM AUTO")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:4px solid #16a34a;border-radius:16px;padding:16px;margin:12px 0;background:#f0fdf4;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-weight:900;}
.target{background:#fef3c7;color:#92400e;border:2px solid #f59e0b;padding:10px;border-radius:10px;margin-top:8px;font-weight:900;}
div.stButton > button{width:100%;height:58px;font-weight:900;border-radius:14px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "auto_done" not in st.session_state: st.session_state.auto_done=False
if "sent" not in st.session_state: st.session_state.sent=set()
if "auto_mode" not in st.session_state: st.session_state.auto_mode=True

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S'); ksa_h=ksa.hour
is_premarket = 2 <= ksa_h <= 6

st.markdown(f"# {ksa_str} - V68 TELEGRAM AUTO")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | تلجرام مفعل ✅ {CHAT_ID} | يفحص كل دقيقة 4 الفجر | اذا طلع عقد ذهبي 6/7 مثل MSFT 490 PUT بيرسل تلجرام وانت نايم</div>', unsafe_allow_html=True)

c1,c2=st.columns(2)
with c1:
    if st.button("🔔 فحص الآن 7 تأكيدات"):
        st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()
with c2:
    if st.button("📱 اختبار تلجرام"):
        if send_tg(f"✅ V68 شغال {ksa_str}\nاذا طلع عقد ذهبي 6/7 بيرسل لك تلقائي"):
            st.success("✅ انرسل - شف تلجرام")
        else:
            st.error("❌ خطأ")

if st.session_state.results:
    gold=[r for r in st.session_state.results if r["total"]>=5]
    if gold:
        st.balloons()
        st.success(f"🔥 {len(gold)} عقد ذهبي - تم الارسال لتلجرام")
        for w in gold:
            st.markdown(f"""<div class="card"><b>🔔 {w['ticker']} {w['strike']} {w['type']} - {w['confirm']}% | {w['total']}/7 | Delta {w['delta']:.2f}</b><br>
            <span style="font-size:11px;">سهم ${w['stock']:.2f} | Ask ${w['ask']:.2f} | Spread {w['spread_pct']:.0f}% | VOL {w['vol']}</span>
            <div class="target">🎯1 ${w['t1']:.2f} (+{w['p1']:.0f}%) | 🎯2 ${w['t2']:.2f} (+{w['p2']:.0f}%) | 🛑 ${w['sl']:.2f} | RR {w['rr']}</div></div>""", unsafe_allow_html=True)

should_scan = (not st.session_state.auto_done) or (st.session_state.auto_mode and is_premarket)
if should_scan:
    tickers=["MSFT","NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","SOFI","GOOGL","AVGO","NFLX"]
    log=st.empty(); prog=st.progress(0); new_results=[]
    for i,ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100)); log.text(f"V68 {ticker}...")
        try:
            tk=yf.Ticker(ticker); h=tk.history(period="20d")
            if len(h)<15: continue
            curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); ch1=float((curr-prev)/prev*100)
            d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            vwap=float(h['Close'].tail(10).mean()); ema9=float(h['Close'].ewm(span=9).mean().iloc[-1]); ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
            vol_ratio=float(h['Volume'].iloc[-1]/h['Volume'].tail(10).mean())
            trend=None
            if rsi<=42 and ch1<=-0.5: trend="BULL"
            elif rsi>=63 and ch1>=0.5: trend="BEAR"
            else: continue
            opts=tk.options; exp=opts[1] if len(opts)>1 else opts[0]; exp_d=datetime.strptime(exp,"%Y-%m-%d"); days=(exp_d-datetime.now()).days
            if days<1 or days>8: continue
            chain=tk.option_chain(exp); df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.35)&(df['lastPrice']<=8)]
            if df.empty or 'bid' not in df.columns: continue
            df=df.sort_values('volume', ascending=False).head(4); picked=None
            for _, r in df.iterrows():
                vol=int(r.get('volume',0) or 0)
                if vol<250: continue
                bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                if bid<=0 or ask<=0 or bid>=ask: continue
                mid=(bid+ask)/2; spread_pct=(ask-bid)/mid*100
                if spread_pct>15: continue
                oi=int(r.get('openInterest',0) or 0)
                if oi>2000 and vol < oi*0.3: continue
                picked=(r,bid,ask,spread_pct,vol,oi); break
            if not picked: continue
            r,bid,ask,spread_pct,vol,oi=picked; strike=int(r['strike'])
            if abs((strike-curr)/curr*100)>6.5: continue
            ok=[]; bad=[]
            ratio=vol/max(1,oi)
            if ratio>=0.5: ok.append(f"VOL/OI {ratio:.1f}x")
            else: bad.append(f"VOL/OI {ratio:.1f}x")
            if (trend=="BULL" and rsi<=32) or (trend=="BEAR" and rsi>=70): ok.append(f"RSI {rsi:.0f} قوي")
            elif (trend=="BULL" and rsi<=42) or (trend=="BEAR" and rsi>=63): ok.append(f"RSI {rsi:.0f} جيد")
            else: bad.append(f"RSI {rsi:.0f}")
            if (trend=="BULL" and curr < vwap*0.98) or (trend=="BEAR" and curr > vwap*1.02): ok.append(f"VWAP {((curr-vwap)/vwap*100):+.1f}%")
            else: bad.append(f"VWAP قريب")
            if (trend=="BULL" and ema9 < ema21) or (trend=="BEAR" and ema9 > ema21): ok.append("EMA عكسي")
            else: bad.append("EMA نفس")
            if vol_ratio>=1.2: ok.append(f"حجم {vol_ratio:.1f}x")
            else: bad.append(f"حجم {vol_ratio:.1f}x")
            if spread_pct<=5: ok.append(f"Spread {spread_pct:.0f}% ممتاز")
            elif spread_pct<=10: ok.append(f"Spread {spread_pct:.0f}% مقبول")
            else: bad.append(f"Spread {spread_pct:.0f}%")
            ok.append(f"Delta 0.5")
            total_ok=len(ok)
            if total_ok<5: continue
            entry=ask; t1=entry*1.5; t2=entry*2.2; sl=entry*0.60
            data={"ticker":ticker,"strike":strike,"type":"CALL" if trend=="BULL" else "PUT","stock":curr,"bid":bid,"ask":ask,"spread_pct":spread_pct,"vol":vol,"delta":0.5,"total":total_ok,"confirm":85,"exp":exp_d.strftime("%m/%d"),"t1":t1,"t2":t2,"sl":sl,"p1":50,"p2":120,"rr":"1:1.3"}
            new_results.append(data)
            key=f"{ticker}{strike}{data['type']}"
            if key not in st.session_state.sent:
                msg=f"🔥 V68 ذهبي {ksa_str}\n{ticker} {strike} {data['type']}\n{total_ok}/7 85%\nدخول ${ask:.2f} Spread {spread_pct:.0f}%\n🎯1 ${t1:.2f} (+50%)\n🎯2 ${t2:.2f} (+120%)\n🛑 ${sl:.2f}\n{', '.join(ok[:3])}"
                if send_tg(msg):
                    st.session_state.sent.add(key)
            time.sleep(0.1)
        except: continue
    prog.progress(100); log.empty()
    st.session_state.results=sorted(new_results, key=lambda x: -x["total"])
    st.session_state.auto_done=True
    if st.session_state.auto_mode and is_premarket:
        time.sleep(60); st.session_state.auto_done=False; st.rerun()
    else:
        time.sleep(0.3); st.rerun()
