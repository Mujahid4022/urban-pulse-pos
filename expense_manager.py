# expense_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, show_error, show_success, ask_yes_no

class ExpenseManager:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Expense Account Manager")
        self.window.geometry("900x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"900x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_expense_accounts()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#e74c3c', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📉 EXPENSE ACCOUNT MANAGER", fg='white', bg='#e74c3c',
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
        
        # Left Panel - Account Tree
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=300)
        paned.add(left_frame, width=300, minsize=250)
        
        tk.Label(left_frame, text="📋 EXPENSE ACCOUNTS", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        # Treeview for expense accounts
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        self.accounts_tree = ttk.Treeview(tree_frame, columns=('Code', 'Balance'), show='tree',
                                          yscrollcommand=vsb.set, height=20)
        vsb.config(command=self.accounts_tree.yview)
        
        self.accounts_tree.column('#0', width=200)
        self.accounts_tree.heading('#0', text='Account Name')
        self.accounts_tree.heading('Code', text='Code')
        self.accounts_tree.heading('Balance', text='Balance')
        
        self.accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.accounts_tree.bind('<<TreeviewSelect>>', self.on_account_select)
        
        # Right Panel - Account Details & Creation
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=600)
        
        # Create new account frame
        create_frame = tk.LabelFrame(right_frame, text="➕ CREATE NEW EXPENSE ACCOUNT", 
                                     font=('Arial', 12, 'bold'), padx=15, pady=10)
        create_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Parent selection
        tk.Label(create_frame, text="Parent Account:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(create_frame, textvariable=self.parent_var, width=40, font=('Arial', 10))
        self.parent_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        self.load_parent_accounts()
        
        # Account name
        tk.Label(create_frame, text="Account Name:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.account_name = tk.Entry(create_frame, width=40, font=('Arial', 10), relief='solid', bd=1)
        self.account_name.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Opening balance
        tk.Label(create_frame, text="Opening Balance (Rs.):", font=('Arial', 10)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.opening_balance = tk.Entry(create_frame, width=20, font=('Arial', 10), relief='solid', bd=1)
        self.opening_balance.insert(0, "0")
        self.opening_balance.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Description
        tk.Label(create_frame, text="Description:", font=('Arial', 10)).grid(row=3, column=0, padx=5, pady=5, sticky='ne')
        self.description = tk.Text(create_frame, height=3, width=40, font=('Arial', 10), relief='solid', bd=1)
        self.description.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons
        btn_frame = tk.Frame(create_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
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
        
        self.details_text = tk.Text(details_frame, height=10, width=60, font=('Courier', 10),
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
        tk.Button(action_frame, text="🔄 Refresh", command=self.load_expense_accounts,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def load_parent_accounts(self):
        """Load parent expense accounts for dropdown"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get all expense parent accounts (Level 3)
        c.execute('''SELECT id, account_code, account_name 
                     FROM accounts 
                     WHERE account_type = 'Expense' 
                     AND parent_id IS NULL
                     ORDER BY account_code''')
        parents = c.fetchall()
        conn.close()
        
        self.parents = parents
        parent_list = [f"{p[1]} - {p[2]}" for p in parents]
        self.parent_combo['values'] = parent_list
        if parent_list:
            self.parent_combo.current(0)
    
    def load_expense_accounts(self):
        """Load all expense accounts into tree"""
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Get all expense accounts
        c.execute('''SELECT id, account_code, account_name, parent_id, current_balance 
                     FROM accounts 
                     WHERE account_type = 'Expense'
                     ORDER BY account_code''')
        accounts = c.fetchall()
        conn.close()
        
        # Build tree structure
        parent_nodes = {}
        
        for acc in accounts:
            acc_id, code, name, parent_id, balance = acc
            
            if parent_id is None:
                # Parent account
                node = self.accounts_tree.insert('', 'end', text=f"  {name}", 
                                                values=(code, f"{CURRENCY_SYMBOL}{balance:.2f}"),
                                                iid=f"ACC_{acc_id}", open=True)
                parent_nodes[acc_id] = node
            else:
                # Child account
                if parent_id in parent_nodes:
                    parent_node = parent_nodes[parent_id]
                else:
                    parent_node = ''
                
                self.accounts_tree.insert(parent_node, 'end', text=f"    {name}",
                                         values=(code, f"{CURRENCY_SYMBOL}{balance:.2f}"),
                                         iid=f"ACC_{acc_id}")
    
    def on_account_select(self, event):
        """Show account details when selected"""
        selected = self.accounts_tree.selection()
        if not selected:
            return
        
        acc_id = int(selected[0].replace('ACC_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT account_code, account_name, current_balance, 
                            parent_code, created_date, is_active
                     FROM accounts WHERE id=?''', (acc_id,))
        acc = c.fetchone()
        
        if acc:
            code, name, balance, parent, created, active = acc
            
            # Get total debits and credits for this account
            c.execute('''SELECT COALESCE(SUM(debit), 0), COALESCE(SUM(credit), 0)
                         FROM ledger_entries WHERE account_id=?''', (acc_id,))
            total_debit, total_credit = c.fetchone()
        
        conn.close()
        
        # Update details text
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        details = f"""
{'='*50}
ACCOUNT DETAILS
{'='*50}

Account Code: {code}
Account Name: {name}
Account Type: Expense
Current Balance: {CURRENCY_SYMBOL}{balance:.2f}
Status: {'🟢 Active' if active else '🔴 Inactive'}

TRANSACTION SUMMARY:
Total Debits: {CURRENCY_SYMBOL}{total_debit:.2f}
Total Credits: {CURRENCY_SYMBOL}{total_credit:.2f}
Net Change: {CURRENCY_SYMBOL}{(total_debit - total_credit):.2f}

Created: {created or 'N/A'}
Parent: {parent or 'None'}
        """
        
        self.details_text.insert('1.0', details)
        self.details_text.config(state='disabled')
    
    def create_account(self):
        """Create a new expense account"""
        parent_sel = self.parent_combo.get()
        acc_name = self.account_name.get().strip()
        opening_bal = self.opening_balance.get().strip()
        desc = self.description.get('1.0', tk.END).strip()
        
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
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            # Get the next available account code under this parent
            base_code = parent_code.split('-')[1][:2]  # Get the first two digits of parent code
            c.execute('''SELECT account_code FROM accounts 
                         WHERE account_code LIKE ? 
                         ORDER BY account_code DESC LIMIT 1''', 
                      (f'5-{base_code}%',))
            last = c.fetchone()
            
            if last:
                last_num = int(last[0].split('-')[1])
                new_code = f"5-{last_num + 1:04d}"
            else:
                new_code = f"5-{base_code}01"
            
            # Create the account
            c.execute('''INSERT INTO accounts 
                        (account_code, account_name, account_type, parent_id, parent_code,
                         opening_balance, current_balance, is_active, created_date, description)
                        VALUES (?, ?, 'Expense', ?, ?, ?, ?, 1, ?, ?)''',
                      (new_code, acc_name, parent_id, parent_code, opening, opening, 
                       self.working_date, desc))
            
            conn.commit()
            show_success(f"Expense account '{acc_name}' created successfully!\nCode: {new_code}")
            
            self.clear_form()
            self.load_expense_accounts()
            
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
        
        # Simple edit dialog - can be expanded
        new_name = tk.simpledialog.askstring("Edit Account", "Enter new account name:",
                                             parent=self.window)
        if new_name:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("UPDATE accounts SET account_name=? WHERE id=?", (new_name.strip(), acc_id))
            conn.commit()
            conn.close()
            
            show_success("Account name updated")
            self.load_expense_accounts()
    
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
            msg = f"Account '{acc_name}' has {tx_count} transactions. Deactivating will hide it from lists but keep history."
        else:
            msg = f"Deactivate account '{acc_name}'?"
        
        if ask_yes_no(msg):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("UPDATE accounts SET is_active=0 WHERE id=?", (acc_id,))
            conn.commit()
            conn.close()
            
            show_success(f"Account '{acc_name}' deactivated")
            self.load_expense_accounts()
    
    def clear_form(self):
        """Clear the create account form"""
        self.account_name.delete(0, tk.END)
        self.opening_balance.delete(0, tk.END)
        self.opening_balance.insert(0, "0")
        self.description.delete('1.0', tk.END)

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    em = ExpenseManager(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()