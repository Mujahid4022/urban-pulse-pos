# credit_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, show_info

class CreditManager:
    def __init__(self, parent, working_date=None):
        self.parent = parent
        self.working_date = working_date or datetime.now().strftime('%Y-%m-%d')
        print(f"Credit Manager using date: {self.working_date}")
        self.window = tk.Toplevel(parent)
        self.window.title("Recovery Management")
        self.window.geometry("1000x650")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 650) // 2
        self.window.geometry(f"1000x650+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Create edit_log table if not exists
        self.create_edit_log_table()
        
        self.create_widgets()
        self.load_credit_sales()
        self.load_overdue()
        self.load_payment_history()
    
    def create_edit_log_table(self):
        """Create edit_log table for tracking invoice edits"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS edit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_type TEXT,
            reference_id INTEGER,
            reference_no TEXT,
            old_value REAL,
            new_value REAL,
            reason TEXT,
            edited_by TEXT,
            edit_date DATETIME
        )''')
        conn.commit()
        conn.close()
        print("✅ Edit log table created/verified")
    
    def create_widgets(self):
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Active Recovery
        self.active_tab = tk.Frame(notebook)
        notebook.add(self.active_tab, text="📋 Active Recovery")
        self.create_active_tab()
        
        # Tab 2: Overdue Recovery
        self.overdue_tab = tk.Frame(notebook)
        notebook.add(self.overdue_tab, text="⚠️ Overdue Recovery")
        self.create_overdue_tab()
        
        # Tab 3: Recovery History
        self.history_tab = tk.Frame(notebook)
        notebook.add(self.history_tab, text="📜 Recovery History")
        self.create_history_tab()
        
        # Tab 4: Recovery Report
        self.report_tab = tk.Frame(notebook)
        notebook.add(self.report_tab, text="📊 Recovery Report")
        self.create_report_tab()
    
    def create_active_tab(self):
        # Title
        title_frame = tk.Frame(self.active_tab, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="ACTIVE RECOVERY", fg='white', bg='#3498db',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Search frame
        search_frame = tk.Frame(self.active_tab, bg='#ecf0f1', height=60)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="Search Member:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=20, y=10)
        tk.Label(search_frame, text="Name/CNIC/Member No:", bg='#ecf0f1', font=('Arial', 9)).place(x=20, y=35)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_credit_sales())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30, font=('Arial', 9), relief='solid', bd=1)
        search_entry.place(x=150, y=32, height=25)
        search_entry.bind('<Return>', lambda e: self.load_credit_sales())
        
        tk.Label(search_frame, text="Status:", bg='#ecf0f1', font=('Arial', 9)).place(x=400, y=35)
        self.status_filter = ttk.Combobox(search_frame, values=['All', 'Pending', 'Partial', 'Paid'], width=12, font=('Arial', 9))
        self.status_filter.set('Pending')
        self.status_filter.place(x=450, y=32, height=25)
        self.status_filter.bind('<<ComboboxSelected>>', lambda e: self.load_credit_sales())
        
        tk.Button(search_frame, text="🔄 Refresh", command=self.load_credit_sales, bg='#3498db', fg='white',
                 font=('Arial', 9), cursor='hand2').place(x=600, y=28, width=100, height=28)
        
        # Treeview
        tree_frame = tk.Frame(self.active_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('ID', 'Invoice #', 'Member', 'Group', 'Total', 'Paid', 'Due', 'Sale Date', 'Due Date', 'Status', 'Days')
        self.active_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                        yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        vsb.config(command=self.active_tree.yview)
        hsb.config(command=self.active_tree.xview)
        
        col_widths = {'ID': 40, 'Invoice #': 90, 'Member': 150, 'Group': 100, 'Total': 80,
                     'Paid': 80, 'Due': 80, 'Sale Date': 90, 'Due Date': 90, 'Status': 80, 'Days': 50}
        
        for col in columns:
            self.active_tree.heading(col, text=col)
            self.active_tree.column(col, width=col_widths.get(col, 70), anchor='center')
        
        self.active_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.active_tree.tag_configure('overdue', background='#ffcccc')
        self.active_tree.tag_configure('due_soon', background='#ffffcc')
        self.active_tree.bind('<Double-Button-1>', self.view_credit_details)
        
        # Buttons - ADDED EDIT BUTTON
        btn_frame = tk.Frame(self.active_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 170, 320, 470]  # Added 4th button position for Edit
        
        tk.Button(btn_frame, text="👁️ View Details", command=self.view_credit_details, bg='#3498db', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[0], y=10)
        tk.Button(btn_frame, text="💰 Receive Payment", command=self.receive_payment, bg='#27ae60', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[1], y=10)
        # NEW EDIT BUTTON
        tk.Button(btn_frame, text="✏️ Edit Invoice", command=self.edit_credit_invoice, bg='#f39c12', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[2], y=10)
        tk.Button(btn_frame, text="🖨️ Print Receipt", command=self.print_receipt, bg='#9b59b6', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[3], y=10)
    
    def create_overdue_tab(self):
        title_frame = tk.Frame(self.overdue_tab, bg='#e74c3c', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="OVERDUE RECOVERY", fg='white', bg='#e74c3c',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        tree_frame = tk.Frame(self.overdue_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('ID', 'Invoice #', 'Member', 'Group', 'Due Amount', 'Due Date', 'Days Overdue', 'Contact')
        self.overdue_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=vsb.set, height=12)
        vsb.config(command=self.overdue_tree.yview)
        
        col_widths = {'ID': 40, 'Invoice #': 90, 'Member': 150, 'Group': 100, 'Due Amount': 80,
                     'Due Date': 80, 'Days Overdue': 80, 'Contact': 120}
        
        for col in columns:
            self.overdue_tree.heading(col, text=col)
            self.overdue_tree.column(col, width=col_widths.get(col, 70), anchor='center')
        
        self.overdue_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        self.overdue_tree.bind('<Double-Button-1>', self.view_credit_details)
        
        btn_frame = tk.Frame(self.overdue_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 170, 320]
        
        tk.Button(btn_frame, text="📧 Send Reminder", command=self.send_reminder, bg='#f39c12', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[0], y=10)
        tk.Button(btn_frame, text="💰 Receive Payment", command=self.receive_payment, bg='#27ae60', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[1], y=10)
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_overdue, bg='#3498db', fg='white',
                 font=('Arial', 10), width=15, cursor='hand2').place(x=btn_x[2], y=10)
        
        self.load_overdue()
    
    def create_history_tab(self):
        title_frame = tk.Frame(self.history_tab, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="RECOVERY HISTORY", fg='white', bg='#f39c12',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        search_frame = tk.Frame(self.history_tab, bg='#ecf0f1', height=50)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="Search Member:", bg='#ecf0f1', font=('Arial', 10)).place(x=20, y=15)
        self.history_search = tk.StringVar()
        self.history_search.trace('w', lambda *args: self.load_payment_history())
        search_entry = tk.Entry(search_frame, textvariable=self.history_search, width=30, font=('Arial', 9), relief='solid', bd=1)
        search_entry.place(x=120, y=12, height=25)
        search_entry.bind('<Return>', lambda e: self.load_payment_history())
        
        tk.Button(search_frame, text="🔄 Refresh", command=self.load_payment_history, bg='#3498db', fg='white',
                 font=('Arial', 9), cursor='hand2').place(x=450, y=10, width=100, height=28)
        
        tree_frame = tk.Frame(self.history_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('Date', 'Invoice #', 'Member', 'Amount', 'Method', 'Receipt #', 'Notes')
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        vsb.config(command=self.history_tree.yview)
        hsb.config(command=self.history_tree.xview)
        
        col_widths = {'Date': 90, 'Invoice #': 90, 'Member': 150, 'Amount': 80,
                     'Method': 80, 'Receipt #': 90, 'Notes': 150}
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=col_widths.get(col, 70), anchor='center')
        
        self.history_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.load_payment_history()
    
    def create_report_tab(self):
        title_frame = tk.Frame(self.report_tab, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="RECOVERY REPORT", fg='white', bg='#27ae60',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        filter_frame = tk.Frame(self.report_tab, bg='#ecf0f1', height=60)
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        filter_frame.pack_propagate(False)
        
        tk.Label(filter_frame, text="Group:", bg='#ecf0f1', font=('Arial', 10)).place(x=20, y=20)
        self.report_group = ttk.Combobox(filter_frame, width=20, font=('Arial', 9))
        self.report_group.place(x=80, y=18, height=25)
        self.load_groups_for_report()
        
        tk.Label(filter_frame, text="From:", bg='#ecf0f1', font=('Arial', 10)).place(x=250, y=20)
        self.from_date = tk.Entry(filter_frame, width=12, font=('Arial', 9), relief='solid', bd=1)
        working_date_obj = datetime.strptime(self.working_date, '%Y-%m-%d')
        self.from_date.insert(0, (working_date_obj - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date.place(x=300, y=18, height=25)
        
        tk.Label(filter_frame, text="To:", bg='#ecf0f1', font=('Arial', 10)).place(x=420, y=20)
        self.to_date = tk.Entry(filter_frame, width=12, font=('Arial', 9), relief='solid', bd=1)
        self.to_date.insert(0, self.working_date)
        self.to_date.place(x=450, y=18, height=25)
        
        tk.Button(filter_frame, text="Generate", command=self.generate_report, bg='#27ae60', fg='white',
                 font=('Arial', 9), cursor='hand2').place(x=550, y=15, width=100, height=28)
        
        # Report tree
        tree_frame = tk.Frame(self.report_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('Group', 'Member No', 'Member Name', 'Invoice #', 'Amount', 'Recovery Date', 'Status')
        self.report_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                        yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        vsb.config(command=self.report_tree.yview)
        hsb.config(command=self.report_tree.xview)
        
        col_widths = {'Group': 100, 'Member No': 80, 'Member Name': 150, 'Invoice #': 90,
                     'Amount': 80, 'Recovery Date': 90, 'Status': 80}
        
        for col in columns:
            self.report_tree.heading(col, text=col)
            self.report_tree.column(col, width=col_widths.get(col, 70), anchor='center')
        
        self.report_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summary
        summary_frame = tk.Frame(self.report_tab, bg='#ecf0f1', height=40)
        summary_frame.pack(fill=tk.X, padx=10, pady=10)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Total Recovered:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=20, y=10)
        self.total_collected = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0", bg='#ecf0f1',
                                        font=('Arial', 10, 'bold'), fg='#27ae60')
        self.total_collected.place(x=150, y=10)
        
        tk.Label(summary_frame, text="Pending Recovery:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=280, y=10)
        self.total_pending = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0", bg='#ecf0f1',
                                      font=('Arial', 10, 'bold'), fg='#e74c3c')
        self.total_pending.place(x=420, y=10)
        
        tk.Button(summary_frame, text="Export CSV", command=self.export_report, bg='#3498db', fg='white',
                 font=('Arial', 9), cursor='hand2').place(x=550, y=6, width=100, height=28)
    
    def load_groups_for_report(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT group_name FROM groups ORDER BY group_name")
        groups = c.fetchall()
        conn.close()
        values = ['All Groups'] + [g[0] for g in groups]
        self.report_group['values'] = values
        self.report_group.set('All Groups')
    
    def load_credit_sales(self):
        for row in self.active_tree.get_children():
            self.active_tree.delete(row)
        
        search = self.search_var.get().strip()
        status = self.status_filter.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT cs.id, cs.invoice_no, m.name, g.group_name,
                          cs.total_amount, cs.paid_amount, cs.due_amount,
                          cs.sale_date, cs.due_date, cs.status
                   FROM credit_sales cs
                   JOIN members m ON cs.member_id = m.id
                   LEFT JOIN groups g ON m.group_id = g.id
                   WHERE 1=1'''
        params = []
        
        if search:
            query += " AND (m.name LIKE ? OR m.member_no LIKE ? OR m.cnic LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if status and status != 'All':
            query += " AND cs.status = ?"
            params.append(status)
        
        query += " ORDER BY cs.due_date"
        
        c.execute(query, params)
        sales = c.fetchall()
        conn.close()
        
        today = datetime.strptime(self.working_date, '%Y-%m-%d').date()
        for s in sales:
            due_date = datetime.strptime(s[8], '%Y-%m-%d').date() if s[8] else None
            days = (today - due_date).days if due_date and due_date < today else 0
            tags = ()
            if days > 0:
                tags = ('overdue',)
            elif days > -7:
                tags = ('due_soon',)
            self.active_tree.insert('', tk.END, values=(s[0], s[1], s[2], s[3] or '',
                                                        f"{CURRENCY_SYMBOL}{s[4]:.2f}",
                                                        f"{CURRENCY_SYMBOL}{s[5]:.2f}",
                                                        f"{CURRENCY_SYMBOL}{s[6]:.2f}",
                                                        s[7][:10] if s[7] else '', 
                                                        s[8] or '', s[9], days), tags=tags)
    
    def load_overdue(self):
        for row in self.overdue_tree.get_children():
            self.overdue_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        today = self.working_date
        
        c.execute('''SELECT cs.id, cs.invoice_no, m.name, g.group_name,
                            cs.due_amount, cs.due_date, m.contact
                     FROM credit_sales cs
                     JOIN members m ON cs.member_id = m.id
                     LEFT JOIN groups g ON m.group_id = g.id
                     WHERE cs.due_date < ? AND cs.status != 'Paid'
                     ORDER BY cs.due_date''', (today,))
        overdue = c.fetchall()
        conn.close()

        today_date = datetime.strptime(self.working_date, '%Y-%m-%d')
        for o in overdue:
            due = datetime.strptime(o[5], '%Y-%m-%d')
            days = (today_date - due).days
            self.overdue_tree.insert('', tk.END, values=(o[0], o[1], o[2], o[3] or '',
                                                         f"{CURRENCY_SYMBOL}{o[4]:.2f}",
                                                         o[5], days, o[6] or 'N/A'))
    
    def load_payment_history(self):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        
        search = self.history_search.get().strip()
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT cp.payment_date, cs.invoice_no, m.name, cp.amount,
                          cp.payment_method, cp.receipt_no, cp.notes
                   FROM credit_payments cp
                   JOIN credit_sales cs ON cp.credit_sale_id = cs.id
                   JOIN members m ON cs.member_id = m.id'''
        params = []
        if search:
            query += " WHERE m.name LIKE ? OR m.member_no LIKE ? OR m.cnic LIKE ?"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        query += " ORDER BY cp.payment_date DESC LIMIT 500"
        
        c.execute(query, params)
        payments = c.fetchall()
        conn.close()
        
        for p in payments:
            self.history_tree.insert('', tk.END, values=(p[0][:16] if p[0] else '', p[1], p[2],
                                                         f"{CURRENCY_SYMBOL}{p[3]:.2f}",
                                                         p[4], p[5] or '-', p[6] or '-'))
    
    def generate_report(self):
        for row in self.report_tree.get_children():
            self.report_tree.delete(row)
        
        group = self.report_group.get()
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT g.group_name, m.member_no, m.name, cs.invoice_no,
                          cp.amount, cp.payment_date, cs.status
                   FROM credit_payments cp
                   JOIN credit_sales cs ON cp.credit_sale_id = cs.id
                   JOIN members m ON cs.member_id = m.id
                   LEFT JOIN groups g ON m.group_id = g.id
                   WHERE DATE(cp.payment_date) BETWEEN ? AND ?'''
        params = [from_d, to_d]
        
        if group and group != 'All Groups':
            query += " AND g.group_name = ?"
            params.append(group)
        
        query += " ORDER BY g.group_name, m.name, cp.payment_date"
        
        c.execute(query, params)
        payments = c.fetchall()
        
        c.execute('''SELECT SUM(cs.due_amount) FROM credit_sales cs
                     JOIN members m ON cs.member_id = m.id
                     WHERE cs.status != 'Paid' ''')
        pending = c.fetchone()[0] or 0
        
        conn.close()
        
        total = 0
        for p in payments:
            self.report_tree.insert('', tk.END, values=(p[0] or 'No Group', p[1], p[2], p[3],
                                                         f"{CURRENCY_SYMBOL}{p[4]:.2f}", p[5][:10] if p[5] else '', p[6]))
            total += p[4]
        
        self.total_collected.config(text=f"{CURRENCY_SYMBOL}{total:.2f}")
        self.total_pending.config(text=f"{CURRENCY_SYMBOL}{pending:.2f}")
    
    def view_credit_details(self, event=None):
        selected = self.active_tree.selection() or self.overdue_tree.selection()
        if not selected:
            return
        
        if selected[0] in self.active_tree.get_children():
            credit_id = self.active_tree.item(selected[0])['values'][0]
        else:
            credit_id = self.overdue_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT cs.*, m.name, m.member_no, m.contact, g.group_name
                     FROM credit_sales cs
                     JOIN members m ON cs.member_id = m.id
                     LEFT JOIN groups g ON m.group_id = g.id
                     WHERE cs.id=?''', (credit_id,))
        row = c.fetchone()
        
        if not row:
            conn.close()
            return
        
        c.execute('''SELECT payment_date, amount, payment_method, receipt_no 
                     FROM credit_payments WHERE credit_sale_id=? ORDER BY payment_date''', (credit_id,))
        payments = c.fetchall()
        conn.close()
        
        win = tk.Toplevel(self.window)
        win.title(f"Recovery Details - {row[3]}")
        win.geometry("500x450")
        win.configure(bg='#f9f9f9')
        
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 500) // 2
        y = (win.winfo_screenheight() - 450) // 2
        win.geometry(f"500x450+{x}+{y}")
        
        text = tk.Text(win, font=('Courier', 10), bg='white', padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        details = f"""
{'='*50}
RECOVERY DETAILS
{'='*50}

Invoice #: {row[3]}
Member: {row[12]} ({row[13]})
Group: {row[15] or 'N/A'}
Contact: {row[14] or 'N/A'}

Sale Date: {row[7][:10] if row[7] else ''}
Due Date: {row[8] or ''}
Total: {CURRENCY_SYMBOL}{row[4]:.2f}
Recovered: {CURRENCY_SYMBOL}{row[5]:.2f}
Pending: {CURRENCY_SYMBOL}{row[6]:.2f}
Status: {row[9]}

PAYMENT HISTORY:
"""
        if payments:
            for p in payments:
                details += f"  {p[0][:10] if p[0] else ''} - {CURRENCY_SYMBOL}{p[1]:.2f} ({p[2]})\n"
        else:
            details += "  No payments recorded\n"
        
        text.insert('1.0', details)
        text.config(state='disabled')
        
        tk.Button(win, text="Close", command=win.destroy, bg='#3498db', fg='white',
                 font=('Arial', 10), cursor='hand2').pack(pady=5)
    
    # ===== EDIT FUNCTIONS =====
    
    def edit_credit_invoice(self):
        """Edit selected credit sale invoice"""
        selected = self.active_tree.selection()
        if not selected:
            show_error("Please select a credit sale to edit")
            return
        
        # Get credit sale details
        credit_id = self.active_tree.item(selected[0])['values'][0]
        invoice_no = self.active_tree.item(selected[0])['values'][1]
        member_name = self.active_tree.item(selected[0])['values'][2]
        
        # Check if payments already received
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM credit_payments WHERE credit_sale_id = ?", (credit_id,))
        payment_count = c.fetchone()[0]
        conn.close()
        
        if payment_count > 0:
            show_error(f"Cannot edit invoice {invoice_no}\n\n"
                      f"Payments have already been received against this invoice.\n"
                      f"This invoice has {payment_count} payment(s).")
            return
        
        # Open edit dialog
        self.open_edit_dialog(credit_id, invoice_no, member_name)
    
    def open_edit_dialog(self, credit_id, invoice_no, member_name):
        """Open dialog to edit credit sale amount"""
        
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Edit Invoice {invoice_no}")
        dialog.geometry("450x350")
        dialog.configure(bg='#f9f9f9')
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 350) // 2
        dialog.geometry(f"450x350+{x}+{y}")
        
        # Title
        tk.Label(dialog, text=f"EDIT INVOICE", font=('Arial', 14, 'bold'),
                bg='#f39c12', fg='white').pack(fill=tk.X, pady=10)
        
        # Main frame
        main = tk.Frame(dialog, bg='#f9f9f9', padx=20, pady=10)
        main.pack(fill=tk.BOTH, expand=True)
        
        # Current info
        info_frame = tk.Frame(main, bg='#ecf0f1', relief=tk.GROOVE, bd=1)
        info_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(info_frame, text=f"Invoice: {invoice_no}", font=('Arial', 11, 'bold'),
                bg='#ecf0f1').pack(anchor='w', padx=10, pady=2)
        tk.Label(info_frame, text=f"Member: {member_name}", bg='#ecf0f1',
                font=('Arial', 10)).pack(anchor='w', padx=10, pady=2)
        
        # Get current amount
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT total_amount FROM credit_sales WHERE id = ?", (credit_id,))
        current_amount = c.fetchone()[0]
        conn.close()
        
        tk.Label(info_frame, text=f"Current Amount: {CURRENCY_SYMBOL}{current_amount:.2f}", 
                font=('Arial', 11, 'bold'), bg='#ecf0f1', fg='#27ae60').pack(anchor='w', padx=10, pady=5)
        
        # New amount
        tk.Label(main, text="New Amount (Rs.):", bg='#f9f9f9', font=('Arial', 11)).pack(anchor='w', pady=5)
        amount_var = tk.StringVar(value=str(int(current_amount)))
        amount_entry = tk.Entry(main, textvariable=amount_var, font=('Arial', 14),
                               width=15, justify='right', relief='solid', bd=1)
        amount_entry.pack(pady=5)
        amount_entry.select_range(0, tk.END)
        amount_entry.focus()
        
        # Reason
        tk.Label(main, text="Reason for edit:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w', pady=5)
        reason_text = tk.Text(main, height=3, width=40, font=('Arial', 9), relief='solid', bd=1)
        reason_text.pack(pady=5)
        
        def save_changes():
            try:
                new_amount = float(amount_var.get())
                if new_amount <= 0:
                    show_error("Amount must be positive")
                    return
                
                reason = reason_text.get('1.0', tk.END).strip()
                if not reason:
                    show_warning = messagebox.askyesno("Warning", "No reason provided. Continue anyway?")
                    if not show_warning:
                        return
                    reason = "No reason provided"
                
                # Process the edit
                self.process_invoice_edit(credit_id, invoice_no, current_amount, new_amount, reason)
                dialog.destroy()
                
            except ValueError:
                show_error("Invalid amount")
        
        # Buttons
        btn_frame = tk.Frame(main, bg='#f9f9f9')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save Changes", command=save_changes,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        amount_entry.bind('<Return>', lambda e: save_changes())
    
    def process_invoice_edit(self, credit_id, invoice_no, old_amount, new_amount, reason):
        """Process invoice edit with proper accounting adjustment"""
        
        if old_amount == new_amount:
            show_info("No change in amount")
            return
        
        difference = new_amount - old_amount
        diff_abs = abs(difference)
        adjustment_type = "Increase" if difference > 0 else "Decrease"
        
        if not ask_yes_no(f"Original Amount: {CURRENCY_SYMBOL}{old_amount:.2f}\n"
                         f"New Amount: {CURRENCY_SYMBOL}{new_amount:.2f}\n"
                         f"{adjustment_type}: {CURRENCY_SYMBOL}{diff_abs:.2f}\n\n"
                         f"This will create an adjustment entry. Continue?"):
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            c.execute("BEGIN TRANSACTION")
            
            # Get member details
            c.execute("SELECT member_id FROM credit_sales WHERE id = ?", (credit_id,))
            member_id = c.fetchone()[0]
            
            c.execute("SELECT account_id FROM members WHERE id = ?", (member_id,))
            member_account = c.fetchone()[0]
            
            # Get account IDs
            c.execute("SELECT id FROM accounts WHERE account_code='1200'")
            receivable = c.fetchone()
            if not receivable:
                raise Exception("Accounts Receivable account (1200) not found!")
            receivable_id = receivable[0]
            
            c.execute("SELECT id FROM accounts WHERE account_code='4000'")
            revenue = c.fetchone()
            if not revenue:
                raise Exception("Sales Revenue account (4000) not found!")
            revenue_id = revenue[0]
            
            # Get or create Other Income account
            c.execute("SELECT id FROM accounts WHERE account_code='4100'")
            other_income = c.fetchone()
            if not other_income:
                c.execute('''INSERT INTO accounts 
                            (account_code, account_name, account_type, current_balance, is_active, created_date)
                            VALUES ('4100', 'Other Income', 'Income', 0, 1, date('now'))''')
                other_income_id = c.lastrowid
                print("✅ Created Other Income account")
            else:
                other_income_id = other_income[0]
            
            # Create adjustment voucher
            from datetime import datetime
            adj_no = f"ADJ-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, created_by, created_at)
                        VALUES (?, 'Adjustment', ?, ?, ?, ?, ?)''',
                      (adj_no, self.working_date, 
                       f"Edit invoice {invoice_no}: {reason}", diff_abs,
                       'admin', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            voucher_id = c.lastrowid
            
            if difference > 0:  # Increase amount
                # Debit member account
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, ?, 0, ?, ?)''',
                          (voucher_id, member_account, difference, self.working_date,
                           f"Increase invoice {invoice_no}"))
                
                # Debit receivable
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, ?, 0, ?, ?)''',
                          (voucher_id, receivable_id, difference, self.working_date,
                           f"Increase invoice {invoice_no}"))
                
                # Credit revenue (simplified - you may want to split based on original)
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, 0, ?, ?, ?)''',
                          (voucher_id, revenue_id, difference, self.working_date,
                           f"Increase invoice {invoice_no}"))
                
                # Update balances
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id = ?", 
                         (difference, member_account))
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id = ?", 
                         (difference, receivable_id))
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id = ?", 
                         (difference, revenue_id))
                
            else:  # Decrease amount
                diff = abs(difference)
                # Credit member account
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, 0, ?, ?, ?)''',
                          (voucher_id, member_account, diff, self.working_date,
                           f"Decrease invoice {invoice_no}"))
                
                # Credit receivable
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, 0, ?, ?, ?)''',
                          (voucher_id, receivable_id, diff, self.working_date,
                           f"Decrease invoice {invoice_no}"))
                
                # Debit revenue
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, ?, 0, ?, ?)''',
                          (voucher_id, revenue_id, diff, self.working_date,
                           f"Decrease invoice {invoice_no}"))
                
                # Update balances
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id = ?", 
                         (diff, member_account))
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id = ?", 
                         (diff, receivable_id))
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id = ?", 
                         (diff, revenue_id))
            
            # Update credit_sales table
            c.execute('''UPDATE credit_sales 
                         SET total_amount = ?, due_amount = ? 
                         WHERE id = ?''', (new_amount, new_amount, credit_id))
            
            # Log the edit
            c.execute('''INSERT INTO edit_log 
                        (reference_type, reference_id, reference_no, old_value, new_value, reason, edited_by, edit_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                      ('credit_sale', credit_id, invoice_no, old_amount, new_amount, reason,
                       'admin', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            conn.commit()
            
            show_success(f"Invoice {invoice_no} updated!\n"
                        f"Old: {CURRENCY_SYMBOL}{old_amount:.2f} → New: {CURRENCY_SYMBOL}{new_amount:.2f}\n"
                        f"Adjustment voucher: {adj_no}")
            
            # Refresh the list
            self.load_credit_sales()
            self.load_overdue()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Failed to edit invoice: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    
    # ===== FIXED RECEIVE PAYMENT METHOD =====
    def receive_payment(self):
        selected = self.active_tree.selection() or self.overdue_tree.selection()
        if not selected:
            show_error("Select a recovery item first")
            return
        
        if selected[0] in self.active_tree.get_children():
            credit_id = self.active_tree.item(selected[0])['values'][0]
        else:
            credit_id = self.overdue_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        # FIXED: Added m.account_id to the SELECT query
        c.execute('''SELECT cs.id, cs.invoice_no, cs.total_amount, cs.paid_amount, 
                            cs.due_amount, cs.status, m.name, m.member_no, m.account_id
                     FROM credit_sales cs
                     JOIN members m ON cs.member_id = m.id
                     WHERE cs.id=?''', (credit_id,))
        sale = c.fetchone()
        conn.close()
        
        if not sale:
            show_error("Credit sale not found")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Receive Payment")
        dialog.geometry("400x480")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 480) // 2
        dialog.geometry(f"400x480+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="RECEIVE PAYMENT", font=('Arial', 14, 'bold'), bg='#27ae60', fg='white').pack(fill=tk.X, pady=10)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Member: {sale[6]}", font=('Arial', 11, 'bold'), bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Invoice: {sale[1]}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Total: {CURRENCY_SYMBOL}{sale[2]:.2f}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Paid: {CURRENCY_SYMBOL}{sale[3]:.2f}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Pending: {CURRENCY_SYMBOL}{sale[4]:.2f}", bg='#f9f9f9', font=('Arial', 10, 'bold')).pack(anchor='w', pady=5)
        
        tk.Label(frame, text="Payment Amount:", bg='#f9f9f9').pack(anchor='w')
        amount_var = tk.StringVar()
        amount_entry = tk.Entry(frame, textvariable=amount_var, width=20, font=('Arial', 11), relief='solid', bd=1)
        amount_entry.pack(pady=5)
        amount_entry.focus()
        
        tk.Label(frame, text="Payment Method:", bg='#f9f9f9').pack(anchor='w')
        method_var = tk.StringVar(value="Cash")
        method_combo = ttk.Combobox(frame, textvariable=method_var, values=["Cash", "Bank Transfer", "Cheque", "UPI"], width=17, font=('Arial', 10))
        method_combo.pack(pady=5)
        
        tk.Label(frame, text="Receipt # (optional):", bg='#f9f9f9').pack(anchor='w')
        receipt_var = tk.StringVar()
        receipt_entry = tk.Entry(frame, textvariable=receipt_var, width=20, font=('Arial', 10), relief='solid', bd=1)
        receipt_entry.pack(pady=5)
        
        tk.Label(frame, text="Notes:", bg='#f9f9f9').pack(anchor='w')
        notes_text = tk.Text(frame, height=2, width=40, font=('Arial', 9), relief='solid', bd=1)
        notes_text.pack(pady=5)
        
        def process():
            try:
                amount = float(amount_var.get())
                if amount <= 0:
                    show_error("Amount must be positive")
                    return
                if amount > sale[4]:
                    if not ask_yes_no(f"Amount {CURRENCY_SYMBOL}{amount:.2f} exceeds pending amount. Continue?"):
                        return
            except ValueError:
                show_error("Invalid amount")
                return
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            new_paid = sale[3] + amount
            new_due = sale[2] - new_paid
            new_status = 'Paid' if new_due <= 0.01 else 'Partial'
            
            c.execute('''UPDATE credit_sales SET paid_amount=?, due_amount=?, status=?, last_payment_date=?
                WHERE id=?''', 
                (new_paid, new_due, new_status, 
                 f"{self.working_date} {datetime.now().strftime('%H:%M:%S')}", credit_id))

            receipt_no = receipt_var.get() or f"RCP-{self.working_date.replace('-', '')}-{datetime.now().strftime('%H%M%S')}"
            
            c.execute('''INSERT INTO credit_payments (credit_sale_id, payment_date, amount, payment_method, receipt_no, notes)
                VALUES (?,?,?,?,?,?)''',
                (credit_id, f"{self.working_date} {datetime.now().strftime('%H:%M:%S')}", 
                 amount, method_var.get(), receipt_no, notes_text.get('1.0', tk.END).strip()))

            # ===== FIXED ACCOUNTING INTEGRATION =====
            today = self.working_date.replace('-', '')
            c.execute("SELECT COUNT(*) FROM vouchers WHERE voucher_no LIKE ?", (f'RCT-{today}%',))
            count = c.fetchone()[0] + 1
            voucher_no = f"RCT-{today}-{count:03d}"
            
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, 
                         created_by, created_at, member_id)
                        VALUES (?,?,?,?,?,?,?,?)''',
                      (voucher_no, 'Receipt', self.working_date, 
                       f"Payment from {sale[6]} for invoice {sale[1]} | Ref: {receipt_no} | Mode: {method_var.get()}", 
                       amount, 'admin', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), sale[0]))
            voucher_id = c.lastrowid
            
            # Get account IDs
            c.execute("SELECT id FROM accounts WHERE account_code='1000'")
            cash_account = c.fetchone()
            c.execute("SELECT id FROM accounts WHERE account_code='1200'")
            ar_account = c.fetchone()
            
            # Get member's individual account ID (from sale[8])
            member_account_id = sale[8]
            
            if cash_account and ar_account and member_account_id:
                # 1. Debit Cash (increase cash)
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?,?,?,?,?,?)''',
                          (voucher_id, cash_account[0], amount, 0, self.working_date, 
                           f"Payment received from {sale[6]}"))
                
                # 2. Credit Member Account (decrease what they owe) - FIXED: Added this entry
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?,?,?,?,?,?)''',
                          (voucher_id, member_account_id, 0, amount, self.working_date,
                           f"Payment received - reduces balance"))
                
                # 3. Credit Accounts Receivable (decrease total receivables)
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?,?,?,?,?,?)''',
                          (voucher_id, ar_account[0], 0, amount, self.working_date, 
                           f"Payment received from {sale[6]}"))
                
                # Update account balances
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                         (amount, cash_account[0]))
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                         (amount, member_account_id))
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                         (amount, ar_account[0]))
            
            # ===== END ACCOUNTING INTEGRATION =====

            conn.commit()
            conn.close()
            
            show_success(f"Payment of {CURRENCY_SYMBOL}{amount:.2f} received!\nVoucher: {voucher_no}")
            dialog.destroy()
            self.load_credit_sales()
            self.load_overdue()
            self.load_payment_history()
        
        amount_entry.bind('<Return>', lambda e: method_combo.focus())
        method_combo.bind('<Return>', lambda e: receipt_entry.focus())
        receipt_entry.bind('<Return>', lambda e: notes_text.focus())
        notes_text.bind('<Return>', lambda e: process())
        
        btn_frame = tk.Frame(frame, bg='#f9f9f9')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Process Payment", command=process, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 11), width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def print_receipt(self):
        """Print receipt for selected credit sale"""
        selected = self.active_tree.selection() or self.overdue_tree.selection()
        if not selected:
            show_error("Please select a credit sale to print receipt")
            return
        
        if selected[0] in self.active_tree.get_children():
            invoice_no = self.active_tree.item(selected[0])['values'][1]
            member_name = self.active_tree.item(selected[0])['values'][2]
            total = self.active_tree.item(selected[0])['values'][4]
            paid = self.active_tree.item(selected[0])['values'][5]
            due = self.active_tree.item(selected[0])['values'][6]
        else:
            invoice_no = self.overdue_tree.item(selected[0])['values'][1]
            member_name = self.overdue_tree.item(selected[0])['values'][2]
            due = self.overdue_tree.item(selected[0])['values'][4]
            total = "(Unknown)"
            paid = "(Unknown)"
        
        # Show receipt preview
        receipt_text = f"""
{'='*50}
     URBAN PULSE - RECEIPT
{'='*50}

Invoice #: {invoice_no}
Member: {member_name}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Total Amount: {CURRENCY_SYMBOL}{total if isinstance(total, str) else f'{total:.2f}'}
Amount Paid: {CURRENCY_SYMBOL}{paid if isinstance(paid, str) else f'{paid:.2f}'}
Balance Due: {CURRENCY_SYMBOL}{due if isinstance(due, str) else f'{due:.2f}'}

{'='*50}
     Thank you for your payment!
{'='*50}
"""
        
        # Create preview window
        preview = tk.Toplevel(self.window)
        preview.title(f"Receipt - {invoice_no}")
        preview.geometry("400x500")
        preview.configure(bg='#f9f9f9')
        
        preview.update_idletasks()
        x = (preview.winfo_screenwidth() - 400) // 2
        y = (preview.winfo_screenheight() - 500) // 2
        preview.geometry(f"400x500+{x}+{y}")
        
        tk.Label(preview, text="RECEIPT PREVIEW", font=('Arial', 14, 'bold'),
                bg='#3498db', fg='white').pack(fill=tk.X, pady=10)
        
        text_area = tk.Text(preview, font=('Courier', 10), bg='white', padx=10, pady=10)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert('1.0', receipt_text)
        text_area.config(state='disabled')
        
        btn_frame = tk.Frame(preview, bg='#f9f9f9')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Print", command=lambda: show_info("Printer not configured. Please connect a printer."),
                 bg='#27ae60', fg='white', width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=preview.destroy,
                 bg='#e74c3c', fg='white', width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def send_reminder(self):
        selected = self.overdue_tree.selection()
        if not selected:
            return
        vals = self.overdue_tree.item(selected[0])['values']
        member = vals[2]
        contact = vals[7]
        show_info(f"Reminder sent to {member} at {contact}")
    
    def export_report(self):
        from tkinter import filedialog
        import csv
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not filename:
            return
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Group', 'Member No', 'Member Name', 'Invoice #', 'Amount', 'Recovery Date', 'Status'])
            for row in self.report_tree.get_children():
                writer.writerow(self.report_tree.item(row)['values'])
        show_success(f"Report exported to {filename}")