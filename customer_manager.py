# customer_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation

class AddEditCustomer:
    def __init__(self, parent, title, cust_id=None):
        self.cust_id = cust_id
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("350x250")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 350) // 2
        y = (self.window.winfo_screenheight() - 250) // 2
        self.window.geometry(f"350x250+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Variables
        self.name = tk.StringVar()
        self.phone = tk.StringVar()
        self.email = tk.StringVar()
        self.points = tk.StringVar()
        
        # If editing, load data
        if cust_id:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("SELECT name, phone, email, loyalty_points FROM customers WHERE id=?", (cust_id,))
            n, p, e, pts = c.fetchone()
            conn.close()
            self.name.set(n)
            self.phone.set(p)
            self.email.set(e or '')
            self.points.set(str(pts))
        
        self.create_widgets()
    
    def create_widgets(self):
        # Form fields
        fields = [
            ("Name *:", self.name),
            ("Phone *:", self.phone),
            ("Email:", self.email),
            ("Loyalty Points:", self.points)
        ]
        
        entries = []
        for i, (label, var) in enumerate(fields):
            tk.Label(self.window, text=label).grid(row=i, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(self.window, textvariable=var, width=25)
            entry.grid(row=i, column=1, padx=5, pady=5)
            entries.append(entry)
        
        # Setup Enter key navigation
        for j in range(len(entries)-1):
            setup_enter_navigation(entries[j], entries[j+1])
        setup_enter_navigation(entries[-1], self.save)
        
        # Note
        tk.Label(self.window, text="* Required fields", fg='red', font=('Arial', 8)).grid(row=4, column=0, columnspan=2, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="Save", command=self.save, 
                 bg='green', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.window.destroy, 
                 width=10).pack(side=tk.LEFT, padx=5)
    
    def save(self):
        name = self.name.get().strip()
        phone = self.phone.get().strip()
        email = self.email.get().strip()
        
        try:
            points = int(self.points.get() or 0)
        except:
            points = 0
        
        if not name or not phone:
            show_error("Name and phone are required")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if self.cust_id:
            c.execute('''UPDATE customers 
                        SET name=?, phone=?, email=?, loyalty_points=?
                        WHERE id=?''',
                      (name, phone, email, points, self.cust_id))
        else:
            try:
                c.execute('''INSERT INTO customers (name, phone, email, loyalty_points, join_date)
                            VALUES (?,?,?,?,?)''',
                          (name, phone, email, points, datetime.now().strftime('%Y-%m-%d')))
            except sqlite3.IntegrityError:
                show_error("Phone number already exists")
                conn.close()
                return
        
        conn.commit()
        conn.close()
        self.window.destroy()

class CustomerHistory:
    def __init__(self, parent, cust_id, cust_name):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Purchase History - {cust_name}")
        self.window.geometry("600x400")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 400) // 2
        self.window.geometry(f"600x400+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Treeview
        columns = ('Date', 'Sale ID', f'Total ({CURRENCY_SYMBOL})', 'Points Earned', 'Points Used', 'Items')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        
        col_widths = {'Date': 100, 'Sale ID': 60, f'Total ({CURRENCY_SYMBOL})': 80, 
                     'Points Earned': 100, 'Points Used': 100, 'Items': 150}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load data
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT datetime, id, total, points_earned, points_used, items 
                     FROM sales 
                     WHERE customer_id=?
                     ORDER BY datetime DESC''', (cust_id,))
        sales = c.fetchall()
        conn.close()
        
        for sale in sales:
            self.tree.insert('', tk.END, values=(sale[0], sale[1], f"{CURRENCY_SYMBOL}{sale[2]:.2f}", 
                                                sale[3], sale[4], sale[5][:30]))
        
        # Close button
        tk.Button(self.window, text="Close", command=self.window.destroy).pack(pady=5)

class CustomerManager:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Customers")
        self.window.geometry("800x500")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 500) // 2
        self.window.geometry(f"800x500+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_customers()
    
    def create_widgets(self):
        # Search frame
        search_frame = tk.Frame(self.window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_customers())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        tk.Button(search_frame, text="Add Customer", command=self.add_customer, 
                 bg='green', fg='white').pack(side=tk.RIGHT, padx=5)
        
        # Treeview
        columns = ('ID', 'Name', 'Phone', 'Email', 'Points', f'Total Spent ({CURRENCY_SYMBOL})', 'Last Visit')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        
        col_widths = {'ID': 40, 'Name': 120, 'Phone': 100, 'Email': 150, 'Points': 60, 
                     f'Total Spent ({CURRENCY_SYMBOL})': 100, 'Last Visit': 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_customer())
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Edit", command=self.edit_customer).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_customer, 
                 bg='red', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View History", command=self.view_history).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_customers).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_customers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if search:
            c.execute('''SELECT id, name, phone, email, loyalty_points, total_spent, last_visit 
                         FROM customers 
                         WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
                         ORDER BY name''', 
                      (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            c.execute("SELECT id, name, phone, email, loyalty_points, total_spent, last_visit FROM customers ORDER BY name")
        
        customers = c.fetchall()
        conn.close()
        
        for cust in customers:
            self.tree.insert('', tk.END, values=(cust[0], cust[1], cust[2], cust[3] or '', 
                                                cust[4], f"{CURRENCY_SYMBOL}{cust[5]:.2f}", cust[6] or ''))
    
    def add_customer(self):
        AddEditCustomer(self.window, "Add Customer")
        self.load_customers()
    
    def edit_customer(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        AddEditCustomer(self.window, "Edit Customer", cust_id)
        self.load_customers()
    
    def delete_customer(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        if ask_yes_no("Delete this customer?"):
            cust_id = self.tree.item(selected[0])['values'][0]
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("DELETE FROM customers WHERE id=?", (cust_id,))
            conn.commit()
            conn.close()
            self.load_customers()
    
    def view_history(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        cust_name = self.tree.item(selected[0])['values'][1]
        CustomerHistory(self.window, cust_id, cust_name)

class SelectCustomer:
    def __init__(self, parent):
        self.parent = parent
        self.selected_customer = None
        self.use_points = False
        
        self.window = tk.Toplevel(parent)
        self.window.title("Select Customer")
        self.window.geometry("600x400")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 400) // 2
        self.window.geometry(f"600x400+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_customers()
    
    def get_setting(self, key, default):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default
    
    def create_widgets(self):
        # Search frame
        search_frame = tk.Frame(self.window)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_customers())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        tk.Button(search_frame, text="Add New", command=self.add_new).pack(side=tk.RIGHT, padx=5)
        
        # Treeview
        columns = ('ID', 'Name', 'Phone', 'Points')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=12)
        
        col_widths = {'ID': 40, 'Name': 200, 'Phone': 120, 'Points': 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind('<Double-Button-1>', self.select)
        
        # Points checkbox
        info_frame = tk.Frame(self.window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.min_redeem = self.get_setting('points_min_redeem', '100')
        self.conversion_rate = self.get_setting('points_conversion_rate', '100')
        
        self.points_var = tk.BooleanVar()
        tk.Checkbutton(info_frame, 
                      text=f"Use loyalty points (Min: {self.min_redeem} points, {self.conversion_rate} points = {CURRENCY_SYMBOL}1)", 
                      variable=self.points_var).pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Select", command=self.select, 
                 bg='blue', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Skip (Walk-in)", command=self.skip, 
                 width=10).pack(side=tk.LEFT, padx=5)
    
    def load_customers(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if search:
            c.execute("SELECT id, name, phone, loyalty_points FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY name",
                      (f'%{search}%', f'%{search}%'))
        else:
            c.execute("SELECT id, name, phone, loyalty_points FROM customers ORDER BY name")
        
        customers = c.fetchall()
        conn.close()
        
        for cust in customers:
            self.tree.insert('', tk.END, values=cust)
    
    def add_new(self):
        AddEditCustomer(self.window, "Add Customer")
        self.load_customers()
    
    def select(self, event=None):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        cust_name = self.tree.item(selected[0])['values'][1]
        cust_phone = self.tree.item(selected[0])['values'][2]
        cust_points = self.tree.item(selected[0])['values'][3]
        
        self.selected_customer = {
            'id': cust_id,
            'name': cust_name,
            'phone': cust_phone,
            'points': cust_points
        }
        self.use_points = self.points_var.get()
        self.window.destroy()
    
    def skip(self):
        self.selected_customer = None
        self.use_points = False
        self.window.destroy()