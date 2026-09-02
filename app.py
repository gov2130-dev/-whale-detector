high=round(float(hist['High'].iloc[-1]),2)
            low=round(float(hist['Low'].iloc[-1]),2)
            direction=get_strong_direction(t)
            if not direction:
                continue
            exp=tk.options[0] if tk.options else None
            if not exp:
                continue
            dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if dte<0 and len(tk.options)>1:
                exp=tk.options[1]
                dte=(datetime.strptime(exp, "%Y-%m-%d").date() - date.today()).days
            if not (0 <= dte <= 7):
                continue
            chain=tk.option_chain(exp)
            opts=chain.calls if direction=="CALL" else chain.puts
            row=opts.iloc[(opts['strike']-curr).abs().argsort()[:1]].iloc[0]
            bid=float(row['bid'] or 0)
            ask=float(row['ask'] or 0)
            entry=round((bid+ask)/2,2) if bid>0 and ask>0 else round(float(row.get('lastPrice',0) or 0),2)
            if entry < 0.20 or entry > 4.00:
                continue
            if bid>0 and ask>0 and (ask-bid)/entry > 0.40:
                continue
            strike=float(row['strike'])
            strike_s=int(strike) if strike==int(strike) else strike
            ft1,ft2,ft3=get_fibo(high, low, direction)
            now_p=get_now_fast(t, exp, strike, direction) or entry
            pnl=(now_p-entry)/entry*100 if entry else 0
            emoji="🟢" if direction=="CALL" else "🔴"
            txt=f"{emoji} {t} {strike_s} {direction} 🐳\nExp: {exp} ({dte}d) Stock: ${curr:.2f}\nEntry: ${entry:.2f} Bid: ${bid:.2f}\nStop: ${entry*0.5:.2f}\nTarget: ${entry*1.5:.2f} (+50%) | ${entry*2.3:.2f} (+130%) | ${entry*3.2:.2f} (+220%)\nTarget Stock: {ft1} > {ft2} > {ft3} (Fibo)\nNow: ${now_p:.2f} | {pnl:+.1f}% شغال\n{datetime.now().strftime('%H:%M:%S')}"
            st.markdown(f'<div class="box">{txt}</div>', unsafe_allow_html=True)
            fpath=os.path.join(BASE, f"{date.today()}.json")
            data=json.load(open(fpath, encoding='utf-8')) if os.path.exists(fpath) else []
            key=f"{t}_{strike}_{direction}_{exp}"
            if not any(d.get('key')==key for d in data):
                data.append({"key":key,"ticker":t,"strike":strike,"dir":direction,"exp":exp,"entry":entry,"high":high,"low":low,"text":txt})
                json.dump(data, open(fpath,"w",encoding='utf-8'), ensure_ascii=False, indent=2)
            if send(txt):
                sent+=1
            time.sleep(1)
        except:
            continue
    st.success(f"تم ارسال {sent} عقد")
