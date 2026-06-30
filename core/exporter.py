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
    ws.merge_cells('A1:T1')
    cell = ws['A1']
    cell.value = "DASHBOARD SSA — AH GUNSAR JAKARTA REGION"
    cell.font = Font(name='Calibri', size=18, bold=True, color='FFFFFF')
    cell.fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 32

    # Baris 2: Sub info
    ws.merge_cells('A2:T2')
    cell2 = ws['A2']
    tanggal_terbaru = metadata.get('tanggal_terbaru', '')
    jam = metadata.get('jam', '')
    cell2.value = f"Data per {tanggal_terbaru} {jam} WIB"
    cell2.font = Font(name='Calibri', size=11, italic=True, color='FFFFFF')
    cell2.fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
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
    
    total_pinjaman = get_val_helper(data_dict, "Total AH Gunsar", "Pinjaman", "Pinjaman", periode_terbaru) or 0
    jumlah_kc = len([k for k in data_dict.keys() if k != "Total AH Gunsar"])
    
    sml_pct = get_val_helper(data_dict, "Total AH Gunsar", "SML", "SML %", periode_terbaru) or 0
    npl_pct = get_val_helper(data_dict, "Total AH Gunsar", "NPL", "NPL %", periode_terbaru) or 0

    kpi_list = [
        ("TOTAL DPK (Rp Juta)", f"{total_dpk:,.0f}", "Ritel & Korporasi", 'A', 'E'),
        ("TOTAL PINJAMAN (Rp Juta)", f"{total_pinjaman:,.0f}", "Seluruh Segmen", 'F', 'J'),
        ("UNIT KERJA", f"{jumlah_kc}", "Kantor Cabang", 'K', 'N'),
        ("SML RATIO", f"{sml_pct*100:.2f}%", "Total AH Gunsar", 'O', 'Q'),
        ("NPL RATIO", f"{npl_pct*100:.2f}%", "Total AH Gunsar", 'R', 'T'),
    ]

    for label, value, sub, col_start, col_end in kpi_list:
        rng = f"{col_start}5:{col_end}5"
        ws.merge_cells(rng)
        c1 = ws[f"{col_start}5"]
        c1.value = label
        c1.font = Font(size=10, bold=True, color='64748B')
        c1.alignment = Alignment(horizontal='center')

        rng2 = f"{col_start}6:{col_end}7"
        ws.merge_cells(rng2)
        c2 = ws[f"{col_start}6"]
        c2.value = value
        c2.font = Font(size=20, bold=True, color='2563EB')
        c2.alignment = Alignment(horizontal='center', vertical='center')

        rng3 = f"{col_start}8:{col_end}8"
        ws.merge_cells(rng3)
        c3 = ws[f"{col_start}8"]
        c3.value = sub
        c3.font = Font(size=9, italic=True, color='94A3B8')
        c3.alignment = Alignment(horizontal='center')

        for row in range(5, 9):
            for col_idx in range(
                column_index_from_string(col_start),
                column_index_from_string(col_end) + 1
            ):
                ws.cell(row=row, column=col_idx).border = border

    ws.row_dimensions[5].height = 18
    ws.row_dimensions[6].height = 26
    ws.row_dimensions[7].height = 8
    ws.row_dimensions[8].height = 16


def write_chart_data(ws, data_dict, periode_terbaru):
    kc_list = [k for k in data_dict.keys() if k != "Total AH Gunsar"]
    total_data = data_dict.get("Total AH Gunsar", {})
    periode_list = total_data.get("periode_list", [])
    
    periode_trend = periode_list[-6:] if len(periode_list) >= 6 else periode_list

    ws['W1'] = "Periode"
    ws['X1'] = "Total DPK"
    ws['Y1'] = "Total Pinjaman"
    for i, periode in enumerate(periode_trend, start=2):
        ws.cell(row=i, column=23).value = periode  # W
        dpk_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Dana Pihak Ketiga", periode) or 0
        dpk_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "DPK Korporasi", periode) or 0
        pinj_val = get_val_helper(data_dict, "Total AH Gunsar", "Pinjaman", "Pinjaman", periode) or 0
        ws.cell(row=i, column=24).value = dpk_ritel + dpk_korp  # X
        ws.cell(row=i, column=25).value = pinj_val  # Y

    kc_portfolio = []
    for kc in kc_list:
        dpk_ritel = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Dana Pihak Ketiga", periode_terbaru) or 0
        dpk_korp = get_val_helper(data_dict, kc, "DPK Korporasi", "DPK Korporasi", periode_terbaru) or 0
        pinjaman = get_val_helper(data_dict, kc, "Pinjaman", "Pinjaman", periode_terbaru) or 0
        kc_portfolio.append((kc, dpk_ritel + dpk_korp + pinjaman))
    kc_portfolio.sort(key=lambda x: x[1], reverse=True)
    top5 = kc_portfolio[:5]

    ws['AA1'] = "KC"
    ws['AB1'] = "Total Portofolio"
    for i, (kc, val) in enumerate(top5, start=2):
        ws.cell(row=i, column=27).value = kc   # AA
        ws.cell(row=i, column=28).value = val  # AB

    tabungan = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Tabungan", periode_terbaru) or 0
    g_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Giro", periode_terbaru) or 0
    g_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "Giro", periode_terbaru) or 0
    d_ritel = get_val_helper(data_dict, "Total AH Gunsar", "Dana Pihak Ketiga", "Deposito", periode_terbaru) or 0
    d_korp = get_val_helper(data_dict, "Total AH Gunsar", "DPK Korporasi", "Deposito", periode_terbaru) or 0

    ws['AC1'] = "Komponen"
    ws['AD1'] = "Nilai"
    ws['AC2'] = "Tabungan"; ws['AD2'] = tabungan
    ws['AC3'] = "Giro"; ws['AD3'] = g_ritel + g_korp
    ws['AC4'] = "Deposito"; ws['AD4'] = d_ritel + d_korp

    ws['AE1'] = "KC"
    ws['AF1'] = "MTD DPK"
    for i, kc in enumerate(kc_list, start=2):
        mtd_ritel = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Dana Pihak Ketiga", None, key='mtd') or 0
        mtd_korp = get_val_helper(data_dict, kc, "DPK Korporasi", "DPK Korporasi", None, key='mtd') or 0
        ws.cell(row=i, column=31).value = kc       # AE
        ws.cell(row=i, column=32).value = (mtd_ritel + mtd_korp)  # AF

    ws['AG1'] = "KC"
    ws['AH1'] = "NPL %"
    for i, kc in enumerate(kc_list, start=2):
        npl_val = get_val_helper(data_dict, kc, "NPL", "NPL %", periode_terbaru) or 0
        ws.cell(row=i, column=33).value = kc          # AG
        ws.cell(row=i, column=34).value = npl_val  # AH

    return {
        'periode_count': len(periode_trend),
        'kc_count': len(kc_list),
        'top5_count': len(top5),
    }


def build_all_charts(ws, chart_meta):
    from openpyxl.chart import BarChart, PieChart, LineChart, Reference
    from openpyxl.chart.label import DataLabelList

    periode_count = chart_meta['periode_count']
    kc_count = chart_meta['kc_count']
    top5_count = chart_meta['top5_count']

    chart1 = BarChart()
    chart1.type = "col"
    chart1.title = "Trend DPK & Pinjaman (Rp Juta)"
    chart1.style = 10
    chart1.y_axis.title = "Rp Juta"
    chart1.height = 8
    chart1.width = 16
    chart1.visible_cells_only = False

    data1 = Reference(ws, min_col=24, max_col=25, min_row=1, max_row=1+periode_count)
    cats1 = Reference(ws, min_col=23, min_row=2, max_row=1+periode_count)
    chart1.add_data(data1, titles_from_data=True)
    chart1.set_categories(cats1)
    ws.add_chart(chart1, "A10")

    chart2 = BarChart()
    chart2.type = "bar"
    chart2.title = "Top 5 KC — Total Portofolio (Rp Juta)"
    chart2.style = 11; chart2.height = 8; chart2.width = 16; chart2.visible_cells_only = False

    data2 = Reference(ws, min_col=28, min_row=1, max_row=1+top5_count)
    cats2 = Reference(ws, min_col=27, min_row=2, max_row=1+top5_count)
    chart2.add_data(data2, titles_from_data=True)
    chart2.set_categories(cats2)
    ws.add_chart(chart2, "K10")

    chart3 = PieChart()
    chart3.title = "Komposisi DPK (Rp Juta)"
    chart3.height = 8; chart3.width = 12; chart3.visible_cells_only = False

    data3 = Reference(ws, min_col=30, min_row=1, max_row=4)
    cats3 = Reference(ws, min_col=29, min_row=2, max_row=4)
    chart3.add_data(data3, titles_from_data=True)
    chart3.set_categories(cats3)
    chart3.dataLabels = DataLabelList()
    chart3.dataLabels.showPercent = True
    ws.add_chart(chart3, "A26")

    chart4 = BarChart()
    chart4.type = "col"
    chart4.title = "Growth MTD — DPK per KC (Rp Juta)"
    chart4.style = 12; chart4.height = 8; chart4.width = 16; chart4.visible_cells_only = False

    data4 = Reference(ws, min_col=32, min_row=1, max_row=1+kc_count)
    cats4 = Reference(ws, min_col=31, min_row=2, max_row=1+kc_count)
    chart4.add_data(data4, titles_from_data=True)
    chart4.set_categories(cats4)
    ws.add_chart(chart4, "K26")

    chart5 = BarChart()
    chart5.type = "col"
    chart5.title = "NPL Ratio per KC (%)"
    chart5.style = 13
    chart5.height = 8
    chart5.width = 16
    chart5.y_axis.numFmt = '0.00%'
    chart5.visible_cells_only = False

    data5 = Reference(ws, min_col=34, min_row=1, max_row=1+kc_count)
    cats5 = Reference(ws, min_col=33, min_row=2, max_row=1+kc_count)
    chart5.add_data(data5, titles_from_data=True)
    chart5.set_categories(cats5)
    ws.add_chart(chart5, "A42")


def build_summary_table(ws, data_dict, periode_terbaru, start_row=58):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    thin = Side(style='thin', color='E2E8F0')
    border = Border(top=thin, bottom=thin, left=thin, right=thin)

    ws.merge_cells(f'A{start_row}:T{start_row}')
    title_cell = ws[f'A{start_row}']
    title_cell.value = "Ringkasan per KC — Periode Terbaru"
    title_cell.font = Font(size=12, bold=True, color='1E3A5F')

    header_row = start_row + 1
    headers = ["KC", "DPK Total", "Pinjaman Total", "SML %", "NPL %", "Pencapaian RKA DPK", "Status"]
    col_widths = [3, 4, 4, 2, 2, 3, 2]
    
    col_idx = 1
    col_positions = []
    for h, w in zip(headers, col_widths):
        start_col = col_idx
        end_col = col_idx + w - 1
        col_positions.append((start_col, end_col))
        start_letter = get_column_letter(start_col)
        end_letter = get_column_letter(end_col)
        ws.merge_cells(f'{start_letter}{header_row}:{end_letter}{header_row}')
        cell = ws[f'{start_letter}{header_row}']
        cell.value = h
        cell.font = Font(bold=True, color='FFFFFF', size=10)
        cell.fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
        cell.alignment = Alignment(horizontal='center')
        col_idx = end_col + 1

    kc_list = [k for k in data_dict.keys() if k != "Total AH Gunsar"]
    row = header_row + 1
    for kc in kc_list + ["Total AH Gunsar"]:
        dpk_ritel = get_val_helper(data_dict, kc, "Dana Pihak Ketiga", "Dana Pihak Ketiga", periode_terbaru)
        dpk_korp = get_val_helper(data_dict, kc, "DPK Korporasi", "DPK Korporasi", periode_terbaru)
        dpk = (dpk_ritel or 0) + (dpk_korp or 0)
        pinj = get_val_helper(data_dict, kc, "Pinjaman", "Pinjaman", periode_terbaru) or 0
        sml_pct = get_val_helper(data_dict, kc, "SML", "SML %", periode_terbaru)
        npl_pct = get_val_helper(data_dict, kc, "NPL", "NPL %", periode_terbaru)
        pencp = 0

        if npl_pct is None:
            status, status_color = "DATA TIDAK TERSEDIA", "94A3B8"
            npl_str = "-"
        elif npl_pct < 0.03:
            status, status_color = "BAIK", "16A34A"
            npl_str = f"{npl_pct*100:.2f}%"
        elif npl_pct < 0.05:
            status, status_color = "PERHATIAN", "D97706"
            npl_str = f"{npl_pct*100:.2f}%"
        else:
            status, status_color = "KRITIS", "DC2626"
            npl_str = f"{npl_pct*100:.2f}%"
            
        sml_str = f"{sml_pct*100:.2f}%" if sml_pct is not None else "-"

        values = [kc, f"{dpk:,.0f}", f"{pinj:,.0f}", sml_str, npl_str, f"{pencp*100:.2f}%", status]

        is_total = (kc == "Total AH Gunsar")
        for (start_col, end_col), val in zip(col_positions, values):
            start_letter = get_column_letter(start_col)
            end_letter = get_column_letter(end_col)
            ws.merge_cells(f'{start_letter}{row}:{end_letter}{row}')
            cell = ws[f'{start_letter}{row}']
            cell.value = val
            cell.font = Font(bold=is_total, size=10,
                             color='1E293B' if not is_total else '1E3A5F')
            if val == status:
                cell.font = Font(bold=True, size=10, color=status_color)
            
            cell.fill = PatternFill(
                start_color='DBEAFE' if is_total else ('FFFFFF' if row % 2 == 0 else 'F8FAFC'),
                end_color='DBEAFE' if is_total else ('FFFFFF' if row % 2 == 0 else 'F8FAFC'),
                fill_type='solid'
            )
            cell.alignment = Alignment(horizontal='center')
            for c in range(start_col, end_col + 1):
                ws.cell(row=row, column=c).border = border

        row += 1
    return row

def hide_support_columns(ws):
    from openpyxl.utils import get_column_letter
    for col_idx in range(23, 35):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].hidden = True

def build_dashboard_visual(ws, data_dict, metadata=None):
    from openpyxl.styles import Font, PatternFill, Alignment
    import json
    
    # ---------------------------------------------
    # USER DIAGNOSTIC
    # ---------------------------------------------
    print("="*60)
    print("[DIAGNOSTIC] STRUKTUR DATA_DICT YANG SEBENARNYA")
    print("="*60)
    print("Keys di data_dict (level 1):", list(data_dict.keys()))
    
    total_data = data_dict.get("Total AH Gunsar")
    if total_data:
        print("\nKeys di Total AH Gunsar:", list(total_data.keys()))
        if 'periode_list' in total_data:
            print("\nperiode_list:", total_data['periode_list'])
        else:
            print("\n[ERROR] Key 'periode_list' TIDAK ADA!")
    else:
        print("\n[FATAL ERROR] 'Total AH Gunsar' TIDAK DITEMUKAN di data_dict!")

    print("\n" + "="*60)
    print("[DIAGNOSTIC] CONTOH SATU KC (bukan Total)")
    print("="*60)
    kc_sample = [k for k in data_dict.keys() if k != "Total AH Gunsar"]
    if kc_sample:
        sample_kc_data = data_dict[kc_sample[0]]
        print(f"KC: {kc_sample[0]}")
        print("Keys:", list(sample_kc_data.keys()))
    print("="*60)
    
    # Adapt argument for older usage
    if metadata is None:
        metadata = {'tanggal_terbaru': '', 'jam': ''}
        
    periode_terbaru = get_periode_terbaru(data_dict)
    if not periode_terbaru:
        print("[ERROR] Tidak ada periode terbaru ditemukan!")
        periode_terbaru = ""
    else:
        metadata['tanggal_terbaru'] = periode_terbaru

    print(f"[DEBUG] Periode terbaru untuk dashboard: {periode_terbaru}")

    ws.column_dimensions['A'].width = 4
    for col in 'BCDEFGHIJKLMNOPQRST':
        ws.column_dimensions[col].width = 9

    style_header(ws, metadata)
    build_kpi_cards(ws, data_dict, periode_terbaru)
    chart_meta = write_chart_data(ws, data_dict, periode_terbaru)
    print(f"[DEBUG] Chart meta: {chart_meta}")
    
    # BUILD CHARTS THEN HIDE
    build_all_charts(ws, chart_meta)
    
    # CHART DEBUG
    print("[CHART DEBUG] Chart berhasil dibuat. Mengecek chart pertama di worksheet...")
    if ws._charts:
        c1 = ws._charts[0]
        print(f"[CHART DEBUG] Chart1 - jumlah series: {len(c1.series)}")
        for s in c1.series:
            ref = s.val.numRef.f if (s.val and s.val.numRef) else 'KOSONG'
            print(f"  Series values ref: {ref}")
    else:
        print("[CHART DEBUG] TIDAK ADA CHART YANG DIBUAT!")
        
    summary_end_row = build_summary_table(ws, data_dict, periode_terbaru)
    hide_support_columns(ws)

    footer_row = summary_end_row + 2
    ws.merge_cells(f'A{footer_row}:T{footer_row}')
    footer_cell = ws[f'A{footer_row}']
    footer_cell.value = "Catatan: Data bersifat rahasia dan hanya untuk penggunaan internal."
    footer_cell.font = Font(size=9, italic=True, color='FFFFFF')
    footer_cell.fill = PatternFill(start_color='1E3A5F', end_color='1E3A5F', fill_type='solid')
    footer_cell.alignment = Alignment(horizontal='center')

    ws.sheet_view.showGridLines = False

    assert ws.max_row > 50, "Dashboard terlalu pendek, kemungkinan ada yang gagal"
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

