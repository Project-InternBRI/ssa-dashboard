"""
success_popup.py — Popup sukses setelah generate berhasil.

Konten dinamis:
  - 2 card jika hanya file berjalan (Simpanan + Pinjaman)
  - 4 card (2x2) jika ada file historis

Tombol tanpa ikon. Animasi fade-in.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect,
    QApplication, QGridLayout, QWidget,
)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QCursor, QColor


class SuccessPopup(QDialog):
    """
    Popup sukses setelah generate berhasil.
    Signals:
        view_preview  — user klik "Lihat Preview"
        export_excel  — user klik "Export Excel"
    """
    view_preview = Signal()
    export_excel = Signal()

    def __init__(self, parent=None, stats: dict | None = None,
                 elapsed: float = 0.0):
        super().__init__(
            parent,
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        self._stats = stats or {}
        self._elapsed = elapsed

        # Tentukan mode: 2 card atau 4 card
        has_historis = (
            self._stats.get('has_historis_simpanan', False)
            or self._stats.get('has_historis_pinjaman', False)
        )
        self._mode = 4 if has_historis else 2

        self._mode = 4 if has_historis else 2

        self.setStyleSheet("QDialog { background: transparent; border: 0px solid transparent; outline: none; }")

        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)

        # Card container
        self._card = QFrame(self)
        self._card.setObjectName("popupCard")
        self._card.setMinimumWidth(480)
        self._card.setStyleSheet("""
            QFrame#popupCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: none;
            }
        """)

        main_lay.addWidget(self._card)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(40)
        shadow.setColor(QColor(15, 23, 42, 50))
        shadow.setOffset(0, 8)
        self._card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(self._card)
        lay.setContentsMargins(32, 28, 32, 24)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignTop)

        # ── Ikon Centang ─────────────────────────────────────────
        icon_frame = QFrame()
        icon_frame.setFixedSize(56, 56)
        icon_frame.setStyleSheet("""
            QFrame {
                background-color: #ECFDF5;
                border-radius: 28px;
                border: 2.5px solid #6EE7B7;
            }
        """)
        ic_lbl = QLabel("✓", icon_frame)
        ic_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic_lbl.setGeometry(0, 0, 56, 56)
        ic_lbl.setStyleSheet(
            "font-size:26px; color:#10B981; background:transparent;")

        # ── Judul ────────────────────────────────────────────────
        lbl_title = QLabel("Generate Berhasil")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            "font-size:18px; font-weight:700; color:#0F172A; background: transparent;")

        # ── Sub-teks ─────────────────────────────────────────────
        lbl_sub = QLabel("Dashboard SSA telah berhasil dibuat.")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size:13px; color:#64748B; background: transparent;")

        # ── Info Cards ───────────────────────────────────────────
        cards_frame = self._build_cards()

        # ── Tombol ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        btn_preview = QPushButton("Lihat Preview")
        btn_preview.setFixedHeight(42)
        btn_preview.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_preview.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)
        btn_preview.clicked.connect(self._on_preview)

        btn_export = QPushButton("Export Excel")
        btn_export.setFixedHeight(42)
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #10B981;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #059669; }
        """)
        btn_export.clicked.connect(self._on_export)

        btn_row.addWidget(btn_preview)
        btn_row.addWidget(btn_export)

        # Tombol tutup
        btn_close = QPushButton("Tutup")
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #94A3B8;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: #64748B; }
        """)
        btn_close.clicked.connect(self.close)

        # Susun layout
        lay.addWidget(icon_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(lbl_title)
        lay.addWidget(lbl_sub)
        lay.addWidget(cards_frame)
        lay.addLayout(btn_row)
        lay.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignHCenter)

    # ─── BUILD CARDS ──────────────────────────────────────────────
    def _build_cards(self) -> QFrame:
        """Buat info cards: 2 card atau 4 card sesuai mode."""
        outer = QFrame()
        outer.setObjectName("OuterCard")
        outer.setStyleSheet("""
            QFrame#OuterCard {
                background: #F8FAFC;
                border: none;
                border-radius: 10px;
            }
        """)

        if self._mode == 2:
            grid = QHBoxLayout(outer)
            grid.setContentsMargins(16, 14, 16, 14)
            grid.setSpacing(16)
            self._add_info_card(
                grid,
                "SSA Simpanan",
                "Periode Berjalan",
                f"{self._stats.get('baris_simpanan_berjalan', 0):,} baris",
            )
            self._add_divider_v(grid)
            self._add_info_card(
                grid,
                "SSA Pinjaman",
                "Periode Berjalan",
                f"{self._stats.get('baris_pinjaman_berjalan', 0):,} baris",
            )
            # Tambah waktu di baris ini
            self._add_divider_v(grid)
            self._add_info_card(
                grid,
                "Waktu Proses",
                f"{self._stats.get('jumlah_kc', 0)} KC · {self._stats.get('jumlah_periode', 0)} periode",
                f"{self._elapsed:.2f} detik",
            )

        else:
            # 4 card mode (ada historis)
            grid = QGridLayout(outer)
            grid.setContentsMargins(16, 14, 16, 14)
            grid.setSpacing(12)

            self._add_grid_card(
                grid, 0, 0,
                "SSA Simpanan",
                "Periode Berjalan",
                f"{self._stats.get('baris_simpanan_berjalan', 0):,} baris",
            )
            self._add_grid_card(
                grid, 0, 1,
                "SSA Pinjaman",
                "Periode Berjalan",
                f"{self._stats.get('baris_pinjaman_berjalan', 0):,} baris",
            )
            self._add_grid_card(
                grid, 1, 0,
                "SSA Simpanan",
                "Periode Historis",
                f"{self._stats.get('baris_simpanan_historis', 0):,} baris",
            )
            self._add_grid_card(
                grid, 1, 1,
                "SSA Pinjaman",
                "Periode Historis",
                f"{self._stats.get('baris_pinjaman_historis', 0):,} baris",
            )

        return outer

    def _add_info_card(self, layout, title: str, subtitle: str, value: str):
        """Tambah satu info card ke HBoxLayout."""
        col = QVBoxLayout()
        col.setSpacing(3)
        col.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(
            "font-size:11px; font-weight:600; color:#64748B; background:transparent;")

        lbl_sub = QLabel(subtitle)
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(
            "font-size:10px; color:#94A3B8; background:transparent;")

        lbl_val = QLabel(value)
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_val.setStyleSheet(
            "font-size:16px; font-weight:700; color:#0F172A; background:transparent;")

        col.addWidget(lbl_title)
        col.addWidget(lbl_sub)
        col.addWidget(lbl_val)

        layout.addLayout(col)

    def _add_divider_v(self, layout):
        """Divider vertikal tipis."""
        div = QFrame()
        div.setFixedSize(1, 40)
        div.setStyleSheet("background:#E2E8F0;")
        layout.addWidget(div, alignment=Qt.AlignmentFlag.AlignVCenter)

    def _add_grid_card(self, grid: QGridLayout, row: int, col: int,
                       title: str, subtitle: str, value: str):
        """Tambah card ke QGridLayout."""
        cell = QFrame()
        cell.setObjectName("GridCard")
        cell.setStyleSheet("""
            QFrame#GridCard {
                background: #FFFFFF;
                border: none;
                border-radius: 8px;
            }
        """)
        c_lay = QVBoxLayout(cell)
        c_lay.setContentsMargins(12, 14, 12, 14)
        c_lay.setSpacing(6)

        lbl_t = QLabel(title)
        lbl_t.setStyleSheet(
            "font-size:11px; font-weight:600; color:#64748B; background:transparent;")

        lbl_s = QLabel(subtitle)
        lbl_s.setStyleSheet(
            "font-size:10px; color:#94A3B8; background:transparent;")

        lbl_v = QLabel(value)
        lbl_v.setStyleSheet(
            "font-size:15px; font-weight:700; color:#0F172A; background:transparent;")

        c_lay.addWidget(lbl_t)
        c_lay.addWidget(lbl_s)
        c_lay.addWidget(lbl_v)
        grid.addWidget(cell, row, col)

    # ─── ANIMASI ──────────────────────────────────────────────────
    def show_animated(self):
        """Tampilkan popup dengan animasi fade-in."""
        self.setWindowOpacity(0.0)
        self.show()
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(250)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    # ─── SLOT TOMBOL ──────────────────────────────────────────────
    def _on_preview(self):
        self.close()
        self.view_preview.emit()

    def _on_export(self):
        self.close()
        self.export_excel.emit()

    # ─── POSISI ───────────────────────────────────────────────────
    def center_on_parent(self):
        self.adjustSize()
        if self.parent():
            pg = self.parent().geometry()
            x = pg.x() + (pg.width() - self.width()) // 2
            y = pg.y() + (pg.height() - self.height()) // 2
            self.move(x, y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            self.move(
                (screen.width() - self.width()) // 2,
                (screen.height() - self.height()) // 2,
            )
