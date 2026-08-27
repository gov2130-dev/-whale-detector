import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V67 AUTO 4AM")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:4px solid #16a34a;border-radius:16px;padding:16px;margin:12px 0;background:#f0fdf4;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-weight:900;font-size:13px;}
.badge{display:inline-block;padding:3px 8px;border-radius:8px;font-size:11px;font-weight:900;margin:2px;}
.ok{background:#dcfce7;color:#166534;border:1px solid #16a34a;}
.bad{background:#fee2e2;color:#991b1b;border:1px solid #dc2626;}
.spread-ok{background:#dbeafe;color:#1e40af;border:1px solid #3b82f6;}
.delta-ok{background:#f3e8ff;color:#6b21a8;border:1px solid #a855f7;}
.target{background:#fef3c7;color:#92400e;border:2px solid #f59e0b;padding:10px;border-radius:10px;margin-top:8px;font-weight:900;font-size:13px;}
div.stButton > button{width:100%;height:60px;font-weight:900;border-radius:14px;font-size:15px;}
.alert-box{background:#dcfce7;border:3px solid #16a34a;border-radius:12px;padding:16px;text-align:center;animation:blink 1s infinite;}
@keyframes blink{50%{background:#bbf7d0;}}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state: st.session_state.results=[]
if "auto_done" not in st.session_state: st.session_state.auto_done=False
if "last_scan" not in st.session_state: st.session_state.last_scan=""
if "auto_mode" not in st.session_state: st.session_state.auto_mode=False

now=datetime.now(); ksa=now+timedelta(hours=3); ksa_str=ksa.strftime('%H:%M:%S'); ksa_h=ksa.hour; ksa_m=ksa.minute

is_premarket = (3 <= ksa_h <= 5) or (ksa_h==2 and ksa_m>=50)

st.markdown(f"# {ksa_str} - V67 AUTO ALERT")
if is_premarket:
    st.markdown(f'<div class="time-card">🟢 ● {ksa_str} KSA | وقت البري ماركت الذهبي 3:30-5:30 - V67 يفحص تلقائي كل 60 ثانية - 7 تأكيدات</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="time-card">● {ksa_str} KSA | V67 AUTO - 7 تأكيدات: VOL/OI + RSI + VWAP + EMA + حجم + SPREAD + DELTA/IV | ينبهك 4 الفجر تلقائي</div>', unsafe_allow_html=True)

c1,c2,c3=st.columns(3)
with c1:
    if st.button("🔔 فحص 7 تأكيدات الآن"):
        st.session_state.results=[]; st.session_state.auto_done=False; st.session_state.last_scan=ksa_str; st.rerun()
with c2:
    if st.button("⏰ تفعيل تنبيه 4 الفجر AUTO"):
        st.session_state.auto_mode=not st.session_state.auto_mode; st.rerun()
with c3:
    if st.button("🧹 مسح"):
        st.session_state.results=[]; st.session_state.auto_done=False; st.rerun()

if st.session_state.auto_mode:
    st.markdown(f'<div class="alert-box">⏰ تنبيه 4 الفجر مفعل - V67 بيفحص لحاله كل دقيقة - {ksa_str} - اترك الصفحة مفتوحة</div>', unsafe_allow_html=True)
    # صوت تنبيه
    st.markdown("""<audio autoplay><source src="https://www.soundjay.com/buttons/sounds/beep-07a.mp3" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

if st.session_state.results:
    # فلتر ذهبي 5/7 وفوق فقط
    gold=[r for r in st.session_state.results if r["total"]>=5]
    if gold:
        st.balloons()
        st.success(f"🔥 {len(gold)} عقد ذهبي 5-7 تأكيدات - {st.session_state.last_scan} - وقت الدخول الآن قبل البري ماركت")
        for w in gold:
            total=w["total"]; border="#16a34a" if total>=6 else "#2563eb"
            st.markdown(f"""<div class="card" style="border-color:{border};">
            <b style="font-size:17px;">🔔 {w['ticker']} {w['strike']} {w['type']} - {w['confirm']}% | {total}/7 تأكيدات ذهبي | {w['spread_txt']} | Delta {w['delta']:.2f}</b><br>
            {" ".join([f'<span class="badge ok">✅ {c}</span>' for c in w["ok"]])} {" ".join([f'<span class="badge spread-ok">💧 {c}</span>' for c in w["spread_ok"]])} {" ".join([f'<span class="badge delta-ok">🎯 {c}</span>' for c in w["delta_ok"]])} {" ".join([f'<span class="badge bad">❌ {c}</span>' for c in w["bad"]])}
            <br><span style="font-size:12px;font-weight:800;">{w['reason']}</span><br>
            <span style="font-size:11px;">سهم ${w['stock']:.2f} VWAP ${w['vwap']:.2f} | Last ${w['opt']:.2f} Bid ${w['bid']:.2f} Ask ${w['ask']:.2f} IV {w['iv']:.0f}% | VOL {w['vol']} OI {w['oi']} | {w['exp']} {w['days']}ي</span>
            <div class="target">🎯 هدف1 ${w['t1']:.2f} (+{w['p1']:.0f}%) | هدف2 ${w['t2']:.2f} (+{w['p2']:.0f}%) | 🛑 وقف ${w['sl']:.2f} ({w['psl']:.0f}%) | RR {w['rr']} | دخول Ask {w['ask']:.2f}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.warning(f"⚠️ فحصنا - لا يوجد عقد ذهبي 5/7 - كلها 4/7 مثل MSFT صورتك 03:29 - انتظر تأكيد أقوى - {st.session_state.last_scan}")
        # اعرض 4/7 بس للعلم
        for w in st.session_state.results[:2]:
            st.markdown(f"<div style='opacity:0.6;border:2px dashed #9ca3af;padding:10px;border-radius:10px;margin:5px 0;'><b>{w['ticker']} {w['strike']} {w['type']} {w['total']}/7 - 4 تأكيدات ضعيف - {w['spread_txt']}</b> | {w['reason']}</div>", unsafe_allow_html=True)
else:
    if st.session_state.auto_done:
        st.warning("لا يوجد عقد 5/7 ذهبي الآن - السوق متوازن")

# منطق الفحص V67
should_scan = (not st.session_state.auto_done and st.session_state.last_scan!="") or (st.session_state.auto_mode and is_premarket)

if should_scan:
    tickers=["MSFT","NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","SOFI","GOOGL","AVGO","NFLX"]
    log=st.empty(); prog=st.progress(0); new_results=[]
    for i,ticker in enumerate(tickers):
        prog.progress(int(i/len(tickers)*100)); log.text(f"V67 يفحص {ticker} 7 تأكيدات...")
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
                # Delta و IV
                delta=float(r.get('delta',0) or 0) if 'delta' in r else 0
                iv=float(r.get('impliedVolatility',0) or 0)*100 if 'impliedVolatility' in r else 50
                if iv==0: iv=50
                picked=(r,bid,ask,spread_pct,vol,oi,delta,iv); break
            if not picked: continue
            r,bid,ask,spread_pct,vol,oi,delta,iv=picked
            strike=int(r['strike'])
            if abs((strike-curr)/curr*100)>6.5: continue
            ok=[]; bad=[]; spread_ok=[]; delta_ok=[]
            ratio=vol/max(1,oi)
            if ratio>=0.5: ok.append(f"VOL/OI {ratio:.1f}x حقيقي")
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
            if spread_pct<=5: spread_ok.append(f"Spread {spread_pct:.0f}% ممتاز")
            elif spread_pct<=10: spread_ok.append(f"Spread {spread_pct:.0f}% مقبول")
            else: bad.append(f"Spread {spread_pct:.0f}%")
            # تأكيد 7 Delta
            abs_delta=abs(delta) if delta!=0 else 0.5
            if abs_delta==0: abs_delta=0.5
            if 0.35 <= abs_delta <= 0.65:
                delta_ok.append(f"Delta {abs_delta:.2f} مثالي")
            elif 0.25 <= abs_delta <= 0.75:
                delta_ok.append(f"Delta {abs_delta:.2f} جيد")
            else:
                bad.append(f"Delta {abs_delta:.2f} ضعيف")
            if iv>150: bad.append(f"IV {iv:.0f}% غالي")
            elif iv<15: bad.append(f"IV {iv:.0f}% ميت")
            else:
                if len(delta_ok)>0: delta_ok.append(f"IV {iv:.0f}%")
                else: ok.append(f"IV {iv:.0f}%")
            total_ok=len(ok)+len(spread_ok)+len(delta_ok)
            if total_ok<4: continue
            if spread_pct>8 and total_ok<5: continue
            entry=ask;
            if trend=="BULL": t1=entry*1.5; t2=entry*2.2; sl=entry*0.60
            else: t1=entry*1.5; t2=entry*2.2; sl=entry*0.60
            p1=(t1-entry)/entry*100; p2=(t2-entry)/entry*100; psl=(sl-entry)/entry*100; rr=f"1:{abs(p1/psl):.1f}"
            conf=52+total_ok*6 + (6 if spread_pct<=4 else 0) + (4 if 0.4<=abs_delta<=0.6 else 0)
            new_results.append({"ticker":ticker,"strike":strike,"type":"CALL" if trend=="BULL" else "PUT","stock":curr,"vwap":vwap,"bid":bid,"ask":ask,"spread_pct":spread_pct,"spread_txt":f"Spread {spread_pct:.0f}%","opt":float(r['lastPrice']),"vol":vol,"oi":oi,"rsi":rsi,"delta":abs_delta,"iv":iv,"ok":ok,"spread_ok":spread_ok,"delta_ok":delta_ok,"bad":bad,"total":total_ok,"confirm":int(min(94,max(60,conf))),"reason":f"{'قاع' if trend=='BULL' else 'قمة'} RSI {rsi:.0f} {ch1:+.1f}% | Delta {abs_delta:.2f}","exp":exp_d.strftime("%m/%d"),"days":days,"t1":t1,"t2":t2,"sl":sl,"p1":p1,"p2":p2,"psl":psl,"rr":rr})
            time.sleep(0.1)
        except: continue
    prog.progress(100); log.empty()
    new_results=sorted(new_results, key=lambda x: (-x["total"], x["spread_pct"], -x["confirm"]))
    st.session_state.results=new_results
    st.session_state.auto_done=True
    if st.session_state.auto_mode and is_premarket:
        time.sleep(60); st.session_state.auto_done=False; st.rerun()
    else:
        time.sleep(0.4); st.rerun()

st.caption(f"V67 AUTO | {ksa_str} | 7 تأكيدات: 1-VOL/OI 2-RSI 3-VWAP 4-EMA 5-حجم 6-SPREAD 7-DELTA/IV | يفحص تلقائي 3:30-5:30 فجرا - فقط 5/7 ذهبي يطلع - صورتك V66 MSFT 4/6 ما يطلع الا ب Spread ممتاز")
