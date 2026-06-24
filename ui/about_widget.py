from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class AboutWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        logo = QLabel("SSA Dashboard")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #1E3A5F;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        desc = QLabel("Aplikasi pengolahan data laporan dashboard perbankan.\\nBank BRI — AH Gunsar Jakarta Region")
        desc.setStyleSheet("font-size: 14px; color: #64748B;")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        
        layout.addWidget(logo)
        layout.addSpacing(10)
        layout.addWidget(desc)
