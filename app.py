import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Brothers Computer", page_icon="🖥️", layout="wide")

# --- Database Initialize ---
def init_db():
    conn = sqlite3.connect("online_brothers_data.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, ngo_name TEXT, total_loan REAL, paid_loan REAL, date TEXT)''')
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# --- Login System ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.title("🖥️ Brothers Computer Management System")
    st.subheader("অনলাইন লগইন প্যানেল")
    
    username = st.text_input("ইউজারনেম (Username)")
    password = st.text_input("পাসওয়ার্ড (Password)", type="password")
    
    if st.button("লগইন করুন"):
        # আপনার পছন্দমত ইউজারনেম ও পাসওয়ার্ড এখানে পরিবর্তন করতে পারেন
        if username == "brothers" and password == "12345":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড!")

# --- Main Application ---
if not st.session_state['logged_in']:
    login()
else:
    # Sidebar Navigation
    st.sidebar.title("Brothers Computer")
    st.sidebar.write("---")
    menu = st.sidebar.radio("মেনু সিলেক্ট করুন", ["🏠 ড্যাশবোর্ড ও রিপোর্ট", "💰 বিক্রি (Sales)", "🏦 লোন ম্যানেজার", "💸 খরচ (Expense)", "💾 ব্যাকআপ ও এক্সপোর্ট"])
    
    if st.sidebar.button("লগআউট (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- 1. Dashboard ---
    if menu == "🏠 ড্যাশবোর্ড ও রিপোর্ট":
        st.title("🏠 ড্যাশবোর্ড ও রিপোর্ট")
        
        # Date Filter
        current_date = datetime.today().strftime('%Y-%m-%d')
        target_date = st.text_input("তারিখ দিয়ে হিসাব দেখুন (YYYY-MM-DD):", current_date)
        
        # Fetch Data
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date=?", (target_date,))
        date_sales = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (target_date,))
        date_expense = cursor.fetchone()[0] or 0
        
        net_profit = date_sales - date_expense
        current_month = target_date[:7]
        
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date LIKE ?", (f"{current_month}%",))
        monthly_sales = cursor.fetchone()[0] or 0

        # Display Cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"📅 {target_date} এর বিক্রি", f"৳ {date_sales}")
        col2.metric(f"💸 {target_date} এর খরচ", f"৳ {date_expense}")
        col3.metric("📊 নিট লাভ/ক্ষতি", f"৳ {net_profit}")
        col4.metric("📈 চলতি মাসের বিক্রি", f"৳ {monthly_sales}")

    # --- 2. Sales ---
    elif menu == "💰 বিক্রি (Sales)":
        st.title("💰 নতুন বিক্রি এন্ট্রি")
        options = ["ফটোকপি", "প্রিন্ট", "কম্পোজ", "অনলাইন", "NID", "জন্ম নিবন্ধন", "ছবি", "ল্যামিনেশন", "স্মার্ট কার্ড", "অন্যান্য"]
        item = st.selectbox("কাজের ধরন", options)
        amount = st.number_input("টাকার পরিমাণ (৳)", min_value=0.0, step=10.0)
        
        if st.button("বিক্রি সংরক্ষণ করুন"):
            if amount > 0:
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO sales (item, amount, date) VALUES (?, ?, ?)", (item, amount, today))
                conn.commit()
                st.success(f"{item} বাবদ ৳{amount} বিক্রি সফলভাবে সংরক্ষিত হয়েছে।")
            else:
                st.error("টাকার পরিমাণ অবশ্যই ০ থেকে বেশি হতে হবে।")

    # --- 3. Loan Manager ---
    elif menu == "🏦 লোন ম্যানেজার":
        st.title("🏦 এনজিও লোন ও কিস্তি ম্যানেজার")
        
        col1, col2, col3 = st.columns(3)
        ngo = col1.text_input("এনজিওর নাম")
        total = col2.number_input("মোট ঋণ (৳)", min_value=0.0)
        paid = col3.number_input("পরিশোধিত (৳)", min_value=0.0)
        
        if st.button("লোন যোগ/আপডেট করুন"):
            if ngo:
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("SELECT id FROM loans WHERE ngo_name=?", (ngo,))
                if cursor.fetchone():
                    cursor.execute("UPDATE loans SET total_loan=?, paid_loan=?, date=? WHERE ngo_name=?", (total, paid, today, ngo))
                else:
                    cursor.execute("INSERT INTO loans (ngo_name, total_loan, paid_loan, date) VALUES (?, ?, ?, ?)", (ngo, total, paid, today))
                conn.commit()
                st.success(f"{ngo} এর লোন আপডেট হয়েছে।")
        
        st.write("---")
        # Display Loan Table
        df_loans = pd.read_sql_query("SELECT ngo_name AS 'এনজিও', total_loan AS 'মোট ঋণ', paid_loan AS 'পরিশোধিত' FROM loans", conn)
        if not df_loans.empty:
            df_loans['বাকি ঋণ'] = df_loans['মোট ঋণ'] - df_loans['পরিশোধিত']
            st.dataframe(df_loans.style.map(lambda x: 'background-color: #4a1515; color: white' if x > 0 else '', subset=['বাকি ঋণ']), use_container_width=True)

    # --- 4. Expense ---
    elif menu == "💸 খরচ (Expense)":
        st.title("💸 দোকান খরচ এন্ট্রি")
        options = ["দোকান ভাড়া", "বিদ্যুৎ বিল", "ইন্টারনেট বিল", "চা-নাস্তা", "অন্যান্য"]
        cat = st.selectbox("খরচের খাত", options)
        amount = st.number_input("খরচের পরিমাণ (৳)", min_value=0.0, step=10.0)
        
        if st.button("খরচ সংরক্ষণ করুন"):
            if amount > 0:
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)", (cat, amount, today))
                conn.commit()
                st.success(f"{cat} বাবদ ৳{amount} খরচ সংরক্ষিত হয়েছে।")

    # --- 5. Backup & Export ---
    elif menu == "💾 ব্যাকআপ ও এক্সপোর্ট":
        st.title("💾 ডেটা ব্যাকআপ ও এক্সেল রিপোর্ট")
        
        df_sales = pd.read_sql_query("SELECT * FROM sales", conn)
        if not df_sales.empty:
            excel_data = df_sales.to_csv(index=False).encode('utf-8')
            st.download_button(label="📊 Excel (CSV) হিসেবে সেলস রিপোর্ট ডাউনলোড করুন", data=excel_data, file_name='sales_report.csv', mime='text/csv')
        else:
            st.info("ডাউনলোড করার মতো কোনো বিক্রি ডেটা এখনো নেই।")