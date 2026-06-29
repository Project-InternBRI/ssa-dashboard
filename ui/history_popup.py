import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QScrollArea, QWidget, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

class HistoryPopup(QDialog):
    def __init__(self, history_list, parent=None):
        super().__init__(parent)
        self.history_list = history_list
        self.setWindowTitle("Semua Aktivitas")
        self.setFixedSize(700, 600)
        self.setStyleSheet("background: #F8FAFC;")
        
        self._setup_ui()
        
    def _icon_label(self, icon_filename, bg, fg):
        lbl = QLabel()
        lbl.setFixedSize(32, 32)
        lbl.setStyleSheet(f"background: {bg}; border-radius: 8px;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if icon_filename:
            icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "icons", icon_filename))
            pixmap = QIcon(icon_path).pixmap(QSize(20, 20))
            if fg:
                from PySide6.QtGui import QPainter, QColor
                painter = QPainter(pixmap)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
                painter.fillRect(pixmap.rect(), QColor(fg))
                painter.end()
            lbl.setPixmap(pixmap)
        return lbl
        
    def _setup_ui(self):
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(24, 24, 24, 24)
        main_lay.setSpacing(20)

        # Header
        header = QHBoxLayout()
        title = QLabel("Semua Aktivitas")
        title.setStyleSheet("font-size: 20px; font-weight: 800; color: #0F2A4A;")
        
        close_btn = QPushButton("Tutup")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("background: #E2E8F0; color: #475569; padding: 6px 16px; border-radius: 6px; font-weight: bold; font-size: 13px; border: none;")
        close_btn.clicked.connect(self.accept)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        main_lay.addLayout(header)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        content_w = QWidget()
        content_w.setStyleSheet("background: transparent;")
        c_lay = QVBoxLayout(content_w)
        c_lay.setContentsMargins(0, 0, 16, 0)
        c_lay.setSpacing(24)

        # Grouping
        from collections import defaultdict
        
        grouped = defaultdict(lambda: defaultdict(list))
        
        for entry in self.history_list:
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
                    time_str = t_part[:5]
                else:
                    month_year_key = "Lainnya"
                    date_key = tgl_full
                    time_str = ""
            except:
                month_year_key = "Lainnya"
                date_key = tgl_full
                time_str = ""
            
            grouped[month_year_key][date_key].append((entry, time_str, tgl_full))

        if not self.history_list:
            empty = QLabel("Tidak ada aktivitas ditemukan.")
            empty.setStyleSheet("color: #64748B; font-size: 14px;")
            c_lay.addWidget(empty)
        
        for my_key, dates in grouped.items():
            # Month Header
            my_lbl = QLabel(my_key)
            my_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #0F2A4A; margin-top: 12px;")
            c_lay.addWidget(my_lbl)
            
            for d_key, runs in dates.items():
                # Date Container
                d_frame = QFrame()
                d_frame.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; border: 1px solid #E2E8F0; }")
                d_lay = QVBoxLayout(d_frame)
                d_lay.setContentsMargins(16, 16, 16, 16)
                d_lay.setSpacing(12)
                
                # Date Header inside the frame
                dh_lbl = QLabel(d_key)
                dh_lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #475569; border: none;")
                d_lay.addWidget(dh_lbl)
                
                # Separator
                sep = QFrame()
                sep.setFixedHeight(1)
                sep.setStyleSheet("background: #E2E8F0; border: none;")
                d_lay.addWidget(sep)
                
                for run_idx, (entry, time_str, tgl_full) in enumerate(runs):
                    if run_idx > 0:
                        sep2 = QFrame()
                        sep2.setFixedHeight(1)
                        sep2.setStyleSheet("background: #F1F5F9; border: none; margin: 8px 0px;")
                        d_lay.addWidget(sep2)
                        
                    ok = entry.get("status", "sukses") != "gagal"
                    fn_simpanan = entry.get("nama_file_simpanan") or "SSA Simpanan.csv"
                    fn_pinjaman = entry.get("nama_file_pinjaman") or "SSA Pinjaman.csv"
                    
                    full_date_str = f"{d_key}, {time_str}" if time_str else d_key

                    activities = [
                        ("Upload File SSA", fn_simpanan, "upload.svg", "#EFF6FF", "#2563EB", "Sukses", ok),
                        ("Upload File SSA", fn_pinjaman, "upload.svg", "#EFF6FF", "#2563EB", "Sukses", ok),
                        ("Generate Dashboard", "Proses konsolidasi data", "settings.svg", "#F0FDF4", "#16A34A", "Sukses", ok)
                    ]
                    
                    if entry.get("is_exported"):
                        activities.append(("Export Excel", "Hasil Dashboard.xlsx", "unduh_homepage.svg", "#FFF7ED", "#D97706", "Berhasil", ok))

                    for title, detail, icon_name, bg_c, fg_c, status_text, is_ok in activities:
                        row_w = QWidget()
                        row_w.setStyleSheet("background: transparent; border: none;")
                        r_lay = QHBoxLayout(row_w)
                        r_lay.setContentsMargins(0, 4, 0, 4)
                        
                        a_ic = self._icon_label(icon_name, bg_c, fg_c)
                        a_lay = QVBoxLayout()
                        a_lay.addWidget(a_ic); a_lay.addStretch()
                        
                        r_lay.addLayout(a_lay)
                        r_lay.addSpacing(12)
                        
                        txt_lay = QVBoxLayout()
                        t = QLabel(title)
                        t.setStyleSheet("color: #0F2A4A; font-size: 13px; font-weight: bold; border: none;")
                        d = QLabel(detail)
                        d.setStyleSheet("color: #64748B; font-size: 11px; border: none;")
                        txt_lay.addWidget(t)
                        txt_lay.addWidget(d)
                        txt_lay.addStretch()
                        r_lay.addLayout(txt_lay)
                        
                        r_lay.addStretch()
                        
                        # Time and Status
                        ts_lay = QVBoxLayout()
                        tm = QLabel(full_date_str)
                        tm.setStyleSheet("color: #64748B; font-size: 11px; border: none;")
                        tm.setAlignment(Qt.AlignmentFlag.AlignRight)
                        
                        s_txt = QLabel(status_text if is_ok else "Gagal")
                        stat_bg = "#DCFCE7" if is_ok else "#FEE2E2"
                        stat_fg = "#16A34A" if is_ok else "#DC2626"
                        s_txt.setStyleSheet(f"background: {stat_bg}; color: {stat_fg}; font-size: 10px; font-weight: bold; padding: 4px 8px; border-radius: 6px; border: none;")
                        
                        st_lay = QHBoxLayout()
                        st_lay.addStretch()
                        st_lay.addWidget(s_txt)
                        
                        ts_lay.addWidget(tm)
                        ts_lay.addSpacing(4)
                        ts_lay.addLayout(st_lay)
                        ts_lay.addStretch()
                        
                        r_lay.addLayout(ts_lay)
                        d_lay.addWidget(row_w)
                        
                c_lay.addWidget(d_frame)

        c_lay.addStretch()
        scroll.setWidget(content_w)
        main_lay.addWidget(scroll)
