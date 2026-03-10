# category_manager.py
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from utils import show_error, show_success, ask_yes_no

class CategoryManager:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Category Manager")
        self.window.geometry("800x700")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 700) // 2
        self.window.geometry(f"800x700+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        self.create_widgets()
        self.load_categories()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#3498db', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="📁 CATEGORY MANAGER", fg='white', bg='#3498db',
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
        
        # Left Panel - Category Tree
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=350)
        paned.add(left_frame, width=350, minsize=300)
        
        tk.Label(left_frame, text="📋 CATEGORY TREE", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=5)
        
        # Treeview for categories
        tree_frame = tk.Frame(left_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        
        self.cat_tree = ttk.Treeview(tree_frame, columns=('Products', 'Value'), 
                                      show='tree headings',
                                      yscrollcommand=vsb.set, height=20)
        vsb.config(command=self.cat_tree.yview)
        
        self.cat_tree.column('#0', width=250)
        self.cat_tree.heading('#0', text='Category')
        self.cat_tree.heading('Products', text='Products')
        self.cat_tree.heading('Value', text='Stock Value')
        
        self.cat_tree.column('Products', width=80, anchor='center')
        self.cat_tree.column('Value', width=100, anchor='e')
        
        self.cat_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.cat_tree.bind('<<TreeviewSelect>>', self.on_category_select)
        
        # Right Panel - Category Details & Creation
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=450)
        
        # Create new category frame
        create_frame = tk.LabelFrame(right_frame, text="➕ CREATE NEW CATEGORY", 
                                     font=('Arial', 12, 'bold'), padx=15, pady=10)
        create_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Parent selection
        tk.Label(create_frame, text="Parent Category:", font=('Arial', 10)).grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.parent_var = tk.StringVar()
        self.parent_combo = ttk.Combobox(create_frame, textvariable=self.parent_var, width=35, font=('Arial', 10))
        self.parent_combo.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        
        # Category name
        tk.Label(create_frame, text="Category Name:", font=('Arial', 10)).grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.cat_name = tk.Entry(create_frame, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.cat_name.grid(row=1, column=1, padx=5, pady=5, sticky='w')
        
        # Description
        tk.Label(create_frame, text="Description:", font=('Arial', 10)).grid(row=2, column=0, padx=5, pady=5, sticky='ne')
        self.description = tk.Text(create_frame, height=3, width=35, font=('Arial', 10), relief='solid', bd=1)
        self.description.grid(row=2, column=1, padx=5, pady=5, sticky='w')
        
        # Buttons
        btn_frame = tk.Frame(create_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        tk.Button(btn_frame, text="✅ Create Category", command=self.create_category,
                 bg='#27ae60', fg='white', font=('Arial', 11, 'bold'),
                 width=15, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="🗑️ Clear", command=self.clear_form,
                 bg='#95a5a6', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        
        # Category details frame
        details_frame = tk.LabelFrame(right_frame, text="📊 CATEGORY DETAILS", 
                                      font=('Arial', 12, 'bold'), padx=15, pady=10)
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.details_text = tk.Text(details_frame, height=12, width=40, font=('Courier', 10),
                                    relief='solid', bd=1, state='disabled')
        self.details_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Action buttons
        action_frame = tk.Frame(details_frame)
        action_frame.pack(pady=5)
        
        tk.Button(action_frame, text="✏️ Edit", command=self.edit_category,
                 bg='#f39c12', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="❌ Delete", command=self.delete_category,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
        tk.Button(action_frame, text="🔄 Refresh", command=self.load_categories,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 width=10, cursor='hand2').pack(side=tk.LEFT, padx=5)
    
    def load_categories(self):
        """Load categories into tree"""
        for item in self.cat_tree.get_children():
            self.cat_tree.delete(item)
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Check if categories table exists
        c.execute('''CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT NOT NULL,
            parent_id INTEGER,
            level INTEGER,
            full_path TEXT,
            description TEXT,
            created_date DATE,
            FOREIGN KEY (parent_id) REFERENCES categories(id)
        )''')
        
        # Insert default "OTHERS" if not exists
        c.execute("SELECT COUNT(*) FROM categories WHERE category_name='OTHERS'")
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO categories 
                        (category_name, parent_id, level, full_path, created_date)
                        VALUES ('OTHERS', NULL, 1, 'OTHERS', ?)''', 
                      (self.working_date,))
            conn.commit()
        
        # Get all categories
        c.execute('''SELECT id, category_name, parent_id, level, full_path 
                     FROM categories ORDER BY full_path''')
        categories = c.fetchall()
        
        # Get product counts per category
        c.execute('''SELECT category_id, COUNT(*), COALESCE(SUM(cost_price * stock), 0)
                     FROM products GROUP BY category_id''')
        product_stats = {row[0]: (row[1], row[2]) for row in c.fetchall()}
        conn.close()
        
        # Build tree
        nodes = {}
        
        # First, create all category nodes
        for cat in categories:
            cat_id, name, parent_id, level, full_path = cat
            
            # Get product count and value
            prod_count, prod_value = product_stats.get(cat_id, (0, 0))
            
            if parent_id is None:
                # Top level category
                node = self.cat_tree.insert('', 'end', 
                                           text=f"📁 {name}",
                                           values=(prod_count, f"Rs.{prod_value:,.0f}"),
                                           iid=f"CAT_{cat_id}", open=True)
                nodes[cat_id] = node
            else:
                # Child category
                if parent_id in nodes:
                    parent_node = nodes[parent_id]
                else:
                    parent_node = ''
                
                node = self.cat_tree.insert(parent_node, 'end',
                                           text=f"  📂 {name}",
                                           values=(prod_count, f"Rs.{prod_value:,.0f}"),
                                           iid=f"CAT_{cat_id}")
                nodes[cat_id] = node
        
        # Load parent combobox
        self.load_parent_combo()
    
    def load_parent_combo(self):
        """Load ONLY parent categories (Level 1) for dropdown"""
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        # Get ONLY parent categories (where parent_id is NULL)
        c.execute("SELECT id, category_name FROM categories WHERE parent_id IS NULL ORDER BY category_name")
        parents = c.fetchall()
        conn.close()
    
        # Add "None (Top Level)" as first option
        parent_list = ['None (Top Level)'] + [p[1] for p in parents]
        self.parent_combo['values'] = parent_list
        self.parent_combo.set('None (Top Level)')
    
        # Store parents for reference
        self.parent_categories = parents
    
    def on_category_select(self, event):
        """Show category details when selected"""
        selected = self.cat_tree.selection()
        if not selected:
            return
        
        cat_id = int(selected[0].replace('CAT_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        c.execute('''SELECT category_name, parent_id, level, full_path, description, created_date
                     FROM categories WHERE id=?''', (cat_id,))
        cat = c.fetchone()
        
        if cat:
            name, parent_id, level, path, desc, created = cat
            
            # Get parent name
            if parent_id:
                c.execute("SELECT category_name FROM categories WHERE id=?", (parent_id,))
                parent_name = c.fetchone()[0]
            else:
                parent_name = "None (Top Level)"
            
            # Get products in this category
            c.execute('''SELECT COUNT(*), SUM(stock), SUM(cost_price * stock)
                         FROM products WHERE category_id=?''', (cat_id,))
            prod_count, total_stock, total_value = c.fetchone()
            if not total_stock: total_stock = 0
            if not total_value: total_value = 0
            
        conn.close()
        
        # Update details text
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        details = f"""
{'='*40}
CATEGORY DETAILS
{'='*40}

Name: {name}
Parent: {parent_name}
Level: {level}
Path: {path}

STATISTICS:
Products: {prod_count or 0}
Total Stock: {total_stock or 0} units
Stock Value: Rs.{total_value:,.2f}

Created: {created or 'N/A'}
Description: {desc or 'N/A'}
        """
        
        self.details_text.insert('1.0', details)
        self.details_text.config(state='disabled')
    
    def create_category(self):
        """Create new category"""
        parent_sel = self.parent_combo.get()
        cat_name = self.cat_name.get().strip()
        desc = self.description.get('1.0', tk.END).strip()
    
        if not cat_name:
            show_error("Please enter category name")
            return
    
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
    
        try:
            # Determine parent ID
            parent_id = None
            parent_path = ""
            level = 1
        
            if parent_sel != 'None (Top Level)':
                # Find parent ID from the parent_categories list
                for pid, pname in self.parent_categories:
                    if pname == parent_sel:
                        parent_id = pid
                        break
            
                if parent_id:
                    # Get parent's full path
                    c.execute("SELECT full_path FROM categories WHERE id=?", (parent_id,))
                    parent_path = c.fetchone()[0]
                    level = parent_path.count('>') + 2
        
            # Generate full path
            if parent_path:
                full_path = f"{parent_path} > {cat_name}"
            else:
                full_path = cat_name
        
            # Insert category
            c.execute('''INSERT INTO categories 
                    (category_name, parent_id, level, full_path, description, created_date)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                  (cat_name, parent_id, level, full_path, desc, self.working_date))
        
            conn.commit()
            show_success(f"Category '{cat_name}' created successfully!")
        
            self.clear_form()
            self.load_categories()
        
        except sqlite3.IntegrityError:
            show_error("Category name already exists")
        except Exception as e:
            show_error(f"Error creating category: {e}")
        finally:
            conn.close()
                
    def edit_category(self):
        """Edit selected category"""
        selected = self.cat_tree.selection()
        if not selected:
            show_error("Select a category to edit")
            return
        
        cat_id = int(selected[0].replace('CAT_', ''))
        
        # Simple edit dialog
        new_name = tk.simpledialog.askstring("Edit Category", "Enter new category name:",
                                             parent=self.window)
        if new_name and new_name.strip():
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            try:
                # Update name and full_path
                c.execute("SELECT full_path FROM categories WHERE id=?", (cat_id,))
                old_path = c.fetchone()[0]
                new_path = old_path.rsplit(' > ', 1)[0] + ' > ' + new_name if ' > ' in old_path else new_name
                
                c.execute("UPDATE categories SET category_name=?, full_path=? WHERE id=?",
                         (new_name.strip(), new_path, cat_id))
                conn.commit()
                show_success("Category updated")
                self.load_categories()
            except Exception as e:
                show_error(f"Error updating category: {e}")
            finally:
                conn.close()
    
    def delete_category(self):
        """Delete selected category"""
        selected = self.cat_tree.selection()
        if not selected:
            show_error("Select a category to delete")
            return
        
        cat_id = int(selected[0].replace('CAT_', ''))
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        
        # Check if category has products
        c.execute("SELECT COUNT(*) FROM products WHERE category_id=?", (cat_id,))
        prod_count = c.fetchone()[0]
        
        # Check if category has sub-categories
        c.execute("SELECT COUNT(*) FROM categories WHERE parent_id=?", (cat_id,))
        sub_count = c.fetchone()[0]
        
        c.execute("SELECT category_name FROM categories WHERE id=?", (cat_id,))
        cat_name = c.fetchone()[0]
        conn.close()
        
        if cat_name == 'OTHERS':
            show_error("Cannot delete default 'OTHERS' category")
            return
        
        if prod_count > 0 or sub_count > 0:
            msg = f"Category '{cat_name}' has {prod_count} products and {sub_count} sub-categories.\n"
            msg += "Deleting will move them to 'OTHERS'. Continue?"
        else:
            msg = f"Delete category '{cat_name}'?"
        
        if ask_yes_no(msg):
            conn = sqlite3.connect('urban_pulse.db')
            c = conn.cursor()
            
            try:
                # Get OTHERS category ID
                c.execute("SELECT id FROM categories WHERE category_name='OTHERS'")
                others_id = c.fetchone()[0]
                
                # Move products to OTHERS
                if prod_count > 0:
                    c.execute("UPDATE products SET category_id=? WHERE category_id=?", 
                             (others_id, cat_id))
                
                # Move sub-categories to OTHERS
                if sub_count > 0:
                    c.execute("UPDATE categories SET parent_id=? WHERE parent_id=?", 
                             (others_id, cat_id))
                
                # Delete the category
                c.execute("DELETE FROM categories WHERE id=?", (cat_id,))
                
                conn.commit()
                show_success(f"Category '{cat_name}' deleted")
                self.load_categories()
                
            except Exception as e:
                show_error(f"Error deleting category: {e}")
            finally:
                conn.close()
    
    def clear_form(self):
        """Clear the create category form"""
        self.parent_combo.set('None (Top Level)')
        self.cat_name.delete(0, tk.END)
        self.description.delete('1.0', tk.END)

# For testing
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    cm = CategoryManager(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()