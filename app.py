import streamlit as st, yfinance as yf, pandas as pd, os, requests, math
from datetime import datetime, date
import pytz

st.set_page_config(layout="wide", page_title="Whale V700 ALL-IN")
st.title("👑 حوت 54 - V700 شامل (0DTE + BW + Sweep + OI)")

# --- Settings ---
with st.sidebar:
    st.header("⚙️ الفلاتر")
    min_oi = st.slider("💎 اقل OI", 500, 30000, 5000, 500)
    min_vol = st.slider("📊 اقل Vol", 0, 1000, 0, 10)
    min_prem = st.slider("💰 اقل بريميوم $ (Sweep)", 0, 200000, 25000, 5000)
    max_bw = st.slider("📏 اقصى BW% (قرب من السعر)", 1, 15, 6)
    max_dte = st.slider("⏰ اقصى DTE (0=اليوم)", 0, 14, 7)
    
    st.divider()
    only_0dte = st.checkbox("🔥 0DTE فقط (اليوم)", False)
    only_sweep = st.checkbox("⚡ Sweep فقط (>25k$)", False)
    only_gems = st.checkbox("💎 جواهر فقط OI>2xVol + BW<5", True)
    
    tickers_sel = st.multiselect("الشركات", ["SPY","QQQ","NVDA","TSLA","AAPL","AMD","META","MSFT","PLTR","COIN","MSTR","GOOGL","AMZN","NFLX","AVGO"], default=["SPY","QQQ","NVDA"])

# --- Logic ---
def days_to_exp(exp_str):
    try: return (datetime.strptime(exp_str, "%Y-%m-%d").date() - date.today()).days
    except: return 99

if st.sidebar.button("🚀 فحص V700 الآن", type="primary", use_container_width=True):
    rows=[]; bar=st.progress(0); log=st.empty()
    for i,t in enumerate(tickers_sel):
        log.write(f"يفحص {t}... {i+1}/{len(tickers_sel)}"); bar.progress((i+1)/len(tickers_sel))
        try:
            tk=yf.Ticker(t)
            hist=tk.history(period="2d")
            S=float(hist['Close'].iloc[-1]) if not hist.empty else 0
            if S==0 or not tk.options: continue
            for exp in tk.options[:4]:
                dte=days_to_exp(exp)
                if dte<0 or dte>max_dte: continue
                if only_0dte and dte!=0: continue
                try:
                    chain=tk.option_chain(exp)
                    for side_name, df in [("C",chain.calls), ("P",chain.puts)]:
                        for _,r in df.iterrows():
                            oi=int(r.get('openInterest',0) or 0)
                            vol=int(r.get('volume',0) or 0)
                            last=float(r.get('lastPrice',0) or 0)
                            strike=float(r['strike'])
                            if oi<min_oi and vol<min_vol: continue
                            prem = vol*last*100
                            if prem < min_prem and only_sweep: continue
                            if only_sweep and prem < 25000: continue
                            bw = abs(strike-S)/S*100
                            if bw>max_bw: continue
                            ratio = oi/max(vol,1)
                            is_sweep = prem>=25000 and vol>=50
                            is_gem = ratio>=2 and bw<=5 and oi>=5000
                            if only_gems and not is_gem and not is_sweep: continue
                            
                            tag=[]
                            if dte==0: tag.append("🔥0DTE")
                            if is_sweep: tag.append("⚡SWEEP")
                            if is_gem: tag.append("💎جوهرة")
                            if ratio>1.5: tag.append(f"OI/Vol {ratio:.1f}x")
                            
                            rows.append({
                                "T":t, "Side":side_name, "Strike":strike, "S":round(S,1),
                                "Exp":exp, "DTE":dte, "OI":oi, "Vol":vol, "Price":last,
                                "Prem $":int(prem), "BW%":round(bw,1), "Tags":" ".join(tag),
                                "is_gem":is_gem, "is_sweep":is_sweep
                            })
                except: continue
        except: continue
    bar.empty(); log.empty()
    
    if rows:
        df=pd.DataFrame(rows)
        # ترتيب: جواهر اول + سويب ثاني + بريميوم
        df = df.sort_values(by=["is_gem","is_sweep","Prem $"], ascending=[False,False,False])
        
        st.success(f"✅ لقى {len(df)} عقد - {len(df[df['is_gem']])} جوهرة 💎 + {len(df[df['is_sweep']])} سويب ⚡")
        
        # 3 جداول
        c1,c2,c3 = st.columns(3)
        with c1:
            st.subheader("💎 جواهر (تجميع)")
            st.dataframe(df[df['is_gem']].head(20)[["T","Strike","Exp","OI","Vol","BW%","Tags"]], use_container_width=True)
        with c2:
            st.subheader("⚡ سويب (سيولة داخلة)")
            st.dataframe(df[df['is_sweep']].head(20)[["T","Strike","Prem $","Vol","Price","Tags"]], use_container_width=True)
        with c3:
            st.subheader("🔥 0DTE اليوم")
            st.dataframe(df[df['DTE']==0].head(20)[["T","Strike","S","Price","Vol","Tags"]], use_container_width=True)
        
        st.divider()
        st.subheader("📋 الكل")
        st.dataframe(df.drop(columns=["is_gem","is_sweep"]), use_container_width=True, height=500)
    else:
        st.warning("ما لقى - نزل OI الى 500 و Prem الى 0 وجرب SPY QQQ بس لأن اليوم ويكند")
else:
    st.info("👈 من اليسار: اختر الشركات وشغل الفلاتر اللي تبغى واضغط 🚀 فحص V700 الآن")
    st.markdown("""
    **وش يسوي V700:**
    - **💎 جواهر:** OI اكبر من Vol بضعف + قريب من السعر (BW<5%) = حوت مجمع
    - **⚡ Sweep:** صفقة وحدة كبيرة > $25k دخلت = سيولة ذكية
    - **🔥 0DTE:** عقود تنتهي اليوم = انفجار سريع للسكالبينج
    - **📏 BW:** كل ما قل كل ما الانفجار اقرب
    """)
