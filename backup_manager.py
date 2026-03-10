# backup_manager.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import shutil
import os
import zipfile
from datetime import datetime
from utils import show_error, show_success, ask_yes_no

class BackupManager:
    def __init__(self, parent, username, working_date):
        self.parent = parent
        self.username = username
        self.working_date = working_date
        self.window = tk.Toplevel(parent)
        self.window.title("Backup & Restore Manager")
        self.window.geometry("800x600")
        
        # Center window
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() - 800) // 2
        y = (self.window.winfo_screenheight() - 600) // 2
        self.window.geometry(f"800x600+{x}+{y}")
        
        self.window.grab_set()
        self.window.transient(parent)
        
        # Backup directory for local copies
        self.backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backups')
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
        
        self.create_widgets()
        self.load_backup_list()
    
    def create_widgets(self):
        # Title
        title_frame = tk.Frame(self.window, bg='#2c3e50', height=40)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        tk.Label(title_frame, text="💾 BACKUP & RESTORE MANAGER", fg='white', bg='#2c3e50',
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
        
        # Left Panel - Backup Controls
        left_frame = tk.Frame(paned, bg='#ecf0f1', width=300)
        paned.add(left_frame, width=300, minsize=250)
        
        tk.Label(left_frame, text="⚙️ BACKUP CONTROLS", font=('Arial', 12, 'bold'),
                bg='#ecf0f1', fg='#2c3e50').pack(pady=10)
        
        # Backup Now Button
        backup_frame = tk.Frame(left_frame, bg='white', relief=tk.RIDGE, bd=1)
        backup_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(backup_frame, text="Create New Backup", font=('Arial', 11, 'bold'),
                bg='white').pack(pady=5)
        
        tk.Label(backup_frame, text="Backup Name:", bg='white', font=('Arial', 9)).pack()
        self.backup_name = tk.Entry(backup_frame, width=30, font=('Arial', 9))
        self.backup_name.pack(pady=2)
        
        # Auto-generate name
        default_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_name.insert(0, default_name)
        
        tk.Button(backup_frame, text="💾 Create Backup", command=self.create_backup,
                 bg='#27ae60', fg='white', font=('Arial', 10, 'bold'),
                 width=20, cursor='hand2').pack(pady=10)
        
        # Auto Backup Settings
        auto_frame = tk.Frame(left_frame, bg='white', relief=tk.RIDGE, bd=1)
        auto_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(auto_frame, text="Auto Backup Settings", font=('Arial', 11, 'bold'),
                bg='white').pack(pady=5)
        
        self.auto_backup = tk.BooleanVar(value=True)
        tk.Checkbutton(auto_frame, text="Enable Auto Backup", variable=self.auto_backup,
                      bg='white').pack(anchor='w', padx=10)
        
        tk.Label(auto_frame, text="Frequency:", bg='white').pack(anchor='w', padx=10)
        self.backup_freq = ttk.Combobox(auto_frame, values=['Daily', 'Weekly', 'Monthly'],
                                        width=15, font=('Arial', 9))
        self.backup_freq.set('Daily')
        self.backup_freq.pack(pady=2)
        
        tk.Label(auto_frame, text="Keep last:", bg='white').pack(anchor='w', padx=10)
        self.keep_count = ttk.Combobox(auto_frame, values=['5', '10', '20', '50'],
                                       width=10, font=('Arial', 9))
        self.keep_count.set('10')
        self.keep_count.pack(pady=2)
        
        tk.Button(auto_frame, text="💾 Save Settings", command=self.save_settings,
                 bg='#3498db', fg='white', font=('Arial', 9),
                 width=15, cursor='hand2').pack(pady=5)
        
        # Settings file path
        self.settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup_settings.json')
        self.load_settings()
        
        # Right Panel - Backup List
        right_frame = tk.Frame(paned, bg='#f9f9f9')
        paned.add(right_frame, width=500)
        
        tk.Label(right_frame, text="📋 AVAILABLE BACKUPS", font=('Arial', 12, 'bold'),
                bg='#f9f9f9', fg='#2c3e50').pack(pady=5)
        
        # Backup List Frame
        list_frame = tk.Frame(right_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        vsb = ttk.Scrollbar(list_frame, orient="vertical")
        hsb = ttk.Scrollbar(list_frame, orient="horizontal")
        
        columns = ('Name', 'Date', 'Size', 'Type')
        self.backup_tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                                         yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=15)
        vsb.config(command=self.backup_tree.yview)
        hsb.config(command=self.backup_tree.xview)
        
        col_widths = {'Name': 200, 'Date': 120, 'Size': 80, 'Type': 80}
        
        for col in columns:
            self.backup_tree.heading(col, text=col)
            self.backup_tree.column(col, width=col_widths.get(col, 100), anchor='center')
        
        self.backup_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        self.backup_tree.bind('<<TreeviewSelect>>', self.on_backup_select)
        
        # Action Buttons
        action_frame = tk.Frame(right_frame, bg='#ecf0f1', height=50)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        action_frame.pack_propagate(False)
        
        tk.Button(action_frame, text="🔄 Restore Selected", command=self.restore_backup,
                 bg='#f39c12', fg='white', font=('Arial', 10, 'bold'),
                 width=15, cursor='hand2').place(x=20, y=10)
        
        tk.Button(action_frame, text="📤 Export Backup", command=self.export_backup,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 width=12, cursor='hand2').place(x=180, y=10)
        
        tk.Button(action_frame, text="📥 Import Backup", command=self.import_backup,
                 bg='#27ae60', fg='white', font=('Arial', 10),
                 width=12, cursor='hand2').place(x=300, y=10)
        
        tk.Button(action_frame, text="🗑️ Delete", command=self.delete_backup,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 width=8, cursor='hand2').place(x=420, y=10)
        
        # Info Frame
        info_frame = tk.Frame(right_frame, bg='#ecf0f1', height=60)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        info_frame.pack_propagate(False)
        
        self.info_text = tk.Text(info_frame, height=3, width=50, font=('Arial', 9),
                                 relief='solid', bd=1, state='disabled')
        self.info_text.pack(pady=5)
    
    def load_settings(self):
        """Load auto backup settings"""
        try:
            import json
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.auto_backup.set(settings.get('auto_backup', True))
                    self.backup_freq.set(settings.get('frequency', 'Daily'))
                    self.keep_count.set(settings.get('keep_count', '10'))
        except:
            pass
    
    def save_settings(self):
        """Save auto backup settings"""
        try:
            import json
            settings = {
                'auto_backup': self.auto_backup.get(),
                'frequency': self.backup_freq.get(),
                'keep_count': self.keep_count.get()
            }
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            show_success("Settings saved successfully!")
        except Exception as e:
            show_error(f"Error saving settings: {e}")
    
    def load_backup_list(self):
        """Load list of available backups from local folder"""
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        try:
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    size = os.path.getsize(file_path)
                    mod_time = os.path.getmtime(file_path)
                    mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M')
                    
                    # Determine backup type
                    if 'auto' in file.lower():
                        btype = 'Auto'
                    else:
                        btype = 'Manual'
                    
                    # Format size
                    if size < 1024:
                        size_str = f"{size} B"
                    elif size < 1024*1024:
                        size_str = f"{size/1024:.1f} KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f} MB"
                    
                    backups.append((file, mod_date, size_str, btype))
            
            # Sort by date (newest first)
            backups.sort(key=lambda x: x[1], reverse=True)
            
            for b in backups:
                self.backup_tree.insert('', tk.END, iid=b[0], values=b)
                
        except Exception as e:
            print(f"Error loading backups: {e}")
    
    def on_backup_select(self, event):
        """Show backup info when selected"""
        selected = self.backup_tree.selection()
        if not selected:
            return
        
        backup_file = selected[0]
        file_path = os.path.join(self.backup_dir, backup_file)
        
        try:
            # Get file info
            size = os.path.getsize(file_path)
            mod_time = os.path.getmtime(file_path)
            mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get zip info
            with zipfile.ZipFile(file_path, 'r') as zipf:
                file_list = zipf.namelist()
                db_files = [f for f in file_list if f.endswith('.db')]
            
            info = f"Backup File: {backup_file}\n"
            info += f"Created: {mod_date}\n"
            info += f"Size: {size/(1024*1024):.2f} MB\n"
            info += f"Contains: {', '.join(db_files)}"
            
            self.info_text.config(state='normal')
            self.info_text.delete('1.0', tk.END)
            self.info_text.insert('1.0', info)
            self.info_text.config(state='disabled')
            
        except Exception as e:
            show_error(f"Error reading backup: {e}")
    
    def create_backup(self):
        """Create a new backup - ask user where to save"""
        backup_name = self.backup_name.get().strip()
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Add .zip extension if not present
        if not backup_name.endswith('.zip'):
            backup_name += '.zip'
        
        # Ask user where to save the backup
        save_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip")],
            initialfile=backup_name,
            title="Save Backup As",
            initialdir=os.path.expanduser("~/Desktop")  # Start at Desktop
        )
        
        if not save_path:  # User cancelled
            return
        
        try:
            # Database path
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'urban_pulse.db')
            
            if not os.path.exists(db_path):
                show_error("Database file not found!")
                return
            
            # Create zip backup at user-selected location
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(db_path, 'urban_pulse.db')
                
                # Also backup settings if they exist
                settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backup_settings.json')
                if os.path.exists(settings_file):
                    zipf.write(settings_file, 'backup_settings.json')
            
            # Also save a copy in the local backups folder for management
            local_copy = os.path.join(self.backup_dir, os.path.basename(save_path))
            shutil.copy2(save_path, local_copy)
            
            show_success(f"Backup saved successfully!\n\nLocation: {save_path}")
            
            # Refresh list
            self.load_backup_list()
            
            # Generate new default name
            new_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.backup_name.delete(0, tk.END)
            self.backup_name.insert(0, new_name)
            
            # Auto cleanup if enabled
            self.cleanup_old_backups()
            
        except Exception as e:
            show_error(f"Error creating backup: {e}")
    
    def restore_backup(self):
        """Restore selected backup"""
        selected = self.backup_tree.selection()
        if not selected:
            show_error("Select a backup to restore")
            return
        
        backup_file = selected[0]
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        if not ask_yes_no(f"⚠️ WARNING!\n\nRestoring will replace your current database.\n\nAre you sure you want to restore:\n{backup_file}?"):
            return
        
        try:
            # Current database path
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'urban_pulse.db')
            
            # Create backup of current db before restore (just in case)
            if os.path.exists(db_path):
                temp_backup = os.path.join(self.backup_dir, f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
                with zipfile.ZipFile(temp_backup, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    zipf.write(db_path, 'urban_pulse.db')
            
            # Extract the backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extract('urban_pulse.db', os.path.dirname(db_path))
            
            show_success("Database restored successfully!\n\nPlease restart the application.")
            
            # Ask to restart
            if ask_yes_no("Restart application now?"):
                python = sys.executable
                os.execl(python, python, *sys.argv)
            
        except Exception as e:
            show_error(f"Error restoring backup: {e}")
    
    def export_backup(self):
        """Export backup to external location"""
        selected = self.backup_tree.selection()
        if not selected:
            show_error("Select a backup to export")
            return
        
        backup_file = selected[0]
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        # Ask where to save
        export_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("Zip files", "*.zip")],
            initialfile=backup_file,
            title="Export Backup As",
            initialdir=os.path.expanduser("~/Desktop")
        )
        
        if export_path:
            try:
                shutil.copy2(backup_path, export_path)
                show_success(f"Backup exported to:\n{export_path}")
            except Exception as e:
                show_error(f"Error exporting backup: {e}")
    
    def import_backup(self):
        """Import backup from external location"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Zip files", "*.zip"), ("All files", "*.*")],
            title="Select Backup File to Import"
        )
        
        if file_path:
            try:
                # Copy to backup directory
                dest_path = os.path.join(self.backup_dir, os.path.basename(file_path))
                
                # Check if file already exists
                if os.path.exists(dest_path):
                    if not ask_yes_no(f"File {os.path.basename(file_path)} already exists. Overwrite?"):
                        return
                
                shutil.copy2(file_path, dest_path)
                show_success("Backup imported successfully!")
                self.load_backup_list()
                
            except Exception as e:
                show_error(f"Error importing backup: {e}")
    
    def delete_backup(self):
        """Delete selected backup"""
        selected = self.backup_tree.selection()
        if not selected:
            show_error("Select a backup to delete")
            return
        
        backup_file = selected[0]
        backup_path = os.path.join(self.backup_dir, backup_file)
        
        if ask_yes_no(f"Delete backup:\n{backup_file}?"):
            try:
                os.remove(backup_path)
                show_success("Backup deleted")
                self.load_backup_list()
                
                # Clear info text
                self.info_text.config(state='normal')
                self.info_text.delete('1.0', tk.END)
                self.info_text.config(state='disabled')
                
            except Exception as e:
                show_error(f"Error deleting backup: {e}")
    
    def cleanup_old_backups(self):
        """Remove old backups based on settings"""
        try:
            if not self.auto_backup.get():
                return
            
            keep = int(self.keep_count.get())
            
            # Get all backups
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.endswith('.zip'):
                    file_path = os.path.join(self.backup_dir, file)
                    mod_time = os.path.getmtime(file_path)
                    backups.append((mod_time, file_path, file))
            
            # Sort by date (oldest first)
            backups.sort()
            
            # Remove excess backups
            while len(backups) > keep:
                _, file_path, file_name = backups.pop(0)
                os.remove(file_path)
                print(f"Removed old backup: {file_name}")
                
        except Exception as e:
            print(f"Error during cleanup: {e}")

# For testing
if __name__ == "__main__":
    import sys
    root = tk.Tk()
    root.withdraw()
    bm = BackupManager(root, "admin", datetime.now().strftime('%Y-%m-%d'))
    root.mainloop()