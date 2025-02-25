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
        st.session_state.groups[group_name] = {
            "members": [],
            "expenses": [],
            "paid_status": {}
        }
        st.success(f"Group '{group_name}' created!")

if st.session_state.groups:
    selected_group = st.selectbox("Select Group:", list(st.session_state.groups.keys()))
    members = st.session_state.groups[selected_group]["members"]
    expenses = st.session_state.groups[selected_group]["expenses"]
    paid_status = st.session_state.groups[selected_group]["paid_status"]

    # 2️⃣ Add Members
    new_member = st.text_input("Add Member Name:")
    if st.button("Add Member"):
        if new_member and new_member not in members:
            members.append(new_member)
            paid_status[new_member] = False  # Default unpaid
            st.success(f"{new_member} added to {selected_group}!")

    # 3️⃣ Add Expense
    st.subheader("➕ Add Expense")
    description = st.text_input("Expense Description:")
    amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
    paid_by = st.selectbox("Paid By:", members if members else ["No Members Yet"])
    split_among = st.multiselect("Split Among:", members, default=members)

    if st.button("Add Expense"):
        if paid_by and split_among:
            expenses.append({
                "desc": description,
                "amount": round(amount, 2),  # Ensure 2-decimal precision
                "paid_by": paid_by,
                "split_among": split_among
            })
            st.success("Expense Added!")

    # 4️⃣ Show Expenses
    st.subheader("📜 Expense List")
    if expenses:
        df_expenses = pd.DataFrame(expenses)
        # Make the index start from 1
        df_expenses.index = df_expenses.index + 1

        styled_df = (
            df_expenses.style
            .format({"amount": "{:.2f}"})
            .set_table_styles(
                [
                    {"selector": "th", "props": [("font-size", "16px"), ("text-align", "center")]},
                    {"selector": "td", "props": [("font-size", "16px"), ("text-align", "center"), ("border", "1px solid #ccc")]}
                ]
            )
            .set_properties(**{"width": "150px"})
        )
        st.dataframe(styled_df, use_container_width=True)

        # 4.1) Download Expense Sheet CSV
        st.markdown("#### Download Expense Sheet")
        expense_csv = df_expenses.to_csv(index=True).encode('utf-8')
        st.download_button(
            label="Download Expense CSV",
            data=expense_csv,
            file_name=f"{selected_group}_expenses.csv",
            mime="text/csv"
        )

    # 5️⃣ Mark Payments
    st.subheader("✅ Mark Payments")
    for member in members:
        paid_checkbox = st.checkbox(
            f"{member} has paid",
            value=paid_status.get(member, False),
            key=f"paid_{member}"
        )
        paid_status[member] = paid_checkbox

    # 6️⃣ Calculate Balances
    st.subheader("📊 Balance Sheet (Updated)")

    # First, calculate raw balances from the expense data
    balances = {member: 0 for member in members}
    for expense in expenses:
        per_person = expense["amount"] / len(expense["split_among"])
        for member in expense["split_among"]:
            if member != expense["paid_by"]:
                balances[member] -= per_person
                balances[expense["paid_by"]] += per_person

    # If a member is marked as paid, set their balance to 0
    for member in members:
        if paid_status.get(member, False):
            balances[member] = 0

    # Display who needs to pay or receive
    for person, balance in balances.items():
        if balance < 0:
            st.warning(f"{person} needs to pay ₹{-balance:.2f}")
        elif balance > 0:
            st.success(f"{person} will receive ₹{balance:.2f}")
        else:
            st.info(f"{person} is settled up.")

    # 6.1) Show the Balance Sheet in a table
    st.markdown("#### Balance Sheet Table")
    df_balances = pd.DataFrame(list(balances.items()), columns=["Member", "Balance"])
    df_balances["Balance"] = df_balances["Balance"].round(2)
    df_balances.index = df_balances.index + 1  # index starts at 1

    styled_balances = (
        df_balances.style
        .format({"Balance": "{:.2f}"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("font-size", "16px"), ("text-align", "center")]},
                {"selector": "td", "props": [("font-size", "16px"), ("text-align", "center"), ("border", "1px solid #ccc")]}
            ]
        )
        .set_properties(**{"width": "150px"})
    )
    st.dataframe(styled_balances, use_container_width=True)

    # 6.2) Download Balance Sheet CSV
    st.markdown("#### Download Balance Sheet")
    balance_csv = df_balances.to_csv(index=True).encode('utf-8')
    st.download_button(
        label="Download Balance CSV",
        data=balance_csv,
        file_name=f"{selected_group}_balances.csv",
        mime="text/csv"
    )

    # 7️⃣ Shared Wallet
    st.subheader("💰 Shared Wallet")
    wallet_amount = st.number_input("Enter Shared Wallet Amount (₹)", min_value=0.0, format="%.2f")
    if st.button("Add to Shared Wallet"):
        st.success(f"₹{wallet_amount:.2f} added to the shared wallet!")

    # 8️⃣ AI Insights (Google Gemini)
    st.subheader("🔍 AI Insights")
    if st.button("Get AI Suggestions"):
        model = genai.GenerativeModel("gemini-1.5-flash")  # or "gemini-2", etc.
        response = model.generate_content(
            f"Analyze this expense data and generate a well-explained summary in indian rupees:\n{expenses}"
        )
        st.write(response.text)

    # 9️⃣ Leaderboard & Gamification
    st.subheader("🏆 Leaderboard")
    sorted_balances = sorted(balances.items(), key=lambda x: x[1], reverse=True)
    for idx, (member, balance) in enumerate(sorted_balances):
        st.write(f"🥇 Rank {idx+1}: {member} (₹{balance:.2f})")

    # 🔟 Dynamic Group Expense Charts & Reports
    st.subheader("📉 Group Expense Reports")
    chart_data = pd.DataFrame({
        "Members": list(balances.keys()),
        "Balances": list(balances.values())
    })
    st.bar_chart(chart_data.set_index("Members"))

    # 11️⃣ Payment Integration (Razorpay)
    st.subheader("💳 Make a Payment")
    pay_to = st.selectbox("Pay To:", [p for p in balances if balances[p] > 0] or ["No one to pay"])
    pay_amount = st.number_input("Amount to Pay (₹)", min_value=0.0, format="%.2f")

    if st.button("Pay Now"):
        if pay_to != "No one to pay" and pay_amount > 0:
            payment = razorpay_client.order.create({
                "amount": int(pay_amount * 100),  # Convert to paise
                "currency": "INR",
                "payment_capture": "1"
            })
            st.success(f"Payment Link (Order ID): {payment['id']}")
        else:
            st.warning("Please select a valid payee and amount.")
