"""
exporter.py — Export hasil proses ke format Excel template Dashboard AH Gunsar.

Struktur sheet:
  2 baris info (judul + tanggal export)
  2 baris header (grup + detail)
  N baris data (template FIXED)

Kolom:
  Mata Anggaran | POSISI (per periode) | RKA | Pencp RKA % | GROWTH (MTD|DTD|YOY|YTD)

Freeze panes: B5 (2 baris info + 2 baris header)
"""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import CellIsRule
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.worksheet.datavalidation import DataValidation

from core.file_reader import BULAN_PANJANG, BULAN_SINGKAT


# ────────────────────────────────────────────────────────────────────
# STYLE HELPERS
# ────────────────────────────────────────────────────────────────────
def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color.lstrip("#"))

def get_default_export_filename(data: dict, kc_name: str = "AH Gunsar") -> str:
    date_str = ""
    try:
        kc_data = data.get(kc_name)
        if not kc_data:
            kc_data = data.get("Total AH Gunsar")
        if not kc_data:
            kc_data = next(iter(data.values()))
            
        rows = kc_data.get("rows", [])
        meta_row = next((r for r in rows if r.get('row_type') == '__metadata__'), None)
        if meta_row:
            terbaru_dt = meta_row['periode_refs']['terbaru']
            from core.file_reader import BULAN_PANJANG
            if terbaru_dt:
                date_str = f" {terbaru_dt.day} {BULAN_PANJANG[terbaru_dt.month]} {terbaru_dt.year}"
    except Exception:
        pass
        
    base_name = f"Dashboard {kc_name}{date_str}.xlsx"
    if kc_name == "AH Gunsar":
        # Specific naming for Export All as requested
        base_name = f"Dashboard AH Gunsar{date_str}.xlsx"
        
    return base_name

def get_unique_path(base_path: str) -> str:
    import os
    if not os.path.exists(base_path):
        return base_path
        
    name, ext = os.path.splitext(base_path)
    counter = 1
    while True:
        new_path = f"{name} ({counter}){ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def _font(bold=False, italic=False, size=10,
          color="1E293B", name="Arial") -> Font:
    return Font(name=name, bold=bold, italic=italic, size=size,
                color=color.lstrip("#"))


def _align(h="center", v="center", wrap=False, indent=0) -> Alignment:
    return Alignment(horizontal=h, vertical=v, wrap_text=wrap,
                     indent=indent)


def _border(style="thin", color="E2E8F0") -> Border:
    s = Side(style=style, color=color.lstrip("#"))
    return Border(left=s, right=s, top=s, bottom=s)


def _border_bottom_medium() -> Border:
    thin = Side(style="thin", color="E2E8F0")
    med = Side(style="medium", color="1E3A5F")
    return Border(left=thin, right=thin, top=thin, bottom=med)


_NO_BORDER = Border()


# Warna
CLR_HEADER_BG     = "1E3A5F"
CLR_HEADER2_BG    = "2563EB"
CLR_HEADER_FONT   = "FFFFFF"
CLR_SECTION_BG    = "DBEAFE"    # Header seksi (biru muda)
CLR_BOLD_BG       = "EFF6FF"    # Bold label
CLR_SEPARATOR_BG  = "1E3A5F"    # Separator biru solid
CLR_ROW_A         = "FFFFFF"
CLR_ROW_B         = "F8FAFC"
CLR_RKA_BG        = "E2E8F0"    # Abu muda sesuai mockup
CLR_PENCAP_BG     = "E2E8F0"    # Abu muda sesuai mockup
CLR_NEG_FONT      = "DC2626"
CLR_POS_FONT      = "1E293B"
CLR_ZERO_FONT     = "94A3B8"
CLR_INFO_BG       = "1E3A5F"
CLR_INFO2_BG      = "EFF6FF"
# ────────────────────────────────────────────────────────────────────
# DASHBOARD VISUALISASI
# ────────────────────────────────────────────────────────────────────
def style_header(ws, metadata):
    from openpyxl.styles import Font, PatternFill, Alignment
    # Baris 1: Judul utama
    ws.merge_cells('B1:U1')
    cell = ws['B1']
    cell.value = "DASHBOARD TABUNGAN, GIRO & DEPOSITO"
    cell.font = Font(name='Calibri', size=18, bold=True, color='FFFFFF')
    cell.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 32

    # Baris 2: Sub info
    ws.merge_cells('B2:U2')
    cell2 = ws['B2']
    tanggal_terbaru = metadata.get('tanggal_terbaru', '')
    jam = metadata.get('jam', '')
    cell2.value = f"Data per {tanggal_terbaru} {jam} WIB"
    cell2.font = Font(name='Calibri', size=11, italic=True, color='FFFFFF')
    cell2.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
    cell2.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[2].height = 22

    # Baris 3: spacer kosong, tinggi kecil
    ws.row_dimensions[3].height = 8

def get_total_ah_gunsar_value(data_dict, kategori, sub, periode):
    total_data = data_dict.get("Total AH Gunsar")
    if not total_data or "rows" not in total_data:
        return 0
    
    kat_map = {'dpk': 'Dana Pihak Ketiga', 'pinjaman': 'Pinjaman'}
    section = kat_map.get(kategori, kategori)
    
def get_value_safe(data, *keys, default=None, label=""):
    '''
    Ambil nilai nested dari dict dengan path keys.
    Jika gagal di tengah jalan, PRINT WARNING dengan jelas
    key mana yang tidak ditemukan, agar mudah di-debug.
    '''
    current = data
    path_so_far = []
    for key in keys:
        path_so_far.append(str(key))
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            print(f"[MISSING FIELD] {label}: path "
                  f"{' -> '.join(path_so_far)} TIDAK DITEMUKAN. "
                  f"Keys yang tersedia di level ini: "
                  f"{list(current.keys()) if isinstance(current, dict) else 'BUKAN DICT'}")
            return default
    return current if current is not None else default

def get_total_ah_gunsar_value(data_dict, kategori, sub, periode):
    # This function is not useful anymore because the original data dict is actually flattened with "rows"
    # We will just rewrite this to use get_val_helper which actually loops through rows
    # The actual keys in data_dict are: 'Total AH Gunsar', 'Tanah Abang', dll
    # Each has keys: 'periode_list', 'rows'
    
    # We are supposed to print diagnostic but we'll adapt getting values.
    # Actually, the user asked to print diagnostic directly in build_dashboard_visual
    pass

def get_valid_kc_list(data_dict):
    excluded = {"Total AH Gunsar"}
    valid_kc = []
    for key in data_dict.keys():
        if key in excluded:
            continue
        if key.startswith('_'):  
            continue
        if not isinstance(data_dict[key], dict):
            continue
        if 'rows' not in data_dict[key]:
            continue
        valid_kc.append(key)
    return valid_kc

def get_val_helper(data_dict, kc, section, label, periode, key='values'):
    kc_data = data_dict.get(kc)
    if not kc_data or "rows" not in kc_data: return None
    curr_sec = ""
    for r in kc_data["rows"]:
        rt = r.get("row_type", "")
        lbl = r.get("label", "")
        if rt in ("header", "header_value") or (rt == "bold" and lbl in ("SML", "NPL", "Recovery. EC")):
            curr_sec = lbl
        if curr_sec == section and lbl == label:
            if key == 'values' and periode:
                val = r.get("values", {}).get(periode)
                return val if val is not None else None
            val = r.get(key)
            return val if val is not None else None
    return None

def get_periode_terbaru(data_dict):
    total_data = data_dict.get("Total AH Gunsar")
    if not total_data: return None
    periode_list = total_data.get("periode_list", [])
    return periode_list[-1] if periode_list else None


def build_kpi_cards(ws, data_dict, periode_terbaru):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import column_index_from_string
    thin = Side(style='thin', color='E2E8F0')
    border = Border(top=thin, bottom=thin, left=thin, right=thin)

    dpk_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Dana Pihak Ketiga", periode_terbaru) or 0
    dpk_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "DPK Korporasi", periode_terbaru) or 0
    total_dpk = dpk_ritel + dpk_korp
    
    t_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Tabungan", periode_terbaru) or 0
    g_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Giro", periode_terbaru) or 0
    g_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "Giro", periode_terbaru) or 0
    d_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Deposito", periode_terbaru) or 0
    d_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "Deposito", periode_terbaru) or 0

    kpi_list = [
        ("TOTAL DANA PIHAK KETIGA (DPK)", total_dpk, 'B', 'F'),
        ("TABUNGAN", t_ritel, 'G', 'K'),
        ("GIRO", g_ritel + g_korp, 'L', 'P'),
        ("DEPOSITO", d_ritel + d_korp, 'Q', 'U'),
    ]

    for lbl, val, col_start, col_end in kpi_list:
        rng = f"{col_start}5:{col_end}5"
        ws.merge_cells(rng)
        c1 = ws[f"{col_start}5"]
        c1.value = lbl
        c1.font = Font(size=10, bold=True, color='1E3A8A')
        c1.alignment = Alignment(horizontal='center')

        rng2 = f"{col_start}6:{col_end}7"
        ws.merge_cells(rng2)
        c2 = ws[f"{col_start}6"]
        c2.value = f"{val:,.0f}".replace(',', '.')
        c2.font = Font(size=20, bold=True, color='1E3A8A')
        c2.alignment = Alignment(horizontal='center', vertical='center')

        rng3 = f"{col_start}8:{col_end}8"
        ws.merge_cells(rng3)
        c3 = ws[f"{col_start}8"]
        c3.value = f"Per {periode_terbaru}"
        c3.font = Font(size=9, italic=True, color='64748B')
        c3.alignment = Alignment(horizontal='center')

        for row in range(5, 9):
            for col_idx in range(column_index_from_string(col_start), column_index_from_string(col_end) + 1):
                ws.cell(row=row, column=col_idx).border = border

    ws.row_dimensions[5].height = 18; ws.row_dimensions[6].height = 26
    ws.row_dimensions[7].height = 8; ws.row_dimensions[8].height = 16


def write_chart_data(ws, data_dict, periode_terbaru):
    kc_list = get_valid_kc_list(data_dict)
    
    metrics = []
    for kc in kc_list:
        mtd_ritel = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Dana Pihak Ketiga", None, key='mtd') or 0
        mtd_korp = get_val_helper(data_dict, kc, "DPK Korporasi", "DPK Korporasi", None, key='mtd') or 0
        mtd_dpk = (mtd_ritel + mtd_korp) / 1000
        
        t_mtd = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Tabungan", None, key='mtd') or 0
        mtd_tab = t_mtd / 1000
        
        g_mtd_r = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Giro", None, key='mtd') or 0
        g_mtd_k = get_val_helper(data_dict, kc, "DPK Korporasi", "Giro", None, key='mtd') or 0
        mtd_gir = (g_mtd_r + g_mtd_k) / 1000
        
        d_mtd_r = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Deposito", None, key='mtd') or 0
        d_mtd_k = get_val_helper(data_dict, kc, "DPK Korporasi", "Deposito", None, key='mtd') or 0
        mtd_dep = (d_mtd_r + d_mtd_k) / 1000
        
        ytd_ritel = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Dana Pihak Ketiga", None, key='ytd') or 0
        ytd_korp = get_val_helper(data_dict, kc, "DPK Korporasi", "DPK Korporasi", None, key='ytd') or 0
        ytd_dpk = (ytd_ritel + ytd_korp) / 1000
        
        t_ytd = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Tabungan", None, key='ytd') or 0
        ytd_tab = t_ytd / 1000
        
        g_ytd_r = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Giro", None, key='ytd') or 0
        g_ytd_k = get_val_helper(data_dict, kc, "DPK Korporasi", "Giro", None, key='ytd') or 0
        ytd_gir = (g_ytd_r + g_ytd_k) / 1000
        
        d_ytd_r = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Deposito", None, key='ytd') or 0
        d_ytd_k = get_val_helper(data_dict, kc, "DPK Korporasi", "Deposito", None, key='ytd') or 0
        ytd_dep = (d_ytd_r + d_ytd_k) / 1000
        
        metrics.append({
            'kc': kc, 
            'mtd_dpk': int(round(mtd_dpk, 0)), 
            'mtd_tab': int(round(mtd_tab, 0)), 
            'mtd_gir': int(round(mtd_gir, 0)), 
            'mtd_dep': int(round(mtd_dep, 0)),
            'ytd_dpk': int(round(ytd_dpk, 0)), 
            'ytd_tab': int(round(ytd_tab, 0)), 
            'ytd_gir': int(round(ytd_gir, 0)), 
            'ytd_dep': int(round(ytd_dep, 0))
        })
        
    def write_sorted_full(ws, start_col, key_val):
        s = sorted(metrics, key=lambda x: x[key_val])
        s = list(reversed(s))
            
        ws.cell(row=1, column=start_col).value = "KC"
        ws.cell(row=1, column=start_col+1).value = key_val
        for i, m in enumerate(s, start=2):
            ws.cell(row=i, column=start_col).value = m['kc']
            ws.cell(row=i, column=start_col+1).value = m[key_val]

    # MTD
    write_sorted_full(ws, 23, 'mtd_dpk')
    write_sorted_full(ws, 25, 'mtd_tab')
    write_sorted_full(ws, 27, 'mtd_gir')
    write_sorted_full(ws, 29, 'mtd_dep')

    # YTD
    write_sorted_full(ws, 31, 'ytd_dpk')
    write_sorted_full(ws, 33, 'ytd_tab')
    write_sorted_full(ws, 35, 'ytd_gir')
    write_sorted_full(ws, 37, 'ytd_dep')
    
    return {
        'metrics': metrics,
        'kc_count': len(metrics)
    }


def build_all_charts(ws, chart_meta, periode_terbaru):
    from openpyxl.chart import BarChart, Reference, Series
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.drawing.line import LineProperties
    from openpyxl.styles import Font, PatternFill
    
    kc_count = chart_meta['kc_count']

    for row, lbl, fill_col in [(10, "PERFORMA MTD (JUNI 2026)", "1E3A8A"), 
                               (26, "PERFORMA YTD (1 JAN - 28 JUN 2026)", "1E3A8A")]:
        ws.merge_cells(f'B{row}:U{row}')
        c = ws[f'B{row}']
        c.value = lbl
        c.font = Font(bold=True, color='FFFFFF', size=11)
        c.fill = PatternFill(start_color=fill_col, end_color=fill_col, fill_type='solid')

    def make_chart_header(title, col_start, col_end, row):
        ws.merge_cells(f'{col_start}{row}:{col_end}{row}')
        c = ws[f'{col_start}{row}']
        c.value = title
        c.font = Font(bold=True, color='FFFFFF', size=10)
        c.fill = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid')
        c.alignment = Alignment(horizontal='center', vertical='center')

    # MTD Headers
    make_chart_header("DANA PIHAK KETIGA (Rp Miliar)", 'B', 'F', 11)
    make_chart_header("TABUNGAN (Rp Miliar)", 'G', 'K', 11)
    make_chart_header("GIRO (Rp Miliar)", 'L', 'P', 11)
    make_chart_header("DEPOSITO (Rp Miliar)", 'Q', 'U', 11)

    # YTD Headers
    make_chart_header("DANA PIHAK KETIGA (Rp Miliar)", 'B', 'F', 27)
    make_chart_header("TABUNGAN (Rp Miliar)", 'G', 'K', 27)
    make_chart_header("GIRO (Rp Miliar)", 'L', 'P', 27)
    make_chart_header("DEPOSITO (Rp Miliar)", 'Q', 'U', 27)

    def make_horizontal_bar_chart(col_start, col_data_start, row_start, bar_color):
        c = BarChart()
        c.type = "bar" 
        c.title = None
        c.height = 6.8
        c.width = 8.8
        c.visible_cells_only = False
        
        c.legend = None
        c.gapWidth = 50
        
        cats = Reference(ws, min_col=col_data_start, min_row=2, max_row=1+kc_count)
        data = Reference(ws, min_col=col_data_start+1, min_row=1, max_row=1+kc_count)
        
        c.add_data(data, titles_from_data=True)
        c.set_categories(cats)
        c.y_axis.numFmt = '#,##0'
        
        # Disable major gridlines on value axis for cleaner look
        c.y_axis.majorGridlines = None
        
        # Ensure category labels stay on left and don't overlap with negative bars
        c.x_axis.tickLblPos = "low"
        
        if c.series:
            c.series[0].graphicalProperties.solidFill = bar_color
            c.series[0].dLbls = DataLabelList()
            c.series[0].dLbls.showVal = True
            c.series[0].dLbls.showCatName = False
            c.series[0].dLbls.showSerName = False
            c.series[0].dLbls.showLegendKey = False
            c.series[0].dLbls.showPercent = False
                
        ws.add_chart(c, f"{col_start}{row_start}")

    # Colors: DPK (Navy), Tabungan (Blue), Giro (Orange), Deposito (Green)
    C_DPK = "1E3A8A"; C_TAB = "2563EB"; C_GIR = "F59E0B"; C_DEP = "10B981"

    make_horizontal_bar_chart("B", 23, 12, C_DPK)
    make_horizontal_bar_chart("G", 25, 12, C_TAB)
    make_horizontal_bar_chart("L", 27, 12, C_GIR)
    make_horizontal_bar_chart("Q", 29, 12, C_DEP)

    make_horizontal_bar_chart("B", 31, 28, C_DPK)
    make_horizontal_bar_chart("G", 33, 28, C_TAB)
    make_horizontal_bar_chart("L", 35, 28, C_GIR)
    make_horizontal_bar_chart("Q", 37, 28, C_DEP)


def build_summary_table(ws, data_dict, periode_terbaru, chart_meta):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    metrics = chart_meta['metrics']
    start_row = 43
    thin = Side(style='thin', color='E2E8F0')
    border = Border(top=thin, bottom=thin, left=thin, right=thin)

    ws.merge_cells(f'B{start_row}:U{start_row}')
    title_cell = ws[f'B{start_row}']
    title_cell.value = "DETAIL PENURUNAN DPK PER KC (Rp Miliar)"
    title_cell.font = Font(size=12, bold=True, color='1E3A8A')
    
    header_row1 = start_row + 1
    header_row2 = start_row + 2
    
    ws.merge_cells(f'B{header_row1}:B{header_row2}'); ws[f'B{header_row1}'] = "No"
    ws.merge_cells(f'C{header_row1}:E{header_row2}'); ws[f'C{header_row1}'] = "Nama KC"
    
    ws.merge_cells(f'F{header_row1}:I{header_row1}'); ws[f'F{header_row1}'] = "DANA PIHAK KETIGA (DPK)"
    ws.merge_cells(f'J{header_row1}:M{header_row1}'); ws[f'J{header_row1}'] = "TABUNGAN"
    ws.merge_cells(f'N{header_row1}:Q{header_row1}'); ws[f'N{header_row1}'] = "GIRO"
    ws.merge_cells(f'R{header_row1}:U{header_row1}'); ws[f'R{header_row1}'] = "DEPOSITO"
    
    col_idx = 6
    for _ in range(4): 
        ws.merge_cells(f'{get_column_letter(col_idx)}{header_row2}:{get_column_letter(col_idx+1)}{header_row2}')
        ws[f'{get_column_letter(col_idx)}{header_row2}'] = "MTD"
        ws.merge_cells(f'{get_column_letter(col_idx+2)}{header_row2}:{get_column_letter(col_idx+3)}{header_row2}')
        ws[f'{get_column_letter(col_idx+2)}{header_row2}'] = "YTD"
        col_idx += 4

    for r in [header_row1, header_row2]:
        for c in range(2, 22):
            cell = ws.cell(row=r, column=c)
            cell.font = Font(bold=True, color='FFFFFF', size=10)
            cell.fill = PatternFill(start_color='1E3A8A', end_color='1E3A8A', fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = border
            
    row = header_row2 + 1
    metrics.sort(key=lambda x: x['kc'])
    
    for i, m in enumerate(metrics, start=1):
        ws.cell(row=row, column=2).value = i
        ws.merge_cells(f'C{row}:E{row}'); ws.cell(row=row, column=3).value = m['kc']
        
        vals = [
            m['mtd_dpk'], m['ytd_dpk'], 
            m['mtd_tab'], m['ytd_tab'],
            m['mtd_gir'], m['ytd_gir'],
            m['mtd_dep'], m['ytd_dep']
        ]
        
        c_idx = 6
        for v in vals:
            ws.merge_cells(f'{get_column_letter(c_idx)}{row}:{get_column_letter(c_idx+1)}{row}')
            c = ws.cell(row=row, column=c_idx)
            c.value = v
            c.number_format = '#,##0.00'
            c_idx += 2
            
        for c in range(2, 22):
            cell = ws.cell(row=row, column=c)
            cell.border = border
            cell.alignment = Alignment(horizontal='center', vertical='center')
            if row % 2 == 0:
                cell.fill = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')
                
        row += 1
    return row

def hide_support_columns(ws):
    from openpyxl.utils import get_column_letter
    for col_idx in range(23, 40):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].hidden = True

def build_dashboard_visual(ws, data_dict, metadata=None):
    from openpyxl.styles import Font, PatternFill, Alignment
    
    if metadata is None: metadata = {'tanggal_terbaru': '', 'jam': ''}
        
    periode_terbaru = get_periode_terbaru(data_dict)
    
    print("\n" + "="*60)
    print("[DIAGNOSTIC] MEMULAI PEMBUATAN DASHBOARD")
    print(f"Periode Terbaru: {periode_terbaru}")
    print(f"Keys data_dict: {list(data_dict.keys())}")
    print("="*60)

    ws.column_dimensions['A'].width = 2
    for col in 'BCDEFGHIJKLMNOPQRSTU':
        ws.column_dimensions[col].width = 11

    style_header(ws, metadata)
    build_kpi_cards(ws, data_dict, periode_terbaru)
    chart_meta = write_chart_data(ws, data_dict, periode_terbaru)
    build_all_charts(ws, chart_meta, periode_terbaru)
    
    summary_end_row = build_summary_table(ws, data_dict, periode_terbaru, chart_meta)
    hide_support_columns(ws)

    footer_row = summary_end_row + 2
    ws.merge_cells(f'B{footer_row}:U{footer_row}')
    footer_cell = ws[f'B{footer_row}']
    footer_cell.value = "Catatan: Data bersifat rahasia dan hanya untuk penggunaan internal."
    footer_cell.font = Font(size=9, italic=True, color='FFFFFF')
    footer_cell.fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    footer_cell.alignment = Alignment(horizontal='center')

    ws.sheet_view.showGridLines = False

    assert ws.max_row >= 40, "Dashboard terlalu pendek, kemungkinan ada yang gagal"
    print(f"[SUCCESS] Dashboard sheet berhasil dibuat dengan {ws.max_row} baris")




# ────────────────────────────────────────────────────────────────────
# EXPORT UTAMA
# ────────────────────────────────────────────────────────────────────
def export_to_excel(data_dict: dict,
                    output_path: str,
                    tanggal_data: str = "") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    
    # ====== KODE BARU — TAMBAHKAN INI ======
    ws_dashboard = wb.active
    ws_dashboard.title = "Dashboard"
    
    total_ah_gunsar = data_dict.get("Total AH Gunsar", {})
    build_dashboard_visual(ws_dashboard, data_dict, metadata=None)
    # ====== AKHIR KODE BARU ======

    # Urutan sheet sesuai spesifikasi
    kc_order = [
        'Tanah Abang', 'Krekot', 'Veteran', 'Roxi',
        'Gunung Sahari', 'Mangga Dua', 'Kemayoran',
    ]

    for kc_name in kc_order:
        if kc_name in data_dict:
            kc_data = data_dict[kc_name]
            ws = wb.create_sheet(title=kc_name[:31])
            _write_sheet(ws, kc_name, kc_data)

    if "Total AH Gunsar" in data_dict:
        ws = wb.create_sheet(title="Total AH Gunsar")
        _write_sheet(ws, "Total AH Gunsar", data_dict["Total AH Gunsar"])

    try:
        wb.save(str(out))
    except Exception as e:
        raise RuntimeError(f"Gagal menyimpan file Excel: {e}") from e

    return out


# ────────────────────────────────────────────────────────────────────
# TULIS SATU SHEET
# ────────────────────────────────────────────────────────────────────
def _write_sheet(ws, kc_name: str, kc_data: dict) -> None:
    periode_list = kc_data.get("periode_list", [])
    rows_data    = kc_data.get("rows", [])
    mtd_label    = kc_data.get("mtd_label", "MTD")
    dtd_label    = kc_data.get("dtd_label", "DTD")
    yoy_label    = kc_data.get("yoy_label", "YOY")
    ytd_label    = kc_data.get("ytd_label", "YTD")

    n_periode = len(periode_list)

    # Kolom layout
    COL_MATA      = 1
    COL_POS_START = 2
    COL_POS_END   = max(COL_POS_START, COL_POS_START + n_periode - 1)
    COL_RKA_START = COL_POS_END + 1
    COL_RKA_END   = COL_RKA_START + 11
    COL_PENCAP    = COL_RKA_END + 1
    COL_MTD       = COL_PENCAP + 1
    COL_DTD       = COL_MTD + 1
    COL_YOY       = COL_DTD + 1
    COL_YTD       = COL_YOY + 1
    LAST_COL      = COL_YTD

    # ══════════════════════════════════════════════════════════════
    # BARIS 1-2: INFO EXPORT
    # ══════════════════════════════════════════════════════════════
    now = datetime.now()
    HARI_ID = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
    hari_str = HARI_ID[now.weekday()]
    tgl_str = f"{now.day} {BULAN_PANJANG[now.month]} {now.year}"
    jam_str = now.strftime("%H:%M") + " WIB"
    export_info = f"Diekspor pada: {tgl_str} {hari_str}, {jam_str}"

    # Baris 1: Judul
    for ci in range(1, LAST_COL + 1):
        c = ws.cell(row=1, column=ci,
                    value=f"Dashboard SSA — Bank BRI AH Gunsar Jakarta Region ({kc_name})"
                    if ci == 1 else "")
        c.fill = _fill(CLR_INFO_BG)
        c.font = _font(bold=True, size=13, color=CLR_HEADER_FONT)
        c.alignment = _align(h="center", v="center")

    if LAST_COL > 1:
        ws.merge_cells(start_row=1, start_column=1,
                       end_row=1, end_column=LAST_COL)
    ws.row_dimensions[1].height = 28

    # Baris 2: Tanggal export
    for ci in range(1, LAST_COL + 1):
        c = ws.cell(row=2, column=ci,
                    value=export_info if ci == 1 else "")
        c.fill = _fill(CLR_INFO2_BG)
        c.font = _font(italic=True, size=10, color="64748B")
        c.alignment = _align(h="center", v="center")

    if LAST_COL > 1:
        ws.merge_cells(start_row=2, start_column=1,
                       end_row=2, end_column=LAST_COL)
    ws.row_dimensions[2].height = 22

    # ══════════════════════════════════════════════════════════════
    # BARIS 3-4: HEADER TABEL
    # ══════════════════════════════════════════════════════════════
    HDR_ROW1 = 3
    HDR_ROW2 = 4

    header_fill = _fill(CLR_HEADER_BG)
    header_font = _font(bold=True, size=11, color=CLR_HEADER_FONT)
    header_align = _align(h="center", v="center", wrap=True)
    header_bdr = _border("medium", "1E3A5F")

    header2_fill = _fill(CLR_HEADER2_BG)
    header2_font = _font(bold=True, size=10, color=CLR_HEADER_FONT)
    header2_align = _align(h="center", v="center", wrap=True)

    # A3: "Mata Anggaran" (merge A3:A4)
    for r in [HDR_ROW1, HDR_ROW2]:
        c = ws.cell(row=r, column=COL_MATA,
                    value="Mata Anggaran" if r == HDR_ROW1 else "")
        c.fill = header_fill
        c.font = header_font
        c.alignment = header_align
        c.border = header_bdr

    # Posisi header grup (baris 3)
    for ci in range(COL_POS_START, COL_POS_END + 1):
        c = ws.cell(row=HDR_ROW1, column=ci,
                    value="Posisi" if ci == COL_POS_START else "")
        c.fill = header_fill
        c.font = header_font
        c.alignment = header_align
        c.border = header_bdr

    # Posisi detail (baris 4) — label periode
    for i, lbl in enumerate(periode_list):
        c = ws.cell(row=HDR_ROW2, column=COL_POS_START + i, value=lbl)
        c.fill = header2_fill
        c.font = header2_font
        c.alignment = header2_align
        c.border = header_bdr

    # RKA header (merge baris 3)
    rka_tahun = now.year
    rka_bulan_terakhir_idx = 0
    if periode_list:
        lbl = periode_list[-1]
        parts = lbl.split('-')
        if len(parts) >= 2:
            thn_str = parts[-1]
            bln_str = parts[0].lower()
            try:
                rka_tahun = int("20" + thn_str) if len(thn_str) == 2 else int(thn_str)
            except: pass
            
            from ui.input_rka_widget import MONTHS_MAP
            for i, (k, v) in enumerate(MONTHS_MAP.items()):
                if k in bln_str:
                    rka_bulan_terakhir_idx = i
                    break

    # RKA Header Row 3
    c = ws.cell(row=HDR_ROW1, column=COL_RKA_START, value="RKA")
    c.fill = header_fill
    c.font = header_font
    c.alignment = header_align
    c.border = header_bdr
    
    for ci in range(COL_RKA_START + 1, COL_RKA_END + 1):
        c2 = ws.cell(row=HDR_ROW1, column=ci, value="")
        c2.border = header_bdr
        c2.fill = header_fill

    # RKA Header Row 4 (12 Bulan)
    bulan_singkat_rka = ["Januari", "Februari", "Maret", "Apr", "Mei", "Juni", "Juli", "Ags", "Sep", "Okt", "Nov", "Des"]
    for i in range(12):
        c = ws.cell(row=HDR_ROW2, column=COL_RKA_START + i, value=f"{bulan_singkat_rka[i]}-{str(rka_tahun)[-2:]}")
        c.fill = header2_fill
        c.font = header2_font
        c.alignment = header2_align
        c.border = header_bdr

    # Pencapaian RKA header (merge baris 3-4)
    pencap_label = f"{BULAN_SINGKAT[now.month]}-{str(now.year)[-2:]}"
    for r in [HDR_ROW1, HDR_ROW2]:
        c = ws.cell(row=r, column=COL_PENCAP,
                    value="Pencp RKA %" if r == HDR_ROW1 else pencap_label)
        c.fill = header_fill
        c.font = header_font
        c.alignment = header_align
        c.border = header_bdr

    # Growth header grup (baris 3)
    for ci in range(COL_MTD, COL_YTD + 1):
        c = ws.cell(row=HDR_ROW1, column=ci,
                    value="Growth" if ci == COL_MTD else "")
        c.fill = header_fill
        c.font = header_font
        c.alignment = header_align
        c.border = header_bdr

    # Growth detail (baris 4)
    for col, lbl in [(COL_MTD, mtd_label), (COL_DTD, dtd_label),
                     (COL_YOY, yoy_label), (COL_YTD, ytd_label)]:
        c = ws.cell(row=HDR_ROW2, column=col, value=lbl)
        c.fill = header2_fill
        c.font = header2_font
        c.alignment = header2_align
        c.border = header_bdr

    # ── MERGE CELLS ──────────────────────────────────────────────
    ws.merge_cells(start_row=HDR_ROW1, start_column=COL_MATA,
                   end_row=HDR_ROW2, end_column=COL_MATA)

    if n_periode > 1:
        ws.merge_cells(start_row=HDR_ROW1, start_column=COL_POS_START,
                       end_row=HDR_ROW1, end_column=COL_POS_END)

    ws.merge_cells(start_row=HDR_ROW1, start_column=COL_RKA_START,
                   end_row=HDR_ROW1, end_column=COL_RKA_END)

    ws.merge_cells(start_row=HDR_ROW1, start_column=COL_PENCAP,
                   end_row=HDR_ROW2, end_column=COL_PENCAP)

    if COL_YTD > COL_MTD:
        ws.merge_cells(start_row=HDR_ROW1, start_column=COL_MTD,
                       end_row=HDR_ROW1, end_column=COL_YTD)

    ws.row_dimensions[HDR_ROW1].height = 28
    ws.row_dimensions[HDR_ROW2].height = 40

    # ══════════════════════════════════════════════════════════════
    # DATA ROWS (mulai baris 5)
    # ══════════════════════════════════════════════════════════════
    current_row = 5
    data_row_counter = 0  # untuk alternating colors

    # === FETCH RKA DATA ===
    from core.db_manager import get_connection
    conn = get_connection()
    conn.row_factory = __import__('sqlite3').Row
    cur = conn.cursor()
    
    rka_records_by_month = {}
    
    if kc_name == "Total AH Gunsar":
        cols = ["dpk_tabungan", "dpk_giro", "dpk_deposito", "dpk_casa", "korp_giro", "korp_deposito",
                "pinj_mikro", "pinj_small", "pinj_konsumer",
                "sml_mikro", "sml_small", "sml_konsumer", 
                "npl_mikro", "npl_small", "npl_konsumer",
                "rec_mikro", "rec_small", "rec_konsumer"]
        query = f"SELECT bulan, {', '.join(['SUM('+c+') as '+c for c in cols])} FROM rka_data_v2 WHERE tahun = ? GROUP BY bulan"
        cur.execute(query, (rka_tahun,))
        for row in cur.fetchall():
            if row[cols[0]] is not None:
                rka_records_by_month[row["bulan"]] = dict(row)
    else:
        kc_db_name = f"KC Jakarta {kc_name}"
        cur.execute("SELECT * FROM rka_data_v2 WHERE kc = ? AND tahun = ?", (kc_db_name, rka_tahun))
        for row in cur.fetchall():
            rka_records_by_month[row["bulan"]] = dict(row)
            
    conn.close()

    # Mapping logic
    def get_rka_vals(section, label):
        vals = [""] * 12
        if not rka_records_by_month: return vals
        
        mapping = {
            ("Dana Pihak Ketiga", "Dana Pihak Ketiga"): ["dpk_tabungan", "dpk_giro", "dpk_deposito"],
            ("Dana Pihak Ketiga", "Tabungan"): ["dpk_tabungan"],
            ("Dana Pihak Ketiga", "Giro"): ["dpk_giro"],
            ("Dana Pihak Ketiga", "Deposito"): ["dpk_deposito"],
            ("Dana Pihak Ketiga", "CASA"): ["dpk_tabungan", "dpk_giro"],
            
            ("DPK Korporasi", "DPK Korporasi"): ["korp_giro", "korp_deposito"],
            ("DPK Korporasi", "Giro"): ["korp_giro"],
            ("DPK Korporasi", "Deposito"): ["korp_deposito"],
            
            ("Pinjaman", "Pinjaman"): ["pinj_mikro", "pinj_small", "pinj_konsumer"],
            ("Pinjaman", "Mikro"): ["pinj_mikro"],
            ("Pinjaman", "Small"): ["pinj_small"],
            ("Pinjaman", "Konsumer"): ["pinj_konsumer"],
            ("Pinjaman", "Konsumer - KPR"): ["pinj_kons_kpr"],
            ("Pinjaman", "Konsumer - Briguna Ritel"): ["pinj_kons_briguna"],
            
            ("SML", "SML"): ["sml_mikro", "sml_small", "sml_konsumer"],
            ("SML", "SML %"): ["sml_pct"],
            ("SML", "Mikro"): ["sml_mikro"],
            ("SML", "Mikro %"): ["sml_mikro_pct"],
            ("SML", "Small"): ["sml_small"],
            ("SML", "Small %"): ["sml_small_pct"],
            ("SML", "Konsumer"): ["sml_konsumer"],
            ("SML", "Konsumer %"): ["sml_konsumer_pct"],
            ("SML", "Konsumer - KPR"): ["sml_kons_kpr"],
            ("SML", "Konsumer - KPR %"): ["sml_kons_kpr_pct"],
            ("SML", "Konsumer - Briguna Ritel"): ["sml_kons_briguna"],
            ("SML", "Konsumer - Briguna Ritel %"): ["sml_kons_briguna_pct"],
            
            ("NPL", "NPL"): ["npl_mikro", "npl_small", "npl_konsumer"],
            ("NPL", "NPL %"): ["npl_pct"],
            ("NPL", "Mikro"): ["npl_mikro"],
            ("NPL", "Mikro %"): ["npl_mikro_pct"],
            ("NPL", "Small"): ["npl_small"],
            ("NPL", "Small %"): ["npl_small_pct"],
            ("NPL", "Konsumer"): ["npl_konsumer"],
            ("NPL", "Konsumer %"): ["npl_konsumer_pct"],
            ("NPL", "Konsumer - KPR"): ["npl_kons_kpr"],
            ("NPL", "Konsumer - KPR %"): ["npl_kons_kpr_pct"],
            ("NPL", "Konsumer - Briguna Ritel"): ["npl_kons_briguna"],
            ("NPL", "Konsumer - Briguna Ritel %"): ["npl_kons_briguna_pct"],
            
            ("Recovery. EC", "Recovery. EC"): ["rec_mikro", "rec_small", "rec_konsumer"],
            ("Recovery. EC", "Mikro"): ["rec_mikro"],
            ("Recovery. EC", "Small"): ["rec_small"],
            ("Recovery. EC", "Konsumer"): ["rec_konsumer"],
        }
        
        cols = mapping.get((section, label), [])
        if not cols: return vals
        if 'pct' in cols[0] and kc_name == "Total AH Gunsar": return vals
            
        from ui.input_rka_widget import MONTHS_MAP
        for i, (k, v) in enumerate(MONTHS_MAP.items()):
            rec = rka_records_by_month.get(v, {})
            if not rec:
                continue
            if 'pct' in cols[0]:
                if cols[0] == 'sml_pct':
                    num = sum(rec.get(c, 0) or 0 for c in ["sml_mikro", "sml_small", "sml_konsumer"])
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'sml_mikro_pct':
                    num = rec.get("sml_mikro", 0) or 0
                    den = rec.get("pinj_mikro", 0) or 0
                elif cols[0] == 'sml_small_pct':
                    num = rec.get("sml_small", 0) or 0
                    den = rec.get("pinj_small", 0) or 0
                elif cols[0] == 'sml_konsumer_pct':
                    num = rec.get("sml_konsumer", 0) or 0
                    den = rec.get("pinj_konsumer", 0) or 0
                elif cols[0] == 'sml_konsumer_kpr_pct':
                    num = rec.get("sml_konsumer_kpr", 0) or 0
                    den = rec.get("pinj_konsumer", 0) or 0
                elif cols[0] == 'sml_konsumer_briguna_pct':
                    num = rec.get("sml_konsumer_briguna", 0) or 0
                    den = rec.get("pinj_konsumer", 0) or 0
                elif cols[0] == 'npl_pct':
                    num = sum(rec.get(c, 0) or 0 for c in ["npl_mikro", "npl_small", "npl_konsumer"])
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'npl_mikro_pct':
                    num = rec.get("npl_mikro", 0) or 0
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'npl_small_pct':
                    num = rec.get("npl_small", 0) or 0
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'npl_konsumer_pct':
                    num = rec.get("npl_konsumer", 0) or 0
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'npl_konsumer_kpr_pct':
                    num = rec.get("npl_konsumer_kpr", 0) or 0
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                elif cols[0] == 'npl_konsumer_briguna_pct':
                    num = rec.get("npl_konsumer_briguna", 0) or 0
                    den = sum(rec.get(c, 0) or 0 for c in ["pinj_mikro", "pinj_small", "pinj_konsumer"])
                else:
                    num, den = 0, 1
                    
                vals[i] = num / den if den != 0 else 0.0
            else:
                vals[i] = sum(rec.get(c, 0) or 0 for c in cols)
        return vals

    current_section = ""

    for row_data in rows_data:
        row_type = row_data.get("row_type", "data")
        label = row_data.get("label", "")
        
        if row_type in ("header", "header_value") or (row_type == "bold" and label in ("SML", "NPL")):
            current_section = label
            
        rka_vals = get_rka_vals(current_section, label)

        if row_type == "separator":
            current_row = _write_separator(ws, current_row, LAST_COL)
        elif row_type == "header":
            current_row = _write_header_seksi(
                ws, current_row, row_data, periode_list,
                COL_MATA, COL_POS_START, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                COL_MTD, COL_DTD, COL_YOY, COL_YTD, LAST_COL)
        elif row_type == "header_value":
            current_row = _write_header_value(
                ws, current_row, row_data, rka_vals, periode_list,
                COL_MATA, COL_POS_START, COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                COL_MTD, COL_DTD, COL_YOY, COL_YTD, LAST_COL, rka_bulan_terakhir_idx)
        elif row_type == "bold":
            current_row = _write_bold_label(
                ws, current_row, row_data, rka_vals, periode_list,
                COL_MATA, COL_POS_START, COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                COL_MTD, COL_DTD, COL_YOY, COL_YTD, rka_bulan_terakhir_idx)
        else:
            current_row = _write_data_row(
                ws, current_row, row_data, rka_vals, periode_list,
                COL_MATA, COL_POS_START, COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                COL_MTD, COL_DTD, COL_YOY, COL_YTD,
                data_row_counter, rka_bulan_terakhir_idx)
            data_row_counter += 1

    # ── CONDITIONAL FORMATTING GROWTH ────────────────────────────
    if current_row > 6:
        for col in [COL_MTD, COL_DTD, COL_YOY, COL_YTD]:
            col_ltr = get_column_letter(col)
            cell_range = f"{col_ltr}5:{col_ltr}{current_row - 1}"
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="lessThan", formula=["0"],
                           font=Font(color=CLR_NEG_FONT)))
            ws.conditional_formatting.add(
                cell_range,
                CellIsRule(operator="equal", formula=["0"],
                           font=Font(color=CLR_ZERO_FONT)))

    # ── FREEZE PANES ─────────────────────────────────────────────
    ws.freeze_panes = ws.cell(row=5, column=COL_POS_START)

    # ── LEBAR KOLOM ──────────────────────────────────────────────
    ws.column_dimensions["A"].width = 22
    for i in range(n_periode):
        ws.column_dimensions[get_column_letter(COL_POS_START + i)].width = 13
    for i in range(12):
        ws.column_dimensions[get_column_letter(COL_RKA_START + i)].width = 13
    ws.column_dimensions[get_column_letter(COL_PENCAP)].width = 13
    ws.column_dimensions[get_column_letter(COL_MTD)].width = 17
    for col in [COL_DTD, COL_YOY, COL_YTD]:
        ws.column_dimensions[get_column_letter(col)].width = 11


# ────────────────────────────────────────────────────────────────────
# SEPARATOR — baris biru solid, height 6px
# ────────────────────────────────────────────────────────────────────
def _write_separator(ws, row: int, last_col: int) -> int:
    fill_obj = _fill(CLR_SEPARATOR_BG)
    for ci in range(1, last_col + 1):
        c = ws.cell(row=row, column=ci, value="")
        c.fill = fill_obj
    ws.row_dimensions[row].height = 6
    return row + 1


# ────────────────────────────────────────────────────────────────────
# HEADER SEKSI — "Dana Pihak Ketiga", "Pinjaman", "Recovery. EC"
# ────────────────────────────────────────────────────────────────────
def _write_header_seksi(ws, row: int, row_data: dict,
                        periode_list, COL_MATA, COL_POS_START,
                        COL_RKA_START, COL_RKA_END, COL_PENCAP,
                        COL_MTD, COL_DTD, COL_YOY, COL_YTD,
                        LAST_COL) -> int:
    label = row_data.get("label", "")
    fill_obj = _fill(CLR_SECTION_BG)
    font_obj = _font(bold=True, size=11, color="1E293B")
    bdr = _border_bottom_medium()
    alg = _align(h="left", v="center")

    for ci in range(1, LAST_COL + 1):
        c = ws.cell(row=row, column=ci,
                    value=label if ci == COL_MATA else "")
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = alg
        c.border = bdr

    ws.row_dimensions[row].height = 18
    return row + 1


# ────────────────────────────────────────────────────────────────────
# HEADER VALUE — Header seksi yang punya nilai (misal: "Pinjaman")
# ────────────────────────────────────────────────────────────────────
def _write_header_value(ws, row: int, row_data: dict, rka_vals: list,
                        periode_list, COL_MATA, COL_POS_START,
                        COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                        COL_MTD, COL_DTD, COL_YOY, COL_YTD,
                        LAST_COL, rka_bulan_idx: int) -> int:
    label = row_data.get("label", "")
    values = row_data.get("values", {})
    fill_obj = _fill(CLR_SECTION_BG)
    font_obj = _font(bold=True, size=11, color="1E293B")
    bdr = _border_bottom_medium()
    
    # Mata Anggaran
    c = ws.cell(row=row, column=COL_MATA, value=label)
    c.fill = fill_obj
    c.font = font_obj
    c.alignment = _align(h="left", v="center")
    c.border = bdr

    # Posisi per periode
    for i, lbl in enumerate(periode_list):
        val = values.get(lbl, 0)
        c = ws.cell(row=row, column=COL_POS_START + i)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # RKA
    for i in range(12):
        c = ws.cell(row=row, column=COL_RKA_START + i)
        val = rka_vals[i] if rka_vals else ""
        if val != "":
            try:
                c.value = float(val)
            except (ValueError, TypeError):
                c.value = val
        else:
            c.value = ""
        c.number_format = "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # Pencapaian RKA
    c = ws.cell(row=row, column=COL_PENCAP)
    label = row_data.get("label", "")
    
    from core.processor import hitung_pencapaian_rka
    val_terbaru = None
    if periode_list:
        terbaru_label = periode_list[-1]
        val_terbaru = row_data.get("values", {}).get(terbaru_label)
        
    val_rka = rka_vals[rka_bulan_idx] if rka_vals and rka_bulan_idx < len(rka_vals) else None
    
    try:
        val_terbaru = float(val_terbaru) if val_terbaru is not None else None
    except:
        val_terbaru = None
        
    try:
        val_rka = float(val_rka) if val_rka is not None else None
    except:
        val_rka = None
        
    pencap = hitung_pencapaian_rka(label, val_terbaru, val_rka)
    
    c.fill = fill_obj
    c.alignment = _align(h="right", v="center")
    c.border = bdr
    c.number_format = "0.00%"
    
    if pencap is not None:
        c.value = pencap
        if pencap >= 1.00:
            c.font = _font(color="16A34A") # Hijau
        elif pencap >= 0.80:
            c.font = _font(color="D97706") # Kuning
        else:
            c.font = _font(color="DC2626") # Merah
    else:
        c.value = ""
        c.font = font_obj

    # Growth (kalau ada)
    is_pct = '%' in label
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key)
        c = ws.cell(row=row, column=col)
        c.fill = fill_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr
        
        if val is None or val == "":
            c.value = ""
            c.font = font_obj
        else:
            try:
                num_val = float(val)
                c.value = num_val
                if is_pct:
                    c.number_format = "0.00%"
                else:
                    c.number_format = "#,##0;-#,##0;\"-\""
                    
                if num_val < 0:
                    c.font = _font(color="DC2626") # Merah
                else:
                    c.font = _font(color="1E293B") # Hitam
            except (ValueError, TypeError):
                c.value = val if val == "-" else ""
                c.font = font_obj

    ws.row_dimensions[row].height = 18
    return row + 1




# ────────────────────────────────────────────────────────────────────
# BOLD LABEL — "SML", "SML %", "NPL", "NPL %", "CASA"
# ────────────────────────────────────────────────────────────────────
def _write_bold_label(ws, row: int, row_data: dict, rka_vals: list,
                      periode_list, COL_MATA, COL_POS_START,
                      COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                      COL_MTD, COL_DTD, COL_YOY, COL_YTD, rka_bulan_idx: int) -> int:
    label = row_data.get("label", "")
    values = row_data.get("values", {})
    fill_obj = _fill(CLR_BOLD_BG)
    font_obj = _font(bold=True, size=10, color="1E293B")
    bdr = _border()

    is_pct = '%' in label

    # Mata Anggaran
    c = ws.cell(row=row, column=COL_MATA, value=label)
    c.fill = fill_obj
    c.font = font_obj
    c.alignment = _align(h="left", v="center")
    c.border = bdr

    # Posisi per periode
    for i, lbl in enumerate(periode_list):
        val = values.get(lbl, 0)
        c = ws.cell(row=row, column=COL_POS_START + i)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # RKA
    for i in range(12):
        c = ws.cell(row=row, column=COL_RKA_START + i)
        val = rka_vals[i] if rka_vals else ""
        if val != "":
            try:
                c.value = float(val)
            except (ValueError, TypeError):
                c.value = val
        else:
            c.value = ""
        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = _fill(CLR_RKA_BG)
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # Pencapaian RKA
    c = ws.cell(row=row, column=COL_PENCAP)
    
    from core.processor import hitung_pencapaian_rka
    val_terbaru = None
    if periode_list:
        terbaru_label = periode_list[-1]
        val_terbaru = row_data.get("values", {}).get(terbaru_label)
        
    val_rka = rka_vals[rka_bulan_idx] if rka_vals and rka_bulan_idx < len(rka_vals) else None
    
    try:
        val_terbaru = float(val_terbaru) if val_terbaru is not None else None
    except:
        val_terbaru = None
        
    try:
        val_rka = float(val_rka) if val_rka is not None else None
    except:
        val_rka = None
        
    pencap = hitung_pencapaian_rka(label, val_terbaru, val_rka)
    
    c.fill = _fill(CLR_PENCAP_BG)
    c.alignment = _align(h="right", v="center")
    c.border = bdr
    c.number_format = "0.00%"
    
    if pencap is not None:
        c.value = pencap
        if pencap >= 1.00:
            c.font = _font(bold=True, color="16A34A") # Hijau
        elif pencap >= 0.80:
            c.font = _font(bold=True, color="D97706") # Kuning
        else:
            c.font = _font(bold=True, color="DC2626") # Merah
    else:
        c.value = ""
        c.font = font_obj

    # Growth
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key)
        c = ws.cell(row=row, column=col)
        c.fill = fill_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr
        
        if val is None or val == "":
            c.value = ""
            c.font = font_obj
        else:
            try:
                num_val = float(val)
                c.value = num_val
                if is_pct:
                    c.number_format = "0.00%"
                else:
                    c.number_format = "#,##0;-#,##0;\"-\""
                    
                if num_val < 0:
                    c.font = _font(bold=True, color="DC2626") # Merah
                else:
                    c.font = font_obj # Hitam Bold
            except (ValueError, TypeError):
                c.value = val if val == "-" else ""
                c.font = font_obj

    ws.row_dimensions[row].height = 18
    return row + 1


# ────────────────────────────────────────────────────────────────────
# DATA ROW — baris data biasa
# ────────────────────────────────────────────────────────────────────
def _write_data_row(ws, row: int, row_data: dict, rka_vals: list,
                    periode_list, COL_MATA, COL_POS_START,
                    COL_POS_END, COL_RKA_START, COL_RKA_END, COL_PENCAP,
                    COL_MTD, COL_DTD, COL_YOY, COL_YTD,
                    counter: int, rka_bulan_idx: int) -> int:
    label = row_data.get("label", "")
    values = row_data.get("values", {})
    fill_obj = _fill(CLR_ROW_A if counter % 2 == 0 else CLR_ROW_B)
    font_obj = _font(size=10, color=CLR_POS_FONT)
    bdr = _border()

    is_pct = '%' in label

    # Mata Anggaran
    c = ws.cell(row=row, column=COL_MATA, value=label)
    c.fill = fill_obj
    c.font = font_obj
    c.alignment = _align(h="left", v="center", indent=1)
    c.border = bdr

    # Posisi per periode
    for i, lbl in enumerate(periode_list):
        val = values.get(lbl, 0)
        c = ws.cell(row=row, column=COL_POS_START + i)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # RKA
    for i in range(12):
        c = ws.cell(row=row, column=COL_RKA_START + i)
        val = rka_vals[i] if rka_vals else ""
        if val != "":
            try:
                c.value = float(val)
            except (ValueError, TypeError):
                c.value = val
        else:
            c.value = ""
        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = _fill(CLR_RKA_BG)
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

    # Pencapaian RKA
    c = ws.cell(row=row, column=COL_PENCAP)
    
    from core.processor import hitung_pencapaian_rka
    val_terbaru = None
    if periode_list:
        terbaru_label = periode_list[-1]
        val_terbaru = row_data.get("values", {}).get(terbaru_label)
        
    val_rka = rka_vals[rka_bulan_idx] if rka_vals and rka_bulan_idx < len(rka_vals) else None
    
    try:
        val_terbaru = float(val_terbaru) if val_terbaru is not None else None
    except:
        val_terbaru = None
        
    try:
        val_rka = float(val_rka) if val_rka is not None else None
    except:
        val_rka = None
        
    pencap = hitung_pencapaian_rka(label, val_terbaru, val_rka)
    
    c.fill = _fill(CLR_PENCAP_BG)
    c.alignment = _align(h="right", v="center")
    c.border = bdr
    c.number_format = "0.00%"
    
    if pencap is not None:
        c.value = pencap
        if pencap >= 1.00:
            c.font = _font(color="16A34A") # Hijau
        elif pencap >= 0.80:
            c.font = _font(color="D97706") # Kuning
        else:
            c.font = _font(color="DC2626") # Merah
    else:
        c.value = ""
        c.font = font_obj

    # Growth
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key)
        c = ws.cell(row=row, column=col)
        c.fill = fill_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr
        
        if val is None or val == "":
            c.value = ""
            c.font = font_obj
        else:
            try:
                num_val = float(val)
                c.value = num_val
                if is_pct:
                    c.number_format = "0.00%"
                else:
                    c.number_format = "#,##0;-#,##0;\"-\""
                    
                if num_val < 0:
                    c.font = _font(color="DC2626") # Merah
                else:
                    c.font = font_obj # Hitam (or default)
            except (ValueError, TypeError):
                c.value = val if val == "-" else ""
                c.font = font_obj

    ws.row_dimensions[row].height = 18
    return row + 1


# ────────────────────────────────────────────────────────────────────
# UTILITY
# ────────────────────────────────────────────────────────────────────
def get_file_size_str(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return "0 KB"
    sz = p.stat().st_size
    if sz < 1_048_576:
        return f"{sz / 1024:.0f} KB"
    return f"{sz / 1_048_576:.1f} MB"

