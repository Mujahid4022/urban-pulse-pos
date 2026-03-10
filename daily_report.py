# daily_report.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import csv
import os
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, setup_enter_navigation

class DailyReport:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Daily Sales Report")
        self.window.geometry("800x600")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_report()
    
    def create_widgets(self):
        # Date selection frame
        date_frame = tk.Frame(self.window)
        date_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(date_frame, text="Select Date:").pack(side=tk.LEFT)
        self.date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = tk.Entry(date_frame, textvariable=self.date_var, width=15)
        date_entry.pack(side=tk.LEFT, padx=5)
        date_entry.focus()
        
        tk.Button(date_frame, text="Load Report", command=self.load_report, 
                 bg='blue', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(date_frame, text="Today", command=self.today_report).pack(side=tk.LEFT, padx=5)
        tk.Button(date_frame, text="Yesterday", command=self.yesterday_report).pack(side=tk.LEFT, padx=5)
        tk.Button(date_frame, text="Export CSV", command=self.export_csv, 
                 bg='green', fg='white').pack(side=tk.LEFT, padx=5)
        
        # Setup Enter key navigation
        setup_enter_navigation(date_entry, lambda: self.load_report())
        
        # Summary cards frame
        summary_frame = tk.Frame(self.window, bg='#ecf0f1', height=100)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        # Card 1: Total Sales
        sales_frame = tk.Frame(summary_frame, bg='#27ae60', width=180, height=80)
        sales_frame.pack(side=tk.LEFT, padx=10, pady=10)
        sales_frame.pack_propagate(False)
        
        tk.Label(sales_frame, text="Total Sales", bg='#27ae60', fg='white', 
                font=('Arial', 10)).pack(pady=5)
        self.total_sales_label = tk.Label(sales_frame, text=f"{CURRENCY_SYMBOL}0", bg='#27ae60', 
                                         fg='white', font=('Arial', 14, 'bold'))
        self.total_sales_label.pack()
        
        # Card 2: Transactions
        trans_frame = tk.Frame(summary_frame, bg='#3498db', width=180, height=80)
        trans_frame.pack(side=tk.LEFT, padx=10, pady=10)
        trans_frame.pack_propagate(False)
        
        tk.Label(trans_frame, text="Transactions", bg='#3498db', fg='white', 
                font=('Arial', 10)).pack(pady=5)
        self.trans_count_label = tk.Label(trans_frame, text="0", bg='#3498db', 
                                         fg='white', font=('Arial', 14, 'bold'))
        self.trans_count_label.pack()
        
        # Card 3: Average Sale
        avg_frame = tk.Frame(summary_frame, bg='#e67e22', width=180, height=80)
        avg_frame.pack(side=tk.LEFT, padx=10, pady=10)
        avg_frame.pack_propagate(False)
        
        tk.Label(avg_frame, text="Average Sale", bg='#e67e22', fg='white', 
                font=('Arial', 10)).pack(pady=5)
        self.avg_sale_label = tk.Label(avg_frame, text=f"{CURRENCY_SYMBOL}0", bg='#e67e22', 
                                      fg='white', font=('Arial', 14, 'bold'))
        self.avg_sale_label.pack()
        
        # Card 4: Items Sold
        items_frame = tk.Frame(summary_frame, bg='#9b59b6', width=180, height=80)
        items_frame.pack(side=tk.LEFT, padx=10, pady=10)
        items_frame.pack_propagate(False)
        
        tk.Label(items_frame, text="Items Sold", bg='#9b59b6', fg='white', 
                font=('Arial', 10)).pack(pady=5)
        self.items_sold_label = tk.Label(items_frame, text="0", bg='#9b59b6', 
                                        fg='white', font=('Arial', 14, 'bold'))
        self.items_sold_label.pack()
        
        # Notebook for detailed reports
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Sales by Hour
        self.hour_tab = tk.Frame(notebook)
        notebook.add(self.hour_tab, text="Sales by Hour")
        self.create_hour_tab()
        
        # Tab 2: Top Products
        self.products_tab = tk.Frame(notebook)
        notebook.add(self.products_tab, text="Top Products")
        self.create_products_tab()
        
        # Tab 3: Payment Methods
        self.payment_tab = tk.Frame(notebook)
        notebook.add(self.payment_tab, text="Payment Methods")
        self.create_payment_tab()
        
        # Tab 4: Transaction List
        self.transactions_tab = tk.Frame(notebook)
        notebook.add(self.transactions_tab, text="Transactions")
        self.create_transactions_tab()
    
    def create_hour_tab(self):
        columns = ('Hour', 'Transactions', 'Sales', 'Items')
        self.hour_tree = ttk.Treeview(self.hour_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'Hour': 100, 'Transactions': 100, 'Sales': 120, 'Items': 100}
        
        for col in columns:
            self.hour_tree.heading(col, text=col)
            self.hour_tree.column(col, width=col_widths.get(col, 100))
        
        self.hour_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def create_products_tab(self):
        columns = ('Product', 'Quantity', 'Revenue', 'Avg Price')
        self.products_tree = ttk.Treeview(self.products_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'Product': 200, 'Quantity': 80, 'Revenue': 120, 'Avg Price': 100}
        
        for col in columns:
            self.products_tree.heading(col, text=col)
            self.products_tree.column(col, width=col_widths.get(col, 100))
        
        self.products_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def create_payment_tab(self):
        columns = ('Method', 'Transactions', 'Amount', 'Percentage')
        self.payment_tree = ttk.Treeview(self.payment_tab, columns=columns, show='headings', height=10)
        
        col_widths = {'Method': 120, 'Transactions': 100, 'Amount': 120, 'Percentage': 100}
        
        for col in columns:
            self.payment_tree.heading(col, text=col)
            self.payment_tree.column(col, width=col_widths.get(col, 100))
        
        self.payment_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    def create_transactions_tab(self):
        columns = ('Time', 'ID', 'Customer', 'Items', 'Total', 'Payment')
        self.trans_tree = ttk.Treeview(self.transactions_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'Time': 80, 'ID': 50, 'Customer': 120, 'Items': 200, 'Total': 80, 'Payment': 80}
        
        for col in columns:
            self.trans_tree.heading(col, text=col)
            self.trans_tree.column(col, width=col_widths.get(col, 80))
        
        self.trans_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.trans_tree.bind('<Double-Button-1>', self.view_receipt)
    
    def load_report(self):
        date = self.date_var.get().strip()
        
        # Clear all trees
        for tree in [self.hour_tree, self.products_tree, self.payment_tree, self.trans_tree]:
            for row in tree.get_children():
                tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get sales for the date
        c.execute('''SELECT id, datetime, customer_name, items, total, payment_method 
                     FROM sales 
                     WHERE DATE(datetime) = ?
                     ORDER BY datetime''', (date,))
        transactions = c.fetchall()
        
        # Calculate totals
        total_sales = sum(t[4] for t in transactions)
        trans_count = len(transactions)
        avg_sale = total_sales / trans_count if trans_count > 0 else 0
        
        # Get items sold count
        items_sold = 0
        for t in transactions:
            items_str = t[3]
            if items_str:
                items_sold += items_str.count('x')
        
        # Update summary labels
        self.total_sales_label.config(text=f"{CURRENCY_SYMBOL}{total_sales:.2f}")
        self.trans_count_label.config(text=str(trans_count))
        self.avg_sale_label.config(text=f"{CURRENCY_SYMBOL}{avg_sale:.2f}")
        self.items_sold_label.config(text=str(items_sold))
        
        # Hourly breakdown
        hourly = {}
        for t in transactions:
            hour = t[1][11:13] + ":00"
            if hour not in hourly:
                hourly[hour] = {'count': 0, 'total': 0, 'items': 0}
            hourly[hour]['count'] += 1
            hourly[hour]['total'] += t[4]
            items_str = t[3]
            if items_str:
                hourly[hour]['items'] += items_str.count('x')
        
        for hour, data in sorted(hourly.items()):
            self.hour_tree.insert('', tk.END, values=(hour, data['count'], 
                                                      f"{CURRENCY_SYMBOL}{data['total']:.2f}", data['items']))
        
        # Product breakdown
        c.execute('''SELECT product_name, SUM(quantity), SUM(final_price) 
                     FROM sale_items si
                     JOIN sales s ON si.sale_id = s.id
                     WHERE DATE(s.datetime) = ?
                     GROUP BY product_name
                     ORDER BY SUM(quantity) DESC''', (date,))
        products = c.fetchall()
        
        if products:
            for p in products:
                avg_price = p[2] / p[1] if p[1] > 0 else 0
                self.products_tree.insert('', tk.END, values=(p[0], p[1], 
                                                             f"{CURRENCY_SYMBOL}{p[2]:.2f}", 
                                                             f"{CURRENCY_SYMBOL}{avg_price:.2f}"))
        else:
            self.products_tree.insert('', tk.END, values=("No data", 0, f"{CURRENCY_SYMBOL}0", f"{CURRENCY_SYMBOL}0"))
        
        # Payment methods breakdown
        methods = {}
        for t in transactions:
            method = t[5] or "Cash"
            if method not in methods:
                methods[method] = {'count': 0, 'total': 0}
            methods[method]['count'] += 1
            methods[method]['total'] += t[4]
        
        for method, data in methods.items():
            percentage = (data['total'] / total_sales * 100) if total_sales > 0 else 0
            self.payment_tree.insert('', tk.END, values=(method, data['count'], 
                                                         f"{CURRENCY_SYMBOL}{data['total']:.2f}", 
                                                         f"{percentage:.1f}%"))
        
        # Transactions list
        for t in transactions:
            self.trans_tree.insert('', tk.END, values=(t[1][11:19], t[0], t[2] or "Walk-in", 
                                                      t[3][:30], f"{CURRENCY_SYMBOL}{t[4]:.2f}", t[5] or "Cash"))
        
        conn.close()
    
    def today_report(self):
        self.date_var.set(datetime.now().strftime('%Y-%m-%d'))
        self.load_report()
    
    def yesterday_report(self):
        yesterday = datetime.now() - timedelta(days=1)
        self.date_var.set(yesterday.strftime('%Y-%m-%d'))
        self.load_report()
    
    def export_csv(self):
        date = self.date_var.get().strip()
        filename = f"reports/sales_report_{date}.csv"
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT datetime, customer_name, items, total, payment_method 
                     FROM sales 
                     WHERE DATE(datetime) = ?
                     ORDER BY datetime''', (date,))
        transactions = c.fetchall()
        conn.close()
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Time', 'Customer', 'Items', 'Total', 'Payment Method'])
            for t in transactions:
                writer.writerow([t[0][11:19], t[1] or 'Walk-in', t[2], f"{CURRENCY_SYMBOL}{t[3]:.2f}", t[4] or 'Cash'])
        
        show_success(f"Report exported to {filename}")
        os.startfile('reports')
    
    def view_receipt(self, event):
        selected = self.trans_tree.selection()
        if not selected:
            return
        
        sale_id = self.trans_tree.item(selected[0])['values'][1]
        
        import glob
        files = glob.glob(f"receipts/receipt_{sale_id}_*.txt")
        if files:
            os.startfile(files[0])
        else:
            show_error(f"Receipt file for sale #{sale_id} not found")