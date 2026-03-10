import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, show_error, show_success

class ReceiptVoucher:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Receipt Voucher")
        self.window.geometry("750x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 750) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"750x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.selected_id = None
        self.selected_name = None
        self.selected_balance = 0
        self.selected_code = None
        self.selected_type = None
        self.all_accounts = []
        self.all_accounts_display = []
        self.current_popup = None
        self.current_listbox = None
        self.filtered_items = []
        self.popup_visible = False
        
        self.create_widgets()
        self.load_all_accounts()
        self.generate_voucher_no()
    
    def generate_voucher_no(self):
        """Generate unique voucher number using working date"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        today = self.working_date.replace('-', '')
        c.execute("SELECT COUNT(*) FROM vouchers WHERE voucher_no LIKE ?", (f'RCT-{today}%',))
        count = c.fetchone()[0] + 1
        conn.close()
        self.voucher_no = f"RCT-{today}-{count:03d}"
        self.voucher_no_var.set(self.voucher_no)
    
    def load_all_accounts(self):
        """Load ALL accounts where receipts can be posted"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            # Load Cash, Bank, Accounts Receivable, Income accounts, and Member accounts
            c.execute('''SELECT id, account_code, account_name, account_type, current_balance 
                         FROM accounts 
                         WHERE account_type IN ('Asset', 'Income', 'Liability')
                         OR account_code LIKE '1-%'  -- Member accounts under Receivable
                         OR account_code IN ('1000', '1100', '1101', '1200', '2000', '4000', '4100')
                         ORDER BY 
                           CASE 
                             WHEN account_code = '1000' THEN 1
                             WHEN account_code LIKE '110%' THEN 2
                             WHEN account_code = '1200' THEN 3
                             WHEN account_code LIKE '1-%' THEN 4
                             WHEN account_code LIKE '2-%' THEN 5
                             WHEN account_type = 'Income' THEN 6
                             ELSE 7
                           END, account_code''')
            
            self.all_accounts = c.fetchall()
            conn.close()
            
            if self.all_accounts:
                # Format for display
                self.all_accounts_display = []
                for acc in self.all_accounts:
                    acc_id, code, name, acc_type, balance = acc
                    
                    # Add emoji based on type
                    if code == '1000':
                        prefix = "💰"
                    elif code.startswith('110'):
                        prefix = "🏦"
                    elif code == '1200':
                        prefix = "📋"
                    elif code.startswith('1-'):
                        prefix = "👤"
                    elif code.startswith('2-'):
                        prefix = "📋"
                    elif acc_type == 'Income':
                        prefix = "📈"
                    else:
                        prefix = "📊"
                    
                    display_text = f"{prefix} {code} - {name}"
                    
                    # Add balance with Dr/Cr indicator
                    if balance != 0:
                        if balance > 0:
                            if acc_type in ['Asset', 'Expense']:
                                balance_display = f"Dr {CURRENCY_SYMBOL}{balance:,.0f}"
                            else:
                                balance_display = f"Cr {CURRENCY_SYMBOL}{balance:,.0f}"
                        else:
                            balance_display = f"{CURRENCY_SYMBOL}{balance:,.0f}"
                        display_text += f" ({balance_display})"
                    
                    self.all_accounts_display.append(display_text)
                
                print(f"✅ Loaded {len(self.all_accounts)} accounts for receipt")
            else:
                print("⚠️ No accounts found")
                self.all_accounts = []
                self.all_accounts_display = []
        except Exception as e:
            print(f"❌ Error loading accounts: {e}")
            self.all_accounts = []
            self.all_accounts_display = []
    
    def safe_widget_exists(self, widget):
        """Safely check if a widget exists"""
        try:
            return widget and widget.winfo_exists()
        except:
            return False
    
    def close_popup_safe(self):
        """Safely close popup without errors"""
        try:
            if self.current_popup and self.current_popup.winfo_exists():
                self.current_popup.destroy()
        except:
            pass
        finally:
            self.current_popup = None
            self.current_listbox = None
            self.filtered_items = []
            self.popup_visible = False
    
    def update_balance_display(self):
        """Update the balance display with selected account info"""
        try:
            if self.selected_code == '1000':
                prefix = "💰 Cash in Hand"
            elif self.selected_code and self.selected_code.startswith('110'):
                prefix = "🏦 Bank Account"
            elif self.selected_code == '1200':
                prefix = "📋 Accounts Receivable"
            elif self.selected_code and self.selected_code.startswith('1-'):
                prefix = "👤 Member Account"
            elif self.selected_code and self.selected_code.startswith('2-'):
                prefix = "📋 Supplier Account"
            elif self.selected_type == 'Income':
                prefix = "📈 Income"
            elif self.selected_type == 'Liability':
                prefix = "📋 Liability"
            elif self.selected_type == 'Expense':
                prefix = "📉 Expense"
            elif self.selected_type == 'Equity':
                prefix = "🏛️ Equity"
            else:
                prefix = "📊 Account"
            
            # Format balance with Dr/Cr
            balance = self.selected_balance
            if balance > 0:
                if self.selected_type in ['Asset', 'Expense']:
                    balance_text = f"Dr {CURRENCY_SYMBOL}{balance:,.0f}"
                else:
                    balance_text = f"Cr {CURRENCY_SYMBOL}{balance:,.0f}"
            elif balance < 0:
                abs_balance = abs(balance)
                if self.selected_type in ['Asset', 'Expense']:
                    balance_text = f"Cr {CURRENCY_SYMBOL}{abs_balance:,.0f}"
                else:
                    balance_text = f"Dr {CURRENCY_SYMBOL}{abs_balance:,.0f}"
            else:
                balance_text = f"{CURRENCY_SYMBOL}0"
            
            display_text = f"{prefix}: {balance_text}"
            self.balance_label.config(text=display_text)
        except Exception as e:
            print(f"Error updating balance: {e}")
    
    def show_account_popup(self, entry_widget):
        """Show popup with filtered accounts (all if empty)"""
        current_text = entry_widget.get().lower()
        
        # Filter items (or show all if empty)
        suggestions = []
        self.filtered_items = []  # Reset filtered items
        
        if not current_text:
            # Show all items when empty (limit to 20 for performance)
            suggestions = self.all_accounts_display[:20]
            self.filtered_items = self.all_accounts[:20]
        else:
            # Filter based on text
            for i, item in enumerate(self.all_accounts_display):
                if current_text in item.lower():
                    suggestions.append(item)
                    self.filtered_items.append(self.all_accounts[i])
        
        if not suggestions:
            # Close popup if no suggestions
            self.close_popup_safe()
            return
        
        # If popup exists, update it instead of creating new one
        if self.safe_widget_exists(self.current_popup):
            try:
                self.current_listbox.delete(0, tk.END)
                for sugg in suggestions:
                    self.current_listbox.insert(tk.END, sugg)
                
                # Select first item
                if self.current_listbox.size() > 0:
                    self.current_listbox.selection_set(0)
                    self.current_listbox.activate(0)
                return
            except:
                self.close_popup_safe()
        
        # Create new popup
        popup = tk.Toplevel(self.window)
        popup.overrideredirect(True)
        
        # Position popup below entry
        x = entry_widget.winfo_rootx()
        y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
        popup.geometry(f"550x250+{x}+{y}")
        
        # Add listbox with scrollbar
        frame = tk.Frame(popup, bg='white')
        frame.pack(fill=tk.BOTH, expand=True)
        
        listbox = tk.Listbox(frame, height=10, font=('Arial', 9), bg='white', selectbackground='#3498db')
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add suggestions
        for sugg in suggestions:
            listbox.insert(tk.END, sugg)
        
        self.current_popup = popup
        self.current_listbox = listbox
        self.popup_visible = True
        
        # Select first item by default
        if listbox.size() > 0:
            listbox.selection_set(0)
            listbox.activate(0)
        
        def select_item():
            try:
                if not self.safe_widget_exists(self.current_listbox):
                    self.close_popup_safe()
                    return
                    
                if self.current_listbox.curselection():
                    idx = self.current_listbox.curselection()[0]
                    selected_text = self.current_listbox.get(idx)
                    
                    # Get the correct data from filtered_items at the same index
                    if idx < len(self.filtered_items):
                        entry_widget.delete(0, tk.END)
                        entry_widget.insert(0, selected_text)
                        
                        # Store selected info
                        self.selected_id = self.filtered_items[idx][0]
                        self.selected_name = self.filtered_items[idx][2]
                        self.selected_balance = self.filtered_items[idx][4]
                        self.selected_code = self.filtered_items[idx][1]
                        self.selected_type = self.filtered_items[idx][3]
                        
                        # Update balance display
                        self.update_balance_display()
                        
                        # Close popup safely
                        self.close_popup_safe()
                        self.amount.focus()
            except Exception as e:
                print(f"Error in select_item: {e}")
                self.close_popup_safe()
        
        # Mouse click selection
        listbox.bind('<ButtonRelease-1>', lambda e: select_item())
        
        # Double-click selection
        listbox.bind('<Double-Button-1>', lambda e: select_item())
        
        def on_key(event):
            try:
                if not self.safe_widget_exists(self.current_popup):
                    return
                    
                if event.keysym == 'Down':
                    if self.safe_widget_exists(self.current_listbox):
                        if self.current_listbox.curselection():
                            idx = self.current_listbox.curselection()[0]
                            if idx < self.current_listbox.size() - 1:
                                self.current_listbox.selection_clear(0, tk.END)
                                self.current_listbox.selection_set(idx + 1)
                                self.current_listbox.activate(idx + 1)
                                self.current_listbox.see(idx + 1)
                        else:
                            self.current_listbox.selection_set(0)
                            self.current_listbox.activate(0)
                            self.current_listbox.see(0)
                    return 'break'
                    
                elif event.keysym == 'Up':
                    if self.safe_widget_exists(self.current_listbox):
                        if self.current_listbox.curselection():
                            idx = self.current_listbox.curselection()[0]
                            if idx > 0:
                                self.current_listbox.selection_clear(0, tk.END)
                                self.current_listbox.selection_set(idx - 1)
                                self.current_listbox.activate(idx - 1)
                                self.current_listbox.see(idx - 1)
                    return 'break'
                    
                elif event.keysym == 'Return':
                    select_item()
                    return 'break'
                    
                elif event.keysym == 'Escape':
                    self.close_popup_safe()
                    self.account_entry.focus()
                    return 'break'
                    
            except Exception as e:
                print(f"Error in on_key: {e}")
                self.close_popup_safe()
                return None
        
        self.window.bind('<Down>', on_key)
        self.window.bind('<Up>', on_key)
        self.window.bind('<Return>', on_key)
        self.window.bind('<Escape>', on_key)
        
        # Bind click outside to close popup
        def on_click_outside(event):
            try:
                if self.safe_widget_exists(self.current_popup):
                    clicked_widget = event.widget
                    if clicked_widget not in (popup, listbox, scrollbar, frame) and clicked_widget != entry_widget:
                        self.close_popup_safe()
            except:
                self.close_popup_safe()
        
        self.window.bind('<Button-1>', on_click_outside)
        popup.lift()
    
    def on_account_key_release(self, event):
        """Handle key release in account entry - real-time filtering"""
        self.show_account_popup(self.account_entry)
        self.account_entry.focus_set()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#27ae60', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="💰 RECEIPT VOUCHER", fg='white', bg='#27ae60',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Main form
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Voucher info
        info_frame = tk.LabelFrame(main_frame, text="Voucher Information", font=('Arial', 11, 'bold'),
                                  padx=10, pady=10)
        info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(info_frame, text="Voucher No:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.voucher_no_var = tk.StringVar()
        tk.Entry(info_frame, textvariable=self.voucher_no_var, width=20, 
                font=('Arial', 10), state='readonly', relief='solid', bd=1).grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(info_frame, text="Date:").grid(row=0, column=2, padx=(20,5), pady=5, sticky='e')
        tk.Label(info_frame, text=self.working_date, font=('Arial', 10, 'bold'),
                bg='#f9f9f9', fg='#2980b9').grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        # Account Selection
        account_frame = tk.LabelFrame(main_frame, text="Account Selection", font=('Arial', 11, 'bold'),
                                     padx=10, pady=10)
        account_frame.pack(fill=tk.X, pady=10)
        
        self.account_label = tk.Label(account_frame, text="Select Receipt Account:", font=('Arial', 10), bg='#f9f9f9')
        self.account_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')
        
        # Frame to hold entry
        entry_frame = tk.Frame(account_frame, bg='#f9f9f9')
        entry_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Account Entry with popup search
        self.account_entry = tk.Entry(entry_frame, width=50, font=('Arial', 10), relief='solid', bd=1)
        self.account_entry.pack(side=tk.LEFT)
        self.account_entry.bind('<KeyRelease>', self.on_account_key_release)
        
        # Balance display
        tk.Label(account_frame, text="Account Balance:", font=('Arial', 10, 'bold'), bg='#f9f9f9').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.balance_label = tk.Label(account_frame, text="Select an account", font=('Arial', 10, 'bold'),
                                     bg='#f9f9f9', fg='#2980b9', anchor='w', justify='left')
        self.balance_label.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Receipt Details
        receipt_frame = tk.LabelFrame(main_frame, text="Receipt Details", font=('Arial', 11, 'bold'),
                                     padx=10, pady=10)
        receipt_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(receipt_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.amount = tk.Entry(receipt_frame, width=20, font=('Arial', 10), relief='solid', bd=1)
        self.amount.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        tk.Label(receipt_frame, text=CURRENCY_SYMBOL, font=('Arial', 10)).grid(row=0, column=2, padx=5, pady=5, sticky='w')
        
        tk.Label(receipt_frame, text="Receipt Mode:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.receipt_mode = ttk.Combobox(receipt_frame, values=['Cash', 'Cheque', 'Bank Transfer', 'Card'], 
                                        width=17, font=('Arial', 10))
        self.receipt_mode.set('Cash')
        self.receipt_mode.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(receipt_frame, text="Reference No:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.reference = tk.Entry(receipt_frame, width=30, font=('Arial', 10), relief='solid', bd=1)
        self.reference.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Narration
        note_frame = tk.LabelFrame(main_frame, text="Narration", font=('Arial', 11, 'bold'),
                                  padx=10, pady=10)
        note_frame.pack(fill=tk.X, pady=10)
        
        self.narration = tk.Text(note_frame, height=3, width=60, font=('Arial', 10), relief='solid', bd=1)
        self.narration.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save Voucher", command=self.save_voucher,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", command=self.clear_form,
                 bg='#95a5a6', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        # ===== NEW PRINT BUTTON ADDED =====
        tk.Button(btn_frame, text="🖨️ Print", command=self.print_voucher,
                 bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=self.window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def print_voucher(self):
        """Print current voucher - placeholder for future functionality"""
        if not self.narration.get('1.0', tk.END).strip():
            show_error("Please save voucher first before printing")
            return
        
        if not self.selected_id:
            show_error("No voucher to print")
            return
        
        messagebox.showinfo("Print", "Print functionality will be added in future update.\n\nVoucher can be printed from history section later.")
    
    def save_voucher(self):
        """Save receipt voucher with correct accounting"""
        account_selection = self.account_entry.get().strip()
        amount_str = self.amount.get().strip()
        narration = self.narration.get('1.0', tk.END).strip()
        receipt_mode = self.receipt_mode.get()
        reference = self.reference.get().strip()
        
        if not self.selected_id:
            show_error("Please select a valid account from the list")
            return
        
        if not amount_str:
            show_error("Please enter amount")
            return
        
        try:
            amount = float(amount_str)
            if amount <= 0:
                show_error("Amount must be positive")
                return
        except ValueError:
            show_error("Invalid amount")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            # Begin transaction
            c.execute("BEGIN TRANSACTION")
            
            # Get the selected account details
            selected_account_id = self.selected_id
            
            # Insert voucher
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, 
                         created_by, created_at)
                        VALUES (?,?,?,?,?,?,?)''',
                      (self.voucher_no, 'Receipt', self.working_date, 
                       f"{narration} | Ref: {reference} | Mode: {receipt_mode}", 
                       amount, self.username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            voucher_id = c.lastrowid
            
            # Get Cash/Bank account ID based on receipt mode
            if receipt_mode == 'Cash':
                c.execute("SELECT id FROM accounts WHERE account_code='1000'")
            else:
                c.execute("SELECT id FROM accounts WHERE account_code='1101'")  # Main Bank Account
            cash_account = c.fetchone()
            if not cash_account:
                raise Exception("Cash/Bank account not found")
            cash_id = cash_account[0]
            
            # Debit Cash/Bank
            c.execute('''INSERT INTO ledger_entries 
                        (voucher_id, account_id, debit, credit, entry_date, narration)
                        VALUES (?,?,?,?,?,?)''',
                      (voucher_id, cash_id, amount, 0, self.working_date, 
                       f"Receipt from {self.selected_name}"))
            
            # Update Cash/Bank balance
            c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                     (amount, cash_id))
            
            # Credit selected account
            c.execute('''INSERT INTO ledger_entries 
                        (voucher_id, account_id, debit, credit, entry_date, narration)
                        VALUES (?,?,?,?,?,?)''',
                      (voucher_id, selected_account_id, 0, amount, self.working_date, 
                       f"Receipt credit"))
            
            # Update selected account balance based on account type
            if self.selected_type == 'Asset':
                # For asset accounts (like Receivable), credit decreases balance
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                         (amount, selected_account_id))
            else:
                # For Income/Liability accounts, credit increases balance
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                         (amount, selected_account_id))
            
            conn.commit()
            
            # Update the displayed balance after saving
            if self.selected_type == 'Asset':
                new_balance = self.selected_balance - amount
            else:
                new_balance = self.selected_balance + amount
            
            # Update balance label with new balance showing Dr/Cr
            if new_balance > 0:
                if self.selected_type in ['Asset', 'Expense']:
                    balance_text = f"Dr {CURRENCY_SYMBOL}{new_balance:,.0f}"
                else:
                    balance_text = f"Cr {CURRENCY_SYMBOL}{new_balance:,.0f}"
            elif new_balance < 0:
                abs_balance = abs(new_balance)
                if self.selected_type in ['Asset', 'Expense']:
                    balance_text = f"Cr {CURRENCY_SYMBOL}{abs_balance:,.0f}"
                else:
                    balance_text = f"Dr {CURRENCY_SYMBOL}{abs_balance:,.0f}"
            else:
                balance_text = f"{CURRENCY_SYMBOL}0"
            
            # Add prefix based on account type/code
            if self.selected_code == '1000':
                prefix = "💰 Cash in Hand"
            elif self.selected_code.startswith('110'):
                prefix = "🏦 Bank Account"
            elif self.selected_code == '1200':
                prefix = "📋 Accounts Receivable"
            elif self.selected_code.startswith('1-'):
                prefix = "👤 Member Account"
            elif self.selected_code.startswith('2-'):
                prefix = "📋 Supplier Account"
            elif self.selected_type == 'Income':
                prefix = "📈 Income"
            elif self.selected_type == 'Liability':
                prefix = "📋 Liability"
            elif self.selected_type == 'Expense':
                prefix = "📉 Expense"
            elif self.selected_type == 'Equity':
                prefix = "🏛️ Equity"
            else:
                prefix = "📊 Account"
            
            display_text = f"{prefix}: {balance_text}"
            self.balance_label.config(text=display_text)
            self.selected_balance = new_balance
            
            show_success(f"Receipt voucher saved!\nAccount: {self.selected_name}\nAmount: {CURRENCY_SYMBOL}{amount:.2f}")
            self.clear_form()
            self.generate_voucher_no()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error saving voucher: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    
    def clear_form(self):
        """Clear all fields"""
        self.account_entry.delete(0, tk.END)
        self.amount.delete(0, tk.END)
        self.receipt_mode.set('Cash')
        self.reference.delete(0, tk.END)
        self.narration.delete('1.0', tk.END)
        self.balance_label.config(text="Select an account")
        self.selected_id = None
        self.selected_name = None
        self.selected_balance = 0
        self.selected_code = None
        self.selected_type = None
        
        # Close any open popup safely
        self.close_popup_safe()