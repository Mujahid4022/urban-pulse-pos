# membership_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import re
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation, show_info

class MembershipManager:
    def __init__(self, parent, working_date=None):
        self.parent = parent
        self.working_date = working_date or datetime.now().strftime('%Y-%m-%d')
        print(f"Membership Manager using date: {self.working_date}")
        self.window = tk.Toplevel(parent)
        self.window.title("Membership Management")
        self.window.geometry("900x700")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"900x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Bind mouse wheel
        self.window.bind_all("<MouseWheel>", self.on_mousewheel)
        
        self.create_widgets()
        self.load_members()
        self.load_groups()
    
    def on_mousewheel(self, event):
        widget = event.widget
        if isinstance(widget, tk.Canvas):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        elif isinstance(widget, tk.Listbox):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        elif isinstance(widget, tk.Text):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def format_cnic(self, event=None):
        widget = event.widget
        value = widget.get()
        digits = ''.join(filter(str.isdigit, value))
        
        if len(digits) > 13:
            digits = digits[:13]
        
        formatted = ''
        if len(digits) > 5:
            formatted = digits[:5] + '-' + digits[5:]
            if len(digits) > 12:
                formatted = digits[:5] + '-' + digits[5:12] + '-' + digits[12:13]
        else:
            formatted = digits
        
        widget.delete(0, tk.END)
        widget.insert(0, formatted)
    
    def format_phone(self, event=None):
        widget = event.widget
        value = widget.get()
        digits = ''.join(filter(str.isdigit, value))
        
        if len(digits) > 11:
            digits = digits[:11]
        
        if len(digits) > 4:
            formatted = digits[:4] + '-' + digits[4:]
        else:
            formatted = digits
        
        widget.delete(0, tk.END)
        widget.insert(0, formatted)
    
    def create_widgets(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        # Tab 1: Members List
        self.members_tab = tk.Frame(notebook)
        notebook.add(self.members_tab, text="👥 Members")
        self.create_members_tab()
        
        # Tab 2: Add Member
        self.add_tab = tk.Frame(notebook)
        notebook.add(self.add_tab, text="➕ Add Member")
        self.create_add_tab()
        
        # Tab 3: Groups
        self.groups_tab = tk.Frame(notebook)
        notebook.add(self.groups_tab, text="📋 Groups")
        self.create_groups_tab()
        
        # Tab 4: Renew
        self.renew_tab = tk.Frame(notebook)
        notebook.add(self.renew_tab, text="🔄 Renew")
        self.create_renew_tab()
    
    def create_members_tab(self):
        title_frame = tk.Frame(self.members_tab, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="👥 MEMBERS LIST", fg='white', bg='#3498db', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Search frame
        search_frame = tk.Frame(self.members_tab, bg='#ecf0f1', height=60)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="🔍 Search:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=20, y=10)
        tk.Label(search_frame, text="Name/CNIC/Member No:", bg='#ecf0f1', font=('Arial', 9)).place(x=20, y=35)
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_members())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30, font=('Arial', 9), relief='solid', bd=1)
        search_entry.place(x=150, y=32, height=25)
        search_entry.bind('<Return>', lambda e: self.load_members())
        
        tk.Label(search_frame, text="Group:", bg='#ecf0f1', font=('Arial', 9)).place(x=400, y=35)
        self.group_filter_var = tk.StringVar()
        self.group_filter = ttk.Combobox(search_frame, textvariable=self.group_filter_var, width=20, font=('Arial', 9))
        self.group_filter.place(x=450, y=32, height=25)
        self.group_filter.bind('<<ComboboxSelected>>', lambda e: self.load_members())
        
        tk.Button(search_frame, text="🔄 Refresh", command=self.load_members, bg='#3498db', fg='white', 
                 font=('Arial', 9), cursor='hand2').place(x=680, y=28, width=100, height=28)
        
        # Treeview
        tree_frame = tk.Frame(self.members_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('ID', 'Member No', 'Name', 'CNIC', 'Contact', 'Group', 'Join Date', 'Expiry', 'Status')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        col_widths = {'ID': 40, 'Member No': 90, 'Name': 150, 'CNIC': 120, 'Contact': 100, 
                     'Group': 100, 'Join Date': 80, 'Expiry': 80, 'Status': 70}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', lambda e: self.view_member_details())
        
        # Buttons
        btn_frame = tk.Frame(self.members_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)

        # Adjusted positions for 6 buttons
        btn_x = [20, 130, 240, 350, 460, 570]

        tk.Button(btn_frame, text="👁️ View", command=self.view_member_details, bg='#3498db', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=20, y=10)
        tk.Button(btn_frame, text="✏️ Edit", command=self.edit_member, bg='#f39c12', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=115, y=10)
        tk.Button(btn_frame, text="🔄 Renew", command=self.renew_member, bg='#27ae60', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=210, y=10)
        tk.Button(btn_frame, text="❌ Deactivate", command=self.deactivate_member, bg='#e74c3c', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=305, y=10)
        tk.Button(btn_frame, text="🗑️ Delete", command=self.delete_member, bg='#c0392b', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=400, y=10)
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_members, bg='#3498db', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=495, y=10)
        tk.Button(btn_frame, text="📥 PDF", command=self.export_members_pdf, bg='#9b59b6', fg='white',
                 font=('Arial', 10), width=9, cursor='hand2').place(x=590, y=10)

    def export_members_pdf(self):
        """Export all members to PDF file with better formatting"""
        from tkinter import filedialog
        from datetime import datetime
        import sqlite3
        from fpdf import FPDF
    
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            title="Save Members List As"
        )
    
        if not filename:
            return
    
        # Get all members
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        c.execute('''SELECT m.id, m.member_no, m.name, m.cnic, m.contact, 
                            g.group_name, m.join_date, m.expiry_date, m.status
                     FROM members m
                     LEFT JOIN groups g ON m.group_id = g.id
                     ORDER BY m.id''')
    
        members = c.fetchall()
        conn.close()
    
        # Create PDF in landscape for more columns
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
    
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'MEMBERS LIST', 0, 1, 'C')
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        pdf.ln(5)
    
        # Set column widths (landscape A4 = 297mm width)
        col_widths = [15, 20, 55, 45, 35, 40, 25, 25, 20]
        headers = ['ID', 'Mem No', 'Name', 'CNIC', 'Contact', 'Group', 'Join', 'Expiry', 'Status']
    
        # Headers with background
        pdf.set_font('Arial', 'B', 9)
        pdf.set_fill_color(200, 200, 200)  # Light gray background
    
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
        pdf.ln()
    
        # Data rows
        pdf.set_font('Arial', '', 8)
        fill = False
    
        for m in members:
            # Check if new page needed
            if pdf.get_y() > 190:
                pdf.add_page()
                # Re-print headers
                pdf.set_font('Arial', 'B', 9)
                pdf.set_fill_color(200, 200, 200)
                for i, header in enumerate(headers):
                    pdf.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
                pdf.ln()
                pdf.set_font('Arial', '', 8)
        
            # Format data
            name = m[2] if len(m[2]) <= 25 else m[2][:23] + '..'
            cnic = m[3] if m[3] else ''
            contact = m[4] if m[4] else ''
            group = m[5] if m[5] else ''
            join_date = m[6][:10] if m[6] else ''
            expiry_date = m[7][:10] if m[7] else ''
            status = m[8] if m[8] else ''
        
            # Alternate row colors for better readability
            if fill:
                pdf.set_fill_color(240, 240, 240)
            else:
                pdf.set_fill_color(255, 255, 255)
        
            pdf.cell(col_widths[0], 7, str(m[0]), 1, 0, 'C', 1)
            pdf.cell(col_widths[1], 7, m[1], 1, 0, 'L', 1)
            pdf.cell(col_widths[2], 7, name, 1, 0, 'L', 1)
            pdf.cell(col_widths[3], 7, cnic, 1, 0, 'L', 1)
            pdf.cell(col_widths[4], 7, contact, 1, 0, 'L', 1)
            pdf.cell(col_widths[5], 7, group, 1, 0, 'L', 1)
            pdf.cell(col_widths[6], 7, join_date, 1, 0, 'C', 1)
            pdf.cell(col_widths[7], 7, expiry_date, 1, 0, 'C', 1)
            pdf.cell(col_widths[8], 7, status, 1, 0, 'C', 1)
            pdf.ln()
            fill = not fill
    
        # Summary
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, f'Total Members: {len(members)}', 0, 1, 'L')
    
        # Save PDF
        pdf.output(filename)
        show_success(f"PDF saved successfully!\nTotal members: {len(members)}")
        
    def create_add_tab(self):
        title_frame = tk.Frame(self.add_tab, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="➕ ADD NEW MEMBER", fg='white', bg='#27ae60', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        # Date display
        date_frame = tk.Frame(self.add_tab, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X, padx=10, pady=(5,0))
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 9, 'bold')).pack(expand=True)
        
        # Form frame
        form_frame = tk.Frame(self.add_tab, bg='#f9f9f9', padx=30, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(form_frame, bg='#f9f9f9', highlightthickness=0)
        scrollbar = tk.Scrollbar(form_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg='#f9f9f9')
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        row = 0
        padx_val = 10
        pady_val = 8
        
        # Member info
        tk.Label(scrollable, text="MEMBER INFORMATION", font=('Arial', 12, 'bold'), bg='#f9f9f9').grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        fields = [
            ("Name *:", "member_name"),
            ("CNIC *:", "member_cnic"),
            ("Husband/Father:", "husband_name"),
            ("Husband CNIC:", "husband_cnic"),
            ("Address:", "address"),
            ("Contact *:", "contact"),
            ("Group *:", "group"),
        ]
        
        self.member_name = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.member_cnic = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.husband_name = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.husband_cnic = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.address = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.contact = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.group_var = tk.StringVar()
        self.group_combo = ttk.Combobox(scrollable, textvariable=self.group_var, width=32, font=('Arial', 10))
        
        entries = [self.member_name, self.member_cnic, self.husband_name, self.husband_cnic,
                  self.address, self.contact, self.group_combo]
        
        for i, (label, field) in enumerate(fields):
            tk.Label(scrollable, text=label, font=('Arial', 10), bg='#f9f9f9').grid(row=row, column=0, padx=padx_val, pady=pady_val, sticky='e')
            entries[i].grid(row=row, column=1, padx=padx_val, pady=pady_val, sticky='w')
            row += 1
        
        self.member_cnic.bind('<KeyRelease>', self.format_cnic)
        self.husband_cnic.bind('<KeyRelease>', self.format_cnic)
        self.contact.bind('<KeyRelease>', self.format_phone)
        
        # Guarantor info
        tk.Label(scrollable, text="GUARANTOR INFORMATION", font=('Arial', 12, 'bold'), bg='#f9f9f9').grid(row=row, column=0, columnspan=2, pady=10)
        row += 1
        
        fields2 = [
            ("Name:", "guarantor_name"),
            ("CNIC:", "guarantor_cnic"),
            ("Contact:", "guarantor_contact"),
        ]
        
        self.guarantor_name = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.guarantor_cnic = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.guarantor_contact = tk.Entry(scrollable, width=35, font=('Arial', 10), relief='solid', bd=1)
        
        entries2 = [self.guarantor_name, self.guarantor_cnic, self.guarantor_contact]
        
        for i, (label, field) in enumerate(fields2):
            tk.Label(scrollable, text=label, font=('Arial', 10), bg='#f9f9f9').grid(row=row, column=0, padx=padx_val, pady=pady_val, sticky='e')
            entries2[i].grid(row=row, column=1, padx=padx_val, pady=pady_val, sticky='w')
            row += 1
        
        self.guarantor_cnic.bind('<KeyRelease>', self.format_cnic)
        self.guarantor_contact.bind('<KeyRelease>', self.format_phone)
        
        # Fee
        tk.Label(scrollable, text="Membership Fee (Rs.):", font=('Arial', 10), bg='#f9f9f9').grid(row=row, column=0, padx=padx_val, pady=pady_val, sticky='e')
        self.membership_fee = tk.Entry(scrollable, width=20, font=('Arial', 10), relief='solid', bd=1)
        self.membership_fee.insert(0, "400")
        self.membership_fee.grid(row=row, column=1, padx=padx_val, pady=pady_val, sticky='w')
        row += 1
        
        tk.Label(scrollable, text="* Required fields", fg='red', font=('Arial', 9), bg='#f9f9f9').grid(row=row, column=0, columnspan=2, pady=10)
        
        # Enter navigation
        all_entries = entries + entries2 + [self.membership_fee]
        for i in range(len(all_entries)-1):
            setup_enter_navigation(all_entries[i], all_entries[i+1])
        setup_enter_navigation(all_entries[-1], self.save_member)
        
        # After all fields, add buttons in the scrollable frame
        row += 1
        btn_frame = tk.Frame(scrollable, bg='#f9f9f9')
        btn_frame.grid(row=row, column=0, columnspan=2, pady=10)
        
        # Center the buttons
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        tk.Button(btn_frame, text="💾 Save", command=self.save_member, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=12, cursor='hand2').grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", command=self.clear_form, bg='#95a5a6', fg='white',
                 font=('Arial', 11), width=12, cursor='hand2').grid(row=0, column=2, padx=5)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)    
    
    def create_member_account(self, member_id, member_name):
        """Create a chart of account for the member under Accounts Receivable"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        try:
            # Get the parent account ID for Accounts Receivable (code 1200)
            c.execute("SELECT id FROM accounts WHERE account_code='1200' OR account_name='Accounts Receivable'")
            parent = c.fetchone()
        
            if not parent:
                # Create Accounts Receivable parent if it doesn't exist
                c.execute('''INSERT INTO accounts 
                            (account_code, account_name, account_type, is_active, created_date)
                            VALUES (?, ?, 'Asset', 1, ?)''',
                          ('1200', 'Accounts Receivable', self.working_date))
                parent_id = c.lastrowid
                print(f"✅ Created Accounts Receivable parent account")
            else:
                parent_id = parent[0]
        
            # Get the next available account code under Accounts Receivable
            c.execute("SELECT account_code FROM accounts WHERE account_code LIKE '1-%' ORDER BY account_code DESC LIMIT 1")
            last = c.fetchone()
        
            if last:
                last_num = int(last[0].split('-')[1])
                new_code = f"1-{last_num + 1:04d}"
            else:
                new_code = "1-1201"
        
            # Create the member's account
            c.execute('''INSERT INTO accounts 
                        (account_code, account_name, account_type, parent_id, is_active, created_date)
                        VALUES (?, ?, 'Asset', ?, 1, ?)''',
                      (new_code, member_name, parent_id, self.working_date))
        
            account_id = c.lastrowid
        
            # Update member record with account_id
            c.execute("UPDATE members SET account_id = ? WHERE id = ?", (account_id, member_id))
        
            conn.commit()
            print(f"✅ Created account for member {member_name}: {new_code}")
        
        except Exception as e:
            print(f"❌ Error creating account for member: {e}")
            conn.rollback()
        finally:
            conn.close()
    def record_membership_fee(self, member_id, member_name, fee, member_no):
        """Record membership fee as income (Debit Cash, Credit Other Income)"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
        
            # Generate voucher number
            voucher_no = f"RCP-{datetime.now().strftime('%Y%m%d')}-{member_id}"
        
            # Create receipt voucher
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, created_by, created_at)
                        VALUES (?, 'Receipt', ?, ?, ?, 'admin', datetime('now'))''',
                      (voucher_no, self.working_date, f"Membership fee from {member_name}", fee))
        
            voucher_id = c.lastrowid
        
            # Find Cash account (1000)
            c.execute("SELECT id FROM accounts WHERE account_code='1000' OR account_name='Cash in Hand'")
            cash = c.fetchone()
        
            # Find Other Income account (4100)
            c.execute("SELECT id FROM accounts WHERE account_code='4100' OR account_name='Other Income'")
            income = c.fetchone()
        
            if cash and income:
                # Debit Cash
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, narration, entry_date)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (voucher_id, cash[0], fee, 0, f"Membership fee {member_name}", self.working_date))
            
                # Credit Other Income
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, narration, entry_date)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (voucher_id, income[0], 0, fee, f"Membership fee {member_name}", self.working_date))
            
                # Update account balances
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id = ?", (fee, cash[0]))
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id = ?", (fee, income[0]))
            
                conn.commit()
                print(f"✅ Membership fee Rs.{fee} recorded for {member_name}")
            else:
                print("⚠️ Cash or Income account not found")
        
            conn.close()
        except Exception as e:
            print(f"⚠️ Error recording fee: {e}")
    
    def create_groups_tab(self):
        title_frame = tk.Frame(self.groups_tab, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📋 GROUPS", fg='white', bg='#f39c12', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Treeview
        tree_frame = tk.Frame(self.groups_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('ID', 'Group Name', 'Area', 'City', 'Members', 'Created')
        self.groups_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=vsb.set, height=12)
        vsb.config(command=self.groups_tree.yview)
        
        col_widths = {'ID': 40, 'Group Name': 150, 'Area': 150, 'City': 100, 'Members': 70, 'Created': 100}
        
        for col in columns:
            self.groups_tree.heading(col, text=col)
            self.groups_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.groups_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(self.groups_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 170, 320, 470]
        
        tk.Button(btn_frame, text="➕ Add", command=self.add_group, bg='#27ae60', fg='white',
                 font=('Arial', 10), width=12, cursor='hand2').place(x=btn_x[0], y=10)
        tk.Button(btn_frame, text="✏️ Edit", command=self.edit_group, bg='#f39c12', fg='white',
                 font=('Arial', 10), width=12, cursor='hand2').place(x=btn_x[1], y=10)
        tk.Button(btn_frame, text="❌ Delete", command=self.delete_group, bg='#e74c3c', fg='white',
                 font=('Arial', 10), width=12, cursor='hand2').place(x=btn_x[2], y=10)
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_groups_tree, bg='#3498db', fg='white',
                 font=('Arial', 10), width=12, cursor='hand2').place(x=btn_x[3], y=10)
        
        self.load_groups_tree()
    
    def create_renew_tab(self):
        title_frame = tk.Frame(self.renew_tab, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="🔄 RENEW MEMBERSHIP", fg='white', bg='#27ae60', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        main_frame = tk.Frame(self.renew_tab, bg='#f9f9f9', padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Search
        search_frame = tk.Frame(main_frame, bg='#ecf0f1', height=60, relief='groove', bd=1)
        search_frame.pack(fill=tk.X, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="Search Member:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=20, y=10)
        tk.Label(search_frame, text="Name/CNIC/Member No:", bg='#ecf0f1', font=('Arial', 9)).place(x=20, y=35)
        
        self.renew_search_var = tk.StringVar()
        self.renew_search_var.trace('w', lambda *args: self.load_renew_search())
        search_entry = tk.Entry(search_frame, textvariable=self.renew_search_var, width=35, font=('Arial', 9), relief='solid', bd=1)
        search_entry.place(x=150, y=32, height=25)
        search_entry.bind('<Return>', lambda e: self.load_renew_search())
        
        # Listbox
        list_frame = tk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(list_frame, text="Select Member:", font=('Arial', 11, 'bold')).pack(anchor='w')
        
        listbox_frame = tk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.renew_listbox = tk.Listbox(listbox_frame, height=8, font=('Arial', 10), relief='solid', bd=1)
        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical", command=self.renew_listbox.yview)
        self.renew_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.renew_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.renew_listbox.bind('<<ListboxSelect>>', self.on_renew_select)
        
        # Details
        details_frame = tk.LabelFrame(main_frame, text="Member Details", font=('Arial', 11, 'bold'), padx=10, pady=10)
        details_frame.pack(fill=tk.X, pady=10)
        
        self.renew_details = tk.Text(details_frame, height=4, width=60, font=('Courier', 10), relief='solid', bd=1)
        self.renew_details.pack()
        
        # Renew options
        options_frame = tk.Frame(main_frame, bg='#ecf0f1', height=60, relief='groove', bd=1)
        options_frame.pack(fill=tk.X, pady=10)
        options_frame.pack_propagate(False)
        
        tk.Label(options_frame, text="Period:", bg='#ecf0f1', font=('Arial', 10)).place(x=20, y=20)
        self.renew_period = ttk.Combobox(options_frame, values=['12 Months', '24 Months', '36 Months'], width=12, font=('Arial', 10))
        self.renew_period.set('12 Months')
        self.renew_period.place(x=80, y=18, height=25)
        
        tk.Label(options_frame, text="Fee (Rs.):", bg='#ecf0f1', font=('Arial', 10)).place(x=220, y=20)
        self.renew_fee = tk.Entry(options_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.renew_fee.insert(0, "400")
        self.renew_fee.place(x=290, y=18, height=25)
        
        tk.Button(options_frame, text="Process Renewal", command=self.process_renewal, bg='#27ae60', fg='white',
                 font=('Arial', 10, 'bold'), cursor='hand2').place(x=420, y=15, width=150, height=30)
    
    def load_groups(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, group_name FROM groups ORDER BY group_name")
        groups = c.fetchall()
        conn.close()
        
        self.groups = groups
        group_names = [g[1] for g in groups]
        self.group_combo['values'] = group_names
        
        # Also load for filter
        filter_values = ['All Groups'] + group_names
        self.group_filter['values'] = filter_values
        self.group_filter.set('All Groups')
    
    def load_members(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        group_filter = self.group_filter_var.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT m.id, m.member_no, m.name, m.cnic, m.contact, g.group_name, 
                          m.join_date, m.expiry_date, m.status
                   FROM members m
                   LEFT JOIN groups g ON m.group_id = g.id
                   WHERE 1=1'''
        params = []
        
        if search:
            query += " AND (m.name LIKE ? OR m.member_no LIKE ? OR m.cnic LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if group_filter and group_filter != 'All Groups':
            query += " AND g.group_name = ?"
            params.append(group_filter)
        
        query += " ORDER BY m.id DESC"
        
        c.execute(query, params)
        members = c.fetchall()
        conn.close()
        
        for m in members:
            status = m[8]
            if m[7]:
                try:
                    expiry = datetime.strptime(m[7], '%Y-%m-%d')
                    if expiry < datetime.now() and m[8] == 'Active':
                        status = "Expired"
                except:
                    pass
            self.tree.insert('', tk.END, values=(m[0], m[1], m[2], m[3], m[4], m[5] or '', m[6], m[7], status))
    
    def load_groups_tree(self):
        for row in self.groups_tree.get_children():
            self.groups_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT g.id, g.group_name, g.area, g.city, COUNT(m.id), g.created_date
                     FROM groups g
                     LEFT JOIN members m ON g.id = m.group_id
                     GROUP BY g.id''')
        groups = c.fetchall()
        conn.close()
        
        for g in groups:
            self.groups_tree.insert('', tk.END, values=g)
    
    def load_renew_search(self):
        self.renew_listbox.delete(0, tk.END)
        search = self.renew_search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT id, member_no, name, cnic FROM members WHERE status='Active' '''
        params = []
        
        if search:
            query += " AND (name LIKE ? OR member_no LIKE ? OR cnic LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY name LIMIT 20"
        
        c.execute(query, params)
        members = c.fetchall()
        conn.close()
        
        self.renew_members = members
        for m in members:
            self.renew_listbox.insert(tk.END, f"{m[2]} | {m[1]} | {m[3]}")
    
    def on_renew_select(self, event):
        sel = self.renew_listbox.curselection()
        if not sel:
            return
        member = self.renew_members[sel[0]]
        self.load_member_details(member[0])
    
    def load_member_details(self, member_id):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT m.name, m.member_no, m.cnic, g.group_name, m.join_date, m.expiry_date, m.status
                     FROM members m
                     LEFT JOIN groups g ON m.group_id = g.id
                     WHERE m.id=?''', (member_id,))
        m = c.fetchone()
        conn.close()
        
        if m:
            details = f"Name: {m[0]}\nMember No: {m[1]}\nCNIC: {m[2]}\nGroup: {m[3] or 'N/A'}\nJoin: {m[4]}\nExpiry: {m[5]}\nStatus: {m[6]}"
            self.renew_details.delete('1.0', tk.END)
            self.renew_details.insert('1.0', details)
            self.selected_renew_id = member_id
    
    def save_member(self):
        name = self.member_name.get().strip()
        cnic = self.member_cnic.get().strip()
        contact = self.contact.get().strip()
        group_name = self.group_var.get()
        
        if not name or not cnic or not contact or not group_name:
            show_error("Name, CNIC, Contact, and Group are required")
            return
        
        # Find group ID
        group_id = None
        for gid, gname in self.groups:
            if gname == group_name:
                group_id = gid
                break
        
        if not group_id:
            show_error("Please select a valid group")
            return
        
        try:
            fee = float(self.membership_fee.get() or 400)
        except:
            fee = 400
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Check duplicate CNIC
        c.execute("SELECT id FROM members WHERE cnic=?", (cnic,))
        if c.fetchone():
            show_error("CNIC already exists!")
            conn.close()
            return
        
        # Generate member number
        c.execute("SELECT COUNT(*) FROM members")
        count = c.fetchone()[0] + 1
        member_no = f"M{count:04d}"
        
        # DEBUG - print the working date
        print(f"SAVING MEMBER - Working date: {self.working_date}")

        # Use working date for join date
        join_date = self.working_date

        # Calculate expiry based on working date
        join_date_obj = datetime.strptime(self.working_date, '%Y-%m-%d')
        expiry = (join_date_obj + timedelta(days=365)).strftime('%Y-%m-%d')
        
        try:
            # Insert member
            c.execute('''INSERT INTO members 
                        (member_no, name, cnic, husband_name, husband_cnic, address, contact, 
                         group_id, membership_fee, join_date, expiry_date, status,
                         guarantor_name, guarantor_cnic, guarantor_contact)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                      (member_no, name, cnic, self.husband_name.get(), self.husband_cnic.get(),
                       self.address.get(), contact, group_id, fee, join_date, expiry, 'Active',
                       self.guarantor_name.get(), self.guarantor_cnic.get(), self.guarantor_contact.get()))
            
            member_id = c.lastrowid
            conn.commit()
            
            # Create chart of account for this member
            self.create_member_account(member_id, name)
            
            show_success(f"Member {name} added! Member No: {member_no}\nAccount created under Accounts Receivable")
            self.clear_form()
            self.load_members()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error: {e}")
        finally:
            conn.close()
    
    def clear_form(self):
        self.member_name.delete(0, tk.END)
        self.member_cnic.delete(0, tk.END)
        self.husband_name.delete(0, tk.END)
        self.husband_cnic.delete(0, tk.END)
        self.address.delete(0, tk.END)
        self.contact.delete(0, tk.END)
        self.group_var.set('')
        self.guarantor_name.delete(0, tk.END)
        self.guarantor_cnic.delete(0, tk.END)
        self.guarantor_contact.delete(0, tk.END)
        self.membership_fee.delete(0, tk.END)
        self.membership_fee.insert(0, "400")
    
    def view_member_details(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member")
            return
    
        member_id = self.tree.item(sel[0])['values'][0]
    
        # Open database
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        # Get member data with joins
        c.execute('''SELECT m.*, g.group_name, a.account_code, a.account_name 
                     FROM members m
                     LEFT JOIN groups g ON m.group_id = g.id
                     LEFT JOIN accounts a ON m.account_id = a.id
                     WHERE m.id=?''', (member_id,))
        m = c.fetchone()
        conn.close()
    
        if not m:
            return
    
        # Map fields by their correct positions
        member_data = {
            # Member Info (indexes based on database structure)
            'member_no': m[1],
            'name': m[2],
            'cnic': m[3],
            'husband_name': m[4] or 'N/A',
            'husband_cnic': m[5] or 'N/A',
        
            # Contact
            'address': m[6] or 'N/A',
            'contact': m[7] or 'N/A',
            'group_name': m[17] if len(m) > 17 else 'N/A',  # From join
        
            # Accounting
            'account_code': m[16] if len(m) > 16 else 'N/A',
            'account_name': m[18] if len(m) > 18 else 'N/A',
        
            # Membership
            'join_date': m[10] or 'N/A',
            'expiry_date': m[11] or 'N/A',
            'status': m[12] or 'N/A',
            'fee': float(m[9] or 0),
        
            # Guarantor
            'guarantor_name': m[13] or 'N/A',
            'guarantor_cnic': m[14] or 'N/A',
            'guarantor_contact': m[15] or 'N/A'
        }
    
        # Create window
        win = tk.Toplevel(self.window)
        win.title("Member Details")
        win.geometry("500x750")
        win.configure(bg='#f9f9f9')
    
        # Center window
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 500) // 2
        y = (win.winfo_screenheight() - 750) // 2
        win.geometry(f"500x750+{x}+{y}")
    
        # Create text widget
        text = tk.Text(win, font=('Courier', 10), bg='white', padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
        # Display EXACTLY as you requested
        details = f"""
    {'='*50}
    MEMBER DETAILS
    {'='*50}

    Member No: {member_data['member_no']}
    Name: {member_data['name']}
    CNIC: {member_data['cnic']}
    Husband: {member_data['husband_name']}
    Husband CNIC: {member_data['husband_cnic']}

    CONTACT:
    Address: {member_data['address']}
    Phone: {member_data['contact']}
    Group: {member_data['group_name']}

    ACCOUNTING:
    Account Code: {member_data['account_code']}
    Account Name: {member_data['account_name']}

    MEMBERSHIP:
    Join Date: {member_data['join_date']}
    Expiry: {member_data['expiry_date']}
    Status: {member_data['status']}
    Fee: {CURRENCY_SYMBOL}{member_data['fee']:.2f}

    GUARANTOR:
    Name: {member_data['guarantor_name']}
    CNIC: {member_data['guarantor_cnic']}
    Contact: {member_data['guarantor_contact']}

    {'='*50}
    """
        text.insert('1.0', details)
        text.config(state='disabled')
    
        # Close button
        tk.Button(win, text="Close", command=win.destroy, bg='#3498db', fg='white',
                 font=('Arial', 10), cursor='hand2').pack(pady=5)
    
    def edit_member(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member to edit")
            return
        
        member_id = self.tree.item(sel[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get full member data
        c.execute('''SELECT m.*, g.group_name 
                     FROM members m
                     LEFT JOIN groups g ON m.group_id = g.id
                     WHERE m.id=?''', (member_id,))
        m = c.fetchone()
        
        # Get column names
        c.execute("PRAGMA table_info(members)")
        columns = [col[1] for col in c.fetchall()]
        conn.close()
        
        if not m:
            return
        
        # Create dictionary for easy access
        member_dict = {}
        for i, col in enumerate(columns):
            member_dict[col] = m[i] if i < len(m) else None
        
        # Add group_name from join
        member_dict['group_name'] = m[len(columns)] if len(m) > len(columns) else ''
        
        # Create edit dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Member")
        dialog.geometry("400x600")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 600) // 2
        dialog.geometry(f"400x600+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="EDIT MEMBER", font=('Arial', 14, 'bold'), bg='#f39c12', fg='white').pack(fill=tk.X, pady=5)
        
        # Form
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Fields with correct mapping
        fields = [
            ("Name:", tk.StringVar(value=member_dict.get('name', ''))),
            ("CNIC:", tk.StringVar(value=member_dict.get('cnic', ''))),
            ("Husband:", tk.StringVar(value=member_dict.get('husband_name', ''))),
            ("Husband CNIC:", tk.StringVar(value=member_dict.get('husband_cnic', ''))),
            ("Address:", tk.StringVar(value=member_dict.get('address', ''))),
            ("Contact:", tk.StringVar(value=member_dict.get('contact', ''))),
            ("Fee (Rs.):", tk.StringVar(value=str(member_dict.get('membership_fee', 0)))),
        ]
        
        entries = []
        row = 0
        for label, var in fields:
            tk.Label(frame, text=label, bg='#f9f9f9', font=('Arial', 10)).grid(row=row, column=0, padx=2, pady=2, sticky='e')
            e = tk.Entry(frame, textvariable=var, width=30, font=('Arial', 10), relief='solid', bd=1)
            e.grid(row=row, column=1, padx=5, pady=2, sticky='w')
            entries.append(e)
            row += 1
        
        # Group dropdown
        tk.Label(frame, text="Group:", bg='#f9f9f9', font=('Arial', 10)).grid(row=row, column=0, padx=2, pady=2, sticky='e')
        group_var = tk.StringVar()
        
        # Find group name from group_id
        group_id = member_dict.get('group_id')
        group_name = ''
        for gid, gname in self.groups:
            if gid == group_id:
                group_name = gname
                break
        
        group_var.set(group_name)
        group_combo = ttk.Combobox(frame, textvariable=group_var, values=[g[1] for g in self.groups], width=27, font=('Arial', 10))
        group_combo.grid(row=row, column=1, padx=2, pady=2, sticky='w')
        entries.append(group_combo)
        
        # Guarantor
        row += 1
        tk.Label(frame, text="Guarantor:", bg='#f9f9f9', font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=2, pady=5)
        row += 1
        
        fields2 = [
            ("Name:", tk.StringVar(value=member_dict.get('guarantor_name', ''))),
            ("CNIC:", tk.StringVar(value=member_dict.get('guarantor_cnic', ''))),
            ("Contact:", tk.StringVar(value=member_dict.get('guarantor_contact', ''))),
        ]
        
        for label, var in fields2:
            tk.Label(frame, text=label, bg='#f9f9f9', font=('Arial', 10)).grid(row=row, column=0, padx=2, pady=2, sticky='e')
            e = tk.Entry(frame, textvariable=var, width=30, font=('Arial', 10), relief='solid', bd=1)
            e.grid(row=row, column=1, padx=2, pady=2, sticky='w')
            entries.append(e)
            row += 1
        
        def save_changes():
            # Find group ID from selected group name
            group_id = None
            for gid, gname in self.groups:
                if gname == group_var.get():
                    group_id = gid
                    break
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            try:
                c.execute('''UPDATE members SET 
                            name=?, cnic=?, husband_name=?, husband_cnic=?, address=?,
                            contact=?, group_id=?, membership_fee=?, guarantor_name=?,
                            guarantor_cnic=?, guarantor_contact=?
                            WHERE id=?''',
                          (fields[0][1].get(), fields[1][1].get(), fields[2][1].get(),
                           fields[3][1].get(), fields[4][1].get(), fields[5][1].get(),
                           group_id, float(fields[6][1].get() or 400),
                           fields2[0][1].get(), fields2[1][1].get(), fields2[2][1].get(),
                           member_id))
                conn.commit()
                
                # Also update the account name if member name changed
                if member_dict.get('account_id'):
                    c.execute("UPDATE accounts SET account_name=? WHERE id=?", 
                             (fields[0][1].get(), member_dict['account_id']))
                    conn.commit()
                
                show_success("Member updated!")
                dialog.destroy()
                self.load_members()
            except Exception as e:
                show_error(f"Error: {e}")
            finally:
                conn.close()
        
        # Enter navigation
        for i in range(len(entries)-1):
            setup_enter_navigation(entries[i], entries[i+1])
        setup_enter_navigation(entries[-1], save_changes)
        
        # Buttons
        row += 1
        btn_frame = tk.Frame(frame, bg='#f9f9f9')
        btn_frame.grid(row=row, column=0, columnspan=2, pady=5)
        
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        tk.Button(btn_frame, text="Save", command=save_changes, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=10, cursor='hand2').grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 11), width=10, cursor='hand2').grid(row=0, column=2, padx=5)
    
    def renew_member(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member")
            return
        
        member_id = self.tree.item(sel[0])['values'][0]
        member_name = self.tree.item(sel[0])['values'][2]
        
        # Switch to renew tab
        self.renew_search_var.set(member_name)
        self.load_renew_search()
        
        for i, m in enumerate(self.renew_members):
            if m[0] == member_id:
                self.renew_listbox.selection_set(i)
                self.load_member_details(member_id)
                break
        
        notebook = self.window.children['!notebook']
        notebook.select(3)
    
    def deactivate_member(self):
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member")
            return
        
        member_id = self.tree.item(sel[0])['values'][0]
        member_name = self.tree.item(sel[0])['values'][2]
        
        if ask_yes_no(f"Deactivate {member_name}?"):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("UPDATE members SET status='Inactive' WHERE id=?", (member_id,))
            
            # Also deactivate the account
            c.execute("SELECT account_id FROM members WHERE id=?", (member_id,))
            account_id = c.fetchone()
            if account_id and account_id[0]:
                c.execute("UPDATE accounts SET is_active=0 WHERE id=?", (account_id[0],))
            
            conn.commit()
            conn.close()
            show_success("Member deactivated")
            self.load_members()

    def delete_member(self):
        """Permanently delete a member from the database"""
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member to delete")
            return
    
        # Get member details
        values = self.tree.item(sel[0])['values']
        member_id = values[0]
        member_name = values[2]
        member_no = values[1]
    
        # Check if member has any transactions/credit
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        # Check for ledger entries
        c.execute("SELECT COUNT(*) FROM ledger_entries WHERE voucher_id IN (SELECT id FROM vouchers WHERE member_id=?)", (member_id,))
        ledger_count = c.fetchone()[0]
    
        # Check for vouchers
        c.execute("SELECT COUNT(*) FROM vouchers WHERE member_id=?", (member_id,))
        voucher_count = c.fetchone()[0]
    
        conn.close()
    
        if ledger_count > 0 or voucher_count > 0:
            show_error(f"Cannot delete {member_name}. They have financial transactions.\nUse Deactivate instead.")
            return
    
        # Strong confirmation
        if not ask_yes_no(f"⚠️ PERMANENT DELETE\n\nDelete member {member_name} (ID: {member_no})?\n\nThis action CANNOT be undone!"):
            return
    
        # Double confirmation
        if not ask_yes_no(f"ARE YOU ABSOLUTELY SURE?\n\nThis will permanently remove {member_name} from the database."):
            return
    
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        try:
            # Disable foreign keys temporarily
            c.execute("PRAGMA foreign_keys = OFF")
        
            # Get account_id before deleting member
            c.execute("SELECT account_id FROM members WHERE id=?", (member_id,))
            account_id = c.fetchone()
        
            # Delete the member
            c.execute("DELETE FROM members WHERE id=?", (member_id,))
        
            # Also delete their account
            if account_id and account_id[0]:
                c.execute("DELETE FROM accounts WHERE id=?", (account_id[0],))
        
            # Re-enable foreign keys
            c.execute("PRAGMA foreign_keys = ON")
        
            conn.commit()
            show_success(f"Member {member_name} permanently deleted")
            self.load_members()
        
        except Exception as e:
            conn.rollback()
            show_error(f"Error deleting member: {e}")
        finally:
            conn.close()

    def process_renewal(self):
        if not hasattr(self, 'selected_renew_id'):
            show_error("Select a member")
            return
        
        try:
            period = int(self.renew_period.get().split()[0])
            fee = float(self.renew_fee.get())
        except:
            show_error("Invalid period/fee")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute("SELECT expiry_date FROM members WHERE id=?", (self.selected_renew_id,))
        current = c.fetchone()[0]
        
        if current:
            try:
                current_date = datetime.strptime(current, '%Y-%m-%d')
                new_expiry = current_date + timedelta(days=30*period)
            except:
                # If current date is invalid, use working date
                base_date = datetime.strptime(self.working_date, '%Y-%m-%d')
                new_expiry = base_date + timedelta(days=30*period)
        else:
            # No current expiry, use working date
            base_date = datetime.strptime(self.working_date, '%Y-%m-%d')
            new_expiry = base_date + timedelta(days=30*period)
        
        new_expiry_str = new_expiry.strftime('%Y-%m-%d')
        c.execute("UPDATE members SET expiry_date=?, status='Active' WHERE id=?", (new_expiry_str, self.selected_renew_id))
        conn.commit()
        conn.close()
        
        show_success(f"Renewed until {new_expiry_str}")
        self.load_members()
        self.renew_details.delete('1.0', tk.END)
        self.renew_search_var.set('')
        self.load_renew_search()
    
    def add_group(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Add Group")
        dialog.geometry("400x250")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 250) // 2
        dialog.geometry(f"400x250+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="ADD GROUP", font=('Arial', 14, 'bold'), bg='#27ae60', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Group Name:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w')
        name = tk.Entry(frame, width=30, font=('Arial', 10), relief='solid', bd=1)
        name.pack(pady=2)
        name.focus()
        
        tk.Label(frame, text="Area:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w', pady=(5,0))
        area = tk.Entry(frame, width=30, font=('Arial', 10), relief='solid', bd=1)
        area.pack(pady=2)
        
        tk.Label(frame, text="City:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w', pady=(5,0))
        city = tk.Entry(frame, width=30, font=('Arial', 10), relief='solid', bd=1)
        city.pack(pady=2)
        
        def save():
            if not name.get().strip():
                show_error("Group name required")
                return
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            try:
                c.execute("INSERT INTO groups (group_name, area, city, created_date) VALUES (?,?,?,?)",
                          (name.get().strip(), area.get().strip(), city.get().strip(), self.working_date))
                conn.commit()
                show_success("Group added")
                dialog.destroy()
                self.load_groups()
                self.load_groups_tree()
            except sqlite3.IntegrityError:
                show_error("Group name exists")
            finally:
                conn.close()
        
        setup_enter_navigation(name, area)
        setup_enter_navigation(area, city)
        setup_enter_navigation(city, save)
        
        btn_frame = tk.Frame(frame, bg='#f9f9f9')
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Save", command=save, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 11), width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def edit_group(self):
        sel = self.groups_tree.selection()
        if not sel:
            show_error("Select a group to edit")
            return
        
        # Get group details
        values = self.groups_tree.item(sel[0])['values']
        group_id = values[0]
        group_name = values[1]
        area = values[2] if len(values) > 2 else ''
        city = values[3] if len(values) > 3 else ''
        
        # Create edit dialog
        dialog = tk.Toplevel(self.window)
        dialog.title("Edit Group")
        dialog.geometry("400x250")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 250) // 2
        dialog.geometry(f"400x250+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="EDIT GROUP", font=('Arial', 14, 'bold'), 
                 bg='#f39c12', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Group Name:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w')
        name_var = tk.StringVar(value=group_name)
        name_entry = tk.Entry(frame, textvariable=name_var, width=30, font=('Arial', 10), relief='solid', bd=1)
        name_entry.pack(pady=2)
        name_entry.focus()
        
        tk.Label(frame, text="Area:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w', pady=(5,0))
        area_var = tk.StringVar(value=area)
        area_entry = tk.Entry(frame, textvariable=area_var, width=30, font=('Arial', 10), relief='solid', bd=1)
        area_entry.pack(pady=2)
        
        tk.Label(frame, text="City:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w', pady=(5,0))
        city_var = tk.StringVar(value=city)
        city_entry = tk.Entry(frame, textvariable=city_var, width=30, font=('Arial', 10), relief='solid', bd=1)
        city_entry.pack(pady=2)
        
        def save_changes():
            if not name_var.get().strip():
                show_error("Group name required")
                return
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            try:
                c.execute('''UPDATE groups 
                             SET group_name=?, area=?, city=? 
                             WHERE id=?''',
                          (name_var.get().strip(), area_var.get().strip(), 
                           city_var.get().strip(), group_id))
                conn.commit()
                show_success("Group updated successfully")
                dialog.destroy()
                self.load_groups()
                self.load_groups_tree()
            except sqlite3.IntegrityError:
                show_error("Group name already exists")
            finally:
                conn.close()
        
        # Setup Enter key navigation
        from utils import setup_enter_navigation
        setup_enter_navigation(name_entry, area_entry)
        setup_enter_navigation(area_entry, city_entry)
        setup_enter_navigation(city_entry, save_changes)
        
        btn_frame = tk.Frame(frame, bg='#f9f9f9')
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Save", command=save_changes,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def delete_group(self):
        sel = self.groups_tree.selection()
        if not sel:
            show_error("Select a group")
            return
        
        group_id = self.groups_tree.item(sel[0])['values'][0]
        group_name = self.groups_tree.item(sel[0])['values'][1]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM members WHERE group_id=?", (group_id,))
        count = c.fetchone()[0]
        conn.close()
        
        if count > 0:
            show_error(f"Cannot delete - {count} members in this group")
            return
        
        if ask_yes_no(f"Delete {group_name}?"):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("DELETE FROM groups WHERE id=?", (group_id,))
            conn.commit()
            conn.close()
            self.load_groups()
            self.load_groups_tree()


class SelectMemberForCredit:
    def __init__(self, parent, working_date=None):
        self.parent = parent
        self.working_date = working_date or datetime.now().strftime('%Y-%m-%d')
        self.selected_member = None
        self.window = tk.Toplevel(parent)
        self.window.title("Select Member")
        self.window.geometry("600x400")
        
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 400) // 2
        self.window.geometry(f"600x400+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_members()
    
    def create_widgets(self):
        tk.Label(self.window, text="SELECT MEMBER", font=('Arial', 14, 'bold'), bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(self.window, bg='#f9f9f9', padx=5, pady=5)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Search
        tk.Label(frame, text="Search:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w')
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_members())
        search_entry = tk.Entry(frame, textvariable=self.search_var, width=40, font=('Arial', 10), relief='solid', bd=1)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        # Tree
        tree_frame = tk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('ID', 'Member No', 'Name', 'CNIC', 'Phone', 'Group', 'Account')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=vsb.set, height=10)
        vsb.config(command=self.tree.yview)
        
        col_widths = {'ID': 40, 'Member No': 90, 'Name': 150, 'CNIC': 120, 'Phone': 100, 'Group': 100, 'Account': 80}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.bind('<Double-Button-1>', self.select)
        
        # Buttons
        btn_frame = tk.Frame(frame, bg='#f9f9f9')
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Select", command=self.select, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=10, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(btn_frame, text="Cancel", command=self.window.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 11), width=10, cursor='hand2').pack(side=tk.LEFT, padx=2)
    
    def load_members(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT m.id, m.member_no, m.name, m.cnic, m.contact, g.group_name, a.account_code
                   FROM members m
                   LEFT JOIN groups g ON m.group_id = g.id
                   LEFT JOIN accounts a ON m.account_id = a.id
                   WHERE m.status='Active' '''
        params = []
        
        if search:
            query += " AND (m.name LIKE ? OR m.member_no LIKE ? OR m.cnic LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY m.name LIMIT 50"
        
        c.execute(query, params)
        members = c.fetchall()
        conn.close()
        
        for m in members:
            self.tree.insert('', tk.END, values=m)
    
    def select(self, event=None):
        sel = self.tree.selection()
        if not sel:
            show_error("Select a member")
            return
        
        values = self.tree.item(sel[0])['values']
        self.selected_member = {
            'id': values[0],
            'member_no': values[1],
            'name': values[2],
            'cnic': values[3],
            'contact': values[4],
            'group': values[5],
            'account_code': values[6]
        }
        self.window.destroy()