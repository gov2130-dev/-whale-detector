# الحيتان V12.1 - سهم واحد = اتجاه واحد بس
# صانع السوق يدخل صعود او يخرج نزول. ما يشتري الاثنين مع بعض.

import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import datetime
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
import pytz

st.set_page_config(page_title="توصيات صانع السوق", layout="wide")
st.title("توصيات صانع السوق - V12.1")

try:
    BOT_TOKEN = st.secrets["BOT_TOKEN"]
    CHAT_ID = st.secrets["CHAT_ID"]
except:
    BOT_TOKEN = ""
    CHAT_ID = ""

RIYADH = pytz.timezone("Asia/Riyadh")

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

if "whales" not in st.session_state:
    st.session_state.whales = {}
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
    by_ticker = {}
    for w in whales_list:
        if w["ticker"] not in by_ticker:
            by_ticker[w["ticker"]] = []
        by_ticker[w["ticker"]].append(w)
    for ticker, lst in by_ticker.items():
        price = lst[0]["price"]
        # الاتجاه - كلهم نفس الاتجاه الحين
        direction = lst[0]["type"]
        if direction == "CALL":
            dir_txt = "صعود"
        else:
            dir_txt = "نزول"
        msg = msg + "=== " + ticker + " $" + str(price) + " - " + dir_txt + " ===\n"
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
    by_ticker = {}
    for w in whales_list:
        if w["ticker"] not in by_ticker:
            by_ticker[w["ticker"]] = []
        by_ticker[w["ticker"]].append(w)
    for ticker, lst in by_ticker.items():
        price = lst[0]["price"]
        change = lst[0]["change"]
        direction = lst[0]["type"]
        if direction == "CALL":
            dir_txt = "صعود 🟢 - صانع السوق داخل"
            dir_color = "#86efac"
        else:
            dir_txt = "نزول 🔴 - صانع السوق خارج"
            dir_color = "#fca5a5"
        st.markdown(
            "<div style='background:#1e293b; border-radius:16px; padding:14px; margin-top:18px; margin-bottom:6px;'>"
            + "<div style='font-size:24px; font-weight:800; color:white;'>🐋 " + ticker + " - $" + str(price) + " (" + str(change) + "%)</div>"
            + "<div style='color:" + dir_color + "; margin-top:4px; font-size:16px; font-weight:700;'>" + dir_txt + " - " + str(len(lst)) + " عقود بنفس الاتجاه</div>"
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

# --- 1. الاكتشاف - مع اصلاح الاتجاه الواحد ---
if do_discover:
    if not is_market_open_now():
        st.warning("السوق مغلق الحين - افحص من 5:30 عصر الى 12 ليل بتوقيت الرياض.")
    else:
        progress = st.progress(0)
        status = st.empty()
        # نجمع كل المرشحين اول، ما نضيفهم على طول
        # عشان نقدر نقارن CALL ضد PUT على نفس السهم
        candidates_by_ticker = {}
        with ThreadPoolExecutor(max_workers=10) as ex:
            for i, res in enumerate(ex.map(get_raw_chain_for_ticker, universe)):
                if res is not None:
                    all_contracts, price, change = res
                    if all_contracts is not None:
                        for c in all_contracts:
                            fake_row = {"volume": c["vol"], "openInterest": c["oi"], "bid": c["bid"], "ask": c["ask"], "lastPrice": c["entry"], "strike": c["strike"]}
                            info = check_discover(fake_row, price)
                            if info is None:
                                continue
                            key = c["ticker"] + "_" + str(int(c["strike"])) + "_" + c["type"] + "_" + c["exp"]
                            if key in st.session_state.whales:
                                continue
                            # نحسب مركز الحوت لهالعقد
                            position_premium = int(c["oi"] * c["entry"] * 100)
                            cand = {
                                "ticker": c["ticker"], "type": c["type"], "strike": c["strike"], "exp": c["exp"], "days": c["days"],
                                "vol": c["vol"], "oi": c["oi"], "first_oi": c["oi"], "bid": c["bid"], "ask": c["ask"],
                                "entry": c["entry"], "first_entry": c["entry"], "price": round(price, 2), "change": round(change, 2),
                                "vol_oi": info["vol_oi"], "flow_premium": info["flow_premium"],
                                "position_premium": position_premium, "first_seen": datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M'),
                                "status": "NEW", "oi_change_pct": 0, "oi_change_txt": "جديد", "stop": round(c["entry"] * 0.5, 2),
                                "t1": round(c["entry"] * 1.5, 2), "t2": round(c["entry"] * 2.3, 2), "t3": round(c["entry"] * 3.2, 2),
                            }
                            if c["ticker"] not in candidates_by_ticker:
                                candidates_by_ticker[c["ticker"]] = []
                            candidates_by_ticker[c["ticker"]].append(cand)
                if i % 30 == 0:
                    progress.progress(min((i+1)/len(universe), 1.0))
                    status.text("فحصت " + str(i+1) + " / " + str(len(universe)))
        progress.progress(1.0)
        # --- هنا الاصلاح: سهم واحد = اتجاه واحد ---
        new_count = 0
        for ticker, cands in candidates_by_ticker.items():
            # اذا السهم عنده حوت قديم، لازم نلتزم باتجاهه، ما نضيف اتجاه عكسه
            old_types = set([w["type"] for w in st.session_state.whales.values() if w["ticker"] == ticker])
            if len(old_types) > 0:
                # السهم عنده اتجاه قديم - نحذف اي مرشح عكس الاتجاه
                old_type = list(old_types)[0]
                cands = [c for c in cands if c["type"] == old_type]
                if len(cands) == 0:
                    continue
            else:
                # سهم جديد - نقارن مجموع CALL ضد مجموع PUT
                call_total = sum([c["position_premium"] for c in cands if c["type"] == "CALL"])
                put_total = sum([c["position_premium"] for c in cands if c["type"] == "PUT"])
                # الاقوى يفوز، والثاني ينحذف كله
                if call_total > 0 and put_total > 0:
                    if call_total >= put_total:
                        # صعود يفوز - نحذف كل PUT
                        cands = [c for c in cands if c["type"] == "CALL"]
                    else:
                        # نزول يفوز - نحذف كل CALL
                        cands = [c for c in cands if c["type"] == "PUT"]
            # نرتب المرشحين وناخذ اقوى 4 بنفس الاتجاه
            cands = sorted(cands, key=lambda x: (-x["position_premium"], x["entry"]))[:MAX_PER_TICKER]
            for cand in cands:
                key = cand["ticker"] + "_" + str(int(cand["strike"])) + "_" + cand["type"] + "_" + cand["exp"]
                st.session_state.whales[key] = cand
                new_count += 1
        st.session_state.last_discover = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
        st.success("اكتشفت " + str(new_count) + " حوت جديد. المجموع الحين: " + str(len(st.session_state.whales)))

# --- 2. المتابعة ---
if do_track:
    if len(st.session_state.whales) == 0:
        st.warning("ما عندك حيتان لسه. اضغط اكتشف حيتان جديدة اول.")
    else:
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
        for key, w in st.session_state.whales.items():
            ticker = w["ticker"]
            if ticker not in results_map:
                updated[key] = w
                continue
            all_contracts, price, change = results_map[ticker]
            found = None
            for c in all_contracts:
                if c["ticker"] == ticker and c["type"] == w["type"] and int(c["strike"]) == int(w["strike"]) and c["exp"] == w["exp"]:
                    found = c
                    break
            if found is None:
                removed.append(key)
                continue
            new_oi = found["oi"]
            new_entry = found["entry"]
            first_oi = w["first_oi"]
            oi_change_pct = 0
            if first_oi > 0:
                oi_change_pct = round((new_oi - first_oi) / first_oi * 100, 1)
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
            updated[key] = w2
        st.session_state.whales = updated
        st.session_state.last_scan = datetime.datetime.now(RIYADH).strftime('%Y-%m-%d %H:%M')
        if len(removed) > 0:
            st.warning("الحيت
