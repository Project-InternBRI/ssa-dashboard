"""
beranda_widget.py — Halaman Beranda.
Menampilkan banner utama, stat cards dinamis, akses cepat, panduan,
dan daftar aktivitas terbaru dari riwayat generate.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea, QGraphicsDropShadowEffect)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRect, QPoint
from PySide6.QtGui import QCursor, QColor, QFont, QPainter, QLinearGradient


class HoverCard(QFrame):
    """Custom Frame dengan efek hover (naik dan shadow)."""
    clicked = Signal()

    def __init__(self, parent=None, is_clickable=False):
        super().__init__(parent)
        self.is_clickable = is_clickable
        if self.is_clickable:
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            
        self.setObjectName("hoverCard")
        self.setStyleSheet("""
            QFrame#hoverCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2EAF4;
            }
        """)

        # Default shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.shadow.setOffset(0, 4)
        self.setGraphicsEffect(self.shadow)

        self._anim_pos = QPropertyAnimation(self, b"pos")
        self._anim_pos.setDuration(200)
        self._anim_pos.setEasingCurve(QEasingCurve.Type.OutQuad)

    def enterEvent(self, event):
        # Hover effect: shadow lebih gelap
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 8)
        
        # Animasi naik (posisi diatur via manual layout offset atau geometry, tapi 
        # karena dikelola oleh layout, mengubah pos() bisa bertentangan. 
        # Alternatif: ubah style margin/border)
        if self.is_clickable:
            self.setStyleSheet("""
                QFrame#hoverCard {
                    background-color: #FFFFFF;
                    border-radius: 12px;
                    border: 1px solid #93C5FD;
                }
            """)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.shadow.setColor(QColor(0, 0, 0, 15))
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 4)
        
        self.setStyleSheet("""
            QFrame#hoverCard {
                background-color: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2EAF4;
            }
        """)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if self.is_clickable and event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class BannerWidget(QFrame):
    """Banner dengan gradient."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(200)
        self.setObjectName("heroBanner")
        self.setStyleSheet("""
            QFrame#heroBanner {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #1E40AF, stop:1 #1E3A5F);
                border-radius: 16px;
            }
        """)


class BerandaWidget(QWidget):
    # Signal untuk navigasi halaman
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_labels = {}
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F8FAFC; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: #F8FAFC;")
        self._main_lay = QVBoxLayout(content)
        self._main_lay.setContentsMargins(32, 28, 32, 48)
        self._main_lay.setSpacing(28)

        # 1. HERO BANNER
        self._build_banner()

        # 2. STAT CARDS
        self._build_stats()

        # 3. AKSES CEPAT
        self._build_akses_cepat()

        # 4. PANDUAN PENGGUNAAN
        self._build_panduan()

        # 5. AKTIVITAS TERBARU
        self._build_aktivitas()

        self._main_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _build_banner(self):
        hero = BannerWidget()
        hero_lay = QVBoxLayout(hero)
        hero_lay.setContentsMargins(40, 36, 40, 36)
        hero_lay.setSpacing(10)

        lbl_title = QLabel("Selamat Datang di SSA Dashboard")
        lbl_title.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold; background: transparent;")

        lbl_sub = QLabel("Kelola data SSA AH Gunsar Jakarta Region dengan mudah")
        lbl_sub.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 15px; background: transparent;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_upload = QPushButton("Mulai Upload")
        btn_upload.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_upload.setFixedHeight(44)
        btn_upload.clicked.connect(lambda: self.navigate_to.emit(2))
        btn_upload.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF; color: #2563EB;
                border: none; border-radius: 8px; font-weight: bold; font-size: 14px; padding: 0 24px;
            }
            QPushButton:hover { background-color: #EFF6FF; }
        """)

        btn_hist = QPushButton("Lihat Hasil Terakhir")
        btn_hist.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hist.setFixedHeight(44)
        btn_hist.clicked.connect(lambda: self.navigate_to.emit(3))
        btn_hist.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #FFFFFF;
                border: 2px solid rgba(255,255,255,0.6); border-radius: 8px; font-weight: bold; font-size: 14px; padding: 0 24px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.15); border-color: #FFFFFF; }
        """)

        btn_row.addWidget(btn_upload)
        btn_row.addWidget(btn_hist)
        btn_row.addStretch()

        hero_lay.addWidget(lbl_title)
        hero_lay.addWidget(lbl_sub)
        hero_lay.addSpacing(16)
        hero_lay.addLayout(btn_row)

        self._main_lay.addWidget(hero)

    def _build_stats(self):
        stats_row = QHBoxLayout()
        stats_row.setSpacing(20)

        configs = [
            ("file_aktif", "📁", "#EFF6FF", "#2563EB", "FILE AKTIF", "—", "SSA Simpanan, Pinjaman, RKA"),
            ("gen_terakhir", "⏱️", "#F3E8FF", "#9333EA", "GENERATE TERAKHIR", "—", "belum ada generate"),
            ("pencapaian_dpk", "📈", "#ECFDF5", "#059669", "PENCAPAIAN DPK", "—", "vs target RKA"),
            ("kc_bawah_target", "⚠️", "#FFFBEB", "#D97706", "KC DI BAWAH TARGET", "—", "dari total 0 KC")
        ]

        for key, icon, bg_color, fg_color, title, val, sub in configs:
            card = HoverCard(is_clickable=False)
            lay = QVBoxLayout(card)
            lay.setContentsMargins(20, 20, 20, 20)
            lay.setSpacing(8)

            # Icon & Title row
            top_row = QHBoxLayout()
            ic_lbl = QLabel(icon)
            ic_lbl.setFixedSize(32, 32)
            ic_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ic_lbl.setStyleSheet(f"background: {bg_color}; color: {fg_color}; border-radius: 8px; font-size: 16px;")
            
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold; letter-spacing: 0.5px;")
            top_row.addWidget(ic_lbl)
            top_row.addSpacing(10)
            top_row.addWidget(t_lbl)
            top_row.addStretch()

            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {fg_color}; font-size: 32px; font-weight: bold;")
            
            s_lbl = QLabel(sub)
            s_lbl.setStyleSheet("color: #94A3B8; font-size: 12px;")

            lay.addLayout(top_row)
            lay.addSpacing(4)
            lay.addWidget(v_lbl)
            lay.addWidget(s_lbl)
            
            self._stats_labels[key] = {"val": v_lbl, "sub": s_lbl}
            stats_row.addWidget(card)

        self._main_lay.addLayout(stats_row)

    def _build_akses_cepat(self):
        lbl = QLabel("Akses Cepat")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F2A4A;")
        self._main_lay.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(20)

        # Card 1: Upload
        card_up = HoverCard(is_clickable=True)
        card_up.clicked.connect(lambda: self.navigate_to.emit(2))
        card_up.setMinimumHeight(130)
        lay_up = QVBoxLayout(card_up)
        lay_up.setContentsMargins(24, 20, 24, 20)
        
        top_up = QHBoxLayout()
        ic_up = QLabel("↑")
        ic_up.setFixedSize(40, 40)
        ic_up.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic_up.setStyleSheet("background: #DBEAFE; color: #2563EB; border-radius: 20px; font-size: 20px; font-weight: bold;")
        bdg_up = QLabel("Langkah 1")
        bdg_up.setStyleSheet("background: #F1F5F9; color: #64748B; font-size: 11px; padding: 4px 8px; border-radius: 10px; font-weight: bold;")
        top_up.addWidget(ic_up)
        top_up.addStretch()
        top_up.addWidget(bdg_up, alignment=Qt.AlignmentFlag.AlignTop)
        
        lay_up.addLayout(top_up)
        tit_up = QLabel("Upload & Generate")
        tit_up.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        desc_up = QLabel("Unggah file CSV/XLSX lalu proses.")
        desc_up.setStyleSheet("font-size: 13px; color: #64748B;")
        lay_up.addSpacing(10)
        lay_up.addWidget(tit_up)
        lay_up.addWidget(desc_up)

        # Card 2: Preview
        card_pr = HoverCard(is_clickable=True)
        card_pr.clicked.connect(lambda: self.navigate_to.emit(3))
        card_pr.setMinimumHeight(130)
        lay_pr = QVBoxLayout(card_pr)
        lay_pr.setContentsMargins(24, 20, 24, 20)
        
        top_pr = QHBoxLayout()
        ic_pr = QLabel("⊞")
        ic_pr.setFixedSize(40, 40)
        ic_pr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic_pr.setStyleSheet("background: #DCFCE7; color: #16A34A; border-radius: 20px; font-size: 20px; font-weight: bold;")
        bdg_pr = QLabel("Langkah 2")
        bdg_pr.setStyleSheet("background: #F1F5F9; color: #64748B; font-size: 11px; padding: 4px 8px; border-radius: 10px; font-weight: bold;")
        top_pr.addWidget(ic_pr)
        top_pr.addStretch()
        top_pr.addWidget(bdg_pr, alignment=Qt.AlignmentFlag.AlignTop)
        
        lay_pr.addLayout(top_pr)
        tit_pr = QLabel("Preview Tabel")
        tit_pr.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B;")
        desc_pr = QLabel("Lihat data hasil konsolidasi per sheet.")
        desc_pr.setStyleSheet("font-size: 13px; color: #64748B;")
        lay_pr.addSpacing(10)
        lay_pr.addWidget(tit_pr)
        lay_pr.addWidget(desc_pr)

        row.addWidget(card_up)
        row.addWidget(card_pr)
        self._main_lay.addLayout(row)

    def _build_panduan(self):
        lbl = QLabel("Panduan Penggunaan")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F2A4A;")
        self._main_lay.addWidget(lbl)

        row = QHBoxLayout()
        row.setSpacing(10)

        steps = [
            ("1", "Upload File SSA", "Unggah file SSA Simpanan dan Pinjaman dalam format CSV atau Excel", "#3B82F6"),
            ("2", "Generate Dashboard", "Klik Generate untuk memproses data secara otomatis", "#10B981"),
            ("3", "Export Excel", "Download hasil dalam format Excel siap pakai", "#F59E0B")
        ]

        for i, (num, title, desc, color) in enumerate(steps):
            c = QFrame()
            c.setStyleSheet("background: transparent;")
            lay = QHBoxLayout(c)
            lay.setContentsMargins(0, 0, 0, 0)
            
            # Badge num
            b = QLabel(num)
            b.setFixedSize(32, 32)
            b.setAlignment(Qt.AlignmentFlag.AlignCenter)
            b.setStyleSheet(f"background: {color}; color: white; border-radius: 16px; font-weight: bold; font-size: 14px;")
            
            # Text
            vl = QVBoxLayout()
            vl.setSpacing(2)
            t = QLabel(title)
            t.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("font-size: 12px; color: #64748B;")
            vl.addWidget(t)
            vl.addWidget(d)
            
            lay.addWidget(b, alignment=Qt.AlignmentFlag.AlignTop)
            lay.addSpacing(12)
            lay.addLayout(vl)
            
            row.addWidget(c)
            
            if i < len(steps) - 1:
                arr = QLabel("→")
                arr.setStyleSheet("color: #CBD5E1; font-size: 20px; font-weight: bold;")
                arr.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row.addWidget(arr)

        self._main_lay.addLayout(row)

    def _build_aktivitas(self):
        lbl = QLabel("Aktivitas Terbaru")
        lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F2A4A;")
        self._main_lay.addWidget(lbl)

        self._act_frame = QFrame()
        self._act_frame.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 12px;
                border: 1px solid #E2EAF4;
            }
        """)
        self._act_lay = QVBoxLayout(self._act_frame)
        self._act_lay.setContentsMargins(0, 8, 0, 8)
        self._act_lay.setSpacing(0)
        self._main_lay.addWidget(self._act_frame)

    def refresh_stats(self, file_count: int = 0, history_list: list = None):
        """Update stat cards berdasarkan data nyata."""
        self._stats_labels["file_aktif"]["val"].setText(str(file_count))
        
        if history_list and len(history_list) > 0:
            latest = history_list[0]
            tgl = latest.get("tanggal_proses", "—")
            if len(tgl) >= 10:
                tgl = tgl[:10]
            self._stats_labels["gen_terakhir"]["val"].setText(tgl)
            self._stats_labels["gen_terakhir"]["sub"].setText(f"{latest.get('jumlah_kc', 0)} KC diproses")
            
            # Simulasi data jika DPK / KC belum dihitung secara global
            self._stats_labels["pencapaian_dpk"]["val"].setText("—")
            self._stats_labels["kc_bawah_target"]["val"].setText("—")
        else:
            self._stats_labels["gen_terakhir"]["val"].setText("—")
            self._stats_labels["gen_terakhir"]["sub"].setText("belum ada generate")
            self._stats_labels["pencapaian_dpk"]["val"].setText("—")
            self._stats_labels["kc_bawah_target"]["val"].setText("—")

    def refresh_activity(self, history_list: list):
        """Update list aktivitas dari riwayat."""
        while self._act_lay.count():
            item = self._act_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history_list:
            # Empty state
            empty = QWidget()
            empty.setStyleSheet("background: transparent;")
            el = QVBoxLayout(empty)
            el.setContentsMargins(0, 30, 0, 30)
            el.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            ic = QLabel("📅")
            ic.setStyleSheet("font-size: 32px;")
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            tx = QLabel("Belum ada aktivitas. Mulai dengan upload file SSA.")
            tx.setStyleSheet("color: #94A3B8; font-size: 13px;")
            tx.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            btn = QPushButton("Mulai Upload Sekarang")
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("""
                QPushButton { background: #EFF6FF; color: #2563EB; font-weight: bold; border-radius: 6px; padding: 8px 16px; border: none; }
                QPushButton:hover { background: #DBEAFE; }
            """)
            btn.clicked.connect(lambda: self.navigate_to.emit(2))
            
            el.addWidget(ic)
            el.addWidget(tx)
            el.addSpacing(10)
            el.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self._act_lay.addWidget(empty)
            return

        # Render list
        for i, entry in enumerate(history_list[:5]):
            row = QWidget()
            row.setStyleSheet("background: transparent;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(20, 12, 20, 12)
            
            ok = entry.get("status", "sukses") != "gagal"
            ic_char = "✓" if ok else "✕"
            bg = "#ECFDF5" if ok else "#FEF2F2"
            fg = "#059669" if ok else "#DC2626"
            
            ic = QLabel(ic_char)
            ic.setFixedSize(32, 32)
            ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ic.setStyleSheet(f"background: {bg}; color: {fg}; font-weight: bold; border-radius: 16px; font-size: 14px;")
            
            vl = QVBoxLayout()
            vl.setSpacing(2)
            title = "Generate sukses" if ok else "Generate gagal"
            t = QLabel(title)
            t.setStyleSheet("font-weight: bold; font-size: 13px; color: #1E293B;")
            d = QLabel(entry.get("nama_file_simpanan", ""))
            d.setStyleSheet("color: #64748B; font-size: 12px;")
            vl.addWidget(t)
            vl.addWidget(d)
            
            ts = QLabel(entry.get("tanggal_proses", ""))
            ts.setStyleSheet("color: #94A3B8; font-size: 11px;")
            
            rl.addWidget(ic)
            rl.addSpacing(12)
            rl.addLayout(vl)
            rl.addStretch()
            rl.addWidget(ts)
            
            self._act_lay.addWidget(row)
            
            if i < min(len(history_list), 5) - 1:
                line = QFrame()
                line.setFixedHeight(1)
                line.setStyleSheet("background: #F1F5F9;")
                self._act_lay.addWidget(line)
