import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

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

# --- Helper Function: Clean Text for PDF ---
def clean_for_pdf(text):
    # বাংলা লেখা থাকলে তা পিডিএফে ঘর ঘর দেখায়, তাই সাময়িকভাবে সেটিকে চেনার মতো টেক্সটে রূপান্তর করা
    mapping = {
        "ফটোকপি": "Photocopy", "প্রিন্ট": "Print", "কম্পোজ": "Compose", 
        "অনলাইন": "Online Work", "NID": "NID Service", "জন্ম নিবন্ধন": "Birth Reg", 
        "ছবি": "Photo", "ল্যামিনেশন": "Lamination", "স্মার্ট কার্ড": "Smart Card", "অন্যান্য": "Others",
        "দোকান ভাড়া": "Shop Rent", "বিদ্যুৎ বিল": "Electricity Bill", 
        "ইন্টারনেট বিল": "Internet Bill", "চা-নাস্তা": "Tea-Snacks"
    }
    return mapping.get(str(text), str(text))

# --- Helper Function: Generate PDF ---
def generate_pdf(title, headers, rows):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#1E3A8A'), alignment=1)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, alignment=1)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=10, leading=12)
    
    # Header
    story.append(Paragraph("<b>Brothers Computer Management System</b>", title_style))
    story.append(Paragraph(f"Report: {title} | Generated on: {datetime.today().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 20))
    
    # Table Data Preparation
    table_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in headers]]
    for row in rows:
        # প্রতিটি ঘরের বাংলা লেখাকে ইংরেজিতে ক্লিন করা যাতে পিডিএফ নষ্ট না হয়
        cleaned_row = [Paragraph(clean_for_pdf(item), cell_style) for item in row]
        table_data.append(cleaned_row)
        
    t = Table(table_data, colWidths=[doc.width/len(headers)]*len(headers))
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F3F4F6')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#FAFAFA')])
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Login System ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.title("🖥️ Brothers Computer Management System")
    st.subheader("অনলাইন লগইন প্যানেল")
    username = st.text_input("ইউজারনেম (Username)")
    password = st.text_input("পাসওয়ার্ড (Password)", type="password")
    if st.button("লগইন করুন"):
        if username == "brothers" and password == "12345":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড!")

# --- Main Application ---
if not st.session_state['logged_in']:
    login()
else:
    st.sidebar.title("Brothers Computer")
    st.sidebar.write("---")
    menu = st.sidebar.radio("মেনু সিলেক্ট করুন", ["🏠 ড্যাশবোর্ড ও রিপোর্ট", "💰 বিক্রি (Sales)", "🏦 লোন ম্যানেজার", "💸 খরচ (Expense)", "💾 ডাউনলোড ও এক্সপোর্ট"])
    
    if st.sidebar.button("লগআউট (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

    # --- 1. Dashboard ---
    if menu == "🏠 ড্যাশবোর্ড ও রিপোর্ট":
        st.title("🏠 ড্যাশবোর্ড ও রিপোর্ট")
        current_date = datetime.today().strftime('%Y-%m-%d')
        target_date = st.text_input("তারিখ দিয়ে হিসাব দেখুন (YYYY-MM-DD):", current_date)
        
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date=?", (target_date,))
        date_sales = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (target_date,))
        date_expense = cursor.fetchone()[0] or 0
        net_profit = date_sales - date_expense
        current_month = target_date[:7]
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date LIKE ?", (f"{current_month}%",))
        monthly_sales = cursor.fetchone()[0] or 0

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
                st.rerun()
        
        st.write("---")
        st.subheader("📋 আজকের বিক্রির তালিকা")
        today_date = datetime.today().strftime('%Y-%m-%d')
        df_today_sales = pd.read_sql_query("SELECT id, item, amount FROM sales WHERE date=?", conn, params=(today_date,))
        
        if not df_today_sales.empty:
            for index, row in df_today_sales.iterrows():
                col_text, col_btn = st.columns([4, 1])
                col_text.write(f"🔹 {row['item']} - ৳ {row['amount']}")
                if col_btn.button(f"❌ Delete", key=f"del_sale_{row['id']}"):
                    cursor.execute("DELETE FROM sales WHERE id=?", (int(row['id']),))
                    conn.commit()
                    st.rerun()
        else:
            st.info("আজকে এখনো কোনো বিক্রি এন্ট্রি করা হয়নি।")

    # --- 3. Loan Manager ---
    elif menu == "🏦 লোন ম্যানেজার":
        st.title("🏦 এনজিও লোন ও কিস্তি ম্যানেজার")
        col1, col2, col3 = st.columns(3)
        ngo = col1.text_input("এনজিওর নাম (ইংরেজি অক্ষরে লিখলে পিডিএফে সুন্দর আসবে)")
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
                st.rerun()
        
        st.write("---")
        st.subheader("📋 বর্তমান লোনের তালিকা")
        cursor.execute("SELECT id, ngo_name, total_loan, paid_loan FROM loans")
        loan_rows = cursor.fetchall()
        
        if loan_rows:
            for row in loan_rows:
                l_id, l_name, l_total, l_paid = row
                l_due = l_total - l_paid
                col_text, col_btn = st.columns([4, 1])
                color_tag = "🔴" if l_due > 0 else "🟢"
                col_text.write(f"{color_tag} **{l_name}** -> মোট ঋণ: ৳{l_total} | শোধ: ৳{l_paid} | **বাকি: ৳{l_due}**")
                if col_btn.button(f"❌ Delete", key=f"del_loan_{l_id}"):
                    cursor.execute("DELETE FROM loans WHERE id=?", (l_id,))
                    conn.commit()
                    st.rerun()
        else:
            st.info("কোনো লোনের তথ্য নেই।")

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
                st.rerun()
        
        st.write("---")
        st.subheader("📋 আজকের খরচের তালিকা")
        today_date = datetime.today().strftime('%Y-%m-%d')
        df_today_exp = pd.read_sql_query("SELECT id, category, amount FROM expenses WHERE date=?", conn, params=(today_date,))
        
        if not df_today_exp.empty:
            for index, row in df_today_exp.iterrows():
                col_text, col_btn = st.columns([4, 1])
                col_text.write(f"🔹 {row['category']} - ৳ {row['amount']}")
                if col_btn.button(f"❌ Delete", key=f"del_exp_{row['id']}"):
                    cursor.execute("DELETE FROM expenses WHERE id=?", (int(row['id']),))
                    conn.commit()
                    st.rerun()
        else:
            st.info("আজকে এখনো কোনো খরচ এন্ট্রি করা হয়নি।")

    # --- 5. Download & Export ---
    elif menu == "💾 ডাউনলোড ও এক্সপোর্ট":
        st.title("💾 ডেটা ডাউনলোড ও রিপোর্ট প্যানেল")
        st.write("আপনার সমস্ত এন্ট্রি এখান থেকে পিডিএফ বা এক্সেল আকারে ডাউনলোড করতে পারবেন।")
        st.write("---")
        
        # 1. Sales Download
        st.subheader("💰 বিক্রির রিপোর্ট (Sales Report)")
        df_sales = pd.read_sql_query("SELECT date AS 'Date', item AS 'Item', amount AS 'Amount' FROM sales", conn)
        if not df_sales.empty:
            col1, col2 = st.columns(2)
            col1.download_button("📊 Excel (Sales) ডাউনলোড করুন", data=df_sales.to_csv(index=False).encode('utf-8'), file_name='sales_report.csv', mime='text/csv')
            sales_pdf = generate_pdf("Sales Report", ["Date", "Item", "Amount"], df_sales.values.tolist())
            col2.download_button("📄 PDF (Sales) ডাউনলোড করুন", data=sales_pdf, file_name='sales_report.pdf', mime='application/pdf')
        else:
            st.info("বিক্রির কোনো ডেটা নেই।")
            
        st.write("---")
        
        # 2. Expenses Download
        st.subheader("💸 খরচের রিপোর্ট (Expense Report)")
        df_exp = pd.read_sql_query("SELECT date AS 'Date', category AS 'Category', amount AS 'Amount' FROM expenses", conn)
        if not df_exp.empty:
            col1, col2 = st.columns(2)
            col1.download_button("📊 Excel (Expenses) ডাউনলোড করুন", data=df_exp.to_csv(index=False).encode('utf-8'), file_name='expense_report.csv', mime='text/csv')
            exp_pdf = generate_pdf("Expense Report", ["Date", "Category", "Amount"], df_exp.values.tolist())
            col2.download_button("📄 PDF (Expenses) ডাউনলোড করুন", data=exp_pdf, file_name='expense_report.pdf', mime='application/pdf')
        else:
            st.info("খরচের কোনো ডেটা নেই।")
            
        st.write("---")
        
        # 3. Loans Download
        st.subheader("🏦 লোনের রিপোর্ট (Loan Report)")
        df_loans = pd.read_sql_query("SELECT ngo_name AS 'NGO Name', total_loan AS 'Total Loan', paid_loan AS 'Paid Loan', date AS 'Last Update' FROM loans", conn)
        if not df_loans.empty:
            col1, col2 = st.columns(2)
            col1.download_button("📊 Excel (Loans) ডাউনলোড করুন", data=df_loans.to_csv(index=False).encode('utf-8'), file_name='loan_report.csv', mime='text/csv')
            loan_pdf = generate_pdf("Loan Report", ["NGO Name", "Total Loan", "Paid Loan", "Last Update"], df_loans.values.tolist())
            col2.download_button("📄 PDF (Loans) ডাউনলোড করুন", data=loan_pdf, file_name='loan_report.pdf', mime='application/pdf')
        else:
            st.info("লোনের কোনো ডেটা নেই।")
