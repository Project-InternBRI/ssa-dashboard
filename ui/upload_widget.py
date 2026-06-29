"""
upload_widget.py — Halaman Upload & Generate.

DropZone bergaya: dashed blue border, circular upload icon, teks biru klikable.
Tanpa input URL. FileStatusCard bersih tanpa border.
Tombol Generate solid color.
"""
import os
import time
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QPushButton, QFileDialog,
    QScrollArea, QProgressBar, QSizePolicy,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QObject
from PySide6.QtGui import QCursor, QColor, QFont

from core.file_reader import get_file_info, FILTER_SSA
from core.validator import validate_ssa_simpanan, validate_ssa_pinjaman
from core.processor import process_files, count_kc
from core.exporter import export_to_excel, get_file_size_str
from core.history_manager import save_history, HISTORY_DIR
from core.file_reader import read_file
from ui.toast_notification import ToastManager


# ────────────────────────────────────────────────────────────────────
# WORKER THREAD
# ────────────────────────────────────────────────────────────────────
class GenerateWorker(QObject):
    progress = Signal(int, str)
    finished = Signal(dict, float)
    error    = Signal(str)

    def __init__(self, path_s, path_p,
                 hist_s: list[str], hist_p: list[str]):
        super().__init__()
        self.path_s = path_s
        self.path_p = path_p
        self.hist_s = hist_s
        self.hist_p = hist_p

    def run(self):
        t0 = time.time()
        try:
            result = process_files(
                self.path_s, self.path_p,
                path_simpanan_historis=self.hist_s,
                path_pinjaman_historis=self.hist_p,
                callback=lambda pct, msg: self.progress.emit(pct, msg),
            )
            self.finished.emit(result, time.time() - t0)
        except Exception as e:
            self.error.emit(str(e))



# ────────────────────────────────────────────────────────────────────
# DROP ZONE — New Design (referensi: dashed border, circle upload icon)
# ────────────────────────────────────────────────────────────────────
class DropZone(QFrame):
    """Drop zone bergaya modern: dashed blue border, circular icon, blue text link."""
    file_selected = Signal(str)
    files_selected = Signal(list)

    def __init__(self, label: str, desc: str = "", multiple: bool = False, parent=None):
        super().__init__(parent)
        self._label = label
        self._multiple = multiple
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(160)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._set_idle_style()

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(10)
        lay.setContentsMargins(20, 24, 20, 24)

        # Circle icon (lingkaran biru dengan panah putih)
        self._icon_frame = QLabel()
        self._icon_frame.setFixedSize(52, 52)
        self._icon_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_frame.setText("↑")
        self._icon_frame.setStyleSheet("""
            QLabel {
                background-color: #2563EB;
                color: white;
                border-radius: 26px;
                font-size: 22px;
                font-weight: bold;
            }
        """)

        # Teks biru klikable
        self._lbl_main = QLabel(f"Pilih file {label}")
        self._lbl_main.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_main.setStyleSheet(
            "color: #2563EB; font-size: 13px; font-weight: 600;"
            "background: transparent;")

        # Teks abu
        lbl_sub = QLabel("atau drag & drop file di sini")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(
            "color: #94A3B8; font-size: 12px; background: transparent;")

        # Format yang diterima
        lbl_fmt = QLabel("CSV · XLSX · XLS")
        lbl_fmt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_fmt.setStyleSheet(
            "color: #CBD5E1; font-size: 10px; font-weight: 500;"
            "background: transparent; letter-spacing: 1px;")

        lay.addWidget(self._icon_frame, alignment=Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(self._lbl_main)
        lay.addWidget(lbl_sub)
        lay.addWidget(lbl_fmt)

    def _set_idle_style(self):
        self.setStyleSheet("""
            QFrame#dropZone {
                background-color: #FAFBFF;
                border: 2px dashed #93C5FD;
                border-radius: 12px;
            }
            QFrame#dropZone:hover {
                background-color: #EFF6FF;
                border-color: #2563EB;
            }
        """)

    def _set_drag_style(self):
        self.setStyleSheet("""
            QFrame#dropZone {
                background-color: #EFF6FF;
                border: 2px dashed #2563EB;
                border-radius: 12px;
            }
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._set_drag_style()
            event.accept()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._set_idle_style()

    def dropEvent(self, event):
        self._set_idle_style()
        if event.mimeData().hasUrls():
            if self._multiple:
                paths = [u.toLocalFile() for u in event.mimeData().urls()]
                self.files_selected.emit(paths)
            else:
                self.file_selected.emit(event.mimeData().urls()[0].toLocalFile())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse()
        super().mousePressEvent(event)

    def _browse(self):
        if self._multiple:
            paths, _ = QFileDialog.getOpenFileNames(
                self, f"Pilih File {self._label}", "", FILTER_SSA)
            if paths:
                self.files_selected.emit(paths)
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, f"Pilih File {self._label}", "", FILTER_SSA)
            if path:
                self.file_selected.emit(path)


# ────────────────────────────────────────────────────────────────────
# FILE STATUS CARD
# ────────────────────────────────────────────────────────────────────
class FileStatusCard(QFrame):
    remove_clicked = Signal()

    def __init__(self, path: str, size_str: str,
                 valid: bool, msg: str = "", btn_text: str = "Ganti File", parent=None):
        super().__init__(parent)
        self.setFixedHeight(64)
        clr_bg  = "#F0FDF4" if valid else "#FFF1F2"
        clr_dot = "#10B981" if valid else "#EF4444"
        clr_txt = "#059669" if valid else "#DC2626"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: {clr_bg};
                border-radius: 10px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(12)

        # Dot status
        dot = QLabel()
        dot.setFixedSize(10, 10)
        dot.setStyleSheet(
            f"background: {clr_dot}; border-radius: 5px;")

        # Teks file
        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        nm = QLabel(os.path.basename(path))
        nm.setStyleSheet(
            f"font-weight: 600; font-size: 13px; color: #0F172A; background: transparent;")
        nm.setMaximumWidth(320)
        st_text = f"{size_str}  ·  Valid" if valid else f"{size_str}  ·  {msg[:50]}"
        st = QLabel(st_text)
        st.setStyleSheet(
            f"font-size: 11px; color: {clr_txt}; background: transparent;")
        info_col.addWidget(nm)
        info_col.addWidget(st)

        # Tombol Action
        btn_x = QPushButton(btn_text)
        btn_x.setFixedHeight(28)
        btn_x.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_x.setStyleSheet("""
            QPushButton {
                background: #F1F5F9;
                color: #475569;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: #E2E8F0;
                color: #0F172A;
            }
        """)
        btn_x.clicked.connect(self.remove_clicked.emit)

        lay.addWidget(dot, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addLayout(info_col)
        lay.addStretch()
        lay.addWidget(btn_x)


# ────────────────────────────────────────────────────────────────────
# SECTION CARD WRAPPER
# ────────────────────────────────────────────────────────────────────
def make_section_card() -> tuple[QFrame, QVBoxLayout]:
    """Card putih tanpa border dengan shadow halus."""
    card = QFrame()
    card.setStyleSheet("""
        QFrame {
            background-color: #FFFFFF;
            border-radius: 16px;
        }
    """)
    shadow = QGraphicsDropShadowEffect(card)
    shadow.setBlurRadius(20)
    shadow.setColor(QColor(0, 0, 0, 12))
    shadow.setOffset(0, 4)
    card.setGraphicsEffect(shadow)

    lay = QVBoxLayout(card)
    lay.setContentsMargins(24, 20, 24, 24)
    lay.setSpacing(16)
    return card, lay


# ────────────────────────────────────────────────────────────────────
# UPLOAD WIDGET UTAMA
# ────────────────────────────────────────────────────────────────────
class UploadWidget(QWidget):
    generate_finished = Signal(dict, float)
    data_cleared      = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._path_s_berjalan: str | None = None
        self._path_p_berjalan: str | None = None
        self._hist_s: list[str] = []
        self._hist_p: list[str] = []

        self._is_generating = False
        self._worker: GenerateWorker | None = None
        self._thread: QThread | None = None
        self._start_time: float = 0.0
        self._last_data_dict: dict | None = None

        self._build_ui()

    # ── BUILD UI ──────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #F1F5F9; }")

        content = QWidget()
        content.setStyleSheet("background: #F1F5F9;")
        self._lay = QVBoxLayout(content)
        self._lay.setContentsMargins(32, 28, 32, 48)
        self._lay.setSpacing(20)

        self._lay.addWidget(self._build_section1())
        self._lay.addWidget(self._build_section2())
        self._lay.addWidget(self._build_generate_area())
        self._lay.addStretch()

        scroll.setWidget(content)
        root.addWidget(scroll)

    # ── SECTION 1: File Periode Berjalan ──────────────────────────
    def _build_section1(self) -> QFrame:
        card, lay = make_section_card()

        # Header section
        hdr = QHBoxLayout()
        title = QLabel("File Periode Berjalan")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #0F172A;")

        badge_req = QLabel("Wajib")
        badge_req.setStyleSheet("""
            background-color: #FEE2E2;
            color: #DC2626;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 10px;
        """)

        self._lbl_s1_counter = QLabel("0 / 2 file")
        self._lbl_s1_counter.setStyleSheet(
            "font-size: 12px; color: #94A3B8; font-weight: 600;")

        hdr.addWidget(title)
        hdr.addSpacing(10)
        hdr.addWidget(badge_req, 0, Qt.AlignmentFlag.AlignVCenter)
        hdr.addStretch()
        hdr.addWidget(self._lbl_s1_counter)
        lay.addLayout(hdr)

        sub = QLabel(
            "Upload SSA Simpanan & SSA Pinjaman untuk periode aktif yang akan diproses.")
        sub.setStyleSheet("font-size: 12px; color: #64748B;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        # 2 kolom drop zone
        zones_row = QHBoxLayout()
        zones_row.setSpacing(16)

        # Kolom SSA Simpanan
        col_s = QVBoxLayout()
        col_s.setSpacing(8)
        lbl_s = QLabel("SSA Simpanan")
        lbl_s.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569;")
        col_s.addWidget(lbl_s)

        self._zone_s = DropZone("SSA Simpanan")
        self._zone_s.file_selected.connect(
            lambda p: self._on_file_berjalan("s", p))
        col_s.addWidget(self._zone_s)

        self._card_s_wrap = QWidget()
        self._card_s_wrap.setStyleSheet("background: transparent;")
        self._card_s_lay = QVBoxLayout(self._card_s_wrap)
        self._card_s_lay.setContentsMargins(0, 0, 0, 0)
        self._card_s_lay.setSpacing(4)
        col_s.addWidget(self._card_s_wrap)

        # Kolom SSA Pinjaman
        col_p = QVBoxLayout()
        col_p.setSpacing(8)
        lbl_p = QLabel("SSA Pinjaman")
        lbl_p.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569;")
        col_p.addWidget(lbl_p)

        self._zone_p = DropZone("SSA Pinjaman")
        self._zone_p.file_selected.connect(
            lambda p: self._on_file_berjalan("p", p))
        col_p.addWidget(self._zone_p)

        self._card_p_wrap = QWidget()
        self._card_p_wrap.setStyleSheet("background: transparent;")
        self._card_p_lay = QVBoxLayout(self._card_p_wrap)
        self._card_p_lay.setContentsMargins(0, 0, 0, 0)
        self._card_p_lay.setSpacing(4)
        col_p.addWidget(self._card_p_wrap)

        zones_row.addLayout(col_s)
        zones_row.addLayout(col_p)
        lay.addLayout(zones_row)

        return card

    # ── SECTION 2: File Historis (Opsional) ───────────────────────
    def _build_section2(self) -> QFrame:
        card, lay = make_section_card()

        hdr = QHBoxLayout()
        title = QLabel("File Periode Sebelumnya")
        title.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #0F172A;")

        badge_opt = QLabel("Opsional")
        badge_opt.setStyleSheet("""
            background-color: #F1F5F9;
            color: #64748B;
            font-size: 10px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 10px;
        """)

        self._lbl_s2_counter = QLabel("0 file")
        self._lbl_s2_counter.setStyleSheet(
            "font-size: 12px; color: #94A3B8; font-weight: 600;")

        hdr.addWidget(title)
        hdr.addSpacing(10)
        hdr.addWidget(badge_opt, 0, Qt.AlignmentFlag.AlignVCenter)
        hdr.addStretch()
        hdr.addWidget(self._lbl_s2_counter)
        lay.addLayout(hdr)

        sub = QLabel(
            "Tambahkan file historis untuk mengisi kolom Posisi dan menghitung Growth (MTD/DTD/YOY/YTD).")
        sub.setStyleSheet("font-size: 12px; color: #64748B;")
        sub.setWordWrap(True)
        lay.addWidget(sub)

        cols = QHBoxLayout()
        cols.setSpacing(16)

        # Historis Simpanan
        col_hs = QVBoxLayout()
        col_hs.setSpacing(8)
        lbl_hs = QLabel("SSA Simpanan — Historis")
        lbl_hs.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569;")
        col_hs.addWidget(lbl_hs)

        self._chips_s_wrap = QWidget()
        self._chips_s_wrap.setStyleSheet("background: transparent;")
        self._chips_s_lay = QVBoxLayout(self._chips_s_wrap)
        self._chips_s_lay.setContentsMargins(0, 0, 0, 0)
        self._chips_s_lay.setSpacing(4)
        col_hs.addWidget(self._chips_s_wrap)

        self._zone_hs = DropZone("Simpanan (Historis)", multiple=True)
        self._zone_hs.files_selected.connect(lambda paths: self._add_historis_files("s", paths))
        col_hs.addWidget(self._zone_hs)

        # Historis Pinjaman
        col_hp = QVBoxLayout()
        col_hp.setSpacing(8)
        lbl_hp = QLabel("SSA Pinjaman — Historis")
        lbl_hp.setStyleSheet(
            "font-size: 12px; font-weight: 600; color: #475569;")
        col_hp.addWidget(lbl_hp)

        self._chips_p_wrap = QWidget()
        self._chips_p_wrap.setStyleSheet("background: transparent;")
        self._chips_p_lay = QVBoxLayout(self._chips_p_wrap)
        self._chips_p_lay.setContentsMargins(0, 0, 0, 0)
        self._chips_p_lay.setSpacing(4)
        col_hp.addWidget(self._chips_p_wrap)

        self._zone_hp = DropZone("Pinjaman (Historis)", multiple=True)
        self._zone_hp.files_selected.connect(lambda paths: self._add_historis_files("p", paths))
        col_hp.addWidget(self._zone_hp)

        cols.addLayout(col_hs)
        cols.addLayout(col_hp)
        lay.addLayout(cols)

        return card

    # ── GENERATE AREA ─────────────────────────────────────────────
    def _build_generate_area(self) -> QWidget:
        card, lay = make_section_card()
        lay.setSpacing(12)

        # Status indikator
        self._lbl_status = QLabel(
            "SSA Simpanan: belum diupload  ·  SSA Pinjaman: belum diupload")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setStyleSheet(
            "font-size: 12px; color: #94A3B8;")
        lay.addWidget(self._lbl_status)

        # Row untuk tombol action
        r_action = QHBoxLayout()
        r_action.setSpacing(12)

        self._btn_clear = QPushButton("Bersihkan")
        self._btn_clear.setFixedHeight(50)
        self._btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9; color: #64748B;
                font-weight: 700; font-size: 15px; border-radius: 12px;
            }
            QPushButton:hover { background-color: #E2E8F0; color: #0F172A; }
        """)
        self._btn_clear.clicked.connect(self._clear_all_submission)
        r_action.addWidget(self._btn_clear, 1)

        # Tombol Generate — solid, 48px
        self._btn_gen = QPushButton("Generate Dashboard")
        self._btn_gen.setFixedHeight(50)
        self._btn_gen.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_gen.setEnabled(False)
        self._btn_gen.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 15px;
                border-radius: 12px;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
            QPushButton:disabled {
                background-color: #E2E8F0;
                color: #94A3B8;
            }
        """)
        self._btn_gen.clicked.connect(self._start_generate)
        r_action.addWidget(self._btn_gen, 3)
        
        lay.addLayout(r_action)

        # Info teks
        self._lbl_info = QLabel("Lengkapi file periode berjalan terlebih dahulu.")
        self._lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_info.setStyleSheet("font-size: 11px; color: #94A3B8;")
        lay.addWidget(self._lbl_info)

        # Progress (tersembunyi)
        self._prog_widget = QWidget()
        self._prog_widget.setStyleSheet("background: transparent;")
        self._prog_widget.hide()
        pl = QVBoxLayout(self._prog_widget)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)

        self._lbl_prog_msg = QLabel("Memulai...")
        self._lbl_prog_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_prog_msg.setStyleSheet(
            "font-size: 13px; color: #1E293B; font-weight: 600;")

        self._prog_bar = QProgressBar()
        self._prog_bar.setFixedHeight(6)
        self._prog_bar.setTextVisible(False)
        self._prog_bar.setRange(0, 100)
        self._prog_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E2E8F0;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2563EB, stop:1 #60A5FA);
                border-radius: 3px;
            }
        """)
        pl.addWidget(self._lbl_prog_msg)
        pl.addWidget(self._prog_bar)
        lay.addWidget(self._prog_widget)

        return card

    def _clear_all_submission(self):
        self._path_s_berjalan = None
        self._path_p_berjalan = None
        self._hist_s.clear()
        self._hist_p.clear()
        
        self._clear_layout(self._card_s_lay)
        self._clear_layout(self._card_p_lay)
        self._zone_s.show()
        self._zone_p.show()
        
        self._rebuild_chips("s")
        self._rebuild_chips("p")
        
        # Reset progress bar
        self._prog_bar.setValue(0)
        self._lbl_prog_msg.setText("")
        self._prog_widget.hide()
        
        self._update_ui()
        self.data_cleared.emit()

    # ── FILE HANDLING ──────────────────────────────────────────────
    def _on_file_berjalan(self, ftype: str, path: str):
        info = get_file_info(path)
        valid = False
        msg   = ""

        try:
            df = read_file(path, nrows=200)
            if ftype == "s":
                r = validate_ssa_simpanan(df)
            else:
                r = validate_ssa_pinjaman(df)
            valid, msg = r.valid, r.message
        except Exception as e:
            valid = False
            msg   = str(e)

        if ftype == "s":
            self._clear_layout(self._card_s_lay)
            if valid:
                self._path_s_berjalan = path
                self._zone_s.hide()
            else:
                self._path_s_berjalan = None
                self._zone_s.show()
        else:
            self._clear_layout(self._card_p_lay)
            if valid:
                self._path_p_berjalan = path
                self._zone_p.hide()
            else:
                self._path_p_berjalan = None
                self._zone_p.show()

        card = FileStatusCard(path, info["size_str"], valid, msg)
        card.remove_clicked.connect(lambda t=ftype: self._remove_berjalan(t))

        if ftype == "s":
            self._card_s_lay.addWidget(card)
        else:
            self._card_p_lay.addWidget(card)

        if not valid:
            ToastManager.show(
                self.window(), f"File tidak valid: {msg[:100]}", "error")

        self._update_ui()

    def _remove_berjalan(self, ftype: str):
        if ftype == "s":
            self._path_s_berjalan = None
            self._clear_layout(self._card_s_lay)
            self._zone_s.show()
        else:
            self._path_p_berjalan = None
            self._clear_layout(self._card_p_lay)
            self._zone_p.show()
        self.data_cleared.emit()
        self._update_ui()

    def _add_historis_files(self, ftype: str, paths: list[str]):
        for path in paths:
            if ftype == "s":
                if path not in self._hist_s:
                    self._hist_s.append(path)
                    self._add_hist_card("s", path)
            else:
                if path not in self._hist_p:
                    self._hist_p.append(path)
                    self._add_hist_card("p", path)
        self._update_hist_counter()
        self._update_ui()

    def _add_hist_card(self, ftype: str, path: str):
        info = get_file_info(path)
        card = FileStatusCard(path, info["size_str"], True, btn_text="Hapus File")
        card.remove_clicked.connect(
            lambda p=path, t=ftype: self._remove_chip(t, p))
        if ftype == "s":
            self._chips_s_lay.addWidget(card)
        else:
            self._chips_p_lay.addWidget(card)

    def _remove_chip(self, ftype: str, path: str):
        if ftype == "s":
            self._hist_s = [p for p in self._hist_s if p != path]
            self._rebuild_chips("s")
        else:
            self._hist_p = [p for p in self._hist_p if p != path]
            self._rebuild_chips("p")
        self._update_hist_counter()
        self._update_ui()

    def _rebuild_chips(self, ftype: str):
        lay = self._chips_s_lay if ftype == "s" else self._chips_p_lay
        lst = self._hist_s if ftype == "s" else self._hist_p
        self._clear_layout(lay)
        for path in lst:
            self._add_hist_card(ftype, path)

    # ── STATUS UPDATE ──────────────────────────────────────────────
    def _update_ui(self):
        s_ok = self._path_s_berjalan is not None
        p_ok = self._path_p_berjalan is not None
        count = int(s_ok) + int(p_ok)

        if self._hist_s:
            self._zone_hs.hide()
        else:
            self._zone_hs.show()
            
        if self._hist_p:
            self._zone_hp.hide()
        else:
            self._zone_hp.show()

        self._lbl_s1_counter.setText(f"{count} / 2 file")
        self._lbl_s1_counter.setStyleSheet(
            f"font-size: 12px; font-weight: 600; "
            f"color: {'#10B981' if count == 2 else '#94A3B8'};")

        def badge(ok): return "Siap" if ok else "Belum"
        self._lbl_status.setText(
            f"Simpanan: {badge(s_ok)}  ·  Pinjaman: {badge(p_ok)}"
            + (f"  ·  {len(self._hist_s)+len(self._hist_p)} file historis"
               if (self._hist_s or self._hist_p) else ""))

        can_gen = s_ok and p_ok and not self._is_generating
        self._btn_gen.setEnabled(can_gen)

        if can_gen:
            self._lbl_info.setText(
                "Siap. Tambahkan file historis untuk kolom Growth (opsional).")
        elif self._is_generating:
            self._lbl_info.setText("Proses sedang berjalan...")
        else:
            self._lbl_info.setText(
                "Lengkapi file SSA Simpanan & Pinjaman terlebih dahulu.")

    def _update_hist_counter(self):
        tot = len(self._hist_s) + len(self._hist_p)
        self._lbl_s2_counter.setText(f"{tot} file")

    # ── GENERATE ──────────────────────────────────────────────────
    def _start_generate(self):
        if self._is_generating:
            ToastManager.show(
                self.window(), "Proses generate sedang berjalan.", "warning")
            return

        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(3000)

        self._is_generating = True
        self._start_time    = time.time()
        self._btn_gen.setEnabled(False)
        self._btn_gen.setText("Memproses...")
        self._prog_widget.show()
        self._prog_bar.setValue(0)

        self._worker = GenerateWorker(
            self._path_s_berjalan, self._path_p_berjalan,
            list(self._hist_s), list(self._hist_p))
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_gen_done)
        self._worker.error.connect(self._on_gen_error)
        self._thread.started.connect(self._worker.run)
        self._thread.start()
        self._update_ui()

    def _on_progress(self, pct: int, msg: str):
        self._prog_bar.setValue(pct)
        self._lbl_prog_msg.setText(msg)

    def _on_gen_done(self, result: dict, elapsed: float):
        self._is_generating = False
        self._thread.quit()
        self._thread.wait()
        self._last_data_dict = result

        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        fname = f"Dashboard_AH_Gunsar_{datetime.now().strftime('%d_%b_%Y')}.xlsx"
        out   = HISTORY_DIR / fname

        try:
            export_to_excel(result, str(out))
            
            latest_period = ""
            if result:
                p_list = list(result.values())[0].get("periode_list", [])
                if p_list:
                    latest_period = p_list[-1]
            if not latest_period:
                latest_period = datetime.now().strftime("%Y-%m-%d")
                
            meta = {
                "tanggal_proses":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tanggal_data":       latest_period,
                "nama_file_simpanan": os.path.basename(self._path_s_berjalan or ""),
                "nama_file_pinjaman": os.path.basename(self._path_p_berjalan or ""),
                "jumlah_kc":          count_kc(result),
                "jumlah_periode":     len(
                    list(result.values())[0].get("periode_list", [])
                ) if result else 0,
                "has_historis":       bool(self._hist_s or self._hist_p),
                "list_kc":            [k for k in result
                                       if k not in ("Total AH Gunsar", "__stats__")],
                "output_path":        str(out),
                "ukuran_file":        get_file_size_str(str(out)),
                "waktu_proses":       f"{elapsed:.1f}s",
                "status":             "sukses",
            }
            save_history(meta)
        except Exception as e:
            ToastManager.show(
                self.window(), f"Gagal simpan Excel: {e}", "warning")

        self._btn_gen.setText("Generate Dashboard")
        self._prog_bar.setValue(100)
        self._lbl_prog_msg.setText("Selesai!")
        self._update_ui()
        self.generate_finished.emit(result, elapsed)

    def _on_gen_error(self, msg: str):
        self._is_generating = False
        self._thread.quit()
        self._thread.wait()

        self._prog_bar.setStyleSheet("""
            QProgressBar { background-color: #FEE2E2; border-radius: 3px; }
            QProgressBar::chunk { background: #EF4444; border-radius: 3px; }
        """)
        self._lbl_prog_msg.setText(f"Gagal: {msg}")
        self._btn_gen.setText("Coba Lagi")
        self._update_ui()
        ToastManager.show(self.window(), f"Proses Gagal: {msg[:120]}", "error")

    # ── HELPERS ───────────────────────────────────────────────────
    @staticmethod
    def _clear_layout(lay):
        while lay.count():
            item = lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def get_file_count(self) -> int:
        return (int(bool(self._path_s_berjalan)) +
                int(bool(self._path_p_berjalan)) +
                len(self._hist_s) + len(self._hist_p))
