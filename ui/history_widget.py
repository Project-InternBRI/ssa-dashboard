"""
history_widget.py — Halaman Riwayat Generate.
Menampilkan daftar riwayat, opsi download ulang, hapus per entri,
serta fitur hapus semua.
"""
import os
import shutil
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton, QScrollArea, QMessageBox,
                               QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor

from core.history_manager import load_history, delete_history, delete_all_history, get_history_file_path
from ui.toast_notification import ToastManager


class HistoryWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
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
        self._main_lay.setSpacing(16)

        # 1. HEADER
        hdr = QHBoxLayout()
        hdr_txt = QVBoxLayout()
        hdr_txt.setSpacing(4)
        lbl_t = QLabel("Riwayat Generate")
        lbl_t.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F2A4A;")
        lbl_s = QLabel("Daftar dashboard yang pernah dihasilkan")
        lbl_s.setStyleSheet("font-size: 13px; color: #94A3B8;")
        hdr_txt.addWidget(lbl_t)
        hdr_txt.addWidget(lbl_s)
        
        self.btn_del_all = QPushButton("🗑️ Hapus Semua")
        self.btn_del_all.setFixedHeight(36)
        self.btn_del_all.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_del_all.setStyleSheet("""
            QPushButton { background: transparent; color: #DC2626; border: 1.5px solid #FCA5A5; border-radius: 6px; padding: 0 16px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #FEF2F2; border-color: #DC2626; }
        """)
        self.btn_del_all.clicked.connect(self._confirm_delete_all)
        self.btn_del_all.hide()

        hdr.addLayout(hdr_txt)
        hdr.addStretch()
        hdr.addWidget(self.btn_del_all, alignment=Qt.AlignmentFlag.AlignTop)
        
        self._main_lay.addLayout(hdr)

        # 2. LIST AREA
        self._list_area = QVBoxLayout()
        self._list_area.setSpacing(16)
        self._main_lay.addLayout(self._list_area)
        self._main_lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    def refresh(self):
        while self._list_area.count():
            item = self._list_area.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        history = load_history()

        if not history:
            self.btn_del_all.hide()
            self._show_empty()
            return

        self.btn_del_all.show()
        for entry in history:
            card = self._make_card(entry)
            self._list_area.addWidget(card)

    def _show_empty(self):
        empty = QWidget()
        empty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(empty)
        el.setContentsMargins(0, 60, 0, 0)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(12)

        ic = QLabel("🕒")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 64px; color: #CBD5E1; border: none;")

        t1 = QLabel("Belum Ada Riwayat Generate")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        
        t2 = QLabel("Riwayat akan muncul setelah Anda melakukan generate")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size: 14px; color: #64748B;")

        btn_gen = QPushButton("Mulai Generate Sekarang")
        btn_gen.setFixedHeight(40)
        btn_gen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_gen.setStyleSheet("""
            QPushButton { background: #2563EB; color: #FFFFFF; border-radius: 8px; font-weight: bold; font-size: 13px; padding: 0 24px; border: none; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn_gen.clicked.connect(lambda: self.navigate_to.emit(2))

        el.addWidget(ic)
        el.addWidget(t1)
        el.addWidget(t2)
        el.addSpacing(16)
        el.addWidget(btn_gen, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._list_area.addWidget(empty)

    def _make_card(self, entry: dict) -> QFrame:
        eid = entry.get("id", "")
        ok = entry.get("status", "sukses") != "gagal"

        card = QFrame()
        card.setStyleSheet("""
            QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2EAF4; }
            QFrame:hover { border-color: #93C5FD; }
        """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(8)

        # Row 1: Title & Date
        r1 = QHBoxLayout()
        ic = QLabel("✅" if ok else "❌")
        ic.setStyleSheet("background: transparent; border: none; font-size: 16px;")
        
        tgl_data = entry.get("tanggal_data", "Unknown")
        tit = QLabel(f"Dashboard AH Gunsar — {tgl_data}")
        tit.setStyleSheet("font-size: 15px; font-weight: bold; color: #1E293B; border: none;")
        
        tgl_proc = entry.get("tanggal_proses", "")
        if len(tgl_proc) > 10:
            # Format to "22 Jun, 14:32" logic simplified
            tgl_proc = tgl_proc[:16] # e.g. "2026-06-23 11:32"
        lbl_d = QLabel(tgl_proc)
        lbl_d.setStyleSheet("font-size: 12px; color: #94A3B8; font-weight: bold; border: none;")

        r1.addWidget(ic)
        r1.addWidget(tit)
        r1.addStretch()
        r1.addWidget(lbl_d)
        lay.addLayout(r1)

        # Row 2: Files
        f_s = entry.get('nama_file_simpanan', '')
        f_p = entry.get('nama_file_pinjaman', '')
        lbl_f = QLabel(f"SSA Simpanan: {f_s} | Pinjaman: {f_p}")
        lbl_f.setStyleSheet("font-size: 13px; color: #64748B; border: none; margin-left: 26px;")
        lay.addWidget(lbl_f)

        # Row 3: Stats
        kc = entry.get('jumlah_kc', 0)
        sz = entry.get('ukuran_file', '0 KB')
        lbl_s = QLabel(f"{kc} KC diproses · {sz}")
        lbl_s.setStyleSheet("font-size: 13px; color: #64748B; border: none; margin-left: 26px;")
        lay.addWidget(lbl_s)

        # Row 4: Buttons
        r_btn = QHBoxLayout()
        
        btn_dl = QPushButton("📥 Download Ulang")
        btn_dl.setFixedHeight(32)
        btn_dl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_dl.setStyleSheet("""
            QPushButton { background: transparent; color: #16A34A; border: 1.5px solid #86EFAC; border-radius: 6px; padding: 0 16px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background: #F0FDF4; border-color: #16A34A; }
        """)
        btn_dl.clicked.connect(lambda _, x=eid: self._download(x))
        if not ok:
            btn_dl.hide()

        btn_rm = QPushButton("🗑️ Hapus")
        btn_rm.setFixedHeight(32)
        btn_rm.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_rm.setStyleSheet("""
            QPushButton { background: transparent; color: #DC2626; border: 1.5px solid #FCA5A5; border-radius: 6px; padding: 0 16px; font-weight: bold; font-size: 12px; }
            QPushButton:hover { background: #FEF2F2; border-color: #DC2626; }
        """)
        btn_rm.clicked.connect(lambda _, x=eid: self._confirm_delete(x))

        r_btn.addStretch()
        r_btn.addWidget(btn_dl)
        r_btn.addWidget(btn_rm)
        lay.addLayout(r_btn)

        return card

    def _download(self, eid: str):
        src = get_history_file_path(eid)
        if not src:
            ToastManager.show(self.window(), "File tidak ditemukan.", "error")
            return

        dest, _ = QFileDialog.getSaveFileName(self, "Simpan File Excel", src.name, "Excel Files (*.xlsx)")
        if not dest:
            return

        try:
            shutil.copy2(str(src), dest)
            ToastManager.show(self.window(), "File berhasil didownload", "success")
        except Exception as e:
            ToastManager.show(self.window(), f"Gagal mendownload: {e}", "error")

    def _confirm_delete(self, eid: str):
        reply = QMessageBox.question(self, "Konfirmasi Hapus", "Yakin ingin menghapus riwayat ini?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            delete_history(eid)
            self.refresh()
            ToastManager.show(self.window(), "Riwayat dihapus", "info")

    def _confirm_delete_all(self):
        reply = QMessageBox.question(self, "Konfirmasi Hapus Semua", "Yakin ingin menghapus SEMUA riwayat?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            cnt = delete_all_history()
            self.refresh()
            ToastManager.show(self.window(), f"{cnt} riwayat dihapus", "info")
