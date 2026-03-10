# utils.py
import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime

# Currency settings for Pakistan
CURRENCY_SYMBOL = "Rs."
CURRENCY_CODE = "PKR"

def get_setting(key, default):
    """Get a setting from the database - returns float for numeric settings, string otherwise"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    
    if result is None:
        return default
    
    value = result[0]
    
    # Try to convert to float if it looks like a number
    try:
        # Check if it's a number (including decimals)
        if '.' in value or value.isdigit():
            return float(value)
    except (ValueError, TypeError):
        pass
    
    # Return as string if not numeric
    return value

def save_setting(key, value):
    """Save a setting to the database"""
    conn = sqlite3.connect('urban_pulse.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def center_window(window, width, height):
    """Center a window on the screen"""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")

def format_currency(amount):
    """Format amount with currency symbol"""
    return f"{CURRENCY_SYMBOL} {amount:.2f}"

def show_error(message):
    """Show error message box"""
    messagebox.showerror("Error", message)

def show_info(message):
    """Show info message box"""
    messagebox.showinfo("Information", message)

def show_success(message):
    """Show success message box"""
    messagebox.showinfo("Success", message)

def ask_yes_no(question):
    """Ask yes/no question"""
    return messagebox.askyesno("Confirm", question)

def setup_enter_navigation(widget, next_widget=None):
    """Setup Enter key to move to next widget"""
    def on_enter(event):
        if next_widget:
            if callable(next_widget):
                next_widget()
            else:
                next_widget.focus()
        return "break"
    widget.bind('<Return>', on_enter)
    return widget