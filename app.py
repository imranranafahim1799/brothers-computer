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
st.set_page_config(page_title="Brothers Computer Ultimate", page_icon="🖥️", layout="wide")

# --- Database Initialize ---
def init_db():
    conn = sqlite3.connect("online_brothers_data_v2.db", check_same_thread=False)
    cursor = conn.cursor()
    # Core Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, ngo_name TEXT, total_loan REAL, paid_loan REAL, date TEXT)''')
    # Premium Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS dues (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, phone TEXT, amount REAL, status TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT, qty INTEGER, min_limit INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, staff_name TEXT, salary REAL, advance REAL)''')
    
    # Insert Default Stock if Empty
    cursor.execute("SELECT COUNT(*) FROM stock")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO stock (item_name, qty, min_limit) VALUES ('A4 Paper Rim', 10, 2)")
        cursor.execute("INSERT INTO stock (item_name, qty, min_limit) VALUES ('Printer Toner/Ink', 5, 1)")
    
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# --- Helper Function: Clean Text for PDF ---
def clean_for_pdf(text):
    mapping = {
        "ফটোকপি": "Photocopy", "প্রিন্ট": "Print", "কম্পোজ": "Compose", 
        "অনলাইন কাজ": "Online Work", "NID সার্ভিস": "NID Service", "জন্ম নিবন্ধন": "Birth Reg", 
        "ছবি": "Photo", "ল্যামিনেশন": "Lamination", "অন্যান্য": "Others", "বাকি আদায়": "Due Collected",
        "দোকান ভাড়া": "Shop Rent", "বিদ্যুৎ বিল": "Electricity Bill", 
        "ইন্টারনেট বিল": "Internet Bill", "চা-নাস্তা": "Tea-Snacks", "কাগজ/কালি ক্রয়": "Buy Stock",
        "স্টাফ অ্যাডভান্স": "Staff Advance"
    }
    return mapping.get(str(text), str(text))

# --- Helper Function: Generate All-in-One PDF ---
def generate_master_pdf(sales_rows, expense_rows, loan_rows):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#1E3A8A'), alignment=1)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, alignment=1)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'), spaceBefore=15, spaceAfter=8)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=9, leading=11)
    
    # Header
    story.append(Paragraph("<b>Brothers Computer Management System</b>", title_style))
    story.append(Paragraph(f"All-in-One Master Report | Generated on: {datetime.today().strftime('%Y-%m-%d %H:%M')}", meta_style))
    story.append(Spacer(1, 15))
    
    # Common Table Styler
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ])

    # 1. Sales Table
    story.append(Paragraph("<b>1. Sales Records</b>", section_style))
    sales_headers = ["Date", "Item", "Amount (Tk)"]
    sales_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in sales_headers]]
    for row in sales_rows:
        sales_data.append([Paragraph(clean_for_pdf(item), cell_style) for item in row])
    t1 = Table(sales_data, colWidths=[doc.width/3]*3)
    t1.setStyle(t_style)
    story.append(t1)
    
    # 2. Expense Table
    story.append(Paragraph("<b>2. Expense Records</b>", section_style))
    exp_headers = ["Date", "Category", "Amount (Tk)"]
    exp_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in exp_headers]]
    for row in expense_rows:
        exp_data.append([Paragraph(clean_for_pdf(item), cell_style) for item in row])
    t2 = Table(exp_data, colWidths=[doc.width/3]*3)
    t2.setStyle(t_style)
    story.append(t2)
    
    # 3. Loan Table
    story.append(Paragraph("<b>3. Loan Records</b>", section_style))
    loan_headers = ["NGO Name", "Total Loan", "Paid Loan", "Last Update"]
    loan_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in loan_headers]]
    for row in loan_rows:
        loan_data.append([Paragraph(clean_for_pdf(item), cell_style) for item in row])
    t3 = Table(loan_data, colWidths=[doc.width/4]*4)
    t3.setStyle(t_style)
    story.append(t3)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Login System ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login():
    st.title("🖥️ Brothers Computer Ultimate Management System")
    st.subheader("প্রিমিয়াম অনলাইন ড্যাশবোর্ড")
    username = st.text_input("ইউজারনেম (Username)")
    password = st.text_input("পাসওয়ার্ড (Password)", type="password")
    if st.button("লগইন করুন"):
        if username == "brothers" and password == "12345":
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("ভুল ইউজারনেম অথবা পাসওয়ার্ড!")

if not st.session_state['logged_in']:
    login()
else:
    # Sidebar Navigation
    st.sidebar.title("Brothers ERP v2.0")
    st.sidebar.write("---")
    menu = st.sidebar.radio("মেনু সিলেক্ট করুন", [
        "🏠 ড্যাশবোর্ড ও গ্রাফ চার্ট", 
        "💰 বিক্রি ও রসিদ (Sales)", 
        "📝 কাস্টমার বাকি খাতা (Dues)",
        "💸 খরচ ও স্টাফ (Expense)", 
        "📦 কাগজ ও কালি স্টক (Stock)",
        "🏦 লোন ম্যানেজার (Loans)", 
        "🧮 দৈনিক ক্যাশ ক্লোজিং",
        "💾 ডাউনলোড ও এক্সপোর্ট"
    ])
    
    if st.sidebar.button("লগআউট (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

    # Session State for Cart & Receipts
    if 'cart' not in st.session_state:
        st.session_state['cart'] = []
    if 'last_receipt' not in st.session_state:
        st.session_state['last_receipt'] = None

    # --- 1. Dashboard & Charts ---
    if menu == "🏠 ড্যাশবোর্ড ও গ্রাফ চার্ট":
        st.title("🏠 বিজনেস ওভারভিউ ড্যাশবোর্ড")
        current_date = datetime.today().strftime('%Y-%m-%d')
        target_date = st.text_input("তারিখ দিয়ে হিসাব দেখুন (YYYY-MM-DD):", current_date)
        
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date=?", (target_date,))
        date_sales = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (target_date,))
        date_expense = cursor.fetchone()[0] or 0
        net_profit = date_sales - date_expense
        
        cursor.execute("SELECT SUM(amount) FROM dues WHERE status='Unpaid'")
        total_dues = cursor.fetchone()[0] or 0

        col1, col2, col3, col4 = st.columns(4)
        col1.metric(f"📅 {target_date} এর বিক্রি", f"৳ {date_sales}")
        col2.metric(f"💸 {target_date} এর খরচ", f"৳ {date_expense}")
        col3.metric("📊 আজকের নিট লাভ", f"৳ {net_profit}")
        col4.metric("🔴 কাস্টমারদের মোট বাকি", f"৳ {total_dues}")
        
        st.write("---")
        st.subheader("📈 আয়ের খাতসমূহের গ্রাফিক্যাল চার্ট")
        df_chart_sales = pd.read_sql_query("SELECT item AS 'Category', SUM(amount) AS 'Total_Tk' FROM sales GROUP BY item", conn)
        if not df_chart_sales.empty:
            st.bar_chart(df_chart_sales.set_index('Category'))
        else:
            st.info("চার্ট দেখানোর মতো কোনো বিক্রির ডাটা নেই।")

    # --- 2. Sales & Receipts ---
    elif menu == "💰 বিক্রি ও রসিদ (Sales)":
        st.title("💰 নতুন বিক্রি ও মাল্টিপল আইটেম রসিদ")
        col_form, col_receipt = st.columns([1, 1])
        
        with col_form:
            st.subheader("🛒 কাস্টমারের কাজের তালিকা তৈরি করুন")
            c_name = st.text_input("קাস্টমারের নাম (ঐচ্ছিক)", key="customer_name_input")
            
            options = ["ফটোকপি", "প্রিন্ট", "কম্পোজ", "অনলাইন কাজ", "NID সার্ভিস", "জন্ম নিবন্ধন", "ছবি", "ল্যামিনেশন", "অন্যান্য"]
            item = st.selectbox("কাজের ধরন সিলেক্ট করুন", options)
            amount = st.number_input("এই কাজের টাকার পরিমাণ (৳)", min_value=0.0, step=10.0)
            
            if st.button("➕ এই কাজটি তালিকায় যোগ করুন"):
                if amount > 0:
                    st.session_state['cart'].append({"item": item, "amount": amount})
                    st.success(f"✓ {item} (৳ {amount}) তালিকায় যোগ হয়েছে।")
                else:
                    st.error("টাকার পরিমাণ ০ থেকে বেশি হতে হবে।")
            
            if st.session_state['cart']:
                st.write("---")
                st.write("**এই কাস্টমারের চলতি কাজের তালিকা:**")
                for idx, cart_item in enumerate(st.session_state['cart']):
                    st.write(f"{idx+1}. {cart_item['item']} — ৳ {cart_item['amount']}")
                
                if st.button("❌ তালিকাটি মুছে ফেলুন (Clear Cart)"):
                    st.session_state['cart'] = []
                    st.rerun()
                
                st.write("---")
                if st.button("💾 সব মিলিয়ে রসিদ তৈরি ও সেভ করুন", type="primary"):
                    today = datetime.today().strftime('%Y-%m-%d')
                    total_bill = 0
                    items_summary = []
                    
                    for cart_item in st.session_state['cart']:
                        cursor.execute("INSERT INTO sales (item, amount, date) VALUES (?, ?, ?)", (cart_item['item'], cart_item['amount'], today))
                        total_bill += cart_item['amount']
                        items_summary.append(cart_item)
                        
                        if cart_item['item'] in ["ফটোকপি", "প্রিন্ট"]:
                            cursor.execute("UPDATE stock SET qty = max(0, qty - 1) WHERE item_name='A4 Paper Rim'")
                    
                    conn.commit()
                    
                    st.session_state['last_receipt'] = {
                        "name": c_name if c_name else "Valued Customer",
                        "items": items_summary,
                        "total": total_bill,
                        "date": today
                    }
                    st.session_state['cart'] = [] 
                    st.success("✓ সকল হিসাব একসাথে সংরক্ষণ করা হয়েছে!")
                    st.rerun()
        
        with col_receipt:
            st.subheader("🧾 ডিজিটাল ক্যাশ মেমো (রসিদ)")
            if st.session_state['last_receipt']:
                rcpt = st.session_state['last_receipt']
                
                st.markdown("### 🖥️ BROTHERS COMPUTER")
                st.write(f"**তারিখ:** {rcpt['date']} | **কাস্টমার:** {rcpt['name']}")
                st.write("---")
                for i in rcpt['items']:
                    st.write(f"• {i['item']} — ৳ {i['amount']}")
                st.write("---")
                st.markdown(f"### **সর্বমোট বিল: ৳ {rcpt['total']}**")
                st.success("● পরিশোধিত (Paid)")
                
                if st.button("নতুন কাস্টমারের জন্য ফ্রেশ এন্ট্রি করুন"):
                    st.session_state['last_receipt'] = None
                    st.rerun()
            else:
                st.info("কাজের তালিকা তৈরি করে সেভ বাটনে চাপ দিলে এখানে একীভূত মেমো রসিদ দেখতে পাবেন।")
                
        st.write("---")
        st.subheader("📋 আজকের বিক্রির তালিকা")
        today_date = datetime.today().strftime('%Y-%m-%d')
        df_today_sales = pd.read_sql_query("SELECT id, item, amount FROM sales WHERE date=?", conn, params=(today_date,))
        
        if not df_today_sales.empty:
            for index, row in df_today_sales.iterrows():
                col_text, col_btn = st.columns([5, 1])
                col_text.write(f"🔹 {row['item']} - ৳ {row['amount']}")
                if col_btn.button(f"❌ Delete", key=f"del_sale_{row['id']}"):
                    cursor.execute("DELETE FROM sales WHERE id=?", (int(row['id']),))
                    conn.commit()
                    st.rerun()
        else:
            st.info("আজকে এখনও কোনো বিক্রি এন্ট্রি করা হয়নি।")

    # --- 3. Dues Ledger ---
    elif menu == "📝 কাস্টমার বাকি খাতা (Dues)":
        st.title("📝 কাস্টমার বাকি খাতা (লেজার)")
        col1, col2, col3 = st.columns(3)
        name = col1.text_input("কাস্টমারের নাম")
        phone = col2.text_input("মোবাইল নম্বর")
        due_amt = col3.number_input("বাকির পরিমাণ (৳)", min_value=0.0)
        
        if st.button("বাকি খাতা আপডেট করুন"):
            if name and due_amt > 0:
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO dues (customer_name, phone, amount, status, date) VALUES (?, ?, ?, 'Unpaid', ?)", (name, phone, due_amt, today))
                conn.commit()
                st.success(f"{name} এর নামে ৳{due_amt} বাকি রেকর্ড করা হয়েছে।")
                st.rerun()
                
        st.write("---")
        st.subheader("📋 বর্তমান বাকি তালিকা")
        df_dues = pd.read_sql_query("SELECT id, customer_name AS 'Name', phone AS 'Phone', amount AS 'Due Tk', status AS 'Status' FROM dues WHERE status='Unpaid'", conn)
        
        if not df_dues.empty:
            for index, row in df_dues.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.error(f"🔴 {row['Name']} ({row['Phone']}) -> বাকি: ৳ {row['Due Tk']}")
                if c2.button(f"টাকা আদায় হয়েছে", key=f"pay_due_{row['id']}"):
                    cursor.execute("UPDATE dues SET status='Paid' WHERE id=?", (int(row['id']),))
                    today = datetime.today().strftime('%Y-%m-%d')
                    cursor.execute("INSERT INTO sales (item, amount, date) VALUES ('বাকি আদায়', ?, ?)", (row['Due Tk'], today))
                    conn.commit()
                    st.success("টাকা সফলভাবে আদায় হয়ে ক্যাশে যোগ হয়েছে!")
                    st.rerun()
        else:
            st.info("দোকানে কোনো কাস্টমারের বাকি নেই! চমৎকার।")

    # --- 4. Expenses & Staff ---
    elif menu == "💸 খরচ ও স্টাফ (Expense)":
        st.title("💸 খরচ ও স্টাফ ম্যানেজমেন্ট")
        tab1, tab2 = st.tabs(["দোকান খরচ", "স্টাফ বেতন ও অ্যাডভান্স"])
        
        with tab1:
            options = ["দোকান ভাড়া", "বিদ্যুৎ বিল", "ইন্টারনেট বিল", "চা-নাস্তা", "কাগজ/কালি ক্রয়", "অন্যান্য"]
            cat = st.selectbox("খরচের খাত", options)
            exp_amt = st.number_input("খরচের পরিমাণ (৳)", min_value=0.0, step=10.0)
            if st.button("খরচ সংরক্ষণ করুন"):
                if exp_amt > 0:
                    today = datetime.today().strftime('%Y-%m-%d')
                    cursor.execute("INSERT INTO expenses (category, amount, date) VALUES (?, ?, ?)", (cat, exp_amt, today))
                    conn.commit()
                    st.success(f"{cat} বাবদ ৳{exp_amt} সংরক্ষিত হয়েছে।")
                    st.rerun()
                    
        with tab2:
            s_name = st.text_input("স্টাফ বা কর্মচারীর নাম")
            s_sal = st.number_input("মাসিক ফিক্সড বেতন (৳)", min_value=0.0)
            s_adv = st.number_input("আজকে অ্যাডভান্স নিলে সেই পরিমাণ (৳)", min_value=0.0)
            if st.button("স্টাফ ডাটা আপডেট করুন"):
                if s_name:
                    cursor.execute("SELECT id, advance FROM staff WHERE staff_name=?", (s_name,))
                    exist = cursor.fetchone()
                    if exist:
                        new_adv = exist[1] + s_adv
                        cursor.execute("UPDATE staff SET salary=?, advance=? WHERE staff_name=?", (s_sal, new_adv, s_name))
                    else:
                        cursor.execute("INSERT INTO staff (staff_name, salary, advance) VALUES (?, ?, ?)", (s_name, s_sal, s_adv))
                    if s_adv > 0:
                        today = datetime.today().strftime('%Y-%m-%d')
                        cursor.execute("INSERT INTO expenses (category, amount, date) VALUES ('স্টাফ অ্যাডভান্স', ?, ?)", (s_adv, today))
                    conn.commit()
                    st.success("স্টাফ রেকর্ড আপডেট হয়েছে!")
                    st.rerun()

    # --- 5. Stock Management ---
    elif menu == "📦 কাগজ ও কালি স্টক (Stock)":
        st.title("📦 মালামাল ও ইনভেন্টরি স্টক")
        cursor.execute("SELECT item_name, qty, min_limit FROM stock")
        stocks = cursor.fetchall()
        
        for s in stocks:
            name, qty, limit = s
            if qty <= limit:
                st.error(f"🔴 **{name}** -> বর্তমান স্টক: {qty} টি (স্টক প্রায় শেষ! দ্রুত কিনুন)")
            else:
                st.success(f"🟢 **{name}** -> বর্তমান স্টক: {qty} টি (পর্যাপ্ত আছে)")
                
        st.write("---")
        st.subheader("🔄 স্টক রিফিল বা নতুন মাল যোগ করুন")
        s_item = st.selectbox("কোন মাল যোগ করবেন?", ["A4 Paper Rim", "Printer Toner/Ink"])
        s_qty = st.number_input("নতুন কত পিস/রিম আনলেন?", min_value=1)
        if st.button("স্টক রিফিল করুন"):
            cursor.execute("UPDATE stock SET qty = qty + ? WHERE item_name=?", (s_qty, s_item))
            conn.commit()
            st.success(f"{s_item} এর স্টক সফলভাবে বাড়ানো হয়েছে।")
            st.rerun()

    # --- 6. Loan Manager ---
    elif menu == "🏦 লোন管理器 (Loans)":
        st.title("🏦 এনজিও লোন ও কিস্তি ম্যানেজার")
        col1, col2, col3 = st.columns(3)
        ngo = col1.text_input("এনজিওর নাম (English)")
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

    # --- 7. Cash Closing ---
    elif menu == "🧮 দৈনিক ক্যাশ ক্লোজিং":
        st.title("🧮 দৈনিক ক্যাশ ক্যালকুলেটর ও ক্লোজিং")
        n500 = st.number_input("৫০০ টাকার নোট (পিস)", min_value=0, step=1)
        n100 = st.number_input("১০০ টাকার নোট (পিস)", min_value=0, step=1)
        n50 = st.number_input("৫০ টাকার নোট (পিস)", min_value=0, step=1)
        n20 = st.number_input("২০ টাকার নোট (পিস)", min_value=0, step=1)
        n10 = st.number_input("১০ টাকার নোট (পিস)", min_value=0, step=1)
        
        total_cash = (n500 * 500) + (n100 * 100) + (n50 * 50) + (n20 * 20) + (n10 * 10)
        st.subheader(f"💵 আপনার হাতের নগদ ক্যাশ মোট: ৳ {total_cash}")
        
        today_date = datetime.today().strftime('%Y-%m-%d')
        cursor.execute("SELECT SUM(amount) FROM sales WHERE date=?", (today_date,))
        ts = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses WHERE date=?", (today_date,))
        te = cursor.fetchone()[0] or 0
        expected_cash = ts - te
        
        st.write(f"📊 সফটওয়্যার অনুযায়ী আজকে ক্যাশে থাকার কথা: **৳ {expected_cash}**")
        if total_cash == expected_cash:
            st.success("🟢 চমৎকার! হাতের ক্যাশ এবং সফটওয়্যারের হিসাব একদম মিলে গেছে।")
        elif total_cash > expected_cash:
            st.info(f"📈 ক্যাশে ৳ {total_cash - expected_cash} টাকা বেশি আছে।")
        else:
            st.error(f"🔴 ক্যাশে ৳ {expected_cash - total_cash} টাকা কম আছে! হিসাব চেক করুন।")

    # --- 8. Download & Export (FIXED WITH PDF BUTTON) ---
    elif menu == "💾 ডাউনলোড ও এক্সপোর্ট":
        st.title("💾 মাস্টার রিপোর্ট ডাউনলোড প্যানেল")
        st.write("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 অল-ইন-ওয়ান এক্সেল ফাইল")
            df_sales = pd.read_sql_query("SELECT date, item, amount FROM sales", conn)
            df_exp = pd.read_sql_query("SELECT date, category, amount FROM expenses", conn)
            df_dues = pd.read_sql_query("SELECT customer_name, phone, amount, status FROM dues", conn)
            
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df_sales.to_excel(writer, sheet_name='Sales', index=False)
                df_exp.to_excel(writer, sheet_name='Expenses', index=False)
                df_dues.to_excel(writer, sheet_name='Dues Records', index=False)
            excel_buffer.seek(0)
            
            st.download_button(
                label="🟢 ডাউনলোড মাস্টার এক্সেল (Excel)",
                data=excel_buffer,
                file_name="Brothers_Computer_Ultimate_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        with col2:
            st.subheader("📄 অল-ইন-ওয়ান পিডিএফ ফাইল")
            
            master_pdf = generate_master_pdf(
                pd.read_sql_query("SELECT date, item, amount FROM sales", conn).values.tolist(),
                pd.read_sql_query("SELECT date, category, amount FROM expenses", conn).values.tolist(),
                pd.read_sql_query("SELECT ngo_name, total_loan, paid_loan, date FROM loans", conn).values.tolist()
            )
            
            st.download_button(
                label="🔴 ডাউনলোড মাস্টার পিডিএফ (PDF)",
                data=master_pdf,
                file_name="Brothers_Computer_Master_Report.pdf",
                mime="application/pdf"
            )
