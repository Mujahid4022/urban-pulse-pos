# balance_sheet.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL

class BalanceSheet:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Balance Sheet")
        self.window.geometry("900x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"900x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#9b59b6', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📉 BALANCE SHEET", fg='white', bg='#9b59b6',
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
        
        tk.Label(filter_frame, text="As at Date:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.as_at_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.as_at_date.insert(0, self.working_date)
        self.as_at_date.pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="🔍 Refresh", command=self.load_data,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="📊 Export", command=self.export_report,
                 bg='#27ae60', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Main frame for report
        report_frame = tk.Frame(self.window, bg='white', relief=tk.RIDGE, bd=1)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Canvas for scrolling
        canvas = tk.Canvas(report_frame, bg='white', highlightthickness=0)
        scrollbar = tk.Scrollbar(report_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg='white')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Report title
        self.report_title = tk.Label(self.scrollable_frame, text="BALANCE SHEET",
                                     font=('Arial', 14, 'bold'), bg='white', fg='#2c3e50')
        self.report_title.pack(pady=10)
        
        self.date_label = tk.Label(self.scrollable_frame, text=f"As at: {self.working_date}",
                                   font=('Arial', 11), bg='white')
        self.date_label.pack(pady=5)
        
        # Separator
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Two-column layout
        columns_frame = tk.Frame(self.scrollable_frame, bg='white')
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Left Column - Assets
        left_frame = tk.Frame(columns_frame, bg='white')
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(left_frame, text="ASSETS", font=('Arial', 12, 'bold'),
                bg='white', fg='#27ae60').pack(anchor='w')
        
        self.assets_container = tk.Frame(left_frame, bg='white')
        self.assets_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Right Column - Liabilities & Equity
        right_frame = tk.Frame(columns_frame, bg='white')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        tk.Label(right_frame, text="LIABILITIES", font=('Arial', 12, 'bold'),
                bg='white', fg='#e74c3c').pack(anchor='w')
        
        self.liabilities_container = tk.Frame(right_frame, bg='white')
        self.liabilities_container.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(right_frame, text="EQUITY", font=('Arial', 12, 'bold'),
                bg='white', fg='#2980b9').pack(anchor='w', pady=(15,0))
        
        self.equity_container = tk.Frame(right_frame, bg='white')
        self.equity_container.pack(fill=tk.X, padx=10, pady=5)
        
        # Totals Row
        total_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', relief=tk.RIDGE, bd=2)
        total_frame.pack(fill=tk.X, padx=30, pady=15)
        
        total_inner = tk.Frame(total_frame, bg='#2c3e50')
        total_inner.pack(fill=tk.X, padx=10, pady=8)
        
        tk.Label(total_inner, text="TOTAL ASSETS", fg='white', bg='#2c3e50',
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=20)
        self.total_assets = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", fg='white', bg='#2c3e50',
                                     font=('Arial', 11, 'bold'))
        self.total_assets.pack(side=tk.LEFT, padx=20)
        
        tk.Label(total_inner, text="TOTAL LIABILITIES & EQUITY", fg='white', bg='#2c3e50',
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=20)
        self.total_liab_equity = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", fg='white', bg='#2c3e50',
                                         font=('Arial', 11, 'bold'))
        self.total_liab_equity.pack(side=tk.LEFT, padx=20)
    
    def load_data(self):
        """Load balance sheet data"""
        # Clear existing data
        for widget in self.assets_container.winfo_children():
            widget.destroy()
        for widget in self.liabilities_container.winfo_children():
            widget.destroy()
        for widget in self.equity_container.winfo_children():
            widget.destroy()
        
        as_at = self.as_at_date.get()
        self.date_label.config(text=f"As at: {as_at}")
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get all accounts with their balances
        c.execute('''
            SELECT id, account_code, account_name, account_type, current_balance
            FROM accounts
            WHERE is_active = 1
            ORDER BY account_code
        ''')
        
        accounts = c.fetchall()
        
        total_assets = 0
        total_liabilities = 0
        total_equity = 0
        
        # Process each account
        for acc in accounts:
            acc_id, code, name, acc_type, balance = acc
            
            if balance == 0:
                continue
            
            if acc_type == 'Asset':
                total_assets += balance
                self.add_account_row(self.assets_container, code, name, balance)
            
            elif acc_type == 'Liability':
                total_liabilities += balance
                self.add_account_row(self.liabilities_container, code, name, balance)
            
            elif acc_type == 'Equity':
                total_equity += balance
                self.add_account_row(self.equity_container, code, name, balance)
        
        conn.close()
        
        # Add total rows
        self.add_total_row(self.assets_container, "TOTAL ASSETS", total_assets, '#27ae60')
        self.add_total_row(self.liabilities_container, "TOTAL LIABILITIES", total_liabilities, '#e74c3c')
        self.add_total_row(self.equity_container, "TOTAL EQUITY", total_equity, '#2980b9')
        
        # Update footer totals
        self.total_assets.config(text=f"{CURRENCY_SYMBOL}{total_assets:,.2f}")
        total_liab_equity = total_liabilities + total_equity
        self.total_liab_equity.config(text=f"{CURRENCY_SYMBOL}{total_liab_equity:,.2f}")
    
    def add_account_row(self, container, code, name, balance):
        """Add an account row to the container"""
        row = tk.Frame(container, bg='white')
        row.pack(fill=tk.X, pady=2)
        
        tk.Label(row, text=f"{code} - {name}", bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        tk.Label(row, text=f"{CURRENCY_SYMBOL}{balance:,.2f}", bg='white',
                font=('Arial', 10)).pack(side=tk.RIGHT)
    
    def add_total_row(self, container, label, amount, color):
        """Add a total row with separator"""
        tk.Frame(container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        row = tk.Frame(container, bg='white')
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label, bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(row, text=f"{CURRENCY_SYMBOL}{amount:,.2f}", bg='white',
                font=('Arial', 10, 'bold'), fg=color).pack(side=tk.RIGHT)
    
    def export_report(self):
        """Export Balance Sheet to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Balance Sheet"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(['BALANCE SHEET'])
                writer.writerow([f"As at: {self.as_at_date.get()}"])
                writer.writerow([])
                
                # Assets
                writer.writerow(['ASSETS'])
                for child in self.assets_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                
                writer.writerow([])
                
                # Liabilities
                writer.writerow(['LIABILITIES'])
                for child in self.liabilities_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                
                writer.writerow([])
                
                # Equity
                writer.writerow(['EQUITY'])
                for child in self.equity_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                
                writer.writerow([])
                writer.writerow(['TOTAL ASSETS', self.total_assets.cget('text')])
                writer.writerow(['TOTAL LIABILITIES & EQUITY', self.total_liab_equity.cget('text')])
            
            messagebox.showinfo("Success", f"Balance Sheet exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    bs = BalanceSheet(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()