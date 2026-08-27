import streamlit as st, yfinance as yf, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V66 TARGET")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #16a34a;border-radius:14px;padding:14px;margin:10px 0;background:#f0fdf4;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-weight:900;}
.badge{display:inline-block;padding:2px 7px;border-radius:8px;font-size:10px;font-weight:900;margin:2px;}
.ok{background:#dcfce7;color:#166534;border:1px solid #16a34a;}
.bad{background:#fee2e2;color:#991b1b;border:1px solid #dc2626;}
.spread-ok{background:#dbeafe;color:#1e40af;border:1px solid #3b82f6;}
.target{background:#fef3c7;color:#92400e;border:1px solid #f59e0b;padding:8px;border-radius:8px;margin-top:6px;font-weight:900;}
div.stButton > button{width:100%;height:56px;font-weight:900;border-radius:12px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "auto_done" not in st.session_state: st.session_state.auto_done=False
if "last_scan" not in st.session_state: st.session_state.last_scan=""

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S')

st.markdown(f"# {ksa_str} - V66 TARGET + STOP")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | V66 - 6 تأكيدات + هدف ووقف تلقائي - يحسب لك ربح 40% و 80%</div>', unsafe_allow_html=True)

if st.button("🔔 فحص 6 تأكيدات + هدف ووقف"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.session_state.last_scan=ksa_str; st.rerun()
if st.button("🧹 مسح"):
    st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.results:
    st.success(f"✅ {len(st.session_state.results)} عقد - {st.session_state.last_scan}")
    for w in st.session_state.results:
        st.markdown(f"""<div class="card" style="border-color:#16a34a;border-width:4px;">
        <b>🔔 {w['ticker']} {w['strike']} {w['type']} - {w['confirm']}% | {w['total']}/6 | {w['spread_txt']}</b><br>
        {" ".join([f'<span class="badge ok">✅ {c}</span>' for c in w["ok"]])} {" ".join([f'<span class="badge spread-ok">💧 {c}</span>' for c in w["spread_ok"]])} {" ".join([f'<span class="badge bad">❌ {c}</span>' for c in w["bad"]])}
        <br><span style="font-size:11px;font-weight:700;">{w['reason']}</span><br>
        <span style="font-size:11px;">سهم ${w['stock']:.2f} | Last ${w['opt']:.2f} Bid ${w['bid']:.2f} Ask ${w['ask']:.2f} | VOL {w['vol']} OI {w['oi']} | {w['exp']}</span>
        <div class="target">🎯 هدف1 ${w['t1']:.2f} (+{w['p1']:.0f}%) | هدف2 ${w['t2']:.2f} (+{w['p2']:.0f}%) | 🛑 وقف ${w['sl']:.2f} ({w['psl']:.0f}%) | نسبة مخاطرة {w['rr']}</div>
        </div>""", unsafe_allow_html=True)

if not st.session_state.auto_done and st.session_state.last_scan!="":
    tickers=["MSFT","NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","SOFI","GOOGL"]
    log=st.empty(); prog=st.progress(0); new_results=[]
    for i,ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100)); log.text(f"V66 {ticker}...")
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
            df=df[(df['lastPrice']>=0.30)&(df['lastPrice']<=8)]
            if df.empty or 'bid' not in df.columns: continue
            df=df.sort_values('volume', ascending=False).head(4); picked=None
            for _, r in df.iterrows():
                vol=int(r.get('volume',0) or 0);
                if vol<200: continue
                bid=float(r.get('bid',0) or 0); ask=float(r.get('ask',0) or 0)
                if bid<=0 or ask<=0 or bid>=ask: continue
                mid=(bid+ask)/2; spread_pct=(ask-bid)/mid*100
                if spread_pct>18: continue
                oi=int(r.get('openInterest',0) or 0)
                if oi>2000 and vol < oi*0.25: continue
                picked=(r,bid,ask,spread_pct,vol,oi); break
            if not picked: continue
            r,bid,ask,spread_pct,vol,oi=picked
            if abs((int(r['strike'])-curr)/curr*100)>7: continue
            ok=[]; bad=[]; spread_ok=[]
            ratio=vol/max(1,oi)
            if ratio>=0.45: ok.append(f"VOL/OI {ratio:.1f}x")
            else: bad.append(f"VOL/OI {ratio:.1f}x")
            if (trend=="BULL" and rsi<=32) or (trend=="BEAR" and rsi>=70): ok.append(f"RSI {rsi:.0f} قوي")
            elif (trend=="BULL" and rsi<=42) or (trend=="BEAR" and rsi>=63): ok.append(f"RSI {rsi:.0f} جيد")
            else: bad.append(f"RSI {rsi:.0f}")
            if (trend=="BULL" and curr < vwap*0.98) or (trend=="BEAR" and curr > vwap*1.02): ok.append(f"VWAP {((curr-vwap)/vwap*100):+.1f}%")
            else: bad.append(f"VWAP {((curr-vwap)/vwap*100):+.1f}% قريب")
            if (trend=="BULL" and ema9 < ema21) or (trend=="BEAR" and ema9 > ema21): ok.append("EMA عكسي")
            else: bad.append("EMA نفس")
            if vol_ratio>=1.2: ok.append(f"حجم {vol_ratio:.1f}x")
            else: bad.append(f"حجم {vol_ratio:.1f}x")
            if spread_pct<=6: spread_ok.append(f"Spread {spread_pct:.0f}% ممتاز")
            elif spread_pct<=12: spread_ok.append(f"Spread {spread_pct:.0f}% مقبول")
            else: bad.append(f"Spread {spread_pct:.0f}%")
            total_ok=len(ok)+len(spread_ok)
            if total_ok<4: continue
            # هدف ووقف
            entry=ask
            if trend=="BULL":
                t1=entry*1.4; t2=entry*1.8; sl=entry*0.65
            else:
                t1=entry*1.4; t2=entry*2.0; sl=entry*0.64
            p1=(t1-entry)/entry*100; p2=(t2-entry)/entry*100; psl=(sl-entry)/entry*100
            rr=f"1:{abs(p1/psl):.1f}"
            conf=56+total_ok*6 + (7 if spread_pct<=5 else 0)
            new_results.append({"ticker":ticker,"strike":int(r['strike']),"type":"CALL" if trend=="BULL" else "PUT","stock":curr,"bid":bid,"ask":ask,"spread_pct":spread_pct,"spread_txt":f"Spread {spread_pct:.0f}%","opt":float(r['lastPrice']),"vol":vol,"oi":oi,"rsi":rsi,"ok":ok,"spread_ok":spread_ok,"bad":bad,"total":total_ok,"confirm":int(min(92,conf)),"reason":f"{'قاع' if trend=='BULL' else 'قمة'} RSI {rsi:.0f} {ch1:+.1f}%","exp":exp_d.strftime("%m/%d"),"t1":t1,"t2":t2,"sl":sl,"p1":p1,"p2":p2,"psl":psl,"rr":rr})
            time.sleep(0.12)
        except: continue
    prog.progress(100); log.empty()
    st.session_state.results=sorted(new_results, key=lambda x: (-x["total"], x["spread_pct"]))
    st.session_state.auto_done=True; time.sleep(0.3); st.rerun()

st.caption(f"V66 | {ksa_str} | 6 تأكيدات + هدف/وقف - عقدك MSFT 490 PUT في الصورة = هدف 40% وقف -36%")
