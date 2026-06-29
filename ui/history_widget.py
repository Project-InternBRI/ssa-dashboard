"""
history_widget.py — Halaman Riwayat Generate.

Card per entri: 3 tombol saja — Lihat, Export, Hapus.
Tombol "Lihat" membuka HistoryPreviewDialog (popup tabel besar).
Tanpa emoji di seluruh UI.
"""
import os
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QScrollArea,
    QFileDialog, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QCursor

from core.history_manager import (
    load_history, delete_history_entry, clear_history)
from ui.toast_notification import ToastManager
from ui.confirm_popup import ConfirmPopup
from PySide6.QtWidgets import QDialog, QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from ui.custom_dropdown import CustomDropdown
import datetime

class HistoryFilterPopup(QDialog):
    def __init__(self, current_month, current_year, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.init_ui(current_month, current_year)
        
    def init_ui(self, m, y):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(10, 10, 10, 10)
        
        container = QFrame(self)
        container.setStyleSheet("QFrame#container { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 16px; }")
        container.setObjectName("container")
        container.setMinimumWidth(250)
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 5)
        container.setGraphicsEffect(shadow)
        
        lay = QVBoxLayout(container)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)
        
        title = QLabel("Filter Riwayat")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F172A; background: transparent;")
        lay.addWidget(title)
        lay.addSpacing(8)
        
        lbl_month = QLabel("Bulan")
        lbl_month.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; background: transparent;")
        lay.addWidget(lbl_month)
        
        months = ["Semua Bulan", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        self.cb_month = CustomDropdown(months, self)
        self.cb_month.setCurrentText(m)
        lay.addWidget(self.cb_month)
        
        lbl_year = QLabel("Tahun")
        lbl_year.setStyleSheet("font-size: 12px; font-weight: bold; color: #64748B; background: transparent;")
        lay.addWidget(lbl_year)
        
        cur_year = datetime.datetime.now().year
        years = ["Semua Tahun"] + [str(yr) for yr in range(cur_year-2, cur_year+3)]
        self.cb_year = CustomDropdown(years, self)
        self.cb_year.setCurrentText(y)
        lay.addWidget(self.cb_year)
        
        lay.addSpacing(12)
        
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        
        btn_cancel = QPushButton("Batal")
        btn_cancel.setFixedHeight(36)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: none; border-radius: 18px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #E2E8F0; }")
        btn_cancel.clicked.connect(self.reject)
        
        btn_apply = QPushButton("Terapkan Filter")
        btn_apply.setFixedHeight(36)
        btn_apply.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_apply.setStyleSheet("QPushButton { background: #2563EB; color: #FFFFFF; border: none; border-radius: 18px; font-weight: bold; font-size: 13px; } QPushButton:hover { background: #1D4ED8; }")
        btn_apply.clicked.connect(self.accept)
        
        btn_lay.addWidget(btn_cancel)
        btn_lay.addWidget(btn_apply)
        
        lay.addLayout(btn_lay)
        main_lay.addWidget(container)


class HistoryWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.filter_month = "Semua Bulan"
        self.filter_year = "Semua Tahun"
        self._init_ui()

    # ─── INIT UI ──────────────────────────────────────────────────
    def _init_ui(self):
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
        self._main_lay.setSpacing(16)

        # Header dengan pencarian, filter, dan tombol hapus semua
        hdr = QHBoxLayout()
        hdr.setSpacing(12)
        
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Cari tanggal (contoh: 29)...")
        self._search_input.setFixedHeight(34)
        self._search_input.setFixedWidth(220)
        self._search_input.setStyleSheet("QLineEdit { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 17px; padding: 0 16px; color: #0F172A; font-size: 13px; } QLineEdit:focus { border: 1px solid #3B82F6; }")
        
        self._btn_filter = QPushButton("Filter")
        self._btn_filter.setFixedHeight(36)
        self._btn_filter.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_filter.setStyleSheet("""
            QPushButton { background: #2563EB; border: none; border-radius: 18px; color: #FFFFFF; padding: 0 20px; font-weight: 600; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        self._btn_filter.clicked.connect(self.open_filter_popup)
        
        self._btn_del_all = QPushButton("Hapus Semua")
        self._btn_del_all.setFixedHeight(34)
        self._btn_del_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_del_all.setObjectName("btnOutlineDanger")
        self._btn_del_all.setStyleSheet("""
            QPushButton {
                background: #FEE2E2; color: #DC2626; border: none;
                border-radius: 17px; padding: 0 16px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background: #FECACA; }
        """)
        self._btn_del_all.clicked.connect(self._confirm_delete_all)
        self._btn_del_all.hide()

        hdr.addWidget(self._search_input)
        hdr.addWidget(self._btn_filter)
        hdr.addStretch()
        hdr.addWidget(self._btn_del_all)
        self._main_lay.addLayout(hdr)

        # List area
        self._list_area = QVBoxLayout()
        self._list_area.setSpacing(14)
        self._main_lay.addLayout(self._list_area)
        self._main_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def open_filter_popup(self):
        popup = HistoryFilterPopup(self.filter_month, self.filter_year, self)
        
        # Position popup relative to the button
        pos = self._btn_filter.mapToGlobal(self._btn_filter.rect().bottomLeft())
        # Offset to align nicely
        popup.move(pos.x() - 10, pos.y() + 5)
        
        if popup.exec() == QDialog.DialogCode.Accepted:
            self.filter_month = popup.cb_month.currentText()
            self.filter_year = popup.cb_year.currentText()
            self.refresh()

    # ─── REFRESH ──────────────────────────────────────────────────
    def refresh(self):
        while self._list_area.count():
            item = self._list_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = load_history()
        if not history:
            self._btn_del_all.hide()
            self._show_empty()
            return

        self._btn_del_all.show()
        
        from collections import defaultdict
        grouped = defaultdict(lambda: defaultdict(list))
        
        search_txt = self._search_input.text().lower().strip()
        filter_month = self.filter_month
        filter_year = self.filter_year
        
        for idx, entry in enumerate(history):
            tgl_full = entry.get("tanggal_proses", "")
            if not tgl_full:
                continue
            
            try:
                if " " in tgl_full:
                    d_part, t_part = tgl_full.split(" ")
                    y, m, d = d_part.split("-")
                    months = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
                    month_name = months[int(m)]
                    month_year_key = f"{month_name} {y}"
                    date_key = f"{int(d)} {month_name[:3]} {y}"
                else:
                    month_year_key = "Lainnya"
                    date_key = tgl_full
                    month_name = ""
                    y = ""
            except:
                month_year_key = "Lainnya"
                date_key = tgl_full
                month_name = ""
                y = ""
            
            if search_txt and search_txt not in date_key.lower():
                continue
            if filter_month != "Semua Bulan" and filter_month != month_name:
                continue
            if filter_year != "Semua Tahun" and filter_year != y:
                continue
            
            grouped[month_year_key][date_key].append((idx, entry))

        for my_key, dates in grouped.items():
            # Month Header
            my_lbl = QLabel(my_key)
            my_lbl.setStyleSheet("font-size: 18px; font-weight: 800; color: #0F2A4A; margin-top: 16px; margin-bottom: 4px;")
            self._list_area.addWidget(my_lbl)
            
            for d_key, runs in dates.items():
                # Date Header
                dh_lbl = QLabel(d_key)
                dh_lbl.setStyleSheet("font-size: 14px; font-weight: 700; color: #64748B; margin-top: 8px; margin-bottom: 4px;")
                self._list_area.addWidget(dh_lbl)
                
                for run_idx, (idx, entry) in enumerate(runs):
                    card = self._make_card(entry, idx)
                    self._list_area.addWidget(card)

    # ─── EMPTY STATE ──────────────────────────────────────────────
    def _show_empty(self):
        empty = QWidget()
        empty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(empty)
        el.setContentsMargins(0, 80, 0, 0)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(12)

        # Ikon SVG sederhana (lingkaran jam)
        ic = QLabel("( )")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet(
            "font-size: 48px; color: #CBD5E1; font-weight: 300; background: transparent;")

        t1 = QLabel("Belum Ada Riwayat Generate")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet(
            "font-size: 16px; font-weight: 700; color: #64748B; background: transparent;")

        t2 = QLabel("Riwayat akan muncul setelah Anda melakukan generate")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet(
            "font-size: 13px; color: #94A3B8; background: transparent;")

        btn_gen = QPushButton("Mulai Generate")
        btn_gen.setFixedHeight(38)
        btn_gen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_gen.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: #FFFFFF;
                border-radius: 8px; font-weight: 600;
                font-size: 13px; padding: 0 24px; border: none;
            }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn_gen.clicked.connect(lambda: self.navigate_to.emit(2))

        el.addWidget(ic)
        el.addWidget(t1)
        el.addWidget(t2)
        el.addSpacing(12)
        el.addWidget(btn_gen, alignment=Qt.AlignmentFlag.AlignCenter)
        self._list_area.addWidget(empty)

    # ─── CARD ─────────────────────────────────────────────────────
    def _make_card(self, entry: dict, idx: int) -> QFrame:
        ok = entry.get("status", "sukses") != "gagal"
        output_path = entry.get("output_path", "")

        card = QFrame()
        card.setObjectName("HistoryCard")
        card.setStyleSheet("""
            QFrame#HistoryCard {
                background: #FFFFFF;
                border: none;
                border-radius: 12px;
            }
            QFrame#HistoryCard:hover { background: #FAFBFF; }
        """)
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 10))
        shadow.setOffset(0, 2)
        card.setGraphicsEffect(shadow)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        # Row 1: Status + Judul + Tanggal
        r1 = QHBoxLayout()
        r1.setSpacing(8)

        status_dot = QLabel()
        status_dot.setFixedSize(8, 8)
        status_dot.setStyleSheet(
            f"background: {'#10B981' if ok else '#EF4444'};"
            "border-radius: 4px;")

        tgl_data = entry.get("tanggal_data", "Unknown")
        tit = QLabel(f"Dashboard AH Gunsar — {tgl_data}")
        tit.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #0F172A; background: transparent;")

        tgl_proc = entry.get("tanggal_proses", "")[:16]
        lbl_proc = QLabel(f"Diproses: {tgl_proc}")
        lbl_proc.setStyleSheet(
            "font-size: 12px; color: #94A3B8; background: transparent;")

        r1.addWidget(status_dot, 0, Qt.AlignmentFlag.AlignVCenter)
        r1.addWidget(tit)
        r1.addStretch()
        r1.addWidget(lbl_proc)
        lay.addLayout(r1)

        # Row 2: Stats
        kc = entry.get('jumlah_kc', 0)
        sz = entry.get('ukuran_file', '0 KB')
        wkt = entry.get('waktu_proses', '—')
        n_periode = entry.get('jumlah_periode', 0)

        lbl_stats = QLabel(
            f"{kc} KC  ·  {n_periode} periode  ·  {sz}  ·  {wkt}")
        lbl_stats.setStyleSheet(
            "font-size: 12px; color: #64748B; background: transparent;")
        lay.addWidget(lbl_stats)

        # Row 3: File names
        f_s = entry.get('nama_file_simpanan', '-')
        f_p = entry.get('nama_file_pinjaman', '-')
        lbl_files = QLabel(f"Simpanan: {f_s}   |   Pinjaman: {f_p}")
        lbl_files.setStyleSheet(
            "font-size: 11px; color: #94A3B8; background: transparent;")
        lbl_files.setWordWrap(True)
        lay.addWidget(lbl_files)

        # Row 4: 3 Tombol
        r_btn = QHBoxLayout()
        r_btn.setSpacing(8)

        file_exists = ok and output_path and Path(output_path).exists()

        # Tombol Lihat
        btn_lihat = QPushButton("Lihat")
        btn_lihat.setFixedHeight(32)
        btn_lihat.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_lihat.setStyleSheet("""
            QPushButton {
                background: #2563EB; color: #FFFFFF;
                border: none; border-radius: 6px;
                padding: 0 16px; font-weight: 500; font-size: 12px;
            }
            QPushButton:hover { background: #1D4ED8; }
            QPushButton:disabled {
                background: #E2E8F0; color: #94A3B8;
            }
        """)
        btn_lihat.setEnabled(file_exists)
        btn_lihat.clicked.connect(
            lambda _, p=output_path, e=entry: self._open_preview(p, e))

        # Tombol Export
        btn_export = QPushButton("Export")
        btn_export.setFixedHeight(32)
        btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_export.setStyleSheet("""
            QPushButton {
                background: #10B981; color: #FFFFFF;
                border: none; border-radius: 6px;
                padding: 0 16px; font-weight: 500; font-size: 12px;
            }
            QPushButton:hover { background: #059669; }
            QPushButton:disabled {
                background: #E2E8F0; color: #94A3B8;
            }
        """)
        btn_export.setEnabled(file_exists)
        btn_export.clicked.connect(
            lambda _, e=entry: self._export_file(e))

        # Tombol Hapus
        btn_hapus = QPushButton("Hapus")
        btn_hapus.setFixedHeight(32)
        btn_hapus.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hapus.setStyleSheet("""
            QPushButton {
                background: #EF4444; color: #FFFFFF;
                border: none; border-radius: 6px;
                padding: 0 16px; font-weight: 500; font-size: 12px;
            }
            QPushButton:hover { background: #DC2626; }
        """)
        btn_hapus.clicked.connect(lambda _, i=idx: self._confirm_delete(i))

        r_btn.addStretch()
        r_btn.addWidget(btn_lihat)
        r_btn.addWidget(btn_export)
        r_btn.addWidget(btn_hapus)
        lay.addLayout(r_btn)

        return card

    # ─── AKSI TOMBOL ──────────────────────────────────────────────
    def _open_preview(self, output_path: str, entry: dict):
        """Buka HistoryPreviewDialog dengan data dari file Excel."""
        from ui.history_preview_dialog import HistoryPreviewDialog
        if not Path(output_path).exists():
            ToastManager.show(self.window(), "File tidak ditemukan.", "error")
            return
        dlg = HistoryPreviewDialog(output_path, entry, parent=self.window())
        dlg.exec()

    def _export_file(self, entry: dict):
        """Salin file Excel ke lokasi yang dipilih user tanpa replace."""
        src_path = entry.get("output_path", "")
        src = Path(src_path)
        if not src.exists():
            ToastManager.show(self.window(), "File tidak ditemukan.", "error")
            return

        import json
        import os
        from core.exporter import get_default_export_filename, get_unique_path
        
        json_path = entry.get("json_path", "")
        data = {}
        try:
            if Path(json_path).exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
        except:
            pass

        base_name = get_default_export_filename(data, "AH Gunsar")
        downloads = str(Path.home() / "Downloads")
        default_path = get_unique_path(os.path.join(downloads, base_name))

        options = QFileDialog.Option.DontConfirmOverwrite
        dest, _ = QFileDialog.getSaveFileName(
            self, "Simpan File Excel", default_path, "Excel Files (*.xlsx)", options=options)
            
        if not dest:
            return

        try:
            shutil.copy2(str(src), dest)
            ToastManager.show(
                self.window(), f"File berhasil disimpan: {dest}", "success")
        except Exception as e:
            ToastManager.show(
                self.window(), f"Gagal ekspor: {e}", "error")

    def _confirm_delete(self, idx: int):
        if ConfirmPopup.ask(
            self, "Konfirmasi Hapus",
            "Yakin ingin menghapus riwayat ini?\nFile Excel hasil generate juga akan dihapus.",
            action_text="Hapus",
            action_color="#DC2626"
        ):
            if delete_history_entry(idx):
                self.refresh()
                ToastManager.show(self.window(), "Riwayat dihapus.", "info")
            else:
                ToastManager.show(
                    self.window(), "Gagal menghapus riwayat.", "error")

    def _confirm_delete_all(self):
        if ConfirmPopup.ask(
            self, "Konfirmasi Hapus Semua",
            "Yakin ingin menghapus SEMUA riwayat?\nFile Excel hasil generate juga akan dihapus.",
            action_text="Hapus Semua",
            action_color="#DC2626"
        ):
            clear_history()
            self.refresh()
            ToastManager.show(self.window(), "Semua riwayat dihapus.", "info")
