# ledger_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL
import re

class LedgerView:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Universal Ledger")
        self.window.geometry("1200x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1200) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"1200x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_parties()
        self.load_transaction_types()
        self.load_ledger()  # Load initial data
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#2c3e50', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📒 UNIVERSAL LEDGER", fg='white', bg='#2c3e50',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Filter Frame
        filter_frame = tk.Frame(self.window, bg='#ecf0f1', padx=10, pady=10)
        filter_frame.pack(fill=tk.X)
        
        # Ledger Type Selection
        tk.Label(filter_frame, text="Ledger Type:", font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.ledger_type = ttk.Combobox(filter_frame, values=[
            "All Transactions",
            "Party Ledger", 
            "Cash/Bank Ledger",
            "Expense Ledger",
            "Income Ledger",
            "Membership Ledger",
            "Supplier Ledger"
        ], width=25, font=('Arial', 10))
        self.ledger_type.set("All Transactions")
        self.ledger_type.grid(row=0, column=1, padx=5, pady=5)
        self.ledger_type.bind('<<ComboboxSelected>>', self.on_ledger_type_change)
        
        # Party Selection (for Party Ledger)
        tk.Label(filter_frame, text="Select Party:", font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5, sticky='e')
        self.party_combo = ttk.Combobox(filter_frame, width=30, font=('Arial', 10))
        self.party_combo.grid(row=0, column=3, padx=5, pady=5)
        self.party_combo.state(['disabled'])
        
        # Transaction Type Filter
        tk.Label(filter_frame, text="Transaction Type:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.trans_type = ttk.Combobox(filter_frame, width=25, font=('Arial', 10))
        self.trans_type.grid(row=1, column=1, padx=5, pady=5)
        
        # Date Range
        tk.Label(filter_frame, text="From Date:", font=('Arial', 10)).grid(row=1, column=2, padx=5, pady=5, sticky='e')
        self.from_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.from_date.insert(0, (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        self.from_date.grid(row=1, column=3, padx=5, pady=5)
        
        tk.Label(filter_frame, text="To Date:", font=('Arial', 10)).grid(row=1, column=4, padx=5, pady=5, sticky='e')
        self.to_date = tk.Entry(filter_frame, width=12, font=('Arial', 10), relief='solid', bd=1)
        self.to_date.insert(0, datetime.now().strftime('%Y-%m-%d'))
        self.to_date.grid(row=1, column=5, padx=5, pady=5)
        
        # Buttons
        tk.Button(filter_frame, text="🔍 View Ledger", command=self.load_ledger,
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                 width=15, cursor='hand2').grid(row=2, column=2, columnspan=2, pady=10)
        
        tk.Button(filter_frame, text="📊 Summary", command=self.show_summary,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 width=15, cursor='hand2').grid(row=2, column=4, columnspan=2, pady=10)
        
        # Treeview Frame
        tree_frame = tk.Frame(self.window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview
        columns = ('Date', 'Voucher No', 'Transaction Type', 'Account/Party', 
                   'Description', 'Debit', 'Credit', 'Balance')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column Widths
        col_widths = {'Date': 90, 'Voucher No': 100, 'Transaction Type': 120, 'Account/Party': 180,
                     'Description': 200, 'Debit': 90, 'Credit': 90, 'Balance': 90}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 100), anchor='center')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summary Frame
        summary_frame = tk.Frame(self.window, bg='#ecf0f1', height=40)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Opening Balance:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=20, y=10)
        self.opening_balance = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1', font=('Arial', 10, 'bold'))
        self.opening_balance.place(x=150, y=10)
        
        tk.Label(summary_frame, text="Total Debit:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=280, y=10)
        self.total_debit = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1', 
                                    font=('Arial', 10, 'bold'), fg='#e74c3c')
        self.total_debit.place(x=380, y=10)
        
        tk.Label(summary_frame, text="Total Credit:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=500, y=10)
        self.total_credit = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1',
                                     font=('Arial', 10, 'bold'), fg='#27ae60')
        self.total_credit.place(x=600, y=10)
        
        tk.Label(summary_frame, text="Closing Balance:", bg='#ecf0f1', font=('Arial', 10, 'bold')).place(x=720, y=10)
        self.closing_balance = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1',
                                        font=('Arial', 10, 'bold'), fg='#2980b9')
        self.closing_balance.place(x=850, y=10)
    
    def load_parties(self):
        """Load all parties (suppliers and members) into the combo box."""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            parties = []
            
            # Load suppliers
            c.execute("SELECT id, company_name FROM suppliers ORDER BY company_name")
            for sid, name in c.fetchall():
                parties.append(f"Supplier: {name}")
            
            # Load members (include member number)
            c.execute("SELECT id, name, member_no FROM members ORDER BY name")
            for mid, name, mno in c.fetchall():
                parties.append(f"Member: {name} ({mno})")
            
            conn.close()
            self.party_combo['values'] = parties
            print(f"✅ Loaded {len(parties)} parties")
        except Exception as e:
            print(f"Error loading parties: {e}")
    
    def load_transaction_types(self):
        """Load transaction types for filter"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("SELECT type_name FROM transaction_types ORDER BY category, type_name")
            types = c.fetchall()
            conn.close()
            
            type_list = ['All'] + [t[0] for t in types]
            self.trans_type['values'] = type_list
            self.trans_type.set('All')
        except Exception as e:
            print(f"Error loading transaction types: {e}")
            self.trans_type['values'] = ['All']
            self.trans_type.set('All')
    
    def on_ledger_type_change(self, event=None):
        """Enable/disable party selection based on ledger type"""
        lt = self.ledger_type.get()
        if lt == "Party Ledger":
            self.party_combo.config(state='normal')
        else:
            self.party_combo.config(state='disabled')
            self.party_combo.set('')
    
    def load_ledger(self):
        """Load ledger entries based on filters."""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        lt = self.ledger_type.get()
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        trans_filter = self.trans_type.get()
        
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            if lt == "Party Ledger" and self.party_combo.get():
                display = self.party_combo.get().strip()
                
                # Determine party type and get account code
                account_code = None
                party_name = display
                
                if display.startswith("Supplier:"):
                    # Extract supplier name
                    supplier_name = display.replace("Supplier:", "").strip()
                    
                    # Get supplier's account code
                    c.execute('''
                        SELECT a.account_code 
                        FROM suppliers s
                        JOIN accounts a ON s.account_id = a.id
                        WHERE s.company_name = ?
                    ''', (supplier_name,))
                    result = c.fetchone()
                    
                    if result:
                        account_code = result[0]
                        party_name = supplier_name
                    else:
                        messagebox.showerror("Error", f"Supplier '{supplier_name}' not found.")
                        conn.close()
                        return
                
                elif display.startswith("Member:"):
                    # Extract member number from parentheses
                    match = re.search(r'\(([^)]+)\)', display)
                    if match:
                        member_no = match.group(1)
                        
                        # Get member's account code
                        c.execute('''
                            SELECT a.account_code 
                            FROM members m
                            JOIN accounts a ON m.account_id = a.id
                            WHERE m.member_no = ?
                        ''', (member_no,))
                        result = c.fetchone()
                        
                        if result:
                            account_code = result[0]
                            party_name = display.split('(')[0].replace("Member:", "").strip()
                        else:
                            messagebox.showerror("Error", f"Member with number {member_no} not found.")
                            conn.close()
                            return
                    else:
                        messagebox.showerror("Error", "Could not parse member number.")
                        conn.close()
                        return
                
                if not account_code:
                    messagebox.showerror("Error", "Could not find account code for this party.")
                    conn.close()
                    return
                
                # Get opening balance (balance before from_date)
                c.execute('''
                    SELECT COALESCE(SUM(debit - credit), 0)
                    FROM ledger_entries le
                    JOIN accounts a ON le.account_id = a.id
                    WHERE a.account_code = ? AND le.entry_date < ?
                ''', (account_code, from_d))
                opening_balance = c.fetchone()[0]
                
                # Get ALL transactions for this account within date range
                c.execute('''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    WHERE a.account_code = ? AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                ''', (account_code, from_d, to_d))
                
                transactions = c.fetchall()
                
                # Display opening balance row
                self._display_opening_balance(party_name, opening_balance)
                
                # Display transactions with running balance
                balance = opening_balance
                total_debit = 0
                total_credit = 0
                
                for t in transactions:
                    date, voucher_no, vtype, acc_name, narration, debit, credit = t
                    balance += (debit - credit)
                    total_debit += debit
                    total_credit += credit
                    
                    self._display_transaction(t, balance, party_name)
                
                # Update summary labels
                self.total_debit.config(text=f"{CURRENCY_SYMBOL}{total_debit:,.2f}")
                self.total_credit.config(text=f"{CURRENCY_SYMBOL}{total_credit:,.2f}")
                
                closing_balance = opening_balance + total_debit - total_credit
                bal_disp = f"{CURRENCY_SYMBOL}{abs(closing_balance):,.2f}"
                if closing_balance > 0:
                    bal_disp += " Dr"
                elif closing_balance < 0:
                    bal_disp += " Cr"
                self.closing_balance.config(text=bal_disp)
            
            elif lt == "Cash/Bank Ledger":
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        COALESCE(s.company_name, m.name, '') as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN suppliers s ON v.supplier_id = s.id
                    LEFT JOIN members m ON v.member_id = m.id
                    WHERE (a.account_code = '1000' OR a.account_code LIKE '1100%')
                    AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            elif lt == "Expense Ledger":
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        COALESCE(s.company_name, m.name, '') as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN suppliers s ON v.supplier_id = s.id
                    LEFT JOIN members m ON v.member_id = m.id
                    WHERE a.account_type = 'Expense'
                    AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            elif lt == "Income Ledger":
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        COALESCE(s.company_name, m.name, '') as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN suppliers s ON v.supplier_id = s.id
                    LEFT JOIN members m ON v.member_id = m.id
                    WHERE a.account_type = 'Income'
                    AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            elif lt == "Membership Ledger":
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        COALESCE(m.name, '') as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN members m ON v.member_id = m.id
                    WHERE v.voucher_type IN ('MEMBERSHIP_FEE', 'Opening Balance')
                    AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            elif lt == "Supplier Ledger":
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        s.company_name as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN suppliers s ON v.supplier_id = s.id
                    WHERE v.supplier_id IS NOT NULL
                    AND le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            else:  # All Transactions
                query = '''
                    SELECT 
                        le.entry_date,
                        v.voucher_no,
                        v.voucher_type,
                        a.account_name,
                        COALESCE(s.company_name, m.name, '') as party_name,
                        le.narration,
                        le.debit,
                        le.credit
                    FROM ledger_entries le
                    JOIN vouchers v ON le.voucher_id = v.id
                    JOIN accounts a ON le.account_id = a.id
                    LEFT JOIN suppliers s ON v.supplier_id = s.id
                    LEFT JOIN members m ON v.member_id = m.id
                    WHERE le.entry_date BETWEEN ? AND ?
                    ORDER BY le.entry_date
                '''
                c.execute(query, (from_d, to_d))
                entries = c.fetchall()
                self._display_general_ledger(entries)
            
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load ledger: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_opening_balance(self, party_name, opening_balance):
        """Display an opening balance row."""
        opening_display = f"{CURRENCY_SYMBOL}{abs(opening_balance):.2f}"
        if opening_balance > 0:
            opening_display += " Dr"
        elif opening_balance < 0:
            opening_display += " Cr"
        
        self.tree.insert('', 0, values=(
            "(Before)",
            "",
            "Opening Balance",
            party_name,
            "Balance brought forward",
            f"{CURRENCY_SYMBOL}{abs(opening_balance):.2f}" if opening_balance > 0 else "",
            f"{CURRENCY_SYMBOL}{abs(opening_balance):.2f}" if opening_balance < 0 else "",
            opening_display
        ), tags=('opening',))
        
        self.opening_balance.config(text=opening_display)
    
    def _display_transaction(self, transaction, balance, party_name=""):
        """Display a single transaction row with running balance."""
        date, voucher_no, vtype, account_name, narration, debit, credit = transaction
        
        # For party ledger, show the account name that was affected
        display_name = account_name
        
        bal_disp = f"{CURRENCY_SYMBOL}{abs(balance):.2f}"
        if balance > 0:
            bal_disp += " Dr"
        elif balance < 0:
            bal_disp += " Cr"
        
        self.tree.insert('', tk.END, values=(
            date[:10] if date else '',
            voucher_no or '',
            vtype or '',
            display_name,
            narration or '',
            f"{CURRENCY_SYMBOL}{debit:.2f}" if debit else f"{CURRENCY_SYMBOL}0.00",
            f"{CURRENCY_SYMBOL}{credit:.2f}" if credit else f"{CURRENCY_SYMBOL}0.00",
            bal_disp
        ))
    
    def _display_general_ledger(self, entries):
        """Display general ledger for non-party views."""
        if not entries:
            return
        
        balance = 0
        total_debit = 0
        total_credit = 0
        
        for e in entries:
            date, voucher_no, vtype, account_name, party_name, narration, debit, credit = e
            balance += (debit - credit)
            total_debit += debit
            total_credit += credit
            
            display_name = account_name
            if party_name:
                display_name = f"{party_name} ({account_name})"
            
            bal_disp = f"{CURRENCY_SYMBOL}{abs(balance):.2f}"
            if balance > 0:
                bal_disp += " Dr"
            elif balance < 0:
                bal_disp += " Cr"
            
            self.tree.insert('', tk.END, values=(
                date[:10] if date else '',
                voucher_no or '',
                vtype or '',
                display_name,
                narration or '',
                f"{CURRENCY_SYMBOL}{debit:.2f}" if debit else f"{CURRENCY_SYMBOL}0.00",
                f"{CURRENCY_SYMBOL}{credit:.2f}" if credit else f"{CURRENCY_SYMBOL}0.00",
                bal_disp
            ))
        
        self.total_debit.config(text=f"{CURRENCY_SYMBOL}{total_debit:,.2f}")
        self.total_credit.config(text=f"{CURRENCY_SYMBOL}{total_credit:,.2f}")
        self.closing_balance.config(text=bal_disp)
        
        # opening balance for general ledger
        opening = balance - total_debit + total_credit
        op_disp = f"{CURRENCY_SYMBOL}{abs(opening):.2f}"
        if opening > 0:
            op_disp += " Dr"
        elif opening < 0:
            op_disp += " Cr"
        self.opening_balance.config(text=op_disp)
    
    def show_summary(self):
        """Show summary by category."""
        summary_win = tk.Toplevel(self.window)
        summary_win.title("Ledger Summary")
        summary_win.geometry("600x500")
        
        # Center window
        summary_win.update_idletasks()
        x = (summary_win.winfo_screenwidth() - 600) // 2
        y = (summary_win.winfo_screenheight() - 500) // 2
        summary_win.geometry(f"600x500+{x}+{y}")
        
        summary_win.grab_set()
        summary_win.transient(self.window)
        
        tk.Label(summary_win, text="📊 LEDGER SUMMARY", font=('Arial', 14, 'bold'),
                bg='#3498db', fg='white').pack(fill=tk.X, pady=10)
        
        from_d = self.from_date.get()
        to_d = self.to_date.get()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Summary by account type
        c.execute('''
            SELECT 
                a.account_type,
                COUNT(*) as transaction_count,
                SUM(le.debit) as total_debit,
                SUM(le.credit) as total_credit
            FROM ledger_entries le
            JOIN accounts a ON le.account_id = a.id
            WHERE le.entry_date BETWEEN ? AND ?
            GROUP BY a.account_type
            ORDER BY a.account_type
        ''', (from_d, to_d))
        summaries = c.fetchall()
        
        # Member receipts
        c.execute('''
            SELECT 
                'Member Receipts' as type,
                COUNT(*) as count,
                SUM(le.credit) as total
            FROM ledger_entries le
            JOIN vouchers v ON le.voucher_id = v.id
            WHERE v.member_id IS NOT NULL 
            AND le.entry_date BETWEEN ? AND ?
            AND le.credit > 0
        ''', (from_d, to_d))
        member_summary = c.fetchone()
        
        # Supplier payments
        c.execute('''
            SELECT 
                'Supplier Payments' as type,
                COUNT(*) as count,
                SUM(le.debit) as total
            FROM ledger_entries le
            JOIN vouchers v ON le.voucher_id = v.id
            WHERE v.supplier_id IS NOT NULL 
            AND le.entry_date BETWEEN ? AND ?
            AND le.debit > 0
        ''', (from_d, to_d))
        supplier_summary = c.fetchone()
        
        # Purchase Orders summary
        c.execute('''
            SELECT 
                'Purchase Orders' as type,
                COUNT(*) as count,
                SUM(total) as total
            FROM purchase_orders
            WHERE order_date BETWEEN ? AND ?
        ''', (from_d, to_d))
        po_summary = c.fetchone()
        
        conn.close()
        
        frame = tk.Frame(summary_win, padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        date_frame = tk.Frame(frame, bg='#ecf0f1', relief=tk.RIDGE, bd=1)
        date_frame.pack(fill=tk.X, pady=5)
        tk.Label(date_frame, text=f"📅 Period: {from_d} to {to_d}", font=('Arial', 11, 'bold'),
                bg='#ecf0f1').pack(pady=5)
        
        for s in summaries:
            if s[0]:
                cat_frame = tk.Frame(frame, bg='#ffffff', relief=tk.RIDGE, bd=1)
                cat_frame.pack(fill=tk.X, pady=3)
                tk.Label(cat_frame, text=f"📁 {s[0]}", font=('Arial', 11, 'bold'),
                        bg='#ffffff').pack(anchor='w', padx=10, pady=5)
                tk.Label(cat_frame, text=f"Transactions: {s[1]}", bg='#ffffff').pack(anchor='w', padx=20)
                tk.Label(cat_frame, text=f"Total Debit: {CURRENCY_SYMBOL}{s[2]:.2f}", 
                        fg='#e74c3c', bg='#ffffff').pack(anchor='w', padx=20)
                tk.Label(cat_frame, text=f"Total Credit: {CURRENCY_SYMBOL}{s[3]:.2f}", 
                        fg='#27ae60', bg='#ffffff').pack(anchor='w', padx=20)
        
        if member_summary and member_summary[1]:
            mem_frame = tk.Frame(frame, bg='#ffffff', relief=tk.RIDGE, bd=1)
            mem_frame.pack(fill=tk.X, pady=3)
            tk.Label(mem_frame, text="📁 Member Receipts", font=('Arial', 11, 'bold'),
                    bg='#ffffff').pack(anchor='w', padx=10, pady=5)
            tk.Label(mem_frame, text=f"Transactions: {member_summary[1]}", bg='#ffffff').pack(anchor='w', padx=20)
            tk.Label(mem_frame, text=f"Total Amount: {CURRENCY_SYMBOL}{member_summary[2]:.2f}", 
                    fg='#2980b9', bg='#ffffff').pack(anchor='w', padx=20)
        
        if supplier_summary and supplier_summary[1]:
            sup_frame = tk.Frame(frame, bg='#ffffff', relief=tk.RIDGE, bd=1)
            sup_frame.pack(fill=tk.X, pady=3)
            tk.Label(sup_frame, text="📁 Supplier Payments", font=('Arial', 11, 'bold'),
                    bg='#ffffff').pack(anchor='w', padx=10, pady=5)
            tk.Label(sup_frame, text=f"Transactions: {supplier_summary[1]}", bg='#ffffff').pack(anchor='w', padx=20)
            tk.Label(sup_frame, text=f"Total Amount: {CURRENCY_SYMBOL}{supplier_summary[2]:.2f}", 
                    fg='#2980b9', bg='#ffffff').pack(anchor='w', padx=20)
        
        if po_summary and po_summary[1]:
            po_frame = tk.Frame(frame, bg='#ffffff', relief=tk.RIDGE, bd=1)
            po_frame.pack(fill=tk.X, pady=3)
            tk.Label(po_frame, text="📁 Purchase Orders", font=('Arial', 11, 'bold'),
                    bg='#ffffff').pack(anchor='w', padx=10, pady=5)
            tk.Label(po_frame, text=f"Orders: {po_summary[1]}", bg='#ffffff').pack(anchor='w', padx=20)
            tk.Label(po_frame, text=f"Total Value: {CURRENCY_SYMBOL}{po_summary[2]:.2f}", 
                    fg='#2980b9', bg='#ffffff').pack(anchor='w', padx=20)
        
        tk.Button(summary_win, text="Close", command=summary_win.destroy,
                 bg='#95a5a6', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(pady=10)
        
        self.tree.tag_configure('opening', background='#e8f4f8', font=('Arial', 9, 'italic'))