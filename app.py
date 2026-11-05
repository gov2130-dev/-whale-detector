# الحيتان V12 - اكتشاف مرة + متابعة تثبت
# الفكرة: الحوت اذا دخل، يقعد يومين ثلاثة خمسة. ما نطرده اذا سعره تحرك.
# نكتشفه مرة بـ Vol/OI، وبعدين نتابعه بـ OI فقط.

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="توصيات صانع السوق", layout="wide")
st.title("توصيات صانع السوق - V12")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")

# --- شروط الاكتشاف - تستخدم مرة وحدة بس عشان نلقط الحوت اول مرة ---
MIN_ENTRY_DISCOVER = 0.50
MAX_ENTRY_DISCOVER = 3.00
MIN_DAYS = 4
MAX_DAYS = 21
MIN_VOL_OI_DISCOVER = 1.00
MIN_FLOW_PREMIUM = 100000
MIN_VOL = 300
MIN_OI_DISCOVER = 300
MAX_PER_TICKER = 4
MAX_STRIKE_PCT = 0.03
MAX_STRIKE_DOLLARS = 3.00
MAX_SPREAD_PCT = 0.30

# --- ذاكرة الحيتان ---
# هنا نخزن الحيتان اللي اكتشفناها. ما تنحذف الا اذا الحوت باع.
if "whales" not in st.session_state:
    st.session_state.whales = {}  # key = TICKER_STRIKE_TYPE_EXP -> dict
if "last_scan" not in st.session_state:
    st.session_state.last_scan = ""
if "last_discover" not in st.session_state:
    st.session_state.last_discover = ""

def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        return False
    try:
        url = "https://api.telegram.org/bot" + BOT_TOKEN + "/sendMessage"
        requests.post(url, json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return True
    except:
        return False

def build_msg(whales_list):
    msg = "توصيات صانع السوق - " + str(datetime.date.today()) + "\n\n"
    # نجمع حسب السهم
    by_ticker = {}
    for w in whales_list:
        if w["ticker"] not in by_ticker:
            by_ticker[w["ticker"]] = []
        by_ticker[w["ticker"]].append(w)
    for ticker, lst in by_ticker.items():
        price = lst[0]["price"]
        msg = msg + "=== " + ticker + " $" + str(price) + " ===\n"
        for r in lst:
            if r["type"] == "CALL":
                e2 = "🟢"
            else:
                e2 = "🔴"
            strike2 = int(r["strike"])
            msg = msg + e2 + " " + ticker + " " + str(strike2) + " " + r["type"] + "\n"
            msg = msg + "Exp: " + r["exp"] + " (" + str(r["days"]) + "d) Entry: $" + str(r["entry"]) + " Bid: $" + str(r["bid"]) + "\n"
            msg = msg + "مركز الحوت: $" + str(r["position_premium"]) + " | OI: " + str(r["oi"]) + " (" + r["oi_change_txt"] + ")\n"
            msg = msg + "Stop: $" + str(r["stop"]) + " Target: $" + str(r["t1"]) + " | $" + str(r["t2"]) + " | $" + str(r["t3"]) + "\n\n"
    return msg

def show_send_buttons(whales_list, suffix):
    msg = build_msg(whales_list)
    encoded = urllib.parse.quote(msg)
    wa_link = "https://wa.me/?text=" + encoded
    c1, c2 = st.columns(2)
    with c1:
        st.link_button("ارسل واتساب", wa_link, use_container_width=True, key="wa_" + suffix)
    with c2:
        if st.button("ارسل تلجرام", use_container_width=True, key="tg_" + suffix):
            if send_telegram(msg):
                st.success("انرسل لتلجرام")
            else:
                st.error("ما انرسل")

def show_whales(whales_list):
    # نجمع حسب السهم
    by_ticker = {}
    for w in whales_list:
        if w["ticker"] not in by_ticker:
            by_ticker[w["ticker"]] = []
        by_ticker[w["ticker"]].append(w)
    for ticker, lst in by_ticker.items():
        price = lst[0]["price"]
        change = lst[0]["change"]
        st.markdown(
            "<div style='background:#1e293b; border-radius:16px; padding:14px; margin-top:18px; margin-bottom:6px;'>"
            + "<div style='font-size:24px; font-weight:800; color:white;'>🐋 " + ticker + " - $" + str(price) + " (" + str(change) + "%)</div>"
            + "<div style='color:#86efac; margin-top:4px; font-size:15px;'>صانع السوق داخل في هالسهم - " + str(len(lst)) + " عقود - اختر حسب سيولتك</div>"
            + "</div>",
            unsafe_allow_html=True
        )
        for r in lst:
            if r["type"] == "CALL":
                emoji_txt = "🟢"
                border = "#22c55e"
            else:
                emoji_txt = "🔴"
                border = "#ef4444"
            strike_int = int(r["strike"])
            # حالة الحوت
            if r["status"] == "EXITING":
                status_html = "<div style='background:#7f1d1d; color:white; padding:8px; border-radius:8px; margin-top:10px; font-size:14px; font-weight:700;'>⚠️ الحوت بدأ يطلع - OI نزل " + str(r["oi_change_pct"]) + "% - لا تدخل جديد</div>"
            elif r["status"] == "NEW":
                status_html = "<div style='background:#14532d; color:white; padding:8px; border-radius:8px; margin-top:10px; font-size:14px; font-weight:700;'>🆕 حوت جديد دخل اليوم - " + r["first_seen"] + "</div>"
            else:
                status_html = "<div style='background:#1e3a8a; color:white; padding:8px; border-radius:8px; margin-top:10px; font-size:14px; font-weight:700;'>✅ الحوت لسه داخل من " + r["first_seen"] + " - مركزه: $" + str(r["position_premium"]) + "</div>"
            if r["bid"] == 0:
                bid_text = "<div style='color:#facc15; margin-top:10px; font-size:14px;'>⚠️ السوق مغلق - Entry هذا سعر اغلاق امس، تأكد من Bid الحي الساعة 5:30</div><div style='color:white; margin-top:4px; font-size:16px;'>Entry (اغلاق امس): <b>$" + str(r["entry"]) + "</b></div>"
            else:
                bid_text = "<div style='color:white; margin-top:10px; font-size:16px;'>Entry: <b>$" + str(r["entry"]) + "</b> Bid: $" + str(r["bid"]) + " Ask: $" + str(r["ask"]) + "</div>"
            st.markdown(
                "<div style='border:2px solid " + border + "; border-radius:16px; padding:16px; margin-bottom:12px; margin-left:16px; background:#0f172a;'>"
                + "<div style='font-size:20px; font-weight:800; color:white;'>" + emoji_txt + " " + ticker + " " + str(strike_int) + " " + r["type"] + "</div>"
                + "<div style='color:#cbd5e1; margin-top:6px; font-size:14px;'>Exp: " + r["exp"] + " (" + str(r["days"]) + "d) | OI: <b>" + str(r["oi"]) + "</b> (" + r["oi_change_txt"] + ") | Vol اليوم: " + str(r["vol"]) + "</div>"
                + "<div style='color:#86efac; margin-top:4px; font-size:15px; font-weight:700;'>مركز الحوت: <b>$" + str(r["position_premium"]) + "</b> | اول دخول: " + r["first_seen"] + "</div>"
                + bid_text
                + "<div style='color:#fca5a5; margin-top:4px; font-size:15px;'>Stop: <b>$" + str(r["stop"]) + "</b></div>"
                + "<div style='color:#86efac; margin-top:8px; font-size:16px; font-weight:700;'>Target: $" + str(r["t1"]) + " (+50%) | $" + str(r["t2"]) + " (+130%) | $" + str(r["t3"]) + " (+220%)</div>"
                + status_html
                + "</div>",
                unsafe_allow_html=True
            )

@st.cache_data(ttl=3600)
def get_universe():
    universe = []
    try:
        sp = pd.read_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies")[0]['Symbol'].tolist()
        for s in sp:
            universe.append(s.replace('.', '-'))
    except:
        pass
    try:
        nd = pd.read_html("https://en.wikipedia.org/wiki/NASDAQ-100")[0]['Ticker'].tolist()
        for s in nd:
            universe.append(s)
    except:
        pass
    hot = ["AAPL","MSFT","NVDA","AMZN","GOOGL","GOOG","META","TSLA","AVGO","NFLX","AMD","SMCI","ARM","APP","PLTR","HOOD","COIN","MSTR","MARA","RIOT","CLSK","GME","AMC","OPEN","CVNA","SOFI","BABA","PDD","JD","MRNA","RIVN","LCID","NIO","DKNG","RBLX","U","AI","SOUN","UPST","AFRM","CHWY","BYND","SPCE","INTC","MU","QCOM","TXN","ADI","MCHP","ON","SHOP","SQ","PYPL","ABNB","UBER","DASH","ROKU","ZM","DOCU","PTON","TLRY","CGC","NOK","PLUG","FCEL","QS","GPRO","TSM","ASML","CRM","ORCL","BAC","JPM","XOM","CVX","WMT","COST","PEP","KO","PFE","BIIB","NUE","FCX","OXY","USO","GLD","SLV","CLF","X","LLY","V","MA","HD","JNJ","UNH","WFC","CSCO","ACN","MCD","ABT","DHR","GE","CAT","LOW","INTU","DE","AMAT","BKNG","LRCX","KLAC","SNPS","CDNS","MRVL","PANW","CRWD","NET","DDOG","ZS","MDB","SNOW","TEAM","WDAY","EA","AAL","UAL","DAL","CCL","NCLH","RCL","HIMS","GRAB","SE","MELI","NU","BILI","XPEV","LI","BIDU","IQ","TME","VIPS","DIDI","OKTA","TWLO","FSLY","ESTC","GTLB","CFLT","PATH","LMND","OPEN","VRM","KMX","AN","PAG","LAD","ABG","SAH","GPI","CARG","CARS","TRUE","ACVA","RUSH","ARCB","ODFL","SAIA","XPO","CHRW","EXPD","JBHT","KNX","WERN","MRTN","SNDR","LSTR","HUBG","GXO","FDX","UPS","SBUX","YUM","DPZ","CMG","SHAK","WING","LUV","JBLU","SAVE","HA","ALK","EXPE","MAR","HLT","H","WYNN","LVS","MGM","CZR","PENN","SEAS","FUN","SIX","PLNT","YETI","CROX","SKX","DECK","UAA","NKE","LULU","GPS","ANF","AEO","URBN","BBY","TGT","BJ","DG","DLTR","FIVE","BURL","ROST","TJX","KSS","JWN","M","DDS","SHW","SWK","MAS","WHR","LEG","TPX","SNBR","RH","WSM","ETSY","EBAY","W","CHWY","PETS","WOOF","FRPT","BARK","CPNG","MELI","SE","OSCR","CLOV","SDC","ROOT","MTTR","CVNA","PINS","SNAP","SPOT","DIS","WBD","PARA","CMCSA","T","VZ","TMUS"]
    for s in hot:
        if s not in universe:
            universe.append(s)
    universe = sorted(list(set(universe)))
    return universe

def is_market_open_now():
    now = datetime.datetime.now(RIYADH)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    open_min = 17 * 60 + 30
    if minutes >= open_min or minutes < 60:
        return True
    return False

def check_discover(row, price):
    # هذا يستخدم مرة وحدة بس عشان نلقط الحوت الجديد
    vol = int(row['volume'])
    oi = int(row['openInterest'])
    if vol < MIN_VOL:
        return None
    if oi < MIN_OI_DISCOVER:
        return None
    bid = 0
    ask = 0
    last = 0
    try:
        bid = float(row['bid'])
    except:
        bid = 0
    try:
        ask = float(row['ask'])
    except:
        ask = 0
    try:
        last = float(row['lastPrice'])
    except:
        last = 0
    entry = 0
    if bid > 0 and ask > 0 and bid <= ask:
        spread = (ask - bid) / bid
        if spread > MAX_SPREAD_PCT:
            return None
        entry = (bid + ask) / 2
    else:
        if last <= 0:
            return None
        entry = last
    if entry < MIN_ENTRY_DISCOVER or entry > MAX_ENTRY_DISCOVER:
        return None
    vol_oi = 0
    if oi > 0:
        vol_oi = vol / oi
    if vol_oi < MIN_VOL_OI_DISCOVER:
        return None
    flow_premium = int(vol * entry * 100)
    if flow_premium < MIN_FLOW_PREMIUM:
        return None
    strike = float(row['strike'])
    dollar_diff = abs(strike - price)
    pct_diff = dollar_diff / price
    if pct_diff > MAX_STRIKE_PCT:
        return None
    if dollar_diff > MAX_STRIKE_DOLLARS:
        return None
    out = {"vol": vol, "oi": oi, "bid": round(bid, 2), "ask": round(ask, 2), "entry": round(entry, 2), "vol_oi": round(vol_oi, 2), "flow_premium": flow_premium}
    return out

def get_raw_chain_for_ticker(ticker):
    # ترجع كل العقود الخام بدون فلترة - عشان المتابعة ما تحذف الحوت القديم
    try:
        tk = yf.Ticker(ticker)
        hist = yf.download(ticker, period="5d", interval="1d", progress=False, auto_adjust=False)
        if hist.empty:
            return None, None, None
        if isinstance(hist.columns, pd.MultiIndex):
            hist.columns = hist.columns.get_level_values(0)
        price = float(hist['Close'].iloc[-1])
        prev_close = float(hist['Close'].iloc[-2])
        change = 0
        if prev_close != 0:
            change = (price - prev_close) / prev_close * 100
        if abs(change) > 25:
            return None, None, None
        exps = tk.options
        if not exps:
            return None, None, None
        today = datetime.date.today()
        all_contracts = []
        for exp_str in exps[:6]:
            try:
                exp_date = datetime.datetime.strptime(exp_str, "%Y-%m-%d").date()
                days_left = (exp_date - today).days
                if days_left < MIN_DAYS or days_left > MAX_DAYS:
                    continue
                chain = tk.option_chain(exp_str)
                pairs = [(chain.calls, "CALL"), (chain.puts, "PUT")]
                for df, typ in pairs:
                    if len(df) == 0:
                        continue
                    for idx, row in df.iterrows():
                        try:
                            vol = int(row['volume'])
                            oi = int(row['openInterest'])
                            bid = float(row['bid']) if pd.notna(row['bid']) else 0
                            ask = float(row['ask']) if pd.notna(row['ask']) else 0
                            last = float(row['lastPrice']) if pd.notna(row['lastPrice']) else 0
                        except:
                            continue
                        entry = 0
                        if bid > 0 and ask > 0 and bid <= ask:
                            entry = (bid + ask) / 2
                        else:
                            entry = last
                        if entry <= 0:
                            continue
                        all_contracts.append({"ticker": ticker, "type": typ, "strike": float(row['strike']), "exp": exp_str, "days": days_left, "vol": vol, "oi": oi, "bid": round(bid, 2), "ask": round(ask, 2), "entry": round(entry, 2), "price": round(price, 2), "change": round(change, 2)})
            except:
                continue
        return all_contracts, price, change
    except:
        return None, None, None

universe = get_universe()
st.write("الكون: " + str(len(universe)) + " سهم")
st.write("الحيتان المتابعة الحين: " + str(len(st.session_state.whales)) + " حوت")

# --- الازرار ---
c1, c2, c3 = st.columns(3)
with c1:
    do_discover = st.button("🔍 اكتشف حيتان جديدة", type="primary", use_container_width=True)
with c2:
    do_track = st.button("👀 تابع الحيتان اللي عندي", use_container_width=True)
with c3:
    do_clear = st.button("🗑️ امسح الكل", use_container_width=True)

if do_clear:
    st.session_state.whales = {}
    st.session_state.last_scan = ""
    st.session_state.last_discover = ""
    st.rerun()

# --- 1. الاكتشاف ---
if do_discover:
    if not is_market_open_now():
        st.warning("السوق مغلق الحين - افحص من 5:30 عصر الى 12 ليل بتوقيت الرياض.")
    else:
        progress = st.progress(0)
        status = st.empty()
        new_count = 0
        with ThreadPoolExecutor(max_workers=10) as ex:
            for i, res in enumerate(ex.map(get_raw_chain_for_ticker, universe)):
                if res is not None:
                    all_contracts, price, change = res
                    if all_contracts is not None:
                        for c in all_contracts:
                            # نطبق شروط الاكتشاف على العقود الجديدة بس
                            # نبني row وهمي عشان check_discover
                            fake_row = {"volume": c["vol"], "openInterest": c["oi"], "bid": c["bid"], "ask": c["ask"], "lastPrice": c["entry"], "strike": c["strike"]}
                            info = check_discover(fake_row, price)
                            if info is None:
                                continue
                            key = c["ticker"] + "_" + str(int(c["strike"])) + "_" + c["type"] + "_" + c["exp"]
                            if key in st.session_state.whales:
                                continue
                            # حوت جديد - نسجله
                            position_premium = int(c["oi"] * c["entry"] * 100)
                            whale = {
                                "ticker": c["ticker"], "type": c["type"], "strike": c["strike"], "exp": c["exp"], "days": c["days"],
                                "vol": c["vol"], "oi": c["oi"], "first_oi": c["oi"], "bid": c["bid"], "ask": c["ask"],
                                "entry": c["entry"], "first_entry": c["entry"], "price": round(price, 2), "change": round(change, 2),
                                "vol_oi": info["vol_oi"], "flow_premium": info["flow_premium"],
                                "position_premium": position_premium, "first_seen": datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M'),
                                "status": "NEW", "oi_change_pct": 0, "oi_change_txt": "جديد", "stop": round(c["entry"] * 0.5, 2),
                                "t1": round(c["entry"] * 1.5, 2), "t2": round(c["entry"] * 2.3, 2), "t3": round(c["entry"] * 3.2, 2),
                            }
                            st.session_state.whales[key] = whale
                            new_count += 1
                if i % 30 == 0:
                    progress.progress(min((i+1)/len(universe), 1.0))
                    status.text("فحصت " + str(i+1) + " / " + str(len(universe)))
        progress.progress(1.0)
        st.session_state.last_discover = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
        st.success("اكتشفت " + str(new_count) + " حوت جديد. المجموع الحين: " + str(len(st.session_state.whales)))

# --- 2. المتابعة - هذا هو المهم ---
if do_track:
    if len(st.session_state.whales) == 0:
        st.warning("ما عندك حيتان لسه. اضغط اكتشف حيتان جديدة اول.")
    else:
        # نجيب اسهم الحيتان بس، مو كل الكون - عشان ما نضيع وقت
        tickers_to_track = sorted(list(set([w["ticker"] for w in st.session_state.whales.values()])))
        progress = st.progress(0)
        status = st.empty()
        updated = {}
        removed = []
        with ThreadPoolExecutor(max_workers=10) as ex:
            results_map = {}
            for i, res in enumerate(ex.map(get_raw_chain_for_ticker, tickers_to_track)):
                if res is not None:
                    all_contracts, price, change = res
                    if all_contracts is not None:
                        results_map[tickers_to_track[i]] = (all_contracts, price, change)
                progress.progress(min((i+1)/len(tickers_to_track), 1.0))
                status.text("تابعت " + str(i+1) + " / " + str(len(tickers_to_track)))
        # الحين نحدث كل حوت
        for key, w in st.session_state.whales.items():
            ticker = w["ticker"]
            if ticker not in results_map:
                # Yahoo ما رد - نخليه مثل ما هو، ما نحذفه
                updated[key] = w
                continue
            all_contracts, price, change = results_map[ticker]
            # ندور على نفس العقد بالضبط: نفس السترايك ونفس النوع ونفس التاريخ
            found = None
            for c in all_contracts:
                if c["ticker"] == ticker and c["type"] == w["type"] and int(c["strike"]) == int(w["strike"]) and c["exp"] == w["exp"]:
                    found = c
                    break
            if found is None:
                # العقد اختفى تماما - الحوت طلع
                removed.append(key)
                continue
            # الحوت لسه موجود - نحدث سعره و OI ومركزه، وما نطرده لو سعره طار فوق 3
            new_oi = found["oi"]
            new_entry = found["entry"]
            first_oi = w["first_oi"]
            oi_change_pct = 0
            if first_oi > 0:
                oi_change_pct = round((new_oi - first_oi) / first_oi * 100, 1)
            # بريموم المركز الجديد = OI الجديد × السعر الجديد × 100
            # هذا هو اللي لازم يزيد ما ينقص
            new_position = int(new_oi * new_entry * 100)
            if new_oi < first_oi * 0.5:
                status_txt = "EXITING"
                oi_txt = str(oi_change_pct) + "% - يطلع"
            else:
                if w["status"] == "NEW" and oi_change_pct == 0:
                    status_txt = "NEW"
                else:
                    status_txt = "HOLDING"
                oi_txt = str(oi_change_pct) + "%"
            w2 = w.copy()
            w2["vol"] = found["vol"]
            w2["oi"] = new_oi
            w2["bid"] = found["bid"]
            w2["ask"] = found["ask"]
            w2["entry"] = new_entry
            w2["price"] = round(price, 2)
            w2["change"] = round(change, 2)
            w2["days"] = found["days"]
            w2["position_premium"] = new_position
            w2["oi_change_pct"] = oi_change_pct
            w2["oi_change_txt"] = oi_txt
            w2["status"] = status_txt
            # الوقف والهدف يبقون على سعر الدخول الاول، ما نغيرهم اذا السعر تحرك
            updated[key] = w2
        st.session_state.whales = updated
        st.session_state.last_scan = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
        if len(removed) > 0:
            st.warning("الحيتان هذي طلعت وبعناها من المتابعة: " + ", ".join(removed))
        st.success("تابعت " + str(len(updated)) + " حوت. اخر متابعة: " + st.session_state.last_scan)

# --- العرض ---
if len(st.session_state.whales) > 0:
    whales_list = sorted(list(st.session_state.whales.values()), key=lambda x: (-x["position_premium"], x["ticker"]))
    # نفصل اللي يطلعون عن اللي ماسكين
    holding = [w for w in whales_list if w["status"] != "EXITING"]
    exiting = [w for w in whales_list if w["status"] == "EXITING"]
    st.write("اخر متابعة: " + st.session_state.last_scan + " | اخر اكتشاف: " + st.session_state.last_discover)
    if len(holding) > 0:
        st.markdown("### 🐋 الحيتان اللي لسه داخلين")
        st.markdown("### ارسال التوصيات")
        show_send_buttons(holding, "top")
        show_whales(holding)
        st.markdown("### ارسال مرة ثانية")
        show_send_buttons(holding, "bottom")
    if len(exiting) > 0:
        st.markdown("### ⚠️ الحيتان اللي بدأت تطلع - لا تدخل جديد")
        show_whales(exiting)
else:
    st.info("اضغط اكتشف حيتان جديدة - مرة وحدة في اليوم، الساعة 6:30 عصر بتوقيت الرياض. بعد كذا اضغط تابع الحيتان اللي عندي كل شوي، ولا تكتشف من جديد.")
