# main.py
import os
import sys
from database import setup_database
from login import LoginWindow
from pos_main import UrbanPulsePOS  # Import directly instead of using os.system

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point for Urban Pulse POS system"""
    
    print("=" * 50)
    print("   Urban Pulse POS System")
    print("=" * 50)
    
    # Database check
    if not os.path.exists('urban_pulse.db'):
        print("First time setup: Creating database...")
        setup_database()
        print("Database created successfully!")
    else:
        print("Database found. Starting POS system...")
    
    print("\nLaunching login window...")
    
    # Show login
    login = LoginWindow()
    
    # After successful login, import and run POS directly
    if login.user_id:
        print(f"User logged in: {login.username} ({login.role})")
        print(f"Working date: {login.selected_date}")
        
        # Create user dict with ALL data including date
        user = {
            'id': login.user_id,
            'username': login.username,
            'role': login.role,
            'working_date': login.selected_date  # THIS IS CRITICAL
        }
        
        # Run POS directly (not as separate process)
        app = UrbanPulsePOS(user)
    else:
        print("Login cancelled. Exiting...")

if __name__ == "__main__":
    main()