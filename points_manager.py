# points_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation

class PointsManager:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Loyalty Points Management")
        self.window.geometry("900x600")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"900x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Get settings
        self.conversion_rate = self.get_setting('points_conversion_rate', '100')
        self.min_redeem = self.get_setting('points_min_redeem', '100')
        self.earn_rate = self.get_setting('points_earn_rate', '1')
        
        self.create_widgets()
        self.load_customers()
    
    def get_setting(self, key, default):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key=?", (key,))
        result = c.fetchone()
        conn.close()
        return result[0] if result else default
    
    def save_setting(self, key, value):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Customer Points
        self.customers_tab = tk.Frame(notebook)
        notebook.add(self.customers_tab, text="Customer Points")
        self.create_customers_tab()
        
        # Tab 2: Points Settings
        self.settings_tab = tk.Frame(notebook)
        notebook.add(self.settings_tab, text="Points Settings")
        self.create_settings_tab()
        
        # Tab 3: Points History
        self.history_tab = tk.Frame(notebook)
        notebook.add(self.history_tab, text="Points History")
        self.create_history_tab()
        
        # Tab 4: Reports
        self.reports_tab = tk.Frame(notebook)
        notebook.add(self.reports_tab, text="Reports")
        self.create_reports_tab()
    
    def create_customers_tab(self):
        # Search frame
        search_frame = tk.Frame(self.customers_tab)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_customers())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        # Summary frame
        summary_frame = tk.Frame(self.customers_tab, bg='#ecf0f1', height=50)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        self.total_points_label = tk.Label(summary_frame, text="Total Points: 0", 
                                          bg='#ecf0f1', font=('Arial', 10, 'bold'))
        self.total_points_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.avg_points_label = tk.Label(summary_frame, text="Avg Points: 0", 
                                        bg='#ecf0f1', font=('Arial', 10))
        self.avg_points_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        self.top_customer_label = tk.Label(summary_frame, text="Top Customer: None", 
                                          bg='#ecf0f1', font=('Arial', 10))
        self.top_customer_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Treeview
        columns = ('ID', 'Name', 'Phone', 'Email', 'Points', f'Total Spent ({CURRENCY_SYMBOL})', 'Last Visit')
        self.tree = ttk.Treeview(self.customers_tab, columns=columns, show='headings', height=12)
        
        col_widths = {'ID': 40, 'Name': 120, 'Phone': 100, 'Email': 150, 'Points': 60, 
                     f'Total Spent ({CURRENCY_SYMBOL})': 100, 'Last Visit': 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.customers_tab)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Add Points", command=self.add_points, 
                 bg='green', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Deduct Points", command=self.deduct_points, 
                 bg='orange', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View History", command=self.view_points_history).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Reset Points", command=self.reset_points, 
                 bg='red', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_customers).pack(side=tk.LEFT, padx=5)
    
    def create_settings_tab(self):
        # Points conversion settings
        frame = tk.LabelFrame(self.settings_tab, text="Points Configuration", padx=10, pady=10)
        frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Conversion rate
        tk.Label(frame, text=f"Points to {CURRENCY_SYMBOL}1 Conversion:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.conversion_var = tk.StringVar(value=self.conversion_rate)
        conversion_entry = tk.Entry(frame, textvariable=self.conversion_var, width=10)
        conversion_entry.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        tk.Label(frame, text=f"points = {CURRENCY_SYMBOL}1").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        
        # Minimum redeem
        tk.Label(frame, text="Minimum Points to Redeem:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.min_redeem_var = tk.StringVar(value=self.min_redeem)
        min_entry = tk.Entry(frame, textvariable=self.min_redeem_var, width=10)
        min_entry.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        tk.Label(frame, text="points").grid(row=1, column=2, padx=5, pady=5, sticky='w')
        
        # Earn rate
        tk.Label(frame, text=f"Points Earned per {CURRENCY_SYMBOL}1:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.earn_rate_var = tk.StringVar(value=self.earn_rate)
        earn_entry = tk.Entry(frame, textvariable=self.earn_rate_var, width=10)
        earn_entry.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        tk.Label(frame, text="points").grid(row=2, column=2, padx=5, pady=5, sticky='w')
        
        # Setup Enter navigation
        setup_enter_navigation(conversion_entry, min_entry)
        setup_enter_navigation(min_entry, earn_entry)
        setup_enter_navigation(earn_entry, self.save_settings)
        
        # Save button
        tk.Button(frame, text="Save Settings", command=self.save_settings, 
                 bg='blue', fg='white').grid(row=3, column=0, columnspan=3, pady=20)
        
        # Info frame
        info_frame = tk.LabelFrame(self.settings_tab, text="Points Information", padx=10, pady=10)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = f"""
        Points System Rules:
        • Customers earn 1 point for every {CURRENCY_SYMBOL}1 spent (configurable)
        • {self.conversion_rate} points = {CURRENCY_SYMBOL}1 discount (configurable)
        • Minimum {self.min_redeem} points to redeem (configurable)
        • Points never expire
        • Points history is tracked for each customer
        """
        tk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
    
    def create_history_tab(self):
        # Customer selection
        top_frame = tk.Frame(self.history_tab)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(top_frame, text="Select Customer:").pack(side=tk.LEFT)
        self.history_customer_var = tk.StringVar()
        self.history_customer_combo = ttk.Combobox(top_frame, textvariable=self.history_customer_var, width=30)
        self.history_customer_combo.pack(side=tk.LEFT, padx=5)
        self.history_customer_combo.bind('<<ComboboxSelected>>', self.load_points_history)
        
        tk.Button(top_frame, text="View All History", command=lambda: self.load_points_history(all_customers=True)).pack(side=tk.LEFT, padx=5)
        
        # Treeview for history
        columns = ('Date', 'Customer', 'Type', 'Points Change', 'Balance', 'Sale ID', 'Notes')
        self.history_tree = ttk.Treeview(self.history_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'Date': 130, 'Customer': 120, 'Type': 100, 'Points Change': 100, 
                     'Balance': 80, 'Sale ID': 60, 'Notes': 150}
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=col_widths.get(col, 100))
        
        self.history_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Load customers for dropdown
        self.load_customer_dropdown()
    
    def create_reports_tab(self):
        # Summary cards
        card_frame = tk.Frame(self.reports_tab)
        card_frame.pack(fill=tk.X, padx=20, pady=20)
        
        # Total points issued
        issued_frame = tk.Frame(card_frame, bg='#3498db', width=200, height=100)
        issued_frame.pack(side=tk.LEFT, padx=10)
        issued_frame.pack_propagate(False)
        
        tk.Label(issued_frame, text="Total Points Issued", bg='#3498db', fg='white', 
                font=('Arial', 10)).pack(pady=10)
        self.issued_label = tk.Label(issued_frame, text="0", bg='#3498db', fg='white', 
                                     font=('Arial', 20, 'bold'))
        self.issued_label.pack()
        
        # Total points redeemed
        redeemed_frame = tk.Frame(card_frame, bg='#e74c3c', width=200, height=100)
        redeemed_frame.pack(side=tk.LEFT, padx=10)
        redeemed_frame.pack_propagate(False)
        
        tk.Label(redeemed_frame, text="Total Points Redeemed", bg='#e74c3c', fg='white', 
                font=('Arial', 10)).pack(pady=10)
        self.redeemed_label = tk.Label(redeemed_frame, text="0", bg='#e74c3c', fg='white', 
                                       font=('Arial', 20, 'bold'))
        self.redeemed_label.pack()
        
        # Active points
        active_frame = tk.Frame(card_frame, bg='#27ae60', width=200, height=100)
        active_frame.pack(side=tk.LEFT, padx=10)
        active_frame.pack_propagate(False)
        
        tk.Label(active_frame, text="Active Points", bg='#27ae60', fg='white', 
                font=('Arial', 10)).pack(pady=10)
        self.active_label = tk.Label(active_frame, text="0", bg='#27ae60', fg='white', 
                                     font=('Arial', 20, 'bold'))
        self.active_label.pack()
        
        # Points distribution
        chart_frame = tk.LabelFrame(self.reports_tab, text="Points Distribution", padx=10, pady=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        dist_columns = ('Range', 'Number of Customers', 'Total Points')
        self.dist_tree = ttk.Treeview(chart_frame, columns=dist_columns, show='headings', height=8)
        
        for col in dist_columns:
            self.dist_tree.heading(col, text=col)
            self.dist_tree.column(col, width=150)
        
        self.dist_tree.pack(fill=tk.BOTH, expand=True)
        
        # Load report data
        self.load_report_data()
    
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
                         ORDER BY loyalty_points DESC''', 
                      (f'%{search}%', f'%{search}%', f'%{search}%'))
        else:
            c.execute('''SELECT id, name, phone, email, loyalty_points, total_spent, last_visit
                         FROM customers ORDER BY loyalty_points DESC''')
        
        customers = c.fetchall()
        conn.close()
        
        total_points = 0
        top_customer = ("", 0)
        
        for cust in customers:
            self.tree.insert('', tk.END, values=(cust[0], cust[1], cust[2], cust[3] or '', 
                                                cust[4], f"{CURRENCY_SYMBOL}{cust[5]:.2f}", cust[6] or ''))
            total_points += cust[4]
            if cust[4] > top_customer[1]:
                top_customer = (cust[1], cust[4])
        
        self.total_points_label.config(text=f"Total Points: {total_points}")
        avg_points = total_points // len(customers) if customers else 0
        self.avg_points_label.config(text=f"Avg Points: {avg_points}")
        self.top_customer_label.config(text=f"Top Customer: {top_customer[0]} ({top_customer[1]} pts)")
    
    def load_customer_dropdown(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM customers ORDER BY name")
        customers = c.fetchall()
        conn.close()
        
        self.customer_list = customers
        self.history_customer_combo['values'] = [f"{c[1]} (ID: {c[0]})" for c in customers]
    
    def add_points(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        cust_name = self.tree.item(selected[0])['values'][1]
        
        points = simpledialog.askinteger("Add Points", f"Enter points to add for {cust_name}:",
                                        parent=self.window, minvalue=1)
        if points:
            reason = simpledialog.askstring("Reason", "Reason for adding points (optional):",
                                           parent=self.window)
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            c.execute("SELECT loyalty_points, points_earned_total FROM customers WHERE id=?", (cust_id,))
            current_points, earned_total = c.fetchone()
            new_points = current_points + points
            
            c.execute('''UPDATE customers 
                        SET loyalty_points = ?, points_earned_total = points_earned_total + ?
                        WHERE id = ?''', (new_points, points, cust_id))
            
            c.execute('''INSERT INTO points_transactions 
                        (customer_id, customer_name, transaction_date, points_change, 
                         balance_after, transaction_type, notes)
                        VALUES (?,?,?,?,?,?,?)''',
                      (cust_id, cust_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                       points, new_points, 'MANUAL_ADD', reason or 'Manual addition'))
            
            conn.commit()
            conn.close()
            
            show_success(f"Added {points} points to {cust_name}")
            self.load_customers()
    
    def deduct_points(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        cust_name = self.tree.item(selected[0])['values'][1]
        current_points = self.tree.item(selected[0])['values'][4]
        
        points = simpledialog.askinteger("Deduct Points", 
                                        f"Enter points to deduct (Max: {current_points}):",
                                        parent=self.window, minvalue=1, maxvalue=current_points)
        if points:
            reason = simpledialog.askstring("Reason", "Reason for deducting points:",
                                           parent=self.window)
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            new_points = current_points - points
            
            c.execute('''UPDATE customers 
                        SET loyalty_points = ?, points_used_total = points_used_total + ?
                        WHERE id = ?''', (new_points, points, cust_id))
            
            c.execute('''INSERT INTO points_transactions 
                        (customer_id, customer_name, transaction_date, points_change, 
                         balance_after, transaction_type, notes)
                        VALUES (?,?,?,?,?,?,?)''',
                      (cust_id, cust_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                       -points, new_points, 'MANUAL_DEDUCT', reason or 'Manual deduction'))
            
            conn.commit()
            conn.close()
            
            show_success(f"Deducted {points} points from {cust_name}")
            self.load_customers()
    
    def reset_points(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a customer first")
            return
        
        cust_id = self.tree.item(selected[0])['values'][0]
        cust_name = self.tree.item(selected[0])['values'][1]
        current_points = self.tree.item(selected[0])['values'][4]
        
        if ask_yes_no(f"Reset all {current_points} points for {cust_name}?"):
            reason = simpledialog.askstring("Reason", "Reason for resetting points:",
                                           parent=self.window)
            
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            c.execute('''INSERT INTO points_transactions 
                        (customer_id, customer_name, transaction_date, points_change, 
                         balance_after, transaction_type, notes)
                        VALUES (?,?,?,?,?,?,?)''',
                      (cust_id, cust_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                       -current_points, 0, 'MANUAL_RESET', reason or 'Points reset'))
            
            c.execute("UPDATE customers SET loyalty_points = 0 WHERE id=?", (cust_id,))
            
            conn.commit()
            conn.close()
            
            show_success(f"Reset points for {cust_name}")
            self.load_customers()
    
    def view_points_history(self):
        selected = self.tree.selection()
        if selected:
            cust_id = self.tree.item(selected[0])['values'][0]
            self.load_points_history(cust_id=cust_id)
    
    def load_points_history(self, event=None, cust_id=None, all_customers=False):
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if all_customers:
            c.execute('''SELECT transaction_date, customer_name, transaction_type, 
                                points_change, balance_after, sale_id, notes
                         FROM points_transactions 
                         ORDER BY transaction_date DESC LIMIT 500''')
        elif cust_id:
            c.execute('''SELECT transaction_date, customer_name, transaction_type, 
                                points_change, balance_after, sale_id, notes
                         FROM points_transactions 
                         WHERE customer_id = ?
                         ORDER BY transaction_date DESC''', (cust_id,))
        else:
            selection = self.history_customer_combo.get()
            if selection and '(ID: ' in selection:
                cust_id = int(selection.split('(ID: ')[1].rstrip(')'))
                c.execute('''SELECT transaction_date, customer_name, transaction_type, 
                                    points_change, balance_after, sale_id, notes
                             FROM points_transactions 
                             WHERE customer_id = ?
                             ORDER BY transaction_date DESC''', (cust_id,))
            else:
                c.execute('''SELECT transaction_date, customer_name, transaction_type, 
                                    points_change, balance_after, sale_id, notes
                             FROM points_transactions 
                             ORDER BY transaction_date DESC LIMIT 200''')
        
        transactions = c.fetchall()
        conn.close()
        
        for trans in transactions:
            self.history_tree.insert('', tk.END, values=trans)
    
    def load_report_data(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute("SELECT SUM(points_earned_total) FROM customers")
        issued = c.fetchone()[0] or 0
        self.issued_label.config(text=str(issued))
        
        c.execute("SELECT SUM(points_used_total) FROM customers")
        redeemed = c.fetchone()[0] or 0
        self.redeemed_label.config(text=str(redeemed))
        
        c.execute("SELECT SUM(loyalty_points) FROM customers")
        active = c.fetchone()[0] or 0
        self.active_label.config(text=str(active))
        
        ranges = [
            (0, 100, "0-100"),
            (101, 500, "101-500"),
            (501, 1000, "501-1000"),
            (1001, 5000, "1001-5000"),
            (5001, float('inf'), "5000+")
        ]
        
        for low, high, label in ranges:
            if high == float('inf'):
                c.execute("SELECT COUNT(*), SUM(loyalty_points) FROM customers WHERE loyalty_points >= ?", (low,))
            else:
                c.execute("SELECT COUNT(*), SUM(loyalty_points) FROM customers WHERE loyalty_points BETWEEN ? AND ?", (low, high))
            
            count, total = c.fetchone()
            count = count or 0
            total = total or 0
            self.dist_tree.insert('', tk.END, values=(label, count, int(total)))
        
        conn.close()
    
    def save_settings(self):
        try:
            conversion = int(self.conversion_var.get())
            min_redeem = int(self.min_redeem_var.get())
            earn_rate = int(self.earn_rate_var.get())
            
            if conversion <= 0 or min_redeem <= 0 or earn_rate <= 0:
                show_error("All values must be positive numbers")
                return
            
            self.save_setting('points_conversion_rate', str(conversion))
            self.save_setting('points_min_redeem', str(min_redeem))
            self.save_setting('points_earn_rate', str(earn_rate))
            
            self.conversion_rate = conversion
            self.min_redeem = min_redeem
            self.earn_rate = earn_rate
            
            show_success("Points settings saved!")
            
        except ValueError:
            show_error("Please enter valid numbers")