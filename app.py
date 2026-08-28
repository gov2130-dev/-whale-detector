sent=load()
if st.button(f"🔍 افحص 54 - عقود مرتبة من الأقوى", type="primary"):
    prog=st.progress(0)
    candidates=[]
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, chg, reason = is_strong_both(t)
        if ok: candidates.append((abs(chg), chg, t, direction, reason))
        prog.progress((i+1)/len(WATCHLIST_54)*0.4)

    # رتب من الأقوى للأضعف
    candidates.sort(key=lambda x: x[0], reverse=True)

    call_c=put_c=0
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c=get_contract_dir(t, direction)
        if not c: continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent: continue

        msg=build_msg(c, reason)
        # هذا هو ستايل العقود نفسه - كلهم بنفس الستايل مرتبين
        st.code(msg)

        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
            st.success(f"✅ #{idx+1} الأقوى: {t} {direction} {chg:+.1f}%")
        prog.progress(0.4 + (idx+1)/len(candidates)*0.6)
        time.sleep(0.2)

    st.balloons()
    st.info(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c} | مرتبة من الأقوى #{len(candidates)}")
