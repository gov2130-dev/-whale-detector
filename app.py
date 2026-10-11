import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="V82 ثابت", layout="wide")
st.title("🎯 V82 ثابت - شروط مضبوطة داخل الكود")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

if "results" not in st.session_state:
    st.session_state.results = []

# ========= الشروط الثابتة داخل الكود - لا تظهر كخيارات =========
# شروط المطرقة (السهم)
TAIL_MULT = 2.0 # الذيل >= 2 ضعف الجسم
BODY_PCT = 40 # الجسم <= 40% من طول الشمعة
TAIL_TOTAL_PCT = 50 # الذيل >= 50% من طول الشمعة كاملة
VOL_MULT = 1.1 # الفوليوم > السابق * 1.1

# شروط التأكيد
CONFIRM_ABOVE_HIGH = True # True = فوق قمة المطرقة (صارم) / False = فوق إغلاقها (سريع)

# شروط الأوبشن المتوافق
MIN_OPT_VOL = 300
MIN_OI = 1000
MIN_BID = 0.15
MAX_SPREAD_PCT = 20
DTE_MIN = 1
DTE_MAX = 5
OTM_MIN = -4
OTM_MAX = 3
MAX_CONTRACT_PRICE = 4.00

# =============================================================

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL","MS","TSM"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["15 دقيقة","30 دقيقة","ساعة","يومي"])
tf_map = {name:(code,period) for code,name,period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

st.caption(f"شروط ثابتة: ذيل {TAIL_MULT}x | جسم ≤{BODY_PCT}% | فوليوم {VOL_MULT}x | DTE {DTE_MIN}-{DTE_MAX} | OTM {OTM_MIN}% إلى {OTM_MAX}% | سعر عقد ≤${MAX_CONTRACT_PRICE}")

def is_hammer(c_ham, c_prev, direction):
    body = abs(c_ham['Close']-c_ham['Open'])
    if body==0: return False, 0
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0: return False, 0

    if direction=="CALL":
        ok = (lower >= body*TAIL_MULT) and (body/total*100 <= BODY_PCT) and (lower/total*100 >= TAIL_TOTAL_PCT) and (c_ham['Volume'] >= c_prev['Volume']*VOL_MULT)
        return ok, lower/body
    else:
        ok = (upper >= body*TAIL_MULT) and (body/total*100 <= BODY_PCT) and (upper/total*100 >= TAIL_TOTAL_PCT) and (c_ham['Volume'] >= c_prev['Volume']*VOL_MULT)
        return ok, upper/body

def check_final(df):
    if len(df) < 4: return None
    c_prev, c_ham, c_next = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    for direction in ["CALL","PUT"]:
        ok, ratio = is_hammer(c_ham, c_prev, direction)
        if not ok: continue
        if direction=="CALL":
            confirmed = c_next['Close'] > c_ham['High'] if CONFIRM_ABOVE_HIGH else c_next['Close'] > c_ham['Close']
        else:
            confirmed = c_next['Close'] < c_ham['Low'] if CONFIRM_ABOVE_HIGH else c_next['Close'] < c_ham['Close']
        if confirmed:
            return {"dir":direction, "type":f"{direction} {'🟢' if direction=='CALL' else '🔴'} {ratio:.1f}x", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":ratio}
    return None

def get_compatible_option(tk, spot, direction):
    try:
        today = datetime.now().date()
        best = None
        for exp_str in tk.options[:5]:
            exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
            dte = (exp_date - today).days
            if not (DTE_MIN <= dte <= DTE_MAX): continue
            chain = tk.option_chain(exp_str)
            df_opt = chain.calls if direction=="CALL" else chain.puts
            if df_opt.empty: continue
            df_opt = df_opt.copy()
            df_opt['bid']=df_opt['bid'].fillna(0)
            df_opt['ask']=df_opt['ask'].fillna(0)
            df_opt['volume']=df_opt['volume'].fillna(0)
            df_opt['openInterest']=df_opt['openInterest'].fillna(0)
            df_opt['spread_pct']=((df_opt['ask']-df_opt['bid'])/df_opt['ask']*100).fillna(100)
            if direction=="CALL":
                df_opt['otm_pct']=(df_opt['strike']-spot)/spot*100
            else:
                df_opt['otm_pct']=(spot-df_opt['strike'])/spot*100

            filt = df_opt[
                (df_opt['volume']>=MIN_OPT_VOL) &
                (df_opt['openInterest']>=MIN_OI) &
                (df_opt['bid']>=MIN_BID) &
                (df_opt['lastPrice']<=MAX_CONTRACT_PRICE) &
                (df_opt['lastPrice']>=0.1) &
                (df_opt['spread_pct']<=MAX_SPREAD_PCT) &
                (df_opt['otm_pct']>=OTM_MIN) & (df_opt['otm_pct']<=OTM_MAX)
            ]
            if filt.empty: continue
            filt=filt.sort_values(['volume','openInterest'], ascending=False)
            top=filt.iloc[0]
            if best is None or top['volume']>best[0]['volume']:
                best=(top,exp_str,dte)
        return best
    except:
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
                            "سهم":sym, "فريم":name, "اتجاه":pat['type'], "ذيل":f"{pat['ratio']:.1f}x",
                            "سعر السهم":f"${spot:.2f}", "سترايك":top['strike'], "اكسبايري":exp, "DTE":dte,
                            "سعر العقد":f"${top['lastPrice']:.2f}", "Vol/OI":f"{int(top['volume'])}/{int(top['openInterest'])}",
                            "OTM":f"{top['otm_pct']:.1f}%", "وقت التأكيد":str(pat['next'].name)[5:16]
                        })
            except: continue
    prog.empty()
    st.session_state.results=all_res

if st.session_state.results:
    st.success(f"✅ {len(st.session_state.results)} إشارة بعد إغلاق التأكيد + عقد متوافق")
    st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True)
    for r in st.session_state.results:
        send_telegram(f"🎯 {r['سهم']} {r['اتجاه']} {r['فريم']} | سهم {r['سعر السهم']} | {r['سترايك']} Exp {r['اكسبايري']} ({r['DTE']}d) | عقد {r['سعر العقد']} Vol {r['Vol/OI']} OTM {r['OTM']}")
    st.balloons()
else:
    st.warning("ما فيه إشارة تطابق الشروط الثابتة الآن - AMD اللي في الصورة السابقة ما تطلع لأنها مو مطابقة")
