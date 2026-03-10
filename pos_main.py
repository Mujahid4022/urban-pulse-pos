# pos/pos_main.py
import sys
import os

# CRITICAL: Add the parent directory to path BEFORE any other imports
# This must be the VERY FIRST thing after the imports
current_dir = os.path.dirname(os.path.abspath(__file__))  # pos folder
parent_dir = os.path.dirname(current_dir)  # Urban_Pulse_pos folder
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now import everything else
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from PIL import Image, ImageTk  # You may need to install: pip install pillow

# Now try to import utils - it should work
try:
    from utils import CURRENCY_SYMBOL, get_setting
    print(f"Success! Found utils at: {os.path.join(parent_dir, 'utils.py')}")
except ImportError as e:
    print(f"Error: {e}")
    print(f"Python path: {sys.path}")
    print(f"Looking for utils in: {parent_dir}")
    # Fallback values
    CURRENCY_SYMBOL = "Rs."
    def get_setting(key, default):
        return default

class CartManager:
    """Simple Cart Manager if module not found"""
    def __init__(self, pos):
        self.pos = pos
    
    def add_to_cart(self, event=None):
        barcode = self.pos.barcode_entry.get().strip()
        if not barcode:
            messagebox.showwarning("Warning", "Please scan or enter a barcode")
            return
    
        # Get product from database
        try:
            import sqlite3
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("SELECT barcode, name, price, stock FROM products WHERE barcode=?", (barcode,))
            product_data = c.fetchone()
            conn.close()
        
            if product_data:
                # Product found in database - use REAL data
                barcode, name, price, stock = product_data
                product = {
                    'barcode': barcode,
                    'name': name,
                    'price': float(price),
                    'stock': stock
                }
            else:
                # Product not found
                messagebox.showwarning("Warning", f"Product with barcode '{barcode}' not found in database")
                self.pos.barcode_entry.delete(0, tk.END)
                return
            
        except Exception as e:
            messagebox.showerror("Database Error", f"Error looking up product: {e}")
            return
    
        # ===== STOCK CHECK =====
        # Check if product is out of stock
        if product['stock'] <= 0:
            messagebox.showerror("❌ OUT OF STOCK", 
                f"Cannot add {product['name']}\n\nThis product is out of stock!\nPlease order from supplier.")
            self.pos.barcode_entry.delete(0, tk.END)
            self.pos.barcode_entry.focus_set()
            return
    
        # Check if product already in cart
        for item in self.pos.cart:
            if item['barcode'] == barcode:
                # Check if adding one more would exceed stock
                if item['qty'] + 1 > product['stock']:
                    messagebox.showerror("Insufficient Stock", 
                        f"You already have {item['qty']} in cart.\n"
                        f"Only {product['stock']} total available.\n"
                        f"You cannot add more.")
                    self.pos.barcode_entry.delete(0, tk.END)
                    self.pos.barcode_entry.focus_set()
                    return
            
                item['qty'] += 1
                item['total'] = item['qty'] * item['price'] * (1 - item['discount']/100)
                self.pos.update_totals()
                self.pos.refresh_cart_display()
                self.pos.barcode_entry.delete(0, tk.END)
                self.pos.barcode_entry.focus_set()
                return
    
        # Add new item with REAL product data
        cart_item = {
            'barcode': barcode,
            'name': product['name'],
            'price': float(product['price']),
            'qty': 1,
            'discount': 0,
            'total': float(product['price'])
        }
        self.pos.cart.append(cart_item)
        self.pos.update_totals()
        self.pos.refresh_cart_display()
        self.pos.barcode_entry.delete(0, tk.END)
        self.pos.barcode_entry.focus_set()

    def manual_add(self):
        """Open dialog with real-time product search - stays open for multiple additions"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Add Product")
        dialog.geometry("650x600")
        dialog.configure(bg='#f9f9f9')
        dialog.transient(self.pos.root)
        dialog.grab_set()
    
        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 650) // 2
        y = (dialog.winfo_screenheight() - 600) // 2
        dialog.geometry(f"650x600+{x}+{y}")
    
        # Title
        tk.Label(dialog, text="🔍 SEARCH PRODUCT", font=('Arial', 14, 'bold'),
                bg='#3498db', fg='white').pack(fill=tk.X, pady=0)
    
        # Main frame
        main = tk.Frame(dialog, bg='#f9f9f9', padx=15, pady=10)
        main.pack(fill=tk.BOTH, expand=True)
    
        # ===== BARCODE FIELD (Read-only, auto-filled) =====
        barcode_frame = tk.Frame(main, bg='#f9f9f9')
        barcode_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(barcode_frame, text="Barcode:", font=('Arial', 10, 'bold'),
                bg='#f9f9f9', width=8).pack(side=tk.LEFT)
    
        barcode_var = tk.StringVar()
        barcode_entry = tk.Entry(barcode_frame, textvariable=barcode_var,
                                font=('Arial', 11), width=30, relief='solid', bd=1,
                                state='readonly', readonlybackground='#ecf0f1')
        barcode_entry.pack(side=tk.LEFT, padx=5)
    
        # ===== PRODUCT NAME SEARCH (Real-time) =====
        search_frame = tk.Frame(main, bg='#f9f9f9')
        search_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(search_frame, text="Product Name:", font=('Arial', 10, 'bold'),
                bg='#f9f9f9', width=12).pack(side=tk.LEFT)
    
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var,
                               font=('Arial', 11), width=40, relief='solid', bd=1)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus_set()
    
        # Results listbox with scrollbar
        list_frame = tk.Frame(main)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
        listbox = tk.Listbox(list_frame, font=('Arial', 10), height=8,
                            selectbackground='#3498db', selectforeground='white')
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
    
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
        # ===== PRICE AND STOCK (Auto-filled) =====
        info_frame = tk.Frame(main, bg='#f9f9f9')
        info_frame.pack(fill=tk.X, pady=5)
    
        tk.Label(info_frame, text="Price:", font=('Arial', 10, 'bold'),
                bg='#f9f9f9').pack(side=tk.LEFT, padx=(0,5))
    
        price_var = tk.StringVar(value="0.00")
        price_label = tk.Label(info_frame, textvariable=price_var, font=('Arial', 11, 'bold'),
                              bg='#ecf0f1', fg='#27ae60', width=10, anchor='w',
                              relief='sunken', bd=1)
        price_label.pack(side=tk.LEFT, padx=5)
    
        tk.Label(info_frame, text="Stock:", font=('Arial', 10, 'bold'),
                bg='#f9f9f9').pack(side=tk.LEFT, padx=(20,5))
    
        stock_var = tk.StringVar(value="0")
        stock_label = tk.Label(info_frame, textvariable=stock_var, font=('Arial', 11),
                              bg='#ecf0f1', fg='#e67e22', width=8, anchor='w',
                              relief='sunken', bd=1)
        stock_label.pack(side=tk.LEFT, padx=5)
    
        # ===== QUANTITY (Manual) =====
        qty_frame = tk.Frame(main, bg='#f9f9f9')
        qty_frame.pack(fill=tk.X, pady=10)
    
        tk.Label(qty_frame, text="Quantity:", font=('Arial', 10, 'bold'),
                bg='#f9f9f9').pack(side=tk.LEFT, padx=(0,5))
    
        qty_var = tk.StringVar(value="1")
        qty_spinbox = tk.Spinbox(qty_frame, from_=1, to=999, textvariable=qty_var,
                                width=8, font=('Arial', 11), relief='solid', bd=1)
        qty_spinbox.pack(side=tk.LEFT, padx=5)
    
        # Quick quantity buttons
        for qty in [5, 10, 20, 50]:
            tk.Button(qty_frame, text=str(qty), command=lambda q=qty: qty_var.set(str(q)),
                     bg='#3498db', fg='white', font=('Arial', 9), width=3,
                     cursor='hand2').pack(side=tk.LEFT, padx=2)
    
        # Info label
        info_text = tk.StringVar(value="👆 Type product name to search")
        info_label = tk.Label(main, textvariable=info_text, bg='#ecf0f1',
                             font=('Arial', 9), anchor='w', relief='sunken', bd=1)
        info_label.pack(fill=tk.X, pady=5)
    
        # Store selected product
        selected_product = None
        products_list = []
    
        def search_products(*args):
            """Real-time search as user types - shows in-stock items first"""
            nonlocal products_list
            search_term = search_var.get().strip()
            listbox.delete(0, tk.END)
        
            if len(search_term) < 2:
                info_text.set("👆 Type at least 2 characters to search")
                return
        
            import sqlite3
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
        
            # Search with in-stock items first
            c.execute('''
                SELECT barcode, name, price, stock 
                FROM products 
                WHERE name LIKE ? OR name LIKE ?
                ORDER BY 
                    CASE 
                        WHEN stock > 0 THEN 0  -- In stock first
                        ELSE 1                   -- Out of stock last
                    END,
                    CASE 
                        WHEN name LIKE ? THEN 1
                        WHEN name LIKE ? THEN 2
                        ELSE 3
                    END,
                    name
                LIMIT 15
            ''', (
                f'{search_term}%',
                f'%{search_term}%',
                f'{search_term}%',
                f'%{search_term}%'
            ))
        
            products_list = c.fetchall()
            conn.close()
        
            if products_list:
                in_stock = sum(1 for p in products_list if p[3] > 0)
                out_stock = len(products_list) - in_stock
                info_text.set(f"Found {len(products_list)} products ({in_stock} in stock, {out_stock} out)")
            
                for p in products_list:
                    display = f"{p[1]} - Rs.{p[2]:.2f} "
                    if p[3] > 0:
                        display += f"(Stock: {p[3]})"
                        listbox.insert(tk.END, display)
                    else:
                        display += "❌ OUT OF STOCK"
                        listbox.insert(tk.END, display)
                        listbox.itemconfig(tk.END, fg='red')
            else:
                info_text.set(f"No products found matching '{search_term}'")
    
        def on_product_select(event):
            """Handle product selection from listbox"""
            nonlocal selected_product
            selection = listbox.curselection()
            if not selection or not products_list:
                return
        
            idx = selection[0]
            if idx < len(products_list):
                selected_product = products_list[idx]
                barcode_var.set(selected_product[0])
                search_var.set(selected_product[1])
                price_var.set(f"{selected_product[2]:.2f}")
                stock_var.set(str(selected_product[3]))
            
                # Show warning if out of stock
                if selected_product[3] <= 0:
                    info_text.set(f"⚠️ OUT OF STOCK: {selected_product[1]}")
                    stock_label.config(fg='red')
                else:
                    info_text.set(f"Selected: {selected_product[1]}")
                    stock_label.config(fg='#e67e22')
    
        def add_to_cart():
            """Add selected product to cart - with stock validation"""
            nonlocal selected_product
            if not selected_product:
                messagebox.showwarning("Warning", "Please select a product first")
                return
        
            try:
                qty = int(qty_var.get())
                if qty <= 0:
                    messagebox.showerror("Error", "Quantity must be positive")
                    return
            
                barcode, name, price, stock = selected_product
            
                # ===== CRITICAL: Check if stock is zero =====
                if stock <= 0:
                    messagebox.showerror("❌ OUT OF STOCK", 
                        f"Cannot add {name}\n\nThis product is out of stock!\nPlease order from supplier.")
                    return
            
                # Check if enough stock for requested quantity
                if qty > stock:
                    messagebox.showerror("Insufficient Stock", 
                        f"Only {stock} units available.\nYou requested {qty}.")
                    return
            
                # Check if already in cart and total would exceed stock
                for item in self.pos.cart:
                    if item['barcode'] == barcode:
                        if item['qty'] + qty > stock:
                            messagebox.showerror("Insufficient Stock", 
                                f"You already have {item['qty']} in cart.\n"
                                f"Only {stock} total available.\n"
                                f"You can add at most {stock - item['qty']} more.")
                            return
                        item['qty'] += qty
                        item['total'] = item['qty'] * price
                        found = True
                        break
                else:
                    # Add new item
                    cart_item = {
                        'barcode': barcode,
                        'name': name,
                        'price': float(price),
                        'qty': qty,
                        'discount': 0,
                        'total': float(price) * qty
                    }
                    self.pos.cart.append(cart_item)
            
                # Update POS display
                self.pos.update_totals()
                self.pos.refresh_cart_display()
            
                # Show success message
                messagebox.showinfo("Success", f"Added {qty} x {name} to cart")
            
                # Reset for next addition (but keep dialog open)
                selected_product = None
                products_list.clear()
                barcode_var.set("")
                search_var.set("")
                price_var.set("0.00")
                stock_var.set("0")
                qty_var.set("1")
                listbox.delete(0, tk.END)
                search_entry.focus_set()
                info_text.set("👆 Type product name to search")
                stock_label.config(fg='#e67e22')
            
            except ValueError:
                messagebox.showerror("Error", "Invalid quantity")
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
        # Bind events
        search_var.trace('w', search_products)
        listbox.bind('<<ListboxSelect>>', on_product_select)
        listbox.bind('<Double-Button-1>', lambda e: add_to_cart())
    
        # Buttons
        btn_frame = tk.Frame(main, bg='#f9f9f9')
        btn_frame.pack(pady=10)
    
        tk.Button(btn_frame, text="➕ ADD TO CART", command=add_to_cart,
                 bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                 width=15, height=2, cursor='hand2').pack(side=tk.LEFT, padx=10)
    
        tk.Button(btn_frame, text="✖ CANCEL", command=dialog.destroy,
                 bg='#e74c3c', fg='white', font=('Arial', 11, 'bold'),
                 width=12, height=1, cursor='hand2').pack(side=tk.LEFT, padx=5)

    def remove_item(self):
        selected = self.pos.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an item to remove")
            return

        # Get the selected item
        item = self.pos.tree.item(selected[0])
        values = item['values']
        if values:
            # Get the barcode from the selected row and convert to string
            barcode = str(values[1])
        
            # Find and remove from cart
            for i, cart_item in enumerate(self.pos.cart):
                if str(cart_item['barcode']) == barcode:
                    # Ask for confirmation before removing
                    if messagebox.askyesno("Confirm", f"Remove {cart_item['name']} from cart?"):
                        del self.pos.cart[i]
                        self.pos.update_totals()
                        self.pos.refresh_cart_display()
                        messagebox.showinfo("Success", f"{cart_item['name']} removed")  # Optional feedback
                    break
        
            self.pos.barcode_entry.focus_set()

    def clear_cart(self):
        if self.pos.cart and messagebox.askyesno("Confirm", "Clear entire cart?"):
            self.pos.cart.clear()
            self.pos.cart_discount_percent = 0
            self.pos.other_charges = 0
            self.pos.other_charges_var.set("0.00")
            self.pos.discount_info.config(text="")
            self.pos.update_totals()
            self.pos.refresh_cart_display()
            self.pos.barcode_entry.focus_set()  # Return focus to barcode field

class CustomerHandler:
    def __init__(self, pos):
        self.pos = pos

class DiscountHandler:
    def __init__(self, pos):
        self.pos = pos
    
    def apply_cart_discount(self):
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Apply Cart Discount")
        dialog.geometry("300x200")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Discount Percentage:", font=('Arial', 10, 'bold')).pack(pady=10)
        
        discount_var = tk.StringVar(value="0")
        discount_spinbox = tk.Spinbox(dialog, from_=0, to=100, textvariable=discount_var, width=10)
        discount_spinbox.pack(pady=5)
        
        def apply_discount():
            try:
                discount = float(discount_var.get())
                if 0 <= discount <= 100:
                    self.pos.cart_discount_percent = discount
                    self.pos.discount_info.config(text=f"Cart Discount: {discount}%")
                    self.pos.update_totals()
                    dialog.destroy()
                    self.pos.barcode_entry.focus_set()  # Return focus to barcode field
                else:
                    messagebox.showerror("Error", "Discount must be between 0 and 100")
            except ValueError:
                messagebox.showerror("Error", "Invalid discount value")
        
        tk.Button(dialog, text="Apply", command=apply_discount,
                 bg='#f39c12', fg='white', font=('Arial', 10, 'bold')).pack(pady=20)
        
        # Bind Enter key to apply_discount
        dialog.bind('<Return>', lambda e: apply_discount())

class PaymentHandler:
    def __init__(self, pos):
        self.pos = pos
    
    def process_checkout(self):
        if not self.pos.cart:
            messagebox.showwarning("Warning", "Cart is empty")
            self.pos.barcode_entry.focus_set()
            return

        if self.pos.sale_type.get() == "credit" and not self.pos.current_member:
            messagebox.showwarning("Warning", "Please select a member for credit sale")
            self.pos.barcode_entry.focus_set()
            return

        # ===== Handle payment method differently for cash vs credit =====
        payment_method = "Credit" if self.pos.sale_type.get() == "credit" else "Cash"
    
        # Only show payment dialog for cash sales
        if self.pos.sale_type.get() == "cash":
            # Payment Method Dialog
            payment_dialog = tk.Toplevel(self.pos.root)
            payment_dialog.title("Select Payment Method")
            payment_dialog.geometry("300x300")
            payment_dialog.transient(self.pos.root)
            payment_dialog.grab_set()

            # Center the dialog
            payment_dialog.update_idletasks()
            x = (payment_dialog.winfo_screenwidth() - 300) // 2
            y = (payment_dialog.winfo_screenheight() - 300) // 2
            payment_dialog.geometry(f"300x300+{x}+{y}")

            tk.Label(payment_dialog, text="PAYMENT METHOD", font=('Arial', 14, 'bold'), 
                 bg='#27ae60', fg='white').pack(fill=tk.X, pady=10)

            frame = tk.Frame(payment_dialog, padx=20, pady=10)
            frame.pack(fill=tk.BOTH, expand=True)

            tk.Label(frame, text="Select payment method:", font=('Arial', 11)).pack(anchor='w', pady=5)

            payment_var = tk.StringVar(value="Cash")
            methods = [
                ("💵 Cash", "Cash"),
                ("💳 Card", "Card"),
                ("📱 Mobile Payment", "Mobile"),
                ("🏦 Bank Transfer", "Bank")
            ]

            for text, value in methods:
                tk.Radiobutton(frame, text=text, variable=payment_var, value=value,
                            font=('Arial', 10)).pack(anchor='w', pady=2)

            def set_payment():
                nonlocal payment_method
                payment_method = payment_var.get()
                payment_dialog.destroy()

            tk.Button(frame, text="Proceed", command=set_payment,
                    bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                    width=10, cursor='hand2').pack(pady=10)

            # Wait for dialog to close
            self.pos.root.wait_window(payment_dialog)

        # ===== PROPER SALE RECORDING WITH LEDGER ENTRIES =====
        import sqlite3
        import json
        from datetime import datetime

        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()

        # Get customer ID and name
        customer_id = None
        customer_name = "Walk-in"
        member_id = None
        member_account_id = None

        if self.pos.sale_type.get() == "cash" and self.pos.current_customer:
            customer_id = self.pos.current_customer.get('id')
            customer_name = self.pos.current_customer.get('name')
        elif self.pos.sale_type.get() == "credit" and self.pos.current_member:
            member_id = self.pos.current_member.get('id')
            customer_name = self.pos.current_member.get('name')
            customer_id = member_id
        
            # Get member's individual account ID
            c.execute("SELECT account_id FROM members WHERE id = ?", (member_id,))
            result = c.fetchone()
            if result:
                member_account_id = result[0]

        # Calculate points earned (1 point per Rs.100 spent as example)
        points_earned = int(self.pos.total / 100) if self.pos.total > 0 else 0

        # Generate receipt path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        receipt_filename = f"receipts/receipt_{timestamp}.txt"

        # Generate a proper SALE voucher number
        today = self.pos.current_business_date.replace('-', '')
        c.execute("SELECT COUNT(*) FROM vouchers WHERE voucher_no LIKE ?", (f'SALE-{today}%',))
        count = c.fetchone()[0] + 1
        voucher_no = f"SALE-{today}-{count:03d}"

        # ===== 1. CREATE SALE VOUCHER =====
        narration = f"Sale to {customer_name} - {len(self.pos.cart)} items"
        if self.pos.other_charges > 0:
            narration += f" (Other charges: {CURRENCY_SYMBOL}{self.pos.other_charges:.2f})"
    
        c.execute('''INSERT INTO vouchers 
                    (voucher_no, voucher_type, voucher_date, narration, total_amount, 
                     created_by, created_at, member_id)
                    VALUES (?, 'Sale', ?, ?, ?, ?, ?, ?)''',
                  (voucher_no, self.pos.current_business_date, narration, self.pos.total,
                   self.pos.user['username'], datetime.now().strftime('%Y-%m-%d %H:%M:%S'), member_id))
        voucher_id = c.lastrowid

        # ===== 2. RECORD SALE IN SALES TABLE =====
        c.execute('''
            INSERT INTO sales (
                datetime, customer_id, customer_name, subtotal, 
                discount_total, tax_total, total, items, payment_method,
                points_earned, points_used, receipt_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            customer_id,
            customer_name,
            self.pos.subtotal,
            self.pos.discount_total,
            self.pos.tax_total,
            self.pos.total,
            json.dumps(self.pos.cart),
            payment_method,
            points_earned,
            self.pos.points_to_use or 0,
            receipt_filename
        ))

        sale_id = c.lastrowid

        # ===== 3. RECORD SALE ITEMS =====
        for item in self.pos.cart:
            c.execute('''
                INSERT INTO sale_items (
                    sale_id, product_id, product_name, quantity, 
                    unit_price, discount_percent, final_price
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                sale_id,
                item.get('id'),
                item['name'],
                item['qty'],
                item['price'],
                item.get('discount', 0),
                item['total']
            ))

        # ===== 4. CREATE LEDGER ENTRIES =====

        # Get account IDs
        # Cash/Bank account (only for cash sales)
        cash_account = None
        if payment_method == 'Cash':
            c.execute("SELECT id FROM accounts WHERE account_code='1000'")
            cash_account = c.fetchone()
        elif payment_method in ['Card', 'Bank Transfer']:
            c.execute("SELECT id FROM accounts WHERE account_code='1101'")  # Bank account
            cash_account = c.fetchone()

        # Sales Revenue account (4000)
        c.execute("SELECT id FROM accounts WHERE account_code='4000'")
        revenue_account = c.fetchone()

        # Other Income account (4100) - for other charges
        c.execute("SELECT id FROM accounts WHERE account_code='4100'")
        other_income_account = c.fetchone()
        if not other_income_account:
            # Create Other Income account if it doesn't exist
            c.execute('''INSERT INTO accounts 
                        (account_code, account_name, account_type, current_balance, is_active, created_date)
                        VALUES ('4100', 'Other Income', 'Income', 0, 1, date('now'))''')
            other_income_account = (c.lastrowid,)

        # Inventory account (1300)
        c.execute("SELECT id FROM accounts WHERE account_code='1300'")
        inventory_account = c.fetchone()

        # Cost of Goods Sold account (5000)
        c.execute("SELECT id FROM accounts WHERE account_code='5000'")
        cogs_account = c.fetchone()

        # Accounts Receivable (for credit sales)
        if self.pos.sale_type.get() == "credit":
            c.execute("SELECT id FROM accounts WHERE account_code='1200'")
            receivable_account = c.fetchone()

        # ===== FIX: Split revenue between product sales and other charges =====
        product_revenue = self.pos.subtotal - self.pos.discount_total
        other_charges = self.pos.other_charges
        total_amount = product_revenue + other_charges

        # ===== ENTRY 1: Debit appropriate account / Credit Revenue accounts =====
        if revenue_account and other_income_account:
            if self.pos.sale_type.get() == "cash" and cash_account:
                # Cash sale: Debit Cash (total amount)
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, ?, 0, ?, ?)''',
                          (voucher_id, cash_account[0], total_amount, 
                           self.pos.current_business_date, f"Cash sale to {customer_name}"))
            
                # Credit Sales Revenue for products
                if product_revenue > 0:
                    c.execute('''INSERT INTO ledger_entries 
                                (voucher_id, account_id, debit, credit, entry_date, narration)
                                VALUES (?, ?, 0, ?, ?, ?)''',
                              (voucher_id, revenue_account[0], product_revenue, 
                               self.pos.current_business_date, f"Sales revenue from products"))
            
                # Credit Other Income for other charges
                if other_charges > 0:
                    c.execute('''INSERT INTO ledger_entries 
                                (voucher_id, account_id, debit, credit, entry_date, narration)
                                VALUES (?, ?, 0, ?, ?, ?)''',
                              (voucher_id, other_income_account[0], other_charges, 
                               self.pos.current_business_date, f"Other charges (delivery/service/etc)"))
            
                # Update cash balance
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                         (total_amount, cash_account[0]))
            
            elif self.pos.sale_type.get() == "credit" and receivable_account:
                # Credit sale: ONLY debit the member's individual account (not AR)
                if member_account_id:
                    c.execute('''INSERT INTO ledger_entries 
                                (voucher_id, account_id, debit, credit, entry_date, narration)
                                VALUES (?, ?, ?, 0, ?, ?)''',
                              (voucher_id, member_account_id, total_amount, 
                               self.pos.current_business_date, f"Credit sale to {customer_name}"))
                    
                    c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                             (total_amount, member_account_id))
                    print(f"✅ Updated member account {member_account_id} with Rs.{total_amount}")

                # Credit Sales Revenue for products
                if product_revenue > 0:
                    c.execute('''INSERT INTO ledger_entries 
                                (voucher_id, account_id, debit, credit, entry_date, narration)
                                VALUES (?, ?, 0, ?, ?, ?)''',
                              (voucher_id, revenue_account[0], product_revenue, 
                               self.pos.current_business_date, f"Sales revenue from products"))
                    c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                             (product_revenue, revenue_account[0]))

                # Credit Other Income for other charges
                if other_charges > 0:
                    c.execute('''INSERT INTO ledger_entries 
                                (voucher_id, account_id, debit, credit, entry_date, narration)
                                VALUES (?, ?, 0, ?, ?, ?)''',
                              (voucher_id, other_income_account[0], other_charges, 
                               self.pos.current_business_date, f"Other charges"))
                    c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                             (other_charges, other_income_account[0]))

        # ===== ENTRY 2: Debit COGS / Credit Inventory (for cost of goods sold) =====
        if cogs_account and inventory_account:
            total_cost = 0
            for item in self.pos.cart:
                # Get cost price for each item
                c.execute("SELECT cost_price FROM products WHERE id=?", (item.get('id'),))
                cost = c.fetchone()
                if cost and cost[0]:
                    item_cost = cost[0] * item['qty']
                    total_cost += item_cost
    
            if total_cost > 0:
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, ?, 0, ?, ?)''',
                          (voucher_id, cogs_account[0], total_cost, 
                           self.pos.current_business_date, f"Cost of goods sold for sale #{sale_id}"))
        
                c.execute('''INSERT INTO ledger_entries 
                            (voucher_id, account_id, debit, credit, entry_date, narration)
                            VALUES (?, ?, 0, ?, ?, ?)''',
                          (voucher_id, inventory_account[0], total_cost, 
                           self.pos.current_business_date, f"Inventory reduction for sale #{sale_id}"))
        
                # Update COGS and Inventory balances
                c.execute("UPDATE accounts SET current_balance = current_balance + ? WHERE id=?", 
                         (total_cost, cogs_account[0]))
                c.execute("UPDATE accounts SET current_balance = current_balance - ? WHERE id=?", 
                         (total_cost, inventory_account[0]))

        # ===== 5. UPDATE PRODUCT STOCK =====
        for item in self.pos.cart:
            c.execute('''
                UPDATE products 
                SET stock = stock - ? 
                WHERE id = ?
            ''', (item['qty'], item.get('id')))

        # ===== 6. RECORD IN CREDIT_SALES TABLE (for credit sales) =====
        if self.pos.sale_type.get() == "credit" and member_id:
            # Generate invoice number
            c.execute("SELECT COUNT(*) FROM credit_sales")
            inv_count = c.fetchone()[0] + 1
            invoice_no = f"INV-{inv_count:04d}"
        
            # Calculate due date (30 days from now)
            from datetime import timedelta
            due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
            c.execute('''INSERT INTO credit_sales 
                        (invoice_no, member_id, sale_date, total_amount, paid_amount, due_amount, due_date, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending')''',
                      (invoice_no, member_id, self.pos.current_business_date, 
                       self.pos.total, 0, self.pos.total, due_date))
            print(f"✅ Recorded in credit_sales table: {invoice_no}")

        conn.commit()
        conn.close()
        # ===== END PROPER SALE RECORDING =====

        # Create receipt display
        receipt = f"""
    ╔════════════════════════════╗
    ║     URBAN PULSE POS        ║
    ╠════════════════════════════╣
    ║ Date: {self.pos.current_business_date} {datetime.now().strftime('%H:%M')}
    ║ {self.pos.sale_type.get().upper()} SALE
    ║ Payment: {payment_method}
    ║ Customer: {customer_name}
    ║ Voucher: {voucher_no}
    ║ Sale ID: {sale_id}
    ╠════════════════════════════╣
    """

        for i, item in enumerate(self.pos.cart, 1):
            receipt += f"\n║ {i}. {item['name'][:15]:15} x{item['qty']}"
            receipt += f"\n║    {CURRENCY_SYMBOL}{item['total']:.2f}\n"

        receipt += f"""
    ╠════════════════════════════╣
    ║ SUB TOTAL: {CURRENCY_SYMBOL}{self.pos.subtotal:.2f}
    ║ DISCOUNT: -{CURRENCY_SYMBOL}{self.pos.discount_total:.2f}
    ║ GST ({int(self.pos.tax_rate*100)}%): {CURRENCY_SYMBOL}{self.pos.tax_total:.2f}
    ║ OTHER CHARGES: {CURRENCY_SYMBOL}{self.pos.other_charges:.2f}
    ║════════════════════════════╣
    ║ GRAND TOTAL: {CURRENCY_SYMBOL}{self.pos.total:.2f}
    ║ Points Earned: {points_earned}
    ╚════════════════════════════╝
    """

        # Save receipt to file
        try:
            with open(receipt_filename, 'w') as f:
                f.write(receipt)
        except:
            pass

        # Show receipt
        receipt_window = tk.Toplevel(self.pos.root)
        receipt_window.title("Receipt")
        receipt_window.geometry("400x600")
        receipt_window.transient(self.pos.root)
        receipt_window.grab_set()
        receipt_window.lift()
        receipt_window.focus_force()

        text_area = tk.Text(receipt_window, font=('Courier', 10), wrap=tk.NONE)
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert('1.0', receipt)
        text_area.config(state=tk.DISABLED)

        close_btn = tk.Button(receipt_window, text="Close", 
                            command=lambda: self.close_receipt(receipt_window),
                            bg='#3498db', fg='white', font=('Arial', 10, 'bold'))
        close_btn.pack(pady=10)

        receipt_window.bind('<Escape>', lambda e: self.close_receipt(receipt_window))
        self.pos.root.wait_window(receipt_window)

    def close_receipt(self, window):
        """Close receipt window and return focus to barcode"""
        window.destroy()
        
        # Ask if cart should be cleared
        if messagebox.askyesno("Confirm", "Complete checkout and clear cart?"):
            self.pos.cart.clear()
            self.pos.current_customer = None
            self.pos.current_member = None
            self.pos.cart_discount_percent = 0
            self.pos.other_charges = 0
            self.pos.other_charges_var.set("0.00")
            self.pos.discount_info.config(text="")
            self.pos.cash_customer_label.config(text="Customer: Not Selected", fg='#7f8c8d')
            self.pos.credit_member_label.config(text="Member: Not Selected", fg='#7f8c8d')
            self.pos.display_customer_name.set("Not Selected")
            self.pos.display_customer_type.set("Cash Customer")
            self.pos.display_loyalty_points.set("0")
            self.pos.customer_id_label.config(text="-")
            self.pos.update_totals()
            self.pos.refresh_cart_display()
        
        # Always return focus to barcode field
        self.pos.barcode_entry.focus_set()

class Navigation:
    def __init__(self, pos):
        self.pos = pos

    def open_category_manager(self):
        """Open Category Manager"""
        try:
            from category_manager import CategoryManager
            CategoryManager(self.pos.root, self.pos.user['username'], 
                           self.pos.current_business_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Category Manager not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Category Manager: {e}")
        
        self.pos.barcode_entry.focus_set()
    
    def open_stock_summary(self):
        """Open Stock Summary Report"""
        try:
            from stock_summary import StockSummary
            StockSummary(self.pos.root, self.pos.user['username'], 
                        self.pos.current_business_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Stock Summary not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Stock Summary: {e}")
        
        self.pos.barcode_entry.focus_set()
    
    def open_sku_ledger(self):
        """Open SKU Ledger"""
        try:
            from sku_ledger import SKULedger
            SKULedger(self.pos.root, self.pos.user['username'], 
                     self.pos.current_business_date)
        except ImportError as e:
            messagebox.showerror("Error", f"SKU Ledger not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening SKU Ledger: {e}")
        
        self.pos.barcode_entry.focus_set()
    
    def manage_products(self):
        """Open Product Manager - FIXED: Only one window"""
        try:
            from product_manager import ProductManager
            # Pass self.pos.root as parent, don't create extra window
            if hasattr(ProductManager, '__init__'):
                # Check if ProductManager expects a parent window
                pm = ProductManager(self.pos.root)
            else:
                messagebox.showerror("Error", "Product manager not compatible")
        except ImportError as e:
            messagebox.showerror("Error", f"Product manager not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening product manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def manage_customers(self):
        """Open Customer Manager - FIXED: Only one window"""
        try:
            from customer_manager import CustomerManager
            # Pass self.pos.root as parent
            cm = CustomerManager(self.pos.root)
        except ImportError:
            try:
                from customer_manager import SelectCustomer
                # Pass self.pos.root as parent
                sc = SelectCustomer(self.pos.root)
            except ImportError:
                messagebox.showerror("Error", "Customer manager not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening customer manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def open_supplier_manager(self):
        """Open Supplier Manager - FIXED: Only one window and passing working_date"""
        try:
            from supplier_manager import SupplierManager
            # Pass self.pos.root as parent AND the working date
            sm = SupplierManager(self.pos.root, working_date=self.pos.current_business_date)
        except ImportError:
            messagebox.showerror("Error", "Supplier manager not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening supplier manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def open_discount_manager(self):
        """Open Discount Manager - FIXED: Only one window"""
        try:
            from discount_manager import DiscountManager
            # Pass self.pos.root as parent
            dm = DiscountManager(self.pos.root)
        except ImportError:
            # Fallback to discount dialog
            self.pos.discount_handler.apply_cart_discount()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening discount manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def open_daily_report(self):
        """Open Daily Report - FIXED: Only one window"""
        try:
            from daily_report import DailyReport
            # Pass self.pos.root as parent
            dr = DailyReport(self.pos.root)
        except ImportError:
            self.show_simple_report()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening daily report: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def points_manager(self):
        """Open Points Manager - FIXED: Only one window"""
        try:
            from points_manager import PointsManager
            # Pass self.pos.root as parent
            pm = PointsManager(self.pos.root)
        except ImportError:
            self.show_points_dialog()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening points manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()

    def open_tax_settings(self):
        """Open Tax Rate Settings"""
        try:
            from tax_settings import TaxSettings
            TaxSettings(self.pos.root)
        except ImportError as e:
            messagebox.showerror("Error", f"Tax Settings module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening tax settings: {e}")
    
    def receipt_history(self):
        """Open Receipt History - FIXED: Only one window"""
        try:
            from receipt import ReceiptHistory
            # Pass self.pos.root as parent
            rh = ReceiptHistory(self.pos.root)
        except ImportError:
            self.show_receipt_history()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening receipt history: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def open_membership_manager(self):
        """Open Membership Manager - FIXED: Only one window"""
        try:
            from membership_manager import MembershipManager
            # Pass self.pos.root as parent and working_date
            mm = MembershipManager(self.pos.root, working_date=self.pos.current_business_date)
        except ImportError:
            try:
                from membership_manager import SelectMemberForCredit
                # Pass self.pos.root as parent
                sm = SelectMemberForCredit(self.pos.root, working_date=self.pos.current_business_date)
            except ImportError:
                messagebox.showerror("Error", "Membership manager not found")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening membership manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    def open_credit_manager(self):
        """Open Credit Manager (Recovery) - FIXED: Only one window"""
        try:
            from credit_manager import CreditManager
            # Pass self.pos.root as parent
            cm = CreditManager(self.pos.root)
        except ImportError:
            self.show_credit_dialog()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening credit manager: {e}")
        
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()

    def open_accounting(self):
        """Open Accounting Menu"""
        try:
            from accounting_menu import AccountingMenu
            am = AccountingMenu(self.pos.root, self.pos.user['username'], 
                                self.pos.current_business_date)
        except ImportError as e:
            messagebox.showerror("Error", f"Accounting module not found: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Error opening accounting: {e}")
        
        self.pos.barcode_entry.focus_set()
    
    def open_day_manager(self):
        """Open Day Open/Close Manager - FIXED: Only one window"""
        try:
            from day_manager import DayManager
            # Pass self.pos.root as parent AND the username
            dm = DayManager(self.pos.root, username=self.pos.user['username'])
        except ImportError:
            self.show_day_dialog()
        except Exception as e:
            messagebox.showerror("Error", f"Error opening day manager: {e}")
    
        # Return focus to barcode after closing
        self.pos.barcode_entry.focus_set()
    
    # ============ FALLBACK DIALOGS ============
    
    def show_simple_report(self):
        """Show a simple daily report dialog"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Daily Report - Simple View")
        dialog.geometry("600x400")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="DAILY REPORT", font=('Arial', 16, 'bold')).pack(pady=10)
        
        report_frame = tk.Frame(dialog, bg='white', relief=tk.RIDGE, bd=2)
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        date_frame = tk.Frame(report_frame, bg='white')
        date_frame.pack(fill=tk.X, pady=5, padx=10)
        tk.Label(date_frame, text="Date:", bg='white', font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
        tk.Label(date_frame, text=datetime.now().strftime('%Y-%m-%d'), bg='white', 
                font=('Arial', 10)).pack(side=tk.RIGHT)
        
        ttk.Separator(report_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        stats = [
            ("Total Sales:", f"{CURRENCY_SYMBOL}0.00"),
            ("Total Transactions:", "0"),
            ("Average Sale:", f"{CURRENCY_SYMBOL}0.00"),
            ("Cash Sales:", f"{CURRENCY_SYMBOL}0.00"),
            ("Credit Sales:", f"{CURRENCY_SYMBOL}0.00"),
        ]
        
        for label, value in stats:
            stat_frame = tk.Frame(report_frame, bg='white')
            stat_frame.pack(fill=tk.X, pady=3, padx=10)
            tk.Label(stat_frame, text=label, bg='white', font=('Arial', 9)).pack(side=tk.LEFT)
            tk.Label(stat_frame, text=value, bg='white', font=('Arial', 9, 'bold')).pack(side=tk.RIGHT)
        
        tk.Button(dialog, text="Close", command=lambda: self.close_dialog(dialog),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
        
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_points_dialog(self):
        """Show points management dialog"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Points Manager")
        dialog.geometry("500x400")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="POINTS MANAGEMENT", font=('Arial', 14, 'bold')).pack(pady=10)
        
        if self.pos.current_customer:
            points_frame = tk.Frame(dialog, bg='#f0f2f5', relief=tk.RIDGE, bd=2)
            points_frame.pack(fill=tk.X, padx=20, pady=10)
            
            tk.Label(points_frame, text=f"Customer: {self.pos.current_customer['name']}", 
                    font=('Arial', 10, 'bold')).pack(pady=5)
            tk.Label(points_frame, text=f"Current Points: {self.pos.display_loyalty_points.get()}", 
                    font=('Arial', 12, 'bold'), fg='#e67e22').pack(pady=5)
            
            button_frame = tk.Frame(points_frame)
            button_frame.pack(pady=10)
            tk.Button(button_frame, text="Add Points", bg='#27ae60', fg='white',
                     command=lambda: self.show_add_points(dialog)).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Redeem Points", bg='#e67e22', fg='white',
                     command=lambda: self.show_redeem_points(dialog)).pack(side=tk.LEFT, padx=5)
        else:
            tk.Label(dialog, text="No customer selected in POS", 
                    fg='red').pack(pady=20)
        
        tk.Button(dialog, text="Close", command=lambda: self.close_dialog(dialog),
                 bg='#95a5a6', fg='white').pack(pady=10)
        
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_add_points(self, parent):
        """Show add points dialog"""
        dialog = tk.Toplevel(parent)
        dialog.title("Add Points")
        dialog.geometry("300x200")
        dialog.transient(parent)
        dialog.grab_set()
        
        tk.Label(dialog, text="Add Points", font=('Arial', 12, 'bold')).pack(pady=10)
        tk.Label(dialog, text="Points to Add:").pack(pady=5)
        
        points_var = tk.StringVar(value="100")
        points_entry = tk.Entry(dialog, textvariable=points_var, width=15)
        points_entry.pack(pady=5)
        points_entry.focus_set()
        
        def add():
            try:
                points = int(points_var.get())
                current = int(self.pos.display_loyalty_points.get() or 0)
                new_total = current + points
                self.pos.display_loyalty_points.set(str(new_total))
                messagebox.showinfo("Success", f"Added {points} points. New total: {new_total}")
                dialog.destroy()
                self.pos.barcode_entry.focus_set()
            except ValueError:
                messagebox.showerror("Error", "Invalid points value")
        
        tk.Button(dialog, text="Add", command=add, bg='#27ae60', fg='white').pack(pady=10)
        tk.Button(dialog, text="Cancel", command=lambda: self.close_dialog(dialog),
                 bg='#95a5a6', fg='white').pack(pady=5)
        
        dialog.bind('<Return>', lambda e: add())
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_redeem_points(self, parent):
        """Show redeem points dialog"""
        dialog = tk.Toplevel(parent)
        dialog.title("Redeem Points")
        dialog.geometry("300x250")
        dialog.transient(parent)
        dialog.grab_set()
        
        tk.Label(dialog, text="Redeem Points", font=('Arial', 12, 'bold')).pack(pady=10)
        
        current_points = int(self.pos.display_loyalty_points.get() or 0)
        tk.Label(dialog, text=f"Available Points: {current_points}").pack(pady=5)
        
        conversion = self.pos.conversion_rate
        tk.Label(dialog, text=f"Conversion: {conversion} points = {CURRENCY_SYMBOL}1").pack(pady=5)
        
        tk.Label(dialog, text="Points to Redeem:").pack(pady=5)
        points_var = tk.StringVar(value=str(min(100, current_points)))
        points_entry = tk.Entry(dialog, textvariable=points_var, width=15)
        points_entry.pack(pady=5)
        points_entry.focus_set()
        
        def redeem():
            try:
                points = int(points_var.get())
                if points > current_points:
                    messagebox.showerror("Error", "Not enough points")
                    return
                if points < self.pos.min_redeem:
                    messagebox.showerror("Error", f"Minimum redeem is {self.pos.min_redeem} points")
                    return
                
                amount = points / conversion
                new_total = current_points - points
                self.pos.display_loyalty_points.set(str(new_total))
                self.pos.points_to_use = points
                messagebox.showinfo("Success", f"Redeemed {points} points for {CURRENCY_SYMBOL}{amount:.2f}")
                dialog.destroy()
                self.pos.barcode_entry.focus_set()
            except ValueError:
                messagebox.showerror("Error", "Invalid points value")
        
        tk.Button(dialog, text="Redeem", command=redeem, bg='#e67e22', fg='white').pack(pady=10)
        tk.Button(dialog, text="Cancel", command=lambda: self.close_dialog(dialog),
                 bg='#95a5a6', fg='white').pack(pady=5)
        
        dialog.bind('<Return>', lambda e: redeem())
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_receipt_history(self):
        """Show receipt history dialog"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Receipt History")
        dialog.geometry("800x500")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="RECEIPT HISTORY", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree_frame = tk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Receipt #', 'Date', 'Customer', 'Total', 'Payment')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        sample_data = [
            ('RCP-001', datetime.now().strftime('%Y-%m-%d %H:%M'), 'Walk-in Customer', f'{CURRENCY_SYMBOL}150.00', 'Cash'),
            ('RCP-002', datetime.now().strftime('%Y-%m-%d %H:%M'), 'Premium Member', f'{CURRENCY_SYMBOL}320.50', 'Credit'),
        ]
        
        for item in sample_data:
            tree.insert('', tk.END, values=item)
        
        tk.Button(dialog, text="Close", command=lambda: self.close_dialog(dialog),
                 bg='#3498db', fg='white', font=('Arial', 10, 'bold')).pack(pady=10)
        
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_credit_dialog(self):
        """Show credit management dialog"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Credit Management - Recovery")
        dialog.geometry("700x500")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="CREDIT RECOVERY", font=('Arial', 14, 'bold')).pack(pady=10)
        
        tree_frame = tk.Frame(dialog)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ('Invoice #', 'Customer', 'Date', 'Amount', 'Due Date', 'Status')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        col_widths = [100, 150, 100, 100, 100, 80]
        for col, width in zip(columns, col_widths):
            tree.heading(col, text=col)
            tree.column(col, width=width)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Record Payment", bg='#27ae60', fg='white',
                 command=lambda: messagebox.showinfo("Info", "Payment recording - To be implemented")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="View Details", bg='#3498db', fg='white',
                 command=lambda: messagebox.showinfo("Info", "View details - To be implemented")).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=lambda: self.close_dialog(dialog),
                 bg='#95a5a6', fg='white').pack(side=tk.LEFT, padx=5)
        
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def show_day_dialog(self):
        """Show day open/close dialog"""
        dialog = tk.Toplevel(self.pos.root)
        dialog.title("Day Open/Close")
        dialog.geometry("500x400")
        dialog.transient(self.pos.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="DAY OPEN/CLOSE", font=('Arial', 14, 'bold')).pack(pady=10)
        
        status_frame = tk.Frame(dialog, bg='#f0f2f5', relief=tk.RIDGE, bd=2)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        current_time = datetime.now()
        is_open = True  # This should come from database
        
        tk.Label(status_frame, text="Current Status:", font=('Arial', 10, 'bold')).pack(pady=5)
        status_text = "🟢 OPEN" if is_open else "🔴 CLOSED"
        status_color = '#27ae60' if is_open else '#e74c3c'
        tk.Label(status_frame, text=status_text, fg=status_color, 
                font=('Arial', 12, 'bold')).pack(pady=5)
        
        tk.Label(status_frame, text=f"Date: {current_time.strftime('%Y-%m-%d')}").pack(pady=2)
        tk.Label(status_frame, text=f"Time: {current_time.strftime('%H:%M:%S')}").pack(pady=2)
        
        action_frame = tk.Frame(dialog)
        action_frame.pack(pady=20)
        
        if is_open:
            tk.Button(action_frame, text="🔴 CLOSE DAY", command=lambda: self.close_day(dialog),
                     bg='#e74c3c', fg='white', font=('Arial', 12, 'bold'),
                     width=15, height=2).pack()
        else:
            tk.Button(action_frame, text="🟢 OPEN DAY", command=lambda: self.open_day(dialog),
                     bg='#27ae60', fg='white', font=('Arial', 12, 'bold'),
                     width=15, height=2).pack()
        
        summary_frame = tk.Frame(dialog, relief=tk.RIDGE, bd=1)
        summary_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(summary_frame, text="Today's Summary", font=('Arial', 10, 'bold')).pack(pady=5)
        
        stats = [
            ("Total Sales:", f"{CURRENCY_SYMBOL}0.00"),
            ("Transactions:", "0"),
            ("Cash:", f"{CURRENCY_SYMBOL}0.00"),
            ("Credit:", f"{CURRENCY_SYMBOL}0.00"),
        ]
        
        for label, value in stats:
            stat_row = tk.Frame(summary_frame)
            stat_row.pack(fill=tk.X, padx=10, pady=2)
            tk.Label(stat_row, text=label).pack(side=tk.LEFT)
            tk.Label(stat_row, text=value, font=('Arial', 9, 'bold')).pack(side=tk.RIGHT)
        
        tk.Button(dialog, text="Close", command=lambda: self.close_dialog(dialog),
                 bg='#95a5a6', fg='white').pack(pady=10)
        
        dialog.bind('<Escape>', lambda e: self.close_dialog(dialog))
    
    def close_dialog(self, dialog):
        """Close dialog and return focus to barcode"""
        dialog.destroy()
        self.pos.barcode_entry.focus_set()

    def open_stock_history(self):
        """Open Stock Adjustment History"""
        try:
            from stock_history import StockHistory
            StockHistory(self.pos.root, self.pos.user['username'], 
                    self.pos.current_business_date)
        except Exception as e:
            messagebox.showerror("Error", f"Error opening Stock History: {e}")
    
        self.pos.barcode_entry.focus_set()
    
    def open_day(self, dialog):
        """Open the day"""
        self.pos.current_business_date = datetime.now().strftime('%Y-%m-%d')
        messagebox.showinfo("Success", f"Day opened for {self.pos.current_business_date}")
        dialog.destroy()
        self.pos.barcode_entry.focus_set()
    
    def close_day(self, dialog):
        """Close the day"""
        if messagebox.askyesno("Confirm", "Close the day? This will generate a report."):
            report = f"""
    DAY CLOSING REPORT
    Date: {self.pos.current_business_date}
    Time: {datetime.now().strftime('%H:%M:%S')}

    Total Sales: {CURRENCY_SYMBOL}{self.pos.subtotal:.2f}
    Total Transactions: {len(self.pos.cart)}
            """
            messagebox.showinfo("Day Closed", report)
            # Set next day
            from datetime import timedelta
            next_day = datetime.now() + timedelta(days=1)
            self.pos.current_business_date = next_day.strftime('%Y-%m-%d')
            dialog.destroy()
            self.pos.barcode_entry.focus_set()

class UrbanPulsePOS:
    def __init__(self, user):
        self.user = user
        self.root = tk.Tk()
        self.root.title(f"Urban Pulse POS - {user['username']} ({user['role']})")
        self.root.geometry("1300x800")  # Reduced height
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 1300) // 2
        y = (self.root.winfo_screenheight() - 800) // 2
        self.root.geometry(f"1300x800+{x}+{y}")
        
        self.root.lift()
        self.root.focus_force()

        # Customer display variables
        self.display_customer_name = tk.StringVar(value="Not Selected")
        self.display_customer_type = tk.StringVar(value="Cash Customer")
        self.display_loyalty_points = tk.StringVar(value="0")
        
        # Cart variables
        self.cart = []
        self.subtotal = 0
        self.discount_total = 0
        self.tax_total = 0
        self.other_charges = 0  # Added for other charges
        self.total = 0
        self.current_customer = None  # For cash/walk-in
        self.current_member = None     # For credit sale
        self.points_to_use = 0
        self.cart_discount_percent = 0
        self.current_business_date = user.get('working_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Sale type: "cash" or "credit"
        self.sale_type = tk.StringVar(value="cash")
        
        # Get settings
        self.conversion_rate = float(get_setting('points_conversion_rate', 100))
        self.min_redeem = float(get_setting('points_min_redeem', 100))
        self.earn_rate = float(get_setting('points_earn_rate', 1))

        # Load tax rate from database settings
        import sqlite3
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("SELECT value FROM settings WHERE key='tax_rate'")
            result = c.fetchone()
            if result:
                tax_rate_value = float(result[0])
                print(f"✅ Tax rate loaded from database: {tax_rate_value}%")
            else:
                tax_rate_value = 0  # Default to 0% if not set
                print(f"ℹ️ No tax rate in database, using default: 0%")
            conn.close()
        except Exception as e:
            print(f"⚠️ Error loading tax rate: {e}")
            tax_rate_value = 0  # Fallback to 0% on error

        self.tax_rate = float(tax_rate_value) / 100
        
        # Initialize handlers
        self.cart_manager = CartManager(self)
        self.customer_handler = CustomerHandler(self)
        self.discount_handler = DiscountHandler(self)
        self.payment_handler = PaymentHandler(self)
        self.navigation = Navigation(self)
        
        # Create UI
        self.create_widgets()
        self.root.mainloop()
    
    def get_setting(self, key, default):
        return get_setting(key, default)
    
    def refresh_cart_display(self):
        """Refresh the cart treeview with editable quantity field"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Add cart items
        for idx, item in enumerate(self.cart, 1):
            values = (
                idx,
                item['barcode'],
                item['name'],
                f"{CURRENCY_SYMBOL}{item['price']:.2f}",
                item['qty'],  # This will be editable
                f"{item['discount']}%",
                f"{CURRENCY_SYMBOL}{item['total']:.2f}"
            )
            self.tree.insert('', tk.END, values=values)
        
        # Bind double-click to edit quantity
        self.tree.bind('<Double-1>', self.on_qty_double_click)
    
    def on_qty_double_click(self, event):
        """Handle double-click on treeview to edit quantity"""
        # Get the row that was clicked
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        if not item:
            return
        
        # Check if the clicked column is the Quantity column (column #5)
        if column == '#5':  # Quantity column
            self.edit_qty(item)
        else:
            # For other columns, just select the item
            self.tree.selection_set(item)
    
    def edit_qty(self, item_id):
        """Create an entry widget to edit quantity inline"""
        # Get the current values
        values = self.tree.item(item_id, 'values')
        if not values:
            return
        
        # Get the barcode to find the cart item
        barcode = values[1]
        
        # Find the cart item
        cart_item = None
        for item in self.cart:
            if item['barcode'] == barcode:
                cart_item = item
                break
        
        if not cart_item:
            return
        
        # Get the bounding box of the cell
        x, y, width, height = self.tree.bbox(item_id, column='#5')
        
        # Create an entry widget for editing
        entry = tk.Entry(self.tree, font=('Arial', 9), justify='center', 
                         bg='white', relief='solid', bd=1)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, str(cart_item['qty']))
        entry.select_range(0, tk.END)
        entry.focus_set()
        
        def save_edit(event=None):
            """Save the edited quantity"""
            try:
                new_qty = int(entry.get().strip())
                
                # Validate quantity
                if new_qty <= 0:
                    # Remove item if quantity is 0 or negative
                    self.cart.remove(cart_item)
                else:
                    # Check stock availability
                    try:
                        import sqlite3
                        conn = sqlite3.connect('urban_pulse.db')
                        c = conn.cursor()
                        c.execute("SELECT stock FROM products WHERE barcode=?", (barcode,))
                        stock_result = c.fetchone()
                        conn.close()
                        
                        if stock_result:
                            available_stock = stock_result[0]
                            if new_qty > available_stock:
                                messagebox.showwarning("Stock Limit", 
                                    f"Only {available_stock} units available in stock!")
                                entry.destroy()
                                self.barcode_entry.focus_set()
                                return
                    except Exception as e:
                        print(f"Stock check error: {e}")
                    
                    # Update quantity
                    cart_item['qty'] = new_qty
                    cart_item['total'] = new_qty * cart_item['price'] * (1 - cart_item['discount']/100)
                
                # Refresh display
                self.update_totals()
                self.refresh_cart_display()
                
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number")
            finally:
                entry.destroy()
                self.barcode_entry.focus_set()
        
        def cancel_edit(event=None):
            """Cancel editing"""
            entry.destroy()
            self.barcode_entry.focus_set()
        
        # Bind events
        entry.bind('<Return>', save_edit)
        entry.bind('<Escape>', cancel_edit)
        entry.bind('<FocusOut>', save_edit)  # Save when clicking away
    
    def update_totals(self, event=None):
        """Update all totals"""
        # Calculate subtotal
        self.subtotal = sum(item['total'] for item in self.cart)
        
        # Apply cart discount
        self.discount_total = self.subtotal * (self.cart_discount_percent / 100)
        
        # Calculate taxable amount
        taxable = self.subtotal - self.discount_total
        
        # Calculate tax
        self.tax_total = taxable * self.tax_rate
        
        # Get other charges from entry field
        try:
            self.other_charges = float(self.other_charges_var.get() or 0)
        except ValueError:
            self.other_charges = 0
            self.other_charges_var.set("0.00")
        
        # Calculate grand total (including other charges)
        self.total = taxable + self.tax_total + self.other_charges
        
        # Update labels
        self.subtotal_label.config(text=f"{CURRENCY_SYMBOL}{self.subtotal:.2f}")
        self.discount_label.config(text=f"-{CURRENCY_SYMBOL}{self.discount_total:.2f}")
        self.tax_label.config(text=f"{CURRENCY_SYMBOL}{self.tax_total:.2f}")
        self.other_charges_display.config(text=f"{CURRENCY_SYMBOL}{self.other_charges:.2f}")
        self.total_label.config(text=f"{CURRENCY_SYMBOL}{self.total:.2f}")
    
    def update_other_charges(self, event=None):
        """Update other charges and recalculate grand total"""
        self.update_totals()
        self.barcode_entry.focus_set()  # Return focus to barcode field after updating other charges
    
    def load_logo(self):
        """Load and resize logo image"""
        try:
            # Try multiple possible locations
            possible_paths = [
                os.path.join(parent_dir, 'logo.png'),  # D:\Urban_Pulse_pos\logo.png
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logo.png'),  # Alternative
                os.path.join(os.getcwd(), 'logo.png'),  # Current working directory
                'D:\\Urban_Pulse_pos\\logo.png'  # Direct path as last resort
            ]
        
            logo_path = None
            for path in possible_paths:
                print(f"Checking: {path}")  # Debug
                if os.path.exists(path):
                    logo_path = path
                    print(f"Found logo at: {logo_path}")
                    break
        
            if logo_path:
                img = Image.open(logo_path)
                img = img.resize((35, 35), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
                return self.logo_image
            else:
                print("Logo not found in any location")
            
        except Exception as e:
            print(f"Could not load logo: {e}")
        return None

    def create_widgets(self):
        # Main container
        main_container = tk.Frame(self.root, bg='#f0f2f5')
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header Frame - reduced height
        header = tk.Frame(main_container, bg='#2c3e50', height=50)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # Try to load and add logo
        logo = self.load_logo()
        if logo:
            logo_label = tk.Label(header, image=logo, bg='#2c3e50')
            logo_label.pack(side=tk.LEFT, padx=(10, 5), pady=7)
        
        tk.Label(header, text="Urban Pulse POS", fg='white', bg='#2c3e50', 
                font=('Arial', 18, 'bold')).pack(side=tk.LEFT, padx=5, pady=10)
        
        # Date display
        date_label = tk.Label(header, text=f"📅 {self.current_business_date}", 
                              fg='white', bg='#2c3e50', font=('Arial', 11, 'bold'))
        date_label.pack(side=tk.LEFT, expand=True, anchor='center')
        
        tk.Label(header, text=f"👤 User: {self.user['username']} ({self.user['role']})", 
                fg='white', bg='#2c3e50', font=('Arial', 11)).pack(side=tk.RIGHT, padx=20)
        
        # Input Frame - reduced height
        input_frame = tk.Frame(main_container, bg='#ecf0f1', height=200)
        input_frame.pack(fill=tk.X, pady=3)
        input_frame.pack_propagate(False)
        
        # Barcode row
        tk.Label(input_frame, text="📷 Scan Barcode:", bg='#ecf0f1', font=('Arial', 11, 'bold')).grid(row=0, column=0, padx=8, pady=3, sticky='e')
        self.barcode_entry = tk.Entry(input_frame, font=('Arial', 13), width=25, relief='solid', bd=2)
        self.barcode_entry.grid(row=0, column=1, padx=5, pady=3, sticky='w')
        self.barcode_entry.bind('<Return>', self.cart_manager.add_to_cart)
        self.barcode_entry.focus_set()
        
        tk.Button(input_frame, text="➕ Add Manual", command=self.cart_manager.manual_add, 
                 bg='#3498db', fg='white', font=('Arial', 9), cursor='hand2', height=1
                 ).grid(row=0, column=2, padx=5)
        
        tk.Button(input_frame, text="🏷️ Apply Discount", command=self.discount_handler.apply_cart_discount, 
                 bg='#f39c12', fg='white', font=('Arial', 9), cursor='hand2', height=1
                 ).grid(row=0, column=3, padx=5)
        
        self.discount_info = tk.Label(input_frame, text="", bg='#ecf0f1', fg='#e74c3c', font=('Arial', 9, 'bold'))
        self.discount_info.grid(row=0, column=4, padx=5, pady=3, sticky='w')
        
        # Create a frame for the three containers
        containers_frame = tk.Frame(input_frame, bg='#ecf0f1')
        containers_frame.grid(row=1, column=0, columnspan=5, pady=5, sticky='ew')
        containers_frame.grid_columnconfigure(0, weight=1)
        containers_frame.grid_columnconfigure(1, weight=1)
        containers_frame.grid_columnconfigure(2, weight=1)
        containers_frame.grid_columnconfigure(3, weight=1)
        
        # ============ MENU CONTAINER ============
        menu_container = tk.Frame(containers_frame, bg='white', relief=tk.RIDGE, bd=2)
        menu_container.grid(row=0, column=0, padx=5, sticky='nsew')
        
        # Content
        menu_content = tk.Frame(menu_container, bg='white', padx=8, pady=5)
        menu_content.pack(fill=tk.BOTH, expand=True)
        
        # Create menu button inside container
        self.menu_btn = tk.Menubutton(menu_content, text="Menu ▼", 
                                      bg='#2c3e50', fg='white',
                                      font=('Arial', 15, 'bold'), relief=tk.RAISED,
                                      width=10, height=4, cursor='hand2')
        self.menu_btn.pack(pady=5)
        
        # Create dropdown menu
        menu = tk.Menu(self.menu_btn, tearoff=0)
        self.menu_btn.config(menu=menu)
        
        # Add menu items
        menu.add_command(label="📦 Products", command=self.navigation.manage_products)
        menu.add_command(label="👥 Customers", command=self.navigation.manage_customers)
        menu.add_command(label="🏭 Suppliers", command=self.navigation.open_supplier_manager)
        menu.add_command(label="💰 Tax Settings", command=self.navigation.open_tax_settings)
        menu.add_separator()
        menu.add_command(label="🏷️ Discounts", command=self.navigation.open_discount_manager)
        menu.add_command(label="📊 Daily Report", command=self.navigation.open_daily_report)
        menu.add_command(label="⭐ Points", command=self.navigation.points_manager)
        menu.add_separator()
        menu.add_command(label="🧾 Receipts", command=self.navigation.receipt_history)
        menu.add_command(label="🆔 Membership", command=self.navigation.open_membership_manager)
        menu.add_command(label="💰 Recovery", command=self.navigation.open_credit_manager)
        menu.add_command(label="📅 Day Open/Close", command=self.navigation.open_day_manager)
        menu.add_separator()
        menu.add_command(label="📊 Accounts", command=self.navigation.open_accounting)
        menu.add_command(label="📁 Categories", command=self.navigation.open_category_manager)
        menu.add_command(label="📈 Stock Summary", command=self.navigation.open_stock_summary)
        menu.add_command(label="📒 SKU Ledger", command=self.navigation.open_sku_ledger)
        menu.add_command(label="📋 Stock History", command=self.navigation.open_stock_history)

        # ============ CASH/WALK-IN CONTAINER ============
        cash_container = tk.Frame(containers_frame, bg='white', relief=tk.RIDGE, bd=2)
        cash_container.grid(row=0, column=1, padx=5, sticky='nsew')
        
        # Green header - reduced height
        cash_header = tk.Frame(cash_container, bg='#27ae60', height=25)
        cash_header.pack(fill=tk.X)
        cash_header.pack_propagate(False)
        tk.Label(cash_header, text="💵 CASH / WALK-IN", fg='white', bg='#27ae60',
                font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Content - reduced padding
        cash_content = tk.Frame(cash_container, bg='white', padx=8, pady=5)
        cash_content.pack(fill=tk.BOTH, expand=True)
        
        # Customer row
        cash_row1 = tk.Frame(cash_content, bg='white')
        cash_row1.pack(fill=tk.X, pady=2)
        tk.Label(cash_row1, text="Customer:", bg='white', font=('Arial', 9, 'bold'),
                width=8, anchor='w').pack(side=tk.LEFT)
        self.cash_customer_label = tk.Label(cash_row1, text="Not Selected", bg='white', 
                                           font=('Arial', 8), fg='#7f8c8d')
        self.cash_customer_label.pack(side=tk.LEFT, padx=3)
        
        # Button row
        cash_row2 = tk.Frame(cash_content, bg='white')
        cash_row2.pack(fill=tk.X, pady=3)
        tk.Button(cash_row2, text="Select Customer", command=self.select_cash_customer,
                 bg='#27ae60', fg='white', font=('Arial', 8, 'bold'), 
                 width=14, height=1, cursor='hand2').pack()
        
        # Radio button
        cash_row3 = tk.Frame(cash_content, bg='white')
        cash_row3.pack(fill=tk.X, pady=3)
        cash_radio = tk.Radiobutton(cash_row3, text="Cash Sale", variable=self.sale_type, 
                                    value="cash", bg='white', font=('Arial', 8, 'bold'),
                                    selectcolor='white', command=self.update_checkout_state)
        cash_radio.pack()
        
        # ============ CREDIT SALE CONTAINER ============
        credit_container = tk.Frame(containers_frame, bg='white', relief=tk.RIDGE, bd=2)
        credit_container.grid(row=0, column=2, padx=5, sticky='nsew')
        
        # Orange header - reduced height
        credit_header = tk.Frame(credit_container, bg='#e67e22', height=25)
        credit_header.pack(fill=tk.X)
        credit_header.pack_propagate(False)
        tk.Label(credit_header, text="📝 CREDIT SALE (MEMBERS ONLY)", fg='white', bg='#e67e22',
                font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Content - reduced padding
        credit_content = tk.Frame(credit_container, bg='white', padx=8, pady=5)
        credit_content.pack(fill=tk.BOTH, expand=True)
        
        # Member row
        credit_row1 = tk.Frame(credit_content, bg='white')
        credit_row1.pack(fill=tk.X, pady=2)
        tk.Label(credit_row1, text="Member:", bg='white', font=('Arial', 9, 'bold'),
                width=8, anchor='w').pack(side=tk.LEFT)
        self.credit_member_label = tk.Label(credit_row1, text="Not Selected", bg='white', 
                                           font=('Arial', 8), fg='#7f8c8d')
        self.credit_member_label.pack(side=tk.LEFT, padx=3)
        
        # Button row
        credit_row2 = tk.Frame(credit_content, bg='white')
        credit_row2.pack(fill=tk.X, pady=3)
        tk.Button(credit_row2, text="Select Member", command=self.select_credit_member,
                 bg='#e67e22', fg='white', font=('Arial', 8, 'bold'), 
                 width=14, height=1, cursor='hand2').pack()
        
        # Radio button
        credit_row3 = tk.Frame(credit_content, bg='white')
        credit_row3.pack(fill=tk.X, pady=3)
        credit_radio = tk.Radiobutton(credit_row3, text="Credit Sale", variable=self.sale_type, 
                                      value="credit", bg='white', font=('Arial', 8, 'bold'),
                                      selectcolor='white', command=self.update_checkout_state)
        credit_radio.pack()
        
        # ============ CUSTOMER INFO CONTAINER ============
        info_container = tk.Frame(containers_frame, bg='white', relief=tk.RIDGE, bd=2)
        info_container.grid(row=0, column=3, padx=5, sticky='nsew')
        
        # Blue header - reduced height
        info_header = tk.Frame(info_container, bg='#3498db', height=25)
        info_header.pack(fill=tk.X)
        info_header.pack_propagate(False)
        tk.Label(info_header, text="👤 CUSTOMER INFO", fg='white', bg='#3498db',
                font=('Arial', 10, 'bold')).pack(expand=True)
        
        # Content - reduced padding
        info_content = tk.Frame(info_container, bg='white', padx=8, pady=5)
        info_content.pack(fill=tk.BOTH, expand=True)
        
        # Name row
        name_row = tk.Frame(info_content, bg='white')
        name_row.pack(fill=tk.X, pady=2)
        tk.Label(name_row, text="Name:", bg='white', font=('Arial', 9, 'bold'),
                width=6, anchor='w').pack(side=tk.LEFT)
        self.customer_name_label = tk.Label(name_row, textvariable=self.display_customer_name,
                                           bg='white', font=('Arial', 8), fg='#2c3e50')
        self.customer_name_label.pack(side=tk.LEFT, padx=3)
        
        # Type row
        type_row = tk.Frame(info_content, bg='white')
        type_row.pack(fill=tk.X, pady=2)
        tk.Label(type_row, text="Type:", bg='white', font=('Arial', 9, 'bold'),
                width=6, anchor='w').pack(side=tk.LEFT)
        self.customer_type_label = tk.Label(type_row, textvariable=self.display_customer_type,
                                           bg='white', font=('Arial', 8), fg='#2c3e50')
        self.customer_type_label.pack(side=tk.LEFT, padx=3)
        
        # Points row
        points_row = tk.Frame(info_content, bg='white')
        points_row.pack(fill=tk.X, pady=2)
        tk.Label(points_row, text="Points:", bg='white', font=('Arial', 9, 'bold'),
                width=6, anchor='w').pack(side=tk.LEFT)
        self.points_display_label = tk.Label(points_row, textvariable=self.display_loyalty_points,
                                            bg='white', font=('Arial', 8), fg='#e67e22')
        self.points_display_label.pack(side=tk.LEFT, padx=3)
        
        # ID row
        id_row = tk.Frame(info_content, bg='white')
        id_row.pack(fill=tk.X, pady=2)
        tk.Label(id_row, text="ID:", bg='white', font=('Arial', 9, 'bold'),
                width=6, anchor='w').pack(side=tk.LEFT)
        self.customer_id_label = tk.Label(id_row, text="-", bg='white', 
                                         font=('Arial', 8), fg='#7f8c8d')
        self.customer_id_label.pack(side=tk.LEFT, padx=3)
        
        # Content area (Treeview + Bottom)
        content_frame = tk.Frame(main_container, bg='#f0f2f5')
        content_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=3)
        
        # Cart Treeview
        tree_frame = tk.Frame(content_frame, bg='#f0f2f5')
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=3)
        
        columns = ('#', 'Barcode', 'Product', f'Price ({CURRENCY_SYMBOL})', 'Qty', 'Disc%', f'Total ({CURRENCY_SYMBOL})')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=8)
        
        col_widths = {'#': 40, 'Barcode': 120, 'Product': 250, f'Price ({CURRENCY_SYMBOL})': 90, 
                     'Qty': 60, 'Disc%': 70, f'Total ({CURRENCY_SYMBOL})': 110}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80), anchor='center')
        
        # Scrollbar for treeview
        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom Frame - reduced height
        bottom_frame = tk.Frame(content_frame, bg='#ecf0f1', height=160)
        bottom_frame.pack(fill=tk.X, pady=3)
        bottom_frame.pack_propagate(False)
        
        # Left side - Management Menu
        left_panel = tk.Frame(bottom_frame, bg='#ecf0f1')
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8)
        
        # Essential buttons (always visible)
        essential_frame = tk.Frame(left_panel, bg='#ecf0f1')
        essential_frame.pack(side=tk.TOP, fill=tk.X, pady=2)
        
        tk.Button(essential_frame, text="❌ Remove", command=self.cart_manager.remove_item,
                 bg='#e74c3c', fg='white', font=('Arial', 9, 'bold'),
                 width=8, height=1, cursor='hand2', relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=2)
        
        tk.Button(essential_frame, text="🗑️ Clear Cart", command=self.cart_manager.clear_cart,
                 bg='#95a5a6', fg='white', font=('Arial', 9, 'bold'),
                 width=8, height=1, cursor='hand2', relief=tk.RAISED, bd=1).pack(side=tk.LEFT, padx=2)
        
        # Center panel - Checkout Button
        center_panel = tk.Frame(bottom_frame, bg='#ecf0f1', width=180)
        center_panel.pack(side=tk.LEFT, fill=tk.Y, padx=8)
        center_panel.pack_propagate(False)
        
        # Checkout Button - smaller
        self.checkout_btn = tk.Button(center_panel, text="💰 CHECKOUT", command=self.payment_handler.process_checkout,
                                      bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                                      width=10, height=1, cursor='hand2', bd=2, relief=tk.RAISED)
        self.checkout_btn.pack(expand=True)
        
        # Right panel - ALL TOTALS IN ONE PLACE with reduced spacing
        right_panel = tk.Frame(bottom_frame, bg='#ecf0f1', width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=8)
        right_panel.pack_propagate(False)
        
        # Totals display - ALL TOTALS TOGETHER with minimal spacing
        totals_frame = tk.Frame(right_panel, bg='#ffffff', relief=tk.RIDGE, bd=1)
        totals_frame.pack(fill=tk.X, pady=2)
        
        # Subtotal - minimal padding
        subtotal_frame = tk.Frame(totals_frame, bg='#ffffff')
        subtotal_frame.pack(fill=tk.X, pady=1, padx=10)
        tk.Label(subtotal_frame, text="SUB TOTAL", bg='#ffffff', font=('Arial', 9, 'bold'), 
                fg='#2c3e50').pack(side=tk.LEFT)
        self.subtotal_label = tk.Label(subtotal_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ffffff', 
                                       font=('Arial', 10, 'bold'), fg='#27ae60')
        self.subtotal_label.pack(side=tk.RIGHT)
        
        ttk.Separator(totals_frame, orient='horizontal').pack(fill=tk.X, padx=8, pady=1)
        
        # Discount - minimal padding
        discount_frame = tk.Frame(totals_frame, bg='#ffffff')
        discount_frame.pack(fill=tk.X, pady=1, padx=10)
        tk.Label(discount_frame, text="DISCOUNT", bg='#ffffff', font=('Arial', 9, 'bold'), 
                fg='#2c3e50').pack(side=tk.LEFT)
        self.discount_label = tk.Label(discount_frame, text=f"-{CURRENCY_SYMBOL}0.00", bg='#ffffff', 
                                       fg='#e74c3c', font=('Arial', 10, 'bold'))
        self.discount_label.pack(side=tk.RIGHT)
        
        ttk.Separator(totals_frame, orient='horizontal').pack(fill=tk.X, padx=8, pady=1)
        
        # Tax (GST) - minimal padding
        tax_frame = tk.Frame(totals_frame, bg='#ffffff')
        tax_frame.pack(fill=tk.X, pady=1, padx=10)
        tk.Label(tax_frame, text=f"GST ({int(self.tax_rate*100)}%)", bg='#ffffff', 
                font=('Arial', 9, 'bold'), fg='#2c3e50').pack(side=tk.LEFT)
        self.tax_label = tk.Label(tax_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ffffff', 
                                  font=('Arial', 10, 'bold'), fg='#e67e22')
        self.tax_label.pack(side=tk.RIGHT)
        
        ttk.Separator(totals_frame, orient='horizontal').pack(fill=tk.X, padx=8, pady=1)
        
        # Other Charges - MANUAL INPUT FIELD with minimal padding
        other_frame = tk.Frame(totals_frame, bg='#ffffff')
        other_frame.pack(fill=tk.X, pady=1, padx=10)
        
        left_other_frame = tk.Frame(other_frame, bg='#ffffff')
        left_other_frame.pack(side=tk.LEFT)
        tk.Label(left_other_frame, text="OTHER CHARGES", bg='#ffffff', font=('Arial', 9, 'bold'), 
                fg='#2c3e50').pack(anchor='w')
        
        right_other_frame = tk.Frame(other_frame, bg='#ffffff')
        right_other_frame.pack(side=tk.RIGHT)
        
        # Entry for other charges - smaller
        self.other_charges_var = tk.StringVar(value="0.00")
        self.other_charges_entry = tk.Entry(right_other_frame, textvariable=self.other_charges_var, 
                                            width=8, font=('Arial', 9), justify='right',
                                            relief='solid', bd=1)
        self.other_charges_entry.pack(side=tk.LEFT)
        self.other_charges_entry.bind('<Return>', self.update_other_charges)
        self.other_charges_entry.bind('<FocusOut>', self.update_other_charges)
        
        tk.Label(right_other_frame, text=CURRENCY_SYMBOL, bg='#ffffff', 
                font=('Arial', 9)).pack(side=tk.LEFT, padx=1)
        
        # Display for other charges
        self.other_charges_display = tk.Label(right_other_frame, text=f"{CURRENCY_SYMBOL}0.00", bg='#ffffff', 
                                             font=('Arial', 10, 'bold'), fg='#3498db')
        
        ttk.Separator(totals_frame, orient='horizontal').pack(fill=tk.X, padx=8, pady=2)
        
        # GRAND TOTAL - PROMINENT but compact
        grand_total_frame = tk.Frame(totals_frame, bg='#2980b9', height=35)
        grand_total_frame.pack(fill=tk.X, pady=2, padx=0)
        grand_total_frame.pack_propagate(False)
        
        tk.Label(grand_total_frame, text="GRAND TOTAL", fg='white', bg='#2980b9', 
                font=('Arial', 11, 'bold')).pack(side=tk.LEFT, padx=10)
        self.total_label = tk.Label(grand_total_frame, text=f"{CURRENCY_SYMBOL}0.00", fg='white', bg='#2980b9', 
                                    font=('Arial', 14, 'bold'))
        self.total_label.pack(side=tk.RIGHT, padx=10)
        
        # Initialize button states
        self.update_checkout_state()
    
    def select_cash_customer(self):
        """Select customer for cash sale"""
        try:
            from customer_manager import SelectCustomer
            selector = SelectCustomer(self.root)
            self.root.wait_window(selector.window)
            
            if selector.selected_customer:
                self.current_customer = selector.selected_customer
                self.cash_customer_label.config(text=f"Customer: {selector.selected_customer['name']}", 
                                               fg='#27ae60')
                
                # Update the info display
                self.display_customer_name.set(selector.selected_customer['name'])
                self.display_customer_type.set("Cash Customer")
                points = selector.selected_customer.get('points', 0)
                self.display_loyalty_points.set(str(points))
                self.customer_id_label.config(text=selector.selected_customer.get('id', '-'))
                
                # Auto-select cash mode
                self.sale_type.set("cash")
            else:
                self.current_customer = None
                self.cash_customer_label.config(text="Customer: Not Selected", fg='#7f8c8d')
                self.display_customer_name.set("Not Selected")
                self.display_customer_type.set("Cash Customer")
                self.display_loyalty_points.set("0")
                self.customer_id_label.config(text="-")
        except ImportError:
            # Mock customer selection
            self.current_customer = {'name': 'Walk-in Customer', 'id': 'C001', 'points': 0}
            self.cash_customer_label.config(text="Customer: Walk-in Customer", fg='#27ae60')
            self.display_customer_name.set("Walk-in Customer")
            self.display_customer_type.set("Cash Customer")
            self.display_loyalty_points.set("0")
            self.customer_id_label.config(text="C001")
            self.sale_type.set("cash")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select customer: {str(e)}")
        
        self.update_checkout_state()
        self.barcode_entry.focus_set()  # Return focus to barcode field
    
    def select_credit_member(self):
        """Select member for credit sale"""
        try:
            from membership_manager import SelectMemberForCredit
            selector = SelectMemberForCredit(self.root)
            self.root.wait_window(selector.window)
            
            if selector.selected_member:
                self.current_member = selector.selected_member
                self.credit_member_label.config(text=f"Member: {selector.selected_member['name']}", 
                                               fg='#e67e22')
                
                # Update the info display
                self.display_customer_name.set(selector.selected_member['name'])
                self.display_customer_type.set("Credit Member")
                points = selector.selected_member.get('points', 0)
                self.display_loyalty_points.set(str(points))
                self.customer_id_label.config(text=selector.selected_member.get('id', '-'))
                
                # Auto-select credit mode
                self.sale_type.set("credit")
            else:
                self.current_member = None
                self.credit_member_label.config(text="Member: Not Selected", fg='#7f8c8d')
                self.display_customer_name.set("Not Selected")
                self.display_customer_type.set("Credit Member")
                self.display_loyalty_points.set("0")
                self.customer_id_label.config(text="-")
        except ImportError:
            # Mock member selection
            self.current_member = {'name': 'Premium Member', 'id': 'M001', 'points': 500}
            self.credit_member_label.config(text="Member: Premium Member", fg='#e67e22')
            self.display_customer_name.set("Premium Member")
            self.display_customer_type.set("Credit Member")
            self.display_loyalty_points.set("500")
            self.customer_id_label.config(text="M001")
            self.sale_type.set("credit")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to select member: {str(e)}")
        
        self.update_checkout_state()
        self.barcode_entry.focus_set()  # Return focus to barcode field
    
    def update_checkout_state(self):
        """Enable/disable checkout based on selections"""
        
        # Reset display if no customer/member is selected for the current mode
        if self.sale_type.get() == "cash":
            if not self.current_customer:
                self.display_customer_name.set("Not Selected")
                self.display_customer_type.set("Cash Customer")
                self.display_loyalty_points.set("0")
        else:
            if not self.current_member:
                self.display_customer_name.set("Not Selected")
                self.display_customer_type.set("Credit Member")
                self.display_loyalty_points.set("0")
        
        if self.sale_type.get() == "cash":
            # Cash sale - always enabled (customer optional)
            self.checkout_btn.config(state=tk.NORMAL, bg='#27ae60')
            # Highlight cash section
            self.cash_customer_label.config(fg='#27ae60' if self.current_customer else '#7f8c8d')
            self.credit_member_label.config(fg='#7f8c8d')
        else:
            # Credit sale - require member
            if self.current_member:
                self.checkout_btn.config(state=tk.NORMAL, bg='#27ae60')
                self.credit_member_label.config(fg='#e67e22')
            else:
                self.checkout_btn.config(state=tk.DISABLED, bg='#95a5a6')
                self.credit_member_label.config(fg='#7f8c8d')
            self.cash_customer_label.config(fg='#7f8c8d')

# For testing
if __name__ == "__main__":
    test_user = {'username': 'admin', 'role': 'admin'}
    app = UrbanPulsePOS(test_user)