# supplier_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
from tkinter import ttk, messagebox, simpledialog
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation

# Ensure returns table exists
def ensure_returns_table():
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS po_returns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        po_id INTEGER,
        product_id INTEGER,
        return_date DATE,
        quantity INTEGER,
        reason TEXT,
        returned_by TEXT,
        FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    conn.commit()
    conn.close()

class AddEditSupplier:
    def __init__(self, parent, title, supplier_id=None, working_date=None):
        self.supplier_id = supplier_id
        self.working_date = working_date or datetime.now().strftime('%Y-%m-%d')
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("450x550")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 450) // 2
        y = (self.window.winfo_screenheight() - 550) // 2
        self.window.geometry(f"450x550+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Variables
        self.company = tk.StringVar()
        self.contact = tk.StringVar()
        self.phone = tk.StringVar()
        self.mobile = tk.StringVar()
        self.email = tk.StringVar()
        self.address = tk.StringVar()
        self.city = tk.StringVar()
        self.payment_terms = tk.StringVar()
        self.tax_number = tk.StringVar()
        self.opening_balance = tk.StringVar()
        self.notes = tk.StringVar()
        
        # If editing, load data
        if supplier_id:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute('''SELECT company_name, contact_person, phone, mobile, email, address, city, 
                               payment_terms, tax_number, opening_balance, notes 
                        FROM suppliers WHERE id=?''', (supplier_id,))
            data = c.fetchone()
            conn.close()
            
            if data:
                self.company.set(data[0])
                self.contact.set(data[1] or '')
                self.phone.set(data[2] or '')
                self.mobile.set(data[3] or '')
                self.email.set(data[4] or '')
                self.address.set(data[5] or '')
                self.city.set(data[6] or '')
                self.payment_terms.set(data[7] or '')
                self.tax_number.set(data[8] or '')
                self.opening_balance.set(str(data[9] or 0))
                self.notes.set(data[10] or '')
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title_color = '#27ae60' if 'Add' in self.window.title() else '#f39c12'
        title_frame = tk.Frame(self.window, bg=title_color, height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text=self.window.title(), fg='white', bg=title_color, 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Main frame
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=10, pady=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame, bg='#f9f9f9', highlightthickness=0, height=400)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f9f9f9')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Form fields
        row = 0
        padx_val = 5
        pady_val = 4
        
        fields = [
            ("Company Name *:", self.company),
            ("Contact Person:", self.contact),
            ("Phone:", self.phone),
            ("Mobile:", self.mobile),
            ("Email:", self.email),
            ("Address:", self.address),
            ("City:", self.city),
            ("Payment Terms:", self.payment_terms),
            ("Tax Number:", self.tax_number),
            ("Opening Balance (Rs.):", self.opening_balance),
            ("Notes:", self.notes),
        ]
        
        entries = []
        for i, (label, var) in enumerate(fields):
            tk.Label(scrollable_frame, text=label, font=('Arial', 9), bg='#f9f9f9').grid(
                row=row, column=0, padx=padx_val, pady=pady_val, sticky='e')
            entry = tk.Entry(scrollable_frame, textvariable=var, width=35, font=('Arial', 9), relief='solid', bd=1)
            entry.grid(row=row, column=1, padx=padx_val, pady=pady_val, sticky='w')
            entries.append(entry)
            row += 1
        
        # Note
        tk.Label(scrollable_frame, text="* Required field", fg='red', font=('Arial', 8), 
                bg='#f9f9f9').grid(row=row, column=0, columnspan=2, pady=2)
        row += 1
        
        # Buttons
        btn_frame = tk.Frame(scrollable_frame, bg='#f9f9f9')
        btn_frame.grid(row=row, column=0, columnspan=2, pady=5)
        
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)
        
        tk.Button(btn_frame, text="💾 Save", command=self.save, bg='#27ae60', fg='white', 
                 font=('Arial', 11, 'bold'), width=12, cursor='hand2').grid(row=0, column=1, padx=8)
        tk.Button(btn_frame, text="❌ Cancel", command=self.window.destroy, bg='#e74c3c', fg='white', 
                 font=('Arial', 11), width=12, cursor='hand2').grid(row=0, column=2, padx=8)
        
        # Setup Enter key navigation
        for j in range(len(entries)-1):
            setup_enter_navigation(entries[j], entries[j+1])
        if entries:
            setup_enter_navigation(entries[-1], self.save)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def save(self):
        company = self.company.get().strip()
        if not company:
            show_error("Company name is required")
            return
        
        try:
            opening_balance = float(self.opening_balance.get() or 0)
        except:
            opening_balance = 0
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if self.supplier_id:
            c.execute('''UPDATE suppliers 
                SET company_name=?, contact_person=?, phone=?, mobile=?, email=?, address=?,
                    city=?, payment_terms=?, tax_number=?, opening_balance=?, current_balance=?, notes=?
                WHERE id=?''',
              (company, self.contact.get(), self.phone.get(), self.mobile.get(), self.email.get(),
               self.address.get(), self.city.get(), self.payment_terms.get(), self.tax_number.get(),
               opening_balance, opening_balance, self.notes.get(), self.supplier_id))
            conn.commit()
            show_success("Supplier updated successfully!")
            self.window.destroy()
        else:
            c.execute('''INSERT INTO suppliers 
                (company_name, contact_person, phone, mobile, email, address, city, payment_terms, tax_number, opening_balance, current_balance, notes, created_date)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''',
              (company, self.contact.get(), self.phone.get(), self.mobile.get(), self.email.get(),
               self.address.get(), self.city.get(), self.payment_terms.get(), self.tax_number.get(),
               opening_balance, opening_balance, self.notes.get(), self.working_date))
            
            supplier_id = c.lastrowid
            conn.commit()
            
            # Create chart of account for this supplier
            self.create_supplier_account(supplier_id, company, opening_balance)
            
            show_success(f"Supplier {company} added successfully!\nAccount created under Accounts Payable")
            self.window.destroy()
        
        conn.close()
    
    def create_supplier_account(self, supplier_id, company_name, opening_balance):
        """Create a chart of account for the supplier under Accounts Payable"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            # Get the parent account ID for Accounts Payable (2-2100)
            c.execute("SELECT id FROM accounts WHERE account_code='2-2100'")
            parent = c.fetchone()
            if not parent:
                # Create Accounts Payable parent if it doesn't exist
                c.execute('''INSERT INTO accounts 
                            (account_code, account_name, account_type, parent_code, is_active)
                            VALUES ('2-2100', 'Accounts Payable', 'Liability', '2', 1)''')
                parent_id = c.lastrowid
            else:
                parent_id = parent[0]
            
            # Get the next available account code under 2-2100
            c.execute("SELECT account_code FROM accounts WHERE account_code LIKE '2-21%' ORDER BY account_code DESC LIMIT 1")
            last = c.fetchone()
            
            if last:
                last_num = int(last[0].split('-')[1])
                new_code = f"2-{last_num + 1:04d}"
            else:
                new_code = "2-2101"
            
            # Create the supplier's account
            c.execute('''INSERT INTO accounts 
                        (account_code, account_name, account_type, parent_id, parent_code, current_balance, is_active, created_date)
                        VALUES (?, ?, 'Liability', ?, '2-2100', ?, 1, ?)''',
                      (new_code, company_name, parent_id, opening_balance, self.working_date))
            
            account_id = c.lastrowid
            
            # Update supplier record with account_id
            c.execute("UPDATE suppliers SET account_id = ? WHERE id = ?", (account_id, supplier_id))
            
            conn.commit()
            print(f"✅ Created account for supplier {company_name}: {new_code} (Balance: {CURRENCY_SYMBOL}{opening_balance:.2f})")
            
        except Exception as e:
            print(f"❌ Error creating account for supplier: {e}")
            conn.rollback()
        finally:
            conn.close()

class SupplierManager:
    def __init__(self, parent, working_date=None):
        self.parent = parent
        self.working_date = working_date or datetime.now().strftime('%Y-%m-%d')
        print(f"Supplier Manager using date: {self.working_date}")
        # Load tax rate from database
        import sqlite3
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='tax_rate'")
            result = c.fetchone()
            if result:
                self.tax_rate = float(result[0]) / 100
                print(f"✅ PO Tax rate loaded from database: {result[0]}%")
            else:
                self.tax_rate = 0.17  # Default to 17% if not set
                print(f"ℹ️ No tax rate in database, using default: 17%")
            conn.close()
        except Exception as e:
            print(f"⚠️ Error loading tax rate: {e}")
            self.tax_rate = 0.17  # Fallback to 17% on error
        
        # Ensure returns table exists
        ensure_returns_table()
        
        self.window = tk.Toplevel(parent)
        self.window.title("Supplier Management")
        self.window.geometry("1000x800")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 800) // 2
        self.window.geometry(f"1000x800+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Bind mouse wheel
        self.window.bind_all("<MouseWheel>", self.on_mousewheel)
        
        self.create_widgets()
        self.load_suppliers()
        self.load_purchase_orders()
        self.load_reorder_alerts()
        self.load_purchase_orders_for_returns()  # Load POs for returns dropdown
    
    def on_mousewheel(self, event):
        widget = event.widget
        if isinstance(widget, tk.Canvas):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
        elif isinstance(widget, tk.Listbox):
            widget.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def create_widgets(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Suppliers
        self.suppliers_tab = tk.Frame(notebook)
        notebook.add(self.suppliers_tab, text="📋 Suppliers")
        self.create_suppliers_tab()
        
        # Tab 2: Purchase Orders
        self.po_tab = tk.Frame(notebook)
        notebook.add(self.po_tab, text="📦 Purchase Orders")
        self.create_po_tab()
        
        # Tab 3: New Purchase Order
        self.new_po_tab = tk.Frame(notebook)
        notebook.add(self.new_po_tab, text="➕ New Purchase Order")
        self.create_new_po_tab()
        
        # Tab 4: Reorder Alerts
        self.reorder_tab = tk.Frame(notebook)
        notebook.add(self.reorder_tab, text="⚠️ Reorder Alerts")
        self.create_reorder_tab()
        
        # Tab 5: Returns (New)
        self.returns_tab = tk.Frame(notebook)
        notebook.add(self.returns_tab, text="🔄 Returns")
        self.create_returns_tab()
    
    def create_suppliers_tab(self):
        # Title
        title_frame = tk.Frame(self.suppliers_tab, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📋 SUPPLIERS LIST", fg='white', bg='#3498db', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Search frame
        search_frame = tk.Frame(self.suppliers_tab, bg='#ecf0f1', height=60)
        search_frame.pack(fill=tk.X, padx=10, pady=10)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="🔍 Search:", bg='#ecf0f1', 
                font=('Arial', 11, 'bold')).place(x=20, y=10)
        
        tk.Label(search_frame, text="Name/Contact:", bg='#ecf0f1', 
                font=('Arial', 9)).place(x=20, y=35)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_suppliers())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, 
                                width=30, font=('Arial', 9), relief='solid', bd=1)
        search_entry.place(x=110, y=32, height=25)
        search_entry.bind('<Return>', lambda e: self.load_suppliers())
        
        tk.Button(search_frame, text="➕ Add Supplier", command=self.add_supplier, 
                 bg='#27ae60', fg='white', font=('Arial', 9), cursor='hand2'
                 ).place(x=500, y=28, width=120, height=28)
        
        tk.Button(search_frame, text="🔄 Refresh", command=self.load_suppliers, 
                 bg='#3498db', fg='white', font=('Arial', 9), cursor='hand2'
                 ).place(x=630, y=28, width=100, height=28)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.suppliers_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('ID', 'Company', 'Contact', 'Phone', 'Mobile', 'Email', 'City', 'Balance', 'Account')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        col_widths = {'ID': 40, 'Company': 150, 'Contact': 120, 'Phone': 90, 
                     'Mobile': 90, 'Email': 150, 'City': 80, 'Balance': 80, 'Account': 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_supplier())
        
        # Button Frame
        btn_frame = tk.Frame(self.suppliers_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 140, 260, 380, 500]
        
        tk.Button(btn_frame, text="✏️ Edit", command=self.edit_supplier, 
                 bg='#f39c12', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[0], y=10)
        
        tk.Button(btn_frame, text="❌ Delete", command=self.delete_supplier, 
                 bg='#e74c3c', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[1], y=10)
        
        tk.Button(btn_frame, text="📦 Products", command=self.view_supplier_products, 
                 bg='#3498db', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[2], y=10)
        
        tk.Button(btn_frame, text="🔄 New PO", command=self.create_po_for_supplier, 
                 bg='#27ae60', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[3], y=10)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_suppliers, 
                 bg='#3498db', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[4], y=10)
    
    def create_po_tab(self):
        # Title
        title_frame = tk.Frame(self.po_tab, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📦 PURCHASE ORDERS", fg='white', bg='#f39c12', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.po_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('PO #', 'Date', 'Supplier', 'Expected', 'Status', 'Total')
        self.po_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                     yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=12)
        
        vsb.config(command=self.po_tree.yview)
        hsb.config(command=self.po_tree.xview)
        
        col_widths = {'PO #': 100, 'Date': 90, 'Supplier': 150, 'Expected': 90, 
                     'Status': 80, 'Total': 80}
        
        for col in columns:
            self.po_tree.heading(col, text=col)
            self.po_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.po_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.po_tree.bind('<Double-Button-1>', self.view_purchase_order)
        
        # Button Frame
        btn_frame = tk.Frame(self.po_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 150, 280, 410]
        
        tk.Button(btn_frame, text="👁️ View", command=self.view_purchase_order, 
                 bg='#3498db', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[0], y=10)
        
        tk.Button(btn_frame, text="✅ Received", command=self.mark_po_received, 
                 bg='#27ae60', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[1], y=10)
        
        tk.Button(btn_frame, text="❌ Cancel", command=self.cancel_po, 
                 bg='#e74c3c', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=btn_x[2], y=10)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_purchase_orders, 
                 bg='#3498db', fg='white', font=('Arial', 10), width=12, cursor='hand2'
                 ).place(x=530, y=10)
    
    def create_new_po_tab(self):
        # Title
        title_frame = tk.Frame(self.new_po_tab, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="➕ CREATE PURCHASE ORDER", fg='white', bg='#27ae60', 
                font=('Arial', 14, 'bold')).pack(expand=True)
    
        # Main frame
        main_frame = tk.Frame(self.new_po_tab, bg='#f9f9f9', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
    
        # ===== TOP SECTION: Supplier + PO Info side by side =====
        top_frame = tk.Frame(main_frame, bg='#f9f9f9')
        top_frame.pack(fill=tk.X, pady=5)
    
        # Left side - Supplier selection
        supplier_frame = tk.Frame(top_frame, bg='#f9f9f9')
        supplier_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
        tk.Label(supplier_frame, text="Select Supplier:", font=('Arial', 10, 'bold'), 
                 bg='#f9f9f9').pack(side=tk.LEFT)
        self.po_supplier_var = tk.StringVar()
        self.po_supplier_combo = ttk.Combobox(supplier_frame, textvariable=self.po_supplier_var, 
                                              width=40, font=('Arial', 9))
        self.po_supplier_combo.pack(side=tk.LEFT, padx=10)
    
        # Right side - PO Number and Expected Date
        po_info_frame = tk.Frame(top_frame, bg='#ecf0f1', relief='groove', bd=1)
        po_info_frame.pack(side=tk.RIGHT, padx=5)
    
        # Generate unique PO number
        today = self.working_date.replace('-', '')
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM purchase_orders WHERE po_number LIKE ?", (f'PO-{today}%',))
        count = c.fetchone()[0] + 1
        conn.close()
        po_number = f"PO-{today}-{count:03d}"
    
        self.po_number_var = tk.StringVar(value=po_number)
    
        tk.Label(po_info_frame, text="PO Number:", font=('Arial', 9, 'bold'), 
                 bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        tk.Label(po_info_frame, textvariable=self.po_number_var, font=('Arial', 9, 'bold'),
                 bg='#ecf0f1', fg='#27ae60').pack(side=tk.LEFT, padx=2)
    
        tk.Label(po_info_frame, text="| Expected:", font=('Arial', 9, 'bold'),
                 bg='#ecf0f1').pack(side=tk.LEFT, padx=(10,2))
    
        working_date_obj = datetime.strptime(self.working_date, '%Y-%m-%d')
        self.po_date_var = tk.StringVar(value=(working_date_obj + timedelta(days=7)).strftime('%Y-%m-%d'))
        date_entry = tk.Entry(po_info_frame, textvariable=self.po_date_var, width=12, 
                             font=('Arial', 9), relief='solid', bd=1)
        date_entry.pack(side=tk.LEFT, padx=5)
    
        self.load_suppliers_for_po()
    
        # ===== SEARCH SECTION =====
        search_frame = tk.Frame(main_frame, bg='#f9f9f9')
        search_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(search_frame, text="🔍 Search Product:", font=('Arial', 10, 'bold'), 
                 bg='#f9f9f9').pack(side=tk.LEFT)
    
        self.product_search_var = tk.StringVar()
        self.product_search_entry = tk.Entry(search_frame, textvariable=self.product_search_var,
                                            width=50, font=('Arial', 10), relief='solid', bd=1)
        self.product_search_entry.pack(side=tk.LEFT, padx=5)
        self.product_search_entry.bind('<KeyRelease>', self.on_product_search_key)
        self.product_search_entry.bind('<Return>', self.select_first_product)
    
        # Quick quantity buttons
        qty_frame = tk.Frame(main_frame, bg='#f9f9f9')
        qty_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(qty_frame, text="Quick Qty:", font=('Arial', 9, 'bold'), 
                 bg='#f9f9f9').pack(side=tk.LEFT, padx=5)
    
        for qty in [5, 10, 20, 50, 100]:
            tk.Button(qty_frame, text=str(qty), command=lambda q=qty: self.set_quick_qty(q),
                     bg='#3498db', fg='white', font=('Arial', 8), width=4, cursor='hand2').pack(side=tk.LEFT, padx=2)
    
        # Selected product preview
        self.selected_product_frame = tk.Frame(main_frame, bg='#ecf0f1', relief=tk.GROOVE, bd=1, height=50)
        self.selected_product_frame.pack(fill=tk.X, pady=5)
        self.selected_product_frame.pack_propagate(False)
    
        self.selected_product_label = tk.Label(self.selected_product_frame, 
                                              text="👆 Type product name to search",
                                              bg='#ecf0f1', font=('Arial', 10, 'italic'))
        self.selected_product_label.pack(expand=True)
    
        # Add button
        add_btn_frame = tk.Frame(main_frame, bg='#f9f9f9')
        add_btn_frame.pack(fill=tk.X, pady=5)
    
        tk.Button(add_btn_frame, text="➕ Add to PO", command=self.add_searched_product_to_po,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 width=20, height=1, cursor='hand2').pack()
    
        # Products tree (MORE SPACE NOW!)
        tree_frame = tk.Frame(main_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
        columns = ('ID', 'Product', 'Stock', 'Cost', 'Quantity', 'Total')
        self.po_products_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
    
        col_widths = {'ID': 40, 'Product': 350, 'Stock': 60, 'Cost': 80, 'Quantity': 80, 'Total': 100}
    
        for col in columns:
            self.po_products_tree.heading(col, text=col)
            self.po_products_tree.column(col, width=col_widths.get(col, 70), anchor='center')
    
        self.po_products_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.po_products_tree.yview)
        self.po_products_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
        # Remove button
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=5)
    
        tk.Button(btn_frame, text="❌ Remove Selected", command=self.remove_po_product, 
                 bg='#e74c3c', fg='white', font=('Arial', 9), width=15, cursor='hand2').pack()
    
        # Totals
        total_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='groove', bd=1)
        total_frame.pack(fill=tk.X, pady=5)
    
        total_inner = tk.Frame(total_frame, bg='#ecf0f1', padx=15, pady=8)
        total_inner.pack()
    
        tk.Label(total_inner, text="Subtotal:", font=('Arial', 10), bg='#ecf0f1').pack(side=tk.LEFT)
        self.po_subtotal = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 10, 'bold'), 
                                    bg='#ecf0f1', fg='#27ae60', width=12)
        self.po_subtotal.pack(side=tk.LEFT, padx=5)
    
        tk.Label(total_inner, text="Tax (17%):", font=('Arial', 10), bg='#ecf0f1').pack(side=tk.LEFT, padx=(20,0))
        self.po_tax = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 10, 'bold'), 
                               bg='#ecf0f1', fg='#e67e22', width=12)
        self.po_tax.pack(side=tk.LEFT, padx=5)
    
        tk.Label(total_inner, text="Total:", font=('Arial', 12, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=(20,0))
        self.po_total = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 12, 'bold'), 
                                 bg='#ecf0f1', fg='#2980b9', width=12)
        self.po_total.pack(side=tk.LEFT, padx=5)
    
        # Notes
        notes_frame = tk.Frame(main_frame)
        notes_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(notes_frame, text="Notes:", font=('Arial', 9)).pack(anchor='w')
        self.po_notes = tk.Text(notes_frame, height=2, width=60, font=('Arial', 9), relief='solid', bd=1)
        self.po_notes.pack(fill=tk.X)
    
        # Create button
        tk.Button(main_frame, text="📝 Create Purchase Order", command=self.create_purchase_order, 
                 bg='#27ae60', fg='white', font=('Arial', 12, 'bold'), 
                 width=25, height=1, cursor='hand2').pack(pady=10)
    
        # Initialize variables for search
        self.search_results = []
        self.selected_product_id = None
        self.selected_product_name = None
        self.selected_product_cost = 0
        self.selected_product_stock = 0
        self.quick_qty = 0

    def create_reorder_tab(self):
        # Title
        title_frame = tk.Frame(self.reorder_tab, bg='#e74c3c', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="⚠️ REORDER ALERTS", fg='white', bg='#e74c3c', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.reorder_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('ID', 'Product', 'Stock', 'Reorder Level', 'Supplier', 'Contact', 'Last Order')
        self.reorder_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                          yscrollcommand=vsb.set, height=12)
        vsb.config(command=self.reorder_tree.yview)
        
        col_widths = {'ID': 40, 'Product': 180, 'Stock': 80, 'Reorder Level': 80, 
                     'Supplier': 150, 'Contact': 120, 'Last Order': 90}
        
        for col in columns:
            self.reorder_tree.heading(col, text=col)
            self.reorder_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.reorder_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button Frame
        btn_frame = tk.Frame(self.reorder_tab, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        btn_frame.pack_propagate(False)
        
        btn_x = [20, 170, 320]
        
        tk.Button(btn_frame, text="📦 Create PO", command=self.create_po_from_reorder, 
                 bg='#27ae60', fg='white', font=('Arial', 10), width=15, cursor='hand2'
                 ).place(x=btn_x[0], y=10)
        
        tk.Button(btn_frame, text="📊 Update Level", command=self.update_reorder_level, 
                 bg='#f39c12', fg='white', font=('Arial', 10), width=15, cursor='hand2'
                 ).place(x=btn_x[1], y=10)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_reorder_alerts, 
                 bg='#3498db', fg='white', font=('Arial', 10), width=15, cursor='hand2'
                 ).place(x=btn_x[2], y=10)
        
        self.load_reorder_alerts()
    
    def create_returns_tab(self):
        """Create returns management tab"""
        # Title
        title_frame = tk.Frame(self.returns_tab, bg='#e67e22', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="🔄 PRODUCT RETURNS", fg='white', bg='#e67e22', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Main frame
        main_frame = tk.Frame(self.returns_tab, bg='#f9f9f9', padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # PO Selection
        po_frame = tk.LabelFrame(main_frame, text="Select Purchase Order", font=('Arial', 11, 'bold'),
                                 padx=10, pady=10)
        po_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(po_frame, text="PO Number:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.return_po_var = tk.StringVar()
        self.return_po_combo = ttk.Combobox(po_frame, textvariable=self.return_po_var, width=30, font=('Arial', 10))
        self.return_po_combo.pack(side=tk.LEFT, padx=5)
        self.load_purchase_orders_for_returns()  # Load POs for returns dropdown
        tk.Button(po_frame, text="🔍 Load Items", command=self.load_po_for_return,
                 bg='#3498db', fg='white', font=('Arial', 9), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Items frame
        items_frame = tk.LabelFrame(main_frame, text="Items to Return", font=('Arial', 11, 'bold'),
                                    padx=10, pady=10)
        items_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Treeview for items
        tree_frame = tk.Frame(items_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('Select', 'Product', 'Ordered', 'Cost', 'Return Qty', 'Reason')
        self.return_items_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                               yscrollcommand=vsb.set, height=8)
        vsb.config(command=self.return_items_tree.yview)
        
        col_widths = {'Select': 40, 'Product': 200, 'Ordered': 60, 'Cost': 70, 'Return Qty': 70, 'Reason': 150}
        
        for col in columns:
            self.return_items_tree.heading(col, text=col)
            self.return_items_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.return_items_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Reason combobox values
        self.reason_values = ['Damaged in transit', 'Wrong item sent', 'Expired product', 
                              'Over-shipment', 'Quality issue', 'Customer return', 'Other']
        
        # Bind double-click to set return quantity
        self.return_items_tree.bind('<Double-Button-1>', self.set_return_quantity)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg='#ecf0f1', height=50)
        btn_frame.pack(fill=tk.X, pady=10)
        btn_frame.pack_propagate(False)
        
        tk.Button(btn_frame, text="✅ Process Return", command=self.process_return,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, cursor='hand2').place(x=20, y=10)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.refresh_returns_tab,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 width=12, cursor='hand2').place(x=180, y=10)
        
        # Returns history
        history_frame = tk.LabelFrame(main_frame, text="Returns History", font=('Arial', 11, 'bold'),
                                      padx=10, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        hist_tree_frame = tk.Frame(history_frame)
        hist_tree_frame.pack(fill=tk.BOTH, expand=True)
        
        vsb2 = ttk.Scrollbar(hist_tree_frame, orient="vertical")
        
        columns2 = ('Date', 'PO #', 'Product', 'Qty', 'Reason', 'By')
        self.returns_history_tree = ttk.Treeview(hist_tree_frame, columns=columns2, show='headings',
                                                  yscrollcommand=vsb2.set, height=5)
        vsb2.config(command=self.returns_history_tree.yview)
        
        col_widths2 = {'Date': 90, 'PO #': 100, 'Product': 180, 'Qty': 50, 'Reason': 120, 'By': 80}
        
        for col in columns2:
            self.returns_history_tree.heading(col, text=col)
            self.returns_history_tree.column(col, width=col_widths2.get(col, 80), anchor='center')
        
        self.returns_history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb2.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Load returns history
        self.load_return_history()
    
    def load_suppliers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if search:
            c.execute('''SELECT s.id, s.company_name, s.contact_person, s.phone, s.mobile, s.email, s.city, s.current_balance, a.account_code 
                         FROM suppliers s
                         LEFT JOIN accounts a ON s.account_id = a.id
                         WHERE s.company_name LIKE ? OR s.contact_person LIKE ? OR s.phone LIKE ? OR s.city LIKE ?
                         ORDER BY s.company_name''', 
                      (f'%{search}%', f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            c.execute('''SELECT s.id, s.company_name, s.contact_person, s.phone, s.mobile, s.email, s.city, s.current_balance, a.account_code 
                         FROM suppliers s
                         LEFT JOIN accounts a ON s.account_id = a.id
                         ORDER BY s.company_name''')
        
        suppliers = c.fetchall()
        conn.close()
        
        for s in suppliers:
            self.tree.insert('', tk.END, values=(s[0], s[1], s[2], s[3], s[4], s[5], s[6], f"{CURRENCY_SYMBOL}{s[7]:.2f}", s[8] or ''))
    
    def load_suppliers_for_po(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, company_name FROM suppliers ORDER BY company_name")
        suppliers = c.fetchall()
        conn.close()
    
        supplier_list = [f"{s[1]} (ID: {s[0]})" for s in suppliers]
        self.po_supplier_combo['values'] = supplier_list
        if supplier_list:
            self.po_supplier_combo.current(0)

    # ===== ADD ALL NEW METHODS HERE =====
    def on_product_search_key(self, event):
        """Handle key release in search field - smooth typing with delay"""
        search_term = self.product_search_var.get().strip()
    
        # Cancel previous scheduled search if any
        if hasattr(self, '_search_after_id'):
            self.window.after_cancel(self._search_after_id)
    
        # Don't search for very short terms
        if len(search_term) < 3:
            if len(search_term) == 0:
                self.selected_product_label.config(text="👆 Type product name to search")
            else:
                self.selected_product_label.config(text=f"🔍 Type {3 - len(search_term)} more characters...")
            self.search_results = []
            self.selected_product_id = None
            return
    
        # Schedule search with delay (300ms) to allow typing
        self._search_after_id = self.window.after(300, lambda: self._perform_search(search_term))

    def _perform_search(self, search_term):
        """Perform the actual product search with prioritization"""
        # Search products with more precise matching
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        # First try exact word matching with prioritization
        c.execute('''
            SELECT id, name, cost_price, stock 
            FROM products 
            WHERE name LIKE ? OR name LIKE ? OR barcode LIKE ?
            ORDER BY 
                CASE 
                    WHEN name LIKE ? THEN 1  -- Starts with search term (highest priority)
                    WHEN name LIKE ? THEN 2  -- Word starts with search term
                    WHEN name LIKE ? THEN 3  -- Contains search term
                    ELSE 4
                END,
                name
            LIMIT 15
        ''', (
            f'{search_term}%',              # Starts with
            f'% {search_term}%',             # Word starts with (space + term)
            f'%{search_term}%',               # Contains anywhere
            f'{search_term}%',                # For CASE
            f'% {search_term}%',               # For CASE
            f'%{search_term}%'                  # For CASE
        ))

        self.search_results = c.fetchall()
        conn.close()

        if not self.search_results:
            self.selected_product_label.config(text=f"❌ No products found matching '{search_term}'")
            self.selected_product_id = None
            return

        # Update preview with first result
        first = self.search_results[0]
        self.selected_product_id = first[0]
        self.selected_product_name = first[1]
        self.selected_product_cost = first[2]
        self.selected_product_stock = first[3]
    
        self.selected_product_label.config(
            text=f"✓ {self.selected_product_name} | Cost: {CURRENCY_SYMBOL}{self.selected_product_cost:.2f} | Stock: {self.selected_product_stock}"
        )

        # Create popup menu with all matches
        popup = tk.Menu(self.window, tearoff=0)
    
        for prod in self.search_results:
            prod_id, name, cost, stock = prod
            display = f"{name} - Rs.{cost:.0f} (Stock: {stock})"
            popup.add_command(
                label=display,
                command=lambda p=prod: self.select_search_result(p)
            )
    
        # Show popup near the search entry
        try:
            popup.tk_popup(
                self.product_search_entry.winfo_rootx(),
                self.product_search_entry.winfo_rooty() + 25
            )
        finally:
            popup.grab_release()

    def select_search_result(self, product):
        """Select a product from search results"""
        self.selected_product_id = product[0]
        self.selected_product_name = product[1]
        self.selected_product_cost = product[2]
        self.selected_product_stock = product[3]
    
        self.selected_product_label.config(
            text=f"✓ {self.selected_product_name} | Cost: {CURRENCY_SYMBOL}{self.selected_product_cost:.2f} | Stock: {self.selected_product_stock}"
        )

    def select_first_product(self, event):
        """Select first product when Enter is pressed"""
        if self.search_results:
            self.select_search_result(self.search_results[0])
            self.add_searched_product_to_po()

    def set_quick_qty(self, qty):
        """Set quick quantity and add product"""
        self.quick_qty = qty
        if self.selected_product_id:
            self.add_searched_product_to_po()

    def add_searched_product_to_po(self):
        """Add the selected product to PO with quick quantity"""
        if not self.selected_product_id:
            messagebox.showwarning("Warning", "Please search and select a product first")
            return

        # Use quick_qty if set, otherwise prompt
        if self.quick_qty > 0:
            qty = self.quick_qty
            self.quick_qty = 0  # Reset
        else:
            qty = simpledialog.askinteger("Quantity", 
                                          f"Enter quantity for {self.selected_product_name}:",
                                          parent=self.window, minvalue=1, initialvalue=1)
            if not qty:
                return

        # Check if product already in PO
        for item in self.po_products_tree.get_children():
            values = self.po_products_tree.item(item)['values']
            if values[0] == self.selected_product_id:
                # Update quantity
                current_qty = values[4]
                new_qty = current_qty + qty
                total = self.selected_product_cost * new_qty
                self.po_products_tree.item(item, values=(
                    self.selected_product_id,
                    self.selected_product_name,
                    self.selected_product_stock,
                    f"{CURRENCY_SYMBOL}{self.selected_product_cost:.2f}",
                    new_qty,
                    f"{CURRENCY_SYMBOL}{total:.2f}"
                ))
                self.calculate_po_totals()
                self.product_search_entry.delete(0, tk.END)
                self.product_search_entry.focus_set()
                self.selected_product_label.config(text="👆 Type product name to search")
                return

        # Add new item
        total = self.selected_product_cost * qty
        self.po_products_tree.insert('', tk.END, values=(
            self.selected_product_id,
            self.selected_product_name,
            self.selected_product_stock,
            f"{CURRENCY_SYMBOL}{self.selected_product_cost:.2f}",
            qty,
            f"{CURRENCY_SYMBOL}{total:.2f}"
        ))

        self.calculate_po_totals()

        # Clear search
        self.product_search_entry.delete(0, tk.END)
        self.product_search_entry.focus_set()
        self.selected_product_label.config(text="👆 Type product name to search")    
    # ===== END NEW METHODS =====
 
    def load_purchase_orders(self):
        for row in self.po_tree.get_children():
            self.po_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT po_number, order_date, supplier_name, expected_date, status, total 
                     FROM purchase_orders ORDER BY id DESC LIMIT 100''')
        pos = c.fetchall()
        conn.close()
        
        for po in pos:
            self.po_tree.insert('', tk.END, values=(po[0], po[1], po[2], po[3], po[4], f"{CURRENCY_SYMBOL}{po[5]:.2f}"))
    
    def load_reorder_alerts(self):
        for row in self.reorder_tree.get_children():
            self.reorder_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT p.id, p.name, p.stock, p.reorder_level, s.company_name, s.contact_person,
                            (SELECT MAX(order_date) FROM purchase_orders WHERE supplier_id = p.supplier_id) as last_order
                     FROM products p
                     LEFT JOIN suppliers s ON p.supplier_id = s.id
                     WHERE p.stock <= p.reorder_level
                     ORDER BY (p.stock * 1.0 / p.reorder_level)''')
        alerts = c.fetchall()
        conn.close()
        
        for a in alerts:
            self.reorder_tree.insert('', tk.END, values=a)
    
    def load_po_for_return(self):
        """Load items from selected PO for return"""
        po_sel = self.return_po_combo.get()
        if not po_sel:
            return
        
        for row in self.return_items_tree.get_children():
            self.return_items_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get PO ID
        c.execute("SELECT id FROM purchase_orders WHERE po_number=?", (po_sel,))
        po_result = c.fetchone()
        if not po_result:
            conn.close()
            return
        
        po_id = po_result[0]
        
        # Get items from this PO
        c.execute('''SELECT pi.product_id, pi.product_name, pi.quantity, pi.unit_cost
                     FROM po_items pi
                     WHERE pi.po_id=?''', (po_id,))
        items = c.fetchall()
        conn.close()
        
        for item in items:
            prod_id, prod_name, qty, cost = item
            self.return_items_tree.insert('', tk.END, iid=f"RET_{prod_id}", values=(
                '☐', prod_name, qty, f"{CURRENCY_SYMBOL}{cost:.2f}", 0, 'Select reason'
            ))
    
    def set_return_quantity(self, event):
        """Set return quantity for selected item"""
        selected = self.return_items_tree.selection()
        if not selected:
            return
        
        item = selected[0]
        values = self.return_items_tree.item(item)['values']
        prod_name = values[1]
        max_qty = values[2]
        
        # Get return quantity
        qty = simpledialog.askinteger("Return Quantity", 
                                      f"Enter quantity to return for {prod_name} (max {max_qty}):",
                                      parent=self.window, minvalue=1, maxvalue=max_qty)
        if not qty:
            return
        
        # Get reason
        reason_dialog = tk.Toplevel(self.window)
        reason_dialog.title("Select Reason")
        reason_dialog.geometry("300x150")
        reason_dialog.transient(self.window)
        reason_dialog.grab_set()
        
        tk.Label(reason_dialog, text="Select return reason:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        reason_var = tk.StringVar()
        reason_combo = ttk.Combobox(reason_dialog, textvariable=reason_var, 
                                    values=self.reason_values, width=25)
        reason_combo.pack(pady=5)
        reason_combo.set('Damaged in transit')
        
        def confirm():
            reason = reason_var.get()
            if reason:
                # Update the tree
                self.return_items_tree.set(item, 'Select', '☑')
                self.return_items_tree.set(item, 'Return Qty', qty)
                self.return_items_tree.set(item, 'Reason', reason)
                reason_dialog.destroy()
        
        tk.Button(reason_dialog, text="Confirm", command=confirm,
                 bg='#27ae60', fg='white', width=10).pack(pady=10)
    
    def process_return(self):
        """Process the returns"""
        items_to_return = []
        for item in self.return_items_tree.get_children():
            values = self.return_items_tree.item(item)['values']
            if values[0] == '☑' and values[4] > 0:  # Selected and quantity > 0
                items_to_return.append({
                    'item_id': item.replace('RET_', ''),
                    'product': values[1],
                    'qty': values[4],
                    'reason': values[5]
                })
        
        if not items_to_return:
            show_error("No items selected for return")
            return
        
        po_sel = self.return_po_combo.get()
        if not po_sel:
            show_error("Please select a PO")
            return
        
        if not ask_yes_no(f"Process return for {len(items_to_return)} item(s)?"):
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get PO ID
        c.execute("SELECT id FROM purchase_orders WHERE po_number=?", (po_sel,))
        po_id = c.fetchone()[0]
        
        try:
            c.execute("BEGIN TRANSACTION")
            
            for ret in items_to_return:
                prod_id = int(ret['item_id'])
                qty = ret['qty']
                reason = ret['reason']
                
                # Insert return record
                c.execute('''INSERT INTO po_returns 
                            (po_id, product_id, return_date, quantity, reason, returned_by)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (po_id, prod_id, self.working_date, qty, reason, 'admin'))
                
                # Get product cost
                c.execute("SELECT cost_price FROM products WHERE id=?", (prod_id,))
                cost = c.fetchone()[0]
                return_value = cost * qty
                
                # Decrease stock
                c.execute("UPDATE products SET stock = stock - ? WHERE id=?", (qty, prod_id))
                
                # Get supplier ID and account
                c.execute("SELECT supplier_id FROM purchase_orders WHERE id=?", (po_id,))
                supplier_id = c.fetchone()[0]
                
                c.execute("SELECT account_id FROM suppliers WHERE id=?", (supplier_id,))
                supplier_account = c.fetchone()
                
                # Update supplier balance (decrease what you owe)
                c.execute("UPDATE suppliers SET current_balance = current_balance - ? WHERE id=?", 
                         (return_value, supplier_id))
                
                # Update Accounts Payable (accounting entry)
                if supplier_account and supplier_account[0]:
                    c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                             (return_value, supplier_account[0]))
                
                # Create accounting entry (reverse of purchase)
                c.execute("SELECT id FROM accounts WHERE account_code='1200'")  # Inventory
                inv_account = c.fetchone()
                c.execute("SELECT id FROM accounts WHERE account_code='2000'")  # Accounts Payable
                ap_account = c.fetchone()
                
                if inv_account and ap_account:
                    # This would need a voucher system integration
                    pass
            
            conn.commit()
            show_success(f"Return processed successfully!\n{len(items_to_return)} item(s) returned.")
            
            # Clear selections
            for item in self.return_items_tree.get_children():
                self.return_items_tree.delete(item)
            self.return_po_combo.set('')
            
            # Refresh
            self.load_return_history()
            self.load_purchase_orders()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error processing return: {e}")
        finally:
            conn.close()
    
    def load_return_history(self):
        """Load returns history"""
        for row in self.returns_history_tree.get_children():
            self.returns_history_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT pr.return_date, po.po_number, p.name, pr.quantity, pr.reason, pr.returned_by
                     FROM po_returns pr
                     JOIN purchase_orders po ON pr.po_id = po.id
                     JOIN products p ON pr.product_id = p.id
                     ORDER BY pr.return_date DESC LIMIT 50''')
        returns = c.fetchall()
        conn.close()
        
        for r in returns:
            self.returns_history_tree.insert('', tk.END, values=r)
    
    def add_supplier(self):
        AddEditSupplier(self.window, "Add Supplier", working_date=self.working_date)
        self.load_suppliers()
        self.load_suppliers_for_po()
    
    def edit_supplier(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a supplier first")
            return
        
        supplier_id = self.tree.item(selected[0])['values'][0]
        AddEditSupplier(self.window, "Edit Supplier", supplier_id, self.working_date)
        self.load_suppliers()
        self.load_suppliers_for_po()
    
    def delete_supplier(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a supplier first")
            return
        
        supplier_id = self.tree.item(selected[0])['values'][0]
        supplier_name = self.tree.item(selected[0])['values'][1]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Check if supplier has products
        c.execute("SELECT COUNT(*) FROM products WHERE supplier_id=?", (supplier_id,))
        product_count = c.fetchone()[0]
        
        # Check if supplier has purchase orders
        c.execute("SELECT COUNT(*) FROM purchase_orders WHERE supplier_id=?", (supplier_id,))
        po_count = c.fetchone()[0]
        
        if product_count > 0 or po_count > 0:
            show_error(f"Cannot delete {supplier_name}. They have {product_count} products and {po_count} purchase orders.")
            conn.close()
            return
        
        # Get account_id before deleting supplier
        c.execute("SELECT account_id FROM suppliers WHERE id=?", (supplier_id,))
        account_id = c.fetchone()
        
        if ask_yes_no(f"Delete supplier {supplier_name}?"):
            # Delete the supplier
            c.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
            
            # Deactivate the account (don't delete for audit trail)
            if account_id and account_id[0]:
                c.execute("UPDATE accounts SET is_active=0 WHERE id=?", (account_id[0],))
            
            conn.commit()
            show_success(f"Supplier {supplier_name} deleted and account deactivated")
        
        conn.close()
        self.load_suppliers()
        self.load_suppliers_for_po()
    
    def view_supplier_products(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a supplier first")
            return
        
        supplier_id = self.tree.item(selected[0])['values'][0]
        supplier_name = self.tree.item(selected[0])['values'][1]
        
        win = tk.Toplevel(self.window)
        win.title(f"Products from {supplier_name}")
        win.geometry("600x400")
        
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 600) // 2
        y = (win.winfo_screenheight() - 400) // 2
        win.geometry(f"600x400+{x}+{y}")
        
        win.grab_set()
        win.transient(self.window)
        
        title_frame = tk.Frame(win, bg='#3498db', height=35)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text=f"📦 Products: {supplier_name}", fg='white', bg='#3498db', 
                font=('Arial', 12, 'bold')).pack(expand=True)
        
        tree_frame = tk.Frame(win)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('ID', 'Barcode', 'Product', 'Price', 'Cost', 'Stock')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', yscrollcommand=vsb.set, height=12)
        vsb.config(command=tree.yview)
        
        col_widths = {'ID': 40, 'Barcode': 100, 'Product': 180, 'Price': 70, 'Cost': 70, 'Stock': 50}
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=col_widths.get(col, 70), anchor='center')
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT id, barcode, name, price, cost_price, stock 
                     FROM products WHERE supplier_id=?''', (supplier_id,))
        products = c.fetchall()
        conn.close()
        
        for p in products:
            tree.insert('', tk.END, values=(p[0], p[1], p[2], f"{CURRENCY_SYMBOL}{p[3]:.2f}", 
                                           f"{CURRENCY_SYMBOL}{p[4]:.2f}", p[5]))
        
        tk.Button(win, text="❌ Close", command=win.destroy, bg='#3498db', fg='white', 
                 font=('Arial', 10), cursor='hand2').pack(pady=5)
    
    def create_po_for_supplier(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a supplier first")
            return
        
        supplier_id = self.tree.item(selected[0])['values'][0]
        supplier_name = self.tree.item(selected[0])['values'][1]
        
        self.po_supplier_combo.set(f"{supplier_name} (ID: {supplier_id})")
        self.load_supplier_products()
        
        notebook = self.window.children['!notebook']
        notebook.select(2)
    
    def load_supplier_products(self):
        selection = self.po_supplier_combo.get()
        if not selection or '(ID: ' not in selection:
            show_error("Select a supplier first")
            return
        
        supplier_id = int(selection.split('(ID: ')[1].rstrip(')'))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT id, name, stock, cost_price FROM products WHERE supplier_id=? ORDER BY name''', (supplier_id,))
        products = c.fetchall()
        conn.close()
        
        for row in self.po_products_tree.get_children():
            self.po_products_tree.delete(row)
        
        for p in products:
            self.po_products_tree.insert('', tk.END, values=(p[0], p[1], p[2], f"{CURRENCY_SYMBOL}{p[3]:.2f}", 0, f"{CURRENCY_SYMBOL}0.00"))
    
    def add_po_product(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, name, cost_price FROM products ORDER BY name")
        products = c.fetchall()
        conn.close()
        
        if not products:
            show_error("No products available")
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Select Product")
        dialog.geometry("400x200")
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f"400x200+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        title_frame = tk.Frame(dialog, bg='#27ae60', height=30)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="➕ SELECT PRODUCT", fg='white', bg='#27ae60', 
                font=('Arial', 11, 'bold')).pack(expand=True)
        
        listbox = tk.Listbox(dialog, font=('Arial', 10))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for p in products:
            listbox.insert(tk.END, f"{p[1]} - {CURRENCY_SYMBOL}{p[2]:.2f}")
        
        def select():
            sel = listbox.curselection()
            if sel:
                prod_id, prod_name, cost = products[sel[0]]
                dialog.destroy()
                
                for item in self.po_products_tree.get_children():
                    if self.po_products_tree.item(item)['values'][0] == prod_id:
                        show_error("Product already in list")
                        return
                
                self.po_products_tree.insert('', tk.END, values=(prod_id, prod_name, 0, f"{CURRENCY_SYMBOL}{cost:.2f}", 0, f"{CURRENCY_SYMBOL}0.00"))
        
        listbox.bind('<Double-Button-1>', lambda e: select())
        tk.Button(dialog, text="✅ Select", command=select, bg='#27ae60', fg='white', 
                 font=('Arial', 10), cursor='hand2').pack(pady=5)
    
    def remove_po_product(self):
        selected = self.po_products_tree.selection()
        if selected:
            self.po_products_tree.delete(selected[0])
            self.calculate_po_totals()
    
    def set_po_quantity(self):
        selected = self.po_products_tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        item = selected[0]
        values = self.po_products_tree.item(item)['values']
        prod_id = values[0]
        prod_name = values[1]
        current_qty = values[4]
        
        qty = simpledialog.askinteger("Quantity", f"Enter quantity for {prod_name}:", 
                                     parent=self.window, minvalue=1, initialvalue=current_qty or 1)
        if qty:
            cost_str = values[3].replace(CURRENCY_SYMBOL, '').strip()
            cost = float(cost_str)
            total = cost * qty
            
            self.po_products_tree.item(item, values=(prod_id, prod_name, 0, f"{CURRENCY_SYMBOL}{cost:.2f}", qty, f"{CURRENCY_SYMBOL}{total:.2f}"))
            self.calculate_po_totals()
    
    def calculate_po_totals(self):
        subtotal = 0
        for item in self.po_products_tree.get_children():
            values = self.po_products_tree.item(item)['values']
            total_str = values[5].replace(CURRENCY_SYMBOL, '').strip()
            subtotal += float(total_str)
        
        tax = subtotal * self.tax_rate
        total = subtotal + tax
        
        self.po_subtotal.config(text=f"{CURRENCY_SYMBOL}{subtotal:.2f}")
        self.po_tax.config(text=f"{CURRENCY_SYMBOL}{tax:.2f}")
        self.po_total.config(text=f"{CURRENCY_SYMBOL}{total:.2f}")
    
    def load_purchase_orders_for_returns(self):
        """Load received POs for returns dropdown"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT po_number FROM purchase_orders WHERE status='Received' ORDER BY po_number DESC")
        pos = c.fetchall()
    
        # DEBUG: Print what was found
        print("=" * 50)
        print("DEBUG - Loading POs for Returns Dropdown")
        print(f"Found {len(pos)} received POs:")
        for po in pos:
            print(f"  - {po[0]}")
    
        conn.close()
    
        po_list = [po[0] for po in pos]
        self.return_po_combo['values'] = po_list
        print(f"Dropdown values set to: {po_list}")
        print("=" * 50)
    
    def create_purchase_order(self):
        selection = self.po_supplier_combo.get()
        if not selection or '(ID: ' not in selection:
            show_error("Select a supplier first")
            return
        
        supplier_id = int(selection.split('(ID: ')[1].rstrip(')'))
        supplier_name = selection.split(' (ID:')[0]
        po_number = self.po_number_var.get()
        expected_date = self.po_date_var.get()
        notes = self.po_notes.get('1.0', tk.END).strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute("SELECT id FROM purchase_orders WHERE po_number=?", (po_number,))
        if c.fetchone():
            # Generate new PO number if exists
            today = self.working_date.replace('-', '')
            c.execute("SELECT COUNT(*) FROM purchase_orders WHERE po_number LIKE ?", (f'PO-{today}%',))
            count = c.fetchone()[0] + 1
            po_number = f"PO-{today}-{count:03d}"
            self.po_number_var.set(po_number)
        
        subtotal = 0
        po_items = []
        for item in self.po_products_tree.get_children():
            values = self.po_products_tree.item(item)['values']
            prod_id = values[0]
            prod_name = values[1]
            cost_str = values[3].replace(CURRENCY_SYMBOL, '').strip()
            cost = float(cost_str)
            qty = values[4]
            total = cost * qty
            
            if qty > 0:
                subtotal += total
                po_items.append((prod_id, prod_name, qty, cost, total))
        
        if not po_items:
            show_error("No items in purchase order")
            conn.close()
            return
        
        tax = subtotal * self.tax_rate  # Uses the tax rate loaded from database
        total = subtotal + tax
        
        try:
            c.execute("BEGIN TRANSACTION")
            
            c.execute('''INSERT INTO purchase_orders 
                        (po_number, supplier_id, supplier_name, order_date, expected_date, status, subtotal, tax, total, notes, created_by)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                      (po_number, supplier_id, supplier_name, self.working_date, 
                       expected_date, 'Pending', subtotal, tax, total, notes, 'admin'))
            po_id = c.lastrowid
            
            for prod_id, prod_name, qty, cost, total_cost in po_items:
                c.execute('''INSERT INTO po_items (po_id, product_id, product_name, quantity, unit_cost, total_cost)
                            VALUES (?,?,?,?,?,?)''', (po_id, prod_id, prod_name, qty, cost, total_cost))
            
            conn.commit()
            show_success(f"Purchase Order {po_number} created successfully!")
            
            # Clear form
            self.po_supplier_combo.set('')
            
            # Generate new PO number for next use
            today = self.working_date.replace('-', '')
            c.execute("SELECT COUNT(*) FROM purchase_orders WHERE po_number LIKE ?", (f'PO-{today}%',))
            count = c.fetchone()[0] + 1
            self.po_number_var.set(f"PO-{today}-{count:03d}")
            
            working_date_obj = datetime.strptime(self.working_date, '%Y-%m-%d')
            self.po_date_var.set((working_date_obj + timedelta(days=7)).strftime('%Y-%m-%d'))
            self.po_notes.delete('1.0', tk.END)
            for row in self.po_products_tree.get_children():
                self.po_products_tree.delete(row)
            
            self.load_purchase_orders()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error creating PO: {e}")
        finally:
            conn.close()
            notebook = self.window.children['!notebook']
            notebook.select(1)
    
    def view_purchase_order(self, event=None):
        selected = self.po_tree.selection()
        if not selected:
            return
        
        po_number = self.po_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get PO details
        c.execute('''SELECT * FROM purchase_orders WHERE po_number=?''', (po_number,))
        po = c.fetchone()
        
        # Get PO items
        c.execute('''SELECT product_name, quantity, unit_cost, total_cost FROM po_items WHERE po_id=?''', (po[0],))
        items = c.fetchall()
        
        # Get returns for this PO
        c.execute('''SELECT pr.return_date, p.name, pr.quantity, pr.reason, pr.returned_by
                     FROM po_returns pr
                     JOIN products p ON pr.product_id = p.id
                     WHERE pr.po_id=?
                     ORDER BY pr.return_date''', (po[0],))
        returns = c.fetchall()
        
        conn.close()
        
        if not po:
            return
        
        win = tk.Toplevel(self.window)
        win.title(f"Purchase Order: {po_number}")
        win.geometry("700x750")
        
        win.update_idletasks()
        x = (win.winfo_screenwidth() - 700) // 2
        y = (win.winfo_screenheight() - 750) // 2
        win.geometry(f"700x750+{x}+{y}")
        
        win.grab_set()
        win.transient(self.window)
        
        # Title
        title_frame = tk.Frame(win, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text=f"📄 PURCHASE ORDER: {po_number}", fg='white', bg='#3498db', 
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Main scrollable frame
        canvas = tk.Canvas(win, bg='#f9f9f9', highlightthickness=0)
        scrollbar = tk.Scrollbar(win, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f9f9f9')
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # PO Info
        info_frame = tk.Frame(scrollable_frame, bg='#f9f9f9')
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(info_frame, text=f"Supplier: {po[3]}", font=('Arial', 12, 'bold'), bg='#f9f9f9').pack(anchor='w')
        tk.Label(info_frame, text=f"Order Date: {po[4]}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(info_frame, text=f"Expected Date: {po[5]}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(info_frame, text=f"Status: {po[6]}", bg='#f9f9f9', fg='#27ae60' if po[6]=='Received' else '#e74c3c').pack(anchor='w')
        
        tk.Label(scrollable_frame, text="───────────────────────────────────────────────────────────",
                font=('Courier', 10), bg='#f9f9f9').pack(pady=5)
        
        # Original Order Section
        tk.Label(scrollable_frame, text="ORIGINAL ORDER", font=('Arial', 12, 'bold'),
                bg='#f9f9f9', fg='#2980b9').pack(anchor='w', padx=20, pady=5)
        
        # Items table
        items_frame = tk.Frame(scrollable_frame, bg='white', relief=tk.RIDGE, bd=1)
        items_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # Headers
        header = tk.Frame(items_frame, bg='#ecf0f1')
        header.pack(fill=tk.X)
        tk.Label(header, text="Item", width=30, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Label(header, text="Qty", width=8, anchor='e', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="Cost", width=10, anchor='e', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        tk.Label(header, text="Total", width=12, anchor='e', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        total_original = 0
        for item in items:
            row = tk.Frame(items_frame, bg='white')
            row.pack(fill=tk.X, pady=1)
            tk.Label(row, text=item[0][:30], width=30, anchor='w', bg='white').pack(side=tk.LEFT, padx=5)
            tk.Label(row, text=str(item[1]), width=8, anchor='e', bg='white').pack(side=tk.LEFT)
            tk.Label(row, text=f"{CURRENCY_SYMBOL}{item[2]:.2f}", width=10, anchor='e', bg='white').pack(side=tk.LEFT)
            tk.Label(row, text=f"{CURRENCY_SYMBOL}{item[3]:.2f}", width=12, anchor='e', bg='white').pack(side=tk.LEFT)
            total_original += item[3]
        
        # Total row
        total_frame = tk.Frame(items_frame, bg='#ecf0f1')
        total_frame.pack(fill=tk.X, pady=2)
        tk.Label(total_frame, text="TOTAL", width=30, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        tk.Label(total_frame, text="", width=8, anchor='e', bg='#ecf0f1').pack(side=tk.LEFT)
        tk.Label(total_frame, text="", width=10, anchor='e', bg='#ecf0f1').pack(side=tk.LEFT)
        tk.Label(total_frame, text=f"{CURRENCY_SYMBOL}{total_original:.2f}", width=12, anchor='e', 
                bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
        
        tk.Label(scrollable_frame, text="───────────────────────────────────────────────────────────",
                font=('Courier', 10), bg='#f9f9f9').pack(pady=5)
        
        # Returns Section
        if returns:
            tk.Label(scrollable_frame, text="RETURNS HISTORY", font=('Arial', 12, 'bold'),
                    bg='#f9f9f9', fg='#e67e22').pack(anchor='w', padx=20, pady=5)
            
            returns_frame = tk.Frame(scrollable_frame, bg='white', relief=tk.RIDGE, bd=1)
            returns_frame.pack(fill=tk.X, padx=20, pady=5)
            
            # Headers
            r_header = tk.Frame(returns_frame, bg='#ecf0f1')
            r_header.pack(fill=tk.X)
            tk.Label(r_header, text="Date", width=12, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
            tk.Label(r_header, text="Product", width=25, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            tk.Label(r_header, text="Qty", width=6, anchor='e', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            tk.Label(r_header, text="Reason", width=20, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            tk.Label(r_header, text="By", width=10, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            
            total_returned = 0
            for ret in returns:
                r_row = tk.Frame(returns_frame, bg='white')
                r_row.pack(fill=tk.X, pady=1)
                tk.Label(r_row, text=ret[0][:10], width=12, anchor='w', bg='white').pack(side=tk.LEFT, padx=5)
                tk.Label(r_row, text=ret[1][:25], width=25, anchor='w', bg='white').pack(side=tk.LEFT)
                tk.Label(r_row, text=str(ret[2]), width=6, anchor='e', bg='white').pack(side=tk.LEFT)
                tk.Label(r_row, text=ret[3][:20], width=20, anchor='w', bg='white').pack(side=tk.LEFT)
                tk.Label(r_row, text=ret[4], width=10, anchor='w', bg='white').pack(side=tk.LEFT)
                total_returned += ret[2]
            
            # Return total row
            r_total_frame = tk.Frame(returns_frame, bg='#ecf0f1')
            r_total_frame.pack(fill=tk.X, pady=2)
            tk.Label(r_total_frame, text="TOTAL RETURNED", width=43, anchor='w', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
            tk.Label(r_total_frame, text=str(total_returned), width=6, anchor='e', bg='#ecf0f1', font=('Arial', 9, 'bold')).pack(side=tk.LEFT)
            
            tk.Label(scrollable_frame, text="───────────────────────────────────────────────────────────",
                    font=('Courier', 10), bg='#f9f9f9').pack(pady=5)
        
        # Summary Section
        summary_frame = tk.Frame(scrollable_frame, bg='#f9f9f9')
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(summary_frame, text="SUMMARY", font=('Arial', 12, 'bold'),
                bg='#f9f9f9', fg='#2c3e50').pack(anchor='w')
        
        # Calculate net payable
        total_returns_value = 0
        if returns:
            for ret in returns:
                # Get cost for each returned item
                conn = sqlite3.connect('urban_pulse.db')
                c = conn.cursor()
                c.execute("SELECT cost_price FROM products WHERE name=?", (ret[1],))
                cost = c.fetchone()
                conn.close()
                if cost:
                    total_returns_value += cost[0] * ret[2]
        
        net_payable = total_original - total_returns_value
        
        summary_text = f"""
Original Total:      {CURRENCY_SYMBOL}{total_original:,.2f}
Less Returns:        {CURRENCY_SYMBOL}{total_returns_value:,.2f}
────────────────────────────────
NET PAYABLE:         {CURRENCY_SYMBOL}{net_payable:,.2f}
        """
        
        tk.Label(summary_frame, text=summary_text, justify=tk.LEFT, bg='#f9f9f9',
                font=('Courier', 11)).pack(anchor='w', pady=5)
        
        # Close button
        tk.Button(scrollable_frame, text="❌ Close", command=win.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                 width=10, cursor='hand2').pack(pady=10)

    def mark_po_received(self, event=None):
        """Mark selected purchase order as received with proper accounting"""
        selected = self.po_tree.selection()
        if not selected:
            show_error("Please select a purchase order")
            return

        po_number = self.po_tree.item(selected[0])['values'][0]

        # Confirm with user
        if not ask_yes_no(f"Mark PO {po_number} as received?\n\nThis will update inventory and supplier balance."):
            return

        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()

        try:
            # Get PO details
            c.execute('''SELECT id, supplier_id, supplier_name, total, subtotal, tax 
                         FROM purchase_orders 
                         WHERE po_number=? AND status='Pending' ''', (po_number,))
            po = c.fetchone()

            if not po:
                show_error("PO not found or already received/cancelled")
                conn.close()
                return

            po_id, supplier_id, supplier_name, po_total, subtotal, tax = po

            # Begin transaction
            c.execute("BEGIN TRANSACTION")

            # ===== 1. Update PO status =====
            c.execute('''UPDATE purchase_orders 
                         SET status='Received', received_date=? 
                         WHERE id=?''', (self.working_date, po_id))
        
            # ===== 2. Get PO items to update inventory =====
            c.execute('''SELECT product_id, quantity FROM po_items WHERE po_id=?''', (po_id,))
            items = c.fetchall()

            # ===== 3. Update product stock quantities =====
            for product_id, qty in items:
                c.execute('''UPDATE products 
                             SET stock = stock + ? 
                             WHERE id=?''', (qty, product_id))

            # ===== 4. Update supplier balance =====
            c.execute('''UPDATE suppliers 
                         SET current_balance = current_balance + ? 
                         WHERE id=?''', (po_total, supplier_id))

            # ===== 5. Get supplier's account ID =====
            c.execute('SELECT account_id FROM suppliers WHERE id=?', (supplier_id,))
            supplier_account = c.fetchone()
        
            if not supplier_account or not supplier_account[0]:
                raise Exception(f"Supplier {supplier_name} has no linked account!")
        
            supplier_account_id = supplier_account[0]

            # ===== 6. Get Inventory account ID (1300) =====
            c.execute("SELECT id FROM accounts WHERE account_code='1300'")
            inventory_account = c.fetchone()
            if not inventory_account:
                raise Exception("Inventory account (1300) not found!")
            inventory_account_id = inventory_account[0]

            # ===== 7. CREATE VOUCHER for this purchase =====
            today = self.working_date.replace('-', '')
            c.execute("SELECT COUNT(*) FROM vouchers WHERE voucher_no LIKE ?", (f'PUR-{today}%',))
            count = c.fetchone()[0] + 1
            voucher_no = f"PUR-{today}-{count:03d}"
        
            narration = f"Purchase from {supplier_name} - PO #{po_number}"
        
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, 
                         created_by, created_at, supplier_id)
                        VALUES (?, 'Purchase', ?, ?, ?, ?, ?, ?)''',
                      (voucher_no, self.working_date, narration, po_total,
                       'admin', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), supplier_id))
            voucher_id = c.lastrowid
            print(f"✅ Created voucher: {voucher_no}")

            # ===== 8. CREATE LEDGER ENTRIES (Double-entry) =====

            # Entry 1: Debit Inventory (1300)
            c.execute('''INSERT INTO ledger_entries 
                        (voucher_id, account_id, debit, credit, entry_date, narration)
                        VALUES (?, ?, ?, 0, ?, ?)''',
                      (voucher_id, inventory_account_id, po_total, self.working_date,
                       f"Inventory increase from PO {po_number}"))

            # Entry 2: Credit Accounts Payable (supplier's account)
            c.execute('''INSERT INTO ledger_entries 
                        (voucher_id, account_id, debit, credit, entry_date, narration)
                        VALUES (?, ?, 0, ?, ?, ?)''',
                      (voucher_id, supplier_account_id, po_total, self.working_date,
                       f"Accounts payable to {supplier_name} for PO {po_number}"))

            # ===== 9. Update account balances =====
            # Increase Inventory
            c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                     (po_total, inventory_account_id))
        
            # Increase Accounts Payable (supplier account)
            c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                     (po_total, supplier_account_id))

            # Commit all changes
            conn.commit()
        
            success_msg = (f"PO {po_number} marked as received!\n\n"
                          f"✓ Voucher: {voucher_no}\n"
                          f"✓ Stock updated for {len(items)} products\n"
                          f"✓ Supplier balance increased by {CURRENCY_SYMBOL}{po_total:,.2f}\n"
                          f"✓ Inventory asset increased by {CURRENCY_SYMBOL}{po_total:,.2f}\n"
                          f"✓ Ledger entries created")
        
            show_success(success_msg)

            # Refresh the PO list
            self.load_purchase_orders()
            self.load_reorder_alerts()

        except Exception as e:
            conn.rollback()
            show_error(f"Error marking PO as received: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def cancel_po(self, event=None):
        """Cancel selected purchase order"""
        selected = self.po_tree.selection()
        if not selected:
            show_error("Please select a purchase order")
            return
    
        po_number = self.po_tree.item(selected[0])['values'][0]
        current_status = self.po_tree.item(selected[0])['values'][4]  # Status column
    
        # Can only cancel pending orders
        if current_status != 'Pending':
            show_error(f"Cannot cancel PO with status: {current_status}")
            return
    
        # Confirm with user
        if not ask_yes_no(f"Cancel PO {po_number}?\n\nThis action cannot be undone."):
            return
    
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        try:
            # Get PO details
            c.execute('''SELECT id FROM purchase_orders 
                         WHERE po_number=? AND status='Pending' ''', (po_number,))
            po = c.fetchone()
        
            if not po:
                show_error("PO not found or already processed")
                conn.close()
                return
        
            po_id = po[0]
        
            # Begin transaction
            c.execute("BEGIN TRANSACTION")
        
            # Update PO status to Cancelled
            c.execute('''UPDATE purchase_orders 
                         SET status='Cancelled' 
                         WHERE id=?''', (po_id,))
        
            conn.commit()
            show_success(f"PO {po_number} has been cancelled")
        
            # Refresh the PO list
            self.load_purchase_orders()
        
        except Exception as e:
            conn.rollback()
            show_error(f"Error cancelling PO: {str(e)}")
        finally:
            conn.close()

    def create_po_from_reorder(self, event=None):
        """Create a purchase order from a reorder alert"""
        selected = self.reorder_tree.selection()
        if not selected:
            show_error("Please select a product from reorder alerts")
            return
    
        # Get product details from selected row
        values = self.reorder_tree.item(selected[0])['values']
        product_id = values[0]
        product_name = values[1]
        current_stock = values[2]
        reorder_level = values[3]
        supplier_name = values[4]
    
        # Get supplier ID
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id FROM suppliers WHERE company_name=?", (supplier_name,))
        supplier_result = c.fetchone()
    
        if not supplier_result:
            show_error(f"Supplier {supplier_name} not found")
            conn.close()
            return
    
        supplier_id = supplier_result[0]
    
        # Get product cost
        c.execute("SELECT cost_price FROM products WHERE id=?", (product_id,))
        cost_result = c.fetchone()
        cost = cost_result[0] if cost_result else 0
    
        conn.close()
    
        # Calculate recommended order quantity (reorder level * 2 - current stock)
        # or at least reorder level if stock is very low
        if current_stock <= 0:
            recommended_qty = reorder_level * 2
        else:
            recommended_qty = max(reorder_level * 2 - current_stock, reorder_level)
    
        # Ask user for quantity
        qty = simpledialog.askinteger(
            "Order Quantity", 
            f"Product: {product_name}\n"
            f"Current Stock: {current_stock}\n"
            f"Reorder Level: {reorder_level}\n"
            f"Recommended: {recommended_qty}\n\n"
            f"Enter quantity to order:",
            parent=self.window,
            minvalue=1,
            initialvalue=recommended_qty
        )
    
        if not qty:
            return
    
        # Switch to New PO tab and pre-fill
        notebook = self.window.children['!notebook']
        notebook.select(2)  # Select New Purchase Order tab
    
        # Set supplier
        self.po_supplier_combo.set(f"{supplier_name} (ID: {supplier_id})")
    
        # Clear existing products
        for row in self.po_products_tree.get_children():
            self.po_products_tree.delete(row)
    
        # Add the product
        total = cost * qty
        self.po_products_tree.insert('', tk.END, values=(
            product_id, 
            product_name, 
            current_stock, 
            f"{CURRENCY_SYMBOL}{cost:.2f}", 
            qty, 
            f"{CURRENCY_SYMBOL}{total:.2f}"
        ))
    
        # Calculate totals
        self.calculate_po_totals()
    
        show_success(f"Added {qty} x {product_name} to new purchase order")

    def update_reorder_level(self, event=None):
        """Update reorder level for a product"""
        selected = self.reorder_tree.selection()
        if not selected:
            show_error("Please select a product from reorder alerts")
            return
    
        # Get product details
        values = self.reorder_tree.item(selected[0])['values']
        product_id = values[0]
        product_name = values[1]
        current_stock = values[2]
        current_reorder = values[3]
    
        # Ask for new reorder level
        new_level = simpledialog.askinteger(
            "Update Reorder Level",
            f"Product: {product_name}\n"
            f"Current Stock: {current_stock}\n"
            f"Current Reorder Level: {current_reorder}\n\n"
            f"Enter new reorder level:",
            parent=self.window,
            minvalue=1,
            initialvalue=current_reorder
        )
    
        if not new_level:
            return
    
        # Update in database
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        try:
            c.execute("UPDATE products SET reorder_level = ? WHERE id = ?", 
                     (new_level, product_id))
            conn.commit()
        
            show_success(f"Reorder level for {product_name} updated from {current_reorder} to {new_level}")
        
            # Refresh the alerts
            self.load_reorder_alerts()
        
        except Exception as e:
            show_error(f"Error updating reorder level: {str(e)}")
        finally:
            conn.close()

    def refresh_returns_tab(self):
        """Refresh the returns tab - load POs and history"""
        self.load_purchase_orders_for_returns()
        self.load_return_history()
        show_success("Returns tab refreshed")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    sm = SupplierManager(root)
    root.mainloop()