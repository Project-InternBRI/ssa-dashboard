"""
preview_table.py — Halaman Preview Tabel.
Menampilkan hasil generate, dengan search, filter segmen, dan fitur Export.
"""
import os
import subprocess
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QPushButton, QTableWidget, QComboBox,
                               QTableWidgetItem, QHeaderView, QLineEdit,
                               QTabBar, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QCursor, QColor, QFont, QIcon

from core.exporter import export_to_excel
from ui.toast_notification import ToastManager


SHEET_ORDER = ["Tabungan", "Giro", "Deposito", "CASA", "Total DPK", "Pinjaman"]
SUBTOTAL_KEYS = ["subtotal", "sub total"]
TOTAL_KEYS    = ["total keseluruhan", "grand total", "total dpk"]


class ExportWorker(QThread):
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, data_dict, output_path, tanggal_data):
        super().__init__()
        self.data_dict = data_dict
        self.output_path = output_path
        self.tanggal_data = tanggal_data

    def run(self):
        try:
            export_to_excel(self.data_dict, self.output_path, self.tanggal_data)
            self.finished.emit(self.output_path)
        except Exception as e:
            self.error.emit(str(e))


class PreviewTableWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_dict = {}
        self._current_sheet = None
        self._export_worker = None
        self.init_ui()

    def init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._container = QWidget()
        self._container.setStyleSheet("background: #F8FAFC;")
        main_lay = QVBoxLayout(self._container)
        main_lay.setContentsMargins(32, 28, 32, 24)
        main_lay.setSpacing(16)

        # 1. TOOLBAR ATAS
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)
        
        self._search = QLineEdit()
        self._search.setPlaceholderText("Cari nama KC...")
        self._search.setFixedHeight(40)
        self._search.setMinimumWidth(250)
        self._search.textChanged.connect(self._filter_table)
        self._search.setStyleSheet("""
            QLineEdit { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 12px; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #2563EB; }
        """)

        self._combo_filter = QComboBox()
        self._combo_filter.addItems(["Semua Segmen"])
        self._combo_filter.setFixedHeight(40)
        self._combo_filter.setMinimumWidth(150)
        self._combo_filter.setStyleSheet("""
            QComboBox { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 12px; font-size: 13px; }
        """)

        self._btn_gen_ulang = QPushButton("🔄 Generate Ulang")
        self._btn_gen_ulang.setFixedHeight(40)
        self._btn_gen_ulang.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_gen_ulang.setStyleSheet("""
            QPushButton { background: transparent; color: #2563EB; border: 1px solid #2563EB; border-radius: 6px; padding: 0 16px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #EFF6FF; }
        """)
        self._btn_gen_ulang.clicked.connect(lambda: self.navigate_to.emit(2))

        self._btn_export = QPushButton("📥 Export Excel")
        self._btn_export.setFixedHeight(40)
        self._btn_export.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._btn_export.setEnabled(False) # Disabled by default
        self._btn_export.setStyleSheet("""
            QPushButton { background: #16A34A; color: #FFFFFF; border: none; border-radius: 6px; padding: 0 20px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #15803D; }
            QPushButton:disabled { background: #94A3B8; color: #F1F5F9; }
        """)
        self._btn_export.clicked.connect(self._start_export)

        toolbar.addWidget(self._search)
        toolbar.addWidget(self._combo_filter)
        toolbar.addStretch()
        toolbar.addWidget(self._btn_gen_ulang)
        toolbar.addWidget(self._btn_export)
        
        main_lay.addLayout(toolbar)

        # 2. TAB SHEET
        self._tab_bar = QTabBar()
        self._tab_bar.setStyleSheet("""
            QTabBar::tab {
                padding: 10px 20px; font-size: 14px; font-weight: 500; color: #64748B; border: none; border-bottom: 3px solid transparent; background: transparent;
            }
            QTabBar::tab:selected {
                color: #2563EB; font-weight: 700; border-bottom: 3px solid #2563EB;
            }
            QTabBar::tab:hover:!selected { color: #1E293B; }
        """)
        self._tab_bar.currentChanged.connect(self._on_tab_changed)
        main_lay.addWidget(self._tab_bar)

        # 3. TABEL DATA
        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet("""
            QTableWidget {
                background: #FFFFFF; border: 1px solid #E2EAF4; border-radius: 8px; gridline-color: #E2EAF4; alternate-background-color: #F8FAFC;
            }
            QTableWidget::item:hover { background-color: #EFF6FF; }
            QHeaderView::section {
                background-color: #1E3A5F; color: #FFFFFF; font-weight: bold; border: none; border-right: 1px solid #334155; padding: 8px;
            }
        """)
        main_lay.addWidget(self._table, 1)

        # 4. EMPTY STATE
        self._empty = QWidget()
        self._empty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(self._empty)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(12)

        ic = QLabel("⊞")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 64px; color: #CBD5E1; border: none;")
        t1 = QLabel("Belum Ada Data untuk Ditampilkan")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        t2 = QLabel("Upload file SSA dan jalankan Generate terlebih dahulu")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size: 14px; color: #64748B;")
        
        btn_up = QPushButton("Mulai Upload & Generate")
        btn_up.setFixedHeight(44)
        btn_up.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_up.setStyleSheet("""
            QPushButton { background: #2563EB; color: #FFFFFF; border-radius: 8px; font-weight: bold; font-size: 14px; padding: 0 24px; border: none; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn_up.clicked.connect(lambda: self.navigate_to.emit(2))

        el.addWidget(ic)
        el.addWidget(t1)
        el.addWidget(t2)
        el.addSpacing(16)
        el.addWidget(btn_up, alignment=Qt.AlignmentFlag.AlignCenter)

        main_lay.addWidget(self._empty)
        root.addWidget(self._container)

        self._empty_btn = btn_up  # For connection from main_window if needed

        self._show_empty_state()

    def load_data(self, data_dict: dict):
        self._data_dict = data_dict
        if not data_dict:
            self._show_empty_state()
            return

        self._show_table_state()

        while self._tab_bar.count():
            self._tab_bar.removeTab(0)

        for sheet in SHEET_ORDER:
            if sheet in data_dict and not data_dict[sheet].empty:
                df = data_dict[sheet]
                kc_count = len(df[df["KC"] != "TOTAL KESELURUHAN"]) if "KC" in df.columns else len(df)
                self._tab_bar.addTab(f"{sheet}  ({kc_count})")

        if self._tab_bar.count() > 0:
            self._tab_bar.setCurrentIndex(0)
            self._render_sheet(SHEET_ORDER[0])

    def _show_empty_state(self):
        self._table.hide()
        self._tab_bar.hide()
        self._search.setEnabled(False)
        self._combo_filter.setEnabled(False)
        self._btn_export.setEnabled(False)
        self._btn_export.setToolTip("Lakukan generate terlebih dahulu")
        self._empty.show()

    def _show_table_state(self):
        self._empty.hide()
        self._table.show()
        self._tab_bar.show()
        self._search.setEnabled(True)
        self._combo_filter.setEnabled(True)
        self._btn_export.setEnabled(True)
        self._btn_export.setToolTip("Export data ke Excel")

    def _on_tab_changed(self, index):
        if index < 0:
            return
        tab_text = self._tab_bar.tabText(index)
        sheet_name = tab_text.split("  (")[0].strip()
        self._render_sheet(sheet_name)

    def _render_sheet(self, sheet_name: str):
        if sheet_name not in self._data_dict:
            return

        self._current_sheet = sheet_name
        df = self._data_dict[sheet_name]
        cols = list(df.columns)

        self._table.clear()
        self._table.setRowCount(len(df))
        self._table.setColumnCount(len(cols))
        self._table.setHorizontalHeaderLabels(cols)

        header = self._table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 300)
        for i in range(1, len(cols)):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        for row_idx in range(len(df)):
            row_data = df.iloc[row_idx]
            kc_val = str(row_data.iloc[0]) if len(row_data) > 0 else ""
            kc_lower = kc_val.strip().lower()

            is_subtotal = any(k in kc_lower for k in SUBTOTAL_KEYS)
            is_total = any(k in kc_lower for k in TOTAL_KEYS)

            for col_idx, col_name in enumerate(cols):
                value = row_data[col_name]
                item = QTableWidgetItem()

                if col_idx == 0:
                    item.setText(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                else:
                    try:
                        num = float(value)
                        formatted = f"{num:,.0f}".replace(",", ".")
                        item.setText(formatted)
                        item.setData(Qt.ItemDataRole.UserRole, num)
                    except (ValueError, TypeError):
                        item.setText(str(value))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

                if is_total:
                    item.setBackground(QColor("#1E3A5F"))
                    item.setForeground(QColor("#FFFFFF"))
                    item.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                elif is_subtotal:
                    item.setBackground(QColor("#DBEAFE"))
                    item.setForeground(QColor("#1E293B"))
                    font = QFont("Arial", 11, QFont.Weight.Bold)
                    font.setItalic(True)
                    item.setFont(font)

                self._table.setItem(row_idx, col_idx, item)

    def _filter_table(self, text: str):
        search = text.strip().lower()
        for row in range(self._table.rowCount()):
            item = self._table.item(row, 0)
            if item:
                match = search in item.text().lower() or search == ""
                self._table.setRowHidden(row, not match)

    def _start_export(self):
        if not self._data_dict:
            return

        default_name = f"Dashboard_AH_Gunsar_{datetime.now().strftime('%d_%b_%Y')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Simpan File Excel", default_name, "Excel Files (*.xlsx)")
        if not path:
            return

        self._btn_export.setEnabled(False)
        self._btn_export.setText("Mengekspor...")
        
        self._export_worker = ExportWorker(self._data_dict, path, datetime.now().strftime("%d %B %Y"))
        self._export_worker.finished.connect(self._on_export_success)
        self._export_worker.error.connect(self._on_export_error)
        self._export_worker.start()

    def _on_export_success(self, path):
        self._btn_export.setEnabled(True)
        self._btn_export.setText("📥 Export Excel")
        
        # Toast dengan aksi
        ToastManager.show(self.window(), f"Export berhasil: {os.path.basename(path)}", "success")
        
        reply = QMessageBox.information(
            self, "Export Berhasil", f"File berhasil disimpan di:\n{path}\n\nIngin membuka folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            folder = os.path.dirname(path)
            if os.name == 'mac':
                subprocess.Popen(["open", folder])
            elif os.name == 'nt':
                os.startfile(folder)
            else:
                subprocess.Popen(["xdg-open", folder])

    def _on_export_error(self, msg):
        self._btn_export.setEnabled(True)
        self._btn_export.setText("📥 Export Excel")
        ToastManager.show(self.window(), f"Export gagal: {msg}", "error")
