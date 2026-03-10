# product_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime
from utils import CURRENCY_SYMBOL, format_currency, show_error, show_success, ask_yes_no, setup_enter_navigation
from fpdf import FPDF  # Add this import for PDF generation

class AddEditProduct:
    def __init__(self, parent, title, prod_id=None):
        self.prod_id = prod_id
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("500x480")  # Slightly taller for better layout
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 500) // 2
        y = (self.window.winfo_screenheight() - 480) // 2
        self.window.geometry(f"500x480+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Variables
        self.barcode = tk.StringVar()
        self.name = tk.StringVar()
        self.price = tk.StringVar()
        self.cost = tk.StringVar()
        self.stock = tk.StringVar()
        self.supplier = tk.StringVar()
        self.reorder = tk.StringVar()
        self.category = tk.StringVar()
        self.category_id = None
        
        # Load suppliers for dropdown
        self.suppliers = []
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, company_name FROM suppliers ORDER BY company_name")
        self.suppliers = c.fetchall()
        conn.close()
        
        # Load categories for dropdown
        self.load_categories()
        
        # If editing, load data
        if prod_id:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute('''SELECT p.barcode, p.name, p.price, p.cost_price, p.stock, 
                                p.supplier_id, p.reorder_level, c.id, c.category_name
                         FROM products p
                         LEFT JOIN categories c ON p.category_id = c.id
                         WHERE p.id=?''', (prod_id,))
            data = c.fetchone()
            conn.close()
            if data:
                self.barcode.set(data[0])
                self.name.set(data[1])
                self.price.set(str(data[2]))
                self.cost.set(str(data[3]))
                self.stock.set(str(data[4]))
                self.reorder.set(str(data[6]))
                self.category_id = data[7]
                
                if data[8]:
                    self.category.set(data[8])
                
                # Find supplier name
                for sid, sname in self.suppliers:
                    if sid == data[5]:
                        self.supplier.set(sname)
                        break
        
        self.create_widgets()
    
    def load_categories(self):
        """Load ONLY sub-categories (categories with a parent) - show only child name"""
        try:
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            c.execute('''
                SELECT c1.id, c1.category_name
                FROM categories c1
                WHERE c1.parent_id IS NOT NULL
                ORDER BY c1.category_name
            ''')
            
            self.categories = c.fetchall()
            conn.close()
            
            self.category_names = [cat[1] for cat in self.categories]
            self.category_lookup = {cat[1]: cat[0] for cat in self.categories}
            
            if not self.category_names:
                self.category_names = ["No sub-categories available"]
                self.categories = [(0, "No sub-categories available")]
                
        except Exception as e:
            print(f"Error loading categories: {e}")
            self.categories = []
            self.category_names = ["Error loading categories"]
            self.category_lookup = {}
    
    def on_category_key(self, event):
        """Auto-complete and filter categories as user types"""
        typed = self.category_combo.get()
        
        if event.keysym in ('Up', 'Down', 'Left', 'Right', 'Return', 'Tab', 'Shift_L', 'Shift_R', 
                            'Control_L', 'Control_R', 'Alt_L', 'Alt_R', 'Escape'):
            return
        
        if typed == '':
            self.category_combo['values'] = self.category_names
            return
        
        matches = [cat for cat in self.category_names if cat.lower().startswith(typed.lower())]
        
        if not matches:
            matches = [cat for cat in self.category_names if typed.lower() in cat.lower()]
        
        if matches:
            self.category_combo['values'] = matches
            
            for cat in matches:
                if cat.lower() == typed.lower():
                    self.category_combo.set(cat)
                    self.category_combo.icursor(tk.END)
                    break
            
            self.category_combo.event_generate('<Down>')
        else:
            self.category_combo['values'] = ['No matching categories']
    
    def adjust_stock(self):
        """Open stock adjustment dialog with history tracking"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Adjust Stock")
        dialog.geometry("400x320")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 320) // 2
        dialog.geometry(f"400x320+{x}+{y}")
        
        tk.Label(dialog, text="STOCK ADJUSTMENT", font=('Arial', 12, 'bold'),
                bg='#3498db', fg='white').pack(fill=tk.X, pady=5)
        
        frame = tk.Frame(dialog, bg='#f9f9f9', padx=15, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text=f"Product: {self.name.get()}", font=('Arial', 10, 'bold'),
                bg='#f9f9f9').pack(anchor='w')
        tk.Label(frame, text=f"Current Stock: {self.stock.get()}", 
                bg='#f9f9f9').pack(anchor='w', pady=5)
        
        tk.Label(frame, text="New Stock:", bg='#f9f9f9').pack(anchor='w')
        new_stock_var = tk.StringVar()
        new_stock_entry = tk.Entry(frame, textvariable=new_stock_var, width=15,
                                   font=('Arial', 10), relief='solid', bd=1)
        new_stock_entry.pack(pady=5)
        new_stock_entry.focus()
        
        tk.Label(frame, text="Reason for adjustment:", bg='#f9f9f9').pack(anchor='w')
        reason_combo = ttk.Combobox(frame, values=['Physical count', 'Damaged', 'Expired', 
                                                   'Found in warehouse', 'Correction', 'Stock take', 'Other'],
                                   width=25)
        reason_combo.pack(pady=5)
        reason_combo.set('Physical count')
        
        tk.Label(frame, text="Notes (optional):", bg='#f9f9f9').pack(anchor='w')
        notes_text = tk.Text(frame, height=2, width=30, font=('Arial', 9), relief='solid', bd=1)
        notes_text.pack(pady=5)
        
        def save_adjustment():
            try:
                new_stock = int(new_stock_var.get())
                if new_stock < 0:
                    show_error("Stock cannot be negative")
                    return
                
                old_stock = int(self.stock.get())
                
                # Update the stock variable
                self.stock.set(str(new_stock))
                
                # Record the adjustment in history
                self.record_stock_adjustment(
                    product_id=self.prod_id,
                    product_name=self.name.get(),
                    old_stock=old_stock,
                    new_stock=new_stock,
                    reason=reason_combo.get(),
                    notes=notes_text.get('1.0', tk.END).strip()
                )
                
                show_success(f"Stock adjusted from {old_stock} to {new_stock}")
                dialog.destroy()
                
            except ValueError:
                show_error("Please enter a valid number")
        
        tk.Button(frame, text="Update Stock", command=save_adjustment,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 width=15, cursor='hand2').pack(pady=10)
    
    def record_stock_adjustment(self, product_id, product_name, old_stock, new_stock, reason, notes=''):
        """Record stock adjustment in history"""
        adjustment = new_stock - old_stock
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Create table if not exists
        c.execute('''CREATE TABLE IF NOT EXISTS stock_adjustments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            product_name TEXT,
            old_stock INTEGER,
            new_stock INTEGER,
            adjustment INTEGER,
            reason TEXT,
            adjusted_by TEXT,
            adjustment_date DATETIME,
            notes TEXT,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )''')
        
        # Get current user (from somewhere - defaulting to 'admin')
        from main import get_current_user
        try:
            username = get_current_user()['username']
        except:
            username = 'admin'
        
        c.execute('''INSERT INTO stock_adjustments 
                    (product_id, product_name, old_stock, new_stock, adjustment, 
                     reason, adjusted_by, adjustment_date, notes)
                    VALUES (?,?,?,?,?,?,?,?,?)''',
                  (product_id, product_name, old_stock, new_stock, adjustment,
                   reason, username, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), notes))
        
        conn.commit()
        conn.close()
        print(f"✅ Stock adjustment recorded: {product_name} {old_stock} → {new_stock} ({adjustment:+d})")
    
    def create_widgets(self):
        # Form fields
        fields = [
            ("Barcode *:", self.barcode),
            ("Name *:", self.name),
            (f"Price ({CURRENCY_SYMBOL}) *:", self.price),
            (f"Cost Price ({CURRENCY_SYMBOL}):", self.cost),
            ("Reorder Level:", self.reorder),
        ]
        
        entries = []
        row = 0
        for i, (label, var) in enumerate(fields):
            tk.Label(self.window, text=label).grid(row=row, column=0, padx=5, pady=5, sticky='e')
            entry = tk.Entry(self.window, textvariable=var, width=25)
            entry.grid(row=row, column=1, padx=5, pady=5)
            entries.append(entry)
            row += 1
        
        # Stock field - SPECIAL HANDLING
        tk.Label(self.window, text="Stock:").grid(row=row, column=0, padx=5, pady=5, sticky='e')
        
        if self.prod_id:  # EDITING existing product
            # Read-only stock display
            stock_label = tk.Label(self.window, text=self.stock.get(), 
                                  font=('Arial', 10, 'bold'), bg='#f0f0f0',
                                  width=20, anchor='w', relief='sunken', bd=1)
            stock_label.grid(row=row, column=1, padx=5, pady=5, sticky='w')
            
            # Adjust stock button
            adjust_btn = tk.Button(self.window, text="📦 Adjust Stock", 
                                  command=self.adjust_stock,
                                  bg='#3498db', fg='white', font=('Arial', 8, 'bold'),
                                  width=12, cursor='hand2')
            adjust_btn.grid(row=row, column=2, padx=5)
        else:  # NEW product
            stock_entry = tk.Entry(self.window, textvariable=self.stock, width=25)
            stock_entry.grid(row=row, column=1, padx=5, pady=5)
            entries.append(stock_entry)
        row += 1
        
        # Supplier dropdown
        tk.Label(self.window, text="Supplier:").grid(row=row, column=0, padx=5, pady=5, sticky='e')
        supplier_values = [s[1] for s in self.suppliers]
        supplier_combo = ttk.Combobox(self.window, textvariable=self.supplier, values=supplier_values, width=23)
        supplier_combo.grid(row=row, column=1, padx=5, pady=5)
        entries.append(supplier_combo)
        row += 1
        
        # Category dropdown
        tk.Label(self.window, text="Category:").grid(row=row, column=0, padx=5, pady=5, sticky='e')
        
        self.category_combo = ttk.Combobox(self.window, textvariable=self.category, 
                                           values=self.category_names, width=23)
        self.category_combo.grid(row=row, column=1, padx=5, pady=5)
        self.category_combo.bind('<KeyRelease>', self.on_category_key)
        entries.append(self.category_combo)
        row += 1
        
        # Note about required fields
        tk.Label(self.window, text="* Required fields", fg='red', font=('Arial', 8)).grid(row=row, column=0, columnspan=3, pady=5)
        row += 1
        
        # Setup Enter key navigation
        for j in range(len(entries)-1):
            setup_enter_navigation(entries[j], entries[j+1])
        if entries:
            setup_enter_navigation(entries[-1], self.save)
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.grid(row=row, column=0, columnspan=3, pady=10)
        
        tk.Button(btn_frame, text="Save", command=self.save, bg='green', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)
    
    def save(self):
        try:
            price = float(self.price.get())
            cost = float(self.cost.get() or 0)
            reorder = int(self.reorder.get() or 10)
        except ValueError:
            show_error("Price, cost, and reorder level must be numbers")
            return
        
        # For new products, validate stock
        if not self.prod_id:
            try:
                stock = int(self.stock.get() or 0)
                if stock < 0:
                    show_error("Stock cannot be negative")
                    return
            except ValueError:
                show_error("Stock must be a number")
                return
        else:
            # For existing products, stock is read-only - use current value
            try:
                stock = int(self.stock.get())
            except:
                stock = 0
        
        barcode = self.barcode.get().strip()
        name = self.name.get().strip()
        supplier_name = self.supplier.get().strip()
        category_child = self.category.get().strip()
        
        if not barcode or not name or not price:
            show_error("Barcode, name, and price are required")
            return
        
        # Find supplier ID
        supplier_id = None
        for sid, sname in self.suppliers:
            if sname == supplier_name:
                supplier_id = sid
                break
        
        # Find category ID
        category_id = None
        if category_child and category_child in self.category_lookup:
            category_id = self.category_lookup[category_child]
        elif self.category_id:
            category_id = self.category_id
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if self.prod_id:
            c.execute('''UPDATE products 
                        SET barcode=?, name=?, price=?, cost_price=?, stock=?, 
                            supplier_id=?, reorder_level=?, category_id=?
                        WHERE id=?''',
                      (barcode, name, price, cost, stock, supplier_id, reorder, category_id, self.prod_id))
            show_success("Product updated successfully!")
        else:
            try:
                c.execute('''INSERT INTO products 
                            (barcode, name, price, cost_price, stock, supplier_id, reorder_level, category_id) 
                            VALUES (?,?,?,?,?,?,?,?)''',
                          (barcode, name, price, cost, stock, supplier_id, reorder, category_id))
                show_success("Product added successfully!")
            except sqlite3.IntegrityError:
                show_error("Barcode already exists")
                conn.close()
                return
        
        conn.commit()
        conn.close()
        self.window.destroy()


# ============ NEW PDF CLASS (ADDED WITHOUT CHANGING EXISTING CODE) ============
class ProductPDF(FPDF):
    """Custom PDF class for product listing"""
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, 'Urban Pulse - Product List', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 8, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


class ProductManager:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Manage Products")
        self.window.geometry("1000x600")  # Increased width for PDF button
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 1000) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"1000x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_products()
    
    def create_widgets(self):
        # Top frame for search and buttons
        top_frame = tk.Frame(self.window)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search frame
        search_frame = tk.Frame(top_frame)
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.load_products())
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.focus()
        
        # ============ NEW PDF BUTTON ADDED HERE ============
        # Button frame on right
        btn_frame = tk.Frame(top_frame)
        btn_frame.pack(side=tk.RIGHT)
        
        tk.Button(btn_frame, text="Add Product", command=self.add_product, 
                 bg='green', fg='white', width=12).pack(side=tk.LEFT, padx=2)
        
        # PDF Button with dropdown menu
        self.pdf_btn = tk.Menubutton(btn_frame, text="📥 PDF ▼", 
                                     bg='#9b59b6', fg='white',
                                     font=('Arial', 9, 'bold'), relief=tk.RAISED,
                                     width=10, cursor='hand2')
        self.pdf_btn.pack(side=tk.LEFT, padx=2)
        
        # Create dropdown menu for PDF options
        pdf_menu = tk.Menu(self.pdf_btn, tearoff=0)
        self.pdf_btn.config(menu=pdf_menu)
        pdf_menu.add_command(label="📄 With Cost Price", command=lambda: self.export_to_pdf(include_cost=True))
        pdf_menu.add_command(label="📄 Without Cost Price", command=lambda: self.export_to_pdf(include_cost=False))
        # ============ END OF NEW PDF BUTTON ============
        
        # Treeview with Category column
        columns = ('ID', 'Barcode', 'Name', f'Price ({CURRENCY_SYMBOL})', 'Cost', 'Stock', 'Supplier', 'Category')
        self.tree = ttk.Treeview(self.window, columns=columns, show='headings', height=15)
        
        col_widths = {'ID': 40, 'Barcode': 100, 'Name': 150, f'Price ({CURRENCY_SYMBOL})': 70, 
                     'Cost': 70, 'Stock': 50, 'Supplier': 120, 'Category': 100}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths.get(col, 80))
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.tree.bind('<Double-Button-1>', lambda e: self.edit_product())
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        btn_frame = tk.Frame(self.window)
        btn_frame.pack(pady=5)
        
        tk.Button(btn_frame, text="Add", command=self.add_product, bg='green', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Edit", command=self.edit_product, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", command=self.delete_product, bg='red', fg='white', width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.load_products, width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=self.window.destroy, width=10).pack(side=tk.LEFT, padx=5)
        
        # Status bar at bottom
        status_frame = tk.Frame(self.window, bg='#ecf0f1', height=25)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(status_frame, text="", bg='#ecf0f1', anchor='w', padx=10)
        self.status_label.pack(side=tk.LEFT)
    
    def load_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        search = self.search_var.get().strip()
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        if search:
            c.execute('''SELECT p.id, p.barcode, p.name, p.price, p.cost_price, p.stock, 
                                s.company_name, c.category_name
                         FROM products p
                         LEFT JOIN suppliers s ON p.supplier_id = s.id
                         LEFT JOIN categories c ON p.category_id = c.id
                         WHERE p.name LIKE ? OR p.barcode LIKE ?
                         ORDER BY p.name''', (f'%{search}%', f'%{search}%'))
        else:
            c.execute('''SELECT p.id, p.barcode, p.name, p.price, p.cost_price, p.stock, 
                                s.company_name, c.category_name
                         FROM products p
                         LEFT JOIN suppliers s ON p.supplier_id = s.id
                         LEFT JOIN categories c ON p.category_id = c.id
                         ORDER BY p.name''')
        
        products = c.fetchall()
        conn.close()
        
        for prod in products:
            category_display = prod[7] if prod[7] else 'Uncategorized'
            
            self.tree.insert('', tk.END, values=(
                prod[0], prod[1], prod[2], 
                f"{CURRENCY_SYMBOL}{prod[3]:.2f}",
                f"{CURRENCY_SYMBOL}{prod[4]:.2f}",
                prod[5], prod[6] or 'No Supplier', category_display
            ))
        
        # Update status bar
        self.status_label.config(text=f"Total Products: {len(products)}")
    
    def add_product(self):
        AddEditProduct(self.window, "Add Product")
        self.load_products()
    
    def edit_product(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        prod_id = self.tree.item(selected[0])['values'][0]
        AddEditProduct(self.window, "Edit Product", prod_id)
        self.load_products()
    
    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            show_error("Select a product first")
            return
        
        if ask_yes_no("Delete this product?"):
            prod_id = self.tree.item(selected[0])['values'][0]
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id=?", (prod_id,))
            conn.commit()
            conn.close()
            self.load_products()
    
    # ============ NEW PDF EXPORT METHOD (ADDED WITHOUT CHANGING EXISTING CODE) ============
    def export_to_pdf(self, include_cost=True):
        """Export product list to PDF with option to include/exclude cost price"""
        try:
            # Ask for save location
            filename = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                title=f"Save Product List {'(with cost)' if include_cost else '(without cost)'}",
                initialfile=f"products_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            )
        
            if not filename:
                return
        
            # Get all products
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
        
            c.execute('''SELECT p.id, p.barcode, p.name, p.price, p.cost_price, p.stock, 
                                s.company_name, c.category_name
                         FROM products p
                         LEFT JOIN suppliers s ON p.supplier_id = s.id
                         LEFT JOIN categories c ON p.category_id = c.id
                         ORDER BY p.name''')
        
            products = c.fetchall()
            conn.close()
        
            if not products:
                show_error("No products to export")
                return
        
            # Create PDF - Landscape orientation for more columns
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
        
            # Title
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, 'Urban Pulse - Product List', 0, 1, 'C')
            pdf.set_font('Arial', '', 10)
            pdf.cell(0, 8, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'C')
            pdf.ln(5)
        
            # Set column widths based on include_cost (landscape A4 = 297mm width)
            if include_cost:
                col_widths = [12, 45, 75, 22, 22, 15, 45, 35]  # Product: 75, Supplier: 45, Category: 35
                # Total: 12+45+75+22+22+15+45+35 = 271mm
                headers = ['ID', 'Barcode', 'Product Name', 'Price', 'Cost', 'Stock', 'Supplier', 'Category']
            else:
                col_widths = [12, 45, 85, 25, 15, 45, 35]  # Without cost
                headers = ['ID', 'Barcode', 'Product Name', 'Price', 'Stock', 'Supplier', 'Category']
        
            # Print headers with background
            pdf.set_font('Arial', 'B', 9)
            pdf.set_fill_color(200, 200, 200)  # Light gray background
        
            for i, header in enumerate(headers):
                pdf.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
            pdf.ln()
        
            # Print data rows
            pdf.set_font('Arial', '', 8)
            fill = False
        
            for prod in products:
                # Check if new page needed
                if pdf.get_y() > 190:
                    pdf.add_page()
                    # Re-print headers
                    pdf.set_font('Arial', 'B', 9)
                    pdf.set_fill_color(200, 200, 200)
                    for i, header in enumerate(headers):
                        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
                    pdf.ln()
                    pdf.set_font('Arial', '', 8)
            
                # Alternate row colors
                if fill:
                    pdf.set_fill_color(240, 240, 240)
                else:
                    pdf.set_fill_color(255, 255, 255)
            
                # Format data
                prod_id = str(prod[0])
                barcode = prod[1]  # Full barcode (45 width enough)

                # Product name - show more characters
                name = prod[2] if len(prod[2]) <= 25 else prod[2][:22] + '...'

                price = f"{CURRENCY_SYMBOL}{prod[3]:.0f}"
                stock = str(prod[5])

                # Supplier - show more
                supplier = prod[6] if prod[6] else '-'
                if len(supplier) > 15:
                    supplier = supplier[:13] + '..'

                # Category - show more
                category = prod[7] if prod[7] else '-'
                if len(category) > 12:
                    category = category[:10] + '..'
            
                if include_cost:
                    cost = f"Rs.{prod[4]:.0f}"
                    pdf.cell(col_widths[0], 7, prod_id, 1, 0, 'C', fill)
                    pdf.cell(col_widths[1], 7, barcode, 1, 0, 'L', fill)
                    pdf.cell(col_widths[2], 7, name, 1, 0, 'L', fill)
                    pdf.cell(col_widths[3], 7, price, 1, 0, 'R', fill)
                    pdf.cell(col_widths[4], 7, cost, 1, 0, 'R', fill)
                    pdf.cell(col_widths[5], 7, stock, 1, 0, 'C', fill)
                    pdf.cell(col_widths[6], 7, supplier, 1, 0, 'L', fill)
                    pdf.cell(col_widths[7], 7, category, 1, 0, 'L', fill)
                else:
                    pdf.cell(col_widths[0], 7, prod_id, 1, 0, 'C', fill)
                    pdf.cell(col_widths[1], 7, barcode, 1, 0, 'L', fill)
                    pdf.cell(col_widths[2], 7, name, 1, 0, 'L', fill)
                    pdf.cell(col_widths[3], 7, price, 1, 0, 'R', fill)
                    pdf.cell(col_widths[4], 7, stock, 1, 0, 'C', fill)
                    pdf.cell(col_widths[5], 7, supplier, 1, 0, 'L', fill)
                    pdf.cell(col_widths[6], 7, category, 1, 0, 'L', fill)
            
                pdf.ln()
                fill = not fill
        
            # Add summary at the end
            pdf.ln(5)
            pdf.set_font('Arial', 'B', 11)
            pdf.cell(0, 8, f'Total Products: {len(products)}', 0, 1, 'L')
        
            # Calculate total value
            total_value = sum(p[3] * p[5] for p in products)
            pdf.cell(0, 8, f'Total Stock Value: Rs.{total_value:,.0f}', 0, 1, 'L')
        
            if include_cost:
                total_cost = sum(p[4] * p[5] for p in products)
                pdf.cell(0, 8, f'Total Cost Value: Rs.{total_cost:,.0f}', 0, 1, 'L')
                pdf.cell(0, 8, f'Potential Profit: Rs.{total_value - total_cost:,.0f}', 0, 1, 'L')
        
            # Save PDF
            pdf.output(filename)
            show_success(f"PDF exported successfully!\nFile: {filename}\nTotal Products: {len(products)}")
         
        except ImportError:
            show_error("FPDF library not installed. Please run: pip install fpdf")
        except Exception as e:
            show_error(f"Error exporting to PDF: {str(e)}")
    # ============ END OF NEW PDF EXPORT METHOD ============