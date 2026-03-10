# stock_summary.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL

class StockSummary:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Stock Summary Report")
        self.window.geometry("1000x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"1000x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📊 STOCK SUMMARY REPORT", fg='white', bg='#27ae60',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 AS AT: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Summary stats frame
        stats_frame = tk.Frame(self.window, bg='#ecf0f1', height=60)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        stats_frame.pack_propagate(False)
        
        self.total_products = tk.Label(stats_frame, text="Total Products: 0", bg='#ecf0f1',
                                       font=('Arial', 11, 'bold'))
        self.total_products.place(x=20, y=20)
        
        self.total_value = tk.Label(stats_frame, text="Total Stock Value: Rs.0", bg='#ecf0f1',
                                    font=('Arial', 11, 'bold'), fg='#27ae60')
        self.total_value.place(x=200, y=20)
        
        self.low_stock = tk.Label(stats_frame, text="Low Stock Items: 0", bg='#ecf0f1',
                                  font=('Arial', 11, 'bold'), fg='#e74c3c')
        self.low_stock.place(x=420, y=20)
        
        self.out_stock = tk.Label(stats_frame, text="Out of Stock: 0", bg='#ecf0f1',
                                  font=('Arial', 11, 'bold'), fg='#c0392b')
        self.out_stock.place(x=600, y=20)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Category-wise Stock
        self.cat_tab = tk.Frame(notebook)
        notebook.add(self.cat_tab, text="📁 By Category")
        self.create_category_tab()
        
        # Tab 2: All Products
        self.prod_tab = tk.Frame(notebook)
        notebook.add(self.prod_tab, text="📋 All Products")
        self.create_products_tab()
        
        # Tab 3: Low Stock Alert
        self.low_tab = tk.Frame(notebook)
        notebook.add(self.low_tab, text="⚠️ Low Stock Alert")
        self.create_low_stock_tab()
        
        # Export button
        btn_frame = tk.Frame(self.window, bg='#ecf0f1', height=40)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        btn_frame.pack_propagate(False)
        
        tk.Button(btn_frame, text="📊 Export to CSV", command=self.export_csv,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 width=15, cursor='hand2').place(x=10, y=5)
        
        tk.Button(btn_frame, text="🔄 Refresh", command=self.load_data,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 width=12, cursor='hand2').place(x=150, y=5)
        
        tk.Button(btn_frame, text="❌ Close", command=self.window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                 width=10, cursor='hand2').place(x=280, y=5)
    
    def create_category_tab(self):
        """Create category-wise stock view"""
        # Tree frame
        tree_frame = tk.Frame(self.cat_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('Category', 'Products', 'Total Qty', 'Cost Value', 'Sale Value', 'Potential Profit')
        self.cat_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings',
                                      yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        vsb.config(command=self.cat_tree.yview)
        hsb.config(command=self.cat_tree.xview)
        
        # Column widths
        col_widths = {'Category': 250, 'Products': 80, 'Total Qty': 80, 
                     'Cost Value': 100, 'Sale Value': 100, 'Potential Profit': 100}
        
        self.cat_tree.column('#0', width=0, stretch=False)
        for col in columns:
            self.cat_tree.heading(col, text=col)
            self.cat_tree.column(col, width=col_widths.get(col, 100), anchor='center')
        
        self.cat_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to show category products
        self.cat_tree.bind('<Double-Button-1>', self.show_category_products)
    
    def create_products_tab(self):
        """Create all products view"""
        # Search frame
        search_frame = tk.Frame(self.prod_tab, bg='#ecf0f1', height=40)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        search_frame.pack_propagate(False)
        
        tk.Label(search_frame, text="Search:", bg='#ecf0f1', font=('Arial', 10)).place(x=10, y=10)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.search_products())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30,
                                font=('Arial', 10), relief='solid', bd=1)
        search_entry.place(x=70, y=8, height=25)
        
        tk.Label(search_frame, text="Category:", bg='#ecf0f1', font=('Arial', 10)).place(x=300, y=10)
        self.cat_filter_var = tk.StringVar()
        self.cat_filter = ttk.Combobox(search_frame, textvariable=self.cat_filter_var, width=20)
        self.cat_filter.place(x=370, y=8, height=25)
        self.cat_filter.bind('<<ComboboxSelected>>', lambda e: self.search_products())
        
        # Tree frame
        tree_frame = tk.Frame(self.prod_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('ID', 'Barcode', 'Product', 'Category', 'Stock', 'Cost Price', 'Sale Price', 'Stock Value', 'SKU Ledger')
        self.prod_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                       yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        vsb.config(command=self.prod_tree.yview)
        hsb.config(command=self.prod_tree.xview)
        
        col_widths = {'ID': 40, 'Barcode': 100, 'Product': 200, 'Category': 120, 'Stock': 60,
                     'Cost Price': 80, 'Sale Price': 80, 'Stock Value': 90, 'SKU Ledger': 80}
        
        for col in columns:
            self.prod_tree.heading(col, text=col)
            self.prod_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.prod_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to open SKU Ledger
        self.prod_tree.bind('<Double-Button-1>', self.open_sku_ledger)
    
    def create_low_stock_tab(self):
        """Create low stock alert view"""
        # Tree frame
        tree_frame = tk.Frame(self.low_tab)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('ID', 'Product', 'Category', 'Current Stock', 'Reorder Level', 'Status', 'Action')
        self.low_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                      yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        vsb.config(command=self.low_tree.yview)
        hsb.config(command=self.low_tree.xview)
        
        col_widths = {'ID': 40, 'Product': 200, 'Category': 120, 'Current Stock': 80,
                     'Reorder Level': 80, 'Status': 100, 'Action': 80}
        
        for col in columns:
            self.low_tree.heading(col, text=col)
            self.low_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.low_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind double-click to create PO
        self.low_tree.bind('<Double-Button-1>', self.create_purchase_order)
    
    def load_data(self):
        """Load all stock data"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get categories for filter
        c.execute("SELECT id, category_name FROM categories ORDER BY full_path")
        categories = c.fetchall()
        cat_list = ['All Categories'] + [c[1] for c in categories]
        self.cat_filter['values'] = cat_list
        self.cat_filter.set('All Categories')
        
        # Load category-wise summary
        self.load_category_summary(c)
        
        # Load all products
        self.load_all_products(c)
        
        # Load low stock items
        self.load_low_stock(c)
        
        # Update summary stats
        c.execute("SELECT COUNT(*) FROM products")
        total_prod = c.fetchone()[0]
        
        c.execute("SELECT COALESCE(SUM(cost_price * stock), 0) FROM products")
        total_val = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM products WHERE stock <= reorder_level AND stock > 0")
        low_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM products WHERE stock = 0")
        out_count = c.fetchone()[0]
        
        conn.close()
        
        self.total_products.config(text=f"Total Products: {total_prod}")
        self.total_value.config(text=f"Total Stock Value: {CURRENCY_SYMBOL}{total_val:,.2f}")
        self.low_stock.config(text=f"Low Stock Items: {low_count}")
        self.out_stock.config(text=f"Out of Stock: {out_count}")
    
    def load_category_summary(self, cursor):
        """Load category-wise summary"""
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        
        cursor.execute('''
            SELECT c.id, c.category_name, 
                   COUNT(p.id),
                   COALESCE(SUM(p.stock), 0),
                   COALESCE(SUM(p.cost_price * p.stock), 0),
                   COALESCE(SUM(p.price * p.stock), 0)
            FROM categories c
            LEFT JOIN products p ON c.id = p.category_id
            GROUP BY c.id
            ORDER BY c.full_path
        ''')
        
        categories = cursor.fetchall()
        
        grand_total_qty = 0
        grand_total_cost = 0
        grand_total_sale = 0
        
        for cat in categories:
            cat_id, name, prod_count, total_qty, cost_val, sale_val = cat
            profit = sale_val - cost_val
            
            grand_total_qty += total_qty
            grand_total_cost += cost_val
            grand_total_sale += sale_val
            
            self.cat_tree.insert('', tk.END, values=(
                name,
                prod_count,
                total_qty,
                f"{CURRENCY_SYMBOL}{cost_val:,.2f}",
                f"{CURRENCY_SYMBOL}{sale_val:,.2f}",
                f"{CURRENCY_SYMBOL}{profit:,.2f}"
            ))
        
        # Add total row
        self.cat_tree.insert('', tk.END, values=(
            "TOTAL",
            "",
            grand_total_qty,
            f"{CURRENCY_SYMBOL}{grand_total_cost:,.2f}",
            f"{CURRENCY_SYMBOL}{grand_total_sale:,.2f}",
            f"{CURRENCY_SYMBOL}{grand_total_sale - grand_total_cost:,.2f}"
        ), tags=('total',))
        
        self.cat_tree.tag_configure('total', background='#ecf0f1', font=('Arial', 10, 'bold'))
    
    def load_all_products(self, cursor):
        """Load all products"""
        for item in self.prod_tree.get_children():
            self.prod_tree.delete(row)
        
        cursor.execute('''
            SELECT p.id, p.barcode, p.name, c.category_name, p.stock,
                   p.cost_price, p.price, (p.cost_price * p.stock)
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY p.name
        ''')
        
        products = cursor.fetchall()
        
        for p in products:
            self.prod_tree.insert('', tk.END, values=(
                p[0],
                p[1],
                p[2],
                p[3] or 'Uncategorized',
                p[4],
                f"{CURRENCY_SYMBOL}{p[5]:.2f}",
                f"{CURRENCY_SYMBOL}{p[6]:.2f}",
                f"{CURRENCY_SYMBOL}{p[7]:,.2f}",
                "🔍 View"
            ))
    
    def load_low_stock(self, cursor):
        """Load low stock items"""
        for item in self.low_tree.get_children():
            self.low_tree.delete(row)
        
        cursor.execute('''
            SELECT p.id, p.name, c.category_name, p.stock, p.reorder_level,
                   CASE 
                       WHEN p.stock = 0 THEN '🚫 Out of Stock'
                       WHEN p.stock <= p.reorder_level/2 THEN '🔴 Critical'
                       ELSE '🟡 Low'
                   END as status
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.stock <= p.reorder_level
            ORDER BY p.stock ASC
        ''')
        
        items = cursor.fetchall()
        
        for item in items:
            self.low_tree.insert('', tk.END, values=(
                item[0],
                item[1],
                item[2] or 'Uncategorized',
                item[3],
                item[4],
                item[5],
                "📦 Create PO"
            ))
    
    def search_products(self):
        """Search and filter products"""
        search = self.search_var.get().lower()
        category = self.cat_filter_var.get()
        
        for item in self.prod_tree.get_children():
            self.prod_tree.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT p.id, p.barcode, p.name, c.category_name, p.stock,
                          p.cost_price, p.price, (p.cost_price * p.stock)
                   FROM products p
                   LEFT JOIN categories c ON p.category_id = c.id
                   WHERE 1=1'''
        params = []
        
        if search:
            query += " AND (LOWER(p.name) LIKE ? OR LOWER(p.barcode) LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category and category != 'All Categories':
            query += " AND c.category_name = ?"
            params.append(category)
        
        query += " ORDER BY p.name"
        
        c.execute(query, params)
        products = c.fetchall()
        conn.close()
        
        for p in products:
            self.prod_tree.insert('', tk.END, values=(
                p[0],
                p[1],
                p[2],
                p[3] or 'Uncategorized',
                p[4],
                f"{CURRENCY_SYMBOL}{p[5]:.2f}",
                f"{CURRENCY_SYMBOL}{p[6]:.2f}",
                f"{CURRENCY_SYMBOL}{p[7]:,.2f}",
                "🔍 View"
            ))
    
    def show_category_products(self, event):
        """Show products in selected category"""
        selected = self.cat_tree.selection()
        if not selected:
            return
        
        values = self.cat_tree.item(selected[0])['values']
        category = values[0]
        
        if category == "TOTAL":
            return
        
        # Switch to products tab and filter by category
        self.cat_filter_var.set(category)
        self.search_products()
        
        # Switch to products tab
        notebook = self.window.children['!notebook']
        notebook.select(1)
    
    def open_sku_ledger(self, event):
        """Open SKU Ledger for selected product"""
        selected = self.prod_tree.selection()
        if not selected:
            return
        
        product_id = self.prod_tree.item(selected[0])['values'][0]
        
        try:
            from sku_ledger import SKULedger
            SKULedger(self.window, self.username, self.working_date, product_id)
        except ImportError:
            messagebox.showerror("Error", "SKU Ledger module not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening SKU Ledger: {e}")
    
    def create_purchase_order(self, event):
        """Create purchase order for low stock item"""
        selected = self.low_tree.selection()
        if not selected:
            return
        
        product_id = self.low_tree.item(selected[0])['values'][0]
        product_name = self.low_tree.item(selected[0])['values'][1]
        
        if messagebox.askyesno("Create PO", f"Create purchase order for {product_name}?"):
            # This will be implemented when we integrate with supplier manager
            messagebox.showinfo("Coming Soon", "Purchase Order creation coming soon!")
    
    def export_csv(self):
        """Export stock summary to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Stock Summary As"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['STOCK SUMMARY REPORT'])
                writer.writerow([f"As at: {self.working_date}"])
                writer.writerow([])
                
                # Write category summary
                writer.writerow(['CATEGORY SUMMARY'])
                writer.writerow(['Category', 'Products', 'Total Qty', 'Cost Value', 'Sale Value', 'Profit'])
                
                for item in self.cat_tree.get_children():
                    values = self.cat_tree.item(item)['values']
                    writer.writerow(values)
                
                writer.writerow([])
                
                # Write low stock items
                writer.writerow(['LOW STOCK ALERTS'])
                writer.writerow(['Product', 'Category', 'Current Stock', 'Reorder Level', 'Status'])
                
                for item in self.low_tree.get_children():
                    values = self.low_tree.item(item)['values']
                    writer.writerow([values[1], values[2], values[3], values[4], values[5]])
                
            messagebox.showinfo("Success", f"Report exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    ss = StockSummary(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()