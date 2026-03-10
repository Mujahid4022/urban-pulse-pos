# create_backup.py
import zipfile
import os
from datetime import datetime

def backup_project():
    # Files to exclude
    exclude = ['.db', '.log', '.bak', '__pycache__', '.git', '.pyc']
    
    # Create backup name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"Urban_Pulse_Backup_{timestamp}.zip"
    
    print("="*60)
    print(f"📦 CREATING BACKUP: {backup_name}")
    print("="*60)
    
    files_added = 0
    
    with zipfile.ZipFile(backup_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude]
            
            for file in files:
                # Skip excluded file types
                if any(file.endswith(ext) for ext in exclude if not ext.startswith('.')):
                    continue
                if any(file.endswith(ext) for ext in ['.pyc', '.log', '.bak']):
                    continue
                
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, '.')
                zipf.write(file_path, arcname)
                files_added += 1
                print(f"  ✅ Added: {arcname}")
    
    print("-"*60)
    print(f"✅ BACKUP COMPLETE!")
    print(f"  📁 File: {backup_name}")
    print(f"  📊 Files backed up: {files_added}")
    print(f"  💾 Size: {os.path.getsize(backup_name) / 1024 / 1024:.2f} MB")
    print("="*60)

if __name__ == "__main__":
    backup_project()