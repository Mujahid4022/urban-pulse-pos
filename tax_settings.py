# tax_settings.py
import tkinter as tk
from tkinter import ttk
import sqlite3
from utils import show_success, show_error

class TaxSettings:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Tax Rate Settings")
        self.window.geometry("400x350")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 400) // 2
        y = (self.window.winfo_screenheight() - 350) // 2
        self.window.geometry(f"400x350+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_current_tax()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="⚙️ TAX RATE SETTINGS", fg='white', bg='#3498db',
                font=('Arial', 14, 'bold')).pack(expand=True)
        
        # Main frame
        main_frame = tk.Frame(self.window, bg='#f9f9f9', padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Current tax display
        current_frame = tk.Frame(main_frame, bg='#ecf0f1', relief='groove', bd=2)
        current_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(current_frame, text="CURRENT TAX RATE:", bg='#ecf0f1',
                font=('Arial', 11, 'bold')).pack(pady=5)
        self.current_tax_label = tk.Label(current_frame, text="0%", bg='#ecf0f1',
                                          font=('Arial', 16, 'bold'), fg='#27ae60')
        self.current_tax_label.pack(pady=5)
        
        # New tax input
        input_frame = tk.Frame(main_frame, bg='#f9f9f9')
        input_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(input_frame, text="New Tax Rate (%):", bg='#f9f9f9',
                font=('Arial', 11)).pack(anchor='w')
        
        self.tax_var = tk.StringVar()
        self.tax_entry = tk.Entry(input_frame, textvariable=self.tax_var,
                                  font=('Arial', 14), width=10, justify='center',
                                  relief='solid', bd=2)
        self.tax_entry.pack(pady=5)
        self.tax_entry.focus()
        
        # Note
        tk.Label(input_frame, text="This will affect all POS sales and Purchase Orders",
                bg='#f9f9f9', font=('Arial', 9), fg='#7f8c8d').pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg='#f9f9f9')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save", command=self.save_tax_rate,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=self.window.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def load_current_tax(self):
        """Load current tax rate from database"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Create settings table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS settings 
                     (key TEXT PRIMARY KEY, value TEXT)''')
        
        # Get tax rate
        c.execute("SELECT value FROM settings WHERE key='tax_rate'")
        result = c.fetchone()
        
        if result:
            tax_rate = result[0]
        else:
            # Default to 17% if not set
            tax_rate = "17"
            c.execute("INSERT INTO settings (key, value) VALUES ('tax_rate', ?)", (tax_rate,))
            conn.commit()
        
        conn.close()
        
        self.current_tax_label.config(text=f"{tax_rate}%")
        self.tax_var.set(tax_rate)
    
    def save_tax_rate(self):
        """Save new tax rate to database"""
        try:
            new_rate = float(self.tax_var.get())
            if new_rate < 0 or new_rate > 100:
                show_error("Tax rate must be between 0 and 100")
                return
        except ValueError:
            show_error("Please enter a valid number")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Update or insert
        c.execute('''INSERT OR REPLACE INTO settings (key, value) 
                     VALUES ('tax_rate', ?)''', (str(int(new_rate) if new_rate.is_integer() else new_rate),))
        conn.commit()
        conn.close()
        
        show_success(f"Tax rate updated to {new_rate}%")
        self.current_tax_label.config(text=f"{new_rate}%")