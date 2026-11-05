import urllib.parse

# --- بعد ما تطلع النتائج ---
if len(results) == 0:
    st.warning("مافيه سهم من المفضلة انطبقت عليه الشروط الحين - لا تدخل شي")
else:
    st.success(f"طلع لك {len(results)} سهم من المفضلة انطبقت عليه الشروط")

    # 1. جهز رسالة الواتساب كاملة
    msg_lines = ["🐋 حيتان صانع السوق - V12.4", ""]
    for m in results:
        msg_lines.append(f"{m['ticker']} | {m['signal']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']}")
    msg_text = "\n".join(msg_lines)
    encoded = urllib.parse.quote(msg_text)

    # 2. صندوق رقم الواتساب - اختياري
    st.divider()
    st.subheader("📲 ارسال للواتساب")
    st.caption("إذا تبي ترسل لنفسك أو لشخص معين، حط رقمه هنا بدون + وبدون صفر في البداية. مثال: 9665XXXXXXXX")
    phone = st.text_input("رقم الواتساب (اختياري)", placeholder="9665XXXXXXXX")

    if phone.strip() != "":
        # يرسل لرقم معين
        wa_link = f"https://wa.me/{phone.strip()}?text={encoded}"
        st.link_button("📲 ارسل كل النتائج لهذا الرقم واتساب", wa_link, use_container_width=True)
    else:
        # يفتح واتساب وتختار انت من ترسل له
        wa_link_all = f"https://wa.me/?text={encoded}"
        st.link_button("📲 ارسل كل النتائج واتساب - اختر من ترسل له", wa_link_all, use_container_width=True)

    # 3. زر نسخ الرسالة - إذا تبي تلصقها في أي مكان
    st.code(msg_text, language="text")

    st.divider()
    # 4. عرض النتائج + زر واتساب لكل سهم لوحده
    for m in results:
        single = f"🐋 {m['ticker']} | {m['signal']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}"
        single_enc = urllib.parse.quote(single)
        col1, col2 = st.columns([4, 1])
        with col1:
            st.info(f"{m['ticker']} | {m['signal']} | {m['kind']} | السعر: {m['price']} | الدخول: {m['entry']} | الوقف: {m['stop']} | {m['condition']}")
        with col2:
            if phone.strip() != "":
                st.link_button("واتساب", f"https://wa.me/{phone.strip()}?text={single_enc}")
            else:
                st.link_button("واتساب", f"https://wa.me/?text={single_enc}")
