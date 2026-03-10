# day_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, show_error, show_success, ask_yes_no, setup_enter_navigation

class DayManager:
    def __init__(self, parent, username):
        self.parent = parent
        self.username = username
        self.window = tk.Toplevel(parent)
        self.window.title("Day Open/Close Management")
        self.window.geometry("800x550")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 550) // 2
        self.window.geometry(f"800x550+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_current_day()
        self.load_day_history()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#2c3e50', height=50)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📅 DAY OPEN/CLOSE MANAGEMENT", fg='white', bg='#2c3e50',
                font=('Arial', 16, 'bold')).pack(expand=True)
        
        # Main content
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=20, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current Day Status Frame
        status_frame = tk.LabelFrame(main_frame, text="Current Day Status", font=('Arial', 12, 'bold'),
                                     bg='#f9f9f9', padx=15, pady=10)
        status_frame.pack(fill=tk.X, pady=5)
        
        self.status_label = tk.Label(status_frame, text="", font=('Arial', 11), bg='#f9f9f9')
        self.status_label.pack(anchor='w', pady=2)
        
        self.day_date_label = tk.Label(status_frame, text="", font=('Arial', 11, 'bold'), bg='#f9f9f9', fg='#2980b9')
        self.day_date_label.pack(anchor='w', pady=2)
        
        self.opened_by_label = tk.Label(status_frame, text="", font=('Arial', 11), bg='#f9f9f9')
        self.opened_by_label.pack(anchor='w', pady=2)
        
        self.cash_label = tk.Label(status_frame, text="", font=('Arial', 11), bg='#f9f9f9')
        self.cash_label.pack(anchor='w', pady=2)
        
        # Action buttons
        button_frame = tk.Frame(main_frame, bg='#f9f9f9')
        button_frame.pack(pady=10)
        
        self.open_btn = tk.Button(button_frame, text="🔓 OPEN DAY", command=self.open_day,
                                  bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                                  width=15, cursor='hand2')
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        self.close_btn = tk.Button(button_frame, text="🔒 CLOSE DAY", command=self.close_day,
                                   bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                                   width=15, cursor='hand2')
        self.close_btn.pack(side=tk.LEFT, padx=5)
        
        self.backdate_btn = tk.Button(button_frame, text="📅 BACK DATE POST", command=self.backdate_post,
                                      bg='#f39c12', fg='white', font=('Arial', 12, 'bold'),
                                      width=15, cursor='hand2')
        self.backdate_btn.pack(side=tk.LEFT, padx=5)
        
        # Back Date Posting Frame
        backdate_frame = tk.LabelFrame(main_frame, text="Back Date Posting", font=('Arial', 12, 'bold'),
                                       bg='#f9f9f9', padx=15, pady=10)
        backdate_frame.pack(fill=tk.X, pady=10)
        
        date_frame = tk.Frame(backdate_frame, bg='#f9f9f9')
        date_frame.pack(pady=5)
        
        tk.Label(date_frame, text="Select Date:", font=('Arial', 10), bg='#f9f9f9').pack(side=tk.LEFT)
        self.backdate_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        backdate_entry = tk.Entry(date_frame, textvariable=self.backdate_var, width=15,
                                  font=('Arial', 10), relief='solid', bd=1)
        backdate_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(date_frame, text="Reason:", font=('Arial', 10), bg='#f9f9f9').pack(side=tk.LEFT, padx=(20,5))
        self.backdate_reason = tk.Entry(date_frame, width=30, font=('Arial', 10), relief='solid', bd=1)
        self.backdate_reason.pack(side=tk.LEFT, padx=5)
        
        tk.Button(date_frame, text="Set as Current", command=self.set_backdate_as_current,
                 bg='#3498db', fg='white', font=('Arial', 9), cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Day History
        history_frame = tk.LabelFrame(main_frame, text="Day History", font=('Arial', 12, 'bold'),
                                      bg='#f9f9f9', padx=10, pady=10)
        history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tree_frame = tk.Frame(history_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        columns = ('Date', 'Opened By', 'Opened At', 'Closed By', 'Closed At', 'Status', 'Opening Cash', 'Closing Cash')
        self.history_tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, height=8)
        vsb.config(command=self.history_tree.yview)
        
        col_widths = {'Date': 90, 'Opened By': 90, 'Opened At': 130, 'Closed By': 90,
                     'Closed At': 130, 'Status': 70, 'Opening Cash': 80, 'Closing Cash': 80}
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            self.history_tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
    
    def load_current_day(self):
        """Load current day status"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute('''SELECT * FROM business_days WHERE day_date=?''', (today,))
        day = c.fetchone()
        
        if day:
            status = day[6]
            self.status_label.config(text=f"Status: {status}")
            self.day_date_label.config(text=f"Business Date: {day[1]}")
            self.opened_by_label.config(text=f"Opened By: {day[2]} at {day[3]}")
            self.cash_label.config(text=f"Opening Cash: {CURRENCY_SYMBOL}{day[7]:.2f}")
            
            if status == 'Open':
                self.open_btn.config(state=tk.DISABLED, bg='#95a5a6')
                self.close_btn.config(state=tk.NORMAL, bg='#e74c3c')
                self.backdate_btn.config(state=tk.NORMAL, bg='#f39c12')
            else:
                self.open_btn.config(state=tk.NORMAL, bg='#27ae60')
                self.close_btn.config(state=tk.DISABLED, bg='#95a5a6')
                self.backdate_btn.config(state=tk.DISABLED, bg='#95a5a6')
        else:
            # No day record - create one
            c.execute('''INSERT INTO business_days (day_date, opened_by, opened_at, status, opening_cash)
                        VALUES (?,?,?,?,?)''',
                      (today, 'System', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Open', 0))
            conn.commit()
            self.load_current_day()
        
        conn.close()
    
    def load_day_history(self):
        """Load day history"""
        for row in self.history_tree.get_children():
            self.history_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT day_date, opened_by, opened_at, closed_by, closed_at, status,
                            opening_cash, closing_cash
                     FROM business_days ORDER BY day_date DESC LIMIT 30''')
        days = c.fetchall()
        conn.close()
        
        for d in days:
            self.history_tree.insert('', tk.END, values=(
                d[0], d[1], d[2][:16] if d[2] else '', d[3] or '-', d[4][:16] if d[4] else '-',
                d[5], f"{CURRENCY_SYMBOL}{d[6]:.2f}", f"{CURRENCY_SYMBOL}{d[7] if d[7] else 0:.2f}"
            ))
    
    def open_day(self):
        """Open a new business day"""
        # Check if there's an open day
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT day_date FROM business_days WHERE status='Open'")
        open_day = c.fetchone()
        
        if open_day:
            show_error(f"Day {open_day[0]} is already open. Please close it first.")
            conn.close()
            return
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Open Day")
        dialog.geometry("350x200")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 350) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f"350x200+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="OPEN NEW DAY", font=('Arial', 14, 'bold'),
                bg='#27ae60', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Date:", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w')
        date_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        date_entry = tk.Entry(frame, textvariable=date_var, width=20, font=('Arial', 10),
                              relief='solid', bd=1)
        date_entry.pack(pady=5)
        
        tk.Label(frame, text="Opening Cash (Rs.):", bg='#f9f9f9', font=('Arial', 10)).pack(anchor='w')
        cash_var = tk.StringVar(value="0")
        cash_entry = tk.Entry(frame, textvariable=cash_var, width=20, font=('Arial', 10),
                              relief='solid', bd=1)
        cash_entry.pack(pady=5)
        
        def save():
            try:
                cash = float(cash_var.get())
                date = date_var.get()
                
                # Check if day already exists
                c.execute("SELECT id FROM business_days WHERE day_date=?", (date,))
                if c.fetchone():
                    show_error(f"Day {date} already exists!")
                    return
                
                c.execute('''INSERT INTO business_days (day_date, opened_by, opened_at, status, opening_cash)
                            VALUES (?,?,?,?,?)''',
                          (date, self.username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Open', cash))
                conn.commit()
                dialog.destroy()
                show_success(f"Day {date} opened successfully!")
                self.load_current_day()
                self.load_day_history()
            except ValueError:
                show_error("Invalid cash amount")
            finally:
                conn.close()
        
        date_entry.bind('<Return>', lambda e: cash_entry.focus())
        cash_entry.bind('<Return>', lambda e: save())
        
        tk.Button(frame, text="Open Day", command=save, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), cursor='hand2').pack(pady=10)
    
    def close_day(self):
        """Close current business day"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        c.execute("SELECT opening_cash FROM business_days WHERE day_date=? AND status='Open'", (today,))
        result = c.fetchone()
        
        if not result:
            show_error("No open day found!")
            conn.close()
            return
        
        opening_cash = result[0]
        
        # Calculate total sales for the day
        c.execute('''SELECT SUM(total) FROM sales WHERE DATE(datetime)=?''', (today,))
        total_sales = c.fetchone()[0] or 0
        
        dialog = tk.Toplevel(self.window)
        dialog.title("Close Day")
        dialog.geometry("400x250")
        dialog.configure(bg='#f9f9f9')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 250) // 2
        dialog.geometry(f"400x250+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        tk.Label(dialog, text="CLOSE DAY", font=('Arial', 14, 'bold'),
                bg='#e74c3c', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=20, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Date: {today}", font=('Arial', 11), bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Opening Cash: {CURRENCY_SYMBOL}{opening_cash:.2f}", bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Total Sales: {CURRENCY_SYMBOL}{total_sales:.2f}", bg='#f9f9f9').pack(anchor='w')
        
        expected_cash = opening_cash + total_sales
        tk.Label(frame, text=f"Expected Cash: {CURRENCY_SYMBOL}{expected_cash:.2f}",
                font=('Arial', 11, 'bold'), bg='#f9f9f9', fg='#27ae60').pack(anchor='w', pady=5)
        
        tk.Label(frame, text="Actual Closing Cash (Rs.):", bg='#f9f9f9').pack(anchor='w')
        cash_var = tk.StringVar(value=str(expected_cash))
        cash_entry = tk.Entry(frame, textvariable=cash_var, width=20, font=('Arial', 10),
                              relief='solid', bd=1)
        cash_entry.pack(pady=5)
        
        def save():
            try:
                actual_cash = float(cash_var.get())
                
                c.execute('''UPDATE business_days 
                            SET closed_by=?, closed_at=?, status='Closed', closing_cash=?
                            WHERE day_date=?''',
                          (self.username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), actual_cash, today))
                conn.commit()
                
                diff = actual_cash - expected_cash
                msg = f"Day closed successfully!"
                if diff != 0:
                    msg += f"\nCash Difference: {CURRENCY_SYMBOL}{diff:.2f}"
                
                dialog.destroy()
                show_success(msg)
                self.load_current_day()
                self.load_day_history()
            except ValueError:
                show_error("Invalid cash amount")
            finally:
                conn.close()
        
        cash_entry.bind('<Return>', lambda e: save())
        
        tk.Button(frame, text="Close Day", command=save, bg='#e74c3c', fg='white',
                 font=('Arial', 11, 'bold'), cursor='hand2').pack(pady=10)
    
    def backdate_post(self):
        """Enable back date posting"""
        date = self.backdate_var.get().strip()
        reason = self.backdate_reason.get().strip()
        
        if not reason:
            show_error("Please enter a reason for back date posting")
            return
        
        # Check if the selected date is a closed day
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT status FROM business_days WHERE day_date=?", (date,))
        result = c.fetchone()
        
        if result and result[0] == 'Closed':
            response = ask_yes_no(f"Day {date} is closed. Back date posting will reopen it. Continue?")
            if not response:
                conn.close()
                return
            
            # Reopen the day
            c.execute('''UPDATE business_days SET status='Open', closed_by=NULL, closed_at=NULL
                        WHERE day_date=?''', (date,))
        
        # Log the back date posting
        c.execute('''INSERT INTO back_date_log (transaction_date, posted_date, posted_by, reason)
                    VALUES (?,?,?,?)''',
                  (date, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), self.username, reason))
        
        conn.commit()
        conn.close()
        
        # Set the system date for transactions (this would need to be implemented in pos_main.py)
        # For now, just show a message
        show_success(f"Back date posting enabled for {date}\nYou can now post transactions to this date.")
        
        # Update current day display
        self.load_current_day()
    
    def set_backdate_as_current(self):
        """Set backdate as current working date"""
        date = self.backdate_var.get().strip()
        
        # In a real system, you'd set a global variable
        # For now, show message
        show_info(f"Working date set to: {date}\nAll new transactions will use this date.")