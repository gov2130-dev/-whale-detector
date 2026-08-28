sent=load()
if st.button(f"🔍 افحص 54 الآن - مرتب من الأقوى", type="primary"):
    call_c=put_c=0
    prog=st.progress(0)

    # 1- اجمع كل الأسهم القوية أول
    candidates=[]
    for i,t in enumerate(WATCHLIST_54):
        ok, direction, reason = is_strong_both(t)
        if ok:
            try:
                curr,_,_=get_data(t)
                daily=yf.Ticker(TICKER_MAP.get(t,t)).history(period="2d")
                chg = (curr/float(daily['Open'].iloc[-1])-1)*100 if not daily.empty else 0
                candidates.append((abs(chg), chg, t, direction, reason))
            except:
                candidates.append((0,0,t,direction,reason))
        prog.progress((i+1)/len(WATCHLIST_54)*0.5)

    # 2- رتب من الأقوى للأضعف
    candidates.sort(key=lambda x: x[0], reverse=True)
    st.write(f"🔥 وجد {len(candidates)} سهم قوي - مرتب من الأقوى:")
    for score, chg, t, direction, reason in candidates:
        st.write(f"{'🟢' if direction=='CALL' else '🔴'} {t} {direction} {chg:+.1f}%")

    # 3- جيب العقود بالترتيب
    prog2=st.progress(0)
    for idx, (score, chg, t, direction, reason) in enumerate(candidates):
        c=get_contract_dir(t, direction)
        if not c:
            st.write(f"❌ {t}: {reason} - ما فيه عقد")
            prog2.progress((idx+1)/len(candidates))
            continue
        key=f"{t}_{c['exp']}_{c['strike']}_{c['type']}_{datetime.now(RIYADH).strftime('%Y-%m-%d')}"
        if key in sent:
            st.write(f"⏭️ {t} مرسل")
            prog2.progress((idx+1)/len(candidates))
            continue
        msg=build_msg_fancy(c, reason)
        st.code(msg)
        if send(msg):
            if c['type']=="CALL": call_c+=1
            else: put_c+=1
            sent.append(key); save(sent)
            st.success(f"✅ {t} {direction} {c['mode']} - قوة {chg:+.1f}%")
        prog2.progress((idx+1)/len(candidates))
        time.sleep(0.2)

    st.balloons()
    st.info(f"تم: 🟢 CALL {call_c} | 🔴 PUT {put_c} | مرتب من الأقوى للأضعف")
