import streamlit as st
import pandas as pd
import calendar
from datetime import datetime
import google.generativeai as genai
import razorpay
from dotenv import load_dotenv
import os

# Page configuration
st.set_page_config(
    page_title="Smart Expense Manager",
    page_icon="💰",
    layout="wide"
)

# Load API Keys
load_dotenv()
GENAI_API_KEY = os.getenv("GOOGLE_API_KEY")
RAZORPAY_KEY = os.getenv("RAZORPAY_KEY")
RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET")

# Configure APIs if keys are available
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)
if RAZORPAY_KEY and RAZORPAY_SECRET:
    razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY, RAZORPAY_SECRET))

# Initialize session states
if "groups" not in st.session_state:
    st.session_state.groups = {}
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Item", "Amount"])
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "Expense Splitter"

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #3498db;
        margin-top: 1.5rem;
    }
    .card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .success-msg {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .warning-msg {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for navigation
with st.sidebar:
    st.image("https://place-hold.it/300x100?text=Expense%20Manager&fontsize=23", width=270)
    st.title("Navigation")
    selected_feature = st.radio(
        "Choose Feature",
        ["Expense Splitter", "Monthly Expense Tracker"],
        index=0 if st.session_state.active_tab == "Expense Splitter" else 1
    )
    st.session_state.active_tab = selected_feature
    
    # Show some app info
    st.markdown("---")
    st.markdown("### About this App")
    st.info("""
    This app helps you manage your expenses in two ways:
    - Split expenses among friends
    - Track your monthly spending
    """)
    
    # Show credentials section only if visible 
    with st.expander("API Credentials"):
        st.text_input("Google API Key", 
                     value=GENAI_API_KEY if GENAI_API_KEY else "", 
                     type="password", 
                     key="google_key")
        st.text_input("Razorpay Key", 
                     value=RAZORPAY_KEY if RAZORPAY_KEY else "", 
                     type="password",
                     key="razor_key")
        st.text_input("Razorpay Secret", 
                     value=RAZORPAY_SECRET if RAZORPAY_SECRET else "", 
                     type="password",
                     key="razor_secret")

# EXPENSE SPLITTER FEATURE
def show_expense_splitter():
    st.markdown("<h1 class='main-header'>💰 Smart Expense Splitter</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        group_name = st.text_input("Enter Group Name:")
        if st.button("Create Group"):
            if group_name:
                st.session_state.groups[group_name] = {
                    "members": [],
                    "expenses": [],
                    "paid_status": {}
                }
                st.markdown("<div class='success-msg'>Group created successfully!</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    if not st.session_state.groups:
        st.warning("No groups created yet. Create a group to get started!")
        return
    
    selected_group = st.selectbox("Select Group:", list(st.session_state.groups.keys()))
    members = st.session_state.groups[selected_group]["members"]
    expenses = st.session_state.groups[selected_group]["expenses"]
    paid_status = st.session_state.groups[selected_group]["paid_status"]
    
    # Group Management Section
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Members", "➕ Add Expense", "📊 Balances", "💳 Payments"])
    
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='sub-header'>Add Members</h3>", unsafe_allow_html=True)
        new_member = st.text_input("Add Member Name:", key="new_member_input")
        if st.button("Add Member"):
            if new_member and new_member not in members:
                members.append(new_member)
                paid_status[new_member] = False  # Default unpaid
                st.markdown(f"<div class='success-msg'>{new_member} added to {selected_group}!</div>", unsafe_allow_html=True)
        
        if members:
            st.markdown("#### Current Members")
            for i, member in enumerate(members):
                st.write(f"{i+1}. {member}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='sub-header'>Add New Expense</h3>", unsafe_allow_html=True)
        description = st.text_input("Expense Description:")
        amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        paid_by = st.selectbox("Paid By:", members if members else ["No Members Yet"])
        split_among = st.multiselect("Split Among:", members, default=members)
        
        if st.button("Add Expense"):
            if members and paid_by in members and split_among:
                expenses.append({
                    "desc": description,
                    "amount": round(amount, 2),
                    "paid_by": paid_by,
                    "split_among": split_among
                })
                st.markdown("<div class='success-msg'>Expense Added!</div>", unsafe_allow_html=True)
        
        # Show Expenses
        if expenses:
            st.markdown("#### Expense List")
            df_expenses = pd.DataFrame(expenses)
            df_expenses.index = df_expenses.index + 1
            st.dataframe(df_expenses, use_container_width=True)
            
            # Download option
            expense_csv = df_expenses.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="Download Expense CSV",
                data=expense_csv,
                file_name=f"{selected_group}_expenses.csv",
                mime="text/csv"
            )
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='sub-header'>Balance Sheet</h3>", unsafe_allow_html=True)
        
        if not members or not expenses:
            st.warning("Add members and expenses to see the balance sheet.")
        else:
            # Calculate balances
            balances = {member: 0 for member in members}
            for expense in expenses:
                per_person = expense["amount"] / len(expense["split_among"])
                for member in expense["split_among"]:
                    if member != expense["paid_by"]:
                        balances[member] -= per_person
                        balances[expense["paid_by"]] += per_person
            
            # Apply paid status
            for member in members:
                if paid_status.get(member, False):
                    balances[member] = 0
            
            # Show who needs to pay
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Who needs to pay")
                for person, balance in balances.items():
                    if balance < 0:
                        st.warning(f"{person} needs to pay ₹{-balance:.2f}")
                    elif balance == 0:
                        st.info(f"{person} is settled up.")
            
            with col2:
                st.markdown("#### Who will receive")
                for person, balance in balances.items():
                    if balance > 0:
                        st.success(f"{person} will receive ₹{balance:.2f}")
            
            # Balance table
            df_balances = pd.DataFrame(list(balances.items()), columns=["Member", "Balance"])
            df_balances["Balance"] = df_balances["Balance"].round(2)
            df_balances.index = df_balances.index + 1
            st.dataframe(df_balances, use_container_width=True)
            
            # Download option
            balance_csv = df_balances.to_csv(index=True).encode('utf-8')
            st.download_button(
                label="Download Balance CSV",
                data=balance_csv,
                file_name=f"{selected_group}_balances.csv",
                mime="text/csv"
            )
            
            # Visualize balances
            st.markdown("#### Balance Visualization")
            chart_data = pd.DataFrame({
                "Members": list(balances.keys()),
                "Balances": list(balances.values())
            })
            st.bar_chart(chart_data.set_index("Members"))
        st.markdown("</div>", unsafe_allow_html=True)
    
    with tab4:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='sub-header'>Payments</h3>", unsafe_allow_html=True)
        
        # Mark payments section
        st.markdown("#### Mark as Paid")
        for member in members:
            paid_checkbox = st.checkbox(
                f"{member} has paid",
                value=paid_status.get(member, False),
                key=f"paid_{selected_group}_{member}"
            )
            paid_status[member] = paid_checkbox
        
        # Razorpay Integration (if API keys are available)
        if RAZORPAY_KEY and RAZORPAY_SECRET:
            st.markdown("#### Make a Payment")
            
            # Calculate balances for dropdown
            balances = {member: 0 for member in members}
            for expense in expenses:
                per_person = expense["amount"] / len(expense["split_among"])
                for member in expense["split_among"]:
                    if member != expense["paid_by"]:
                        balances[member] -= per_person
                        balances[expense["paid_by"]] += per_person
            
            pay_to = st.selectbox("Pay To:", [p for p in balances if balances[p] > 0] or ["No one to pay"])
            pay_amount = st.number_input("Amount to Pay (₹)", min_value=0.0, format="%.2f", key="pay_amount")
            
            if st.button("Pay Now"):
                if pay_to != "No one to pay" and pay_amount > 0:
                    try:
                        payment = razorpay_client.order.create({
                            "amount": int(pay_amount * 100),  # Convert to paise
                            "currency": "INR",
                            "payment_capture": "1"
                        })
                        st.success(f"Payment Link (Order ID): {payment['id']}")
                    except Exception as e:
                        st.error(f"Payment error: {str(e)}")
                else:
                    st.warning("Please select a valid payee and amount.")
        else:
            st.info("Razorpay payment integration requires API keys. Please configure them in the sidebar.")
        st.markdown("</div>", unsafe_allow_html=True)
        
        # AI Insights (if API key is available)
        if GENAI_API_KEY and expenses:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<h3 class='sub-header'>AI Insights</h3>", unsafe_allow_html=True)
            if st.button("Get AI Suggestions"):
                try:
                    model = genai.GenerativeModel("gemini-1.5-flash")
                    response = model.generate_content(
                        f"Analyze this expense data and generate a well-explained summary in Indian rupees:\n{expenses}"
                    )
                    st.write(response.text)
                except Exception as e:
                    st.error(f"AI error: {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

# MONTHLY EXPENSE TRACKER FEATURE
def show_expense_tracker():
    st.markdown("<h1 class='main-header'>💸 Monthly Expense Tracker</h1>", unsafe_allow_html=True)
    
    # Month Selection
    month_names = list(calendar.month_name)[1:]  # Get month names
    selected_month = st.selectbox("Select Month", month_names)
    
    # Convert month name to number
    month_number = month_names.index(selected_month) + 1
    current_year = datetime.now().year  # Use the current year
    
    # Layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<h3 class='sub-header'>Add New Expense</h3>", unsafe_allow_html=True)
        
        # Date Selection
        selected_date = st.date_input("Select Date", 
                                    min_value=datetime(current_year, month_number, 1), 
                                    max_value=datetime(current_year, month_number, calendar.monthrange(current_year, month_number)[1]))
        
        # Expense Entry
        expense_item = st.text_input("Expense Item", "")
        expense_amount = st.number_input("Amount (₹)", min_value=0.0, format="%.2f")
        
        if st.button("Add Expense"):
            if expense_item and expense_amount > 0:
                new_expense = pd.DataFrame({
                    "Date": [selected_date.strftime('%Y-%m-%d')], 
                    "Item": [expense_item], 
                    "Amount": [expense_amount]
                })
                st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
                st.markdown("<div class='success-msg'>Expense added successfully!</div>", unsafe_allow_html=True)
                st.rerun()  # Refresh to update calendar highlights
            else:
                st.warning("Please enter both an item name and an amount greater than zero.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown(f"<h3 class='sub-header'>Calendar for {selected_month} {current_year}</h3>", unsafe_allow_html=True)
        
        # Get all recorded expense dates
        expense_dates = st.session_state.expenses["Date"].tolist()
        expense_dates = [datetime.strptime(date, "%Y-%m-%d").day for date in expense_dates 
                        if date.startswith(f"{current_year}-{month_number:02d}")]
        
        # Generate a monthly calendar with highlighted expense dates
        month_calendar = calendar.monthcalendar(current_year, month_number)
        calendar_html = "<table style='width:100%; text-align:center; font-size:16px;'>"
        
        # Table headers
        calendar_html += "<tr><th>Mon</th><th>Tue</th><th>Wed</th><th>Thu</th><th>Fri</th><th style='color:red;'>Sat</th><th style='color:red;'>Sun</th></tr>"
        
        # Populate calendar with highlighted days
        for week in month_calendar:
            calendar_html += "<tr>"
            for day in week:
                if day == 0:
                    calendar_html += "<td></td>"  # Empty cell for padding
                elif day in expense_dates:
                    calendar_html += f"<td style='background-color:#90EE90; border-radius: 5px; padding:8px;'>{day}</td>"  # Highlighted in light green
                else:
                    calendar_html += f"<td style='padding:8px;'>{day}</td>"
            calendar_html += "</tr>"
        
        calendar_html += "</table>"
        st.markdown(calendar_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display Expenses for Selected Month
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown(f"<h3 class='sub-header'>Expenses for {selected_month} {current_year}</h3>", unsafe_allow_html=True)
    
    filtered_expenses = st.session_state.expenses[st.session_state.expenses["Date"].str.startswith(f"{current_year}-{month_number:02d}")]
    
    if not filtered_expenses.empty:
        st.dataframe(filtered_expenses, use_container_width=True)
        total_expenses = filtered_expenses["Amount"].sum()
        st.markdown(f"### 💵 Total Expenses: ₹{total_expenses:.2f}")
        
        # Download option
        csv = filtered_expenses.to_csv(index=False).encode("utf-8")
        st.download_button("Download Expense Report", csv, f"expenses_{selected_month}_{current_year}.csv", "text/csv")
        
        # Show expense breakdown
        st.markdown("#### Expense Breakdown")
        category_data = filtered_expenses.groupby("Item")["Amount"].sum().reset_index()
        st.bar_chart(category_data.set_index("Item"))
    else:
        st.info("No expenses recorded for this month. Add some expenses to see them here.")
    st.markdown("</div>", unsafe_allow_html=True)

# Main app logic - show the selected feature
if st.session_state.active_tab == "Expense Splitter":
    show_expense_splitter()
else:
    show_expense_tracker()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center;'>© 2025 Smart Expense Manager</p>", unsafe_allow_html=True)