# accounting_menu.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime

class AccountingMenu:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Accounting System")
        self.window.geometry("600x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 600) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"600x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#2c3e50', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📊 ACCOUNTING SYSTEM", fg='white', bg='#2c3e50',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=20)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Main frame
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=10, pady=5)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Voucher Entry Section
        voucher_label = tk.Label(main_frame, text="VOUCHER ENTRY", font=('Arial', 12, 'bold'),
                                bg='#f9f9f9', fg='#2c3e50')
        voucher_label.pack(anchor='w', pady=(10,5))
        
        voucher_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=1)
        voucher_frame.pack(fill=tk.X, pady=5)
        
        # Payment Voucher
        pmt_btn = tk.Button(voucher_frame, text="💸 Payment Voucher", 
                           command=self.open_payment_voucher,
                           bg='#e74c3c', fg='white', font=('Arial', 11),
                           width=20, height=1, cursor='hand2', anchor='w', padx=10)
        pmt_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Receipt Voucher
        rec_btn = tk.Button(voucher_frame, text="💰 Receipt Voucher", 
                           command=self.open_receipt_voucher,
                           bg='#27ae60', fg='white', font=('Arial', 11),
                           width=20, height=1, cursor='hand2', anchor='w', padx=10)
        rec_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Journal Voucher
        jv_btn = tk.Button(voucher_frame, text="📝 Journal Voucher", 
                          command=self.open_journal_voucher,
                          bg='#f39c12', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        jv_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Chart of Accounts Section
        coa_label = tk.Label(main_frame, text="CHART OF ACCOUNTS", font=('Arial', 12, 'bold'),
                              bg='#f9f9f9', fg='#2c3e50')
        coa_label.pack(anchor='w', pady=(15,5))
        
        coa_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=1)
        coa_frame.pack(fill=tk.X, pady=5)
        
        # Chart of Accounts Manager (covers all account types)
        coa_btn = tk.Button(coa_frame, text="📋 Chart of Accounts", 
                           command=self.open_chart_of_accounts,
                           bg='#3498db', fg='white', font=('Arial', 11),
                           width=20, height=1, cursor='hand2', anchor='w', padx=10)
        coa_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Reports Section
        report_label = tk.Label(main_frame, text="REPORTS", font=('Arial', 12, 'bold'),
                               bg='#f9f9f9', fg='#2c3e50')
        report_label.pack(anchor='w', pady=(15,5))
        
        report_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=1)
        report_frame.pack(fill=tk.X, pady=5)
        
        # Ledger View
        ledger_btn = tk.Button(report_frame, text="📒 Ledger View", 
                              command=self.open_ledger,
                              bg='#3498db', fg='white', font=('Arial', 11),
                              width=20, height=1, cursor='hand2', anchor='w', padx=10)
        ledger_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Trial Balance
        tb_btn = tk.Button(report_frame, text="⚖️ Trial Balance", 
                          command=self.open_trial_balance,
                          bg='#9b59b6', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        tb_btn.pack(pady=8, padx=10, fill=tk.X)

        # Profit & Loss
        pl_btn = tk.Button(report_frame, text="📈 Profit & Loss", 
                          command=self.open_profit_loss,
                          bg='#27ae60', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        pl_btn.pack(pady=8, padx=10, fill=tk.X)

        # Balance Sheet
        bs_btn = tk.Button(report_frame, text="📉 Balance Sheet", 
                          command=self.open_balance_sheet,
                          bg='#9b59b6', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        bs_btn.pack(pady=8, padx=10, fill=tk.X)

        # Cash Flow
        cf_btn = tk.Button(report_frame, text="💰 Cash Flow", 
                          command=self.open_cash_flow,
                          bg='#3498db', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        cf_btn.pack(pady=8, padx=10, fill=tk.X)

        # Budget Management
        bm_btn = tk.Button(report_frame, text="📊 Budget Management", 
                          command=self.open_budget_manager,
                          bg='#f39c12', fg='white', font=('Arial', 11),
                          width=20, height=1, cursor='hand2', anchor='w', padx=10)
        bm_btn.pack(pady=8, padx=10, fill=tk.X)

        # Tools Section
        tool_label = tk.Label(main_frame, text="TOOLS", font=('Arial', 12, 'bold'),
                              bg='#f9f9f9', fg='#2c3e50')
        tool_label.pack(anchor='w', pady=(15,5))
        
        tool_frame = tk.Frame(main_frame, bg='white', relief=tk.RIDGE, bd=1)
        tool_frame.pack(fill=tk.X, pady=5)
        
        # Backup Manager
        backup_btn = tk.Button(tool_frame, text="💾 Backup & Restore", 
                              command=self.open_backup_manager,
                              bg='#2c3e50', fg='white', font=('Arial', 11),
                              width=20, height=1, cursor='hand2', anchor='w', padx=10)
        backup_btn.pack(pady=8, padx=10, fill=tk.X)
        
        # Close button
        close_btn = tk.Button(main_frame, text="❌ Close", command=self.window.destroy,
                             bg='#95a5a6', fg='white', font=('Arial', 10),
                             width=30, height=2, cursor='hand2')
        close_btn.pack(pady=20)
    
    def open_payment_voucher(self):
        """Open Payment Voucher"""
        try:
            from voucher_payment import PaymentVoucher  # Import inside function
            PaymentVoucher(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Payment Voucher module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Payment Voucher: {e}")
    
    def open_receipt_voucher(self):
        """Open Receipt Voucher"""
        try:
            from voucher_receipt import ReceiptVoucher
            ReceiptVoucher(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Receipt Voucher module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Receipt Voucher: {e}")
    
    def open_journal_voucher(self):
        """Open Journal Voucher"""
        try:
            from voucher_journal import JournalVoucher
            JournalVoucher(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Journal Voucher module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Journal Voucher: {e}")
    
    def open_ledger(self):
        """Open Ledger View"""
        try:
            from ledger_view import LedgerView
            LedgerView(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Ledger View module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Ledger View: {e}")

    def open_trial_balance(self):
        """Open Trial Balance"""
        try:
            from trial_balance import TrialBalance
            TrialBalance(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Trial Balance module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Trial Balance: {e}")

    def open_profit_loss(self):
        """Open Profit & Loss Statement"""
        try:
            from profit_loss import ProfitLoss
            ProfitLoss(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Profit & Loss module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Profit & Loss: {e}")

    def open_balance_sheet(self):
        """Open Balance Sheet"""
        try:
            from balance_sheet import BalanceSheet
            BalanceSheet(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Balance Sheet module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Balance Sheet: {e}")

    def open_cash_flow(self):
        """Open Cash Flow Statement"""
        try:
            from cash_flow import CashFlow
            CashFlow(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Cash Flow module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Cash Flow: {e}")

    def open_budget_manager(self):
        """Open Budget Manager"""
        try:
            from budget_manager import BudgetManager
            BudgetManager(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Budget Manager module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Budget Manager: {e}")
    
    def open_chart_of_accounts(self):
        """Open Chart of Accounts Manager"""
        try:
            from chart_of_accounts import ChartOfAccounts
            ChartOfAccounts(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Chart of Accounts module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Chart of Accounts: {e}")

    def open_backup_manager(self):
        """Open Backup Manager"""
        try:
            from backup_manager import BackupManager
            BackupManager(self.window, self.username, self.working_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Backup Manager module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Backup Manager: {e}")