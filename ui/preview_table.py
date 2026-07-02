from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QPushButton, QScrollArea, QSizePolicy, QGridLayout, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QDateTime
from PySide6.QtGui import QFont, QColor, QCursor, QIcon, QPixmap, QPainter, QBrush, QPen
import os

class PreviewTableWidget(QWidget):
    navigate_to = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self._card_stat_labels = {}  # {card_key: QLabel}
        # File paths — diset dari main_window setelah generate
        self._path_s_berjalan: str | None = None
        self._path_p_berjalan: str | None = None
        self._hist_s: list = []
        self._hist_p: list = []
        self._init_ui()
        
        # Timer for live clock
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()
        
        self.show_empty_cleared()
    
    def set_source_paths(self, path_s_berjalan, path_p_berjalan,
                         hist_s=None, hist_p=None):
        """Simpan path file SSA agar kartu KCP/Unit bisa export secara mandiri."""
        self._path_s_berjalan = path_s_berjalan
        self._path_p_berjalan = path_p_berjalan
        self._hist_s = hist_s or []
        self._hist_p = hist_p or []
        

    def _init_ui(self):
        # Root layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        
        # Scroll area for the whole dashboard
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background-color: #F8FAFC; }")
        
        content_widget = QWidget()
        content_widget.setObjectName("main_content")
        content_widget.setStyleSheet("QWidget#main_content { background-color: #F8FAFC; }")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(24)
        
        # 1. Header Row
        header_row = QHBoxLayout()
        title_col = QVBoxLayout()
        title_lbl = QLabel("Dashboard Center")
        title_lbl.setStyleSheet("font-size: 24px; font-weight: bold; color: #0F172A;")
        sub_lbl = QLabel("Pusat informasi dashboard hasil generate")
        sub_lbl.setStyleSheet("font-size: 14px; color: #64748B;")
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        
        header_row.addLayout(title_col)
        header_row.addStretch()
        
        # Clock
        self.clock_lbl = QLabel()
        self.clock_lbl.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 500;")
        header_row.addWidget(self.clock_lbl, 0, Qt.AlignmentFlag.AlignVCenter)
        
        content_layout.addLayout(header_row)
        
        # 2. Banner Card
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame#banner {
                background-color: #EFF6FF;
                border: 1px solid #DBEAFE;
                border-radius: 16px;
            }
        """)
        banner.setObjectName("banner")
        
        # Add shadow to banner
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 15))
        shadow.setOffset(0, 4)
        banner.setGraphicsEffect(shadow)
        
        banner_layout = QHBoxLayout(banner)
        banner_layout.setContentsMargins(30, 24, 30, 24)
        banner_layout.setSpacing(20)
        
        # Success Icon (left)
        self.icon_bg_frame = QFrame()
        self.icon_bg_frame.setFixedSize(110, 110)
        self.icon_bg_frame.setStyleSheet("background-color: #FFFFFF; border-radius: 55px;")
        
        icon_layout = QVBoxLayout(self.icon_bg_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.icon_status = QLabel()
        self.icon_status.setFixedSize(80, 80)
        self.icon_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_layout.addWidget(self.icon_status)
        banner_layout.addWidget(self.icon_bg_frame)
        
        # Banner Text
        banner_text_col = QVBoxLayout()
        banner_text_col.setSpacing(6)
        self.b_title = QLabel("Menunggu Proses Generate")
        self.b_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B; background: transparent;")
        self.b_sub = QLabel("Silakan upload file SSA dan lakukan generate data.")
        self.b_sub.setStyleSheet("font-size: 14px; color: #64748B; background: transparent;")
        
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 8, 0, 0)
        
        footer_icon = QLabel()
        footer_icon.setFixedSize(16, 16)
        path_history = "assets/icons/history.svg"
        if os.path.exists(path_history):
            pix = QPixmap(path_history).scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(2.0)
            footer_icon.setPixmap(pix)
        footer_icon.setStyleSheet("background: transparent;")
        
        self.last_gen_lbl = QLabel("Terakhir di-generate: Belum ada data")
        self.last_gen_lbl.setStyleSheet("font-size: 12px; color: #94A3B8; background: transparent;")
        
        footer_layout.addWidget(footer_icon)
        footer_layout.addWidget(self.last_gen_lbl)
        footer_layout.addStretch()
        
        banner_text_col.addWidget(self.b_title)
        banner_text_col.addWidget(self.b_sub)
        banner_text_col.addLayout(footer_layout)
        
        banner_layout.addLayout(banner_text_col)
        
        banner_layout.addStretch()
        
        # Center Illustration
        self.illus_lbl = QLabel()
        self.illus_lbl.setFixedSize(260, 130)
        self.illus_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner_layout.addWidget(self.illus_lbl)
        
        banner_layout.addSpacing(20)
        
        # Divider
        div = QFrame()
        div.setFixedWidth(2)
        div.setStyleSheet("background-color: #BFDBFE; border: none;")
        banner_layout.addWidget(div)
        
        banner_layout.addSpacing(20)
        
        # Right Stats
        stat_col = QVBoxLayout()
        self.stat_num = QLabel("4")
        self.stat_num.setStyleSheet("font-size: 48px; font-weight: 900; color: #2563EB; background: transparent;")
        self.stat_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stat_lbl1 = QLabel("Dashboard")
        self.stat_lbl1.setStyleSheet("font-size: 14px; color: #2563EB; font-weight: bold; background: transparent;")
        self.stat_lbl1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stat_lbl2 = QLabel("Siap Digunakan")
        self.stat_lbl2.setStyleSheet("font-size: 14px; color: #2563EB; font-weight: bold; background: transparent;")
        self.stat_lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stat_col.addWidget(self.stat_num)
        stat_col.addWidget(self.stat_lbl1)
        stat_col.addWidget(self.stat_lbl2)
        
        banner_layout.addLayout(stat_col)
        content_layout.addWidget(banner)
        
        # 3. Section Title
        sec_row = QHBoxLayout()
        sec_col = QVBoxLayout()
        sec_title = QLabel("Pilih Dashboard yang Ingin Diekspor")
        sec_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A;")
        sec_sub = QLabel("Pilih salah satu dashboard di bawah untuk mengekspor hasil analisis dalam format yang tersedia.")
        sec_sub.setStyleSheet("font-size: 13px; color: #64748B;")
        sec_col.addWidget(sec_title)
        sec_col.addWidget(sec_sub)
        
        sec_row.addLayout(sec_col)
        sec_row.addStretch()
        
        btn_refresh = QPushButton(" ↻ Refresh Data")
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.setStyleSheet("""
            QPushButton {
                background: #FFFFFF; border: 1px solid #E2E8F0;
                border-radius: 8px; padding: 8px 16px;
                color: #475569; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background: #F8FAFC; border-color: #CBD5E1; }
        """)
        sec_row.addWidget(btn_refresh, 0, Qt.AlignmentFlag.AlignVCenter)
        
        content_layout.addLayout(sec_row)
        
        # 4. Cards Layout (4 Columns)
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        # Card definitions: (key, color, icon_path, title, desc, stat_title, export_label)
        cards_config = [
            {
                "key": "kc",
                "color": "#2563EB",           # Biru – sesuai warna KC pada screenshot
                "icon_path": "assets/illus_logo_kc_dash.png",
                "title": "KC\nDashboard",
                "desc": "Menampilkan performa dan pencapaian seluruh Kantor Cabang (KC).",
                "stat_title": "Total KC",
            },
            {
                "key": "kcp",
                "color": "#0EA5E9",           # Biru muda – KCP Dashboard
                "icon_path": "assets/illus_logo_kcp_dash.png",
                "title": "KCP\nDashboard",
                "desc": "Menampilkan performa dan pencapaian seluruh KCP.",
                "stat_title": "Total KCP",
            },
            {
                "key": "unit",
                "color": "#F97316",           # Oranye – Unit Dashboard
                "icon_path": "assets/illus_logo_unit_dash.png",
                "title": "Unit\nDashboard",
                "desc": "Menampilkan performa dan komposisi unit kerja.",
                "stat_title": "Total Unit",
            },
            {
                "key": "produk",
                "color": "#1E3A8A",           # Biru tua – Monitoring Produk
                "icon_path": "assets/illus_logo_moni_dash.png",
                "title": "Monitoring Produk\nDashboard",
                "desc": "Menampilkan monitoring kinerja produk simpanan (Tabungan, Giro, Deposito, CASA, DPK).",
                "stat_title": "Produk Simpanan",
            },
        ]
        
        for cfg in cards_config:
            c, stat_lbl = self._build_export_card(cfg)
            self._card_stat_labels[cfg["key"]] = stat_lbl
            cards_layout.addWidget(c)
            
        content_layout.addLayout(cards_layout)
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        root.addWidget(scroll)

    def _build_export_card(self, data: dict):
        """Build an export card. Returns (card_widget, stat_val_label)."""
        color = data["color"]
        key = data["key"]
        
        # Lighten the color for icon background (10% opacity)
        icon_bg_colors = {
            "#2563EB": "#DBEAFE",
            "#0EA5E9": "#E0F2FE",
            "#F97316": "#FFEDD5",
            "#1E3A8A": "#DBEAFE",
        }
        icon_bg = icon_bg_colors.get(color, "#EFF6FF")
        
        card = QFrame()
        card.setObjectName(f"card_{key}")
        card.setStyleSheet(f"""
            QFrame#card_{key} {{
                background: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-radius: 16px;
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setColor(QColor(37, 99, 235, 12))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 22, 20, 20)
        lay.setSpacing(14)
        
        # ── Header: Icon circle + Title ─────────────────────────────
        h_lay = QHBoxLayout()
        h_lay.setSpacing(14)
        
        icon_circle = QFrame()
        icon_circle.setFixedSize(64, 64)
        icon_circle.setStyleSheet(
            f"background-color: {icon_bg}; border-radius: 32px; border: none;"
        )
        icon_inner = QVBoxLayout(icon_circle)
        icon_inner.setContentsMargins(0, 0, 0, 0)
        icon_inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        icon_lbl = QLabel()
        icon_lbl.setFixedSize(44, 44)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background: transparent;")
        if os.path.exists(data["icon_path"]):
            pix = QPixmap(data["icon_path"]).scaled(88, 88, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(2.0)
            icon_lbl.setPixmap(pix)
        icon_inner.addWidget(icon_lbl)
        h_lay.addWidget(icon_circle)
        
        title_lbl = QLabel(data["title"])
        title_lbl.setStyleSheet(
            f"font-size: 14px; font-weight: 800; color: {color}; background: transparent; line-height: 1.4;"
        )
        h_lay.addWidget(title_lbl)
        h_lay.addStretch()
        lay.addLayout(h_lay)
        
        # ── Description ─────────────────────────────────────────────
        desc_lbl = QLabel(data["desc"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #64748B; background: transparent; min-height: 36px;")
        lay.addWidget(desc_lbl)
        
        # ── Stat Card ───────────────────────────────────────────────
        stat_frame = QFrame()
        stat_frame.setStyleSheet(
            f"background: {icon_bg}; border-radius: 10px; border: none;"
        )
        stat_lay = QVBoxLayout(stat_frame)
        stat_lay.setContentsMargins(14, 10, 14, 10)
        stat_lay.setSpacing(2)
        
        stitle = QLabel(data["stat_title"])
        stitle.setStyleSheet("font-size: 11px; color: #64748B; background: transparent;")
        stat_lay.addWidget(stitle)
        
        stat_val_lbl = QLabel("Tidak ada data")
        stat_val_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 900; color: {color}; background: transparent;"
        )
        stat_lay.addWidget(stat_val_lbl)
        
        lay.addWidget(stat_frame)
        lay.addStretch()
        
        # ── Export Button (solid color) ──────────────────────────────
        btn_exp = QPushButton("Ekspor Dashboard")
        btn_exp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Darken color on hover
        hover_colors = {
            "#2563EB": "#1D4ED8",
            "#0EA5E9": "#0284C7",
            "#F97316": "#EA6800",
            "#1E3A8A": "#172554",
        }
        hover = hover_colors.get(color, color)
        btn_exp.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 11px 16px;
                font-weight: 700;
                font-size: 13px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:pressed {{ background: {hover}; }}
        """)
        
        # Hubungkan ke handler yang sesuai untuk setiap kartu
        if key == "kc":
            btn_exp.clicked.connect(self._export)
        elif key == "kcp":
            btn_exp.clicked.connect(self._export_kcp)
        elif key == "unit":
            btn_exp.clicked.connect(self._export_unit)
        elif key == "produk":
            btn_exp.clicked.connect(self._export_produk)
        else:
            btn_exp.clicked.connect(self._export)
        
        lay.addWidget(btn_exp)
        
        return card, stat_val_lbl


    def update_clock(self):
        now = QDateTime.currentDateTime()
        self.clock_lbl.setText(now.toString("ddd, dd MMM yyyy • HH:mm WIB"))
        
    def load_data(self, data_dict: dict):
        self._data = data_dict
        if data_dict:
            now = QDateTime.currentDateTime().toString("dd MMM yyyy • HH:mm WIB")
            self.last_gen_lbl.setText(f"Terakhir di-generate: {now}")
            self.b_title.setText("Semua data berhasil diproses!")
            self.b_sub.setText("4 dashboard berhasil dibuat dari file yang di-upload.")
            
            path_done = "assets/gambar_file_dashboard_done.png"
            if os.path.exists(path_done):
                pix = QPixmap(path_done).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                pix.setDevicePixelRatio(2.0)
                self.icon_status.setPixmap(pix)
                self.icon_status.setStyleSheet("background: transparent;")
            else:
                self.icon_status.setText("✔")
                self.icon_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.icon_status.setStyleSheet("font-size: 32px; color: #2563EB; background: transparent;")
                
            path_illus = "assets/illust_dash_done_alpha.png"
            if os.path.exists(path_illus):
                pix = QPixmap(path_illus).scaled(520, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                pix.setDevicePixelRatio(2.0)
                self.illus_lbl.setPixmap(pix)
                self.illus_lbl.setStyleSheet("background: transparent;")
            else:
                self.illus_lbl.setText("[Illustration]")
                self.illus_lbl.setStyleSheet("color: #CBD5E1; border: 1px dashed #E2E8F0; border-radius: 8px; background: transparent;")
                
            self.stat_num.setText("4")
            self.stat_num.setStyleSheet("font-size: 48px; font-weight: 900; color: #2563EB; background: transparent;")
            self.stat_lbl1.setText("Dashboard")
            self.stat_lbl1.setStyleSheet("font-size: 14px; color: #2563EB; font-weight: bold; background: transparent;")
            self.stat_lbl2.setText("Siap Digunakan")
            self.stat_lbl2.setStyleSheet("font-size: 14px; color: #2563EB; font-weight: bold; background: transparent;")
            
            # ── Update card stat labels dari __stats__ ──
            stats = data_dict.get('__stats__', {})
            
            # KC card
            if 'kc' in self._card_stat_labels:
                n_kc = stats.get('jumlah_kc', len([k for k in data_dict if k not in ('Total AH Gunsar', '__stats__')]))
                self._card_stat_labels['kc'].setText(str(n_kc) if n_kc else 'Tidak ada data')
            
            # KCP card
            if 'kcp' in self._card_stat_labels:
                n_kcp = stats.get('jumlah_kcp', 0)
                self._card_stat_labels['kcp'].setText(str(n_kcp) if n_kcp else 'Tidak ada data')
            
            # Unit card
            if 'unit' in self._card_stat_labels:
                n_unit = stats.get('jumlah_unit', 0)
                self._card_stat_labels['unit'].setText(str(n_unit) if n_unit else 'Tidak ada data')
            
            # Monitoring Produk card — tampilkan ringkasan tabungan/giro/deposito/casa/dpk
            if 'produk' in self._card_stat_labels:
                ps = stats.get('produk_simpanan', {})
                if ps and any(v > 0 for v in ps.values()):
                    self._card_stat_labels['produk'].setText('5 Produk')
                else:
                    self._card_stat_labels['produk'].setText('Tidak ada data')

    def show_empty_cleared(self):
        self._data = {}
        self.last_gen_lbl.setText("Terakhir di-generate: Belum ada data")
        self.b_title.setText("Menunggu Proses Generate")
        self.b_sub.setText("Silakan upload file SSA dan lakukan generate data.")
        
        path_wait = "assets/gambar_file_dashboard_wait.png"
        if os.path.exists(path_wait):
            pix = QPixmap(path_wait).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(2.0)
            self.icon_status.setPixmap(pix)
            self.icon_status.setStyleSheet("background: transparent;")
        else:
            self.icon_status.setText("⏳")
            self.icon_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.icon_status.setStyleSheet("font-size: 32px; color: #F59E0B; background: transparent;")
            
        path_illus = "assets/illust_dash_wait_alpha.png"
        if os.path.exists(path_illus):
            pix = QPixmap(path_illus).scaled(520, 260, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.setDevicePixelRatio(2.0)
            self.illus_lbl.setPixmap(pix)
            self.illus_lbl.setStyleSheet("background: transparent;")
        else:
            self.illus_lbl.setText("[Illustration]")
            self.illus_lbl.setStyleSheet("color: #CBD5E1; border: 1px dashed #E2E8F0; border-radius: 8px; background: transparent;")
            
        self.stat_num.setText("0")
        self.stat_num.setStyleSheet("font-size: 48px; font-weight: 900; color: #F97316; background: transparent;")
        self.stat_lbl1.setText("Dashboard")
        self.stat_lbl1.setStyleSheet("font-size: 14px; color: #F97316; font-weight: bold; background: transparent;")
        self.stat_lbl2.setText("Belum Tersedia")
        self.stat_lbl2.setStyleSheet("font-size: 14px; color: #F97316; font-weight: bold; background: transparent;")
        
        # Reset semua card stat labels
        for lbl in self._card_stat_labels.values():
            lbl.setText("Tidak ada data")

    def _export(self):
        from ui.toast_notification import ToastManager
        if not self._data:
            ToastManager.show(self.window(), "Silakan Generate data terlebih dahulu.", "warning")
            return
            
        from core.exporter import get_default_export_filename, get_unique_path
        from PySide6.QtWidgets import QFileDialog
        import os
        from pathlib import Path
        
        base_name = get_default_export_filename(self._data, "KC AH Gunsar")
        downloads = str(Path.home() / "Downloads")
        default_path = get_unique_path(os.path.join(downloads, base_name))
        
        options = QFileDialog.Option.DontConfirmOverwrite
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel Dashboard", default_path,
            "Excel Files (*.xlsx)", options=options)
            
        if not path:
            return

        try:
            from core.exporter import export_to_excel
            export_to_excel(self._data, path)
            from core.history_manager import mark_last_exported
            mark_last_exported()
            ToastManager.show(self.window(),
                              f"File berhasil disimpan: {path}", "success")
        except Exception as e:
            ToastManager.show(self.window(), f"Gagal export: {e}", "error")

    def _export_kcp(self):
        """Export Dashboard KCP — membaca Nama Uker dari SSA, filter KCP."""
        self._export_uker_common('KCP')

    def _export_unit(self):
        """Export Dashboard Unit — membaca Nama Uker dari SSA, filter Unit."""
        self._export_uker_common('Unit')

    def _export_produk(self):
        """Export Monitoring Produk Dashboard."""
        from ui.toast_notification import ToastManager
        from PySide6.QtWidgets import QFileDialog
        import os
        from pathlib import Path

        if not self._data:
            ToastManager.show(self.window(),
                              "Silakan Generate data terlebih dahulu.", "warning")
            return

        from core.exporter import get_default_export_filename, get_unique_path
        
        # Buat nama file berdasarkan nama Dashboard
        base_name = get_default_export_filename(self._data, "KC AH Gunsar")
        base_name = base_name.replace("Dashboard KC", "Monitoring Produk Dashboard")
        downloads = str(Path.home() / "Downloads")
        default_path = get_unique_path(os.path.join(downloads, base_name))

        options = QFileDialog.Option.DontConfirmOverwrite
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel Monitoring Produk", default_path,
            "Excel Files (*.xlsx)", options=options)

        if not path:
            return

        try:
            from core.exporter_produk import export_monitoring_produk_to_excel
            export_monitoring_produk_to_excel(self._data, path)
            from core.history_manager import mark_last_exported
            mark_last_exported()
            ToastManager.show(self.window(),
                              f"Monitoring Produk berhasil disimpan: {path}", "success")
        except Exception as e:
            ToastManager.show(self.window(), f"Gagal export Monitoring Produk: {e}", "error")

    def _export_uker_common(self, uker_type: str):
        """Common handler untuk export KCP/Unit."""
        from ui.toast_notification import ToastManager
        from PySide6.QtWidgets import QFileDialog
        import os
        from pathlib import Path

        if not self._data or '__uker_data__' not in self._data:
            ToastManager.show(self.window(),
                              "Silakan Generate ulang data terlebih dahulu.", "warning")
            return

        data_uker = self._data['__uker_data__']

        # Buat nama file berdasarkan periode terbaru
        from core.exporter_uker import get_filename_uker, export_uker_to_excel
        from core.exporter import get_unique_path
        base_name = get_filename_uker(data_uker, uker_type)
        downloads = str(Path.home() / "Downloads")
        default_path = get_unique_path(os.path.join(downloads, base_name))

        options = QFileDialog.Option.DontConfirmOverwrite
        path, _ = QFileDialog.getSaveFileName(
            self, f"Export Excel Dashboard {uker_type}", default_path,
            "Excel Files (*.xlsx)", options=options)

        if not path:
            return

        try:
            export_uker_to_excel(data_uker, path, uker_type)
            from core.history_manager import mark_last_exported
            mark_last_exported()
            ToastManager.show(self.window(),
                              f"Dashboard {uker_type} berhasil disimpan: {path}", "success")
        except Exception as e:
            ToastManager.show(self.window(), f"Gagal export {uker_type}: {e}", "error")

