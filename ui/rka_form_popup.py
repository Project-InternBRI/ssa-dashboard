from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QGridLayout, QFrame, QLineEdit, QApplication,
    QGraphicsDropShadowEffect, QListView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QCursor

from core.db_manager import load_rka_record, save_rka_record
from ui.toast_notification import ToastManager
from ui.custom_dropdown import CustomDropdown

KCS = [
    "KC Jakarta Tanah Abang", "KC Jakarta Krekot", "KC Jakarta Veteran",
    "KC Jakarta Roxi", "KC Jakarta Gunung Sahari", "KC Jakarta Mangga Dua",
    "KC Jakarta Kemayoran"
]
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
         "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
TAHUN = ["2026", "2027"]

COMBOBOX_STYLE = """
QComboBox {
    border: 1px solid #CBD5E1;
    border-radius: 18px;
    padding: 6px 16px;
    background: #FFFFFF;
    color: #334155;
    font-size: 13px;
    font-weight: 500;
}
QComboBox:focus {
    border: 2px solid #3B82F6;
    background: #F8FAFC;
}
QComboBox QAbstractItemView {
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    background-color: #FFFFFF;
    selection-background-color: #EFF6FF;
    selection-color: #1E3A8A;
    color: #475569;
    outline: none;
    padding: 6px;
}
QComboBox QAbstractItemView::item {
    min-height: 32px;
    border-radius: 8px;
    padding: 4px 12px;
}
"""

class FormInputRKA(QDialog):
    data_saved = Signal()
    
    def __init__(self, target_kc=None, target_tahun=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.resize(600, 750)
        
        self.inputs = {}
        self._initial_kc = target_kc
        self._initial_tahun = target_tahun
        
        self.init_ui()
        self.load_current_data()
        
    def init_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(20, 20, 20, 20)
        
        card = QFrame(self)
        card.setObjectName("card")
        card.setStyleSheet("QFrame#card { background: #FFFFFF; border-radius: 20px; border: none; }")
        
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        card.setGraphicsEffect(shadow)
        
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
        card_lay.setSpacing(0)
        
        # ── HEADER ──
        hdr = QFrame()
        hdr.setStyleSheet("background: #F8FAFC; border-top-left-radius: 20px; border-top-right-radius: 20px; border-bottom: 1px solid #E2E8F0;")
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(24, 16, 24, 16)
        
        title = QLabel("Form Input RKA")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #0F172A; border: none;")
        
        btn_close = QPushButton("✕")
        btn_close.setFixedSize(28, 28)
        btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_close.setStyleSheet("QPushButton { background: transparent; color: #94A3B8; font-size: 16px; font-weight: bold; border: none; } QPushButton:hover { color: #EF4444; }")
        btn_close.clicked.connect(self.reject)
        
        hdr_lay.addWidget(title)
        hdr_lay.addStretch()
        hdr_lay.addWidget(btn_close)
        
        # ── FILTERS ──
        flt = QFrame()
        flt.setStyleSheet("border-bottom: 1px solid #E2E8F0;")
        flt_lay = QHBoxLayout(flt)
        flt_lay.setContentsMargins(24, 16, 24, 16)
        flt_lay.setSpacing(12)
        
        self.cb_kc = CustomDropdown(KCS)
        if self._initial_kc and self._initial_kc in KCS:
            self.cb_kc.setCurrentText(self._initial_kc)
        
        self.cb_tahun = CustomDropdown(TAHUN)
        if self._initial_tahun and self._initial_tahun in TAHUN:
            self.cb_tahun.setCurrentText(self._initial_tahun)
        
        self.cb_bulan = CustomDropdown(BULAN)
        
        flt_lay.addWidget(self.cb_kc, 2)
        flt_lay.addWidget(self.cb_tahun, 1)
        flt_lay.addWidget(self.cb_bulan, 1)
        
        self.cb_kc.currentTextChanged.connect(self.load_current_data)
        self.cb_tahun.currentTextChanged.connect(self.load_current_data)
        self.cb_bulan.currentTextChanged.connect(self.load_current_data)
        
        # ── SCROLL AREA FOR FORM ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; } QScrollBar:vertical { width: 8px; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        form_lay = QVBoxLayout(scroll_content)
        form_lay.setContentsMargins(24, 24, 24, 24)
        form_lay.setSpacing(24)
        
        self._build_section(form_lay, "Dana Pihak Ketiga", [
            ("Tabungan", "dpk_tabungan"),
            ("Giro", "dpk_giro"),
            ("Deposito", "dpk_deposito")
        ])
        
        self._build_section(form_lay, "DPK Korporasi", [
            ("Giro", "korp_giro"),
            ("Deposito", "korp_deposito")
        ])
        
        self._build_section(form_lay, "Pinjaman", [
            ("Mikro", "pinj_mikro"),
            ("Small", "pinj_small"),
            ("Konsumer", "pinj_konsumer")
        ])
        
        self._build_section(form_lay, "SML", [
            ("Mikro", "sml_mikro"),
            ("Small", "sml_small"),
            ("Konsumer", "sml_konsumer")
        ])
        
        self._build_section(form_lay, "NPL", [
            ("Mikro", "npl_mikro"),
            ("Small", "npl_small"),
            ("Konsumer", "npl_konsumer")
        ])
        
        self._build_section(form_lay, "Recovery EC", [
            ("Mikro", "rec_mikro"),
            ("Small", "rec_small"),
            ("Konsumer", "rec_konsumer")
        ])
        
        form_lay.addStretch()
        scroll.setWidget(scroll_content)
        
        # ── FOOTER ──
        ftr = QFrame()
        ftr.setStyleSheet("background: #FFFFFF; border-top: 1px solid #E2E8F0; border-bottom-left-radius: 20px; border-bottom-right-radius: 20px;")
        ftr_lay = QHBoxLayout(ftr)
        ftr_lay.setContentsMargins(24, 16, 24, 16)
        
        btn_cancel = QPushButton("Batal")
        btn_cancel.setFixedHeight(40)
        btn_cancel.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancel.setStyleSheet("QPushButton { background: #F1F5F9; color: #475569; border: none; border-radius: 20px; padding: 0 24px; font-weight: 600; font-size: 13px; } QPushButton:hover { background: #E2E8F0; }")
        btn_cancel.clicked.connect(self.reject)
        
        btn_save = QPushButton("Simpan RKA")
        btn_save.setFixedHeight(40)
        btn_save.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_save.setStyleSheet("QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #3B82F6); color: #FFFFFF; border: none; border-radius: 20px; padding: 0 24px; font-weight: 700; font-size: 13px; } QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1D4ED8, stop:1 #2563EB); }")
        btn_save.clicked.connect(self.save_data)
        
        ftr_lay.addStretch()
        ftr_lay.addWidget(btn_cancel)
        ftr_lay.addWidget(btn_save)
        
        card_lay.addWidget(hdr)
        card_lay.addWidget(flt)
        card_lay.addWidget(scroll, 1)
        card_lay.addWidget(ftr)
        
        main_lay.addWidget(card)
        
    def _build_section(self, parent_lay, title, fields):
        frm = QFrame()
        frm.setStyleSheet("QFrame { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; }")
        lay = QVBoxLayout(frm)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(16)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: 800; color: #1E293B; border: none; background: transparent;")
        lay.addWidget(lbl_title)
        
        grid = QGridLayout()
        grid.setSpacing(12)
        
        row = 0
        col = 0
        for label_text, key in fields:
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #64748B; border: none; background: transparent;")
            inp = QLineEdit()
            inp.setFixedHeight(38)
            inp.setStyleSheet("QLineEdit { border: 1px solid #CBD5E1; border-radius: 19px; padding: 0 16px; background: #FFFFFF; color: #1E293B; font-weight: 500; font-size: 13px; } QLineEdit:focus { border: 2px solid #3B82F6; background: #EFF6FF; }")
            
            # Formatting events
            inp.textEdited.connect(lambda txt, k=key: self._format_input(k, txt))
            
            self.inputs[key] = inp
            
            cell = QVBoxLayout()
            cell.setSpacing(4)
            cell.addWidget(lbl)
            cell.addWidget(inp)
            
            grid.addLayout(cell, row, col)
            col += 1
            if col > 1: # 2 columns
                col = 0
                row += 1
                
        lay.addLayout(grid)
        parent_lay.addWidget(frm)
        
    def _format_input(self, key, text):
        inp = self.inputs[key]
        if key.endswith("_pct"):
            # Don't restrict formatting for percentages too strictly during typing
            pass
        else:
            try:
                # Remove non-digits
                clean = "".join(c for c in text if c.isdigit())
                if clean:
                    val = int(clean)
                    formatted = f"{val:,}".replace(",", ".")
                    inp.setText(formatted)
                else:
                    inp.setText("")
            except:
                pass
                
    def load_current_data(self):
        kc = self.cb_kc.currentText()
        tahun = int(self.cb_tahun.currentText())
        bulan = self.cb_bulan.currentText()
        
        record = load_rka_record(kc, tahun, bulan)
        
        for key, inp in self.inputs.items():
            val = record.get(key, "")
            if key.endswith("_pct"):
                inp.setText(str(val) if val else "0,00")
            else:
                if val:
                    formatted = f"{int(val):,}".replace(",", ".")
                    inp.setText(formatted)
                else:
                    inp.setText("0")
                    
    def save_data(self):
        kc = self.cb_kc.currentText()
        tahun = int(self.cb_tahun.currentText())
        bulan = self.cb_bulan.currentText()
        
        data = {
            "kc": kc,
            "tahun": tahun,
            "bulan": bulan
        }
        
        for key, inp in self.inputs.items():
            txt = inp.text()
            if key.endswith("_pct"):
                data[key] = txt
            else:
                clean = "".join(c for c in txt if c.isdigit())
                data[key] = int(clean) if clean else 0
                
        save_rka_record(data)
        self.data_saved.emit()
        ToastManager.show(self.window(), "Data RKA Berhasil Disimpan", "success")
        self.accept()
