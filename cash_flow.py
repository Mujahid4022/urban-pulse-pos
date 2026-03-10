# cash_flow.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL

class CashFlow:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Cash Flow Statement")
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
        title_frame = tk.Frame(self.window, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="💰 CASH FLOW STATEMENT", fg='white', bg='#3498db',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
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
        self.report_title = tk.Label(self.scrollable_frame, text="CASH FLOW STATEMENT",
                                     font=('Arial', 14, 'bold'), bg='white', fg='#2c3e50')
        self.report_title.pack(pady=10)
        
        self.period_label = tk.Label(self.scrollable_frame, text="",
                                     font=('Arial', 11), bg='white')
        self.period_label.pack(pady=5)
        
        # Separator
        ttk.Separator(self.scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Operating Activities
        self.operating_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.operating_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.operating_frame, text="OPERATING ACTIVITIES", font=('Arial', 12, 'bold'),
                bg='white', fg='#27ae60').pack(anchor='w')
        
        self.operating_container = tk.Frame(self.operating_frame, bg='white')
        self.operating_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Investing Activities
        self.investing_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.investing_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.investing_frame, text="INVESTING ACTIVITIES", font=('Arial', 12, 'bold'),
                bg='white', fg='#e67e22').pack(anchor='w')
        
        self.investing_container = tk.Frame(self.investing_frame, bg='white')
        self.investing_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Financing Activities
        self.financing_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.financing_frame.pack(fill=tk.X, padx=30, pady=5)
        
        tk.Label(self.financing_frame, text="FINANCING ACTIVITIES", font=('Arial', 12, 'bold'),
                bg='white', fg='#e74c3c').pack(anchor='w')
        
        self.financing_container = tk.Frame(self.financing_frame, bg='white')
        self.financing_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Net Cash Flow
        self.net_frame = tk.Frame(self.scrollable_frame, bg='#ecf0f1', relief=tk.RIDGE, bd=1)
        self.net_frame.pack(fill=tk.X, padx=30, pady=10)
        
        self.net_cash = tk.Label(self.net_frame, text="NET CASH FLOW: Rs. 0.00",
                                 font=('Arial', 12, 'bold'), bg='#ecf0f1', fg='#2980b9')
        self.net_cash.pack(pady=5)
        
        # Opening/Closing Cash
        self.cash_frame = tk.Frame(self.scrollable_frame, bg='white')
        self.cash_frame.pack(fill=tk.X, padx=30, pady=5)
        
        self.cash_container = tk.Frame(self.cash_frame, bg='white')
        self.cash_container.pack(fill=tk.X, padx=20, pady=5)
        
        # Final Balance
        self.final_frame = tk.Frame(self.scrollable_frame, bg='#2c3e50', relief=tk.RIDGE, bd=2)
        self.final_frame.pack(fill=tk.X, padx=30, pady=15)
        
        self.closing_cash = tk.Label(self.final_frame, text="CLOSING CASH BALANCE: Rs. 0.00",
                                      font=('Arial', 14, 'bold'), fg='white', bg='#2c3e50')
        self.closing_cash.pack(pady=8)
    
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
    
    def load_data(self):
        """Load cash flow data"""
        # Clear existing data
        for widget in self.operating_container.winfo_children():
            widget.destroy()
        for widget in self.investing_container.winfo_children():
            widget.destroy()
        for widget in self.financing_container.winfo_children():
            widget.destroy()
        for widget in self.cash_container.winfo_children():
            widget.destroy()
        
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        self.period_label.config(text=f"For the period: {from_d} to {to_d}")
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # 1. OPERATING ACTIVITIES
        # Cash from Sales/Receipts
        c.execute('''
            SELECT COALESCE(SUM(le.debit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '1000%'  -- Cash in Hand
            AND le.entry_date BETWEEN ? AND ?
            AND le.debit > 0  -- Cash inflows
        ''', (from_d, to_d))
        cash_in = c.fetchone()[0]
        
        # Cash paid to Suppliers & Expenses
        c.execute('''
            SELECT COALESCE(SUM(le.credit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '1000%'  -- Cash in Hand
            AND le.entry_date BETWEEN ? AND ?
            AND le.credit > 0  -- Cash outflows
        ''', (from_d, to_d))
        cash_out = c.fetchone()[0]
        
        # Operating cash flow
        operating_net = cash_in - cash_out
        
        # Add operating items
        self.add_cash_row(self.operating_container, "Cash from Sales/Receipts", cash_in, 'in')
        self.add_cash_row(self.operating_container, "Cash paid to Suppliers/Expenses", cash_out, 'out')
        self.add_total_row(self.operating_container, "Net Cash from Operations", operating_net)
        
        # 2. INVESTING ACTIVITIES (simplified)
        # For now, just show placeholder
        self.add_cash_row(self.investing_container, "Purchase of Fixed Assets", 0, 'out')
        self.add_cash_row(self.investing_container, "Sale of Fixed Assets", 0, 'in')
        investing_net = 0
        self.add_total_row(self.investing_container, "Net Cash from Investing", investing_net)
        
        # 3. FINANCING ACTIVITIES
        # Loans received/repaid
        c.execute('''
            SELECT COALESCE(SUM(le.debit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '2200%'  -- Loan accounts
            AND le.entry_date BETWEEN ? AND ?
            AND le.debit > 0  -- Loan received (increase cash)
        ''', (from_d, to_d))
        loans_in = c.fetchone()[0]
        
        c.execute('''
            SELECT COALESCE(SUM(le.credit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '2200%'  -- Loan accounts
            AND le.entry_date BETWEEN ? AND ?
            AND le.credit > 0  -- Loan repayment (decrease cash)
        ''', (from_d, to_d))
        loans_out = c.fetchone()[0]
        
        # Owner investments
        c.execute('''
            SELECT COALESCE(SUM(le.debit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '3000%'  -- Owner's Capital
            AND le.entry_date BETWEEN ? AND ?
            AND le.debit > 0  -- Owner investment
        ''', (from_d, to_d))
        capital_in = c.fetchone()[0]
        
        financing_net = loans_in + capital_in - loans_out
        
        self.add_cash_row(self.financing_container, "Loans Received", loans_in, 'in')
        self.add_cash_row(self.financing_container, "Loans Repaid", loans_out, 'out')
        self.add_cash_row(self.financing_container, "Owner Investment", capital_in, 'in')
        self.add_total_row(self.financing_container, "Net Cash from Financing", financing_net)
        
        # 4. Net Cash Flow
        net_cash_flow = operating_net + investing_net + financing_net
        self.net_cash.config(text=f"NET CASH FLOW: {CURRENCY_SYMBOL}{net_cash_flow:,.2f}")
        
        # 5. Opening & Closing Cash
        # Get opening cash balance (before from_date)
        c.execute('''
            SELECT COALESCE(SUM(
                CASE WHEN entry_date < ? THEN debit - credit ELSE 0 END
            ), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '1000%'  -- Cash in Hand
        ''', (from_d,))
        opening_cash = c.fetchone()[0]
        
        # Get all cash transactions in period
        c.execute('''
            SELECT COALESCE(SUM(debit - credit), 0)
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE a.account_code LIKE '1000%'  -- Cash in Hand
            AND le.entry_date BETWEEN ? AND ?
        ''', (from_d, to_d))
        period_cash_change = c.fetchone()[0]
        
        closing_cash = opening_cash + period_cash_change
        
        conn.close()
        
        # Add cash summary
        self.add_cash_row(self.cash_container, "Opening Cash Balance", opening_cash, 'in')
        self.add_cash_row(self.cash_container, "Net Cash Flow during Period", net_cash_flow, 'in')
        tk.Frame(self.cash_container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        self.add_cash_row(self.cash_container, "Closing Cash Balance", closing_cash, 'in', bold=True)
        
        self.closing_cash.config(text=f"CLOSING CASH BALANCE: {CURRENCY_SYMBOL}{closing_cash:,.2f}")
    
    def add_cash_row(self, container, label, amount, flow_type, bold=False):
        """Add a cash flow row"""
        row = tk.Frame(container, bg='white')
        row.pack(fill=tk.X, pady=2)
        
        font = ('Arial', 10, 'bold') if bold else ('Arial', 10)
        
        tk.Label(row, text=label, bg='white', font=('Arial', 10)).pack(side=tk.LEFT)
        
        color = '#27ae60' if flow_type == 'in' else '#e74c3c'
        sign = '' if flow_type == 'in' else '-'
        
        tk.Label(row, text=f"{sign}{CURRENCY_SYMBOL}{amount:,.2f}", bg='white',
                font=font, fg=color).pack(side=tk.RIGHT)
    
    def add_total_row(self, container, label, amount):
        """Add a total row with separator"""
        tk.Frame(container, bg='#cccccc', height=1).pack(fill=tk.X, pady=5)
        row = tk.Frame(container, bg='white')
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label, bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(row, text=f"{CURRENCY_SYMBOL}{amount:,.2f}", bg='white',
                font=('Arial', 10, 'bold'), fg='#2980b9').pack(side=tk.RIGHT)
    
    def export_report(self):
        """Export Cash Flow to CSV"""
        from tkinter import filedialog
        import csv
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            title="Save Cash Flow Statement"
        )
        
        if not filename:
            return
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                writer.writerow(['CASH FLOW STATEMENT'])
                writer.writerow([f"Period: {self.from_date.get()} to {self.to_date.get()}"])
                writer.writerow([])
                
                # Operating Activities
                writer.writerow(['OPERATING ACTIVITIES'])
                for child in self.operating_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                writer.writerow([])
                
                # Investing Activities
                writer.writerow(['INVESTING ACTIVITIES'])
                for child in self.investing_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                writer.writerow([])
                
                # Financing Activities
                writer.writerow(['FINANCING ACTIVITIES'])
                for child in self.financing_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
                writer.writerow([])
                
                # Cash Summary
                writer.writerow(['CASH SUMMARY'])
                for child in self.cash_container.winfo_children():
                    if isinstance(child, tk.Frame):
                        labels = []
                        for subchild in child.winfo_children():
                            if isinstance(subchild, tk.Label):
                                labels.append(subchild.cget('text'))
                        if labels:
                            writer.writerow(labels)
            
            messagebox.showinfo("Success", f"Cash Flow Statement exported to {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    cf = CashFlow(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()