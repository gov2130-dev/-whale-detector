import streamlit as st, yfinance as yf, pandas as pd, time
from datetime import datetime, timedelta

st.set_page_config(layout="wide", page_title="V65 6 CONFIRMS FINAL")
st.markdown("""<style>
.stApp{background:#fff!important;}
.card{border:3px solid #000;border-radius:14px;padding:14px;margin:10px 0;background:#fff;color:#000;}
.time-card{background:#111;color:#4ade80;border-radius:12px;padding:12px;text-align:center;font-family:monospace;border:2px solid #22c55e;font-weight:900;font-size:13px;}
.badge{display:inline-block;padding:2px 7px;border-radius:8px;font-size:10px;font-weight:900;margin:2px;}
.ok{background:#dcfce7;color:#166534;border:1px solid #16a34a;}
.bad{background:#fee2e2;color:#991b1b;border:1px solid #dc2626;}
.spread-ok{background:#dbeafe;color:#1e40af;border:1px solid #3b82f6;}
div.stButton > button{width:100%;height:56px;font-weight:900;border-radius:12px;font-size:14px;}
</style>""", unsafe_allow_html=True)

if "results" not in st.session_state:
    st.session_state.results=[]
if "auto_done" not in st.session_state:
    st.session_state.auto_done=False
if "last_scan" not in st.session_state:
    st.session_state.last_scan=""

now=datetime.now()
ksa=now+timedelta(hours=3)
ksa_str=ksa.strftime('%H:%M:%S')
ksa_date=ksa.strftime('%Y-%m-%d')

st.markdown(f"# {ksa_str} - V65 FINAL")
st.markdown(f'<div class="time-card">● {ksa_str} KSA | {ksa_date} | V65 FINAL 6 تأكيدات: VOL/OI + RSI + VWAP + EMA + حجم + BID/ASK SPREAD | قبل البري ماركت 4 الفجر | يحميك من السبريد الواسع</div>', unsafe_allow_html=True)

col1,col2=st.columns(2)
with col1:
    if st.button("🔔 فحص 6 تأكيدات - 12 شركة"):
        st.session_state.results=[]
        st.session_state.auto_done=False
        st.session_state.last_scan=ksa_str
        st.rerun()
with col2:
    if st.button("🧹 مسح"):
        st.session_state.results=[]
        st.session_state.auto_done=False
        st.rerun()

# عرض النتائج
if st.session_state.results:
    st.success(f"✅ {len(st.session_state.results)} عقد مؤكد - 4-6 تأكيدات - Spread ضيق - فحص {st.session_state.last_scan} - {ksa_str}")
    for w in st.session_state.results:
        total=w["total_conf"]
        if total>=5:
            border="#16a34a"
            bg="#f0fdf4"
        elif total==4:
            border="#2563eb"
            bg="#eff6ff"
        else:
            border="#d97706"
            bg="#fffbeb"
        
        st.markdown(f"""
        <div class="card" style="border-color:{border};background:{bg};border-width:4px;">
            <b style="font-size:16px;">🔔 {w['ticker']} {w['strike']} {w['type']} - {w['confirm']}% | {total}/6 تأكيدات | {w['spread_txt']} | {w['vol']/max(1,w['oi']):.1f}x حقيقي</b><br>
            <div style="margin:6px 0;">
                {" ".join([f'<span class="badge ok">✅ {c}</span>' for c in w["ok"]])}
                {" ".join([f'<span class="badge spread-ok">💧 {c}</span>' for c in w["spread_ok"]])}
                {" ".join([f'<span class="badge bad">❌ {c}</span>' for c in w["bad"]])}
            </div>
            <span style="font-size:12px;font-weight:800;color:#111;">{w['reason']}</span><br>
            <span style="font-size:11px;">سهم ${w['stock']:.2f} VWAP ${w['vwap']:.2f} EMA9 {w['ema9']:.2f} | عقد Last ${w['opt']:.2f} Bid ${w['bid']:.2f} Ask ${w['ask']:.2f} Spread {w['spread_pct']:.0f}% | VOL {w['vol']} OI {w['oi']} | {w['exp']} {w['days']}ي</span>
        </div>
        """, unsafe_allow_html=True)
else:
    if st.session_state.auto_done:
        st.warning(f"⚠️ فحصنا 12 شركة - لا يوجد عقد يحقق 4/6 تأكيدات - السوق متوازن - آخر فحص {st.session_state.last_scan}")
    else:
        st.info("⏳ V65 جاهز - اضغط فحص 6 تأكيدات - بيطلع فقط عقود Spread ضيق أقل من 15% + 4 تأكيدات")

# الفحص
if not st.session_state.auto_done and st.session_state.last_scan=="":
    st.markdown("---")
    st.markdown("### 🔍 V65 يفحص الآن 6 تأكيدات...")

if not st.session_state.auto_done and st.session_state.last_scan!="":
    tickers=["NVDA","AAPL","HOOD","COIN","MSTR","PLTR","TSLA","META","AMD","SOFI","GOOGL","MSFT"]
    log=st.empty()
    prog=st.progress(0)
    new_results=[]
    
    for i,ticker in enumerate(tickers):
        prog.progress(int((i)/len(tickers)*100))
        log.text(f"V65 يفحص {ticker} {i+1}/{len(tickers)} + 6 تأكيدات + Spread...")
        try:
            tk=yf.Ticker(ticker)
            h=tk.history(period="20d")
            if len(h)<15:
                time.sleep(0.1)
                continue
            
            curr=float(h['Close'].iloc[-1])
            prev=float(h['Close'].iloc[-2])
            ch1=float((curr-prev)/prev*100)
            
            # RSI
            d=h['Close'].diff()
            g=d.where(d>0,0).ewm(alpha=1/14).mean()
            l=(-d.where(d<0,0)).ewm(alpha=1/14).mean()
            rsi=float(100-(100/(1+float(g.iloc[-1])/(float(l.iloc[-1])+0.01))))
            
            # VWAP 10
            vwap=float(h['Close'].tail(10).mean())
            # EMA
            ema9=float(h['Close'].ewm(span=9).mean().iloc[-1])
            ema21=float(h['Close'].ewm(span=21).mean().iloc[-1])
            # حجم
            vol_today=float(h['Volume'].iloc[-1])
            vol_avg=float(h['Volume'].tail(10).mean())
            vol_ratio=vol_today/vol_avg if vol_avg>0 else 1.0

            # فقط عكسي
            trend=None
            if rsi<=42 and ch1<=-0.5:
                trend="BULL"
            elif rsi>=63 and ch1>=0.5:
                trend="BEAR"
            else:
                time.sleep(0.05)
                continue

            opts=tk.options
            if not opts:
                continue
            exp=opts[1] if len(opts)>1 else opts[0]
            exp_d=datetime.strptime(exp,"%Y-%m-%d")
            days=(exp_d-datetime.now()).days
            if days<1 or days>8:
                continue
            
            chain=tk.option_chain(exp)
            df=chain.calls if trend=="BULL" else chain.puts
            df=df[(df['lastPrice']>=0.30) & (df['lastPrice']<=8)]
            if df.empty:
                continue
            if 'bid' not in df.columns or 'ask' not in df.columns:
                continue
            
            df=df.sort_values('volume', ascending=False).head(4)
            picked=None
            for _, r in df.iterrows():
                vol=int(r.get('volume',0) or 0)
                if vol<200:
                    continue
                bid=float(r.get('bid',0) or 0)
                ask=float(r.get('ask',0) or 0)
                if bid<=0 or ask<=0:
                    continue
                if bid>=ask:
                    continue
                mid=(bid+ask)/2
                if mid==0:
                    continue
                spread_pct=(ask-bid)/mid*100
                oi=int(r.get('openInterest',0) or 0)
                # فلتر Spread
                if spread_pct>18:
                    continue
                if spread_pct>12 and vol<800:
                    continue
                # فلتر تحوط
                if oi>2000 and vol < oi*0.25:
                    continue
                picked=(r,bid,ask,spread_pct,vol,oi)
                break
            
            if not picked:
                continue
            
            r,bid,ask,spread_pct,vol,oi=picked
            strike=int(r['strike'])
            dist=(strike-curr)/curr*100
            if abs(dist)>7:
                continue

            ok=[]
            bad=[]
            spread_ok=[]

            # 1 VOL/OI
            ratio=vol/max(1,oi)
            if ratio>=0.45:
                ok.append(f"VOL/OI {ratio:.1f}x حقيقي")
            else:
                bad.append(f"VOL/OI {ratio:.1f}x تحوط")

            # 2 RSI
            if (trend=="BULL" and rsi<=32) or (trend=="BEAR" and rsi>=70):
                ok.append(f"RSI {rsi:.0f} قوي")
            elif (trend=="BULL" and rsi<=42) or (trend=="BEAR" and rsi>=63):
                ok.append(f"RSI {rsi:.0f} جيد")
            else:
                bad.append(f"RSI {rsi:.0f}")

            # 3 VWAP
            vwap_diff=(curr-vwap)/vwap*100
            if (trend=="BULL" and curr < vwap*0.98) or (trend=="BEAR" and curr > vwap*1.02):
                ok.append(f"VWAP {vwap_diff:+.1f}%")
            else:
                bad.append(f"VWAP {vwap_diff:+.1f}% قريب")

            # 4 EMA
            if (trend=="BULL" and ema9 < ema21) or (trend=="BEAR" and ema9 > ema21):
                ok.append("EMA عكسي جاهز")
            else:
                bad.append("EMA نفس الاتجاه")

            # 5 حجم اليوم
            if vol_ratio>=1.2:
                ok.append(f"حجم {vol_ratio:.1f}x عالي")
            else:
                bad.append(f"حجم {vol_ratio:.1f}x ضعيف")

            # 6 SPREAD
            if spread_pct<=6:
                spread_ok.append(f"Spread {spread_pct:.0f}% ضيق ممتاز")
            elif spread_pct<=12:
                spread_ok.append(f"Spread {spread_pct:.0f}% مقبول")
            else:
                bad.append(f"Spread {spread_pct:.0f}% واسع")

            total_ok=len(ok)+len(spread_ok)
            if total_ok<4:
                continue
            if spread_pct>10 and total_ok<5:
                continue

            conf=56 + total_ok*6
            if spread_pct<=5:
                conf+=7
            if rsi<=25 or rsi>=75:
                conf+=7
            if ratio>=2.5:
                conf+=5
            if vol_ratio>=1.5:
                conf+=3

            reason=f"{'قاع' if trend=='BULL' else 'قمة'} RSI {rsi:.0f} {ch1:+.1f}% + {' | '.join(ok[:2])} + {spread_ok[0] if spread_ok else ''}"

            new_results.append({
                "ticker":ticker,
                "strike":strike,
                "type":"CALL" if trend=="BULL" else "PUT",
                "stock":curr,
                "vwap":vwap,
                "ema9":ema9,
                "bid":bid,
                "ask":ask,
                "spread_pct":spread_pct,
                "spread_txt":f"Spread {spread_pct:.0f}%",
                "opt":float(r['lastPrice']),
                "vol":vol,
                "oi":oi,
                "rsi":rsi,
                "ch1":ch1,
                "ok":ok,
                "spread_ok":spread_ok,
                "bad":bad,
                "total_conf":total_ok,
                "confirm":int(min(92,max(62,conf))),
                "reason":reason,
                "exp":exp_d.strftime("%m/%d"),
                "days":days
            })
            time.sleep(0.12)
        except Exception as e:
            time.sleep(0.1)
            continue
    
    prog.progress(100)
    log.empty()
    # ترتيب: أكثر تأكيدات + أقل سبريد + أعلى ثقة
    new_results=sorted(new_results, key=lambda x: (-x["total_conf"], x["spread_pct"], -x["confirm"]))
    st.session_state.results=new_results
    st.session_state.auto_done=True
    time.sleep(0.4)
    st.rerun()

st.caption(f"V65 FINAL FULL | {ksa_str} KSA | 6 تأكيدات: 1-VOL/OI حقيقي>0.45x 2-RSI قاع<=42 قمة>=63 3-VWAP بعيد 4-EMA عكسي 5-حجم>=1.2x 6-Spread<=12% ضيق | قبل البري ماركت 4 الفجر - يحميك من سبريد واسع ياكلك 30%")
