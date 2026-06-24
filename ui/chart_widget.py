"""
chart_widget.py — Halaman Dashboard Grafik.
Menampilkan grafik data nyata, filter produk/KC, dan empty state.
"""
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QComboBox, QScrollArea, QPushButton)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QBarSeries,
                               QBarSet, QValueAxis, QCategoryAxis,
                               QBarCategoryAxis)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QCursor


class ChartWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data_dict = {}
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
        lay = QVBoxLayout(content)
        lay.setContentsMargins(32, 28, 32, 40)
        lay.setSpacing(20)

        # Header
        hdr = QVBoxLayout()
        hdr.setSpacing(4)
        lbl_t = QLabel("Dashboard")
        lbl_t.setStyleSheet("font-size: 22px; font-weight: bold; color: #0F2A4A;")
        lbl_s = QLabel("Ringkasan kinerja per KC")
        lbl_s.setStyleSheet("font-size: 13px; color: #94A3B8;")
        hdr.addWidget(lbl_t)
        hdr.addWidget(lbl_s)
        lay.addLayout(hdr)

        # Filter card
        filter_card = QFrame()
        filter_card.setStyleSheet("""
            QFrame { background: #FFFFFF; border-radius: 12px; border: 1px solid #E2EAF4; }
        """)
        f_lay = QHBoxLayout(filter_card)
        f_lay.setContentsMargins(20, 14, 20, 14)
        f_lay.setSpacing(20)

        lbl_p = QLabel("Produk")
        lbl_p.setStyleSheet("font-size: 12px; font-weight: 600; color: #6B7A8D;")

        self._combo_produk = QComboBox()
        self._combo_produk.setMinimumWidth(200)
        self._combo_produk.setFixedHeight(38)
        self._combo_produk.addItems(["— Semua Produk —", "Tabungan", "Giro", "Deposito", "CASA", "Total DPK", "Pinjaman"])
        self._combo_produk.currentTextChanged.connect(self._on_filter_changed)
        self._combo_produk.setStyleSheet("QComboBox { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 12px; }")

        lbl_kc = QLabel("Kantor Cabang")
        lbl_kc.setStyleSheet("font-size: 12px; font-weight: 600; color: #6B7A8D;")

        self._combo_kc = QComboBox()
        self._combo_kc.setMinimumWidth(240)
        self._combo_kc.setFixedHeight(38)
        self._combo_kc.addItem("— Semua KC —")
        self._combo_kc.currentTextChanged.connect(self._on_filter_changed)
        self._combo_kc.setStyleSheet("QComboBox { background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 0 12px; }")

        f_lay.addWidget(lbl_p)
        f_lay.addWidget(self._combo_produk)
        f_lay.addWidget(lbl_kc)
        f_lay.addWidget(self._combo_kc)
        f_lay.addStretch()
        
        self.filter_card = filter_card
        lay.addWidget(filter_card)

        # Charts Area
        self.charts_container = QWidget()
        charts_row = QHBoxLayout(self.charts_container)
        charts_row.setContentsMargins(0, 0, 0, 0)
        charts_row.setSpacing(20)

        self._view_line, self._chart_line = self._make_chart_card(charts_row, "Tren Realisasi per Segmen", "Rp Juta")
        self._view_bar, self._chart_bar = self._make_chart_card(charts_row, "DPK vs Pinjaman per KC", "Rp Juta")

        lay.addWidget(self.charts_container)

        # Empty State
        self.empty_state = QWidget()
        el = QVBoxLayout(self.empty_state)
        el.setContentsMargins(0, 40, 0, 0)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(12)

        ic = QLabel("📊")
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("font-size: 64px; color: #CBD5E1;")

        t1 = QLabel("Belum Ada Data untuk Ditampilkan")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        
        t2 = QLabel("Lakukan generate data terlebih dahulu untuk melihat grafik")
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

        lay.addWidget(self.empty_state)

        lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll)

        self._show_empty()

    def load_data(self, data_dict: dict):
        self._data_dict = data_dict

        if not data_dict:
            self._show_empty()
            return

        # Hide empty state, show charts
        self.empty_state.hide()
        self.filter_card.show()
        self.charts_container.show()

        # Update KC combo
        if "Total DPK" in data_dict and not data_dict["Total DPK"].empty:
            df = data_dict["Total DPK"]
            kcs = df[df["KC"] != "TOTAL KESELURUHAN"]["KC"].tolist()
            self._combo_kc.blockSignals(True)
            self._combo_kc.clear()
            self._combo_kc.addItem("— Semua KC —")
            self._combo_kc.addItems(kcs)
            self._combo_kc.blockSignals(False)

        self.update_chart()

    def _show_empty(self):
        self.empty_state.show()
        self.filter_card.hide()
        self.charts_container.hide()

    def update_chart(self):
        if not self._data_dict:
            return

        produk = self._combo_produk.currentText()
        kc = self._combo_kc.currentText()
        is_all_produk = "Semua" in produk
        is_all_kc = "Semua" in kc

        filter_kc = None if is_all_kc else kc

        if is_all_produk:
            self._draw_dpk_pinjaman_bar(filter_kc)
            self._draw_tren_line("Total DPK", filter_kc)
        else:
            self._draw_tren_line(produk, filter_kc)
            self._draw_dpk_pinjaman_bar(filter_kc)

    def _draw_tren_line(self, sheet_name: str, filter_kc: str = None):
        self._chart_line.removeAllSeries()
        for ax in self._chart_line.axes():
            self._chart_line.removeAxis(ax)

        if sheet_name not in self._data_dict or self._data_dict[sheet_name].empty:
            return

        df = self._data_dict[sheet_name]
        num_cols = [c for c in df.columns if c not in ("KC", "Total", "Target RKA")]

        if filter_kc:
            rows = df[df["KC"] == filter_kc]
            if rows.empty: return
            data_rows = [rows.iloc[0]]
        else:
            data_rows = df[df["KC"] != "TOTAL KESELURUHAN"].head(8).to_dict("records")

        colors = ["#2563EB", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16"]
        max_v = 0
        series_list = []

        for idx, row in enumerate(data_rows):
            s = QLineSeries()
            kc_name = row["KC"] if isinstance(row, dict) else row
            s.setName(kc_name[:15] + "…" if len(kc_name) > 15 else kc_name)
            
            pen = QPen(QColor(colors[idx % len(colors)]))
            pen.setWidth(2)
            s.setPen(pen)

            for i, seg in enumerate(num_cols):
                v = float(row.get(seg, 0) if isinstance(row, dict) else 0)
                s.append(i, v)
                max_v = max(max_v, v)

            self._chart_line.addSeries(s)
            series_list.append(s)

        if not series_list: return

        ax_x = QCategoryAxis()
        ax_x.setLabelsFont(QFont("Arial", 9))
        for i, seg in enumerate(num_cols):
            ax_x.append(seg, i)
        ax_x.setRange(0, max(len(num_cols) - 1, 1))

        ax_y = QValueAxis()
        ax_y.setRange(0, max(max_v * 1.2, 10))
        ax_y.setLabelFormat("%d")
        ax_y.setLabelsFont(QFont("Arial", 9))

        self._chart_line.addAxis(ax_x, Qt.AlignmentFlag.AlignBottom)
        self._chart_line.addAxis(ax_y, Qt.AlignmentFlag.AlignLeft)
        for s in series_list:
            s.attachAxis(ax_x)
            s.attachAxis(ax_y)

    def _draw_dpk_pinjaman_bar(self, filter_kc: str = None):
        self._chart_bar.removeAllSeries()
        for ax in self._chart_bar.axes():
            self._chart_bar.removeAxis(ax)

        df_dpk = self._data_dict.get("Total DPK")
        df_pinj = self._data_dict.get("Pinjaman")

        if df_dpk is None or df_pinj is None:
            return

        if filter_kc:
            rows_dpk = df_dpk[df_dpk["KC"] == filter_kc]
            rows_pinj = df_pinj[df_pinj["KC"] == filter_kc]
        else:
            rows_dpk = df_dpk[df_dpk["KC"] != "TOTAL KESELURUHAN"].head(6)
            rows_pinj = df_pinj[df_pinj["KC"] != "TOTAL KESELURUHAN"].head(6)

        kcs = list(rows_dpk["KC"])
        if not kcs: return

        bar_dpk = QBarSet("DPK")
        bar_dpk.setColor(QColor("#1E3A5F"))

        bar_pinj = QBarSet("Pinjaman")
        bar_pinj.setColor(QColor("#60A5FA"))

        max_v = 0
        for kc in kcs:
            d_val = float(rows_dpk[rows_dpk["KC"] == kc]["Total"].values[0]) if not rows_dpk[rows_dpk["KC"] == kc].empty else 0
            p_val = float(rows_pinj[rows_pinj["KC"] == kc]["Total"].values[0]) if not rows_pinj[rows_pinj["KC"] == kc].empty else 0
            bar_dpk.append(d_val)
            bar_pinj.append(p_val)
            max_v = max(max_v, d_val, p_val)

        bs = QBarSeries()
        bs.append(bar_dpk)
        bs.append(bar_pinj)
        self._chart_bar.addSeries(bs)

        short_kcs = [k.replace("KC Jakarta", "Jkt").replace("KC ", "")[:10] for k in kcs]
        
        ax_cat = QBarCategoryAxis()
        ax_cat.append(short_kcs)
        ax_cat.setLabelsFont(QFont("Arial", 8))

        ax_val = QValueAxis()
        ax_val.setRange(0, max(max_v * 1.2, 10))
        ax_val.setLabelFormat("%d")
        ax_val.setLabelsFont(QFont("Arial", 9))

        self._chart_bar.addAxis(ax_cat, Qt.AlignmentFlag.AlignBottom)
        self._chart_bar.addAxis(ax_val, Qt.AlignmentFlag.AlignLeft)
        bs.attachAxis(ax_cat)
        bs.attachAxis(ax_val)

    def _on_filter_changed(self):
        self.update_chart()

    def _make_chart_card(self, lay_ref, title: str, unit: str):
        card = QFrame()
        card.setStyleSheet("QFrame { background-color: #FFFFFF; border-radius: 12px; border: 1px solid #E2EAF4; }")
        c_lay = QVBoxLayout(card)
        c_lay.setContentsMargins(16, 16, 16, 12)

        hdr = QHBoxLayout()
        lbl_t = QLabel(title)
        lbl_t.setStyleSheet("font-size: 14px; font-weight: bold; color: #0F2A4A;")
        lbl_u = QLabel(unit)
        lbl_u.setStyleSheet("font-size: 11px; color: #94A3B8;")
        hdr.addWidget(lbl_t)
        hdr.addStretch()
        hdr.addWidget(lbl_u)
        c_lay.addLayout(hdr)

        chart = QChart()
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        chart.setBackgroundVisible(False)
        chart.setMargins(chart.margins().__class__(0, 0, 0, 0))

        view = QChartView(chart)
        view.setRenderHint(QPainter.RenderHint.Antialiasing)
        view.setMinimumHeight(280)
        view.setBackgroundBrush(QColor("transparent"))
        c_lay.addWidget(view)

        lay_ref.addWidget(card, 1)
        return view, chart