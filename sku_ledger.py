# sku_ledger.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL

class SKULedger:
    def __init__(self, parent, username, working_date, product_id=None):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.product_id = product_id
        self.window = tk.Toplevel(parent)
        self.window.title("SKU Ledger")
        self.window.geometry("1000x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"1000x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_products()
        if product_id:
            self.load_product_ledger(product_id)
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📒 SKU LEDGER", fg='white', bg='#3498db',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Main Paned Window
        paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Panel - Product Selection
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=300)
        paned.add(left_frame, width=300, minsize=250)
        
        tk.Label(left_frame, text="🔍 SELECT PRODUCT", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        # Search frame
        search_frame = tk.Frame(left_frame, bg='#ecf0f1')
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="Search:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_products())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Product list
        list_frame = tk.Frame(left_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        
        self.product_list = ttk.Treeview(list_frame, columns=('Barcode', 'Stock'), 
                                         show='tree', yscrollcommand=vsb.set, height=20)
        vsb.config(command=self.product_list.yview)
        
        self.product_list.column('#0', width=180)
        self.product_list.heading('#0', text='Product Name')
        self.product_list.heading('Barcode', text='Barcode')
        self.product_list.heading('Stock', text='Stock')
        
        self.product_list.column('Barcode', width=100, anchor='center')
        self.product_list.column('Stock', width=60, anchor='center')
        
        self.product_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.product_list.bind('<<TreeviewSelect>>', self.on_product_select)
        
        # Right Panel - Ledger Details
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=700)
        
        # Product Info Frame
        info_frame = tk.Frame(right_frame, bg='#ecf0f1', height=80)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        info_frame.pack_propagate(False)
        
        self.product_info = tk.Label(info_frame, text="Select a product to view ledger",
                                     bg='#ecf0f1', font=('Arial', 11))
        self.product_info.pack(pady=10)
        
        # Date Range Frame
        range_frame = tk.Frame(right_frame, bg='#f9f9f9')
        range_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(range_frame, text="From:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.from_date = tk.Entry(range_frame, width=12, font=('Arial', 9), relief='solid', bd=1)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(range_frame, text="To:", font=('Arial', 9)).pack(side=tk.LEFT, padx=5)
        self.to_date = tk.Entry(range_frame, width=12, font=('Arial', 9), relief='solid', bd=1)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.to_date.pack(side=tk.LEFT, padx=5)
        
        tk.Button(range_frame, text="🔍 View", command=self.refresh_ledger,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Ledger Treeview
        tree_frame = tk.Frame(right_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        vsb2 = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb2 = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('Date', 'Transaction Type', 'Reference', 'Description', 
                   'In Qty', 'Out Qty', 'Balance Qty', 'Unit Cost', 'Total Value')
        self.ledger_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                        yscrollcommand=vsb2.set, xscrollcommand=hsb2.set, height=15)
        vsb2.config(command=self.ledger_tree.yview)
        hsb2.config(command=self.ledger_tree.xview)
        
        col_widths = {'Date': 90, 'Transaction Type': 120, 'Reference': 100, 'Description': 150,
                     'In Qty': 60, 'Out Qty': 60, 'Balance Qty': 70, 'Unit Cost': 80, 'Total Value': 90}
        
        for col in columns:
            self.ledger_tree.heading(col, text=col)
            self.ledger_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.ledger_tree.grid(row=0, column=0, sticky='nsew')
        vsb2.grid(row=0, column=1, sticky='ns')
        hsb2.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summary Frame
        summary_frame = tk.Frame(right_frame, bg='#ecf0f1', height=50)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Opening Balance:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=20, y=15)
        self.opening_qty = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'))
        self.opening_qty.place(x=140, y=15)
        
        tk.Label(summary_frame, text="Total In:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=220, y=15)
        self.total_in = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'), fg='#27ae60')
        self.total_in.place(x=300, y=15)
        
        tk.Label(summary_frame, text="Total Out:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=380, y=15)
        self.total_out = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'), fg='#e74c3c')
        self.total_out.place(x=460, y=15)
        
        tk.Label(summary_frame, text="Closing Balance:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=540, y=15)
        self.closing_qty = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'), fg='#2980b9')
        self.closing_qty.place(x=660, y=15)
        
        tk.Label(summary_frame, text="Stock Value:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=740, y=15)
        self.stock_value = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0", bg='#ecf0f1', 
                                     font=('Arial', 10, 'bold'), fg='#8e44ad')
        self.stock_value.place(x=840, y=15)
    
    def load_products(self):
        """Load all products into list"""
        for item in self.product_list.get_children():
            self.product_list.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, name, barcode, stock FROM products ORDER BY name''')
        products = c.fetchall()
        conn.close()
        
        for p in products:
            self.product_list.insert('', tk.END, iid=f"PROD_{p[0]}",
                                     text=p[1],
                                     values=(p[2], p[3]))
    
    def search_products(self):
        """Search products by name or barcode"""
        search = self.search_var.get().lower()
        
        for item in self.product_list.get_children():
            self.product_list.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, name, barcode, stock FROM products 
                     WHERE LOWER(name) LIKE ? OR LOWER(barcode) LIKE ?
                     ORDER BY name''', (f'%{search}%', f'%{search}%'))
        products = c.fetchall()
        conn.close()
        
        for p in products:
            self.product_list.insert('', tk.END, iid=f"PROD_{p[0]}",
                                     text=p[1],
                                     values=(p[2], p[3]))
    
    def on_product_select(self, event):
        """Handle product selection"""
        selected = self.product_list.selection()
        if not selected:
            return
        
        product_id = int(selected[0].replace('PROD_', ''))
        self.load_product_ledger(product_id)
    
    def load_product_ledger(self, product_id):
        """Load ledger for selected product"""
        self.product_id = product_id
        self.refresh_ledger()
    
    def refresh_ledger(self):
        """Refresh ledger with current date range"""
        if not self.product_id:
            return
        
        for item in self.ledger_tree.get_children():
            self.ledger_tree.delete(item)
        
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get product details
        c.execute('''SELECT name, barcode, stock, cost_price, price 
                     FROM products WHERE id=?''', (self.product_id,))
        product = c.fetchone()
        
        if not product:
            conn.close()
            return
        
        prod_name, barcode, current_stock, cost_price, sale_price = product
        
        # Update product info
        self.product_info.config(
            text=f"📦 {prod_name} | Barcode: {barcode} | Current Stock: {current_stock} | "
                 f"Cost: {CURRENCY_SYMBOL}{cost_price:.2f} | Sale: {CURRENCY_SYMBOL}{sale_price:.2f}"
        )
        
        # Get all stock movements
        # 1. Purchase Orders Received
        # 2. Sales (from credit_sales and pos sales)
        # 3. Adjustments (future)
        
        movements = []
        
        # Purchase Orders (Stock In)
        c.execute('''
            SELECT po.order_date, 'Purchase', po.po_number, po.notes,
                   poi.quantity, 0, poi.unit_cost
            FROM purchase_orders po
            JOIN po_items poi ON po.id = poi.po_id
            WHERE poi.product_id = ? AND po.status = 'Received'
            AND po.order_date BETWEEN ? AND ?
        ''', (self.product_id, from_d, to_d))
        
        movements.extend(c.fetchall())
        
        # Sales (Stock Out) - from credit_sales
        c.execute('''
            SELECT cs.sale_date, 'Credit Sale', cs.invoice_no, 'Credit Sale',
                   0, cs.total_amount / NULLIF(p.price, 0), p.cost_price
            FROM credit_sales cs
            JOIN products p ON p.id = ?
            WHERE cs.member_id IS NOT NULL
            AND cs.sale_date BETWEEN ? AND ?
        ''', (self.product_id, from_d, to_d))
        
        movements.extend(c.fetchall())
        
        # Sort by date
        movements.sort(key=lambda x: x[0])
        
        # Calculate running balance
        balance = 0
        total_in_qty = 0
        total_out_qty = 0
        
        # Get opening balance before from_date
        c.execute('''
            SELECT COALESCE(SUM(CASE WHEN type='in' THEN qty ELSE 0 END), 0) -
                   COALESCE(SUM(CASE WHEN type='out' THEN qty ELSE 0 END), 0)
            FROM (
                SELECT 'in' as type, quantity as qty
                FROM po_items poi
                JOIN purchase_orders po ON poi.po_id = po.id
                WHERE poi.product_id = ? AND po.status = 'Received' AND po.order_date < ?
                UNION ALL
                SELECT 'out' as type, quantity as qty
                FROM sales_items si
                WHERE si.product_id = ? AND si.sale_date < ?
            )
        ''', (self.product_id, from_d, self.product_id, from_d))
        
        opening = c.fetchone()[0] or 0
        balance = opening
        
        for move in movements:
            date, trans_type, ref, desc, qty_in, qty_out, unit_cost = move
            
            if trans_type == 'Purchase':
                balance += qty_in
                total_in_qty += qty_in
            else:
                balance -= qty_out
                total_out_qty += qty_out
            
            total_value = balance * unit_cost
            
            self.ledger_tree.insert('', tk.END, values=(
                date[:10] if date else '',
                trans_type,
                ref or '',
                desc or '',
                qty_in if qty_in > 0 else '',
                qty_out if qty_out > 0 else '',
                balance,
                f"{CURRENCY_SYMBOL}{unit_cost:.2f}",
                f"{CURRENCY_SYMBOL}{total_value:.2f}"
            ))
        
        conn.close()
        
        # Update summary
        self.opening_qty.config(text=str(opening))
        self.total_in.config(text=str(total_in_qty))
        self.total_out.config(text=str(total_out_qty))
        self.closing_qty.config(text=str(balance))
        self.stock_value.config(text=f"{CURRENCY_SYMBOL}{balance * cost_price:.2f}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    sku = SKULedger(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()