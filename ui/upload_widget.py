"""
upload_widget.py — Halaman Upload & Generate.
Drop zone multi-format, RKA opsional, dan tombol Generate besar.
"""
import os
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton, QFileDialog,
                               QGraphicsOpacityEffect, QScrollArea,
                               QProgressBar)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QCursor

from core.file_reader import get_file_info, FILTER_SSA, FILTER_RKA
from core.validator import validate_ssa_simpanan, validate_ssa_pinjaman, validate_rka
from core.processor import process_files, count_kc
from core.exporter import export_to_excel, get_file_size_str as exp_size
from core.history_manager import save_history, HISTORY_DIR
from ui.toast_notification import ToastManager
import pandas as pd
from core.file_reader import read_file


class FileCard(QFrame):
    """Kartu info file setelah dipilih."""
    remove_clicked = Signal(str)

    def __init__(self, file_type, file_path, size_str, valid, message=""):
        super().__init__()
        self.file_type = file_type
        self.setObjectName("cardFrame")
        self.setFixedHeight(72)

        color_ok = "#059669"
        color_err = "#DC2626"
        border_clr = color_ok if valid else color_err

        self.setStyleSheet(f"""
            QFrame#cardFrame {{
                background-color: #FFFFFF;
                border: 1.5px solid {border_clr};
                border-radius: 12px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)

        badge = QLabel("✓" if valid else "✕")
        badge.setFixedSize(32, 32)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bg = "#ECFDF5" if valid else "#FEF2F2"
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {border_clr};
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }}
        """)

        info = QVBoxLayout()
        info.setSpacing(1)
        lbl_name = QLabel(os.path.basename(file_path))
        lbl_name.setStyleSheet("font-weight: 600; font-size: 13px; color: #1E293B; border: none;")
        
        status_text = "Valid" if valid else f"Tidak Valid: {message}"
        lbl_status = QLabel(f"{size_str}  •  {status_text}")
        lbl_status.setStyleSheet(f"font-size: 11px; color: {border_clr}; border: none;")
        
        info.addWidget(lbl_name)
        info.addWidget(lbl_status)

        btn_x = QPushButton("✕")
        btn_x.setFixedSize(28, 28)
        btn_x.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_x.setStyleSheet("""
            QPushButton {
                background: #FEF2F2; color: #DC2626; border-radius: 14px; font-size: 12px; font-weight: bold; border: none;
            }
            QPushButton:hover { background: #FEE2E2; }
        """)
        btn_x.clicked.connect(lambda: self.remove_clicked.emit(self.file_type))

        lay.addWidget(badge)
        lay.addSpacing(12)
        lay.addLayout(info)
        lay.addStretch()
        lay.addWidget(btn_x)

        # Fade in
        eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(eff)
        eff.setOpacity(1)


class UploadArea(QFrame):
    """Drag & Drop area."""
    file_dropped = Signal(str)

    def __init__(self, title, accept_text, is_optional=False):
        super().__init__()
        self.setObjectName("uploadArea")
        self.setAcceptDrops(True)
        self.setMinimumHeight(120)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.is_optional = is_optional
        self.filter_str = FILTER_RKA if is_optional else FILTER_SSA

        border_clr = "#E2EAF4" if is_optional else "#CBD5E1"
        self.setStyleSheet(f"""
            QFrame#uploadArea {{
                background-color: #F8FAFC;
                border: 2px dashed {border_clr};
                border-radius: 12px;
            }}
            QFrame#uploadArea:hover {{ background-color: #EFF6FF; border-color: #93C5FD; }}
        """)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(4)

        ic = QLabel("↑")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 28px; color: #93C5FD; border: none; background: transparent;")

        lbl_t = QLabel(f"Drag & Drop file {title} di sini")
        lbl_t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_t.setStyleSheet("font-weight: 700; font-size: 14px; color: #1E293B; border: none; background: transparent;")

        lbl_s = QLabel(f"atau klik Browse ({accept_text})")
        lbl_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_s.setStyleSheet("font-size: 12px; color: #94A3B8; border: none; background: transparent;")

        btn = QPushButton("Browse File")
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setFixedHeight(34)
        btn.setStyleSheet("""
            QPushButton { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 16px; color: #1E293B; font-weight: bold; }
            QPushButton:hover { background: #F1F5F9; }
        """)
        btn.clicked.connect(self._browse)

        lay.addWidget(ic)
        lay.addWidget(lbl_t)
        lay.addWidget(lbl_s)
        lay.addSpacing(6)
        lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.setStyleSheet("QFrame#uploadArea { background: #EFF6FF; border: 2px solid #2563EB; border-radius: 14px; }")
            event.accept()
            return
        event.ignore()

    def dragLeaveEvent(self, event):
        border_clr = "#E2EAF4" if self.is_optional else "#CBD5E1"
        self.setStyleSheet(f"QFrame#uploadArea {{ background-color: #F8FAFC; border: 2px dashed {border_clr}; border-radius: 12px; }}")

    def dropEvent(self, event):
        self.dragLeaveEvent(event)
        if event.mimeData().hasUrls():
            self.file_dropped.emit(event.mimeData().urls()[0].toLocalFile())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._browse()
        super().mousePressEvent(event)

    def _browse(self):
        path, _ = QFileDialog.getOpenFileName(self, "Pilih File", "", self.filter_str)
        if path:
            self.file_dropped.emit(path)


class GenerateWorker(QThread):
    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, path_s, path_p, path_r):
        super().__init__()
        self.path_s = path_s
        self.path_p = path_p
        self.path_r = path_r

    def run(self):
        try:
            result = process_files(
                self.path_s, self.path_p, self.path_r,
                callback=lambda pct, msg: self.progress.emit(pct, msg)
            )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class UploadWidget(QWidget):
    generate_finished = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._paths = {}
        self._cards = {}
        self._areas = {}
        self._worker = None
        self._valid_status = {"simpanan": False, "pinjaman": False, "rka": False}
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
        self._main_lay.setSpacing(20)

        # Header
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        lbl_t = QLabel("Upload & Generate")
        lbl_t.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F2A4A;")
        lbl_s = QLabel("Unggah file data dan jalankan proses konsolidasi dashboard")
        lbl_s.setStyleSheet("font-size: 13px; color: #94A3B8;")
        hdr.addWidget(lbl_t)
        hdr.addWidget(lbl_s)
        self._main_lay.addLayout(hdr)

        # Sections
        sections = [
            ("simpanan", "SSA Simpanan", "CSV / XLSX", ".CSV, .XLSX, .XLS", "File data simpanan nasabah per cabang", False),
            ("pinjaman", "SSA Pinjaman", "CSV / XLSX", ".CSV, .XLSX, .XLS", "File data pinjaman & baki debet per cabang", False),
            ("rka", "Target RKA", "XLSX", ".XLSX, .XLS", "Jika tidak diupload, kolom target akan dikosongkan", True),
        ]

        for ftype, title, tag, ext, desc, opt in sections:
            section = self._make_section(ftype, title, tag, ext, desc, opt)
            self._main_lay.addWidget(section)

        # Generate Section
        self._build_generate_section()

        self._main_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

    def _make_section(self, ftype, title, tag, ext, desc, is_optional):
        outer = QFrame()
        outer.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 14px; border: 1px solid #E2EAF4; }")
        lay = QVBoxLayout(outer)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)

        hdr = QHBoxLayout()
        tag_lbl = QLabel(tag)
        tag_lbl.setFixedHeight(22)
        tag_bg = "#EFF6FF" if "CSV" in tag else "#F0FDF4"
        tag_clr = "#1D4ED8" if "CSV" in tag else "#059669"
        tag_lbl.setStyleSheet(f"QLabel {{ background-color: {tag_bg}; color: {tag_clr}; font-size: 10px; font-weight: bold; padding: 0 8px; border-radius: 4px; border: none; }}")
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #0F2A4A;")
        
        hdr.addWidget(tag_lbl)
        hdr.addSpacing(10)
        hdr.addWidget(lbl)
        
        if is_optional:
            opt_lbl = QLabel("(Opsional)")
            opt_lbl.setStyleSheet("font-size: 13px; color: #94A3B8; font-weight: bold;")
            hdr.addSpacing(6)
            hdr.addWidget(opt_lbl)

        hdr.addSpacing(8)
        lbl_d = QLabel(desc)
        lbl_d.setStyleSheet("font-size: 12px; color: #94A3B8;")
        hdr.addWidget(lbl_d)
        hdr.addStretch()
        lay.addLayout(hdr)

        area = UploadArea(title, ext, is_optional)
        area.file_dropped.connect(lambda p, t=ftype: self._on_file(t, p))
        self._areas[ftype] = area
        lay.addWidget(area)

        slot = QFrame()
        slot.setFixedHeight(0)
        setattr(self, f"_slot_{ftype}", slot)
        lay.addWidget(slot)

        return outer

    def _build_generate_section(self):
        gen_container = QWidget()
        lay = QVBoxLayout(gen_container)
        lay.setContentsMargins(0, 20, 0, 0)
        lay.setSpacing(12)

        # Status Indikator
        self.lbl_status_ind = QLabel("— SSA Simpanan   — SSA Pinjaman   — RKA")
        self.lbl_status_ind.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status_ind.setStyleSheet("font-size: 13px; font-weight: bold; color: #94A3B8;")
        lay.addWidget(self.lbl_status_ind)

        # Tombol Generate
        self.btn_generate = QPushButton("⚡  GENERATE DASHBOARD")
        self.btn_generate.setFixedHeight(52)
        self.btn_generate.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_generate.setEnabled(False)
        self.btn_generate.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: #FFFFFF; font-weight: bold; font-size: 16px; border-radius: 10px; border: none;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:disabled { background-color: #94A3B8; color: #F1F5F9; }
        """)
        self.btn_generate.clicked.connect(self._start_generate)
        lay.addWidget(self.btn_generate)

        # Progress
        self.prog_container = QWidget()
        self.prog_container.hide()
        pl = QVBoxLayout(self.prog_container)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(4)
        
        self.lbl_prog_msg = QLabel("Memulai...")
        self.lbl_prog_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_prog_msg.setStyleSheet("font-size: 13px; color: #1E293B; font-weight: bold;")
        
        self.prog_bar = QProgressBar()
        self.prog_bar.setFixedHeight(8)
        self.prog_bar.setTextVisible(False)
        self.prog_bar.setRange(0, 100)
        self.prog_bar.setStyleSheet("""
            QProgressBar { background-color: #E2EAF4; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #2563EB; border-radius: 4px; }
        """)
        
        pl.addWidget(self.lbl_prog_msg)
        pl.addWidget(self.prog_bar)
        lay.addWidget(self.prog_container)

        self._main_lay.addWidget(gen_container)

    def _update_status_indicator(self):
        s_ok = self._valid_status["simpanan"]
        p_ok = self._valid_status["pinjaman"]
        r_ok = self._valid_status["rka"]

        def icon(ok): return "✓" if ok else "—"
        def clr(ok): return "#059669" if ok else "#94A3B8"

        text = f"<span style='color: {clr(s_ok)}'>{icon(s_ok)} SSA Simpanan</span>   " \
               f"<span style='color: {clr(p_ok)}'>{icon(p_ok)} SSA Pinjaman</span>   " \
               f"<span style='color: {clr(r_ok)}'>{icon(r_ok)} RKA (Opsional)</span>"
        
        self.lbl_status_ind.setText(text)

        # Tombol aktif jika simpanan & pinjaman valid
        can_generate = s_ok and p_ok
        self.btn_generate.setEnabled(can_generate)

    def _on_file(self, ftype, path):
        info = get_file_info(path)
        valid = False
        msg = ""

        try:
            df = read_file(path, nrows=500)
            if ftype == "simpanan":
                res = validate_ssa_simpanan(df)
                valid, msg = res.valid, res.message
            elif ftype == "pinjaman":
                res = validate_ssa_pinjaman(df)
                valid, msg = res.valid, res.message
            else:
                res = validate_rka(df)
                valid, msg = res.valid, res.message
        except Exception as e:
            valid = False
            msg = str(e)

        old = self._cards.get(ftype)
        if old:
            old.setParent(None)
            old.deleteLater()

        card = FileCard(ftype, path, info["size_str"], valid, msg)
        card.remove_clicked.connect(self._on_remove)
        self._cards[ftype] = card

        slot = getattr(self, f"_slot_{ftype}")
        sl = slot.layout()
        if not sl:
            sl = QVBoxLayout(slot)
            sl.setContentsMargins(0, 0, 0, 0)
        sl.addWidget(card)
        slot.setFixedHeight(76)

        self._areas[ftype].hide()

        if valid:
            self._paths[ftype] = path
            self._valid_status[ftype] = True
        else:
            self._paths.pop(ftype, None)
            self._valid_status[ftype] = False
            ToastManager.show(self.window(), f"File tidak valid: {msg}", "error")

        self._update_status_indicator()

    def _on_remove(self, ftype):
        card = self._cards.pop(ftype, None)
        if card:
            card.setParent(None)
            card.deleteLater()

        self._paths.pop(ftype, None)
        self._valid_status[ftype] = False

        slot = getattr(self, f"_slot_{ftype}")
        slot.setFixedHeight(0)

        self._areas[ftype].show()
        self._update_status_indicator()

    def _start_generate(self):
        self.btn_generate.setEnabled(False)
        self.btn_generate.setText("⏳ Memproses...")
        self.prog_container.show()
        self.prog_bar.setValue(0)
        self.prog_bar.setStyleSheet("""
            QProgressBar { background-color: #E2EAF4; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #2563EB; border-radius: 4px; }
        """)

        path_rka = self._paths.get("rka")
        self._worker = GenerateWorker(
            self._paths["simpanan"],
            self._paths["pinjaman"],
            path_rka
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_gen_finished)
        self._worker.error.connect(self._on_gen_error)
        self._worker.start()

    def _on_progress(self, pct, msg):
        self.prog_bar.setValue(pct)
        self.lbl_prog_msg.setText(msg)

    def _on_gen_finished(self, data_dict):
        # Simpan Excel
        now = datetime.now()
        fname = f"Dashboard_AH_Gunsar_{now.strftime('%d_%b_%Y')}.xlsx"
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        output_path = HISTORY_DIR / fname
        tanggal_data = now.strftime("%d %B %Y")

        try:
            export_to_excel(data_dict, str(output_path), tanggal_data)
            meta = {
                "tanggal_proses": now.strftime("%Y-%m-%d %H:%M:%S"),
                "tanggal_data": tanggal_data,
                "nama_file_simpanan": os.path.basename(self._paths.get("simpanan", "")),
                "nama_file_pinjaman": os.path.basename(self._paths.get("pinjaman", "")),
                "nama_file_rka": os.path.basename(self._paths.get("rka", "")) if "rka" in self._paths else "-",
                "jumlah_kc": count_kc(data_dict),
                "output_path": str(output_path),
                "ukuran_file": exp_size(str(output_path)),
                "status": "sukses",
            }
            save_history(meta)
            
            self.prog_bar.setValue(100)
            self.lbl_prog_msg.setText("✅ Selesai!")
            ToastManager.show(self.window(), "Generate Dashboard Berhasil!", "success")
            
            # Reset button state
            self.btn_generate.setText("⚡  GENERATE DASHBOARD")
            self.btn_generate.setEnabled(True)
            
            QTimer.singleShot(1500, lambda: self.generate_finished.emit(data_dict))

        except Exception as e:
            self._on_gen_error(str(e))

    def _on_gen_error(self, msg):
        self.prog_bar.setStyleSheet("""
            QProgressBar { background-color: #E2EAF4; border-radius: 4px; border: none; }
            QProgressBar::chunk { background-color: #DC2626; border-radius: 4px; }
        """)
        self.lbl_prog_msg.setText(f"Error: {msg}")
        self.btn_generate.setText("Coba Lagi")
        self.btn_generate.setEnabled(True)
        ToastManager.show(self.window(), f"Proses Gagal: {msg}", "error")

    def get_file_count(self) -> int:
        return sum(1 for v in self._valid_status.values() if v)
