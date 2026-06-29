"""
preview_table.py — Halaman Preview Tabel.

Tab per KC. Setiap tab menampilkan tabel dengan kolom:
  Mata Anggaran | POSISI (per periode) | RKA (kosong) |
  Pencapaian RKA (—) | GROWTH (MTD | DTD | YOY | YTD)

Dilengkapi toolbar (Export Excel, Generate Ulang, Search).
"""
from __future__ import annotations

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton, QTabWidget, QTableWidget,
                               QTableWidgetItem, QHeaderView, QLineEdit,
                               QScrollArea, QAbstractItemView, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QColor, QFont, QBrush

from core.exporter import export_to_excel
from ui.toast_notification import ToastManager

# Warna baris
COLORS = {
    "header":   "#FFFFFF",
    "data_a":   "#FFFFFF",
    "data_b":   "#F8FAFC",
    "subtotal": "#EBF2FA",
    "total":    "#1F4E78",
}
FONT_TOTAL = QColor("#FFFFFF")
FONT_DARK  = QColor("#1E293B")
FONT_DIM   = QColor("#64748B")
FONT_RED   = QColor("#DC2626")


class PreviewTableWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self._init_ui()

    # ── BUILD UI ────────────────────────────────────────────────
    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Toolbar
        self._toolbar = self._build_toolbar()
        root.addWidget(self._toolbar)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: #FFFFFF; border-top: 1px solid #E2EAF4; }
            QTabBar::tab {
                background: #F8FAFC; color: #64748B; padding: 10px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                font-size: 13px; font-weight: bold;
                border: none; margin-right: 2px;
            }
            QTabBar::tab:selected { background: #FFFFFF; color: #2563EB; border-top: 3px solid #2563EB; }
            QTabBar::tab:hover:!selected { background: #F1F5F9; color: #1E293B; }
        """)
        root.addWidget(self._tabs)

        # Empty state
        self._empty = self._build_empty()
        root.addWidget(self._empty)

        self._show_empty()

    def _build_toolbar(self) -> QFrame:
        fr = QFrame()
        fr.setFixedHeight(64)
        fr.setStyleSheet("""
            QFrame { background: #FFFFFF; border-bottom: 1px solid #E2EAF4; }
        """)
        lay = QHBoxLayout(fr)
        lay.setContentsMargins(24, 0, 24, 0)
        lay.setSpacing(12)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cari mata anggaran, segmen, produk...")
        self._search.setFixedHeight(36)
        self._search.setMinimumWidth(300)
        self._search.setStyleSheet("""
            QLineEdit { background: #F8FAFC; border: 1px solid #E2EAF4;
                border-radius: 8px; padding: 0 12px; font-size: 13px; }
            QLineEdit:focus { border-color: #93C5FD; }
        """)
        self._search.textChanged.connect(self._filter_rows)

        lay.addWidget(self._search)
        lay.addStretch()

        # Tombol Generate Ulang
        btn_gen = QPushButton("Generate Ulang")
        btn_gen.setFixedHeight(36)
        btn_gen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_gen.setStyleSheet("""
            QPushButton { background: #EFF6FF; color: #2563EB; border: none;
                border-radius: 8px; padding: 0 16px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #DBEAFE; }
        """)
        btn_gen.clicked.connect(lambda: self.navigate_to.emit(2))

        # Tombol Export Excel
        self._btn_export = QPushButton("Export Excel")
        self._btn_export.setFixedHeight(36)
        self._btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_export.setEnabled(False)
        self._btn_export.setStyleSheet("""
            QPushButton { background: #16A34A; color: #FFFFFF; border: none;
                border-radius: 8px; padding: 0 16px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #15803D; }
            QPushButton:disabled { background: #CBD5E1; color: #FFFFFF; }
        """)
        self._btn_export.clicked.connect(self._export)

        lay.addWidget(btn_gen)
        lay.addWidget(self._btn_export)
        return fr

    def _build_empty(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(14)

        t1 = QLabel("Belum Ada Data Preview")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size: 20px; font-weight: bold; color: #1E293B;")
        t2 = QLabel("Lakukan generate terlebih dahulu untuk melihat preview tabel")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size: 14px; color: #64748B;")

        btn = QPushButton("Generate Sekarang")
        btn.setFixedHeight(40)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton { background: #2563EB; color: #FFFFFF; border-radius: 8px;
                padding: 0 24px; font-weight: bold; font-size: 14px; border: none; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn.clicked.connect(lambda: self.navigate_to.emit(2))

        lay.addWidget(t1)
        lay.addWidget(t2)
        lay.addSpacing(8)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        return w

    # ── LOAD DATA ────────────────────────────────────────────────
    def load_data(self, data_dict: dict):
        self._data = data_dict
        if not data_dict:
            self._show_empty()
            return

        self._tabs.clear()
        self._empty.hide()
        self._toolbar.show()
        self._tabs.show()
        self._btn_export.setEnabled(True)

        # Buat tab per KC — Total AH Gunsar terakhir
        kc_names = [k for k in data_dict if k not in ("Total AH Gunsar", "__stats__")]
        if "Total AH Gunsar" in data_dict:
            kc_names.append("Total AH Gunsar")

        for kc in kc_names:
            kc_data = data_dict[kc]
            short   = kc_data.get("kc_short", kc)[:20]
            widget  = self._build_tab(kc, kc_data)
            self._tabs.addTab(widget, short)

    def show_empty_cleared(self):
        """
        Tampilkan empty state khusus saat file wajib di-clear.
        Data preview dihapus dan tombol export dinonaktifkan.
        """
        self._data = {}
        self._tabs.clear()
        self._tabs.hide()
        self._btn_export.setEnabled(False)

        # Rebuild empty widget dengan pesan khusus
        # Hapus empty state lama
        old = self._empty
        if old:
            old.hide()

        w = QWidget()
        w.setStyleSheet("background: #F8FAFC;")
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(14)

        t1 = QLabel("Data Tidak Tersedia")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet(
            "font-size: 17px; font-weight: 700; color: #64748B;")

        t2 = QLabel(
            "File SSA telah dihapus. Upload ulang dan generate kembali.")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size: 13px; color: #94A3B8;")

        btn = QPushButton("Upload File")
        btn.setFixedHeight(38)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: white;
                border-radius: 8px; padding: 0 24px;
                font-weight: 600; font-size: 13px; border: none;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn.clicked.connect(lambda: self.navigate_to.emit(2))

        lay.addWidget(t1)
        lay.addWidget(t2)
        lay.addSpacing(8)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Insert ke root layout
        self.layout().addWidget(w)
        self._empty = w
        w.show()

    def _build_tab(self, kc_name: str, kc_data: dict) -> QWidget:
        """Buat satu tab berisi QTableWidget."""
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)

        rows_all  = kc_data.get("rows", [])
        rows_dpk  = kc_data.get("rows_dpk", [])
        rows_pinj = kc_data.get("rows_pinjaman", [])
        periodes  = kc_data.get("periode_list", [])
        mtd_lbl   = kc_data.get("mtd_label", "MTD")
        dtd_lbl   = kc_data.get("dtd_label", "DTD")
        yoy_lbl   = kc_data.get("yoy_label", "YOY")
        ytd_lbl   = kc_data.get("ytd_label", "YTD")

        # Kolom: Mata Anggaran + periode + 4 Growth
        col_headers = (["Mata Anggaran"] + periodes +
                       [mtd_lbl, dtd_lbl, yoy_lbl, ytd_lbl])

        all_rows = []
        if rows_all:
            all_rows = rows_all
        else:
            if rows_dpk:
                all_rows.append({"row_type": "__section__", "label": f"DPK — {kc_name}"})
                all_rows.extend(rows_dpk)
            if rows_pinj:
                all_rows.append({"row_type": "__section__", "label": f"PINJAMAN — {kc_name}"})
                all_rows.extend(rows_pinj)

        tbl = QTableWidget(len(all_rows), len(col_headers))
        tbl.setHorizontalHeaderLabels(col_headers)
        tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        tbl.setAlternatingRowColors(False)
        tbl.verticalHeader().setVisible(False)
        tbl.setFrameShape(QFrame.Shape.NoFrame)
        tbl.setGridStyle(Qt.PenStyle.SolidLine)
        tbl.setStyleSheet("""
            QTableWidget { background: #FFFFFF; gridline-color: #F1F5F9; border: none; }
            QHeaderView::section {
                background-color: #1E3A5F; color: #FFFFFF; font-weight: bold;
                font-size: 12px; padding: 8px; border: none;
                border-right: 1px solid #2A5080; border-bottom: 1px solid #2A5080;
            }
            QTableWidget::item:selected { background: #EFF6FF; color: #1E3A5F; }
        """)

        # Resize kolom
        hh = tbl.horizontalHeader()
        hh.setDefaultSectionSize(120)
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        tbl.setColumnWidth(0, 220)

        n_p = len(periodes)
        for i in range(1, n_p + 1):
            tbl.setColumnWidth(i, 110)
        for i in range(n_p + 1, n_p + 5):
            tbl.setColumnWidth(i, 130)

        # Isi baris
        for r_idx, row_data in enumerate(all_rows):
            row_type = row_data.get("row_type", "data")
            label    = row_data.get("label", "")
            values   = row_data.get("values", {})
            mtd_v    = row_data.get("mtd", 0)
            dtd_v    = row_data.get("dtd", 0)
            yoy_v    = row_data.get("yoy", 0)
            ytd_v    = row_data.get("ytd", 0)

            # Section separator (old format)
            if row_type == "__section__":
                for c in range(len(col_headers)):
                    item = QTableWidgetItem(label if c == 0 else "")
                    item.setBackground(QBrush(QColor("#0F2A4A")))
                    item.setForeground(QBrush(QColor("#FFFFFF")))
                    f = QFont()
                    f.setBold(True)
                    item.setFont(f)
                    tbl.setItem(r_idx, c, item)
                tbl.setRowHeight(r_idx, 26)
                continue

            # Separator (new format — baris biru solid tipis)
            if row_type == "separator":
                for c in range(len(col_headers)):
                    item = QTableWidgetItem("")
                    item.setBackground(QBrush(QColor("#1E3A5F")))
                    tbl.setItem(r_idx, c, item)
                tbl.setRowHeight(r_idx, 8)
                continue

            # Pilih warna baris
            font_obj = QFont()
            if row_type == "total":
                bg_clr = QColor(COLORS["total"])
                fg_clr = FONT_TOTAL
                font_obj.setBold(True)
            elif row_type == "subtotal":
                bg_clr = QColor(COLORS["subtotal"])
                fg_clr = FONT_DARK
                font_obj.setBold(True)
                font_obj.setItalic(True)
            elif row_type == "header":
                bg_clr = QColor(COLORS["header"])
                fg_clr = FONT_DARK
                font_obj.setBold(True)
            elif row_type == "bold":
                bg_clr = QColor(COLORS.get("subtotal", "#EFF6FF"))
                fg_clr = FONT_DARK
                font_obj.setBold(True)
            else:
                bg_clr = QColor(COLORS["data_a"] if r_idx % 2 == 0
                                 else COLORS["data_b"])
                fg_clr = FONT_DARK
                font_obj.setBold(False)

            tbl.setRowHeight(r_idx, 28)

            # Kolom 0: Mata Anggaran
            item_ma = QTableWidgetItem(label)
            item_ma.setBackground(QBrush(bg_clr))
            item_ma.setForeground(QBrush(fg_clr))
            item_ma.setFont(font_obj)
            tbl.setItem(r_idx, 0, item_ma)

            # Kolom Posisi
            for c_i, p in enumerate(periodes):
                val = values.get(p, 0)
                if row_type == "header" or val == "":
                    txt = ""
                else:
                    try:
                        is_pct = '%' in label
                        txt = f"{val * 100:,.2f}%" if is_pct else f"{val:,.0f}"
                    except:
                        txt = str(val)
                it  = QTableWidgetItem(txt)
                it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                it.setBackground(QBrush(bg_clr))
                it.setForeground(QBrush(fg_clr))
                it.setFont(font_obj)
                tbl.setItem(r_idx, 1 + c_i, it)

            # Growth columns
            growth_start = n_p + 1
            for gi, gv in enumerate([mtd_v, dtd_v, yoy_v, ytd_v]):
                if row_type == "header" or gv == "":
                    txt = ""
                elif gv == 0:
                    txt = "0"
                else:
                    try:
                        txt = f"{gv:,.0f}"
                    except:
                        txt = str(gv)
                it_g = QTableWidgetItem(txt)
                it_g.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                it_g.setBackground(QBrush(bg_clr))
                # Warna font growth
                if row_type not in ("header", "__section__"):
                    is_negative = isinstance(gv, (int, float)) and gv < 0
                    if is_negative:
                        it_g.setForeground(QBrush(FONT_RED))
                    elif row_type == "total":
                        it_g.setForeground(QBrush(FONT_TOTAL))
                    else:
                        it_g.setForeground(QBrush(fg_clr))
                it_g.setFont(font_obj)
                tbl.setItem(r_idx, growth_start + gi, it_g)

        lay.addWidget(tbl)
        self._current_table = tbl
        return w

    # ── SEARCH ───────────────────────────────────────────────────
    def _filter_rows(self, query: str):
        q = query.strip().lower()
        for i in range(self._tabs.count()):
            widget = self._tabs.widget(i)
            tbl    = widget.findChild(QTableWidget)
            if not tbl:
                continue
            for r in range(tbl.rowCount()):
                item = tbl.item(r, 0)
                if item:
                    visible = (not q) or (q in item.text().lower())
                    tbl.setRowHidden(r, not visible)

    # ── EXPORT ───────────────────────────────────────────────────
    def _export(self):
        if not self._data:
            ToastManager.show(self.window(), "Tidak ada data untuk dieksport.", "warning")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export Excel", "Dashboard_SSA.xlsx",
            "Excel Files (*.xlsx)")
        if not path:
            return

        try:
            export_to_excel(self._data, path)
            ToastManager.show(self.window(),
                              f"File berhasil disimpan: {path}", "success")
        except Exception as e:
            ToastManager.show(self.window(), f"Gagal export: {e}", "error")

    # ── HELPERS ──────────────────────────────────────────────────
    def _show_empty(self):
        self._tabs.hide()
        self._toolbar.hide()
        self._empty.show()
