# stock_adjustment.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, show_error, show_success

class StockAdjustment:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Stock Adjustment History")
        self.window.geometry("1000x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"1000x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Create adjustments table if not exists
        self.create_adjustments_table()
        
        self.create_widgets()
        self.load_adjustments()
    
    def create_adjustments_table(self):
        """Create stock adjustments table if not exists"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS stock_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            old_stock INTEGER,
            new_stock INTEGER,
            adjustment INTEGER,
            reason TEXT,
            adjusted_by TEXT,
            adjustment_date DATETIME,
            notes TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📊 STOCK ADJUSTMENT HISTORY", fg='white', bg='#f39c12',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 AS AT: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Filter Frame
        filter_frame = tk.Frame(self.window, bg='#ecf0f1', padx=10, pady=5)
        filter_frame.pack(fill=tk.X)
        
        tk.Label(filter_frame, text="Filter by Product:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.product_filter = ttk.Combobox(filter_frame, width=30, font=('Arial', 10))
        self.product_filter.pack(side=tk.LEFT, padx=5)
        self.product_filter.bind('<<ComboboxSelected>>', lambda e: self.load_adjustments())
        
        tk.Label(filter_frame, text="From:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(20,5))
        self.from_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.to_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.to_date.pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="🔍 Filter", command=self.load_adjustments,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=10)
        
        tk.Button(filter_frame, text="🔄 Reset", command=self.reset_filters,
                 bg='#95a5a6', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('Date', 'Product', 'Old Stock', 'New Stock', 'Adjustment', 'Reason', 'Adjusted By', 'Notes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column Widths
        col_widths = {'Date': 120, 'Product': 200, 'Old Stock': 70, 'New Stock': 70,
                     'Adjustment': 70, 'Reason': 120, 'Adjusted By': 100, 'Notes': 150}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Color coding for adjustments
        self.tree.tag_configure('positive', foreground='#27ae60')  # Green for increase
        self.tree.tag_configure('negative', foreground='#e74c3c')  # Red for decrease
        
        # Summary Frame
        summary_frame = tk.Frame(self.window, bg='#ecf0f1', height=50)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Total Adjustments:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=20, y=15)
        self.total_adjustments = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'))
        self.total_adjustments.place(x=150, y=15)
        
        tk.Label(summary_frame, text="Net Stock Change:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=250, y=15)
        self.net_change = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'), fg='#2980b9')
        self.net_change.place(x=380, y=15)
        
        # Export button
        tk.Button(summary_frame, text="📊 Export to CSV", command=self.export_csv,
                 bg='#27ae60', fg='white', font=('Arial', 9),
                 width=15, cursor='hand2').place(x=550, y=10)
        
        # Load products for filter
        self.load_products()
    
    def load_products(self):
        """Load products for filter dropdown"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM products ORDER BY name")
        products = c.fetchall()
        conn.close()
        
        self.products = products
        product_list = ['All Products'] + [p[1] for p in products]
        self.product_filter['values'] = product_list
        self.product_filter.set('All Products')
    
    def load_adjustments(self):
        """Load stock adjustments from database"""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        product_filter = self.product_filter.get()
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT adjustment_date, product_name, old_stock, new_stock, 
                          adjustment, reason, adjusted_by, notes
                   FROM stock_adjustments
                   WHERE DATE(adjustment_date) BETWEEN ? AND ?'''
        params = [from_d, to_d]
        
        if product_filter and product_filter != 'All Products':
            query += " AND product_name = ?"
            params.append(product_filter)
        
        query += " ORDER BY adjustment_date DESC"
        
        c.execute(query, params)
        adjustments = c.fetchall()
        conn.close()
        
        total_adj = 0
        net_change = 0
        
        for adj in adjustments:
            date, product, old, new, adj_val, reason, by, notes = adj
            
            # Determine tag based on adjustment direction
            tag = 'positive' if adj_val > 0 else 'negative'
            
            self.tree.insert('', tk.END, values=(
                date[:16] if date else '',
                product,
                old,
                new,
                f"{adj_val:+d}",
                reason,
                by,
                notes or ''
            ), tags=(tag,))
            
            total_adj += 1
            net_change += adj_val
        
        # Update summary
        self.total_adjustments.config(text=str(total_adj))
        self.net_change.config(text=f"{net_change:+d} units")
    
    def reset_filters(self):
        """Reset all filters"""
        self.product_filter.set('All Products')
        self.from_date.delete(0, tk.END)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.to_date.delete(0, tk.END)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.load_adjustments()
    
    def add_adjustment(self, product_id, product_name, old_stock, new_stock, reason, notes=''):
        """Add a stock adjustment record (called from other modules)"""
        adjustment = new_stock - old_stock
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO stock_adjustments 
                    (product_id, product_name, old_stock, new_stock, adjustment, 
                     reason, adjusted_by, adjustment_date, notes)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                  (product_id, product_name, old_stock, new_stock, adjustment,
                   reason, self.username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notes))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Stock adjustment recorded: {product_name} {old_stock} → {new_stock} ({adjustment:+d})")
    
    def export_csv(self):
        """Export adjustments to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Stock Adjustments"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Date', 'Product', 'Old Stock', 'New Stock', 
                                'Adjustment', 'Reason', 'Adjusted By', 'Notes'])
                writer.writerow([f"Period: {self.from_date.get()} to {self.to_date.get()}", "", "", "", "", "", "", ""])
                writer.writerow([])
                
                # Write data
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    writer.writerow(values)
                
                # Write summary
                writer.writerow([])
                writer.writerow(['Total Adjustments', self.total_adjustments.cget('text'), '', '', '', '', '', ''])
                writer.writerow(['Net Stock Change', self.net_change.cget('text'), '', '', '', '', '', ''])
            
            show_success(f"Adjustments exported to {filename}")
            
        except Exception as e:
            show_error(f"Error exporting: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    sa = StockAdjustment(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()