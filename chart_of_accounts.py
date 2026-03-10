# chart_of_accounts.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, show_error, show_success, ask_yes_no

class ChartOfAccounts:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Chart of Accounts Manager")
        self.window.geometry("1000x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"1000x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_accounts()
        self.load_parent_accounts()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#2c3e50', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📋 CHART OF ACCOUNTS MANAGER", fg='white', bg='#2c3e50',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Date display
        date_frame = tk.Frame(self.window, bg='#3498db', height=25)
        date_frame.pack(fill=tk.X)
        date_frame.pack_propagate(False)
        tk.Label(date_frame, text=f"📅 WORKING DATE: {self.working_date}", 
                fg='white', bg='#3498db', font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Main Paned Window
        paned = tk.PanedWindow(self.window, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left Panel - Account Tree (Hierarchical)
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=400)
        paned.add(left_frame, width=400, minsize=350)
        
        tk.Label(left_frame, text="📋 ACCOUNTS HIERARCHY", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        # Search box
        search_frame = tk.Frame(left_frame, bg='#ecf0f1')
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(search_frame, text="Search:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.filter_accounts())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        # Treeview for accounts (Hierarchical)
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        self.accounts_tree = ttk.Treeview(tree_frame, columns=('Code', 'Type', 'Balance'), 
                                          show='tree headings',
                                          yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                          height=20)
        vsb.config(command=self.accounts_tree.yview)
        hsb.config(command=self.accounts_tree.xview)
        
        self.accounts_tree.column('#0', width=300)
        self.accounts_tree.heading('#0', text='Account Name')
        self.accounts_tree.heading('Code', text='Code')
        self.accounts_tree.heading('Type', text='Type')
        self.accounts_tree.heading('Balance', text='Balance')
        
        self.accounts_tree.column('Code', width=80, anchor='center')
        self.accounts_tree.column('Type', width=80, anchor='center')
        self.accounts_tree.column('Balance', width=100, anchor='e')
        
        self.accounts_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.accounts_tree.bind('<<TreeviewSelect>>', self.on_account_select)
        
        # Right Panel - Account Details & Creation
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=600)
        
        # Create new account frame
        create_frame = tk.LabelFrame(right_frame, text="➕ CREATE NEW ACCOUNT", 
                                     font=('Arial', 12, 'bold'), padx=15, pady=10)
        create_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Account Type selection
        tk.Label(create_frame, text="Account Type:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.type_var = tk.StringVar()
        self.type_combo = ttk.Combobox(create_frame, textvariable=self.type_var, 
                                       values=['Asset', 'Liability', 'Equity', 'Income', 'COGS', 'Expense'],
                                       width=20, font=('Arial', 10))
        self.type_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Parent selection
        tk.Label(create_frame, text="Parent Account:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(create_frame, textvariable=self.parent_var, width=40, font=('Arial', 10))
        self.parent_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Account name
        tk.Label(create_frame, text="Account Name:", font=('Arial', 10)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.account_name = tk.Entry(create_frame, width=40, font=('Arial', 10), relief='solid', bd=1)
        self.account_name.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Opening balance
        tk.Label(create_frame, text="Opening Balance (Rs.):", font=('Arial', 10)).grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.opening_balance = tk.Entry(create_frame, width=20, font=('Arial', 10), relief='solid', bd=1)
        self.opening_balance.insert(0, "0")
        self.opening_balance.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Description
        tk.Label(create_frame, text="Description:", font=('Arial', 10)).grid(row=4, column=0, padx=5, pady=5, sticky='ne')
        self.description = tk.Text(create_frame, height=3, width=40, font=('Arial', 10), relief='solid', bd=1)
        self.description.grid(row=4, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons
        btn_frame = tk.Frame(create_frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="✅ Create Account", command=self.create_account,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", command=self.clear_form,
                 bg='#95a5a6', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Account details frame
        details_frame = tk.LabelFrame(right_frame, text="📊 ACCOUNT DETAILS", 
                                      font=('Arial', 12, 'bold'), padx=15, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.details_text = tk.Text(details_frame, height=12, width=60, font=('Courier', 10),
                                    relief='solid', bd=1, state='disabled')
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Action buttons for selected account
        action_frame = tk.Frame(details_frame)
        action_frame.pack(pady=5)
        
        tk.Button(action_frame, text="✏️ Edit", command=self.edit_account,
                 bg='#f39c12', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="❌ Deactivate", command=self.deactivate_account,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="🔄 Refresh", command=self.load_accounts,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def on_type_change(self, event=None):
        """Update parent accounts based on selected type"""
        self.load_parent_accounts()
    
    def load_parent_accounts(self):
        """Load parent accounts for dropdown based on selected type"""
        account_type = self.type_var.get()
        if not account_type:
            return
        
        # Map UI type to database type
        type_map = {
            'Asset': 'Asset',
            'Liability': 'Liability',
            'Equity': 'Equity',
            'Income': 'Income',
            'COGS': 'Expense',
            'Expense': 'Expense'
        }
        
        db_type = type_map.get(account_type, account_type)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get parent accounts (Level 1)
        c.execute('''SELECT id, account_code, account_name 
                     FROM accounts 
                     WHERE account_type = ? AND parent_id IS NULL
                     ORDER BY account_code''', (db_type,))
        parents = c.fetchall()
        conn.close()
        
        self.parents = parents
        parent_list = [f"{p[1]} - {p[2]}" for p in parents]
        self.parent_combo['values'] = parent_list
        if parent_list:
            self.parent_combo.current(0)
    
    def load_accounts(self):
        """Load all accounts into tree with hierarchy like Category Manager"""
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get all accounts ordered by code
        c.execute('''SELECT id, account_code, account_name, account_type, 
                            parent_id, current_balance, is_active
                     FROM accounts 
                     ORDER BY account_code''')
        accounts = c.fetchall()
        conn.close()
        
        # First, create a dictionary to organize by parent
        account_dict = {}
        for acc in accounts:
            acc_id = acc[0]
            account_dict[acc_id] = {
                'data': acc,
                'children': []
            }
        
        # Build hierarchy by assigning children to parents
        root_accounts = []
        for acc_id, acc_info in account_dict.items():
            acc = acc_info['data']
            parent_id = acc[4]  # parent_id is at index 4
            
            if parent_id is None or parent_id not in account_dict:
                root_accounts.append(acc_id)
            else:
                # Add as child to parent
                if parent_id in account_dict:
                    account_dict[parent_id]['children'].append(acc_id)
        
        # Function to recursively insert accounts
        def insert_account(acc_id, parent_node='', level=0):
            acc_info = account_dict[acc_id]
            acc = acc_info['data']
            
            acc_id_val, code, name, acc_type, parent_id, balance, active = acc
            
            # Determine icon based on type
            if acc_type == 'Asset':
                icon = '💰'
            elif acc_type == 'Liability':
                icon = '📋'
            elif acc_type == 'Equity':
                icon = '🏦'
            elif acc_type == 'Income':
                icon = '📈'
            elif acc_type == 'Expense':
                icon = '📉'
            else:
                icon = '📁'
            
            # Add active/inactive indicator
            status = '' if active else ' (Inactive)'
            
            # Create indentation based on level
            indent = '  ' * level
            
            # Insert the account
            if parent_node == '':
                node = self.accounts_tree.insert('', 'end', 
                                                text=f"{icon} {name}{status}",
                                                values=(code, acc_type, f"{CURRENCY_SYMBOL}{balance:.2f}"),
                                                iid=f"ACC_{acc_id}", open=True)
            else:
                node = self.accounts_tree.insert(parent_node, 'end',
                                                text=f"{indent}{icon} {name}{status}",
                                                values=(code, acc_type, f"{CURRENCY_SYMBOL}{balance:.2f}"),
                                                iid=f"ACC_{acc_id}", open=True)
            
            # Insert children recursively
            for child_id in acc_info['children']:
                insert_account(child_id, node, level + 1)
        
        # Insert all root accounts
        for acc_id in root_accounts:
            insert_account(acc_id)
    
    def filter_accounts(self):
        """Filter accounts based on search"""
        search = self.search_var.get().lower()
        
        # Expand all if searching
        if search:
            for item in self.accounts_tree.get_children():
                self.accounts_tree.item(item, open=True)
        else:
            # Collapse all except top level
            for item in self.accounts_tree.get_children():
                self.accounts_tree.item(item, open=False)
    
    def on_account_select(self, event):
        """Show account details when selected"""
        selected = self.accounts_tree.selection()
        if not selected:
            return
        
        acc_id = int(selected[0].replace('ACC_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT a.account_code, a.account_name, a.account_type, 
                            a.current_balance, a.created_date, a.is_active,
                            p.account_name as parent_name, p.account_code as parent_code
                     FROM accounts a
                     LEFT JOIN accounts p ON a.parent_id = p.id
                     WHERE a.id=?''', (acc_id,))
        acc = c.fetchone()
        
        if acc:
            code, name, acc_type, balance, created, active, parent_name, parent_code = acc
            
            # Get total debits and credits for this account
            c.execute('''SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                         FROM ledger_entries WHERE account_id=?''', (acc_id,))
            total_debit, total_credit = c.fetchone()
        
        conn.close()
        
        # Update details text
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        # Determine normal balance
        if acc_type in ['Asset', 'Expense']:
            normal_balance = "Debit"
        else:
            normal_balance = "Credit"
        
        details = f"""
{'='*60}
ACCOUNT DETAILS
{'='*60}

Account Code: {code}
Account Name: {name}
Account Type: {acc_type}
Normal Balance: {normal_balance}
Current Balance: {CURRENCY_SYMBOL}{balance:.2f}
Status: {'🟢 Active' if active else '🔴 Inactive'}

HIERARCHY:
Parent Account: {parent_name or 'None'}
Parent Code: {parent_code or 'None'}

TRANSACTION SUMMARY:
Total Debits: {CURRENCY_SYMBOL}{total_debit:.2f}
Total Credits: {CURRENCY_SYMBOL}{total_credit:.2f}
Net Change: {CURRENCY_SYMBOL}{(total_debit - total_credit):.2f}

Created: {created or 'N/A'}
        """
        
        self.details_text.insert('1.0', details)
        self.details_text.config(state='disabled')
    
    def create_account(self):
        """Create a new account"""
        acc_type = self.type_var.get()
        parent_sel = self.parent_combo.get()
        acc_name = self.account_name.get().strip()
        opening_bal = self.opening_balance.get().strip()
        desc = self.description.get('1.0', tk.END).strip()
        
        if not acc_type:
            show_error("Please select account type")
            return
        
        if not parent_sel:
            show_error("Please select a parent account")
            return
        
        if not acc_name:
            show_error("Please enter account name")
            return
        
        try:
            opening = float(opening_bal) if opening_bal else 0
        except ValueError:
            show_error("Invalid opening balance")
            return
        
        # Find parent ID
        parent_id = None
        parent_code = None
        for pid, pcode, pname in self.parents:
            if f"{pcode} - {pname}" == parent_sel:
                parent_id = pid
                parent_code = pcode
                break
        
        if not parent_id:
            show_error("Invalid parent account")
            return
        
        # Map UI type to database type
        type_map = {
            'Asset': 'Asset',
            'Liability': 'Liability',
            'Equity': 'Equity',
            'Income': 'Income',
            'COGS': 'Expense',
            'Expense': 'Expense'
        }
        db_type = type_map.get(acc_type, acc_type)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            # Get the base prefix (e.g., "1" from "1-1000" or "1200")
            if '-' in parent_code:
                base_prefix = parent_code.split('-')[0]
                parent_num = int(parent_code.split('-')[1])
            else:
                # Handle codes without hyphen (like "1200")
                base_prefix = parent_code[0]  # First digit as prefix
                parent_num = int(parent_code)
            
            # Get the next available account code under this parent
            c.execute('''SELECT account_code FROM accounts 
                         WHERE account_code LIKE ? 
                         ORDER BY account_code DESC LIMIT 1''', 
                      (f'{base_prefix}-%',))
            last = c.fetchone()
            
            if last:
                # Extract number from last account code
                last_code = last[0]
                if '-' in last_code:
                    last_num = int(last_code.split('-')[1])
                else:
                    last_num = int(last_code)
                new_code = f"{base_prefix}-{last_num + 1:04d}"
            else:
                # If no existing children, start at parent_num + 1
                new_code = f"{base_prefix}-{parent_num + 1:04d}"
            
            # Create the account
            c.execute('''INSERT INTO accounts 
                        (account_code, account_name, account_type, parent_id, parent_code,
                         opening_balance, current_balance, is_active, created_date, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)''',
                      (new_code, acc_name, db_type, parent_id, parent_code, opening, opening, 
                       self.working_date, desc))
            
            conn.commit()
            show_success(f"Account '{acc_name}' created successfully!\nCode: {new_code}")
            
            self.clear_form()
            self.load_accounts()
            
        except Exception as e:
            conn.rollback()
            show_error(f"Error creating account: {e}")
        finally:
            conn.close()
    
    def edit_account(self):
        """Edit selected account"""
        selected = self.accounts_tree.selection()
        if not selected:
            show_error("Select an account to edit")
            return
        
        acc_id = int(selected[0].replace('ACC_', ''))
        
        # Simple edit dialog
        new_name = tk.simpledialog.askstring("Edit Account", "Enter new account name:",
                                             parent=self.window)
        if new_name and new_name.strip():
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("UPDATE accounts SET account_name=? WHERE id=?", (new_name.strip(), acc_id))
            conn.commit()
            conn.close()
            
            show_success("Account name updated")
            self.load_accounts()
    
    def deactivate_account(self):
        """Deactivate selected account"""
        selected = self.accounts_tree.selection()
        if not selected:
            show_error("Select an account to deactivate")
            return
        
        acc_id = int(selected[0].replace('ACC_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Check if account has any transactions
        c.execute("SELECT COUNT(*) FROM ledger_entries WHERE account_id=?", (acc_id,))
        tx_count = c.fetchone()[0]
        
        c.execute("SELECT account_name FROM accounts WHERE id=?", (acc_id,))
        acc_name = c.fetchone()[0]
        conn.close()
        
        if tx_count > 0:
            msg = f"Account '{acc_name}' has {tx_count} transactions. Deactivating will hide it but keep history."
        else:
            msg = f"Deactivate account '{acc_name}'?"
        
        if ask_yes_no(msg):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("UPDATE accounts SET is_active=0 WHERE id=?", (acc_id,))
            conn.commit()
            conn.close()
            
            show_success(f"Account '{acc_name}' deactivated")
            self.load_accounts()
    
    def clear_form(self):
        """Clear the create account form"""
        self.type_var.set('')
        self.parent_combo.set('')
        self.account_name.delete(0, tk.END)
        self.opening_balance.delete(0, tk.END)
        self.opening_balance.insert(0, "0")
        self.description.delete('1.0', tk.END)

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    coa = ChartOfAccounts(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()