# database.py
import sqlite3
import os
from datetime import datetime

def setup_database():
    """Create all database tables and populate with sample data"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE,
                  password TEXT,
                  role TEXT)''')
    
    # Settings table
    c.execute('''CREATE TABLE IF NOT EXISTS settings
                 (key TEXT PRIMARY KEY,
                  value TEXT)''')
    
    # Suppliers table
    c.execute('''CREATE TABLE IF NOT EXISTS suppliers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  company_name TEXT NOT NULL,
                  contact_person TEXT,
                  phone TEXT,
                  mobile TEXT,
                  email TEXT,
                  address TEXT,
                  city TEXT,
                  payment_terms TEXT,
                  tax_number TEXT,
                  opening_balance REAL DEFAULT 0,
                  current_balance REAL DEFAULT 0,
                  notes TEXT,
                  created_date TEXT)''')
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  barcode TEXT UNIQUE,
                  name TEXT NOT NULL,
                  price REAL NOT NULL,
                  cost_price REAL DEFAULT 0,
                  stock INTEGER DEFAULT 0,
                  supplier_id INTEGER,
                  reorder_level INTEGER DEFAULT 10,
                  discount_percent REAL DEFAULT 0,
                  discount_start TEXT,
                  discount_end TEXT,
                  is_bogo INTEGER DEFAULT 0,
                  FOREIGN KEY(supplier_id) REFERENCES suppliers(id))''')
    
    # Customers table
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT UNIQUE,
                  email TEXT,
                  loyalty_points INTEGER DEFAULT 0,
                  total_spent REAL DEFAULT 0,
                  last_visit TEXT,
                  join_date TEXT,
                  points_earned_total INTEGER DEFAULT 0,
                  points_used_total INTEGER DEFAULT 0)''')
    
    # Purchase Orders table (UPDATED with payment_method)
    c.execute('''CREATE TABLE IF NOT EXISTS purchase_orders
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  po_number TEXT UNIQUE,
                  supplier_id INTEGER,
                  supplier_name TEXT,
                  order_date TEXT,
                  expected_date TEXT,
                  status TEXT,
                  subtotal REAL,
                  tax REAL,
                  discount REAL,
                  total REAL,
                  payment_method TEXT DEFAULT 'Credit',
                  payment_status TEXT DEFAULT 'Unpaid',
                  notes TEXT,
                  created_by TEXT,
                  FOREIGN KEY(supplier_id) REFERENCES suppliers(id))''')
    
    # Purchase Order Items table
    c.execute('''CREATE TABLE IF NOT EXISTS po_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  po_id INTEGER,
                  product_id INTEGER,
                  product_name TEXT,
                  quantity INTEGER,
                  unit_cost REAL,
                  total_cost REAL,
                  received_quantity INTEGER DEFAULT 0,
                  FOREIGN KEY(po_id) REFERENCES purchase_orders(id),
                  FOREIGN KEY(product_id) REFERENCES products(id))''')
    
    # Points transactions table
    c.execute('''CREATE TABLE IF NOT EXISTS points_transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  customer_id INTEGER,
                  customer_name TEXT,
                  transaction_date TEXT,
                  points_change INTEGER,
                  balance_after INTEGER,
                  transaction_type TEXT,
                  sale_id INTEGER,
                  notes TEXT,
                  FOREIGN KEY(customer_id) REFERENCES customers(id))''')
    
    # Sales table
    c.execute('''CREATE TABLE IF NOT EXISTS sales
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  datetime TEXT,
                  customer_id INTEGER,
                  customer_name TEXT,
                  subtotal REAL,
                  discount_total REAL,
                  tax_total REAL,
                  total REAL,
                  items TEXT,
                  payment_method TEXT,
                  points_earned INTEGER,
                  points_used INTEGER,
                  receipt_path TEXT,
                  FOREIGN KEY(customer_id) REFERENCES customers(id))''')
    
    # Sale items table
    c.execute('''CREATE TABLE IF NOT EXISTS sale_items
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sale_id INTEGER,
                  product_id INTEGER,
                  product_name TEXT,
                  quantity INTEGER,
                  unit_price REAL,
                  discount_percent REAL,
                  discount_amount REAL,
                  final_price REAL,
                  FOREIGN KEY(sale_id) REFERENCES sales(id),
                  FOREIGN KEY(product_id) REFERENCES products(id))''')
    
    # Promotions table
    c.execute('''CREATE TABLE IF NOT EXISTS promotions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  type TEXT,
                  value REAL,
                  min_purchase REAL,
                  start_date TEXT,
                  end_date TEXT,
                  product_id INTEGER,
                  is_active INTEGER DEFAULT 1,
                  FOREIGN KEY(product_id) REFERENCES products(id))''')
    # Add accounting tables
    from accounting import create_accounting_tables,initialize_chart_of_accounts
    create_accounting_tables()
    initialize_chart_of_accounts

    print("✅ Database setup complete")
    
    # Create folders
    for folder in ['receipts', 'reports', 'purchase_orders']:
        if not os.path.exists(folder):
            os.makedirs(folder)
    
    # Add default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role) VALUES (?,?,?)",
                  ('admin', 'admin123', 'admin'))
    
    # Add default settings
    default_settings = [
        ('points_conversion_rate', '100'),
        ('points_min_redeem', '100'),
        ('points_earn_rate', '1'),
        ('currency_symbol', 'Rs.'),
        ('currency_code', 'PKR'),
        ('tax_rate', '17'),
        ('store_name', 'Urban Pulse'),
        ('store_phone', '0300-1234567'),
        ('store_address', 'Main Market, Karachi'),
        ('reorder_alert', '1'),
    ]
    for key, value in default_settings:
        c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
    
    # Add sample suppliers
    c.execute("SELECT COUNT(*) FROM suppliers")
    if c.fetchone()[0] == 0:
        sample_suppliers = [
            ('Shan Foods Pvt Ltd', 'Ali Raza', '021-34567890', '0300-1234001', 'ali@shanfoods.com', 'SITE Area, Karachi', 'Karachi', 'Net 30', '1234567-8', 0, 0, 'Spices and rice supplier', datetime.now().strftime('%Y-%m-%d')),
            ('Engro Foods', 'Sana Malik', '021-34567891', '0300-1234002', 'sana@engro.com', 'Port Qasim, Karachi', 'Karachi', 'Net 45', '2345678-9', 0, 0, 'Dairy products', datetime.now().strftime('%Y-%m-%d')),
            ('Mitchells', 'Ahmed Khan', '042-34567892', '0300-1234003', 'ahmed@mitchells.com', 'Gulberg, Lahore', 'Lahore', 'Net 30', '3456789-0', 0, 0, 'Beverages and snacks', datetime.now().strftime('%Y-%m-%d')),
            ('Coca-Cola Pakistan', 'Bilal Ahmed', '021-34567893', '0300-1234004', 'bilal@cocacola.com', 'Ferozepur Road, Lahore', 'Lahore', 'Net 60', '4567890-1', 0, 0, 'Soft drinks', datetime.now().strftime('%Y-%m-%d')),
            ('National Foods', 'Fatima Zaidi', '021-34567894', '0300-1234005', 'fatima@national.com', 'Korangi, Karachi', 'Karachi', 'Net 30', '5678901-2', 0, 0, 'Processed foods', datetime.now().strftime('%Y-%m-%d')),
        ]
        c.executemany('''INSERT INTO suppliers 
                        (company_name, contact_person, phone, mobile, email, address, city, payment_terms, tax_number, opening_balance, current_balance, notes, created_date) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)''', sample_suppliers)
    
    # Add sample products
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ('123456789012', 'Milk 1L', 150.00, 120.00, 50, 2, 10, 0, None, None, 0),
            ('234567890123', 'Bread', 80.00, 60.00, 30, 2, 8, 0, None, None, 0),
            ('345678901234', 'Eggs (12)', 220.00, 180.00, 20, 1, 5, 0, None, None, 0),
            ('456789012345', 'Basmati Rice 5kg', 850.00, 700.00, 15, 1, 3, 10, '2024-03-01', '2024-03-31', 0),
            ('567890123456', 'Cooking Oil 3L', 550.00, 450.00, 25, 5, 5, 0, None, None, 0),
            ('678901234567', 'Sugar 1kg', 120.00, 95.00, 40, 5, 15, 0, None, None, 0),
            ('789012345678', 'Tea 250g', 280.00, 220.00, 35, 3, 10, 5, '2024-03-01', '2024-03-15', 0),
            ('890123456789', 'Flour 10kg', 650.00, 520.00, 20, 1, 5, 0, None, None, 1),
            ('901234567890', 'Lentils (Daal) 1kg', 220.00, 170.00, 45, 1, 20, 0, None, None, 0),
        ]
        c.executemany('''INSERT INTO products 
                        (barcode, name, price, cost_price, stock, supplier_id, reorder_level, discount_percent, discount_start, discount_end, is_bogo) 
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)''', sample_products)
    
    # Add sample customers
    c.execute("SELECT COUNT(*) FROM customers")
    if c.fetchone()[0] == 0:
        sample_customers = [
            ('Ali Raza', '03001234567', 'ali@email.com', 150, 12500.50, '2024-02-28', '2024-01-15', 175, 25),
            ('Sana Khan', '03011234567', 'sana@email.com', 75, 7500.25, '2024-03-01', '2024-02-01', 100, 25),
            ('Ahmed Malik', '03021234567', 'ahmed@email.com', 200, 21000.00, '2024-02-29', '2023-12-10', 250, 50),
            ('Fatima Zaidi', '03031234567', 'fatima@email.com', 500, 32500.75, '2024-03-01', '2023-11-15', 550, 50),
            ('Bilal Ahmed', '03041234567', 'bilal@email.com', 25, 8500.00, '2024-02-20', '2024-02-01', 35, 10),
        ]
        c.executemany('''INSERT INTO customers 
                        (name, phone, email, loyalty_points, total_spent, last_visit, join_date, points_earned_total, points_used_total) 
                        VALUES (?,?,?,?,?,?,?,?,?)''', sample_customers)
    
    # Add sample promotions
    c.execute("SELECT COUNT(*) FROM promotions")
    if c.fetchone()[0] == 0:
        sample_promotions = [
            ('Summer Sale', 'percent', 10, 0, '2024-06-01', '2024-08-31', None, 1),
            ('Milk Special', 'percent', 5, 0, '2024-03-01', '2024-03-31', 1, 1),
            ('Rice BOGO', 'bogo', 50, 500, '2024-03-01', '2024-04-30', 4, 1),
            ('Weekend Discount', 'percent', 15, 1000, '2024-03-01', '2024-12-31', None, 1),
            ('Clearance Sale', 'percent', 25, 0, '2024-03-15', '2024-03-31', None, 1),
        ]
        c.executemany('''INSERT INTO promotions (name, type, value, min_purchase, start_date, end_date, product_id, is_active) 
                        VALUES (?,?,?,?,?,?,?,?)''', sample_promotions)
    
    conn.commit()
    conn.close()
    print("Database setup complete!")

if __name__ == "__main__":
    setup_database()