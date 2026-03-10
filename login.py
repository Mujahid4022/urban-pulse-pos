# login.py
import os
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import messagebox
import sqlite3
from utils import setup_enter_navigation
import random
from datetime import datetime
from tkcalendar import DateEntry

class LoginWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Urban Pulse POS - Login")
        self.window.geometry("400x500")
        self.window.resizable(False, False)
        
        # Center the window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 400) // 2
        y = (self.window.winfo_screenheight() - 500) // 2
        self.window.geometry(f"450x500+{x}+{y}")
        
        self.user_id = None
        self.username = None
        self.role = None
        
        # Color palette
        self.colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
            '#D4A5A5', '#9B59B6', '#3498DB', '#E67E22', '#2ECC71',
            '#F1C40F', '#E74C3C', '#1ABC9C', '#9B59B6', '#34495E'
        ]
        
        self.create_colorful_background()
        self.create_login_form()
        
        self.window.mainloop()
    
    def create_colorful_background(self):
        """Create a vibrant, colorful background"""
        # Configure window background
        self.window.configure(bg='#f0f2f5')
        
        # Create canvas for patterns
        self.canvas = tk.Canvas(self.window, width=400, height=550, highlightthickness=0, bg='#f0f2f5')
        self.canvas.place(x=0, y=0)
        
        # Create diagonal stripes
        for i in range(-100, 700, 40):
            color = random.choice(self.colors)
            self.canvas.create_polygon(
                i, 0,
                i + 30, 0,
                i - 30, 550,
                i - 60, 550,
                fill=color, outline='', stipple='gray50'
            )
        
        # Create circles
        for _ in range(15):
            x = random.randint(0, 400)
            y = random.randint(0, 450)
            size = random.randint(30, 100)
            color = random.choice(self.colors)
            self.canvas.create_oval(x-size, y-size, x+size, y+size, 
                                    fill=color, outline='', stipple='gray25')
    
    def create_login_form(self):
        """Create the login form with colorful styling"""
        
        # White form background
        overlay = tk.Frame(self.window, bg='#ffffff', bd=0)
        overlay.place(relx=0.5, rely=0.5, anchor=tk.CENTER, width=300, height=500)
        
        # Add colorful top bar
        top_bar = tk.Frame(overlay, height=10)
        top_bar.pack(fill=tk.X)
        
        # Create rainbow bar
        rainbow_colors = ['#FF6B6B', '#FF8E53', '#FFB347', '#4ECDC4', '#45B7D1', '#9B59B6', '#FF6B6B']
        for color in rainbow_colors:
            bar = tk.Frame(top_bar, bg=color, height=10, width=54)
            bar.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Main content frame
        main_frame = tk.Frame(overlay, bg='white', padx=30, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Logo
        logo_frame = tk.Frame(main_frame, bg='white')
        logo_frame.pack(pady=(15, 5))
        
        # Try to load logo.png
        try:
            from PIL import Image, ImageTk
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo.png')
            if os.path.exists(logo_path):
                img = Image.open(logo_path)
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                self.logo_image = ImageTk.PhotoImage(img)
                logo_label = tk.Label(logo_frame, image=self.logo_image, bg='white')
                logo_label.pack()
            else:
                # Fallback to emoji if logo not found
                logo_canvas = tk.Canvas(logo_frame, width=90, height=90, bg='white', highlightthickness=0)
                logo_canvas.pack()
                ring_colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#F1C40F', '#9B59B6']
                for i, color in enumerate(ring_colors):
                    size = 80 - i * 12
                    logo_canvas.create_oval(45-size//2, 45-size//2, 45+size//2, 45+size//2, 
                                            fill=color, outline='')
                logo_canvas.create_text(45, 45, text="🏪", font=('Arial', 35), fill='white')
        except:
            # Fallback if PIL not available
            logo_canvas = tk.Canvas(logo_frame, width=90, height=90, bg='white', highlightthickness=0)
            logo_canvas.pack()
            logo_canvas.create_text(45, 45, text="🏪", font=('Arial', 35), fill='#2c3e50')
        
        # App name
        title_frame = tk.Frame(main_frame, bg='white')
        title_frame.pack(pady=5)
        
        tk.Label(title_frame, text="URBAN PULSE", font=('Arial', 18, 'bold'),
                bg='white', fg='#2c3e50').pack()
        
        # Tagline
        tk.Label(main_frame, text="Point of Sale System", font=('Arial', 9, 'italic'),
                bg='white', fg='#7f8c8d').pack(pady=(0, 15))
        
        # Username field with placeholder
        username_frame = tk.Frame(main_frame, bg='#dddddd', bd=1, relief=tk.SOLID)  # Dark gray border
        username_frame.pack(pady=5, fill=tk.X)
        
        # Username icon
        user_icon_frame = tk.Frame(username_frame, bg='#3498db', width=40, height=40)
        user_icon_frame.pack(side=tk.LEFT)
        user_icon_frame.pack_propagate(False)
        
        tk.Label(user_icon_frame, text="👤", font=('Arial', 16), 
                bg='#3498db', fg='white').pack(expand=True)
        
        # Username entry - LIGHT GRAY background
        self.entry_user = tk.Entry(username_frame, font=('Arial', 11),
                                   bg='#f0f0f0',  # Light gray
                                   fg='#aaaaaa',  # Light gray text for placeholder
                                   bd=0, highlightthickness=0)
        self.entry_user.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=8)
        
        # Insert placeholder text
        self.entry_user.insert(0, "Enter username")
        
        # Bind focus events for placeholder
        self.entry_user.bind('<FocusIn>', self.on_username_focus_in)
        self.entry_user.bind('<FocusOut>', self.on_username_focus_out)
        
        # Password field with placeholder
        password_frame = tk.Frame(main_frame, bg='#dddddd', bd=1, relief=tk.SOLID)  # Dark gray border
        password_frame.pack(pady=5, fill=tk.X)
        
        # Password icon
        pass_icon_frame = tk.Frame(password_frame, bg='#e67e22', width=40, height=40)
        pass_icon_frame.pack(side=tk.LEFT)
        pass_icon_frame.pack_propagate(False)
        
        tk.Label(pass_icon_frame, text="🔒", font=('Arial', 16),
                bg='#e67e22', fg='white').pack(expand=True)
        
        # Password entry
        pass_entry_frame = tk.Frame(password_frame, bg='#f0f0f0')  # Light gray
        pass_entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.entry_pass = tk.Entry(pass_entry_frame, font=('Arial', 11),
                                   bg='#f0f0f0',  # Light gray
                                   fg='#aaaaaa',  # Light gray text for placeholder
                                   bd=0, highlightthickness=0, show="")  # show="" for placeholder visibility
        self.entry_pass.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=8)
        
        # Insert placeholder text
        self.entry_pass.insert(0, "Enter password")
        
        # Bind focus events for placeholder
        self.entry_pass.bind('<FocusIn>', self.on_password_focus_in)
        self.entry_pass.bind('<FocusOut>', self.on_password_focus_out)
        
        # Show/Hide password button
        self.show_password = tk.BooleanVar(value=False)
        self.toggle_btn = tk.Label(pass_entry_frame, text="👁️", font=('Arial', 12),
                                    bg='#f0f0f0', fg='#7f8c8d', cursor='hand2')
        self.toggle_btn.pack(side=tk.RIGHT, padx=8)
        self.toggle_btn.bind('<Button-1>', self.toggle_password)

        # Working Date field with calendar
        date_frame = tk.Frame(main_frame, bg='#dddddd', bd=1, relief=tk.SOLID)
        date_frame.pack(pady=5, fill=tk.X)
        
        # Date icon
        date_icon_frame = tk.Frame(date_frame, bg='#9b59b6', width=40, height=40)
        date_icon_frame.pack(side=tk.LEFT)
        date_icon_frame.pack_propagate(False)
        tk.Label(date_icon_frame, text="📅", font=('Arial', 16),
                bg='#9b59b6', fg='white').pack(expand=True)
        
        # Calendar Date Picker
        date_picker_frame = tk.Frame(date_frame, bg='#f0f0f0')
        date_picker_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        from tkcalendar import DateEntry
        self.calendar_date = DateEntry(date_picker_frame, width=20, font=('Arial', 11),
                                      background='#f0f0f0', foreground='#2c3e50',
                                      borderwidth=0, date_pattern='yyyy-mm-dd')
        self.calendar_date.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=8)
        
        # Store the date as string variable for compatibility
        self.working_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        self.calendar_date.bind('<<DateEntrySelected>>', 
                               lambda e: self.working_date.set(self.calendar_date.get_date().strftime('%Y-%m-%d'))) 
                                      
        # Forgot password only
        forgot_frame = tk.Frame(main_frame, bg='white')
        forgot_frame.pack(pady=8, fill=tk.X)
        
        forgot_label = tk.Label(forgot_frame, text="Forgot Password?",
                                bg='white', fg='#FF6B6B',
                                font=('Arial', 9, 'bold'),
                                cursor='hand2')
        forgot_label.pack(side=tk.RIGHT)
        forgot_label.bind('<Button-1>', self.forgot_password)
        
        # Login button - DARK GRAY BLUE with light black border
        login_btn = tk.Button(main_frame, text="LOGIN", command=self.login,
                              bg='#2c3e50', fg='white',  # Dark gray-blue
                              font=('Arial', 13, 'bold'),
                              bd=1, relief=tk.SOLID,  # Border
                              highlightbackground='#1a1a1a',  # Light black border
                              cursor='hand2')
        login_btn.pack(pady=15, fill=tk.X, ipady=12)
        
        # Hover effects (slightly lighter on hover)
        login_btn.bind('<Enter>', lambda e: login_btn.configure(bg='#34495e'))
        login_btn.bind('<Leave>', lambda e: login_btn.configure(bg='#2c3e50'))
        
        # Version info
        version_frame = tk.Frame(main_frame, bg='white')
        version_frame.pack(side=tk.BOTTOM, pady=5)
        
        tk.Label(version_frame, text="Version 2.0.0",
                font=('Arial', 8), bg='white', fg='#95a5a6').pack()
        
        # Setup Enter key navigation
        setup_enter_navigation(self.entry_user, self.entry_pass)
        setup_enter_navigation(self.entry_pass, self.login)
    
    def on_username_focus_in(self, event):
        """Handle username field focus in"""
        if self.entry_user.get() == "Enter username":
            self.entry_user.delete(0, tk.END)
            self.entry_user.config(fg='#2c3e50')  # Dark text when typing
    
    def on_username_focus_out(self, event):
        """Handle username field focus out"""
        if not self.entry_user.get():
            self.entry_user.insert(0, "Enter username")
            self.entry_user.config(fg='#aaaaaa')  # Light gray placeholder
    
    def on_password_focus_in(self, event):
        """Handle password field focus in"""
        if self.entry_pass.get() == "Enter password":
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.config(fg='#2c3e50', show="●")  # Dark text, show bullets
    
    def on_password_focus_out(self, event):
        """Handle password field focus out"""
        if not self.entry_pass.get():
            self.entry_pass.config(show="")  # Show text for placeholder
            self.entry_pass.insert(0, "Enter password")
            self.entry_pass.config(fg='#aaaaaa')  # Light gray placeholder
    
    def toggle_password(self, event=None):
        """Toggle password visibility"""
        # Don't toggle if showing placeholder
        if self.entry_pass.get() == "Enter password":
            return
        
        if self.show_password.get():
            self.entry_pass.config(show="●")
            self.toggle_btn.config(text="👁️")
        else:
            self.entry_pass.config(show="")
            self.toggle_btn.config(text="👁️‍🗨️")
        self.show_password.set(not self.show_password.get())
    
    def forgot_password(self, event=None):
        """Handle forgot password click"""
        messagebox.showinfo("Forgot Password",
                           "Please contact your system administrator.\n\n"
                           "📞 Support: 0300-1234567\n"
                           "📧 Email: support@urbanpulse.com")
    
    def login(self, event=None):
        """Handle login button click"""
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        
        # Check if using placeholder text
        if username == "Enter username":
            username = ""
        if password == "Enter password":
            password = ""
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter username and password")
            return
        
        conn = sqlite3.connect('urban_pulse.db')
        c = conn.cursor()
        c.execute("SELECT id, username, role FROM users WHERE username=? AND password=?",
                  (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            self.user_id, self.username, self.role = user
            self.selected_date = self.calendar_date.get_date().strftime('%Y-%m-%d')
            self.window.destroy()
        else:
            messagebox.showerror("Error", "Invalid username or password")
            # Reset password field
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.insert(0, "Enter password")
            self.entry_pass.config(fg='#aaaaaa', show="")
            self.entry_user.focus_set()