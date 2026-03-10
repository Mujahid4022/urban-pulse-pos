# voucher_journal.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, show_error, show_success

class JournalVoucher:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Journal Voucher")
        self.window.geometry("950x800")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 950) // 2
        y = (self.window.winfo_screenheight() - 800) // 2
        self.window.geometry(f"950x800+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.entries = []
        self.all_accounts = []
        self.account_display_list = []
        self.current_popup = None
        self.current_listbox = None
        self.filtered_items = []
        self.current_entry = None
        self.current_type_filter = None
        
        self.create_widgets()
        self.load_accounts()
        self.generate_voucher_no()
        self.add_entry_row()
        self.add_entry_row()
    
    def generate_voucher_no(self):
        """Generate unique voucher number using working date"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        today = self.working_date.replace('-', '')
        c.execute("SELECT COUNT(*) FROM vouchers WHERE voucher_no LIKE ?", (f'JV-{today}%',))
        count = c.fetchone()[0] + 1
        conn.close()
        self.voucher_no = f"JV-{today}-{count:03d}"
        self.voucher_no_var.set(self.voucher_no)
    
    def load_accounts(self):
        """Load ALL accounts"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            c.execute('''SELECT id, account_code, account_name, account_type, current_balance 
                         FROM accounts 
                         WHERE is_active = 1
                         ORDER BY account_code''')
            self.all_accounts = c.fetchall()
            conn.close()
            
            # Create formatted list for display with balances
            self.account_display_list = []
            for acc in self.all_accounts:
                acc_id, code, name, acc_type, balance = acc
                
                # Add emoji based on type
                if acc_type == 'Asset':
                    prefix = '💰'
                elif acc_type == 'Liability':
                    prefix = '📋'
                elif acc_type == 'Equity':
                    prefix = '🏦'
                elif acc_type == 'Income':
                    prefix = '📈'
                elif acc_type == 'Expense':
                    prefix = '📉'
                else:
                    prefix = '📊'
                
                # Truncate long names for better display
                if len(name) > 30:
                    name = name[:27] + '...'
                
                display = f"{prefix} {code} - {name}"
                if balance != 0:
                    if balance > 0:
                        if acc_type in ['Asset', 'Expense']:
                            display += f" [Dr {CURRENCY_SYMBOL}{balance:,.0f}]"
                        else:
                            display += f" [Cr {CURRENCY_SYMBOL}{balance:,.0f}]"
                    else:
                        abs_balance = abs(balance)
                        if acc_type in ['Asset', 'Expense']:
                            display += f" [Cr {CURRENCY_SYMBOL}{abs_balance:,.0f}]"
                        else:
                            display += f" [Dr {CURRENCY_SYMBOL}{abs_balance:,.0f}]"
                
                self.account_display_list.append(display)
            
            print(f"✅ Loaded {len(self.all_accounts)} accounts")
        except Exception as e:
            print(f"❌ Error loading accounts: {e}")
            self.all_accounts = []
            self.account_display_list = []
    
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
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📝 JOURNAL VOUCHER", fg='white', bg='#f39c12',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Main form
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Voucher info
        info_frame = tk.LabelFrame(main_frame, text="Voucher Information", font=('Arial', 11, 'bold'),
                                  padx=10, pady=8)
        info_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(info_frame, text="Voucher No:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.voucher_no_var = tk.StringVar()
        tk.Entry(info_frame, textvariable=self.voucher_no_var, width=20, 
                font=('Arial', 10), state='readonly', relief='solid', bd=1).grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        tk.Label(info_frame, text="Date:").grid(row=0, column=2, padx=(20,5), pady=5, sticky='e')
        tk.Label(info_frame, text=self.working_date, font=('Arial', 10, 'bold'),
                bg='#f9f9f9', fg='#2980b9').grid(row=0, column=3, padx=5, pady=5, sticky='w')
        
        # Narration for whole voucher
        tk.Label(info_frame, text="Narration:", font=('Arial', 10, 'bold')).grid(row=1, column=0, padx=5, pady=5, sticky='ne')
        self.voucher_narration = tk.Text(info_frame, height=2, width=60, font=('Arial', 10), relief='solid', bd=1)
        self.voucher_narration.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='w')
        
        # ===== FILTER BUTTONS ONLY (NO SEARCH FIELD) =====
        filter_frame = tk.Frame(main_frame, bg='#f9f9f9')
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="Filter by type:", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Quick filter buttons
        tk.Button(filter_frame, text="All", command=lambda: self.set_type_filter(None),
                 bg='#3498db', fg='white', font=('Arial', 8, 'bold'), 
                 width=5, height=1, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Asset", command=lambda: self.set_type_filter('Asset'),
                 bg='#27ae60', fg='white', font=('Arial', 8, 'bold'), 
                 width=5, height=1, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Liability", command=lambda: self.set_type_filter('Liability'),
                 bg='#e74c3c', fg='white', font=('Arial', 8, 'bold'), 
                 width=6, height=1, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Income", command=lambda: self.set_type_filter('Income'),
                 bg='#f39c12', fg='white', font=('Arial', 8, 'bold'), 
                 width=5, height=1, cursor='hand2').pack(side=tk.LEFT, padx=2)
        tk.Button(filter_frame, text="Expense", command=lambda: self.set_type_filter('Expense'),
                 bg='#9b59b6', fg='white', font=('Arial', 8, 'bold'), 
                 width=6, height=1, cursor='hand2').pack(side=tk.LEFT, padx=2)
        
        # Entries Frame
        entries_frame = tk.LabelFrame(main_frame, text="Journal Entries", font=('Arial', 11, 'bold'),
                                     padx=10, pady=10)
        entries_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Headers
        header_frame = tk.Frame(entries_frame, bg='#2c3e50', height=30)
        header_frame.pack(fill=tk.X, pady=2)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="Account", font=('Arial', 10, 'bold'), 
                bg='#2c3e50', fg='white', width=55, anchor='w').pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Debit", font=('Arial', 10, 'bold'), 
                bg='#2c3e50', fg='white', width=12, anchor='e').pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="Credit", font=('Arial', 10, 'bold'), 
                bg='#2c3e50', fg='white', width=12, anchor='e').pack(side=tk.LEFT, padx=5)
        tk.Label(header_frame, text="", width=3, bg='#2c3e50').pack(side=tk.LEFT)
        
        # Scrollable frame for entries
        canvas = tk.Canvas(entries_frame, bg='#f9f9f9', highlightthickness=0, height=300)
        scrollbar = tk.Scrollbar(entries_frame, orient="vertical", command=canvas.yview)
        self.entries_container = tk.Frame(canvas, bg='#f9f9f9')
        
        self.entries_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.entries_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add Entry button
        btn_add = tk.Button(entries_frame, text="➕ Add Entry", command=self.add_entry_row,
                           bg='#3498db', fg='white', font=('Arial', 9, 'bold'),
                           width=15, height=1, cursor='hand2')
        btn_add.pack(pady=5)
        
        # Totals Frame
        total_frame = tk.Frame(main_frame, bg='#ecf0f1', relief=tk.RIDGE, bd=2)
        total_frame.pack(fill=tk.X, pady=5)
        
        total_inner = tk.Frame(total_frame, bg='#ecf0f1', padx=10, pady=8)
        total_inner.pack()
        
        tk.Label(total_inner, text="Total Debit:", font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.total_debit_label = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 11, 'bold'),
                                         bg='#ecf0f1', fg='#e74c3c', width=12)
        self.total_debit_label.pack(side=tk.LEFT, padx=5)
        
        tk.Label(total_inner, text="Total Credit:", font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=(20,5))
        self.total_credit_label = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 11, 'bold'),
                                          bg='#ecf0f1', fg='#27ae60', width=12)
        self.total_credit_label.pack(side=tk.LEFT, padx=5)
        
        tk.Label(total_inner, text="Difference:", font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=(20,5))
        self.diff_label = tk.Label(total_inner, text=f"{CURRENCY_SYMBOL}0.00", font=('Arial', 11, 'bold'),
                                  bg='#ecf0f1', fg='#2980b9', width=12)
        self.diff_label.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="💾 Save Voucher", command=self.save_voucher,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, height=1, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear All", command=self.clear_all,
                 bg='#95a5a6', fg='white', font=('Arial', 10, 'bold'),
                 width=12, height=1, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🖨️ Print", command=self.print_voucher,
                 bg='#9b59b6', fg='white', font=('Arial', 10, 'bold'),
                 width=10, height=1, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=self.window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 10, 'bold'),
                 width=10, height=1, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def set_type_filter(self, acc_type):
        """Set the account type filter"""
        self.current_type_filter = acc_type
        filter_name = acc_type if acc_type else "All"
        messagebox.showinfo("Filter Applied", f"Showing {filter_name} accounts.\nClick in Account field to see filtered results.")
    
    def print_voucher(self):
        """Print current voucher - placeholder"""
        if not self.voucher_narration.get('1.0', tk.END).strip():
            show_error("Please save voucher first before printing")
            return
        
        if not self.entries or len(self.entries) < 2:
            show_error("No entries to print")
            return
        
        messagebox.showinfo("Print", "Print functionality will be added in future update.")
    
    def add_entry_row(self, account='', debit='', credit=''):
        """Add a new entry row with popup search"""
        row_frame = tk.Frame(self.entries_container, bg='#f9f9f9')
        row_frame.pack(fill=tk.X, pady=2)
        
        # Create a dictionary to store row widgets
        entry_row = {}
        
        # Account Entry
        account_var = tk.StringVar(value=account)
        account_entry = tk.Entry(row_frame, textvariable=account_var, 
                                width=55, font=('Arial', 9), relief='solid', bd=1)
        account_entry.pack(side=tk.LEFT, padx=2)
        
        entry_row['account_entry'] = account_entry
        entry_row['account_var'] = account_var
        
        # Function to close popup
        def close_popup():
            if self.current_popup and self.current_popup.winfo_exists():
                self.current_popup.destroy()
                self.current_popup = None
                self.current_listbox = None
                self.filtered_items = []
        
        # Function to show popup with suggestions
        def show_popup():
            # Close existing popup
            close_popup()
            
            current_text = account_var.get().lower()
            
            # Filter accounts based on text and type filter
            suggestions = []
            filtered_items = []
            
            for i, acc_display in enumerate(self.account_display_list):
                acc = self.all_accounts[i]
                acc_type = acc[3]
                
                # Apply type filter if set
                if self.current_type_filter and acc_type != self.current_type_filter:
                    continue
                
                # Apply text filter
                if not current_text or current_text in acc_display.lower():
                    suggestions.append(acc_display)
                    filtered_items.append(acc)
            
            if not suggestions:
                return
            
            # Create popup
            popup = tk.Toplevel(self.window)
            popup.overrideredirect(True)
            
            # Position popup below the entry field
            x = account_entry.winfo_rootx()
            y = account_entry.winfo_rooty() + account_entry.winfo_height()
            
            # Adjust height based on number of suggestions
            height = min(250, len(suggestions) * 20 + 10)
            popup.geometry(f"650x{height}+{x}+{y}")
            
            # Add listbox with scrollbar
            frame = tk.Frame(popup, bg='white')
            frame.pack(fill=tk.BOTH, expand=True)
            
            listbox = tk.Listbox(frame, height=min(12, len(suggestions)), 
                                font=('Arial', 9), bg='white', selectbackground='#3498db')
            scrollbar = tk.Scrollbar(frame, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            # Add suggestions
            for sugg in suggestions:
                listbox.insert(tk.END, sugg)
            
            self.current_popup = popup
            self.current_listbox = listbox
            self.filtered_items = filtered_items
            self.current_entry = account_entry
            
            # Select first item by default
            if listbox.size() > 0:
                listbox.selection_set(0)
                listbox.activate(0)
            
            # Set focus to listbox
            listbox.focus_set()
            
            # Function to select item
            def select_item(event=None):
                if self.current_listbox and self.current_listbox.curselection():
                    idx = self.current_listbox.curselection()[0]
                    selected_text = self.current_listbox.get(idx)
                    account_var.set(selected_text)
                    close_popup()
                    # Move focus to debit field
                    debit_entry.focus()
            
            # Mouse click selection
            listbox.bind('<ButtonRelease-1>', select_item)
            listbox.bind('<Double-Button-1>', select_item)
            listbox.bind('<Return>', select_item)
            
            # Keyboard navigation
            def on_key(event):
                if not self.current_popup or not self.current_listbox:
                    return
                    
                if event.keysym == 'Down':
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
                    close_popup()
                    account_entry.focus()
                    return 'break'
                
                return None
            
            # Bind keyboard events
            popup.bind('<Key>', on_key)
            listbox.bind('<Key>', on_key)
            
            # Bind click outside to close popup
            def on_click_outside(event):
                if self.current_popup and self.current_popup.winfo_exists():
                    clicked_widget = event.widget
                    if clicked_widget not in (popup, listbox, scrollbar, frame) and clicked_widget != account_entry:
                        close_popup()
            
            self.window.bind('<Button-1>', on_click_outside)
            
            # Ensure popup stays on top
            popup.lift()
            popup.focus_force()
        
        # Function to handle key release with debounce
        def on_key_release(event):
            # Use after to debounce
            if hasattr(self, '_after_id'):
                self.window.after_cancel(self._after_id)
            self._after_id = self.window.after(200, show_popup)
        
        # Bind key release
        account_entry.bind('<KeyRelease>', on_key_release)
        account_entry.bind('<FocusIn>', on_key_release)
        
        # Debit Entry
        debit_var = tk.StringVar(value=debit)
        debit_entry = tk.Entry(row_frame, textvariable=debit_var, width=12, font=('Arial', 9),
                              justify='right', relief='solid', bd=1)
        debit_entry.pack(side=tk.LEFT, padx=2)
        debit_entry.bind('<KeyRelease>', self.calculate_totals)
        entry_row['debit'] = debit_var
        entry_row['debit_entry'] = debit_entry
        
        # Credit Entry
        credit_var = tk.StringVar(value=credit)
        credit_entry = tk.Entry(row_frame, textvariable=credit_var, width=12, font=('Arial', 9),
                               justify='right', relief='solid', bd=1)
        credit_entry.pack(side=tk.LEFT, padx=2)
        credit_entry.bind('<KeyRelease>', self.calculate_totals)
        entry_row['credit'] = credit_var
        
        # Remove button
        remove_btn = tk.Button(row_frame, text="❌", command=lambda: self.remove_entry_row(row_frame),
                              bg='#e74c3c', fg='white', font=('Arial', 8, 'bold'), 
                              width=2, height=1, cursor='hand2')
        remove_btn.pack(side=tk.LEFT, padx=2)
        
        # Store row data
        entry_row['frame'] = row_frame
        self.entries.append(entry_row)
    
    def remove_entry_row(self, row_frame):
        """Remove an entry row"""
        for entry in self.entries:
            if entry['frame'] == row_frame:
                self.entries.remove(entry)
                row_frame.destroy()
                break
        self.calculate_totals()
    
    def calculate_totals(self, event=None):
        """Calculate total debit and credit"""
        total_debit = 0
        total_credit = 0
        
        for entry in self.entries:
            try:
                if entry['debit'].get().strip():
                    total_debit += float(entry['debit'].get() or 0)
                if entry['credit'].get().strip():
                    total_credit += float(entry['credit'].get() or 0)
            except ValueError:
                pass
        
        self.total_debit_label.config(text=f"{CURRENCY_SYMBOL}{total_debit:.2f}")
        self.total_credit_label.config(text=f"{CURRENCY_SYMBOL}{total_credit:.2f}")
        
        diff = total_debit - total_credit
        self.diff_label.config(text=f"{CURRENCY_SYMBOL}{diff:.2f}")
        
        if diff == 0:
            self.diff_label.config(fg='#27ae60')
        else:
            self.diff_label.config(fg='#e74c3c')
    
    def save_voucher(self):
        """Save journal voucher"""
        voucher_narration = self.voucher_narration.get('1.0', tk.END).strip()
        
        if not voucher_narration:
            show_error("Please enter narration for this voucher")
            return
        
        total_debit = 0
        total_credit = 0
        journal_entries = []
        
        for entry in self.entries:
            account_sel = entry['account_var'].get().strip()
            debit_str = entry['debit'].get().strip()
            credit_str = entry['credit'].get().strip()
            
            if not account_sel:
                show_error("Please select account for all rows")
                return
            
            # Find account ID
            account_id = None
            for i, acc in enumerate(self.all_accounts):
                if self.account_display_list[i] == account_sel or acc[2] in account_sel or acc[1] in account_sel:
                    account_id = acc[0]
                    break
            
            if not account_id:
                show_error(f"Invalid account selection: {account_sel}")
                return
            
            try:
                debit = float(debit_str) if debit_str else 0
                credit = float(credit_str) if credit_str else 0
            except ValueError:
                show_error("Invalid amount in one of the rows")
                return
            
            if debit > 0 and credit > 0:
                show_error("A row cannot have both debit and credit")
                return
            
            if debit == 0 and credit == 0:
                show_error("Each row must have either debit or credit amount")
                return
            
            total_debit += debit
            total_credit += credit
            
            journal_entries.append({
                'account_id': account_id,
                'debit': debit,
                'credit': credit
            })
        
        if total_debit != total_credit:
            show_error(f"Journal is not balanced!\nDebit: {CURRENCY_SYMBOL}{total_debit:.2f}\nCredit: {CURRENCY_SYMBOL}{total_credit:.2f}\nDifference: {CURRENCY_SYMBOL}{abs(total_debit - total_credit):.2f}")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            c.execute("BEGIN TRANSACTION")
            
            c.execute('''INSERT INTO vouchers 
                        (voucher_no, voucher_type, voucher_date, narration, total_amount, 
                         created_by, created_at)
                        VALUES (?,?,?,?,?,?,?)''',
                      (self.voucher_no, 'Journal', self.working_date, voucher_narration, 
                       total_debit, self.username, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            voucher_id = c.lastrowid
            
            for entry in journal_entries:
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?,?,?,?,?,?)''',
                          (voucher_id, entry['account_id'], entry['debit'], entry['credit'], 
                           self.working_date, voucher_narration))
                
                # Update account balances
                if entry['debit'] > 0:
                    c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                             (entry['debit'], entry['account_id']))
                if entry['credit'] > 0:
                    c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                             (entry['credit'], entry['account_id']))
            
            conn.commit()
            show_success(f"Journal voucher {self.voucher_no} saved successfully!\nTotal Amount: {CURRENCY_SYMBOL}{total_debit:.2f}")
            self.clear_all()
            self.generate_voucher_no()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error saving voucher: {e}")
            import traceback
            traceback.print_exc()
        finally:
            conn.close()
    
    def clear_all(self):
        """Clear all entries"""
        # Close any open popup
        self.close_popup_safe()
        
        # Clear all entry rows
        for entry in self.entries:
            try:
                entry['frame'].destroy()
            except:
                pass
        self.entries.clear()
        
        # Add fresh rows
        self.add_entry_row()
        self.add_entry_row()
        
        # Clear narration
        self.voucher_narration.delete('1.0', tk.END)
        
        # Reset totals
        self.calculate_totals()