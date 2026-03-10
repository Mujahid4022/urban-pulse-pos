# dashboard.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL
import os
import sys

class Dashboard:
    def __init__(self, user):
        self.user = user
        self.root = tk.Tk()
        self.root.title(f"Urban Pulse POS - Dashboard")
        self.root.geometry("1200x700")
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1200) // 2
        y = (self.root.winfo_screenheight() - 700) // 2
        self.root.geometry(f"1200x700+{x}+{y}")
        
        self.root.lift()
        self.root.focus_force()
        
        # Colors
        self.bg_color = '#f0f2f5'
        self.header_color = '#2c3e50'
        self.sidebar_color = '#34495e'
        self.accent_color = '#3498db'
        
        self.create_widgets()
        self.load_dashboard_data()
        self.root.mainloop()
    
    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # ========== TOP HEADER ==========
        header = tk.Frame(main_container, bg=self.header_color, height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Logo and title
        tk.Label(header, text="🏪 Urban Pulse POS", fg='white', bg=self.header_color,
                font=('Arial', 18, 'bold')).pack(side=tk.LEFT, padx=20)
        
        # Date display
        date_label = tk.Label(header, text=f"📅 {datetime.now().strftime('%Y-%m-%d')}",
                              fg='white', bg=self.header_color, font=('Arial', 12))
        date_label.pack(side=tk.LEFT, expand=True, anchor='center')
        
        # User info and alerts
        right_frame = tk.Frame(header, bg=self.header_color)
        right_frame.pack(side=tk.RIGHT, padx=20)
        
        # Alert button
        self.alert_btn = tk.Button(right_frame, text="🔔 Alerts", bg='#e74c3c', fg='white',
                                   font=('Arial', 10), cursor='hand2',
                                   command=self.show_alerts)
        self.alert_btn.pack(side=tk.LEFT, padx=5)
        
        # User menu
        tk.Label(right_frame, text=f"👤 {self.user['username']} ({self.user['role']})",
                fg='white', bg=self.header_color, font=('Arial', 11)).pack(side=tk.LEFT, padx=10)
        
        # Logout button
        tk.Button(right_frame, text="🚪", bg='#e74c3c', fg='white',
                 font=('Arial', 10), width=2, cursor='hand2',
                 command=self.logout).pack(side=tk.LEFT)
        
        # ========== MAIN CONTENT ==========
        content_frame = tk.Frame(main_container, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ========== QUICK STATS ROW ==========
        stats_frame = tk.Frame(content_frame, bg=self.bg_color)
        stats_frame.pack(fill=tk.X, pady=5)
        
        # Today's Sales
        self.create_stat_card(stats_frame, "💰 TODAY'S SALES", "Rs. 0", 0, 0)
        
        # Today's Transactions
        self.create_stat_card(stats_frame, "📊 TRANSACTIONS", "0", 1, 0)
        
        # Low Stock Items
        self.low_stock_card = self.create_stat_card(stats_frame, "⚠️ LOW STOCK", "0", 2, 0, '#e74c3c')
        
        # Inventory Value
        self.create_stat_card(stats_frame, "📦 INVENTORY VALUE", "Rs. 0", 3, 0)
        
        # ========== QUICK ACTIONS ==========
        actions_frame = tk.Frame(content_frame, bg='white', relief=tk.RIDGE, bd=1)
        actions_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(actions_frame, text="⚡ QUICK ACTIONS", font=('Arial', 12, 'bold'),
                bg='white', fg=self.header_color).pack(anchor='w', padx=10, pady=5)
        
        actions_grid = tk.Frame(actions_frame, bg='white')
        actions_grid.pack(pady=10)
        
        # Action buttons
        actions = [
            ("🛒 New Sale", self.open_pos, '#27ae60'),
            ("👤 Add Member", self.open_add_member, '#3498db'),
            ("📦 New Purchase", self.open_purchase_order, '#f39c12'),
            ("📊 Reports", self.open_reports, '#9b59b6'),
            ("📋 Inventory", self.open_inventory, '#1abc9c'),
            ("💰 Accounting", self.open_accounting, '#e74c3c'),
        ]
        
        for i, (text, cmd, color) in enumerate(actions):
            row = i // 3
            col = i % 3
            btn = tk.Button(actions_grid, text=text, command=cmd, bg=color, fg='white',
                           font=('Arial', 11, 'bold'), width=18, height=2,
                           cursor='hand2', relief=tk.RAISED, bd=2)
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # ========== MAIN MENU ==========
        menu_frame = tk.Frame(content_frame, bg='white', relief=tk.RIDGE, bd=1)
        menu_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(menu_frame, text="📋 MAIN MENU", font=('Arial', 12, 'bold'),
                bg='white', fg=self.header_color).pack(anchor='w', padx=10, pady=5)
        
        menu_grid = tk.Frame(menu_frame, bg='white')
        menu_grid.pack(pady=10)
        
        # Menu buttons
        menu_items = [
            ("🏪 POS", self.open_pos, '#3498db'),
            ("👥 Members", self.open_members, '#9b59b6'),
            ("📦 Suppliers", self.open_suppliers, '#1abc9c'),
            ("📋 Products", self.open_products, '#f39c12'),
            ("📊 Inventory", self.open_inventory, '#e74c3c'),
            ("💰 Accounting", self.open_accounting, '#27ae60'),
            ("📑 Reports", self.open_reports, '#2980b9'),
            ("⚙️ Settings", self.open_settings, '#7f8c8d'),
        ]
        
        for i, (text, cmd, color) in enumerate(menu_items):
            row = i // 4
            col = i % 4
            btn = tk.Button(menu_grid, text=text, command=cmd, bg=color, fg='white',
                           font=('Arial', 11, 'bold'), width=15, height=1,
                           cursor='hand2', relief=tk.RAISED, bd=2)
            btn.grid(row=row, column=col, padx=5, pady=5)
        
        # ========== RECENT ACTIVITY ==========
        activity_frame = tk.Frame(content_frame, bg='white', relief=tk.RIDGE, bd=1)
        activity_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        tk.Label(activity_frame, text="🕒 RECENT ACTIVITY", font=('Arial', 12, 'bold'),
                bg='white', fg=self.header_color).pack(anchor='w', padx=10, pady=5)
        
        # Activity list
        self.activity_listbox = tk.Listbox(activity_frame, height=6, font=('Arial', 10),
                                          relief='solid', bd=1)
        self.activity_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Add some sample activities
        self.activity_listbox.insert(tk.END, "📅 Welcome back! Dashboard loaded successfully")
        self.activity_listbox.insert(tk.END, "ℹ️ Click any menu item to get started")
    
    def create_stat_card(self, parent, title, value, row, col, color=None):
        """Create a statistics card"""
        if color is None:
            color = self.accent_color
        
        card = tk.Frame(parent, bg=color, width=250, height=80, relief=tk.RIDGE, bd=2)
        card.grid(row=row, column=col, padx=5, pady=5)
        card.pack_propagate(False)
        
        tk.Label(card, text=title, fg='white', bg=color,
                font=('Arial', 10)).pack(anchor='w', padx=10, pady=2)
        
        value_label = tk.Label(card, text=value, fg='white', bg=color,
                              font=('Arial', 16, 'bold'))
        value_label.pack(anchor='e', padx=10, pady=5)
        
        return value_label
    
    def load_dashboard_data(self):
        """Load real data into dashboard"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            # Today's sales
            today = datetime.now().strftime('%Y-%m-%d')
            c.execute('''SELECT COALESCE(SUM(total_amount), 0) FROM vouchers 
                         WHERE voucher_type IN ('Sale', 'Receipt') 
                         AND voucher_date=?''', (today,))
            sales = c.fetchone()[0]
            
            # Update sales card (assuming you stored the label reference)
            # This is simplified - you'd need to store references to all stat labels
            
            # Low stock count
            c.execute('''SELECT COUNT(*) FROM products 
                         WHERE stock <= reorder_level AND stock > 0''')
            low_stock = c.fetchone()[0]
            
            # Update low stock card
            if hasattr(self, 'low_stock_card'):
                self.low_stock_card.config(text=str(low_stock))
            
            # Inventory value
            c.execute('''SELECT COALESCE(SUM(cost_price * stock), 0) FROM products''')
            inv_value = c.fetchone()[0]
            
            conn.close()
            
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
    
    def show_alerts(self):
        """Show alerts popup"""
        alerts = []
        
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            # Low stock alerts
            c.execute('''SELECT name, stock, reorder_level FROM products 
                         WHERE stock <= reorder_level''')
            low_stock = c.fetchall()
            
            for item in low_stock:
                alerts.append(f"⚠️ Low Stock: {item[0]} - {item[1]} left (min: {item[2]})")
            
            # Overdue credit payments
            c.execute('''SELECT m.name, cs.due_amount FROM credit_sales cs
                         JOIN members m ON cs.member_id = m.id
                         WHERE cs.due_date < date('now') AND cs.status != 'Paid' ''')
            overdue = c.fetchall()
            
            for item in overdue:
                alerts.append(f"⚠️ Overdue Payment: {item[0]} - Rs.{item[1]:.2f}")
            
            conn.close()
            
        except Exception as e:
            print(f"Error loading alerts: {e}")
        
        if alerts:
            messagebox.showinfo("Alerts", "\n\n".join(alerts))
        else:
            messagebox.showinfo("Alerts", "No alerts at this time.")
    
    # ========== NAVIGATION METHODS ==========
    
    def open_pos(self):
        """Open POS screen"""
        self.root.destroy()
        from pos_main import UrbanPulsePOS
        app = UrbanPulsePOS(self.user)
    
    def open_members(self):
        """Open Membership Manager"""
        try:
            from membership_manager import MembershipManager
            MembershipManager(self.root, working_date=datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Members: {e}")
    
    def open_suppliers(self):
        """Open Supplier Manager"""
        try:
            from supplier_manager import SupplierManager
            SupplierManager(self.root, working_date=datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Suppliers: {e}")
    
    def open_products(self):
        """Open Product Manager"""
        try:
            from product_manager import ProductManager
            ProductManager(self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Products: {e}")
    
    def open_inventory(self):
        """Open Inventory Menu"""
        # This will be implemented later
        messagebox.showinfo("Coming Soon", "Inventory Management coming soon!")
    
    def open_accounting(self):
        """Open Accounting Menu"""
        try:
            from accounting_menu import AccountingMenu
            AccountingMenu(self.root, self.user['username'], 
                          datetime.now().strftime('%Y-%m-%d'))
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Accounting: {e}")
    
    def open_reports(self):
        """Open Reports Menu"""
        # This will be implemented later
        messagebox.showinfo("Coming Soon", "Reports coming soon!")
    
    def open_settings(self):
        """Open Settings"""
        messagebox.showinfo("Settings", "Settings coming soon!")
    
    def open_add_member(self):
        """Quick add member"""
        try:
            from membership_manager import MembershipManager
            # This would ideally open the Add Member tab directly
            mm = MembershipManager(self.root, working_date=datetime.now().strftime('%Y-%m-%d'))
            # Switch to add tab logic would go here
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Add Member: {e}")
    
    def open_purchase_order(self):
        """Create new purchase order"""
        try:
            from supplier_manager import SupplierManager
            sm = SupplierManager(self.root, working_date=datetime.now().strftime('%Y-%m-%d'))
            # Switch to PO tab logic would go here
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Purchase Order: {e}")
    
    def logout(self):
        """Logout and return to login"""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.destroy()
            from login import LoginWindow
            login = LoginWindow()

# For testing
if __name__ == "__main__":
    test_user = {'username': 'admin', 'role': 'admin', 'id': 1}
    app = Dashboard(test_user)