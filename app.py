import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="V83 مطرقة حقيقية", layout="wide")
st.title("🔨 V83 - مطرقة حقيقية بدون ذيل عكسي + عقد متوافق")

BOT_TOKEN = st.secrets["BOT_TOKEN"]
CHAT_ID = st.secrets["CHAT_ID"]

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try: requests.post(url, data=data, timeout=10)
    except: pass

if "results" not in st.session_state:
    st.session_state.results = []

# ========= الشروط الثابتة - مطرقة حقيقية =========
# شروط المطرقة الصاعدة CALL
TAIL_MULT = 2.0 # الذيل الطويل >= 2x الجسم
BODY_PCT = 40 # الجسم <= 40% من الشمعة
TAIL_TOTAL_PCT = 50 # الذيل الطويل >= 50% من الشمعة كاملة
VOL_MULT = 1.1 # الفوليوم > السابق * 1.1
NO_WICK_PCT = 15 # الذيل العكسي <= 15% من الشمعة (مافي ذيل علوي)
NO_WICK_MULT = 0.3 # الذيل العكسي <= 0.3x الجسم

# شروط الأوبشن
MIN_OPT_VOL = 300
MIN_OI = 1000
MIN_BID = 0.15
MAX_SPREAD_PCT = 20
DTE_MIN = 1
DTE_MAX = 5
OTM_MIN = -4
OTM_MAX = 3
MAX_CONTRACT_PRICE = 4.00
CONFIRM_ABOVE_HIGH = True
# ==============================================

TIMEFRAMES = [("5m","5 دقايق","5d"),("15m","15 دقيقة","10d"),("30m","30 دقيقة","10d"),("1h","ساعة","20d"),("1d","يومي","60d")]
UNIVERSE = ["NVDA","TSLA","AMD","PLTR","COIN","MSTR","META","AAPL","MSFT","AMZN","NFLX","AVGO","ARM","MU","MARA","RIOT","SOFI","NIO","UPST","AI","HOOD","DKNG","RBLX","ORCL","CRWD","PANW","GOOGL"]

selected_tfs = st.multiselect("الفريمات", [t[1] for t in TIMEFRAMES], default=["15 دقيقة","30 دقيقة","ساعة","يومي"])
tf_map = {name:(code,period) for code,name,period in TIMEFRAMES}
selected_codes = [tf_map[name] for name in selected_tfs]

st.caption(f"مطرقة حقيقية: ذيل {TAIL_MULT}x + بدون ذيل عكسي ≤{NO_WICK_PCT}% | DTE {DTE_MIN}-{DTE_MAX} | OTM {OTM_MIN}%→{OTM_MAX}%")

def is_real_hammer(c_ham, c_prev, direction):
    body = abs(c_ham['Close']-c_ham['Open'])
    if body==0: return False, 0
    upper = c_ham['High'] - max(c_ham['Close'],c_ham['Open'])
    lower = min(c_ham['Close'],c_ham['Open']) - c_ham['Low']
    total = c_ham['High']-c_ham['Low']
    if total==0: return False, 0

    if direction=="CALL":
        # ذيل سفلي طويل + بدون ذيل علوي
        cond_long = (lower >= body*TAIL_MULT) and (lower/total*100 >= TAIL_TOTAL_PCT)
        cond_body = (body/total*100 <= BODY_PCT)
        cond_vol = (c_ham['Volume'] >= c_prev['Volume']*VOL_MULT)
        cond_no_upper = (upper/total*100 <= NO_WICK_PCT) and (upper <= body*NO_WICK_MULT)
        ok = cond_long and cond_body and cond_vol and cond_no_upper
        return ok, lower/body

    else: # PUT - ذيل علوي طويل + بدون ذيل سفلي
        cond_long = (upper >= body*TAIL_MULT) and (upper/total*100 >= TAIL_TOTAL_PCT)
        cond_body = (body/total*100 <= BODY_PCT)
        cond_vol = (c_ham['Volume'] >= c_prev['Volume']*VOL_MULT)
        cond_no_lower = (lower/total*100 <= NO_WICK_PCT) and (lower <= body*NO_WICK_MULT)
        ok = cond_long and cond_body and cond_vol and cond_no_lower
        return ok, upper/body

def check_final(df):
    if len(df) < 4: return None
    c_prev, c_ham, c_next = df.iloc[-3], df.iloc[-2], df.iloc[-1]
    for direction in ["CALL","PUT"]:
        ok, ratio = is_real_hammer(c_ham, c_prev, direction)
        if not ok: continue
        if direction=="CALL":
            confirmed = c_next['Close'] > c_ham['High'] if CONFIRM_ABOVE_HIGH else c_next['Close'] > c_ham['Close']
        else:
            confirmed = c_next['Close'] < c_ham['Low'] if CONFIRM_ABOVE_HIGH else c_next['Close'] < c_ham['Close']
        if confirmed:
            return {"dir":direction, "type":f"{direction} {'🟢' if direction=='CALL' else '🔴'} {ratio:.1f}x بدون ذيل عكسي", "ham":c_ham, "prev":c_prev, "next":c_next, "ratio":ratio}
    return None

def get_compatible_option(tk, spot, direction):
    try:
        today = datetime.now().date()
        best=None
        for exp_str in tk.options[:5]:
            dte = (datetime.strptime(exp_str, "%Y-%m-%d").date() - today).days
            if not (DTE_MIN <= dte <= DTE_MAX): continue
            chain = tk.option_chain(exp_str)
            df_opt = chain.calls if direction=="CALL" else chain.puts
            if df_opt.empty: continue
            df_opt=df_opt.copy()
            df_opt['bid']=df_opt['bid'].fillna(0)
            df_opt['ask']=df_opt['ask'].fillna(0)
            df_opt['volume']=df_opt['volume'].fillna(0)
            df_opt['openInterest']=df_opt['openInterest'].fillna(0)
            df_opt['spread_pct']=((df_opt['ask']-df_opt['bid'])/df_opt['ask']*100).fillna(100)
            df_opt['otm_pct']=(df_opt['strike']-spot)/spot*100 if direction=="CALL" else (spot-df_opt['strike'])/spot*100

            filt=df_opt[(df_opt['volume']>=MIN_OPT_VOL)&(df_opt['openInterest']>=MIN_OI)&(df_opt['bid']>=MIN_BID)&(df_opt['lastPrice']<=MAX_CONTRACT_PRICE)&(df_opt['spread_pct']<=MAX_SPREAD_PCT)&(df_opt['otm_pct']>=OTM_MIN)&(df_opt['otm_pct']<=OTM_MAX)]
            if filt.empty: continue
            filt=filt.sort_values(['volume','openInterest'], ascending=False)
            top=filt.iloc[0]
            if best is None or top['volume']>best[0]['volume']:
                best=(top,exp_str,dte)
        return best
    except: return None

if st.button(f"🚀 افحص {len(UNIVERSE)} سهم - مطرقة حقيقية + عقد"):
    all_res=[]; prog=st.progress(0); cnt=0; total=len(UNIVERSE)*len(selected_codes)
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
                        top,exp,dte=opt
                        all_res.append({
                            "سهم":sym,"فريم":name,"اتجاه":pat['type'],"ذيل":f"{pat['ratio']:.1f}x",
                            "سعر السهم":f"${spot:.2f}","سترايك":top['strike'],"اكسبايري":exp,"DTE":dte,
                            "سعر العقد":f"${top['lastPrice']:.2f}","Vol/OI":f"{int(top['volume'])}/{int(top['openInterest'])}",
                            "OTM":f"{top['otm_pct']:.1f}%","وقت التأكيد":str(pat['next'].name)[5:16]
                        })
            except: continue
    prog.empty()
    st.session_state.results=all_res

if st.session_state.results:
    st.success(f"✅ {len(st.session_state.results)} مطرقة حقيقية (بدون ذيل عكسي) + عقد متوافق بعد إغلاق التأكيد")
    st.dataframe(pd.DataFrame(st.session_state.results), use_container_width=True)
    for r in st.session_state.results:
        send_telegram(f"🔨 {r['سهم']} {r['اتجاه']} {r['فريم']} | {r['سعر السهم']} | {r['سترايك']} Exp {r['اكسبايري']} {r['سعر العقد']} {r['OTM']}")
    st.balloons()
else:
    st.warning("ما فيه مطرقة حقيقية الآن (ذيل طويل + بدون ذيل عكسي) - AMD اللي رسلتها فيها ذيلين عشان كذا ما طلعت وهذا الصح")
