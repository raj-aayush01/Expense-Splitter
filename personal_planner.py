import streamlit as st
import pandas as pd
import calendar
from datetime import datetime

# Initialize session state for storing expenses
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Item", "Amount"])

# Streamlit UI
st.title("💰 Monthly Expense Tracker")

# Month Selection
month_names = list(calendar.month_name)[1:]  # Get month names
selected_month = st.selectbox("Select Month", month_names)

# Convert month name to number
month_number = month_names.index(selected_month) + 1
current_year = datetime.now().year  # Use the current year

# Date Selection
selected_date = st.date_input("Select Date to Add/View Expenses", 
                              min_value=datetime(current_year, month_number, 1), 
                              max_value=datetime(current_year, month_number, calendar.monthrange(current_year, month_number)[1]))

# Calendar Display with Highlighted Dates
st.write(f"### Calendar for {selected_month} {current_year}")

# Get all recorded expense dates
expense_dates = st.session_state.expenses["Date"].tolist()
expense_dates = [datetime.strptime(date, "%Y-%m-%d").day for date in expense_dates if date.startswith(f"{current_year}-{month_number:02d}")]

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

# Expense Entry
st.write(f"### Expenses for {selected_date.strftime('%Y-%m-%d')}")
expense_item = st.text_input("Enter Expense Item", "")
expense_amount = st.number_input("Enter Amount", min_value=0.0, format="%.2f")

if st.button("Add Expense"):
    if expense_item and expense_amount:
        new_expense = pd.DataFrame({"Date": [selected_date.strftime('%Y-%m-%d')], 
                                    "Item": [expense_item], 
                                    "Amount": [expense_amount]})
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
        st.success("Expense added successfully!")
        st.rerun()  # Refresh to update calendar highlights

# Display Expenses for Selected Month
st.write(f"### Expenses for {selected_month} {current_year}")
filtered_expenses = st.session_state.expenses[st.session_state.expenses["Date"].str.startswith(f"{current_year}-{month_number:02d}")]

if not filtered_expenses.empty:
    st.dataframe(filtered_expenses)
    total_expenses = filtered_expenses["Amount"].sum()
    st.write(f"## 💵 Total Expenses for {selected_month} {current_year}: ₹{total_expenses:.2f}")
else:
    st.write("No expenses recorded for this month.")

# CSV Download
if not filtered_expenses.empty:
    csv = filtered_expenses.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, f"expenses_{selected_month}_{current_year}.csv", "text/csv")
