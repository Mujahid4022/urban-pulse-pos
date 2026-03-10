# budget_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, show_error, show_success, ask_yes_no

class BudgetManager:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Budget Management")
        self.window.geometry("1000x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"1000x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_budgets()
        self.load_accounts()
        self.load_periods()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#f39c12', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📊 BUDGET MANAGEMENT", fg='white', bg='#f39c12',
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
        
        # Left Panel - Budget List
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=350)
        paned.add(left_frame, width=350, minsize=300)
        
        tk.Label(left_frame, text="📋 BUDGETS", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        # Filter Frame
        filter_frame = tk.Frame(left_frame, bg='#ecf0f1')
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(filter_frame, text="Period:", bg='#ecf0f1').pack(side=tk.LEFT)
        self.period_filter = ttk.Combobox(filter_frame, width=15, font=('Arial', 9))
        self.period_filter.pack(side=tk.LEFT, padx=5)
        self.period_filter.bind('<<ComboboxSelected>>', lambda e: self.load_budgets())
        
        tk.Button(filter_frame, text="🔄", command=self.load_budgets,
                 bg='#3498db', fg='white', font=('Arial', 8),
                 width=2, cursor='hand2').pack(side=tk.RIGHT)
        
        # Treeview for budgets
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        
        columns = ('Account', 'Budget', 'Actual', 'Variance', 'Status')
        self.budget_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        vsb.config(command=self.budget_tree.yview)
        hsb.config(command=self.budget_tree.xview)
        
        col_widths = {'Account': 150, 'Budget': 90, 'Actual': 90, 'Variance': 90, 'Status': 60}
        
        for col in columns:
            self.budget_tree.heading(col, text=col)
            self.budget_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.budget_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.budget_tree.bind('<<TreeviewSelect>>', self.on_budget_select)
        
        # Summary Frame
        summary_frame = tk.Frame(left_frame, bg='white', relief=tk.RIDGE, bd=1)
        summary_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(summary_frame, text="SUMMARY", font=('Arial', 10, 'bold'),
                bg='white').pack(anchor='w', padx=5, pady=2)
        
        self.summary_text = tk.Text(summary_frame, height=4, width=40, font=('Courier', 9),
                                    relief='solid', bd=1, state='disabled')
        self.summary_text.pack(padx=5, pady=5)
        
        # Right Panel - Budget Creation
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=650)
        
        # Create Budget Frame
        create_frame = tk.LabelFrame(right_frame, text="➕ CREATE / EDIT BUDGET", 
                                     font=('Arial', 12, 'bold'), padx=15, pady=10)
        create_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Period
        tk.Label(create_frame, text="Period:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.period_var = tk.StringVar()
        self.period_combo = ttk.Combobox(create_frame, textvariable=self.period_var, width=20, font=('Arial', 10))
        self.period_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Account
        tk.Label(create_frame, text="Account:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(create_frame, textvariable=self.account_var, width=40, font=('Arial', 10))
        self.account_combo.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Budget Amount
        tk.Label(create_frame, text="Budget Amount (Rs.):", font=('Arial', 10)).grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.budget_amount = tk.Entry(create_frame, width=20, font=('Arial', 10), relief='solid', bd=1)
        self.budget_amount.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Notes
        tk.Label(create_frame, text="Notes:", font=('Arial', 10)).grid(row=3, column=0, padx=5, pady=5, sticky='ne')
        self.notes = tk.Text(create_frame, height=3, width=40, font=('Arial', 10), relief='solid', bd=1)
        self.notes.grid(row=3, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons
        btn_frame = tk.Frame(create_frame)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="✅ Save Budget", command=self.save_budget,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=12, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", command=self.clear_form,
                 bg='#95a5a6', fg='white', font=('Arial', 10),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Delete", command=self.delete_budget,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 width=8, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Budget vs Actual Chart Frame
        chart_frame = tk.LabelFrame(right_frame, text="📊 BUDGET VS ACTUAL", 
                                    font=('Arial', 12, 'bold'), padx=15, pady=10)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a simple bar chart representation
        self.chart_canvas = tk.Canvas(chart_frame, bg='white', height=200)
        self.chart_canvas.pack(fill=tk.X, pady=5)
        
        # Legend
        legend_frame = tk.Frame(chart_frame, bg='white')
        legend_frame.pack()
        
        tk.Label(legend_frame, text="🟦 Budget", bg='white', fg='#3498db').pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="🟩 Actual", bg='white', fg='#27ae60').pack(side=tk.LEFT, padx=10)
        tk.Label(legend_frame, text="🟥 Over Budget", bg='white', fg='#e74c3c').pack(side=tk.LEFT, padx=10)
        
        # Alerts Frame
        alert_frame = tk.LabelFrame(right_frame, text="⚠️ BUDGET ALERTS", 
                                    font=('Arial', 12, 'bold'), padx=15, pady=10)
        alert_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.alert_text = tk.Text(alert_frame, height=3, width=60, font=('Arial', 9),
                                  relief='solid', bd=1, state='disabled')
        self.alert_text.pack(fill=tk.X, pady=5)
    
    def load_periods(self):
        """Load available periods"""
        periods = [
            'Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026',
            'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026',
            'Q1 2026', 'Q2 2026', 'Q3 2026', 'Q4 2026',
            'Year 2026'
        ]
        self.period_combo['values'] = periods
        self.period_filter['values'] = ['All'] + periods
        self.period_filter.set('All')
        self.period_combo.set('Mar 2026')
    
    def load_accounts(self):
        """Load expense accounts for budgeting"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT id, account_code, account_name 
                     FROM accounts 
                     WHERE account_type = 'Expense'
                     ORDER BY account_code''')
        accounts = c.fetchall()
        conn.close()
        
        self.accounts = accounts
        account_list = [f"{a[1]} - {a[2]}" for a in accounts]
        self.account_combo['values'] = account_list
    
    def load_budgets(self):
        """Load budgets from database"""
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)
        
        # Create budgets table if not exists
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT,
            account_id INTEGER,
            budget_amount REAL,
            notes TEXT,
            created_date DATE,
            created_by TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            UNIQUE(period, account_id)
        )''')
        
        period_filter = self.period_filter.get()
        
        query = '''SELECT b.id, b.period, a.account_code, a.account_name, 
                          b.budget_amount, b.notes
                   FROM budgets b
                   JOIN accounts a ON b.account_id = a.id'''
        params = []
        
        if period_filter and period_filter != 'All':
            query += " WHERE b.period = ?"
            params.append(period_filter)
        
        query += " ORDER BY b.period, a.account_code"
        
        c.execute(query, params)
        budgets = c.fetchall()
        
        # Get actual expenses for the period
        total_budget = 0
        total_actual = 0
        over_budget_count = 0
        
        for b in budgets:
            budget_id, period, code, name, budget_amt, notes = b
            
            # Get actual expenses for this account in the period
            actual = self.get_actual_expense(period, b[2])
            
            variance = budget_amt - actual
            variance_percent = (variance / budget_amt * 100) if budget_amt > 0 else 0
            
            if variance >= 0:
                status = "✅ On Track"
                status_color = '#27ae60'
            else:
                status = "⚠️ Over"
                status_color = '#e74c3c'
                over_budget_count += 1
            
            total_budget += budget_amt
            total_actual += actual
            
            self.budget_tree.insert('', tk.END, iid=f"BUDGET_{budget_id}", values=(
                f"{code} - {name}",
                f"{CURRENCY_SYMBOL}{budget_amt:,.0f}",
                f"{CURRENCY_SYMBOL}{actual:,.0f}",
                f"{CURRENCY_SYMBOL}{variance:,.0f} ({variance_percent:.0f}%)",
                status
            ), tags=(status_color,))
        
        # Add total row
        total_variance = total_budget - total_actual
        total_variance_percent = (total_variance / total_budget * 100) if total_budget > 0 else 0
        
        self.budget_tree.insert('', tk.END, values=(
            "TOTAL",
            f"{CURRENCY_SYMBOL}{total_budget:,.0f}",
            f"{CURRENCY_SYMBOL}{total_actual:,.0f}",
            f"{CURRENCY_SYMBOL}{total_variance:,.0f} ({total_variance_percent:.0f}%)",
            ""
        ), tags=('total',))
        
        self.budget_tree.tag_configure('total', background='#ecf0f1', font=('Arial', 10, 'bold'))
        
        # Update summary
        summary = f"""Total Budget: {CURRENCY_SYMBOL}{total_budget:,.0f}
Total Actual: {CURRENCY_SYMBOL}{total_actual:,.0f}
Variance: {CURRENCY_SYMBOL}{total_variance:,.0f}
Over Budget Items: {over_budget_count}"""
        
        self.summary_text.config(state='normal')
        self.summary_text.delete('1.0', tk.END)
        self.summary_text.insert('1.0', summary)
        self.summary_text.config(state='disabled')
        
        # Update alerts
        self.update_alerts(over_budget_count)
        
        # Draw chart
        self.draw_budget_chart(budgets)
        
        conn.close()
    
    def get_actual_expense(self, period, account_code):
        """Get actual expense for account in period"""
        # Parse period (e.g., "Mar 2026")
        try:
            month_map = {
                'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
            }
            month_name, year = period.split()
            month = month_map[month_name]
            year = int(year)
            
            start_date = f"{year}-{month:02d}-01"
            if month == 12:
                end_date = f"{year+1}-01-01"
            else:
                end_date = f"{year}-{month+1:02d}-01"
        except:
            # For quarters or years, use simplified approach
            return 0
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT COALESCE(SUM(le.debit), 0)
                     FROM ledger_entries le
                     JOIN accounts a ON le.account_id = a.id
                     WHERE a.account_code LIKE ? || '%'
                     AND le.entry_date >= ? AND le.entry_date < ?''',
                  (account_code[:1], start_date, end_date))
        
        actual = c.fetchone()[0]
        conn.close()
        
        return actual
    
    def draw_budget_chart(self, budgets):
        """Draw simple bar chart of budget vs actual"""
        self.chart_canvas.delete('all')
        
        if not budgets:
            self.chart_canvas.create_text(400, 100, text="No budget data to display",
                                          font=('Arial', 12), fill='#95a5a6')
            return
        
        # Get top 5 budgets for display
        top_budgets = sorted(budgets, key=lambda x: x[4], reverse=True)[:5]
        
        chart_width = 600
        chart_height = 150
        bar_width = 50
        spacing = 30
        start_x = 50
        
        max_amount = max(b[4] for b in top_budgets) * 1.2  # Add 20% headroom
        
        for i, b in enumerate(top_budgets):
            budget_id, period, code, name, budget_amt, notes = b
            actual = self.get_actual_expense(period, code)
            
            x = start_x + i * (bar_width + spacing)
            
            # Budget bar
            budget_height = (budget_amt / max_amount) * chart_height
            self.chart_canvas.create_rectangle(x, chart_height - budget_height,
                                              x + bar_width, chart_height,
                                              fill='#3498db', outline='')
            
            # Actual bar
            actual_height = (actual / max_amount) * chart_height
            actual_color = '#e74c3c' if actual > budget_amt else '#27ae60'
            self.chart_canvas.create_rectangle(x + bar_width//2, chart_height - actual_height,
                                              x + bar_width//2 + bar_width//2, chart_height,
                                              fill=actual_color, outline='')
            
            # Labels
            short_name = code[:10]
            self.chart_canvas.create_text(x + bar_width//2, chart_height + 15,
                                         text=short_name, font=('Arial', 8))
    
    def on_budget_select(self, event):
        """Handle budget selection"""
        selected = self.budget_tree.selection()
        if not selected or selected[0] == 'total':
            return
        
        budget_id = int(selected[0].replace('BUDGET_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT period, account_id, budget_amount, notes
                     FROM budgets WHERE id=?''', (budget_id,))
        budget = c.fetchone()
        
        if budget:
            period, account_id, amount, notes = budget
            
            # Get account name
            c.execute("SELECT account_code, account_name FROM accounts WHERE id=?", (account_id,))
            code, name = c.fetchone()
            
            self.period_combo.set(period)
            self.account_combo.set(f"{code} - {name}")
            self.budget_amount.delete(0, tk.END)
            self.budget_amount.insert(0, str(int(amount)))
            self.notes.delete('1.0', tk.END)
            self.notes.insert('1.0', notes or '')
        
        conn.close()
    
    def save_budget(self):
        """Save budget to database"""
        period = self.period_combo.get()
        account_sel = self.account_combo.get()
        amount_str = self.budget_amount.get().strip()
        notes = self.notes.get('1.0', tk.END).strip()
        
        if not period or not account_sel or not amount_str:
            show_error("Please fill all required fields")
            return
        
        try:
            amount = float(amount_str)
        except ValueError:
            show_error("Invalid budget amount")
            return
        
        # Find account ID
        account_id = None
        for acc in self.accounts:
            if f"{acc[1]} - {acc[2]}" == account_sel:
                account_id = acc[0]
                break
        
        if not account_id:
            show_error("Invalid account selection")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        try:
            # Check if budget exists for this period and account
            c.execute("SELECT id FROM budgets WHERE period=? AND account_id=?", (period, account_id))
            existing = c.fetchone()
            
            if existing:
                # Update
                c.execute('''UPDATE budgets 
                             SET budget_amount=?, notes=?
                             WHERE id=?''', (amount, notes, existing[0]))
                show_success("Budget updated successfully!")
            else:
                # Insert
                c.execute('''INSERT INTO budgets 
                             (period, account_id, budget_amount, notes, created_date, created_by)
                             VALUES (?,?,?,?,?,?)''',
                          (period, account_id, amount, notes, self.working_date, self.username))
                show_success("Budget created successfully!")
            
            conn.commit()
            self.clear_form()
            self.load_budgets()
            
        except Exception as e:
            show_error(f"Error saving budget: {e}")
        finally:
            conn.close()
    
    def delete_budget(self):
        """Delete selected budget"""
        selected = self.budget_tree.selection()
        if not selected or selected[0] == 'total':
            show_error("Select a budget to delete")
            return
        
        budget_id = int(selected[0].replace('BUDGET_', ''))
        
        if ask_yes_no("Delete this budget?"):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("DELETE FROM budgets WHERE id=?", (budget_id,))
            conn.commit()
            conn.close()
            
            show_success("Budget deleted")
            self.clear_form()
            self.load_budgets()
    
    def clear_form(self):
        """Clear the form"""
        self.period_combo.set('Mar 2026')
        self.account_combo.set('')
        self.budget_amount.delete(0, tk.END)
        self.notes.delete('1.0', tk.END)
    
    def update_alerts(self, over_count):
        """Update budget alerts"""
        self.alert_text.config(state='normal')
        self.alert_text.delete('1.0', tk.END)
        
        if over_count > 0:
            self.alert_text.insert('1.0', f"⚠️ {over_count} budget item(s) are over budget!\n")
            self.alert_text.insert('end', "Review and take corrective action.")
            self.alert_text.config(fg='#e74c3c')
        else:
            self.alert_text.insert('1.0', "✅ All budgets are on track.")
            self.alert_text.config(fg='#27ae60')
        
        self.alert_text.config(state='disabled')

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    bm = BudgetManager(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()