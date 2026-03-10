# accounting.py
import sqlite3
from datetime import datetime

def create_accounting_tables():
    """Create accounting tables if they don't exist"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    
    # Chart of Accounts
    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_code VARCHAR(20) UNIQUE,
        account_name VARCHAR(100),
        account_type VARCHAR(20), -- Asset, Liability, Income, Expense, Equity
        parent_id INTEGER,
        opening_balance DECIMAL(10,2) DEFAULT 0,
        current_balance DECIMAL(10,2) DEFAULT 0,
        is_active BOOLEAN DEFAULT 1,
        created_date DATE,
        FOREIGN KEY (parent_id) REFERENCES accounts(id)
    )''')
    
    # Vouchers
    c.execute('''CREATE TABLE IF NOT EXISTS vouchers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_no VARCHAR(20) UNIQUE,
        voucher_type VARCHAR(20), -- Payment, Receipt, Journal, Contra
        voucher_date DATE,
        narration TEXT,
        total_amount DECIMAL(10,2),
        created_by VARCHAR(50),
        created_at DATETIME,
        status VARCHAR(20) DEFAULT 'Posted', -- Posted, Cancelled
        supplier_id INTEGER,
        customer_id INTEGER,
        member_id INTEGER
    )''')
    
    # Ledger Entries (Double-entry)
    c.execute('''CREATE TABLE IF NOT EXISTS ledger_entries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        voucher_id INTEGER,
        account_id INTEGER,
        debit DECIMAL(10,2) DEFAULT 0,
        credit DECIMAL(10,2) DEFAULT 0,
        narration TEXT,
        entry_date DATE,
        FOREIGN KEY (voucher_id) REFERENCES vouchers(id),
        FOREIGN KEY (account_id) REFERENCES accounts(id)
    )''')
    
    # Transaction Types Reference
    c.execute('''CREATE TABLE IF NOT EXISTS transaction_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_code VARCHAR(20) UNIQUE,
        type_name VARCHAR(50),
        category VARCHAR(20) -- Expense, Income, Asset, Liability, Equity
    )''')
    
    conn.commit()
    conn.close()
    print("✅ Accounting tables created successfully")

def initialize_chart_of_accounts():
    """Insert standard chart of accounts"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    
    # Check if accounts already exist
    c.execute("SELECT COUNT(*) FROM accounts")
    if c.fetchone()[0] > 0:
        conn.close()
        print("📊 Chart of Accounts already exists")
        return
    
    # Standard Chart of Accounts
    accounts = [
        # Assets (1)
        ('1000', 'Cash in Hand', 'Asset', None, 0),
        ('1100', 'Bank Accounts', 'Asset', None, 0),
        ('1101', 'Main Bank Account', 'Asset', 1100, 0),
        ('1200', 'Accounts Receivable', 'Asset', None, 0),
        ('1300', 'Inventory', 'Asset', None, 0),
        
        # Liabilities (2)
        ('2000', 'Accounts Payable', 'Liability', None, 0),
        ('2100', 'Credit Card Payable', 'Liability', None, 0),
        
        # Equity (3)
        ('3000', 'Owner\'s Capital', 'Equity', None, 0),
        ('3100', 'Retained Earnings', 'Equity', None, 0),
        
        # Income (4)
        ('4000', 'Sales Revenue', 'Income', None, 0),
        ('4100', 'Other Income', 'Income', None, 0),
        
        # Expenses (5)
        ('5000', 'Cost of Goods Sold', 'Expense', None, 0),
        ('5100', 'Salaries Expense', 'Expense', None, 0),
        ('5200', 'Rent Expense', 'Expense', None, 0),
        ('5300', 'Utilities Expense', 'Expense', None, 0),
        ('5400', 'Office Expenses', 'Expense', None, 0),
        ('5500', 'Purchase Account', 'Expense', None, 0),
    ]
    
    for acc in accounts:
        c.execute('''INSERT INTO accounts 
                    (account_code, account_name, account_type, parent_id, opening_balance)
                    VALUES (?,?,?,?,?)''', acc)
    
    conn.commit()
    conn.close()
    print("✅ Chart of Accounts initialized with 16 standard accounts")

def initialize_transaction_types():
    """Insert standard transaction types"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    
    # Check if transaction types already exist
    c.execute("SELECT COUNT(*) FROM transaction_types")
    if c.fetchone()[0] > 0:
        conn.close()
        print("📊 Transaction types already exist")
        return
    
    # Standard transaction types
    transaction_types = [
        ('SALE', 'Sales Revenue', 'Income'),
        ('SALE_RETURN', 'Sales Return', 'Income'),
        ('PURCHASE', 'Purchase', 'Expense'),
        ('PURCHASE_RETURN', 'Purchase Return', 'Expense'),
        ('EXPENSE', 'General Expense', 'Expense'),
        ('MEMBERSHIP_FEE', 'Membership Fee', 'Income'),
        ('CREDIT_SALE', 'Credit Sale', 'Income'),
        ('CREDIT_PAYMENT', 'Credit Payment', 'Asset'),
        ('SUPPLIER_PAYMENT', 'Supplier Payment', 'Liability'),
        ('CUSTOMER_PAYMENT', 'Customer Payment', 'Asset'),
        ('OTHER_CHARGE', 'Other Charges', 'Income'),
        ('DISCOUNT', 'Discount', 'Expense'),
    ]
    
    for tt in transaction_types:
        c.execute('''INSERT OR IGNORE INTO transaction_types (type_code, type_name, category)
                    VALUES (?,?,?)''', tt)
    
    conn.commit()
    conn.close()
    print("✅ Transaction types initialized with 12 types")

# Run this when file is executed directly
if __name__ == "__main__":
    create_accounting_tables()
    initialize_chart_of_accounts()
    initialize_transaction_types()
    print("🎉 Accounting system setup complete!")