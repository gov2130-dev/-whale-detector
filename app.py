import streamlit as st, yfinance as yf, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V63 4AM")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #16a34a;border-radius:14px;padding:14px;margin:10px 0;background:#f0fdf4;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-weight:900;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')
hour=ksa.hour

st.markdown(f"# {ksa_str} - V63 4AM PREMARKET")
if 3 <= hour <= 5:
    st.markdown(f'<div class="time-card">● {ksa_str} KSA | 🟢 وقت البري ماركت الآن - فحص عكسي مفيد لبكره</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="time-card">● {ksa_str} KSA | V63 - يفحص عكسي 4 الفجر - الآن {ksa_str} - اضبط منبه 3:50</div>', unsafe_allow_html=True)

if st.button("🔔 فحص 4 الفجر - فقط عكسي مفيد"):
    st.session_state.results=[]; st.rerun()

tickers=["AAPL","HOOD","COIN","MSTR","PLTR","NVDA","TSLA","META","AMD","SOFI"]
log=st.empty(); prog=st.progress(0)
new=[]
for i,t in enumerate(tickers):
    prog.progress(int(i/len(tickers)*100))
    log.text(f"4AM يفحص {t}...")
    try:
        tk=yf.Ticker(t)
        h=tk.history(period="10d")
        if len(h)<5: continue
        curr=float(h['Close'].iloc[-1]); prev=float(h['Close'].iloc[-2]); ch1=float((curr-prev)/prev*100)
        d=h['Close'].diff(); g=d.where(d>0,0).ewm(alpha=1/14).mean(); l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
        rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
        trend=None; reason=""
        if rsi>=65 and ch1>=1.0: trend="BEAR"; reason=f"قمة RSI {rsi:.0f} صعد {ch1:+.1f}% = PUT بكره"
        elif rsi<=42 and ch1<=-1.0: trend="BULL"; reason=f"قاع RSI {rsi:.0f} نزل {ch1:.1f}% = CALL بكره"
        else: continue
        opts=tk.options; exp=opts[1] if len(opts)>1 else opts[0]
        exp_d=datetime.strptime(exp,"%Y-%m-%d")
        chain=tk.option_chain(exp)
        df=chain.calls if trend=="BULL" else chain.puts
        df=df[(df['lastPrice']>=0.3)&(df['lastPrice']<=6)].sort_values('volume', ascending=False).head(1)
        if df.empty: continue
        r=df.iloc[0]; vol=int(r.get('volume',0) or 0); oi=int(r.get('openInterest',0) or 0)
        if vol<150 or oi>2000 and vol<oi*0.3: continue
        new.append({"ticker":t,"strike":int(r['strike']),"type":"CALL" if trend=="BULL" else "PUT","reason":reason,"rsi":rsi,"ch1":ch1,"vol":vol,"oi":oi,"stock":curr,"price":float(r['lastPrice']),"exp":exp_d.strftime("%m/%d"),"conf":78 if rsi>=66 or rsi<=35 else 70})
        time.sleep(0.2)
    except: continue

prog.progress(100); log.empty()
st.session_state.results=sorted(new, key=lambda x: x["conf"], reverse=True)

if st.session_state.results:
    for w in st.session_state.results:
        st.markdown(f"""<div class="card">
        <b>🔔 {w['ticker']} {w['strike']} {w['type']} - {w['conf']}% | بكره عكسي مفيد | {w['reason']}</b><br>
        سهم ${w['stock']:.2f} | عقد ${w['price']:.2f} | VOL {w['vol']} OI {w['oi']} | {w['exp']}
        </div>""", unsafe_allow_html=True)
else:
    st.info("لا يوجد عكسي مفيد الآن - مثل صورتك V61 فاضي 03:14 - السوق متوازن - نام واصح 4 الفجر")

st.caption(f"V63 4AM | {ksa_str} | يفحص فقط قمة RSI>65 + صعود = PUT بكره - مثل AAPL 315 PUT 78% في صورتك")
