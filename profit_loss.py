# profit_loss.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL

class ProfitLoss:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Profit & Loss Statement")
        self.window.geometry("900x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"900x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_periods()
        self.load_data()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📈 PROFIT & LOSS STATEMENT", fg='white', bg='#27ae60',
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
        
        tk.Label(filter_frame, text="Period:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.period_var = tk.StringVar()
        self.period_combo = ttk.Combobox(filter_frame, textvariable=self.period_var, width=20, font=('Arial', 10))
        self.period_combo.pack(side=tk.LEFT, padx=5)
        self.period_combo.bind('<<ComboboxSelected>>', lambda e: self.load_data())
        
        tk.Label(filter_frame, text="From:", font=('Arial', 10)).pack(side=tk.LEFT, padx=(20,5))
        self.from_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.from_date.pack(side=tk.LEFT, padx=5)
        
        tk.Label(filter_frame, text="To:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.to_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.to_date.pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="🔍 Generate", command=self.load_data,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=10)
        
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
        self.report_title = tk.Label(self.scrollable_frame, text="PROFIT & LOSS STATEMENT",
                                     font=('Arial', 14, 'bold'), bg='white', fg='#2c3e50')
        self.report_title.pack(pady=10)
        
        self.period_label = tk.Label(self.scrollable_frame, text="",
                                     font=('Arial', 11), bg='white')
        self.period_label.pack(pady=5)
        
        # Separator
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Income Section
        self.income_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.income_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.income_frame, text="INCOME", font=('Arial', 12, 'bold'),
                bg='white', fg='#27ae60').pack(anchor='w')
        
        self.income_container = tk.Frame(self.income_frame, bg='white')
        self.income_container.pack(fill=tk.X, padx=20, pady=5)
        
        # COGS Section
        self.cogs_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.cogs_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.cogs_frame, text="COST OF GOODS SOLD", font=('Arial', 12, 'bold'),
                bg='white', fg='#e67e22').pack(anchor='w')
        
        self.cogs_container = tk.Frame(self.cogs_frame, bg='white')
        self.cogs_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Gross Profit
        self.gross_frame = tk.Frame(self.scrollable_frame, bg='#ecf0f1', relief=tk.RIDGE, bd=1)
        self.gross_frame.pack(fill=tk.X, padx=30, pady=10)
        
        self.gross_profit = tk.Label(self.gross_frame, text="GROSS PROFIT: Rs. 0.00",
                                      font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2980b9')
        self.gross_profit.pack(pady=5)
        
        # Expenses Section
        self.expense_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.expense_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.expense_frame, text="EXPENSES", font=('Arial', 12, 'bold'),
                bg='white', fg='#e74c3c').pack(anchor='w')
        
        self.expense_container = tk.Frame(self.expense_frame, bg='white')
        self.expense_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Net Profit
        self.net_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', relief=tk.RIDGE, bd=2)
        self.net_frame.pack(fill=tk.X, padx=30, pady=15)
        
        self.net_profit = tk.Label(self.net_frame, text="NET PROFIT: Rs. 0.00",
                                    font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50')
        self.net_profit.pack(pady=8)
    
    def load_periods(self):
        """Load predefined periods"""
        periods = [
            'Custom',
            'Today',
            'This Week',
            'This Month',
            'This Quarter',
            'This Year',
            'Last Month',
            'Last Quarter',
            'Last Year'
        ]
        self.period_combo['values'] = periods
        self.period_combo.set('This Month')
        
        # Set default dates
        today = datetime.now()
        first_day = today.replace(day=1)
        self.from_date.insert(0, first_day.strftime('%Y-%m-%d'))
        self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        self.period_combo.bind('<<ComboboxSelected>>', self.on_period_change)
    
    def on_period_change(self, event=None):
        """Handle period selection"""
        period = self.period_var.get()
        today = datetime.now()
        
        if period == 'Today':
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, today.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        elif period == 'This Week':
            start = today - timedelta(days=today.weekday())
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        elif period == 'This Month':
            start = today.replace(day=1)
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        elif period == 'This Quarter':
            quarter = (today.month - 1) // 3
            start = today.replace(month=quarter*3 + 1, day=1)
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        elif period == 'This Year':
            start = today.replace(month=1, day=1)
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, today.strftime('%Y-%m-%d'))
        
        elif period == 'Last Month':
            first = today.replace(day=1)
            last_month = first - timedelta(days=1)
            start = last_month.replace(day=1)
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, last_month.strftime('%Y-%m-%d'))
        
        elif period == 'Last Quarter':
            current_quarter = (today.month - 1) // 3
            if current_quarter == 0:
                # Last quarter of previous year
                start = today.replace(year=today.year-1, month=10, day=1)
                end = today.replace(year=today.year-1, month=12, day=31)
            else:
                start = today.replace(month=(current_quarter-1)*3 + 1, day=1)
                end = today.replace(month=current_quarter*3, day=1) - timedelta(days=1)
            
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, end.strftime('%Y-%m-%d'))
        
        elif period == 'Last Year':
            start = today.replace(year=today.year-1, month=1, day=1)
            end = today.replace(year=today.year-1, month=12, day=31)
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start.strftime('%Y-%m-%d'))
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, end.strftime('%Y-%m-%d'))
    
    def load_data(self):
        """Load profit & loss data"""
        # Clear existing data
        for widget in self.income_container.winfo_children():
            widget.destroy()
        for widget in self.cogs_container.winfo_children():
            widget.destroy()
        for widget in self.expense_container.winfo_children():
            widget.destroy()
        
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        self.period_label.config(text=f"For the period: {from_d} to {to_d}")
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # 1. INCOME (Revenue accounts)
        c.execute('''
            SELECT a.account_code, a.account_name, 
                   COALESCE(SUM(le.credit), 0) as amount
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_type = 'Income'
            AND le.entry_date BETWEEN ? AND ?
            GROUP BY a.id
            HAVING amount > 0
            ORDER BY a.account_code
        ''', (from_d, to_d))
        
        incomes = c.fetchall()
        total_income = 0
        
        for inc in incomes:
            code, name, amount = inc
            total_income += amount
            
            row = tk.Frame(self.income_container, bg='white')
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{code} - {name}", bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
            tk.Label(row, text=f"{CURRENCY_SYMBOL}{amount:,.2f}", bg='white', 
                    font=('Arial', 10, 'bold')).pack(side=tk.RIGHT)
        
        # Total Income row
        tk.Frame(self.income_container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        total_income_row = tk.Frame(self.income_container, bg='white')
        total_income_row.pack(fill=tk.X, pady=2)
        tk.Label(total_income_row, text="TOTAL INCOME", bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.total_income_label = tk.Label(total_income_row, text=f"{CURRENCY_SYMBOL}{total_income:,.2f}",
                                          bg='white', font=('Arial', 10, 'bold'), fg='#27ae60')
        self.total_income_label.pack(side=tk.RIGHT)
        
        # 2. COST OF GOODS SOLD
        # Opening Stock (from previous period)
        c.execute('''
            SELECT COALESCE(SUM(p.cost_price * p.stock), 0)
            FROM products p
            WHERE p.id IN (
                SELECT DISTINCT product_id FROM po_items
                UNION
                SELECT DISTINCT id FROM products WHERE stock > 0
            )
        ''')
        opening_stock = c.fetchone()[0]
        
        # Purchases during period
        c.execute('''
            SELECT COALESCE(SUM(le.debit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '5500%'  -- Purchase Account
            AND le.entry_date BETWEEN ? AND ?
        ''', (from_d, to_d))
        purchases = c.fetchone()[0]
        
        # Closing Stock (current stock)
        c.execute('SELECT COALESCE(SUM(cost_price * stock), 0) FROM products')
        closing_stock = c.fetchone()[0]
        
        # COGS calculation
        cogs = opening_stock + purchases - closing_stock
        
        # Display COGS components
        cogs_items = [
            ("Opening Stock", opening_stock),
            ("Add: Purchases", purchases),
            ("Less: Closing Stock", -closing_stock)
        ]
        
        for label, amount in cogs_items:
            row = tk.Frame(self.cogs_container, bg='white')
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=label, bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
            tk.Label(row, text=f"{CURRENCY_SYMBOL}{abs(amount):,.2f}", bg='white',
                    font=('Arial', 10)).pack(side=tk.RIGHT)
        
        tk.Frame(self.cogs_container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        cogs_row = tk.Frame(self.cogs_container, bg='white')
        cogs_row.pack(fill=tk.X, pady=2)
        tk.Label(cogs_row, text="COST OF GOODS SOLD", bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.cogs_label = tk.Label(cogs_row, text=f"{CURRENCY_SYMBOL}{cogs:,.2f}",
                                   bg='white', font=('Arial', 10, 'bold'), fg='#e67e22')
        self.cogs_label.pack(side=tk.RIGHT)
        
        # 3. Gross Profit
        gross_profit = total_income - cogs
        self.gross_profit.config(text=f"GROSS PROFIT: {CURRENCY_SYMBOL}{gross_profit:,.2f}")
        
        # 4. EXPENSES
        c.execute('''
            SELECT a.account_code, a.account_name, 
                   COALESCE(SUM(le.debit), 0) as amount
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_type = 'Expense'
            AND a.account_code NOT LIKE '5500%'  -- Exclude Purchase account
            AND le.entry_date BETWEEN ? AND ?
            GROUP BY a.id
            HAVING amount > 0
            ORDER BY a.account_code
        ''', (from_d, to_d))
        
        expenses = c.fetchall()
        total_expenses = 0
        
        for exp in expenses:
            code, name, amount = exp
            total_expenses += amount
            
            row = tk.Frame(self.expense_container, bg='white')
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{code} - {name}", bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
            tk.Label(row, text=f"{CURRENCY_SYMBOL}{amount:,.2f}", bg='white',
                    font=('Arial', 10)).pack(side=tk.RIGHT)
        
        tk.Frame(self.expense_container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        total_exp_row = tk.Frame(self.expense_container, bg='white')
        total_exp_row.pack(fill=tk.X, pady=2)
        tk.Label(total_exp_row, text="TOTAL EXPENSES", bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        self.total_expenses_label = tk.Label(total_exp_row, text=f"{CURRENCY_SYMBOL}{total_expenses:,.2f}",
                                            bg='white', font=('Arial', 10, 'bold'), fg='#e74c3c')
        self.total_expenses_label.pack(side=tk.RIGHT)
        
        # 5. Net Profit
        net_profit = gross_profit - total_expenses
        self.net_profit.config(text=f"NET PROFIT: {CURRENCY_SYMBOL}{net_profit:,.2f}")
        
        conn.close()
    
    def export_report(self):
        """Export P&L to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Profit & Loss Report"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(['PROFIT & LOSS STATEMENT'])
                writer.writerow([f"Period: {self.from_date.get()} to {self.to_date.get()}"])
                writer.writerow([])
                
                # Income
                writer.writerow(['INCOME'])
                for child in self.income_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                if 'TOTAL' in subchild.cget('text'):
                                    writer.writerow(['', subchild.cget('text'), 
                                                    self.total_income_label.cget('text')])
                                else:
                                    text = subchild.cget('text')
                                    if text.startswith(CURRENCY_SYMBOL):
                                        writer.writerow(['', '', text])
                                    else:
                                        writer.writerow([text])
                
                writer.writerow([])
                
                # COGS
                writer.writerow(['COST OF GOODS SOLD'])
                for child in self.cogs_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                if 'COST OF GOODS SOLD' in subchild.cget('text'):
                                    writer.writerow(['', subchild.cget('text'), 
                                                    self.cogs_label.cget('text')])
                                else:
                                    text = subchild.cget('text')
                                    if text.startswith(CURRENCY_SYMBOL):
                                        writer.writerow(['', '', text])
                                    else:
                                        writer.writerow([text])
                
                writer.writerow([])
                writer.writerow(['GROSS PROFIT', '', self.gross_profit.cget('text').split(': ')[1]])
                writer.writerow([])
                
                # Expenses
                writer.writerow(['EXPENSES'])
                for child in self.expense_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                if 'TOTAL' in subchild.cget('text'):
                                    writer.writerow(['', subchild.cget('text'), 
                                                    self.total_expenses_label.cget('text')])
                                else:
                                    text = subchild.cget('text')
                                    if text.startswith(CURRENCY_SYMBOL):
                                        writer.writerow(['', '', text])
                                    else:
                                        writer.writerow([text])
                
                writer.writerow([])
                writer.writerow(['NET PROFIT', '', self.net_profit.cget('text').split(': ')[1]])
            
            messagebox.showinfo("Success", f"Report exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    pl = ProfitLoss(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()