import streamlit as st
import yfinance as yf
import pandas as pd
import requests

st.set_page_config(page_title="V82 مضبوط", layout="wide")
st.title("🎯 V82 مضبوط - شروط السهم + شروط الأوبشن")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

if "results" not in st.session_state:
    st.session_state.results = []

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["15 دقيقة","30 دقيقة","ساعة"])

# ========= 1- ضبط شروط السهم =========
st.divider()
st.subheader("1️⃣ شروط المطرقة (السهم)")

c1,c2,c3,c4 = st.columns(4)
with c1:
    tail_mult = st.slider("الذيل >= كم ضعف الجسم", 1.0, 3.0, 2.0, 0.1)
with c2:
    body_pct = st.slider("الجسم <= كم % من الشمعة", 20, 60, 40, 5)
with c3:
    vol_mult = st.slider("الفوليوم > السابق *", 1.0, 2.0, 1.1, 0.1)
with c4:
    tail_total_pct = st.slider("الذيل >= كم % من الشمعة كاملة", 30, 70, 50, 5)

confirm_type = st.radio("نوع التأكيد بعد الإغلاق", ["فوق قمة المطرقة (صارم)", "فوق إغلاق المطرقة (سريع)"], index=0, horizontal=True)

# ========= 2- ضبط شروط الأوبشن =========
st.divider()
st.subheader("2️⃣ شروط عقد الأوبشن المتوافق")
c1,c2,c3,c4 = st.columns(4)
with c1:
    min_opt_vol = st.number_input("أقل فوليوم عقد", 100, 5000, 300, 100)
    min_oi = st.number_input("أقل Open Interest", 500, 20000, 1000, 500)
with c2:
    min_bid = st.number_input("أقل Bid", 0.05, 2.0, 0.15, 0.05)
    max_spread = st.slider("أكبر فرق Bid-Ask %", 5, 50, 20)
with c3:
    dte_min = st.slider("DTE من", 0, 14, 1)
    dte_max = st.slider("DTE إلى", 1, 21, 7)
with c4:
    otm_min = st.slider("OTM من %", -5, 10, 0)
    otm_max = st.slider("OTM إلى %", 0, 15, 5)
    max_contract_price = st.number_input("أعلى سعر عقد", 0.5, 20.0, 4.0, 0.5)

tf_map = {name:(code,period) for code,name,period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

def is_hammer(c_ham, c_prev, direction):
    body = abs(c_ham['Close']-c_ham['Open'])
    if body==0: return False, 0, {}
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0: return False, 0, {}

    details = {
        "tail_ratio": lower/body if direction=="CALL" else upper/body,
        "body_pct": body/total*100,
        "tail_pct": lower/total*100 if direction=="CALL" else upper/total*100,
        "vol_ratio": c_ham['Volume']/c_prev['Volume'] if c_prev['Volume']>0 else 0
    }

    if direction=="CALL":
        ok = (lower >= body*tail_mult) and (body/total*100 <= body_pct) and (lower/total*100 >= tail_total_pct) and (c_ham['Volume'] >= c_prev['Volume']*vol_mult)
    else:
        ok = (upper >= body*tail_mult) and (body/total*100 <= body_pct) and (upper/total*100 >= tail_total_pct) and (c_ham['Volume'] >= c_prev['Volume']*vol_mult)

    return ok, details["tail_ratio"], details

def check_final(df):
    if len(df) < 4: return None
    c_prev, c_ham, c_next = df.iloc[-3], df.iloc[-2], df.iloc[-1]

    for direction in ["CALL","PUT"]:
        ok, ratio, det = is_hammer(c_ham, c_prev, direction)
        if not ok: continue

        if direction=="CALL":
            confirmed = c_next['Close'] > c_ham['High'] if "قمة" in confirm_type else c_next['Close'] > c_ham['Close']
        else:
            confirmed = c_next['Close'] < c_ham['Low'] if "قمة" in confirm_type else c_next['Close'] < c_ham['Close']

        if confirmed:
            return {"dir":direction, "type":f"{direction} {'🟢' if direction=='CALL' else '🔴'} {ratio:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":ratio, "det":det}
    return None

def get_compatible_option(tk, spot, direction):
    try:
        options = tk.options
        if not options: return None
        from datetime import datetime
        today = datetime.now().date()
        best = None

        for exp_str in options[:5]:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if not (dte_min <= dte <= dte_max): continue

            chain = tk.option_chain(exp_str)
            df_opt = chain.calls if direction=="CALL" else chain.puts
            if df_opt.empty: continue

            df_opt = df_opt.copy()
            df_opt['bid'] = df_opt['bid'].fillna(0)
            df_opt['ask'] = df_opt['ask'].fillna(0)
            df_opt['volume'] = df_opt['volume'].fillna(0)
            df_opt['openInterest'] = df_opt['openInterest'].fillna(0)
            df_opt['spread_pct'] = ((df_opt['ask']-df_opt['bid'])/df_opt['ask']*100).fillna(100)

            # OTM%
            if direction=="CALL":
                df_opt['otm_pct'] = (df_opt['strike']-spot)/spot*100
            else:
                df_opt['otm_pct'] = (spot-df_opt['strike'])/spot*100

            filt = df_opt[
                (df_opt['volume'] >= min_opt_vol) &
                (df_opt['openInterest'] >= min_oi) &
                (df_opt['bid'] >= min_bid) &
                (df_opt['lastPrice'] <= max_contract_price) &
                (df_opt['lastPrice'] >= 0.1) &
                (df_opt['spread_pct'] <= max_spread) &
                (df_opt['otm_pct'] >= otm_min) & (df_opt['otm_pct'] <= otm_max)
            ]
            if filt.empty: continue
            filt = filt.sort_values(['volume','openInterest'], ascending=False)
            top = filt.iloc[0]
            # اختار الأعلى فوليوم
            if best is None or top['volume'] > best[0]['volume']:
                best = (top, exp_str, dte)

        return best
    except Exception as e:
        return None

if st.button(f"🚀 افحص {len(UNIVERSE)} سهم + عقد متوافق"):
    all_res=[]
    prog=st.progress(0)
    cnt=0
    total=len(UNIVERSE)*len(selected_codes)
    for sym in UNIVERSE:
        tk=yf.Ticker(sym)
        try: spot=tk.fast_info['last_price']
        except:
            try: spot=tk.history(period="1d", interval="1m")['Close'].iloc[-1]
            except: continue

        for (code,period),name in zip(selected_codes,selected_tfs):
            cnt+=1; prog.progress(cnt/total)
            try:
                df=tk.history(period=period, interval=code)
                pat=check_final(df)
                if pat:
                    opt=get_compatible_option(tk, spot, pat['dir'])
                    if opt:
                        top, exp, dte = opt
                        all_res.append({
                            "سهم":sym, "فريم":name, "اتجاه":pat['type'],
                            "ذيل":f"{pat['ratio']:.1f}x", "جسم":f"{pat['det']['body_pct']:.0f}%",
                            "فوليوم سهم":f"{pat['det']['vol_ratio']:.1f}x",
                            "سعر السهم":f"${spot:.2f}",
                            "سترايك":top['strike'], "اكسبايري":exp, "DTE":dte,
                            "سعر العقد":f"${top['lastPrice']:.2f}", "Bid/Ask":f"{top['bid']:.2f}/{top['ask']:.2f}",
                            "Vol OI":f"{int(top['volume'])}/{int(top['openInterest'])}",
                            "OTM":f"{top['otm_pct']:.1f}%",
                            "وقت التأكيد":str(pat['next'].name)[5:16],
                            "_top":top, "_exp":exp, "_dir":pat['dir'], "_spot":spot
                        })
            except: continue
    prog.empty()
    st.session_state.results=all_res

if st.session_state.results:
    df_show = pd.DataFrame(st.session_state.results)[["سهم","فريم","اتجاه","ذيل","سعر السهم","سترايك","اكسبايري","DTE","سعر العقد","Vol OI","OTM","وقت التأكيد"]]
    st.success(f"✅ {len(st.session_state.results)} إشارة صارمة + عقد متوافق - بعد إغلاق شمعة التأكيد مباشرة")
    st.dataframe(df_show, use_container_width=True)
    for r in st.session_state.results:
        msg = f"{'🟢' if r['_dir']=='CALL' else '🔴'} <b>{r['سهم']} {r['اتجاه']} {r['فريم']}</b>\nسهم {r['سعر السهم']} ذيل {r['ذيل']} فوليوم {r['فوليوم سهم']}\n💰 {r['سترايك']} {r['_dir']} Exp {r['اكسبايري']} ({r['DTE']}d)\nعقد {r['سعر العقد']} {r['Bid/Ask']} Vol/OI {r['Vol OI']} OTM {r['OTM']}\nوقت {r['وقت التأكيد']}"
        send_telegram(msg)
else:
    if len(st.session_state.results)==0 and "results" in st.session_state:
        st.warning("ما فيه مطرقة صارمة + عقد متوافق الآن - جرب تخفف الشروط فوق")
        st.info("AMD اللي رسلتها: ذيلها 0.2x فقط (مطلوب 2.0x) وفوليومها نازل - عشان كذا ما راح تطلع الآن وهذا الصح")

# فحص سهم واحد تفصيلي
st.divider()
sym_test = st.text_input("فحص تفصيلي لسهم (مثال AMD)", "AMD")
code_test = st.selectbox("فريم تفصيلي", ["5m","15m","30m","1h","1d"], index=2)
if st.button(f"ليش {sym_test} ما طلعت؟"):
    df=yf.Ticker(sym_test).history(period="10d", interval=code_test)
    c_prev, c_ham, c_next = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    ok_call, ratio, det = is_hammer(c_ham, c_prev, "CALL")
    ok_put, ratio2, det2 = is_hammer(c_ham, c_prev, "PUT")
    st.write(f"CALL: ذيل {det['tail_ratio']:.1f}x مطلوب {tail_mult} - {'✅' if det['tail_ratio']>=tail_mult else '❌'}")
    st.write(f"جسم {det['body_pct']:.1f}% مطلوب <= {body_pct}% - {'✅' if det['body_pct']<=body_pct else '❌'}")
    st.write(f"فوليوم {det['vol_ratio']:.1f}x مطلوب >= {vol_mult} - {'✅' if det['vol_ratio']>=vol_mult else '❌'}")
    st.write(f"ذيل من الشمعة {det['tail_pct']:.1f}% مطلوب >= {tail_total_pct}% - {'✅' if det['tail_pct']>=tail_total_pct else '❌'}")
