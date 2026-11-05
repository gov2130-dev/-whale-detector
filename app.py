    if len(results) == 0:
        st.warning("مافيه سهم في قاع تماماً أو قمة تماماً الحين - كل الأسهم في النص 20%-80% - لا تدخل شي، هذا هو الصح")
        st.info("CVX اللي كان 67.2% اختفى الحين، لأنه صار في المنطقة المحرمة.")
        # --- قائمة المراقبة: أقرب 5 أسهم للحافة ---
        st.subheader("👀 قائمة المراقبة - لا تدخل الحين، راقب بس")
        st.caption("هذي الأسهم قريبة من القاع أو القمة، باقي لها شوي وتدخل منطقة الحوت. إذا وصلت، بيطلع لك عليها إشارة في البحث الجاي.")
        watch = []
        for t in FAVORITE_OPTIONS:
            try:
                dfw = yf.download(t, period="6mo", interval="1d", progress=False, auto_adjust=False)
                if dfw is None or dfw.empty:
                    continue
                if isinstance(dfw.columns, pd.MultiIndex):
                    dfw.columns = [c[0] if isinstance(c, tuple) else c for c in dfw.columns]
                cw = num(dfw["Close"])
                loww = float(dfw["Low"].tail(90).min())
                highw = float(dfw["High"].tail(90).max())
                if highw == loww:
                    continue
                posw = (cw - loww) / (highw - loww) * 100
                # المسافة للحافة: إذا كان تحت 50%، المسافة للقاع 20%، وإذا فوق 50%، المسافة للقمة 80%
                if posw < 50:
                    dist = posw - 20  # كم باقي له ويوصل القاع
                    zone = "قريب من القاع"
                    target = "CALL"
                else:
                    dist = 80 - posw  # كم باقي له ويوصل القمة
                    zone = "قريب من القمة"
                    target = "PUT"
                watch.append({"ticker": t, "price": round(cw, 2), "pos": round(posw, 1), "dist": round(abs(dist), 1), "zone": zone, "target": target})
            except Exception:
                continue
        watch = sorted(watch, key=lambda x: x["dist"])[:5]
        for w in watch:
            st.warning(f"{w['ticker']} | السعر: {w['price']} | موقع السعر: {w['pos']}% من القاع | {w['zone']} | باقي له {w['dist']}% ويوصل منطقة {w['target']} | 👀 مراقبة فقط، لا تدخل")
