import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="V82 مطرقة + أوبشن", layout="wide")
st.title("🎯💰 V82 - مطرقة صارمة + عقد الأوبشن المتوافق")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=15)
    except: pass

if "results" not in st.session_state:
    st.session_state.results = []

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["15 دقيقة","30 دقيقة","ساعة","يومي"])
tf_map = {name:(code,period) for code,name,period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

st.markdown("### إعدادات عقد الأوبشن المتوافق")
col1, col2, col3 = st.columns(3)
with col1:
    min_vol = st.number_input("أقل فوليوم للعقد", value=200)
    min_premium = st.number_input("أقل بريميوم (مجموع $)", value=20000)
with col2:
    exp_days = st.slider("الاكسبايري خلال كم يوم", 1, 21, 7, help="7 أيام = أسبوعي")
    otm_pct = st.slider("بعد السترايك عن السعر %", -5, 10, 2, help="2% = خارج المال بشوي")
with col3:
    min_bid = st.number_input("أقل Bid", value=0.2)
    max_price = st.number_input("أعلى سعر للعقد", value=5.0)

def is_strict_hammer(c_ham, c_prev, direction):
    body = abs(c_ham['Close']-c_ham['Open'])
    if body==0: return False, 0
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0: return False, 0
    if direction=="CALL":
        ok = (lower >= body*2.0) and (body <= total*0.4) and (lower >= total*0.5) and (c_ham['Volume'] > c_prev['Volume']*1.1)
        return ok, lower/body
    else:
        ok = (upper >= body*2.0) and (body <= total*0.4) and (upper >= total*0.5) and (c_ham['Volume'] > c_prev['Volume']*1.1)
        return ok, upper/body

def check_final(df):
    if len(df) < 4: return None
    c_prev = df.iloc[-3]; c_ham = df.iloc[-2]; c_next = df.iloc[-1]
    ok_call, r1 = is_strict_hammer(c_ham, c_prev, "CALL")
    if ok_call and c_next['Close'] > c_ham['High']:
        return {"dir":"CALL", "type":f"CALL 🟢 {r1:.1f}x سفلي", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":r1}
    ok_put, r2 = is_strict_hammer(c_ham, c_prev, "PUT")
    if ok_put and c_next['Close'] < c_ham['Low']:
        return {"dir":"PUT", "type":f"PUT 🔴 {r2:.1f}x علوي", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":r2}
    return None

def get_compatible_option(tk, spot, direction):
    try:
        # نجيب اكسبايريات قريبة
        exps = tk.options[:4] # أول 4 اكسبايريات
        best = None
        best_score = -1

        for exp in exps:
            chain = tk.option_chain(exp)
            df_opt = chain.calls if direction=="CALL" else chain.puts
            df_opt = df_opt.copy()
            if len(df_opt)==0: continue

            # فلترة متوافقة مع اتجاه المطرقة
            df_opt['premium'] = df_opt['volume'].fillna(0) * df_opt['lastPrice'] * 100
            df_opt['otm_pct'] = (df_opt['strike'] - spot)/spot*100 if direction=="CALL" else (spot - df_opt['strike'])/spot*100

            # شروط العقد المتوافق
            filt = df_opt[
                (df_opt['volume'].fillna(0) >= min_vol) &
                (df_opt['bid'].fillna(0) >= min_bid) &
                (df_opt['lastPrice'] <= max_price) &
                (df_opt['lastPrice'] >= 0.1) &
                (df_opt['premium'] >= min_premium) &
                (df_opt['otm_pct'] >= otm_pct-2) & (df_opt['otm_pct'] <= otm_pct+5) # قريب من السعر
            ]

            if len(filt)==0: continue

            # نختار العقد اللي عليه أكثر بريميوم + فوليوم
            filt = filt.sort_values(['premium','volume'], ascending=False)
            top = filt.iloc[0]

            score = top['premium'] + top['volume']
            if score > best_score:
                best_score = score
                best = (top, exp)

        return best
    except Exception as e:
        return None

if st.button(f"🚀 افحص {len(UNIVERSE)} سهم + عقود متوافقة"):
    all_res=[]
    prog=st.progress(0)
    cnt=0
    total=len(UNIVERSE)*len(selected_codes)
    for sym in UNIVERSE:
        tk = yf.Ticker(sym)
        try:
            spot = tk.history(period="1d", interval="1m")['Close'].iloc[-1]
        except:
            continue
        for (code,period),name in zip(selected_codes,selected_tfs):
            cnt+=1; prog.progress(cnt/total)
            try:
                df=tk.history(period=period, interval=code)
                pat=check_final(df)
                if pat:
                    opt = get_compatible_option(tk, spot, pat['dir'])
                    if opt:
                        top, exp = opt
                        all_res.append({
                            "سهم":sym, "فريم":name, "اتجاه":pat['type'],
                            "سعر":f"${spot:.2f}",
                            "وقت إغلاق التأكيد":str(pat['next'].name)[5:16],
                            "ذيل":f"{pat['ratio']:.1f}x",
                            "سترايك":f"{top['strike']}",
                            "اكسبايري":exp,
                            "سعر العقد":f"${top['lastPrice']:.2f}",
                            "Bid":f"{top['bid']:.2f}",
                            "Vol":f"{int(top['volume']):,}",
                            "بريميوم":f"${top['premium']:,.0f}",
                            "OTM%":f"{(top['strike']-spot)/spot*100:.1f}%" if pat['dir']=="CALL" else f"{(spot-top['strike'])/spot*100:.1f}%",
                            "_top":top, "_exp":exp, "_dir":pat['dir']
                        })
                    else:
                        # مطرقة بدون عقد متوافق (ما نعرضها لأنك طلبت عقود فقط)
                        pass
            except: continue
    prog.empty()
    st.session_state.results=all_res

if st.session_state.results:
    df_show = pd.DataFrame(st.session_state.results)[["سهم","فريم","اتجاه","ذيل","سعر","سترايك","اكسبايري","سعر العقد","Vol","بريميوم","OTM%","وقت إغلاق التأكيد"]]
    st.success(f"لقيت {len(st.session_state.results)} مطرقة صارمة + عقد متوافق بعد إغلاق التأكيد مباشرة")
    st.dataframe(df_show, use_container_width=True)

    for r in st.session_state.results:
        msg = f"{'🟢' if r['_dir']=='CALL' else '🔴'} <b>{r['سهم']} {r['اتجاه']} فريم {r['فريم']}</b>\nذيل {r['ذيل']} | وقت {r['وقت إغلاق التأكيد']} | سعر {r['سعر']}\n💰 عقد متوافق: {r['سترايك']} {r['_dir']} Exp {r['اكسبايري']}\nسعر ${r['سعر العقد']} Vol {r['Vol']} بريميوم {r['بريميوم']} {r['OTM%']} OTM\nBid {r['Bid']}"
        send_telegram(msg)

    st.balloons()
else:
    st.warning("بالشروط الصارمة + فلتر الأوبشن ما فيه مطرقة متوافقة الآن")
    st.info("خفف: قلل أقل فوليوم من 200 إلى 50، أو زود أعلى سعر للعقد من 5 إلى 10، أو خلي OTM من 2% إلى 5%")

st.caption("AMD اللي في صورتك ما راح تطلع لأنه ما فيه مطرقة صارمة + حتى لو فيه، ما عليه عقد فوليوم عالي")
