high_r = round(mid,2)
                close_p = round(float(row.get('lastPrice', mid) or mid),2)
                entry = round(mid,2)
                bid_p = round(bid,2)
                bw = round(dist*100,2)
                stop = round(entry*0.5,2)
                if direction=="CALL":
                    t1_s = round(strike + 0.3,2)
                    t2_s = round(strike + 0.6,2)
                    t3_s = round(strike + 1.0,2)
                else:
                    t1_s = round(strike - 0.3,2)
                    t2_s = round(strike - 0.6,2)
                    t3_s = round(strike - 1.0,2)
                t1_c = round(entry*1.5,2)
                t2_c = round(entry*2.3,2)
                t3_c = round(entry*3.2,2)
                return {
                    "ticker":ticker, "dir":direction, "strike":int(strike) if strike==int(strike) else strike,
                    "exp":exp_str, "dte":dte, "curr":round(curr,2), "bw":bw,
                    "range_low":low_r, "range_high":high_r, "close":close_p,
                    "entry":entry, "bid":bid_p, "stop":stop,
                    "t1_s":t1_s, "t2_s":t2_s, "t3_s":t3_s,
                    "t1_c":t1_c, "t2_c":t2_c, "t3_c":t3_c,
                }
        return None
    except: return None

st.title("🐋 V99 - اختبار التيليجرام")

# زر اختبار سريع
if st.button("📨 اختبار التيليجرام فقط"):
    if send("تجربة بوت V99 🐋"):
        st.success("انرسل - شيك التيليجرام")
    else:
        st.error("ما انرسل - شيك الـ CHAT_ID والبوت")

st.divider()

if st.button("🚀 فحص العقود وارسال"):
    sent=load()
    all_contracts=[]
    for t in WATCHLIST:
        direction=get_technical_direction(t)
        if not direction or direction=="NEUTRAL":
            continue
        contract=find_matching_contract(t, direction)
        if contract:
            all_contracts.append(contract)
        time.sleep(0.3)

    if not all_contracts:
        st.info("لا يوجد عقود")
    else:
        for c in all_contracts:
            emoji = "🟢" if c['dir']=="CALL" else "🔴"
            text = (
                f"{emoji} {c['ticker']} {c['strike']} {c['dir']} 🐋\n"
                f"Exp: {c['exp']} ({c['dte']}d) Stock: ${c['curr']} BW {c['bw']}%\n"
                f"Range: ${c['range_low']} - ${c['range_high']} Close: ${c['close']}\n"
                f"Entry: ${c['entry']} Bid: ${c['bid']}\n"
                f"Stop: ${c['stop']}\n"
                f"Target Stock: {c['t1_s']} > {c['t2_s']} > {c['t3_s']}\n"
                f"Target Contract: ${c['t1_c']} (+50%) | ${c['t2_c']} (+130%) | ${c['t3_c']} (+220%)"
            )
            st.code(text)
            # ارسال مباشر بدون شرط التكرار للاختبار
            send(text)
            time.sleep(1)
