# receipt.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
import os
import glob
from utils import CURRENCY_SYMBOL, format_currency, setup_enter_navigation

def generate_receipt_text(sale_id, cashier, customer, items, subtotal, discount_total, tax_total, total, points_earned=0, points_used=0, conversion_rate=100):
    """Generate formatted receipt text"""
    lines = []
    lines.append("="*42)
    lines.append("            URBAN PULSE")
    lines.append("         Urban Mart & General Store")
    lines.append("="*42)
    lines.append(f"Sale #: {sale_id}")
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Cashier: {cashier}")
    if customer:
        lines.append(f"Customer: {customer['name']}")
        lines.append(f"Phone: {customer['phone']}")
        lines.append(f"Points Balance: {customer['points']}")
    lines.append("-"*42)
    lines.append(f"{'Item':<20} {'Qty':>3} {'Price':>8} {'Disc':>6} {'Total':>9}")
    lines.append("-"*42)
    
    for item in items:
        name = item['name'][:18]
        line = f"{name:<20} {item['qty']:>3} {CURRENCY_SYMBOL}{item['price']:>7.2f} "
        if item.get('discount_percent', 0) > 0:
            line += f"{item['discount_percent']:>5.1f}% "
        elif item.get('is_bogo') and item['qty'] >= 2:
            line += " BOGO "
        else:
            line += " "*6
        line += f"{CURRENCY_SYMBOL}{item.get('final_price', item['price']*item['qty']):>8.2f}"
        lines.append(line)
    
    lines.append("-"*42)
    lines.append(f"{'SUBTOTAL:':>32} {CURRENCY_SYMBOL}{subtotal:>8.2f}")
    
    if discount_total > 0:
        lines.append(f"{'DISCOUNT:':>32} -{CURRENCY_SYMBOL}{discount_total:>8.2f}")
    
    if tax_total > 0:
        lines.append(f"{'GST (17%):':>32} {CURRENCY_SYMBOL}{tax_total:>8.2f}")
    
    if points_used > 0:
        discount = points_used / conversion_rate
        lines.append(f"{'Points Used:':>32} {points_used:>8}")
        lines.append(f"{'Points Discount:':>32} -{CURRENCY_SYMBOL}{discount:>8.2f}")
    
    lines.append("="*42)
    lines.append(f"{'TOTAL:':>32} {CURRENCY_SYMBOL}{total:>8.2f}")
    lines.append("="*42)
    if points_earned > 0:
        lines.append(f"Points Earned: {points_earned}")
    lines.append("         Thank you for shopping!")
    lines.append("          Visit us again!")
    lines.append("="*42)
    
    return "\n".join(lines)

def save_receipt(sale_id, cashier, customer, items, subtotal, discount_total, tax_total, total, points_earned=0, points_used=0, conversion_rate=100):
    """Save receipt to file"""
    filename = f"receipts/receipt_{sale_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    receipt_text = generate_receipt_text(sale_id, cashier, customer, items, subtotal, discount_total, tax_total, total, points_earned, points_used, conversion_rate)
    
    with open(filename, 'w') as f:
        f.write(receipt_text)
    
    return filename, receipt_text

class ReceiptPreview:
    def __init__(self, parent, sale_id, cashier, customer, items, subtotal, discount_total, tax_total, total, points_earned=0, points_used=0):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Receipt #{sale_id}")
        self.window.geometry("550x650")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 550) // 2
        y = (self.window.winfo_screenheight() - 650) // 2
        self.window.geometry(f"550x650+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Get conversion rate
        conversion_rate = self.get_conversion_rate()
        
        self.filename, self.receipt_text = save_receipt(sale_id, cashier, customer, items, subtotal, discount_total, tax_total, total, points_earned, points_used, conversion_rate)
        
        # Title
        tk.Label(self.window, text="Receipt Preview", font=('Arial', 16)).pack(pady=10)
        
        # Receipt text area
        text_frame = tk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        text_area = tk.Text(text_frame, font=('Courier', 10), width=55, height=30)
        scrollbar = tk.Scrollbar(text_frame, command=text_area.yview)
        text_area.configure(yscrollcommand=scrollbar.set)
        
        text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        text_area.insert('1.0', self.receipt_text)
        text_area.config(state='disabled')
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Print", command=self.print_receipt, 
                 bg='blue', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Save Copy", command=self.save_copy, 
                 bg='green', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.window.destroy, 
                 width=10).pack(side=tk.LEFT, padx=5)
        
        self.status = tk.Label(self.window, text=f"Saved as: {self.filename}", fg='green')
        self.status.pack(pady=5)
    
    def get_conversion_rate(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key='points_conversion_rate'")
        result = c.fetchone()
        conn.close()
        return int(result[0]) if result else 100
    
    def print_receipt(self):
        messagebox.showinfo("Print", 
            "To print:\n"
            "1. Open the receipt file\n"
            "2. Press Ctrl+P\n"
            f"File: {self.filename}")
        os.startfile(self.filename)
    
    def save_copy(self):
        from tkinter import filedialog
        new_file = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"receipt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if new_file:
            with open(new_file, 'w') as f:
                f.write(self.receipt_text)
            self.status.config(text=f"Saved as: {new_file}")

class ReceiptHistory:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Receipt History")
        self.window.geometry("600x400")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 400) // 2
        self.window.geometry(f"600x400+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_receipts()
    
    def create_widgets(self):
        # Treeview
        columns = ('ID', 'Date/Time', 'Customer', f'Total ({CURRENCY_SYMBOL})', 'Points Earned', 'Points Used')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        
        col_widths = {'ID': 50, 'Date/Time': 130, 'Customer': 150, f'Total ({CURRENCY_SYMBOL})': 80, 
                     'Points Earned': 100, 'Points Used': 100}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.tree.bind('<Double-Button-1>', self.view_receipt)
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="View Selected", command=self.view_receipt).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def load_receipts(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT id, datetime, customer_name, total, points_earned, points_used 
                     FROM sales ORDER BY id DESC LIMIT 100''')
        receipts = c.fetchall()
        conn.close()
        
        for r in receipts:
            self.tree.insert('', tk.END, values=(r[0], r[1], r[2] or 'Walk-in', 
                                                f"{CURRENCY_SYMBOL}{r[3]:.2f}", r[4], r[5]))
    
    def view_receipt(self, event=None):
        selected = self.tree.selection()
        if not selected:
            return
        
        sale_id = self.tree.item(selected[0])['values'][0]
        
        files = glob.glob(f"receipts/receipt_{sale_id}_*.txt")
        if files:
            os.startfile(files[0])
        else:
            messagebox.showinfo("Info", f"Receipt file for sale #{sale_id} not found")