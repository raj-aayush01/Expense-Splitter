import streamlit as st
import pandas as pd
import google.generativeai as genai
import razorpay
from dotenv import load_dotenv
import os

# Load API Keys
load_dotenv()
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

# Configure APIs
genai.configure(api_key=GENAI_API_KEY)
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

# Expense Data
if "groups" not in st.session_state:
    st.session_state.groups = {}

st.title("💰 Smart Expense Splitter with AI & Payments")

# 1️⃣ Create or Select Group
group_name = st.text_input("Enter Group Name:")
if st.button("Create Group"):
    if group_name:
        st.session_state.groups[group_name] = {"members": [], "expenses": [], "paid_status": {}}
        st.success(f"Group '{group_name}' created!")

if st.session_state.groups:
    selected_group = st.selectbox("Select Group:", list(st.session_state.groups.keys()))
    members = st.session_state.groups[selected_group]["members"]
    expenses = st.session_state.groups[selected_group]["expenses"]
    paid_status = st.session_state.groups[selected_group]["paid_status"]

    # 2️⃣ Add Members
    new_member = st.text_input("Add Member Name:")
    if st.button("Add Member"):
        if new_member not in members:
            members.append(new_member)
            paid_status[new_member] = False  # Default unpaid
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

    # 4️⃣ Show Expenses with Mark Paid ✅
    st.subheader("📜 Expense List")
    if expenses:
        df = pd.DataFrame(expenses)
        st.table(df)

        st.subheader("✅ Mark Payments")
        for member in members:
            if st.checkbox(f"{member} has paid"):
                paid_status[member] = True

    # 5️⃣ Calculate Settlements & Shared Wallet
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

    st.subheader("💰 Shared Wallet")
    wallet_amount = st.number_input("Enter Shared Wallet Amount (₹)", min_value=0.0, format="%.2f")
    if st.button("Add to Shared Wallet"):
        st.success(f"₹{wallet_amount} added to the shared wallet!")

    # 6️⃣ AI Insights (Google Gemini)
    st.subheader("🔍 AI Insights")
    if st.button("Get AI Suggestions"):
        prompt = f"Analyze this expense data and suggest ways to optimize spending:\n{expenses}"
        response = genai.chat(model="gemini-pro", prompt=prompt)
        st.write(response.text)

    # 7️⃣ Leaderboard & Gamification 🏆
    st.subheader("🏆 Leaderboard")
    sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
    for idx, (member, balance) in enumerate(sorted_balances):
        st.write(f"🥇 Rank {idx+1}: {member} (₹{balance:.2f})")

    # 8️⃣ Dynamic Group Expense Charts & Reports 📊
    st.subheader("📉 Group Expense Reports")
    chart_data = pd.DataFrame({"Members": list(balances.keys()), "Balances": list(balances.values())})
    st.bar_chart(chart_data.set_index("Members"))

    # 9️⃣ Payment Integration (Razorpay)
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