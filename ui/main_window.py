"""
main_window.py — SSA Dashboard Bank BRI
Sidebar slim 88px: ikon + label vertikal, active = solid blue bg.
Header 56px: nama halaman + jam.
Tanpa border di mana pun.
"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QSystemTrayIcon, QMenu, QApplication,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QDateTime, QSize
from PySide6.QtGui import QIcon, QAction, QPixmap, QColor, QFont, QCursor, QPainter, QImage
from PySide6.QtSvg import QSvgRenderer

from ui.beranda_widget import BerandaWidget
from ui.upload_widget import UploadWidget
from ui.input_rka_widget import InputRKAWidget
from ui.preview_table import PreviewTableWidget
from ui.history_widget import HistoryWidget
from ui.input_rka_widget import InputRKAWidget
from ui.success_popup import SuccessPopup
from ui.confirm_popup import ConfirmPopup
from core.history_manager import load_history
from core.processor import count_kc
from core.db_manager import get_connection


# ─── NAV ITEM WIDGET ─────────────────────────────────────────────────
class NavItem(QFrame):
    def __init__(self, icon_name, label, parent=None):
        super().__init__(parent)
        self.setFixedSize(72, 72)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

        self._active = False
        self._icon_name = icon_name

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 12, 0, 12)
        lay.setSpacing(6)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._icon_lbl = QLabel()
        self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_lbl.setFixedSize(24, 24)
        self._icon_lbl.setStyleSheet("background: transparent;")

        self._text_lbl = QLabel(label)
        self._text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_lbl.setWordWrap(True)
        self._text_lbl.setFixedWidth(68)
        self._text_lbl.setStyleSheet(
            "font-size: 9px; color: #94A3B8; font-weight: 500; background: transparent;")

        lay.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._text_lbl, 0, Qt.AlignmentFlag.AlignHCenter)
        self._refresh()

    def _tint_icon(self, color_hex):
        icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", self._icon_name)
        if not os.path.exists(icon_path):
            self._icon_lbl.setText("?")
            return
            
        with open(icon_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
            
        # Directly replace the fill attribute that comes from Material Symbols
        svg_content = svg_content.replace('fill="#000000"', f'fill="{color_hex}"')
        # Fallback for other standard icons
        svg_content = svg_content.replace('currentColor', color_hex)
        
        # Force the SVG to render at 48x48 (2x resolution) for Retina displays
        svg_content = svg_content.replace('width="24px"', 'width="48px"')
        svg_content = svg_content.replace('height="24px"', 'height="48px"')
        
        pix = QPixmap()
        pix.loadFromData(svg_content.encode('utf-8'))
        pix.setDevicePixelRatio(2.0)
        
        self._icon_lbl.setPixmap(pix)

    def set_active(self, active: bool):
        self._active = active
        self._refresh()

    def _refresh(self):
        if self._active:
            self.setStyleSheet("""
                NavItem {
                    background-color: #2563EB;
                    border-radius: 12px;
                }
            """)
            self._tint_icon("#FFFFFF")
            self._text_lbl.setStyleSheet(
                "font-size: 9px; color: #FFFFFF; font-weight: 600; background: transparent;")
        else:
            self.setStyleSheet("""
                NavItem {
                    background-color: transparent;
                    border-radius: 12px;
                }
            """)
            self._tint_icon("#94A3B8")
            self._text_lbl.setStyleSheet(
                "font-size: 9px; color: #94A3B8; font-weight: 500; background: transparent;")

    def enterEvent(self, event):
        if not self._active:
            self.setStyleSheet("""
                NavItem {
                    background-color: #2563EB;
                    border-radius: 12px;
                }
            """)
            self._tint_icon("#FFFFFF")
            self._text_lbl.setStyleSheet("font-size: 9px; color: #FFFFFF; font-weight: 600; background: transparent;")
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self._active:
            self._refresh()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.parent_clicked()
        super().mousePressEvent(event)

    def parent_clicked(self):
        """Override in subclass or connect externally."""
        pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BRIVIEW — Bank BRI")
        self.setMinimumSize(1100, 700)
        self.resize(1280, 800)

        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self._data_dict: dict | None = None
        self._nav_items: list[NavItem] = []
        self.init_ui()
        self.init_system_tray()

    # ─── INIT UI ──────────────────────────────────────────────────
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        base_layout = QVBoxLayout(central)
        base_layout.setContentsMargins(0, 0, 0, 0)
        base_layout.setSpacing(0)

        main_area = QWidget()
        main_area.setStyleSheet("background-color: #F1F5F9;")
        main_layout = QHBoxLayout(main_area)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # ── SIDEBAR (88px, floating white) ───────────────
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(88)
        self.sidebar.setStyleSheet("QFrame#sidebar { background-color: #FFFFFF; border-radius: 16px; }")

        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect(self.sidebar)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        self.sidebar.setGraphicsEffect(shadow)

        sb_lay = QVBoxLayout(self.sidebar)
        sb_lay.setContentsMargins(8, 24, 8, 24)
        sb_lay.setSpacing(0)
        sb_lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Logo di paling atas
        logo_container = QWidget()
        logo_container.setFixedSize(72, 60)
        logo_container.setStyleSheet("background: transparent;")
        logo_inner = QVBoxLayout(logo_container)
        logo_inner.setContentsMargins(0, 0, 0, 0)
        logo_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_lbl = QLabel()
        logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(logo_path):
            # Scale to 144x64 (2x the logical size of 72x32) to fit perfectly within the 72px container width
            logo_pix = QPixmap(logo_path)
            logo_pix = logo_pix.scaled(144, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_pix.setDevicePixelRatio(2.0)
            logo_lbl.setPixmap(logo_pix)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            logo_lbl.setText("B")
            logo_lbl.setFixedSize(40, 40)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            logo_lbl.setStyleSheet(
                "background: #2563EB; color: white; font-weight: 800;"
                "font-size: 20px; border-radius: 10px;")
        logo_inner.addWidget(logo_lbl)
        sb_lay.addWidget(logo_container, 0, Qt.AlignmentFlag.AlignHCenter)
        sb_lay.addSpacing(16)

        # Garis pemisah tipis
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet("background: #E2E8F0;")
        sb_lay.addWidget(div)
        sb_lay.addSpacing(16)

        sb_lay.addStretch()

        nav_config = [
            ("home.svg", "BERANDA"),
            ("input.svg", "INPUT RKA"),
            ("upload.svg", "UPLOAD"),
            ("table.svg", "PREVIEW"),
            ("history.svg", "RIWAYAT"),
        ]

        for i, (icon, label) in enumerate(nav_config):
            item = NavItem(icon, label)
            item.mouseReleaseEvent = lambda e, idx=i: self.switch_page(idx)
            self._nav_items.append(item)
            sb_lay.addWidget(item, 0, Qt.AlignmentFlag.AlignHCenter)
            sb_lay.addSpacing(4)

        sb_lay.addStretch()

        # Versi
        ver = QLabel("v1.2")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ver.setStyleSheet("color: #334155; font-size: 9px; background: transparent;")
        ver.setFixedWidth(72)
        sb_lay.addWidget(ver, 0, Qt.AlignmentFlag.AlignHCenter)

        # ── CONTENT AREA ──────────────────────────────────────────
        content_area = QWidget()
        content_area.setStyleSheet("background: #F1F5F9;")
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header bar
        self.header_bar = QFrame()
        self.header_bar.setObjectName("headerBar")
        self.header_bar.setFixedHeight(60)
        self.header_bar.setStyleSheet("""
            QFrame#headerBar {
                background-color: transparent;
            }
        """)

        hdr_lay = QHBoxLayout(self.header_bar)
        hdr_lay.setContentsMargins(28, 0, 28, 0)
        hdr_lay.setSpacing(0)

        self.page_title = QLabel("Beranda")
        self.page_title.setStyleSheet(
            "font-size: 17px; font-weight: 700; color: #0F172A;")
        hdr_lay.addWidget(self.page_title)
        hdr_lay.addStretch()

        self.time_label = QLabel()
        self.time_label.setStyleSheet("font-size: 12px; color: #94A3B8;")
        hdr_lay.addWidget(self.time_label)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_time)
        self._timer.start(1000)
        self._update_time()

        # Stacked pages
        self.stacked_widget = QStackedWidget()
        self.page_beranda = BerandaWidget()
        self.page_upload = UploadWidget()
        self.page_rka = InputRKAWidget()
        self.page_preview = PreviewTableWidget()
        self.page_history = HistoryWidget()

        self.stacked_widget.addWidget(self.page_beranda)
        self.stacked_widget.addWidget(self.page_rka)
        self.stacked_widget.addWidget(self.page_upload)
        self.stacked_widget.addWidget(self.page_preview)
        self.stacked_widget.addWidget(self.page_history)

        content_layout.addWidget(self.header_bar)
        content_layout.addWidget(self.stacked_widget, 1)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(content_area, 1)

        base_layout.addWidget(main_area, 1)

        # ── CONNECTIONS ───────────────────────────────────────────
        self.page_beranda.navigate_to.connect(self.switch_page)
        self.page_preview.navigate_to.connect(self.switch_page)
        self.page_history.navigate_to.connect(self.switch_page)
        self.page_upload.generate_finished.connect(self._on_generate_finished)

        if hasattr(self.page_upload, 'data_cleared'):
            self.page_upload.data_cleared.connect(self._on_data_cleared)

        # Initial
        if self._nav_items:
            self._nav_items[0].set_active(True)
        self._refresh_beranda()

    # ─── TIME ─────────────────────────────────────────────────────
    def _update_time(self):
        self.time_label.setText(
            QDateTime.currentDateTime().toString("ddd, dd MMM yyyy  •  HH:mm"))

    def switch_page(self, index: int):
        _titles = [
            "Beranda", "Input RKA", "Upload & Generate",
            "Preview Tabel", "Riwayat Generate"
        ]
        for i, item in enumerate(self._nav_items):
            item.set_active(i == index)

        if 0 <= index < len(_titles):
            self.page_title.setText(_titles[index])

        self.stacked_widget.setCurrentIndex(index)

        if index == 0:
            self._refresh_beranda()
        elif index == 4:
            self.page_history.refresh()

    # ─── GENERATE FINISHED ────────────────────────────────────────
    def _on_generate_finished(self, data_dict: dict, elapsed: float = 0.0):
        self._data_dict = data_dict
        self.page_preview.load_data(data_dict)
        self.page_history.refresh()
        self._refresh_beranda()

        stats = data_dict.get('__stats__', {})
        self._popup = SuccessPopup(parent=self, stats=stats, elapsed=elapsed)
        self._popup.view_preview.connect(lambda: self.switch_page(3))
        self._popup.export_excel.connect(self.page_preview._export)
        self._popup.center_on_parent()
        self._popup.show_animated()

    # ─── DATA CLEARED ─────────────────────────────────────────────
    def _on_data_cleared(self):
        self._data_dict = None
        self.page_preview.show_empty_cleared()
        self._refresh_beranda()

    # ─── REFRESH BERANDA ──────────────────────────────────────────
    def _refresh_beranda(self):
        history = load_history()
        
        # Check files
        s_ready = self.page_upload._path_s_berjalan is not None
        p_ready = self.page_upload._path_p_berjalan is not None
        
        # Check RKA
        rka_ready = False
        try:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM rka_data_v2")
            if c.fetchone()[0] > 0:
                rka_ready = True
        except Exception:
            pass
            
        dash_ready = self._data_dict is not None
        self.page_beranda.refresh_stats(s_ready, p_ready, rka_ready, dash_ready, history)
        self.page_beranda.refresh_activity(history)

    # ─── SYSTEM TRAY ──────────────────────────────────────────────
    def init_system_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "icons", "bri_logo.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(
                self.style().standardIcon(
                    self.style().StandardPixmap.SP_ComputerIcon))
        tray_menu = QMenu()
        act_restore = QAction("Buka SSA Dashboard", self)
        act_restore.triggered.connect(self.showNormal)
        act_quit = QAction("Keluar", self)
        act_quit.triggered.connect(self._force_quit)
        tray_menu.addAction(act_restore)
        tray_menu.addAction(act_quit)
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "SSA Dashboard", "Aplikasi berjalan di background",
                    QSystemTrayIcon.MessageIcon.Information, 2000)
        super().changeEvent(event)

    def closeEvent(self, event):
        reply = ConfirmPopup.ask(
            self,
            "Konfirmasi Keluar",
            "Yakin ingin keluar dari BRIVIEW?",
            action_text="Keluar",
            action_color="#DC2626"
        )
        if reply:
            event.accept()
        else:
            event.ignore()

    def _force_quit(self):
        self.tray_icon.hide()
        QApplication.quit()