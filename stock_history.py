# stock_history.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, show_error, show_success

class StockHistory:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Stock Adjustment History")
        self.window.geometry("1100x650")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1100) // 2
        y = (self.window.winfo_screenheight() - 650) // 2
        self.window.geometry(f"1100x650+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_products()
        self.load_history()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📋 STOCK ADJUSTMENT HISTORY", fg='white', bg='#f39c12',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 AS AT: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Filter Frame
        filter_frame = tk.Frame(self.window, bg='#ecf0f1', padx=10, pady=8)
        filter_frame.pack(fill=tk.X)
        
        tk.Label(filter_frame, text="Product:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.product_filter = ttk.Combobox(filter_frame, width=30, font=('Arial', 10))
        self.product_filter.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.product_filter.bind('<<ComboboxSelected>>', lambda e: self.load_history())
        
        tk.Label(filter_frame, text="Reason:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.reason_filter = ttk.Combobox(filter_frame, width=20, font=('Arial', 10))
        self.reason_filter.grid(row=0, column=3, padx=5, pady=5, sticky='w')
        self.reason_filter.bind('<<ComboboxSelected>>', lambda e: self.load_history())
        
        tk.Label(filter_frame, text="From:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.from_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(filter_frame, text="To:", font=('Arial', 10)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.to_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.to_date.grid(row=1, column=3, padx=5, pady=5, sticky='w')
        
        # Buttons
        tk.Button(filter_frame, text="🔍 Apply Filter", command=self.load_history,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=12, cursor='hand2').grid(row=2, column=0, columnspan=2, pady=10)
        
        tk.Button(filter_frame, text="🔄 Reset", command=self.reset_filters,
                 bg='#95a5a6', fg='white', font=('Arial', 9),
                 width=10, cursor='hand2').grid(row=2, column=2, columnspan=2, pady=10)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('Date', 'Product', 'Old Stock', 'New Stock', 'Change', 'Reason', 'Adjusted By', 'Notes')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column Widths
        col_widths = {'Date': 140, 'Product': 200, 'Old Stock': 70, 'New Stock': 70,
                     'Change': 60, 'Reason': 120, 'Adjusted By': 100, 'Notes': 200}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Color coding
        self.tree.tag_configure('positive', foreground='#27ae60')  # Green for increase
        self.tree.tag_configure('negative', foreground='#e74c3c')  # Red for decrease
        
        # Summary Frame
        summary_frame = tk.Frame(self.window, bg='#ecf0f1', height=50)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Total Adjustments:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=20, y=15)
        self.total_label = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'))
        self.total_label.place(x=150, y=15)
        
        tk.Label(summary_frame, text="Net Change:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=250, y=15)
        self.net_change = tk.Label(summary_frame, text="0", bg='#ecf0f1', font=('Arial', 10, 'bold'), fg='#2980b9')
        self.net_change.place(x=350, y=15)
        
        tk.Button(summary_frame, text="📊 Export CSV", command=self.export_csv,
                 bg='#27ae60', fg='white', font=('Arial', 9),
                 width=12, cursor='hand2').place(x=500, y=10)
        
        tk.Button(summary_frame, text="🔄 Refresh", command=self.load_history,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=10, cursor='hand2').place(x=650, y=10)
    
    def load_products(self):
        """Load products for filter dropdown"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT product_name FROM stock_adjustments ORDER BY product_name")
        products = c.fetchall()
        conn.close()
        
        product_list = ['All Products'] + [p[0] for p in products]
        self.product_filter['values'] = product_list
        self.product_filter.set('All Products')
        
        # Load reasons
        self.reason_filter['values'] = ['All Reasons', 'Physical count', 'Damaged', 'Expired', 
                                        'Found in warehouse', 'Correction', 'Stock take', 'Other']
        self.reason_filter.set('All Reasons')
    
    def load_history(self):
        """Load stock adjustment history"""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        product = self.product_filter.get()
        reason = self.reason_filter.get()
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        query = '''SELECT adjustment_date, product_name, old_stock, new_stock, 
                          adjustment, reason, adjusted_by, notes
                   FROM stock_adjustments
                   WHERE DATE(adjustment_date) BETWEEN ? AND ?'''
        params = [from_d, to_d]
        
        if product and product != 'All Products':
            query += " AND product_name = ?"
            params.append(product)
        
        if reason and reason != 'All Reasons':
            query += " AND reason = ?"
            params.append(reason)
        
        query += " ORDER BY adjustment_date DESC"
        
        c.execute(query, params)
        adjustments = c.fetchall()
        conn.close()
        
        total = 0
        net = 0
        
        for adj in adjustments:
            date, product, old, new, change, reason, by, notes = adj
            
            # Determine tag based on change
            tag = 'positive' if change > 0 else 'negative'
            
            self.tree.insert('', tk.END, values=(
                date[:16] if date else '',
                product,
                old,
                new,
                f"{change:+d}",
                reason,
                by,
                notes or ''
            ), tags=(tag,))
            
            total += 1
            net += change
        
        self.total_label.config(text=str(total))
        self.net_change.config(text=f"{net:+d}")
    
    def reset_filters(self):
        """Reset all filters"""
        self.product_filter.set('All Products')
        self.reason_filter.set('All Reasons')
        self.from_date.delete(0, tk.END)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.to_date.delete(0, tk.END)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.load_history()
    
    def export_csv(self):
        """Export history to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Stock History"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(['Date', 'Product', 'Old Stock', 'New Stock', 
                                'Change', 'Reason', 'Adjusted By', 'Notes'])
                writer.writerow([f"Period: {self.from_date.get()} to {self.to_date.get()}", "", "", "", "", "", "", ""])
                writer.writerow([])
                
                # Write data
                for item in self.tree.get_children():
                    values = self.tree.item(item)['values']
                    writer.writerow(values)
                
                # Write summary
                writer.writerow([])
                writer.writerow(['Total Adjustments', self.total_label.cget('text'), '', '', '', '', '', ''])
                writer.writerow(['Net Change', self.net_change.cget('text'), '', '', '', '', '', ''])
            
            show_success(f"History exported to {filename}")
            
        except Exception as e:
            show_error(f"Error exporting: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    sh = StockHistory(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()