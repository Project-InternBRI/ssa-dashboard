"""
dashboard_widget.py — Halaman Dashboard 6 Grafik.
Embed matplotlib ke PySide6 via FigureCanvasQTAgg.

Layout 2×3 grid:
  Chart 1: Tren DPK per Periode  (Line)
  Chart 2: DPK vs Pinjaman per KC (Grouped Bar)
  Chart 3: Growth MTD per KC      (Bar ±)
  Chart 4: Komposisi DPK          (Donut)
  Chart 5: Ranking KC by DPK      (Horizontal Sorted Bar)
  Chart 6: Tren per KC            (Multi-line)
"""
from __future__ import annotations

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message=".*Tight layout not applied.*")

import matplotlib
matplotlib.use("QtAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

# Styling Matplotlib yang modern
plt.rcParams.update({
    "axes.facecolor": "none",
    "axes.edgecolor": "none",
    "axes.grid": True,
    "grid.color": "#E2EAF4",
    "grid.linestyle": "-",
    "grid.alpha": 1.0,
    "axes.labelcolor": "#64748B",
    "xtick.color": "#64748B",
    "ytick.color": "#64748B",
    "font.size": 9,
    "figure.facecolor": "none"
})

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                               QFrame, QScrollArea, QPushButton,
                               QGridLayout, QGraphicsDropShadowEffect, QListView)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor, QColor
from ui.custom_dropdown import CustomDropdown

PALETTE = ["#1E3A5F", "#2563EB", "#60A5FA", "#16A34A", "#34D399",
           "#D97706", "#F59E0B", "#DC2626", "#F87171", "#8B5CF6"]

class MplCanvas(FigureCanvas):
    """Wrapper matplotlib figure ke Qt widget."""
    def __init__(self, width=5, height=3.5, dpi=96):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.fig.patch.set_alpha(0.0)  # transparent background
        super().__init__(self.fig)
        self.setStyleSheet("background: transparent;")


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    """Buat card putih dengan judul, return (frame, content_layout)."""
    fr = QFrame()
    fr.setStyleSheet("QFrame { background: #FFFFFF; border-radius: 12px; border: none; }")
    shadow = QGraphicsDropShadowEffect(fr)
    shadow.setBlurRadius(10)
    shadow.setColor(QColor(0, 0, 0, 8))
    shadow.setOffset(0, 2)
    fr.setGraphicsEffect(shadow)

    lay = QVBoxLayout(fr)
    lay.setContentsMargins(16, 16, 16, 12)
    lay.setSpacing(8)

    lbl = QLabel(title)
    lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: #1E293B;")
    lay.addWidget(lbl)
    return fr, lay


def _get_rows(kc_data: dict, section: str = "all") -> list:
    """
    Get rows from kc_data supporting both old and new format.
    section: 'all', 'dpk', 'pinjaman'
    """
    # New format: single 'rows' list
    if "rows" in kc_data:
        return kc_data["rows"]
    # Old format: rows_dpk + rows_pinjaman
    if section == "dpk":
        return kc_data.get("rows_dpk", [])
    elif section == "pinjaman":
        return kc_data.get("rows_pinjaman", [])
    return kc_data.get("rows_dpk", []) + kc_data.get("rows_pinjaman", [])


class ChartWidget(QWidget):
    navigate_to = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: dict = {}
        self._init_ui()

    # ── BUILD UI ────────────────────────────────────────────────
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
        self._main_lay.setContentsMargins(32, 28, 32, 40)
        self._main_lay.setSpacing(20)

        # Filter
        self._filter_card = self._build_filter()
        self._main_lay.addWidget(self._filter_card)

        # Grid chart 2×3
        self._grid_widget = QWidget()
        grid = QGridLayout(self._grid_widget)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(16)

        # Inisialisasi 6 canvas
        self._canvases = {}
        self._axes     = {}

        defs = [
            (0, 0, "c1", "Tren DPK per Periode"),
            (0, 1, "c2", "DPK vs Pinjaman per KC"),
            (1, 0, "c3", "Growth MTD per KC"),
            (1, 1, "c4", "Komposisi DPK"),
            (2, 0, "c5", "Ranking KC by Total DPK"),
            (2, 1, "c6", "Tren per KC"),
        ]

        for r, c, key, title in defs:
            fr, cl = _card(title)
            canvas = MplCanvas()
            cl.addWidget(canvas)
            self._canvases[key] = canvas
            grid.addWidget(fr, r, c)

        self._main_lay.addWidget(self._grid_widget)

        # Empty state
        self._empty = self._build_empty()
        self._main_lay.addWidget(self._empty)

        scroll.setWidget(content)
        root.addWidget(scroll)

        self._show_empty()

    def _build_filter(self) -> QFrame:
        fr = QFrame()
        fr.setStyleSheet("""
            QFrame { background: #FFFFFF; border-radius: 12px; border: 1px solid #E2EAF4; }
        """)
        lay = QHBoxLayout(fr)
        lay.setContentsMargins(20, 14, 20, 14)
        lay.setSpacing(20)

        def create_dropdown(items, min_w=160):
            c = CustomDropdown(items)
            c.setMinimumWidth(min_w)
            c.setFixedHeight(36)
            return c

        self._combo_produk  = create_dropdown(["Semua Produk", "Tabungan", "Giro", "Deposito", "DPK", "Pinjaman"])
        self._combo_kc      = create_dropdown(["Semua KC"], 200)
        self._combo_periode = create_dropdown(["Semua Periode"], 200)

        for lbl_txt, widget in [
            ("Produk", self._combo_produk),
            ("KC", self._combo_kc),
            ("Periode", self._combo_periode),
        ]:
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #6B7A8D;")
            lay.addWidget(lbl)
            lay.addWidget(widget)

        lay.addStretch()

        btn_refresh = QPushButton("↻  Refresh Grafik")
        btn_refresh.setFixedHeight(36)
        btn_refresh.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_refresh.setStyleSheet("""
            QPushButton { background: #EFF6FF; color: #2563EB; border: 1px solid #93C5FD;
                border-radius: 6px; padding: 0 16px; font-weight: bold; font-size: 13px; }
            QPushButton:hover { background: #DBEAFE; }
        """)
        btn_refresh.clicked.connect(self._draw_all)
        lay.addWidget(btn_refresh)

        self._combo_produk.currentTextChanged.connect(self._draw_all)
        self._combo_kc.currentTextChanged.connect(self._draw_all)

        return fr

    def _build_empty(self) -> QWidget:
        empty = QWidget()
        empty.setStyleSheet("background: transparent;")
        el = QVBoxLayout(empty)
        el.setContentsMargins(0, 60, 0, 0)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        el.setSpacing(12)

        t1 = QLabel("Belum Ada Data untuk Ditampilkan")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet("font-size: 18px; font-weight: bold; color: #1E293B;")
        t2 = QLabel("Lakukan generate data terlebih dahulu untuk melihat grafik")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet("font-size: 14px; color: #64748B;")

        btn = QPushButton("Mulai Generate Sekarang")
        btn.setFixedHeight(40)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton { background: #2563EB; color: #FFFFFF; border-radius: 8px;
                font-weight: bold; font-size: 13px; padding: 0 24px; border: none; }
            QPushButton:hover { background: #1D4ED8; }
        """)
        btn.clicked.connect(lambda: self.navigate_to.emit(2))

        el.addWidget(t1)
        el.addWidget(t2)
        el.addSpacing(16)
        el.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        return empty

    # ── DATA LOAD ────────────────────────────────────────────────
    def load_data(self, data_dict: dict):
        self._data = data_dict
        if not data_dict:
            self._show_empty()
            return

        self._show_charts()

        # Update KC combo
        _skip = {"Total AH Gunsar", "__stats__"}
        kcs = [k for k in data_dict if k not in _skip]
        self._combo_kc.blockSignals(True)
        self._combo_kc.clear()
        self._combo_kc.addItem("Semua KC")
        self._combo_kc.addItems(kcs)
        self._combo_kc.blockSignals(False)

        # Update Periode combo
        sample = next((v for k, v in data_dict.items() if k not in _skip), {})
        periodes = sample.get("periode_list", [])
        self._combo_periode.blockSignals(True)
        self._combo_periode.clear()
        self._combo_periode.addItem("Semua Periode")
        self._combo_periode.addItems(periodes)
        self._combo_periode.blockSignals(False)

        self._draw_all()

    def _show_empty(self):
        self._filter_card.hide()
        self._grid_widget.hide()
        self._empty.show()

    def _show_charts(self):
        self._empty.hide()
        self._filter_card.show()
        self._grid_widget.show()

    # ── DRAW ALL ─────────────────────────────────────────────────
    def _draw_all(self):
        if not self._data:
            return
        try:
            self._draw_c1_tren_dpk()
            self._draw_c2_dpk_pinjaman()
            self._draw_c3_growth_mtd()
            self._draw_c4_donut()
            self._draw_c5_ranking()
            self._draw_c6_tren_kc()
        except Exception:
            pass  # Jangan crash UI jika data tidak sempurna

    def _get_total_row(self, kc_name: str, row_key: str,
                       label_filter: str) -> dict[str, float]:
        """Ambil nilai dari baris tertentu berdasarkan label."""
        kc_data = self._data.get(kc_name, {})
        for row in kc_data.get(row_key, []):
            if label_filter.lower() in row.get("label", "").lower():
                return row.get("values", {})
        return {}

    def _get_growth_rows(self, kc_name: str, row_key: str,
                         label_filter: str) -> list[dict]:
        """Ambil semua baris yang cocok dengan label filter."""
        kc_data = self._data.get(kc_name, {})
        return [r for r in kc_data.get(row_key, [])
                if label_filter.lower() in r.get("label", "").lower()]

    # ── CHART 1: Tren DPK per Periode ───────────────────────────
    def _draw_c1_tren_dpk(self):
        canvas = self._canvases["c1"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        sample = next(iter(self._data.values()), {})
        periodes = sample.get("periode_list", [])
        if not periodes:
            ax.text(0.5, 0.5, "Data tidak tersedia",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
            canvas.draw()
            return

        kc_total = "Total AH Gunsar" if "Total AH Gunsar" in self._data \
                   else list(self._data.keys())[0]

        colors_map = {
            "tabungan": "#2563EB", "giro": "#16A34A",
            "deposito": "#D97706", "total dpk": "#8B5CF6",
        }

        kc_data = self._data.get(kc_total, {})
        plotted = False
        for row in _get_rows(kc_data):
            lbl = row.get("label", "").strip().lower()
            if row.get("row_type") in ("subtotal", "total") and any(
                    k in lbl for k in ["tabungan", "giro", "deposito", "dpk"]):
                vals = [row["values"].get(p, 0) / 1e6 for p in periodes]
                name = row.get("label", "").replace("Total ", "")
                clr  = next((v for k, v in colors_map.items() if k in lbl), "#2563EB")
                lw   = 2.5 if "dpk" in lbl else 1.5
                ax.plot(periodes, vals, color=clr, linewidth=lw,
                        marker="o", markersize=4, label=name)
                plotted = True

        if not plotted:
            ax.text(0.5, 0.5, "Tidak ada data DPK",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
        else:
            ax.legend(fontsize=8, loc="upper left")
            ax.set_xlabel("")
            ax.set_ylabel("Miliar Rp", fontsize=9)
            ax.tick_params(axis="x", rotation=30, labelsize=8)
            ax.tick_params(axis="y", labelsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            ax.spines[["top", "right"]].set_visible(False)

        canvas.fig.tight_layout()
        canvas.draw()

    # ── CHART 2: DPK vs Pinjaman per KC ─────────────────────────
    def _draw_c2_dpk_pinjaman(self):
        canvas = self._canvases["c2"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        kcs   = [k for k in self._data if k not in ("Total AH Gunsar", "__stats__")][:8]
        dpk_v = []
        pin_v = []

        for kc in kcs:
            kc_data = self._data[kc]
            # Cari baris TOTAL DPK
            dpk = 0.0
            for r in _get_rows(kc_data):
                if "total dpk" in r.get("label", "").lower():
                    vals = r.get("values", {})
                    if vals:
                        dpk = list(vals.values())[-1] / 1e6
                    break
            # Cari baris TOTAL PINJAMAN
            pin = 0.0
            for r in _get_rows(kc_data):
                if "total pinjaman" in r.get("label", "").lower():
                    vals = r.get("values", {})
                    if vals:
                        pin = list(vals.values())[-1] / 1e6
                    break
            dpk_v.append(dpk)
            pin_v.append(pin)

        if not kcs:
            ax.text(0.5, 0.5, "Tidak ada data KC",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
            canvas.fig.tight_layout()
            canvas.draw()
            return

        x       = np.arange(len(kcs))
        width   = 0.38
        short   = [k.replace("KC Jakarta", "Jkt").replace("KC ", "")[:8] for k in kcs]

        ax.bar(x - width/2, dpk_v, width, label="DPK",     color="#1E3A5F")
        ax.bar(x + width/2, pin_v, width, label="Pinjaman", color="#60A5FA")
        ax.set_xticks(x)
        ax.set_xticklabels(short, fontsize=7, rotation=20)
        ax.set_ylabel("Miliar Rp", fontsize=9)
        ax.legend(fontsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="y", labelsize=8)

        canvas.fig.tight_layout()
        canvas.draw()

    # ── CHART 3: Growth MTD per KC ───────────────────────────────
    def _draw_c3_growth_mtd(self):
        canvas = self._canvases["c3"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        kcs   = [k for k in self._data if k not in ("Total AH Gunsar", "__stats__")][:8]
        mtds  = []

        for kc in kcs:
            kc_data = self._data[kc]
            val = 0.0
            for r in _get_rows(kc_data):
                if "total dpk" in r.get("label", "").lower():
                    val = r.get("mtd", 0) / 1e6
                    break
            mtds.append(val)

        if not kcs:
            ax.text(0.5, 0.5, "Tidak ada data",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
            canvas.fig.tight_layout()
            canvas.draw()
            return

        short  = [k.replace("KC Jakarta", "Jkt").replace("KC ", "")[:8] for k in kcs]
        colors = ["#16A34A" if v >= 0 else "#DC2626" for v in mtds]

        ax.bar(short, mtds, color=colors)
        ax.axhline(0, color="#94A3B8", linewidth=0.8)
        ax.set_ylabel("Growth MTD (Miliar Rp)", fontsize=9)
        ax.tick_params(axis="x", rotation=20, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

        canvas.fig.tight_layout()
        canvas.draw()

    # ── CHART 4: Donut Komposisi DPK ────────────────────────────
    def _draw_c4_donut(self):
        canvas = self._canvases["c4"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        kc_total = "Total AH Gunsar" if "Total AH Gunsar" in self._data \
                   else list(self._data.keys())[0]
        kc_data  = self._data.get(kc_total, {})

        labels = []
        vals   = []
        colors = ["#2563EB", "#16A34A", "#D97706"]

        for produk in ["Tabungan", "Giro", "Deposito"]:
            for r in _get_rows(kc_data):
                if r.get("label", "").strip().lower() == f"total {produk.lower()}":
                    v = list(r.get("values", {}).values())
                    if v:
                        labels.append(produk)
                        vals.append(abs(v[-1]) / 1e6)
                    break

        if not vals or sum(vals) == 0:
            ax.text(0.5, 0.5, "Tidak ada data DPK",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
        else:
            wedges, texts, autotexts = ax.pie(
                vals, labels=labels, colors=colors[:len(labels)],
                autopct="%1.1f%%", pctdistance=0.78,
                wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2)
            )
            for at in autotexts:
                at.set_fontsize(9)
            for t in texts:
                t.set_fontsize(9)

        canvas.fig.tight_layout()
        canvas.draw()

    # ── CHART 5: Ranking KC by DPK ───────────────────────────────
    def _draw_c5_ranking(self):
        canvas = self._canvases["c5"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        kcs  = [k for k in self._data if k not in ("Total AH Gunsar", "__stats__")]
        data = []
        for kc in kcs:
            for r in _get_rows(self._data[kc]):
                if "total dpk" in r.get("label", "").lower():
                    v = list(r.get("values", {}).values())
                    data.append((kc, abs(v[-1]) / 1e6 if v else 0))
                    break

        if not data:
            ax.text(0.5, 0.5, "Tidak ada data",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
            canvas.fig.tight_layout()
            canvas.draw()
            return

        data.sort(key=lambda x: x[1])
        names, vals = zip(*data)
        short = [n.replace("KC Jakarta", "Jkt").replace("KC ", "")[:12] for n in names]

        # Gradient warna biru
        n = len(vals)
        grad_colors = [PALETTE[min(i, len(PALETTE) - 1)] for i in range(n)]

        bars = ax.barh(short, vals, color=grad_colors)
        ax.set_xlabel("Miliar Rp", fontsize=9)
        ax.tick_params(axis="y", labelsize=7)
        ax.tick_params(axis="x", labelsize=8)
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

        canvas.fig.tight_layout()
        canvas.draw()

    # ── CHART 6: Tren per KC ─────────────────────────────────────
    def _draw_c6_tren_kc(self):
        canvas = self._canvases["c6"]
        canvas.fig.clear()
        ax = canvas.fig.add_subplot(111)

        sample   = next(iter(self._data.values()), {})
        periodes = sample.get("periode_list", [])
        kcs      = [k for k in self._data if k not in ("Total AH Gunsar", "__stats__")][:6]

        if not periodes or not kcs:
            ax.text(0.5, 0.5, "Tidak ada data",
                    ha="center", va="center", transform=ax.transAxes, color="#94A3B8")
            canvas.fig.tight_layout()
            canvas.draw()
            return

        plotted = False
        for i, kc in enumerate(kcs):
            vals = []
            for r in _get_rows(self._data[kc]):
                if "total dpk" in r.get("label", "").lower():
                    vals = [r["values"].get(p, 0) / 1e6 for p in periodes]
                    break
            if vals:
                short = kc.replace("KC Jakarta", "Jkt").replace("KC ", "")[:10]
                ax.plot(periodes, vals, color=PALETTE[i % len(PALETTE)],
                        linewidth=1.5, marker="o", markersize=3, label=short)
                plotted = True

        if plotted:
            ax.legend(fontsize=7, loc="upper left")
        ax.set_ylabel("Miliar Rp", fontsize=9)
        ax.tick_params(axis="x", rotation=30, labelsize=7)
        ax.tick_params(axis="y", labelsize=8)
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        ax.spines[["top", "right"]].set_visible(False)

        canvas.fig.tight_layout()
        canvas.draw()