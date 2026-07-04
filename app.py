import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import io

# --- Page Config ---
st.set_page_config(page_title="Brothers Computer Ultimate", page_icon="🖥️", layout="wide")

# --- Database Initialize ---
def init_db():
    conn = sqlite3.connect("online_brothers_data_v3.db", check_same_thread=False)
    cursor = conn.cursor()
    # Core Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS sales (id INTEGER PRIMARY KEY AUTOINCREMENT, item TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS loans (id INTEGER PRIMARY KEY AUTOINCREMENT, ngo_name TEXT, total_loan REAL, paid_loan REAL, date TEXT)''')
    # Premium Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS dues (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, phone TEXT, amount REAL, status TEXT, date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS stock (id INTEGER PRIMARY KEY AUTOINCREMENT, item_name TEXT UNIQUE, qty INTEGER, min_limit INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS staff (id INTEGER PRIMARY KEY AUTOINCREMENT, staff_name TEXT, salary REAL, advance REAL)''')
    
    # Insert Default Stock if Empty safely using INSERT OR IGNORE
    cursor.execute("INSERT OR IGNORE INTO stock (item_name, qty, min_limit) VALUES ('A4 Paper Rim', 10, 2)")
    cursor.execute("INSERT OR IGNORE INTO stock (item_name, qty, min_limit) VALUES ('Printer Toner/Ink', 5, 1)")
    
    conn.commit()
    return conn, cursor

conn, cursor = init_db()

# --- Helper Function: Clean Text for PDF ---
def clean_for_pdf(text):
    mapping = {
        "ফটোকপি": "Photocopy", "প্রিন্ট": "Print", "কম্পোজ": "Compose", 
        "অনлайн কাজ": "Online Work", "NID সার্ভিস": "NID Service", "জন্ম নিবন্ধন": "Birth Reg", 
        "ছবি": "Photo", "ল্যামিনেশন": "Lamination", "অন্যান্য": "Others", "বাকি আদায়": "Due Collected",
        "দোকান ভাড়া": "Shop Rent", "বিদ্যুৎ বিল": "Electricity Bill", 
        "ইন্টারনেট বিল": "Internet Bill", "চা-নাস্তা": "Tea-Snacks", "কাগজ/কালি ক্রয়": "Buy Stock",
        "স্টাফ অ্যাডভান্স": "Staff Advance"
    }
    return mapping.get(str(text), str(text))

# --- Helper Function: Generate Single Receipt PDF ---
def generate_receipt_pdf(rcpt):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(300, 480), rightMargin=15, leftMargin=15, topMargin=15, bottomMargin=15)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('RTitle', parent=styles['Heading2'], fontSize=15, leading=18, alignment=1, textColor=colors.HexColor('#1E3A8A'))
    sub_style = ParagraphStyle('RSub', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=1, textColor=colors.HexColor('#475569'))
    meta_style = ParagraphStyle('RMeta', parent=styles['Normal'], fontSize=8.5, leading=11, alignment=1, textColor=colors.gray)
    text_style = ParagraphStyle('RText', parent=styles['Normal'], fontSize=10, leading=14)
    bold_text = ParagraphStyle('RBold', parent=styles['Normal'], fontSize=10, leading=14, fontName="Helvetica-Bold")
    right_bold = ParagraphStyle('RRightBold', parent=styles['Normal'], fontSize=12, leading=16, fontName="Helvetica-Bold", alignment=2, textColor=colors.HexColor('#1E3A8A'))
    
    story.append(Paragraph("<b>BROTHERS COMPUTER</b>", title_style))
    story.append(Paragraph("Shimantabazar, Kazipur, Sirajganj", sub_style))
    story.append(Paragraph("Mob: 01644-693874, 01880-813373", sub_style))
    story.append(Paragraph("<i>Digital Cash Memo</i>", meta_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"<b>Date:</b> {rcpt['date']}", text_style))
    story.append(Paragraph(f"<b>Customer:</b> {rcpt['name']}", text_style))
    story.append(Spacer(1, 5))
    
    data = [[Paragraph("<b>Description</b>", bold_text), Paragraph("<b>Amount</b>", bold_text)]]
    for i in rcpt['items']:
        data.append([Paragraph(clean_for_pdf(i['item']), text_style), Paragraph(f"Tk {i['amount']}", text_style)])
        
    t = Table(data, colWidths=[180, 90])
    t.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,0), 1, colors.HexColor('#0F172A')),
        ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.lightgrey),
        ('PADDING', (0,0), (-1,-1), 4),
        ('ALIGN', (1,0), (1,-1), 'RIGHT')
    ]))
    story.append(t)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(f"Total Bill: Tk {rcpt['total']}", right_bold))
    story.append(Paragraph("<font color='#10b981'><b>● Paid</b></font>", text_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<i>Thank you, visit again!</i>", meta_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- Helper Function: Generate All-in-One Report PDF ---
def generate_master_pdf(sales_rows, expense_rows, loan_rows, start_d, end_d):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, textColor=colors.HexColor('#1E3A8A'), alignment=1)
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.gray, alignment=1)
    section_style = ParagraphStyle('SectionStyle', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=6)
    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=9, leading=11)
    
    story.append(Paragraph("<b>Brothers Computer Management System</b>", title_style))
    story.append(Paragraph("Shimantabazar, Kazipur, Sirajganj | Mob: 01644-693874", meta_style))
    story.append(Paragraph(f"Report Period: {start_d} to {end_d} | Generated: {datetime.today().strftime('%Y-%m-%d')}", meta_style))
    story.append(Spacer(1, 15))
    
    t_style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#E2E8F0')),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')])
    ])

    story.append(Paragraph("<b>1. Sales Records</b>", section_style))
    sales_data = [[Paragraph("<b>Date</b>", cell_style), Paragraph("<b>Item</b>", cell_style), Paragraph("<b>Amount (Tk)</b>", cell_style)]]
    for row in sales_rows:
        sales_data.append([Paragraph(str(row[0]), cell_style), Paragraph(clean_for_pdf(row[1]), cell_style), Paragraph(str(row[2]), cell_style)])
    t1 = Table(sales_data, colWidths=[doc.width/3]*3)
    t1.setStyle(t_style)
    story.append(t1)
    
    story.append(Paragraph("<b>2. Expense Records</b>", section_style))
    exp_data = [[Paragraph("<b>Date</b>", cell_style), Paragraph("<b>Category</b>", cell_style), Paragraph("<b>Amount (Tk)</b>", cell_style)]]
    for row in expense_rows:
        exp_data.append([Paragraph(str(row[0]), cell_style), Paragraph(clean_for_pdf(row[1]), cell_style), Paragraph(str(row[2]), cell_style)])
    t2 = Table(exp_data, colWidths=[doc.width/3]*3)
    t2.setStyle(t_style)
    story.append(t2)
    
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
    st.sidebar.title("Brothers ERP v3.0")
    st.sidebar.write("---")
    menu = st.sidebar.radio("মেনু সিলেক্ট করুন", [
        "🏠 ড্যাশবোর্ড ও সামগ্রিক সারসংক্ষেপ", 
        "💰 বিক্রি ও রসিদ (Sales)", 
        "📝 কাস্টমার বাকি খাতা (Dues)",
        "💸 খরচ ও স্টাফ (Expense)", 
        "📦 মালামাল ও কালি স্টক (Stock)",
        "🏦 লোন ম্যানেজার (Loans)", 
        "🧮 দৈনিক ক্যাশ ক্লোজিং",
        "💾 ডাউনলোড ও এক্সপোর্ট"
    ])
    
    if st.sidebar.button("লগআউট (Logout)"):
        st.session_state['logged_in'] = False
        st.rerun()

    if 'cart' not in st.session_state:
        st.session_state['cart'] = []
    if 'last_receipt' not in st.session_state:
        st.session_state['last_receipt'] = None

    # --- 1. Dashboard & Global Summary ---
    if menu == "🏠 ড্যাশবোর্ড ও সামগ্রিক সারসংক্ষেপ":
        st.title("🏠 ড্যাশবোর্ড ও সামগ্রিক সারসংক্ষেপ (Business Summary)")
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
        
        # --- NEW GLOBAL SUMMARY OPTION ---
        st.write("---")
        st.subheader("📊 ব্যবসায়ের সামগ্রিক আর্থিক সারসংক্ষেপ (Lifetime Summary)")
        
        cursor.execute("SELECT SUM(amount) FROM sales")
        all_sales = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(amount) FROM expenses")
        all_expenses = cursor.fetchone()[0] or 0
        cursor.execute("SELECT SUM(total_loan) - SUM(paid_loan) FROM loans")
        net_loans = cursor.fetchone()[0] or 0
        cursor.execute("SELECT COUNT(*) FROM stock WHERE qty <= min_limit")
        low_stock_count = cursor.fetchone()[0] or 0
        
        summary_data = {
            "খাত / বিষয়ের বিবরণ (Description)": ["সর্বমোট মোট বিক্রি (Total Sales)", "সর্বমোট দোকান খরচ (Total Expense)", "বাজারের মোট কাস্টমার বাকি (Total Dues)", "এনজিওর নিট লোন দেনা (Net Loan Due)", "রিফিলযোগ্য জরুরি স্টক আইটেম"],
            "বর্তমান অবস্থা / হিসাব (Status Amount)": [f"৳ {all_sales}", f"৳ {all_expenses}", f"৳ {total_dues}", f"৳ {net_loans}", f"{low_stock_count} টি আইটেমে মাল কম আছে"]
        }
        st.table(pd.DataFrame(summary_data))
        
        st.write("---")
        st.subheader("📈 আয়ের খাতসমূহের গ্রাফিক্যাল চার্ট")
        df_chart_sales = pd.read_sql_query("SELECT item AS 'Category', SUM(amount) AS 'Total_Tk' FROM sales GROUP BY item", conn)
        if not df_chart_sales.empty:
            st.bar_chart(df_chart_sales.set_index('Category'))

    # --- 2. Sales & Receipts ---
    elif menu == "💰 বিক্রি ও রসিদ (Sales)":
        st.title("💰 নতুন বিক্রি ও মাল্টিপল আইটেম রসিদ")
        col_form, col_receipt = st.columns([1, 1])
        
        with col_form:
            st.subheader("🛒 কাস্টমারের কাজের তালিকা তৈরি করুন")
            c_name = st.text_input("কাস্টমারের নাম (ঐচ্ছিক)", key="customer_name_input")
            
            options = ["ফটোকপি", "প্রিন্ট", "কম্পোজ", "অনлайн কাজ", "NID সার্ভিস", "জন্ম নিবন্ধন", "ছবি", "ল্যামিনেশন", "অন্যান্য"]
            item = st.selectbox("কাজের ধরন সিলেক্ট করুন", options)
            amount = st.number_input("এই কাজের টাকার পরিমাণ (৳)", min_value=0.0, step=10.0)
            
            if st.button("➕ এই কাজটি তালিকায় যোগ করুন"):
                if amount > 0:
                    st.session_state['cart'].append({"item": item, "amount": amount})
                    st.success(f"✓ {item} (৳ {amount}) তালিকায় যোগ হয়েছে।")
            
            if st.session_state['cart']:
                st.write("---")
                st.write("**এই কাস্টমারের চলতি কাজের তালিকা:**")
                for idx, cart_item in enumerate(st.session_state['cart']):
                    st.write(f"{idx+1}. {cart_item['item']} — ৳ {cart_item['amount']}")
                
                if st.button("❌ Dynamic Clear"):
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
                st.caption("📍 সিমান্তবাজার, কাজিপুর, সিরাজগঞ্জ।")
                st.caption("📞 মোবাইল: ০১৬৪৪-৬৯৩৮৭৪, ০১৮৮০-৮১৩৩৭৩")
                st.write("---")
                st.write(f"**তারিখ:** {rcpt['date']} | **কাস্টমার:** {rcpt['name']}")
                for i in rcpt['items']:
                    st.write(f"• {i['item']} — ৳ {i['amount']}")
                st.write("---")
                st.markdown(f"### **সর্বমোট বিল: ৳ {rcpt['total']}**")
                st.success("● পরিশোধিত (Paid)")
                
                receipt_pdf_data = generate_receipt_pdf(rcpt)
                st.download_button(label="🧾 ডাউনলোড করুন রসিদ (PDF প্রিন্ট)", data=receipt_pdf_data, file_name=f"Receipt_{rcpt['date']}.pdf", mime="application/pdf")
            else:
                st.info("কাজের তালিকা তৈরি করে সেভ করুন।")

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

    # --- 4. Expenses & Staff ---
    elif menu == "💸 খরচ ও স্টাফ (Expense)":
        st.title("💸 খরচ ও স্টাফ ম্যানেজমেন্ট")
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

    # --- 5. Stock Management (UPDATED AND SECURED) ---
    elif menu == "📦 মালামাল ও কালি স্টক (Stock)":
        st.title("📦 মালামাল ও ইনভেন্টরি স্টক প্যানেল")
        
        # Display Current Stock Data Frame Securely
        df_stock_view = pd.read_sql_query("SELECT id, item_name AS 'আইটেমের নাম', qty AS 'বর্তমান স্টক পরিমাণ', min_limit AS 'সর্বনিম্ন এলার্ট লিমিট' FROM stock", conn)
        st.subheader("📋 বর্তমান স্টকের রিয়েল-টাইম অবস্থা:")
        st.dataframe(df_stock_view, use_container_width=True)
        
        st.write("---")
        
        # Form 1: Add a Brand NEW unique item to Database
        col_new1, col_new2, col_new3 = st.columns(3)
        with col_new1:
            new_item_title = st.text_input("🆕 নতুন মালের নাম লিখুন (যেমন: A4 Paper Double-A, Heavy Ink)")
        with col_new2:
            new_item_qty = st.number_value = st.number_input("শুরুর স্টক পরিমাণ (পিস/রিম)", min_value=0, value=10)
        with col_new3:
            new_item_limit = st.number_input("সর্বনিম্ন ওয়ার্নিং লিমিট", min_value=0, value=2)
            
        if st.button("➕ সম্পূর্ণ নতুন আইটেম যুক্ত করুন", type="primary"):
            if new_item_title.strip():
                try:
                    cursor.execute("INSERT INTO stock (item_name, qty, min_limit) VALUES (?, ?, ?)", (new_item_title.strip(), new_item_qty, new_item_limit))
                    conn.commit()
                    st.success(f"✓ '{new_item_title}' সফলভাবে স্টক লিস্টে নতুন আইটেম হিসেবে যুক্ত হয়েছে!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("⚠️ এই নামের আইটেমটি ইতিমধ্যে স্টকে আছে! পরিমাণ বাড়াতে নিচের 'স্টক রিফিল' অপশনটি ব্যবহার করুন।")
            else:
                st.error("দয়া করে মালের একটি সঠিক নাম লিখুন।")

        st.write("---")
        
        # Form 2: Refill/Update quantity of existing items
        st.subheader("🔄 বিদ্যমান মালের স্টক রিফিল বা আপডেট করুন")
        cursor.execute("SELECT item_name FROM stock")
        existing_items = [r[0] for r in cursor.fetchall()]
        
        if existing_items:
            col_ref1, col_ref2 = st.columns(2)
            s_item = col_ref1.selectbox("কোন মালের স্টক বাড়াবেন?", existing_items)
            s_qty = col_ref2.number_input("নতুন কত পিস/রিম যোগ করলেন?", min_value=1, step=1)
            
            if st.button("🚀 স্টক রিফিল নিশ্চিত করুন"):
                cursor.execute("UPDATE stock SET qty = qty + ? WHERE item_name=?", (s_qty, s_item))
                conn.commit()
                st.success(f"✓ {s_item} এর স্টক সফলভাবে {s_qty} টি বাড়ানো হয়েছে।")
                st.rerun()
        else:
            st.info("স্টকে কোনো আইটেম নেই। প্রথমে নতুন আইটেম যোগ করুন।")

    # --- 6. Loan Manager ---
    elif menu == "🏦 লোন ম্যানেজার (Loans)":
        st.title("🏦 এনজিও লোন ও কিস্তি ম্যানেজার")
        col1, col2, col3 = st.columns(3)
        ngo = col1.text_input("এনজিওর নাম (English)")
        total = col2.number_input("মোট ঋণ (৳)", min_value=0.0)
        paid = col3.number_input("পরিশোধিত (৳)", min_value=0.0)
        
        if st.button("লোন যোগ/আপডেট করুন"):
            if ngo:
                today = datetime.today().strftime('%Y-%m-%d')
                cursor.execute("INSERT INTO loans (ngo_name, total_loan, paid_loan, date) VALUES (?, ?, ?, ?)", (ngo, total, paid, today))
                conn.commit()
                st.success(f"{ngo} এর লোন রেকর্ড সংরক্ষণ করা হয়েছে।")
                st.rerun()

    # --- 7. Cash Closing ---
    elif menu == "🧮 দৈনিক ক্যাশ ক্লোজিং":
        st.title("🧮 দৈনিক ক্যাশ ক্যালকুলেটর ও ক্লোজিং")
        n500 = st.number_input("৫০০ টাকার নোট (পিস)", min_value=0, step=1)
        n100 = st.number_input("১০০ টাকার নোট (পিস)", min_value=0, step=1)
        total_cash = (n500 * 500) + (n100 * 100)
        st.subheader(f"💵 আপনার হাতের নগদ ক্যাশ মোট: ৳ {total_cash}")

    # --- 8. Download & Export ---
    elif menu == "💾 ডাউনলোড ও এক্সপোর্ট":
        st.title("💾 ফিল্টারড ক্যাশ রিপোর্ট ডাউনলোড প্যানেল")
        st.subheader("📅 আপনি কতদিনের রিপোর্ট ডাউনলোড করতে চান?")
        filter_option = st.selectbox("সময়সীমা সিলেক্ট করুন", ["আজকের হিসাব", "গত ৩ দিন", "গত ৭ দিন", "গত ৩০ দিন"])
