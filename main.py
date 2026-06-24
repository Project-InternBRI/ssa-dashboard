import sys
import os
from PySide6.QtWidgets import QApplication
from ui.splash_screen import SplashScreen
from ui.main_window import MainWindow

def load_stylesheet(app):
    # Load stylesheet if exists
    style_path = os.path.join(os.path.dirname(__file__), "assets", "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

def main():
    app = QApplication(sys.argv)
    
    # Load global styling
    load_stylesheet(app)
    
    # Initialize main window (do not show yet)
    main_window = MainWindow()
    
    # Initialize and show splash screen
    splash = SplashScreen()
    
    # Connect splash screen finish signal to show main window
    splash.splash_finished.connect(main_window.show)
    
    # Start the splash screen process
    splash.start_splash()
    splash.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()