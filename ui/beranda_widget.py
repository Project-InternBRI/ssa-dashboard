"""
beranda_widget.py — Halaman Beranda.
Banner hero, stat cards dinamis dengan ikon modern, akses cepat interaktif,
panduan penggunaan 3-step, dan aktivitas terbaru dari riwayat.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QFrame, QScrollArea,
                               QGraphicsDropShadowEffect, QProgressBar, QGridLayout)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, QRectF, QSize
from PySide6.QtGui import QCursor, QColor, QPainter, QPixmap, QPainterPath, QIcon
import os

# ────────────────────────────────────────────────────────────────────
# CUSTOM WIDGETS
# ────────────────────────────────────────────────────────────────────

class HeroBanner(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        img_full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "images", "hero_bg_fullscreen.png"))
        img_norm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "images", "hero_bg_normal.png"))
        self.pix_full = QPixmap(img_full_path)
        self.pix_norm = QPixmap(img_norm_path)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 16, 16)
        painter.fillPath(path, QColor("#031569"))
        painter.setClipPath(path)
        
        pix = self.pix_full if self.width() > 1400 else self.pix_norm
        if not pix.isNull():
            painter.drawPixmap(self.rect(), pix)

class ClickableCard(QFrame):
    clicked = Signal()
    def __init__(self, bg_normal="#FFFFFF", bg_hover="#F8FAFC", bg_image=None, parent=None):
        super().__init__(parent)
        self._bg_normal = bg_normal
        self._bg_hover = bg_hover
        self._current_bg = self._bg_normal
        self._bg_pixmap = QPixmap(bg_image) if bg_image else None
        
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), 12, 12)
        
        painter.fillPath(path, QColor(self._current_bg))
        painter.setClipPath(path)
        
        if self._bg_pixmap and not self._bg_pixmap.isNull():
            painter.drawPixmap(self.rect(), self._bg_pixmap)

    def enterEvent(self, e):
        self._current_bg = self._bg_hover
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._current_bg = self._bg_normal
        self.update()
        super().leaveEvent(e)
        
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

# ────────────────────────────────────────────────────────────────────
# BERANDA WIDGET
# ────────────────────────────────────────────────────────────────────
class BerandaWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._stats_refs = {}
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F8FAFC; border: none; }")

        content = QWidget()
        content.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(content)
        lay.setContentsMargins(32, 28, 32, 48)
        lay.setSpacing(32)

        lay.addWidget(self._build_banner())
        lay.addLayout(self._build_stats())
        lay.addLayout(self._build_akses_cepat())
        lay.addLayout(self._build_panduan())
        lay.addLayout(self._build_bottom_section())
        lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ── BANNER HERO ──
    def _build_banner(self) -> QFrame:
        hero = HeroBanner()
        hero.setObjectName("hero_banner")
        hero.setFixedHeight(280)
        hero.setStyleSheet("QFrame#hero_banner { background-color: transparent; }")
        
        lay = QVBoxLayout(hero)
        lay.setContentsMargins(40, 36, 40, 36)
        lay.setSpacing(10)

        t = QLabel("Selamat Datang di BRIVIEW")
        t.setStyleSheet("color: #FFFFFF; font-size: 28px; font-weight: bold; background: transparent;")
        s = QLabel("BRI Performance Review & Evaluation")
        s.setStyleSheet("color: rgba(255,255,255,0.80); font-size: 15px; background: transparent;")

        btn_row = QHBoxLayout()
        btn_row.setSpacing(16)

        btn_up = QPushButton(" Mulai Upload")
        icon_up_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "logo_upload_biru.svg"))
        btn_up.setIcon(QIcon(icon_up_path))
        btn_up.setIconSize(QSize(20, 20))
        btn_up.setFixedHeight(44)
        btn_up.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_up.clicked.connect(lambda: self.navigate_to.emit(2))
        btn_up.setStyleSheet("""
            QPushButton { background: #FFFFFF; color: #2563EB; border: none; border-radius: 8px; font-weight: bold; font-size: 14px; padding: 0 24px; text-align: center; }
            QPushButton:hover { background: #EFF6FF; }
        """)

        btn_pr = QPushButton(" Lihat Hasil Terakhir")
        icon_pr_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "bar_chart_putih.svg"))
        btn_pr.setIcon(QIcon(icon_pr_path))
        btn_pr.setIconSize(QSize(20, 20))
        btn_pr.setFixedHeight(44)
        btn_pr.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_pr.clicked.connect(lambda: self.navigate_to.emit(3))
        btn_pr.setStyleSheet("""
            QPushButton { background: rgba(0, 0, 50, 0.4); color: #FFFFFF; border: 1px solid rgba(255,255,255,0.3); border-radius: 8px; font-weight: bold; font-size: 14px; padding: 0 24px; text-align: center; }
            QPushButton:hover { background: rgba(0, 0, 50, 0.6); }
        """)

        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_pr)
        btn_row.addStretch()

        lay.addWidget(t)
        lay.addWidget(s)
        lay.addSpacing(16)
        lay.addLayout(btn_row)
        return hero

    # ── STAT CARDS ──
    def _create_shadow_card(self):
        c = QFrame()
        c.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; }")
        c.setFixedHeight(240)
        s = QGraphicsDropShadowEffect(c)
        s.setBlurRadius(12)
        s.setColor(QColor(0,0,0,8))
        s.setOffset(0, 4)
        c.setGraphicsEffect(s)
        return c

    def _icon_label(self, icon_filename, bg, fg):
        lbl = QLabel()
        lbl.setFixedSize(32, 32)
        lbl.setStyleSheet(f"background: {bg}; border-radius: 8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_filename:
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", icon_filename))
            pixmap = QIcon(icon_path).pixmap(QSize(20, 20))
            if fg:
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(fg))
                painter.end()
            lbl.setPixmap(pixmap)
        return lbl

    def _build_stats(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(20)

        # 1. STATUS FILE
        c1 = self._create_shadow_card()
        l1 = QVBoxLayout(c1)
        l1.setContentsMargins(20, 20, 20, 20)
        l1.setSpacing(8)
        
        h1 = QHBoxLayout()
        h1.addWidget(self._icon_label("file_homepage.svg", "#EFF6FF", "#2563EB"))
        h1.addSpacing(10)
        t1 = QLabel("STATUS FILE")
        t1.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h1.addWidget(t1)
        h1.addStretch()
        l1.addLayout(h1)

        v1 = QLabel("0/3")
        v1.setStyleSheet("color: #2563EB; font-size: 32px; font-weight: bold;")
        s1 = QLabel("File Siap")
        s1.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 4px;")
        l1.addWidget(v1)
        l1.addWidget(s1)

        p1 = QProgressBar()
        p1.setFixedHeight(6)
        p1.setTextVisible(False)
        p1.setStyleSheet("QProgressBar { background: #E2E8F0; border-radius: 3px; border: none; } QProgressBar::chunk { background: #16A34A; border-radius: 3px; }")
        l1.addWidget(p1)

        def make_chk(txt):
            lay = QHBoxLayout()
            lbl = QLabel(txt)
            lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: 600;")
            chk = QLabel("X")
            chk.setStyleSheet("color: #94A3B8; font-size: 11px; font-weight: bold;")
            lay.addWidget(lbl)
            lay.addStretch()
            lay.addWidget(chk)
            return lay, chk

        lay_s, chk_s = make_chk("SSA Simpanan")
        lay_p, chk_p = make_chk("SSA Pinjaman")
        lay_r, chk_r = make_chk("RKA")
        l1.addLayout(lay_s)
        l1.addLayout(lay_p)
        l1.addLayout(lay_r)

        l1.addStretch()
        b1 = QHBoxLayout()
        d1 = QLabel("●")
        d1.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds1 = QLabel("Belum ada file")
        ds1.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b1.addWidget(d1)
        b1.addWidget(ds1)
        b1.addStretch()
        l1.addLayout(b1)

        self._stats_refs["upload"] = {"val": v1, "prog": p1, "cs": chk_s, "cp": chk_p, "cr": chk_r, "dot": d1, "ds": ds1}
        row.addWidget(c1)

        # 2. KC TERDETEKSI
        c2 = self._create_shadow_card()
        l2 = QVBoxLayout(c2)
        l2.setContentsMargins(20, 20, 20, 20)
        l2.setSpacing(8)
        
        h2 = QHBoxLayout()
        h2.addWidget(self._icon_label("kc_homepage.svg", "#FEF3C7", "#D97706"))
        h2.addSpacing(10)
        t2 = QLabel("KC TERDETEKSI")
        t2.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h2.addWidget(t2)
        h2.addStretch()
        l2.addLayout(h2)

        v2 = QLabel("0")
        v2.setStyleSheet("color: #D97706; font-size: 32px; font-weight: bold;")
        s2 = QLabel("KC Aktif")
        s2.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l2.addWidget(v2)
        l2.addWidget(s2)

        l2.addStretch()

        p_txt = QLabel("Siap Diproses")
        p_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l2.addWidget(p_txt)
        b2 = QHBoxLayout()
        d2 = QLabel("●")
        d2.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds2 = QLabel("Data KC terdeteksi")
        ds2.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b2.addWidget(d2)
        b2.addWidget(ds2)
        b2.addStretch()
        l2.addLayout(b2)

        self._stats_refs["kc"] = {"val": v2, "dot": d2, "ds": ds2}
        row.addWidget(c2)

        # 3. PERIODE SSA
        c3 = self._create_shadow_card()
        l3 = QVBoxLayout(c3)
        l3.setContentsMargins(20, 20, 20, 20)
        l3.setSpacing(8)
        
        h3 = QHBoxLayout()
        h3.addWidget(self._icon_label("calendar_homepage.svg", "#DCFCE7", "#16A34A"))
        h3.addSpacing(10)
        t3 = QLabel("PERIODE SSA")
        t3.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h3.addWidget(t3)
        h3.addStretch()
        l3.addLayout(h3)

        v3 = QLabel("—")
        v3.setStyleSheet("color: #16A34A; font-size: 32px; font-weight: bold;")
        s3 = QLabel("Periode Terakhir")
        s3.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l3.addWidget(v3)
        l3.addWidget(s3)

        l3.addStretch()

        cal_txt = QLabel("Periode Aktif")
        cal_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l3.addWidget(cal_txt)
        b3 = QHBoxLayout()
        d3 = QLabel("●")
        d3.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds3 = QLabel("Belum tersedia")
        ds3.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b3.addWidget(d3)
        b3.addWidget(ds3)
        b3.addStretch()
        l3.addLayout(b3)

        self._stats_refs["periode"] = {"val": v3, "dot": d3, "ds": ds3}
        row.addWidget(c3)

        # 4. STATUS DASHBOARD
        c4 = self._create_shadow_card()
        l4 = QVBoxLayout(c4)
        l4.setContentsMargins(20, 20, 20, 20)
        l4.setSpacing(8)
        
        h4 = QHBoxLayout()
        h4.addWidget(self._icon_label("status_homepage.svg", "#F3E8FF", "#9333EA"))
        h4.addSpacing(10)
        t4 = QLabel("STATUS DASHBOARD")
        t4.setStyleSheet("color: #475569; font-size: 11px; font-weight: 800; letter-spacing: 0.5px;")
        h4.addWidget(t4)
        h4.addStretch()
        l4.addLayout(h4)

        v4 = QLabel("WAIT")
        v4.setStyleSheet("color: #9333EA; font-size: 32px; font-weight: bold;")
        s4 = QLabel("Dashboard Siap")
        s4.setStyleSheet("color: #1E293B; font-size: 13px; font-weight: bold; margin-bottom: 20px;")
        l4.addWidget(v4)
        l4.addWidget(s4)

        l4.addStretch()

        clk_txt = QLabel("Terakhir Update, —")
        clk_txt.setStyleSheet("color: #1E293B; font-size: 12px; font-weight: bold;")
        l4.addWidget(clk_txt)
        b4 = QHBoxLayout()
        d4 = QLabel("●")
        d4.setStyleSheet("color: #94A3B8; font-size: 12px;")
        ds4 = QLabel("Belum di-generate")
        ds4.setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold;")
        b4.addWidget(d4)
        b4.addWidget(ds4)
        b4.addStretch()
        l4.addLayout(b4)

        self._stats_refs["dash"] = {"val": v4, "time": clk_txt, "dot": d4, "ds": ds4}
        row.addWidget(c4)
        return row

    # ── AKSES CEPAT ──
    def _build_akses_cepat(self) -> QVBoxLayout:
        vl = QVBoxLayout()
        vl.setSpacing(14)
        sec = QLabel("Akses Cepat")
        sec.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F2A4A;")
        vl.addWidget(sec)

        row = QHBoxLayout()
        row.setSpacing(20)

        def make_ac_card(idx, title, desc, bg, btn_bg, btn_fg, btn_text, img_name, circle_icon_name):
            img_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "images", img_name))
            card = ClickableCard(bg_normal=bg, bg_hover=bg, bg_image=img_path)
            card.clicked.connect(lambda: self.navigate_to.emit(idx))
            card.setMinimumHeight(160)
            cl = QHBoxLayout(card)
            cl.setContentsMargins(32, 28, 32, 28)
            
            left = QVBoxLayout()
            left.setSpacing(12)
            
            title_row = QHBoxLayout()
            title_row.setSpacing(16)
            
            circle_icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", circle_icon_name))
            circle = QLabel()
            circle.setFixedSize(48, 48)
            circle.setStyleSheet(f"background-color: {btn_bg}; border-radius: 24px;")
            circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            circle.setPixmap(QIcon(circle_icon_path).pixmap(QSize(24, 24)))
            
            t = QLabel(title)
            t.setStyleSheet("font-size: 18px; font-weight: bold; color: #0F2A4A; background: transparent;")
            
            title_row.addWidget(circle, 0, Qt.AlignmentFlag.AlignVCenter)
            title_row.addWidget(t, 0, Qt.AlignmentFlag.AlignVCenter)
            title_row.addStretch()
            
            d = QLabel(desc)
            d.setStyleSheet("font-size: 13px; color: #475569; background: transparent; padding-left: 2px;")
            d.setWordWrap(True)
            
            left.addLayout(title_row)
            left.addWidget(d)
            left.addStretch()
            
            btn = QPushButton(btn_text)
            btn.setFixedSize(160, 36)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            
            arrow_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "arrow_putih.svg"))
            btn.setIcon(QIcon(arrow_path))
            btn.setIconSize(QSize(16, 16))
            btn.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            
            btn.setStyleSheet(f"""
                QPushButton {{ background: {btn_bg}; color: {btn_fg}; font-weight: bold; font-size: 13px; border-radius: 18px; border: none; text-align: center; }}
                QPushButton:hover {{ opacity: 0.8; }}
            """)
            btn.clicked.connect(lambda: self.navigate_to.emit(idx))
            left.addWidget(btn)
            
            cl.addLayout(left, 3)
            cl.addStretch(2)
            return card

        # Blue card
        c1 = make_ac_card(2, "Upload & Generate", "Unggah file SSA dan proses\\nkonsolidasi data secara otomatis.", "#F0F5FF", "#2563EB", "#FFFFFF", "Mulai Sekarang", "akses_cepat_bg.png", "logo_upload_putih.svg")
        # Green card
        c2 = make_ac_card(3, "Preview Tabel", "Lihat hasil konsolidasi\\nper KC dalam bentuk tabel interaktif.", "#F0FDF4", "#16A34A", "#FFFFFF", "Lihat Sekarang", "preview_tabel_bg.png", "bar_chart_putih.svg")

        row.addWidget(c1)
        row.addWidget(c2)
        vl.addLayout(row)
        return vl

    # ── PANDUAN PENGGUNAAN ──
    def _build_panduan(self) -> QVBoxLayout:
        vl = QVBoxLayout()
        vl.setSpacing(14)
        sec = QLabel("Panduan Penggunaan")
        sec.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F2A4A;")
        vl.addWidget(sec)

        row = QHBoxLayout()
        row.setSpacing(12)

        steps = [
            ("1", "#2563EB", "#EFF6FF", "Upload File SSA", "Unggah file SSA Simpanan dan Pinjaman dalam format CSV atau Excel", "upload.svg", "#2563EB"),
            ("2", "#16A34A", "#F0FDF4", "Generate Dashboard", "Klik Generate untuk memproses data secara otomatis.", "settings.svg", "#16A34A"),
            ("3", "#D97706", "#FFF7ED", "Export Excel", "Download hasil dalam format Excel siap pakai.", "unduh_homepage.svg", "#000000")
        ]

        for i, (num, clr, bg_clr, title, desc, icon_name, icon_clr) in enumerate(steps):
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: #FFFFFF; border-radius: 12px;
                    border: 1px solid #E2E8F0;
                    border-left: 3px solid {clr};
                }}
            """)
            
            cl = QHBoxLayout(card)
            cl.setContentsMargins(12, 16, 16, 16)
            cl.setSpacing(12)

            # Badge container to align it top
            badge_lay = QVBoxLayout()
            badge = QLabel(num)
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"background: {clr}; color: white; border-radius: 12px; font-weight: bold; font-size: 12px; border: none;")
            badge_lay.addWidget(badge)
            badge_lay.addStretch()

            # Icon
            icon_lbl = self._icon_label(icon_name, bg_clr, icon_clr)
            # Make the icon slightly larger if possible, but _icon_label is fixed to 36x36 which is good.
            
            txt_lay = QVBoxLayout()
            txt_lay.setSpacing(4)
            t = QLabel(title)
            t.setStyleSheet("font-size: 13px; font-weight: bold; color: #0F2A4A; border: none;")
            d = QLabel(desc)
            d.setWordWrap(True)
            d.setStyleSheet("font-size: 11px; color: #64748B; border: none;")
            txt_lay.addWidget(t)
            txt_lay.addWidget(d)
            txt_lay.addStretch()

            cl.addLayout(badge_lay)
            cl.addWidget(icon_lbl, alignment=Qt.AlignmentFlag.AlignTop)
            cl.addLayout(txt_lay)
            
            # Adjust icon layout to center it vertically relative to text if desired, but AlignTop matches screenshot better
            row.addWidget(card)

            if i < len(steps) - 1:
                arr = QLabel("⇢")
                arr.setStyleSheet("color: #3B82F6; font-size: 18px; font-weight: bold;")
                arr.setAlignment(Qt.AlignmentFlag.AlignCenter)
                row.addWidget(arr)

        vl.addLayout(row)
        return vl

    # ── BOTTOM SECTION ──
    def _build_bottom_section(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(32)

        # LEFT: Aktivitas Terbaru
        left = QVBoxLayout()
        left.setSpacing(14)
        l_sec = QHBoxLayout()
        lt = QLabel("Aktivitas Terbaru")
        lt.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F2A4A;")
        ls = QPushButton("Lihat Semua")
        ls.setCursor(Qt.CursorShape.PointingHandCursor)
        ls.setStyleSheet("color: #2563EB; font-size: 12px; font-weight: bold; background: #EFF6FF; padding: 6px 14px; border-radius: 6px; border: none;")
        ls.clicked.connect(self._show_history_popup)
        l_sec.addWidget(lt)
        l_sec.addStretch()
        l_sec.addWidget(ls)
        left.addLayout(l_sec)

        self._act_frame = QFrame()
        self._act_frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        self._act_lay = QVBoxLayout(self._act_frame)
        self._act_lay.setContentsMargins(0, 0, 0, 0)
        self._act_lay.setSpacing(0)
        
        # Header table
        h_row = QWidget()
        h_row.setStyleSheet("background: #F8FAFC; border-bottom: 1px solid #E2E8F0; border-top-left-radius: 12px; border-top-right-radius: 12px;")
        h_lay = QHBoxLayout(h_row)
        h_lay.setContentsMargins(20, 12, 20, 12)
        h1 = QLabel("AKTIVITAS"); h1.setFixedWidth(180); h1.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none;")
        h2 = QLabel("DETAIL"); h2.setFixedWidth(220); h2.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none;")
        h3 = QLabel("WAKTU"); h3.setFixedWidth(140); h3.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none;")
        h4 = QLabel("STATUS"); h4.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none;")
        h_lay.addWidget(h1); h_lay.addWidget(h2); h_lay.addWidget(h3); h_lay.addWidget(h4); h_lay.addStretch()
        self._act_lay.addWidget(h_row)
        
        self._act_list_lay = QVBoxLayout()
        self._act_list_lay.setContentsMargins(0, 0, 0, 0)
        self._act_list_lay.setSpacing(0)
        self._act_lay.addLayout(self._act_list_lay)
        self._act_lay.addStretch()
        left.addWidget(self._act_frame)

        # RIGHT: Ringkasan Kinerja
        right = QVBoxLayout()
        right.setSpacing(14)
        r_sec = QHBoxLayout()
        rt = QLabel("Ringkasan Kinerja")
        rt.setStyleSheet("font-size: 16px; font-weight: 800; color: #0F2A4A;")
        rs = QLabel("Hari ini v")
        rs.setStyleSheet("color: #64748B; font-size: 12px; background: #F1F5F9; padding: 4px 8px; border-radius: 6px;")
        r_sec.addWidget(rt)
        r_sec.addStretch()
        r_sec.addWidget(rs)
        right.addLayout(r_sec)

        r_card = QFrame()
        r_card.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
        rc_lay = QVBoxLayout(r_card)
        rc_lay.setContentsMargins(20, 20, 20, 20)
        rc_lay.setSpacing(24)

        def make_rk(ic, bg, fg, title, val, stat, stat_clr):
            ly = QHBoxLayout()
            il = QLabel(ic)
            il.setFixedSize(36, 36)
            il.setAlignment(Qt.AlignmentFlag.AlignCenter)
            il.setStyleSheet(f"background: {bg}; color: {fg}; font-size: 16px; border-radius: 18px; border: none;")
            vl = QVBoxLayout()
            vl.setSpacing(2)
            t = QLabel(title)
            t.setStyleSheet("color: #0F2A4A; font-size: 11px; font-weight: bold; border: none;")
            v = QLabel(val)
            v.setStyleSheet("color: #0F2A4A; font-size: 18px; font-weight: bold; border: none;")
            vl.addWidget(t); vl.addWidget(v)
            s = QLabel(stat)
            s.setStyleSheet(f"color: {stat_clr}; font-size: 11px; font-weight: bold; border: none;")
            ly.addWidget(il); ly.addSpacing(12); ly.addLayout(vl); ly.addStretch(); ly.addWidget(s)
            return ly, v, s
            
        self._rk_1_lay, self._rk_1_v, self._rk_1_s = make_rk("📄", "#EFF6FF", "#2563EB", "File Diproses", "0", "0% Selesai", "#2563EB")
        self._rk_2_lay, self._rk_2_v, self._rk_2_s = make_rk("🏢", "#FEF3C7", "#D97706", "KC Aktif", "0", "Menunggu", "#D97706")
        self._rk_3_lay, self._rk_3_v, self._rk_3_s = make_rk("✓", "#ECFDF5", "#16A34A", "Data Valid", "0%", "Tidak Ada Error", "#16A34A")
        self._rk_4_lay, self._rk_4_v, self._rk_4_s = make_rk("🕒", "#F3E8FF", "#9333EA", "Dashboard Terbaru", "—", "—", "#9333EA")

        rc_lay.addLayout(self._rk_1_lay)
        
        lin1 = QFrame(); lin1.setFixedHeight(1); lin1.setStyleSheet("background: #F1F5F9; border: none;")
        rc_lay.addWidget(lin1)
        
        rc_lay.addLayout(self._rk_2_lay)
        
        lin2 = QFrame(); lin2.setFixedHeight(1); lin2.setStyleSheet("background: #F1F5F9; border: none;")
        rc_lay.addWidget(lin2)
        
        rc_lay.addLayout(self._rk_3_lay)
        
        lin3 = QFrame(); lin3.setFixedHeight(1); lin3.setStyleSheet("background: #F1F5F9; border: none;")
        rc_lay.addWidget(lin3)
        
        rc_lay.addLayout(self._rk_4_lay)
        rc_lay.addStretch()

        right.addWidget(r_card)

        row.addLayout(left, 6)
        row.addLayout(right, 4)
        return row

    # ── REFRESH METODE ──
    def refresh_stats(self, s_ready: bool, p_ready: bool, rka_ready: bool, dash_ready: bool, history_list: list | None = None):
        ready_count = sum([s_ready, p_ready, rka_ready])
        
        # 1. Status File
        if "upload" in self._stats_refs:
            r = self._stats_refs["upload"]
            r["val"].setText(f"{ready_count}/3")
            r["prog"].setValue(int((ready_count/3)*100))
            def set_chk(lbl, ready):
                lbl.setText("✓" if ready else "X")
                lbl.setStyleSheet("color: #16A34A; font-size: 12px; font-weight: bold; border: none;" if ready else "color: #94A3B8; font-size: 11px; font-weight: bold; border: none;")
            set_chk(r["cs"], s_ready)
            set_chk(r["cp"], p_ready)
            set_chk(r["cr"], rka_ready)
            if ready_count == 3:
                r["dot"].setStyleSheet("color: #16A34A; font-size: 12px; border: none;")
                r["ds"].setText("Semua file siap diproses")
                r["ds"].setStyleSheet("color: #16A34A; font-size: 11px; font-weight: bold; border: none;")
            else:
                r["dot"].setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
                r["ds"].setText("Belum semua siap")
                r["ds"].setStyleSheet("color: #64748B; font-size: 11px; font-weight: bold; border: none;")

        # 2. KC
        if "kc" in self._stats_refs:
            r2 = self._stats_refs["kc"]
            if history_list and dash_ready:
                kc = history_list[0].get("jumlah_kc", 0)
                r2["val"].setText(str(kc))
                r2["dot"].setStyleSheet("color: #16A34A; font-size: 12px; border: none;")
                r2["ds"].setText("Data KC terdeteksi")
            else:
                r2["val"].setText("0")
                r2["dot"].setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
                r2["ds"].setText("Belum ada data")

        # 3. Periode
        if "periode" in self._stats_refs:
            r3 = self._stats_refs["periode"]
            if history_list:
                tgl = history_list[0].get("tanggal_data", "—")
                try:
                    y, m, d = tgl.split("-")
                    months = ["", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                    tgl_formatted = f"{int(d)} {months[int(m)]} {y}"
                except:
                    tgl_formatted = tgl
                r3["val"].setText(tgl_formatted)
                r3["val"].setStyleSheet("color: #16A34A; font-size: 24px; font-weight: bold; border: none;")
                r3["dot"].setStyleSheet("color: #16A34A; font-size: 12px; border: none;")
                r3["ds"].setText("Periode terbaru tersedia")
            else:
                r3["val"].setText("—")
                r3["val"].setStyleSheet("color: #94A3B8; font-size: 24px; font-weight: bold; border: none;")
                r3["dot"].setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
                r3["ds"].setText("Belum tersedia")

        # 4. Status Dashboard
        if "dash" in self._stats_refs:
            r4 = self._stats_refs["dash"]
            if history_list:
                tgl = history_list[0].get("tanggal_proses", "—")
                if " " in tgl:
                    d_part, t_part = tgl.split(" ", 1)
                    tgl_str = f"{d_part}, {t_part} WIB"
                else:
                    tgl_str = tgl
                
                if dash_ready:
                    status = history_list[0].get("status", "sukses").title()
                    r4["val"].setText("READY" if status.lower()=="sukses" else "ERROR")
                    r4["val"].setStyleSheet("color: #9333EA; font-size: 24px; font-weight: bold; border: none;" if status.lower()=="sukses" else "color: #DC2626; font-size: 24px; font-weight: bold; border: none;")
                    r4["time"].setText(f"Terakhir Update, {tgl_str}")
                    r4["dot"].setStyleSheet("color: #16A34A; font-size: 12px; border: none;" if status.lower()=="sukses" else "color: #DC2626; font-size: 12px; border: none;")
                    r4["ds"].setText("Dashboard telah diperbarui" if status.lower()=="sukses" else "Gagal diperbarui")
                else:
                    r4["val"].setText("NOT READY")
                    r4["val"].setStyleSheet("color: #94A3B8; font-size: 20px; font-weight: bold; border: none;")
                    r4["time"].setText(f"Terakhir Update, {tgl_str}")
                    r4["dot"].setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
                    r4["ds"].setText("Belum diperbarui")
            else:
                r4["val"].setText("NOT READY")
                r4["val"].setStyleSheet("color: #94A3B8; font-size: 20px; font-weight: bold; border: none;")
                r4["time"].setText("Terakhir Update, —")
                r4["dot"].setStyleSheet("color: #94A3B8; font-size: 12px; border: none;")
                r4["ds"].setText("Belum di-generate")
                
        # 5. Update Ringkasan Kinerja
        if hasattr(self, "_rk_1_v"):
            self._rk_1_v.setText(str(ready_count))
            self._rk_1_s.setText(f"{int((ready_count/3)*100)}% Selesai")
            
            if history_list:
                kc = history_list[0].get("jumlah_kc", 0)
                self._rk_2_v.setText(str(kc))
                self._rk_2_s.setText("Siap Diproses")
                self._rk_2_s.setStyleSheet("color: #D97706; font-size: 11px; font-weight: bold; border: none;")
                
                status = history_list[0].get("status", "sukses").lower()
                self._rk_3_v.setText("100%" if status == "sukses" else "0%")
                self._rk_3_s.setText("Tidak Ada Error" if status == "sukses" else "Terjadi Error")
                self._rk_3_s.setStyleSheet("color: #16A34A; font-size: 11px; font-weight: bold; border: none;" if status == "sukses" else "color: #DC2626; font-size: 11px; font-weight: bold; border: none;")
                
                tgl = history_list[0].get("tanggal_proses", "—")
                d_part = tgl.split(" ")[0] if " " in tgl else tgl
                self._rk_4_v.setText("Hari Ini")
                self._rk_4_s.setText(d_part)
            else:
                self._rk_2_v.setText("0")
                self._rk_2_s.setText("Menunggu")
                self._rk_3_v.setText("0%")
                self._rk_3_s.setText("Menunggu Proses")
                self._rk_4_v.setText("—")
                self._rk_4_s.setText("—")

    def refresh_activity(self, history_list: list | None):
        self._history_list = history_list or []
        while self._act_list_lay.count():
            item = self._act_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not history_list:
            self._show_empty_activity()
            return

        # Ambil proses terakhir (paling baru)
        entry = history_list[0]
        ok = entry.get("status", "sukses") != "gagal"
        
        # Ambil tanggal dan jam (format: YYYY-MM-DD HH:MM:SS)
        tgl_full = entry.get("tanggal_proses", "")
        # Format ke "DD MMM YYYY, HH:MM"
        try:
            if " " in tgl_full:
                d_part, t_part = tgl_full.split(" ")
                y, m, d = d_part.split("-")
                months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                tgl_str = f"{d} {months[int(m)]} {y}, {t_part[:5]}"
            else:
                tgl_str = tgl_full
        except:
            tgl_str = tgl_full

        fn_simpanan = entry.get("nama_file_simpanan") or "SSA Simpanan.csv"
        fn_pinjaman = entry.get("nama_file_pinjaman") or "SSA Pinjaman.csv"

        # Definisi baris aktivitas untuk 1 proses
        activities = [
            ("Upload File SSA", fn_simpanan, "upload.svg", "#EFF6FF", "#2563EB", "Sukses", ok),
            ("Upload File SSA", fn_pinjaman, "upload.svg", "#EFF6FF", "#2563EB", "Sukses", ok),
            ("Generate Dashboard", "Proses konsolidasi data", "settings.svg", "#F0FDF4", "#16A34A", "Sukses", ok),
            ("Export Excel", "Hasil Dashboard.xlsx", "unduh_homepage.svg", "#FFF7ED", "#D97706", "Berhasil", ok)
        ]

        for i, (title, detail, icon_name, bg_c, fg_c, status_text, is_ok) in enumerate(activities):
            row = QWidget()
            row.setStyleSheet("background: transparent; border-bottom: 1px solid #F1F5F9;")
            rl  = QHBoxLayout(row)
            rl.setContentsMargins(20, 14, 20, 14)

            # Aktivitas
            a_lay = QHBoxLayout()
            a_ic = self._icon_label(icon_name, bg_c, fg_c)
            # Make the icon slightly smaller for the table
            a_ic.setFixedSize(32, 32)
            
            a_txt = QLabel(title)
            a_txt.setStyleSheet("color: #0F2A4A; font-size: 11px; font-weight: bold; border: none;")
            a_lay.addWidget(a_ic); a_lay.addSpacing(8); a_lay.addWidget(a_txt); a_lay.addStretch()
            w_a = QWidget(); w_a.setLayout(a_lay); w_a.setFixedWidth(180)

            # Detail
            d_txt = QLabel(detail)
            d_txt.setStyleSheet("color: #64748B; font-size: 11px; border: none;")
            d_txt.setFixedWidth(220)

            # Waktu
            w_txt = QLabel(tgl_str)
            w_txt.setStyleSheet("color: #64748B; font-size: 11px; border: none;")
            w_txt.setFixedWidth(140)

            # Status
            s_txt = QLabel(status_text if is_ok else "Gagal")
            stat_bg = "#DCFCE7" if is_ok else "#FEE2E2"
            stat_fg = "#16A34A" if is_ok else "#DC2626"
            s_txt.setStyleSheet(f"background: {stat_bg}; color: {stat_fg}; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 6px; border: none;")
            s_lay = QHBoxLayout()
            s_lay.addWidget(s_txt); s_lay.addStretch()
            w_s = QWidget(); w_s.setLayout(s_lay)

            rl.addWidget(w_a)
            rl.addWidget(d_txt)
            rl.addWidget(w_txt)
            rl.addWidget(w_s)
            self._act_list_lay.addWidget(row)

    def _show_empty_activity(self):
        empty = QWidget()
        el = QVBoxLayout(empty)
        el.setContentsMargins(0, 24, 0, 24)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tx = QLabel("Belum ada aktivitas.")
        tx.setStyleSheet("color: #94A3B8; font-size: 13px; border: none;")
        el.addWidget(tx, alignment=Qt.AlignmentFlag.AlignCenter)
        self._act_list_lay.addWidget(empty)

    def _show_history_popup(self):
        from .history_popup import HistoryPopup
        popup = HistoryPopup(self._history_list, self)
        popup.exec()
