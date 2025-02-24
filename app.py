import streamlit as st
import pandas as pd
import google.generativeai as genai
import razorpay

# Configure Google Gemini API
genai.configure(api_key="YOUR_GEMINI_API_KEY")

# Razorpay Client Setup
razorpay_client = razorpay.Client(auth=("YOUR_RAZORPAY_KEY", "YOUR_RAZORPAY_SECRET"))

# Expense Data
if "groups" not in st.session_state:
    st.session_state.groups = {}

# Title
st.title("💰 Expense Splitter with AI")

# 1️⃣ Create or Select Group
group_name = st.text_input("Enter Group Name:")
if st.button("Create Group"):
    if group_name:
        st.session_state.groups[group_name] = {"members": [], "expenses": []}
        st.success(f"Group '{group_name}' created!")

# Select Existing Group
if st.session_state.groups:
    selected_group = st.selectbox("Select Group:", list(st.session_state.groups.keys()))
    members = st.session_state.groups[selected_group]["members"]
    expenses = st.session_state.groups[selected_group]["expenses"]

    # 2️⃣ Add Members
    new_member = st.text_input("Add Member Name:")
    if st.button("Add Member"):
        if new_member not in members:
            members.append(new_member)
            st.success(f"{new_member} added to {selected_group}!")

    # 3️⃣ Add Expense
    st.subheader("➕ Add Expense")
    description = st.text_input("Expense Description:")
    amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
    paid_by = st.selectbox("Paid By:", members)
    split_among = st.multiselect("Split Among:", members, default=members)

    if st.button("Add Expense"):
        if paid_by and split_among:
            expenses.append({"desc": description, "amount": amount, "paid_by": paid_by, "split_among": split_among})
            st.success("Expense Added!")

    # 4️⃣ Show Expenses
    st.subheader("📜 Expense List")
    if expenses:
        df = pd.DataFrame(expenses)
        st.table(df)

    # 5️⃣ Calculate Settlements
    st.subheader("📊 Settlements")
    balances = {member: 0 for member in members}

    for expense in expenses:
        per_person = expense["amount"] / len(expense["split_among"])
        for member in expense["split_among"]:
            if member != expense["paid_by"]:
                balances[member] -= per_person
                balances[expense["paid_by"]] += per_person

    for person, balance in balances.items():
        if balance < 0:
            st.warning(f"{person} needs to pay ₹{-balance:.2f}")
        elif balance > 0:
            st.success(f"{person} will receive ₹{balance:.2f}")

    # 6️⃣ AI Insights (Google Gemini)
    st.subheader("🔍 AI Insights")
    if st.button("Get AI Suggestions"):
        prompt = f"Analyze this expense data and suggest ways to optimize spending:\n{expenses}"
        response = genai.chat(model="gemini-pro", prompt=prompt)
        st.write(response.text)

    # 7️⃣ Payment Integration (Razorpay)
    st.subheader("💳 Make a Payment")
    pay_to = st.selectbox("Pay To:", [p for p in balances if balances[p] > 0])
    pay_amount = st.number_input("Amount to Pay (₹)", min_value=0.0, format="%.2f")

    if st.button("Pay Now"):
        payment = razorpay_client.order.create({
            "amount": int(pay_amount * 100),  # Convert to paise
            "currency": "INR",
            "payment_capture": "1"
        })
        st.success(f"Payment Link: {payment['id']}")