# discount_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation

class DiscountManager:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Discounts & Promotions Manager")
        self.window.geometry("900x600")
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 900) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"900x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_promotions()
    
    def create_widgets(self):
        # Notebook for tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Active Promotions
        self.promotions_tab = tk.Frame(notebook)
        notebook.add(self.promotions_tab, text="Active Promotions")
        self.create_promotions_tab()
        
        # Tab 2: Product Discounts
        self.product_discounts_tab = tk.Frame(notebook)
        notebook.add(self.product_discounts_tab, text="Product Discounts")
        self.create_product_discounts_tab()
        
        # Tab 3: Create Promotion
        self.create_tab = tk.Frame(notebook)
        notebook.add(self.create_tab, text="Create Promotion")
        self.create_promotion_tab()
        
        # Tab 4: BOGO Offers
        self.bogo_tab = tk.Frame(notebook)
        notebook.add(self.bogo_tab, text="BOGO Offers")
        self.create_bogo_tab()
    
    def create_promotions_tab(self):
        # Treeview for promotions
        columns = ('ID', 'Name', 'Type', 'Value', 'Min Purchase', 'Start Date', 'End Date', 'Status')
        self.promo_tree = ttk.Treeview(self.promotions_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'ID': 40, 'Name': 150, 'Type': 100, 'Value': 80, 'Min Purchase': 100, 
                     'Start Date': 90, 'End Date': 90, 'Status': 80}
        
        for col in columns:
            self.promo_tree.heading(col, text=col)
            self.promo_tree.column(col, width=col_widths.get(col, 80))
        
        self.promo_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.promotions_tab)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Activate", command=self.activate_promotion, 
                 bg='green', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Deactivate", command=self.deactivate_promotion, 
                 bg='orange', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_promotion, 
                 bg='red', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_promotions).pack(side=tk.LEFT, padx=5)
    
    def create_product_discounts_tab(self):
        # Search frame
        search_frame = tk.Frame(self.product_discounts_tab)
        search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(search_frame, text="Search Product:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_product_discounts())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        # Treeview for product discounts
        columns = ('ID', 'Barcode', 'Product', 'Price', 'Discount %', 'Start Date', 'End Date', 'BOGO')
        self.prod_discount_tree = ttk.Treeview(self.product_discounts_tab, columns=columns, show='headings', height=15)
        
        col_widths = {'ID': 40, 'Barcode': 100, 'Product': 180, 'Price': 70, 
                     'Discount %': 70, 'Start Date': 90, 'End Date': 90, 'BOGO': 50}
        
        for col in columns:
            self.prod_discount_tree.heading(col, text=col)
            self.prod_discount_tree.column(col, width=col_widths.get(col, 70))
        
        self.prod_discount_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Buttons
        btn_frame = tk.Frame(self.product_discounts_tab)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Set Discount", command=self.set_product_discount, 
                 bg='blue', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear Discount", command=self.clear_product_discount, 
                 bg='orange', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Set BOGO", command=self.set_bogo, 
                 bg='purple', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_product_discounts).pack(side=tk.LEFT, padx=5)
    
    def create_promotion_tab(self):
        # Create form
        form_frame = tk.Frame(self.create_tab)
        form_frame.pack(pady=20)
        
        # Promotion name
        tk.Label(form_frame, text="Promotion Name:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.promo_name = tk.Entry(form_frame, width=30)
        self.promo_name.grid(row=0, column=1, padx=5, pady=5)
        
        # Promotion type
        tk.Label(form_frame, text="Promotion Type:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.promo_type = ttk.Combobox(form_frame, values=['percent', 'fixed', 'bogo'], width=27)
        self.promo_type.grid(row=1, column=1, padx=5, pady=5)
        self.promo_type.set('percent')
        
        # Value
        tk.Label(form_frame, text="Value:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.promo_value = tk.Entry(form_frame, width=30)
        self.promo_value.grid(row=2, column=1, padx=5, pady=5)
        
        # Minimum purchase
        tk.Label(form_frame, text="Minimum Purchase:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.promo_min = tk.Entry(form_frame, width=30)
        self.promo_min.grid(row=3, column=1, padx=5, pady=5)
        self.promo_min.insert(0, "0")
        
        # Start date
        tk.Label(form_frame, text="Start Date (YYYY-MM-DD):").grid(row=4, column=0, padx=5, pady=5, sticky='e')
        self.promo_start = tk.Entry(form_frame, width=30)
        self.promo_start.grid(row=4, column=1, padx=5, pady=5)
        self.promo_start.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        # End date
        tk.Label(form_frame, text="End Date (YYYY-MM-DD):").grid(row=5, column=0, padx=5, pady=5, sticky='e')
        self.promo_end = tk.Entry(form_frame, width=30)
        self.promo_end.grid(row=5, column=1, padx=5, pady=5)
        self.promo_end.insert(0, (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        
        # Product (optional)
        tk.Label(form_frame, text="Product ID (optional):").grid(row=6, column=0, padx=5, pady=5, sticky='e')
        self.promo_product = tk.Entry(form_frame, width=30)
        self.promo_product.grid(row=6, column=1, padx=5, pady=5)
        
        # Setup Enter key navigation
        entries = [
            self.promo_name, self.promo_type, self.promo_value, 
            self.promo_min, self.promo_start, self.promo_end, self.promo_product
        ]
        for i in range(len(entries)-1):
            setup_enter_navigation(entries[i], entries[i+1])
        setup_enter_navigation(entries[-1], self.create_promotion)
        
        # Create button
        tk.Button(self.create_tab, text="Create Promotion", command=self.create_promotion, 
                 bg='green', fg='white', font=('Arial', 12)).pack(pady=20)
    
    def create_bogo_tab(self):
        tk.Label(self.bogo_tab, text="Buy One Get One Offers", font=('Arial', 14)).pack(pady=10)
        
        info_text = """
        BOGO (Buy One Get One) Rules:
        • Select a product to mark as BOGO
        • Customer buys one, gets one free
        • Can be combined with other discounts
        • Automatically applied at checkout
        """
        tk.Label(self.bogo_tab, text=info_text, justify=tk.LEFT).pack(pady=10)
        
        # Product selection
        select_frame = tk.Frame(self.bogo_tab)
        select_frame.pack(pady=10)
        
        tk.Label(select_frame, text="Select Product:").pack(side=tk.LEFT)
        self.bogo_product = ttk.Combobox(select_frame, width=40)
        self.bogo_product.pack(side=tk.LEFT, padx=5)
        
        # Load products
        self.load_products_for_bogo()
        
        # Buttons
        btn_frame = tk.Frame(self.bogo_tab)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Enable BOGO", command=self.enable_bogo, 
                 bg='green', fg='white', width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Disable BOGO", command=self.disable_bogo, 
                 bg='red', fg='white', width=15).pack(side=tk.LEFT, padx=5)
        
        # Current BOGO products
        tk.Label(self.bogo_tab, text="Current BOGO Products:", font=('Arial', 12)).pack(pady=10)
        
        columns = ('ID', 'Product', 'Price')
        self.bogo_tree = ttk.Treeview(self.bogo_tab, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.bogo_tree.heading(col, text=col)
            self.bogo_tree.column(col, width=150)
        
        self.bogo_tree.pack(fill=tk.X, padx=10, pady=5)
        
        self.load_bogo_products()
    
    def load_products_for_bogo(self):
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, name FROM products ORDER BY name")
        products = c.fetchall()
        conn.close()
        
        self.bogo_product['values'] = [f"{p[1]} (ID: {p[0]})" for p in products]
    
    def load_bogo_products(self):
        for row in self.bogo_tree.get_children():
            self.bogo_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, name, price FROM products WHERE is_bogo=1 ORDER BY name")
        products = c.fetchall()
        conn.close()
        
        for p in products:
            self.bogo_tree.insert('', tk.END, values=(p[0], p[1], f"{CURRENCY_SYMBOL}{p[2]:.2f}"))
    
    def enable_bogo(self):
        selection = self.bogo_product.get()
        if not selection or '(ID: ' not in selection:
            show_error("Select a product first")
            return
        
        prod_id = int(selection.split('(ID: ')[1].rstrip(')'))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("UPDATE products SET is_bogo=1 WHERE id=?", (prod_id,))
        conn.commit()
        conn.close()
        
        show_success("BOGO enabled for selected product")
        self.load_bogo_products()
        self.load_product_discounts()
    
    def disable_bogo(self):
        selection = self.bogo_tree.selection()
        if not selection:
            show_error("Select a product from the list")
            return
        
        prod_id = self.bogo_tree.item(selection[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("UPDATE products SET is_bogo=0 WHERE id=?", (prod_id,))
        conn.commit()
        conn.close()
        
        show_success("BOGO disabled for selected product")
        self.load_bogo_products()
        self.load_product_discounts()
    
    def load_promotions(self):
        for row in self.promo_tree.get_children():
            self.promo_tree.delete(row)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''SELECT id, name, type, value, min_purchase, start_date, end_date, is_active 
                     FROM promotions ORDER BY id DESC''')
        promotions = c.fetchall()
        conn.close()
        
        for p in promotions:
            status = "Active" if p[7] else "Inactive"
            type_display = {"percent": "Percentage", "fixed": "Fixed Amount", "bogo": "BOGO"}.get(p[2], p[2])
            value_display = f"{p[3]}%" if p[2] == "percent" else f"{CURRENCY_SYMBOL}{p[3]}" if p[2] == "fixed" else "-"
            self.promo_tree.insert('', tk.END, values=(p[0], p[1], type_display, value_display, 
                                                       f"{CURRENCY_SYMBOL}{p[4]}", p[5], p[6], status))
    
    def load_product_discounts(self):
        for row in self.prod_discount_tree.get_children():
            self.prod_discount_tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if search:
            c.execute('''SELECT id, barcode, name, price, discount_percent, discount_start, discount_end, is_bogo
                         FROM products 
                         WHERE name LIKE ? OR barcode LIKE ?
                         ORDER BY name''', (f'%{search}%', f'%{search}%'))
        else:
            c.execute('''SELECT id, barcode, name, price, discount_percent, discount_start, discount_end, is_bogo
                         FROM products ORDER BY name''')
        
        products = c.fetchall()
        conn.close()
        
        for p in products:
            bogo_text = "Yes" if p[7] else "No"
            discount = f"{p[4]}%" if p[4] > 0 else "No"
            self.prod_discount_tree.insert('', tk.END, values=(p[0], p[1], p[2], f"{CURRENCY_SYMBOL}{p[3]:.2f}", 
                                                               discount, p[5] or "-", p[6] or "-", bogo_text))
    
    def set_product_discount(self):
        selected = self.prod_discount_tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        prod_id = self.prod_discount_tree.item(selected[0])['values'][0]
        prod_name = self.prod_discount_tree.item(selected[0])['values'][2]
        
        # Dialog for discount
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Set Discount for {prod_name}")
        dialog.geometry("340x400")
        dialog.configure(bg='#f9f9f9')
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 340) // 2
        y = (dialog.winfo_screenheight() - 400) // 2
        dialog.geometry(f"340x400+{x}+{y}")
        
        dialog.grab_set()
        dialog.transient(self.window)
        
        # Title
        tk.Label(dialog, text=f"SET DISCOUNT", font=('Arial', 14, 'bold'), 
                bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        
        # Main frame
        main_frame = tk.Frame(dialog, bg='#f9f9f9', padx=20, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Product name
        tk.Label(main_frame, text=f"Product: {prod_name}", font=('Arial', 11, 'bold'), 
                bg='#f9f9f9').pack(pady=5)
        
        # Discount percentage
        tk.Label(main_frame, text="Discount Percentage (%):", font=('Arial', 10), bg='#f9f9f9').pack(pady=5)
        discount_var = tk.StringVar()
        discount_entry = tk.Entry(main_frame, textvariable=discount_var, width=15, font=('Arial', 11), 
                                  justify='center', relief='solid', bd=1)
        discount_entry.pack(pady=5)
        discount_entry.focus()
        
        # Start date
        tk.Label(main_frame, text="Start Date (YYYY-MM-DD):", font=('Arial', 10), bg='#f9f9f9').pack(pady=5)
        start_var = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        start_entry = tk.Entry(main_frame, textvariable=start_var, width=15, font=('Arial', 11), 
                               justify='center', relief='solid', bd=1)
        start_entry.pack(pady=5)
        
        # End date
        tk.Label(main_frame, text="End Date (YYYY-MM-DD):", font=('Arial', 10), bg='#f9f9f9').pack(pady=5)
        end_var = tk.StringVar(value=(datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'))
        end_entry = tk.Entry(main_frame, textvariable=end_var, width=15, font=('Arial', 11), 
                             justify='center', relief='solid', bd=1)
        end_entry.pack(pady=5)
        
        # Setup Enter navigation
        setup_enter_navigation(discount_entry, start_entry)
        setup_enter_navigation(start_entry, end_entry)
        setup_enter_navigation(end_entry, lambda: save_discount())
        
        def save_discount():
            try:
                discount = float(discount_var.get())
                if discount < 0 or discount > 100:
                    show_error("Discount must be between 0 and 100")
                    return
                
                conn = sqlite3.connect('urban_pulse.db')
                c = conn.cursor()
                c.execute('''UPDATE products 
                            SET discount_percent=?, discount_start=?, discount_end=?
                            WHERE id=?''', (discount, start_var.get(), end_var.get(), prod_id))
                conn.commit()
                conn.close()
                
                show_success(f"Discount set for {prod_name}")
                dialog.destroy()
                self.load_product_discounts()
                
            except ValueError:
                show_error("Please enter a valid number")
        
        # Buttons
        btn_frame = tk.Frame(main_frame, bg='#f9f9f9')
        btn_frame.pack(pady=15)
        
        tk.Button(btn_frame, text="💾 Save Discount", command=save_discount, bg='#27ae60', fg='white',
                 font=('Arial', 11, 'bold'), width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy, bg='#e74c3c', fg='white',
                 font=('Arial', 11), width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def clear_product_discount(self):
        selected = self.prod_discount_tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        prod_id = self.prod_discount_tree.item(selected[0])['values'][0]
        prod_name = self.prod_discount_tree.item(selected[0])['values'][2]
        
        if ask_yes_no(f"Clear discount for {prod_name}?"):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute('''UPDATE products 
                        SET discount_percent=0, discount_start=NULL, discount_end=NULL
                        WHERE id=?''', (prod_id,))
            conn.commit()
            conn.close()
            
            show_success(f"Discount cleared for {prod_name}")
            self.load_product_discounts()
    
    def set_bogo(self):
        selected = self.prod_discount_tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        prod_id = self.prod_discount_tree.item(selected[0])['values'][0]
        prod_name = self.prod_discount_tree.item(selected[0])['values'][2]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("UPDATE products SET is_bogo=1 WHERE id=?", (prod_id,))
        conn.commit()
        conn.close()
        
        show_success(f"BOGO enabled for {prod_name}")
        self.load_product_discounts()
        self.load_bogo_products()
    
    def create_promotion(self):
        name = self.promo_name.get().strip()
        ptype = self.promo_type.get()
        value = self.promo_value.get().strip()
        min_purchase = self.promo_min.get().strip()
        start = self.promo_start.get().strip()
        end = self.promo_end.get().strip()
        product = self.promo_product.get().strip()
        
        if not name or not value or not start or not end:
            show_error("Please fill all required fields")
            return
        
        try:
            value = float(value)
            min_purchase = float(min_purchase) if min_purchase else 0
            product_id = int(product) if product else None
        except ValueError:
            show_error("Invalid number format")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute('''INSERT INTO promotions (name, type, value, min_purchase, start_date, end_date, product_id)
                    VALUES (?,?,?,?,?,?,?)''', (name, ptype, value, min_purchase, start, end, product_id))
        conn.commit()
        conn.close()
        
        show_success("Promotion created successfully!")
        self.load_promotions()
        
        # Clear form
        self.promo_name.delete(0, tk.END)
        self.promo_value.delete(0, tk.END)
        self.promo_min.delete(0, tk.END)
        self.promo_min.insert(0, "0")
        self.promo_product.delete(0, tk.END)
    
    def activate_promotion(self):
        selected = self.promo_tree.selection()
        if not selected:
            return
        
        promo_id = self.promo_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("UPDATE promotions SET is_active=1 WHERE id=?", (promo_id,))
        conn.commit()
        conn.close()
        
        self.load_promotions()
    
    def deactivate_promotion(self):
        selected = self.promo_tree.selection()
        if not selected:
            return
        
        promo_id = self.promo_tree.item(selected[0])['values'][0]
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("UPDATE promotions SET is_active=0 WHERE id=?", (promo_id,))
        conn.commit()
        conn.close()
        
        self.load_promotions()
    
    def delete_promotion(self):
        selected = self.promo_tree.selection()
        if not selected:
            return
        
        promo_id = self.promo_tree.item(selected[0])['values'][0]
        promo_name = self.promo_tree.item(selected[0])['values'][1]
        
        if ask_yes_no(f"Delete promotion '{promo_name}'?"):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("DELETE FROM promotions WHERE id=?", (promo_id,))
            conn.commit()
            conn.close()
            
            self.load_promotions()