# trial_balance.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL

class TrialBalance:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Trial Balance")
        self.window.geometry("1100x750")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1100) // 2
        y = (self.window.winfo_screenheight() - 750) // 2
        self.window.geometry(f"1100x750+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_trial_balance()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#9b59b6', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="⚖️ TRIAL BALANCE", fg='white', bg='#9b59b6',
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
        
        tk.Button(filter_frame, text="🔍 Refresh", command=self.load_trial_balance,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="📊 Export CSV", command=self.export_csv,
                 bg='#27ae60', fg='white', font=('Arial', 9),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        tk.Button(filter_frame, text="🖨️ Print", command=lambda: messagebox.showinfo("Print", "Use Export CSV to save and print"),
                 bg='#9b59b6', fg='white', font=('Arial', 9, 'bold'),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Treeview Frame with hierarchy
        tree_frame = tk.Frame(self.window)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        # Treeview with hierarchy (show='tree' for hierarchical view)
        columns = ('Account Code', 'Debit', 'Credit')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings',
                                  yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=20)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Column settings
        self.tree.column('#0', width=450, minwidth=350, stretch=True)
        self.tree.heading('#0', text='Account Name')
        
        self.tree.heading('Account Code', text='Code')
        self.tree.heading('Debit', text=f'Debit ({CURRENCY_SYMBOL})')
        self.tree.heading('Credit', text=f'Credit ({CURRENCY_SYMBOL})')
        
        self.tree.column('Account Code', width=100, anchor='center')
        self.tree.column('Debit', width=130, anchor='e')
        self.tree.column('Credit', width=130, anchor='e')
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Summary Frame
        summary_frame = tk.Frame(self.window, bg='#ecf0f1', height=50)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        summary_frame.pack_propagate(False)
        
        tk.Label(summary_frame, text="Total Debit:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=200, y=15)
        self.total_debit = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1', 
                                    font=('Arial', 11, 'bold'), fg='#e74c3c')
        self.total_debit.place(x=300, y=15)
        
        tk.Label(summary_frame, text="Total Credit:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=450, y=15)
        self.total_credit = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1',
                                     font=('Arial', 11, 'bold'), fg='#27ae60')
        self.total_credit.place(x=550, y=15)
        
        tk.Label(summary_frame, text="Difference:", bg='#ecf0f1', font=('Arial', 11, 'bold')).place(x=700, y=15)
        self.difference = tk.Label(summary_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ecf0f1',
                                   font=('Arial', 11, 'bold'), fg='#2980b9')
        self.difference.place(x=800, y=15)
    
    def load_trial_balance(self):
        """Load trial balance data with proper hierarchy"""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            # Define account types in order
            account_types = [
                ('Asset', '💰 ASSETS'),
                ('Liability', '📋 LIABILITIES'),
                ('Equity', '🏦 EQUITY'),
                ('Income', '📈 INCOME'),
                ('Expense', '📉 EXPENSES')
            ]
            
            total_debit = 0
            total_credit = 0
            
            for acc_type, display_name in account_types:
                # Add type header
                type_node = self.tree.insert('', tk.END, 
                                            text=display_name,
                                            values=('', '', ''),
                                            tags=('type',))
                
                # Get parent accounts of this type
                c.execute('''
                    SELECT id, account_code, account_name, current_balance
                    FROM accounts
                    WHERE account_type = ? AND is_active = 1 AND parent_id IS NULL
                    ORDER BY account_code
                ''', (acc_type,))
                
                parent_accounts = c.fetchall()
                
                type_debit = 0
                type_credit = 0
                
                for parent in parent_accounts:
                    p_id, p_code, p_name, p_balance = parent
                    
                    # Add parent account
                    parent_node = self.tree.insert(type_node, tk.END,
                                                  text=f"  {p_name}",
                                                  values=(p_code, '', ''),
                                                  tags=('parent',))
                    
                    # Get child accounts under this parent
                    c.execute('''
                        SELECT account_code, account_name, current_balance
                        FROM accounts
                        WHERE parent_id = ? AND is_active = 1
                        ORDER BY account_code
                    ''', (p_id,))
                    
                    child_accounts = c.fetchall()
                    
                    parent_debit = 0
                    parent_credit = 0
                    
                    # Process parent's own balance
                    if acc_type in ['Asset', 'Expense']:
                        if p_balance > 0:
                            p_debit = p_balance
                            p_credit = 0
                        elif p_balance < 0:
                            p_debit = 0
                            p_credit = abs(p_balance)
                        else:
                            p_debit = 0
                            p_credit = 0
                    else:
                        if p_balance > 0:
                            p_debit = 0
                            p_credit = p_balance
                        elif p_balance < 0:
                            p_debit = abs(p_balance)
                            p_credit = 0
                        else:
                            p_debit = 0
                            p_credit = 0
                    
                    parent_debit += p_debit
                    parent_credit += p_credit
                    
                    # Add child accounts
                    for child in child_accounts:
                        c_code, c_name, c_balance = child
                        
                        if acc_type in ['Asset', 'Expense']:
                            if c_balance > 0:
                                c_debit = c_balance
                                c_credit = 0
                            elif c_balance < 0:
                                c_debit = 0
                                c_credit = abs(c_balance)
                            else:
                                c_debit = 0
                                c_credit = 0
                        else:
                            if c_balance > 0:
                                c_debit = 0
                                c_credit = c_balance
                            elif c_balance < 0:
                                c_debit = abs(c_balance)
                                c_credit = 0
                            else:
                                c_debit = 0
                                c_credit = 0
                        
                        parent_debit += c_debit
                        parent_credit += c_credit
                        
                        self.tree.insert(parent_node, tk.END,
                                        text=f"    {c_name}",
                                        values=(
                                            c_code,
                                            f"{CURRENCY_SYMBOL}{c_debit:,.2f}" if c_debit > 0 else "",
                                            f"{CURRENCY_SYMBOL}{c_credit:,.2f}" if c_credit > 0 else ""
                                        ))
                    
                    # Update parent row with its balance
                    self.tree.item(parent_node, values=(
                        p_code,
                        f"{CURRENCY_SYMBOL}{p_debit:,.2f}" if p_debit > 0 else "",
                        f"{CURRENCY_SYMBOL}{p_credit:,.2f}" if p_credit > 0 else ""
                    ))
                    
                    # Add parent total row if there are children
                    if child_accounts:
                        self.tree.insert(parent_node, tk.END,
                                        text=f"    TOTAL {p_name}",
                                        values=(
                                            '',
                                            f"{CURRENCY_SYMBOL}{parent_debit:,.2f}" if parent_debit > 0 else "",
                                            f"{CURRENCY_SYMBOL}{parent_credit:,.2f}" if parent_credit > 0 else ""
                                        ), tags=('subtotal',))
                    
                    type_debit += parent_debit
                    type_credit += parent_credit
                
                # Add type total row
                if type_debit > 0 or type_credit > 0:
                    self.tree.insert(type_node, tk.END,
                                    text=f"  TOTAL {display_name}",
                                    values=(
                                        '',
                                        f"{CURRENCY_SYMBOL}{type_debit:,.2f}" if type_debit > 0 else "",
                                        f"{CURRENCY_SYMBOL}{type_credit:,.2f}" if type_credit > 0 else ""
                                    ), tags=('type_total',))
                    
                    total_debit += type_debit
                    total_credit += type_credit
            
            # Add separator
            self.tree.insert('', tk.END,
                            text="═" * 60,
                            values=('', '', ''),
                            tags=('separator',))
            
            # Add grand total
            self.tree.insert('', tk.END,
                            text="GRAND TOTAL",
                            values=(
                                '',
                                f"{CURRENCY_SYMBOL}{total_debit:,.2f}",
                                f"{CURRENCY_SYMBOL}{total_credit:,.2f}"
                            ), tags=('grand_total',))
            
            # Configure tags
            self.tree.tag_configure('type', background='#d4e6f1', font=('Arial', 11, 'bold'))
            self.tree.tag_configure('parent', font=('Arial', 10, 'bold'))
            self.tree.tag_configure('subtotal', background='#e8f0f7', font=('Arial', 9, 'italic'))
            self.tree.tag_configure('type_total', background='#c9dbe9', font=('Arial', 10, 'bold'))
            self.tree.tag_configure('separator', font=('Courier', 8))
            self.tree.tag_configure('grand_total', background='#2c3e50', foreground='white', font=('Arial', 11, 'bold'))
            
            # Update summary
            self.total_debit.config(text=f"{CURRENCY_SYMBOL}{total_debit:,.2f}")
            self.total_credit.config(text=f"{CURRENCY_SYMBOL}{total_credit:,.2f}")
            
            diff = total_debit - total_credit
            self.difference.config(text=f"{CURRENCY_SYMBOL}{diff:,.2f}")
            
            if diff == 0:
                self.difference.config(fg='#27ae60')
            else:
                self.difference.config(fg='#e74c3c')
            
            # Expand all nodes
            for item in self.tree.get_children():
                self.tree.item(item, open=True)
                for child in self.tree.get_children(item):
                    self.tree.item(child, open=True)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load trial balance: {e}")
        finally:
            conn.close()
    
    def export_csv(self):
        """Export trial balance to CSV"""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Save Trial Balance As"
            )
            
            if not filename:
                return
            
            with open(filename, 'w', newline='', encoding='utf-8') as file:
                file.write(f"TRIAL BALANCE as at {self.as_at_date.get()}\n")
                file.write("\n")
                file.write("Account Name,Account Code,Debit,Credit\n")
                
                def write_tree_data(item, level=0):
                    text = self.tree.item(item)['text']
                    values = self.tree.item(item)['values']
                    indent = "  " * level
                    
                    if not any(tag in self.tree.item(item)['tags'] for tag in ['type', 'separator', 'grand_total']):
                        file.write(f"{indent}{text},{values[0]},{values[1]},{values[2]}\n")
                    
                    for child in self.tree.get_children(item):
                        write_tree_data(child, level + 1)
                
                for item in self.tree.get_children():
                    write_tree_data(item)
            
            messagebox.showinfo("Success", f"Trial Balance exported to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    tb = TrialBalance(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()