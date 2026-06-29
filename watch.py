import sys
import time
import subprocess
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ReloadHandler(FileSystemEventHandler):
    def __init__(self):
        super().__init__()
        self.process = None
        self.last_reload = time.time()
        self.start_app()

    def start_app(self):
        if self.process:
            self.process.kill()
            self.process.wait()
            
        print("\n[+] Memulai ulang aplikasi (Live Reload)...")
        # Run main.py using the current python executable
        self.process = subprocess.Popen([sys.executable, "main.py"])

    def on_modified(self, event):
        # Only reload if a python file is changed and avoid multiple triggers within 1 second
        if event.src_path.endswith('.py') and not event.is_directory:
            current_time = time.time()
            if current_time - self.last_reload > 1.0:
                print(f"\n[!] Perubahan terdeteksi pada file: {os.path.basename(event.src_path)}")
                self.last_reload = current_time
                self.start_app()

if __name__ == "__main__":
    path = "."
    
    # Check if main.py exists in current directory
    if not os.path.exists("main.py"):
        print("Error: main.py tidak ditemukan di direktori saat ini.")
        sys.exit(1)
        
    print("==================================================")
    print("🚀 LIVE RELOAD AKTIF")
    print("Setiap kali Anda menyimpan (.py), aplikasi akan otomatis di-restart.")
    print("Tekan Ctrl+C di terminal ini untuk berhenti.")
    print("==================================================")
    
    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()
            print("\n[+] Live Reload dihentikan.")
    observer.join()
