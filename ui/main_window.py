"""
main_window.py — Window utama aplikasi.
Mengelola navigasi sidebar, sistem tray, dan mengatur perpindahan antar halaman.
"""
import os
import sys
from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QLabel, QPushButton, QStackedWidget, QFrame, 
                               QSystemTrayIcon, QMenu, QMessageBox, QApplication)
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QIcon, QAction, QPixmap

from ui.beranda_widget import BerandaWidget
from ui.chart_widget import ChartWidget
from ui.upload_widget import UploadWidget
from ui.preview_table import PreviewTableWidget
from ui.history_widget import HistoryWidget
from core.history_manager import load_history


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSA Dashboard — Bank BRI")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)
        
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.init_ui()
        self.init_system_tray()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.base_layout = QVBoxLayout(self.central_widget)
        self.base_layout.setContentsMargins(0, 0, 0, 0)
        self.base_layout.setSpacing(0)
        
        self.main_area = QWidget()
        self.main_layout = QHBoxLayout(self.main_area)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # 1. SIDEBAR
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(240)
        self.sidebar.setStyleSheet("QFrame#sidebar { background-color: #0D2240; border-right: 1px solid rgba(255,255,255,0.05); }")
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(16, 20, 16, 20)
        self.sidebar_layout.setSpacing(0)
        
        logo_container = QHBoxLayout()
        logo_container.setSpacing(12)
        
        self.sidebar_logo = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.sidebar_logo.setPixmap(pixmap)
        else:
            self.sidebar_logo.setText("S")
            self.sidebar_logo.setFixedSize(36, 36)
            self.sidebar_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.sidebar_logo.setStyleSheet("background-color: #2563EB; color: white; font-weight: bold; font-size: 18px; border-radius: 8px;")
        
        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        lbl_app_name = QLabel("Dashboard SSA")
        lbl_app_name.setStyleSheet("color: white; font-weight: bold; font-size: 15px;")
        lbl_app_sub = QLabel("AH Gunsar Jakarta")
        lbl_app_sub.setStyleSheet("color: #64879F; font-size: 11px;")
        title_col.addWidget(lbl_app_name)
        title_col.addWidget(lbl_app_sub)
        
        logo_container.addWidget(self.sidebar_logo)
        logo_container.addLayout(title_col)
        logo_container.addStretch()
        
        self.sidebar_layout.addLayout(logo_container)
        self.sidebar_layout.addSpacing(28)
        
        workspace_lbl = QLabel("MENU")
        workspace_lbl.setStyleSheet("color: #4A7A9B; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;")
        self.sidebar_layout.addWidget(workspace_lbl)
        self.sidebar_layout.addSpacing(8)
        
        self.nav_buttons = []
        nav_items = [
            ("Beranda", "home"),
            ("Dashboard", "dashboard"),
            ("Upload & Generate", "upload"),
            ("Preview Tabel", "table"),
            ("Riwayat Generate", "history"),
        ]
        
        for name, icon_name in nav_items:
            btn = QPushButton(f"  {name}")
            btn.setObjectName(f"nav_{icon_name}")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setCheckable(True)
            btn.setFixedHeight(42)
            btn.setStyleSheet("""
                QPushButton { color: #8BADC4; text-align: left; padding-left: 16px; border: none; font-size: 14px; border-radius: 8px; background-color: transparent; }
                QPushButton:hover { color: white; background-color: rgba(255, 255, 255, 0.06); }
                QPushButton:checked { color: white; background-color: #2563EB; font-weight: bold; }
            """)
            self.nav_buttons.append(btn)
            self.sidebar_layout.addWidget(btn)
            self.sidebar_layout.addSpacing(4)
        
        self.sidebar_layout.addStretch()
        
        ver_label = QLabel("v1.1.0")
        ver_label.setStyleSheet("color: #3D5F7A; font-size: 10px;")
        ver_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sidebar_layout.addWidget(ver_label)
        
        # 2. CONTENT AREA
        self.content_area = QWidget()
        self.content_area.setStyleSheet("background-color: #F8FAFC;")
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        self.header_bar = QFrame()
        self.header_bar.setObjectName("headerBar")
        self.header_bar.setFixedHeight(64)
        self.header_bar.setStyleSheet("QFrame#headerBar { background-color: #FFFFFF; border-bottom: 1px solid #E8EDF2; }")
        
        self.header_layout = QHBoxLayout(self.header_bar)
        self.header_layout.setContentsMargins(32, 0, 32, 0)
        
        self.header_title_container = QVBoxLayout()
        self.header_title_container.setSpacing(2)
        
        self.page_title = QLabel("Beranda")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        
        self.page_subtitle = QLabel("Ringkasan workspace SSA — AH Gunsar Jakarta Region")
        self.page_subtitle.setStyleSheet("font-size: 12px; color: #94A3B8;")
        
        self.header_title_container.addWidget(self.page_title)
        self.header_title_container.addWidget(self.page_subtitle)
        self.header_layout.addLayout(self.header_title_container)
        
        self.header_layout.addStretch()
        
        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 13px; color: #64748B;")
        self.header_layout.addWidget(self.time_label)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()
        
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet("background-color: #F8FAFC;")
        
        self.page_beranda = BerandaWidget()
        self.page_dashboard = ChartWidget()
        self.page_upload = UploadWidget()
        self.page_preview = PreviewTableWidget()
        self.page_history = HistoryWidget()
        
        self.stacked_widget.addWidget(self.page_beranda)     # 0
        self.stacked_widget.addWidget(self.page_dashboard)   # 1
        self.stacked_widget.addWidget(self.page_upload)      # 2
        self.stacked_widget.addWidget(self.page_preview)     # 3
        self.stacked_widget.addWidget(self.page_history)     # 4
        
        self.content_layout.addWidget(self.header_bar)
        self.content_layout.addWidget(self.stacked_widget)
        
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.content_area)
        
        # 3. STATUS BAR
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(28)
        self.status_bar.setStyleSheet("""
            QFrame { background-color: #FAFBFC; border-top: 1px solid #E2E8F0; }
            QLabel { color: #94A3B8; font-size: 11px; }
        """)
        sb_layout = QHBoxLayout(self.status_bar)
        sb_layout.setContentsMargins(20, 0, 20, 0)
        
        sb_layout.addWidget(QLabel("SSA Dashboard — Bank BRI"))
        sb_layout.addStretch()
        sb_layout.addWidget(QLabel("v1.1.0"))
        
        self.base_layout.addWidget(self.main_area)
        self.base_layout.addWidget(self.status_bar)
        
        # 4. CONNECTIONS
        self._page_subtitles = [
            "Ringkasan workspace SSA — AH Gunsar Jakarta Region",
            "Ringkasan kinerja per KC",
            "Unggah file dan jalankan proses konsolidasi",
            "Hasil konsolidasi dashboard SSA",
            "Daftar dashboard yang pernah dihasilkan",
        ]
        
        # Navigasi sidebar
        for i, btn in enumerate(self.nav_buttons):
            btn.clicked.connect(lambda checked, idx=i: self.switch_page(idx))
            
        # Emit signal navigasi antar widget
        self.page_beranda.navigate_to.connect(self.switch_page)
        self.page_dashboard.navigate_to.connect(self.switch_page)
        self.page_preview.navigate_to.connect(self.switch_page)
        self.page_history.navigate_to.connect(self.switch_page)

        # Proses generate selesai
        self.page_upload.generate_finished.connect(self._on_generate_finished)

        # Initial state
        if self.nav_buttons:
            self.nav_buttons[0].setChecked(True)
        self._refresh_beranda()

    def update_time(self):
        self.time_label.setText(QDateTime.currentDateTime().toString("dd MMM yyyy  •  hh:mm"))

    def switch_page(self, index):
        page_titles = ["Beranda", "Dashboard", "Upload & Generate", "Preview Tabel", "Riwayat Generate"]
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        
        if index < len(page_titles):
            self.page_title.setText(page_titles[index])
        if index < len(self._page_subtitles):
            self.page_subtitle.setText(self._page_subtitles[index])
            
        self.stacked_widget.setCurrentIndex(index)
        
        # Refresh logic per halaman
        if index == 0:
            self._refresh_beranda()
        elif index == 4:
            self.page_history.refresh()

    def _on_generate_finished(self, data_dict: dict):
        # Update widget-widget lain dengan data baru
        self.page_preview.load_data(data_dict)
        self.page_dashboard.load_data(data_dict)
        self.page_history.refresh()
        self._refresh_beranda()

        # Otomatis pindah ke Preview Tabel
        self.switch_page(3)

    def _refresh_beranda(self):
        history = load_history()
        self.page_beranda.refresh_stats(self.page_upload.get_file_count(), history)
        self.page_beranda.refresh_activity(history)
        
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
        self.tray_menu = QMenu()
        restore_action = QAction("Buka SSA Dashboard", self)
        restore_action.triggered.connect(self.showNormal)
        
        quit_action = QAction("Keluar", self)
        quit_action.triggered.connect(self.force_quit)
        
        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage("SSA Dashboard", "Aplikasi berjalan di background", QSystemTrayIcon.MessageIcon.Information, 2000)
        super().changeEvent(event)

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Konfirmasi Keluar', "Yakin ingin keluar dari SSA Dashboard?\nPastikan Anda sudah mengekspor data yang diperlukan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()
            
    def force_quit(self):
        self.tray_icon.hide()
        QApplication.quit()