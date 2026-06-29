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

from core.file_reader import BULAN_PANJANG, BULAN_SINGKAT


# ────────────────────────────────────────────────────────────────────
# STYLE HELPERS
# ────────────────────────────────────────────────────────────────────
def _fill(hex_color: str) -> PatternFill:
    return PatternFill("solid", fgColor=hex_color.lstrip("#"))


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
# EXPORT UTAMA
# ────────────────────────────────────────────────────────────────────
def export_to_excel(data_dict: dict,
                    output_path: str,
                    tanggal_data: str = "") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    wb.remove(wb.active)

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
            
            ("SML", "SML"): ["sml_mikro", "sml_small", "sml_konsumer"],
            ("SML", "SML %"): ["sml_pct"],
            ("SML", "Mikro"): ["sml_mikro"],
            ("SML", "Mikro %"): ["sml_mikro_pct"],
            ("SML", "Small"): ["sml_small"],
            ("SML", "Small %"): ["sml_small_pct"],
            ("SML", "Konsumer"): ["sml_konsumer"],
            ("SML", "Konsumer %"): ["sml_konsumer_pct"],
            
            ("NPL", "NPL"): ["npl_mikro", "npl_small", "npl_konsumer"],
            ("NPL", "NPL %"): ["npl_pct"],
            ("NPL", "Mikro"): ["npl_mikro"],
            ("NPL", "Mikro %"): ["npl_mikro_pct"],
            ("NPL", "Small"): ["npl_small"],
            ("NPL", "Small %"): ["npl_small_pct"],
            ("NPL", "Konsumer"): ["npl_konsumer"],
            ("NPL", "Konsumer %"): ["npl_konsumer_pct"],
            
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
    col_pos_ltr = get_column_letter(COL_POS_END)
    col_rka_ltr = get_column_letter(COL_RKA_START + rka_bulan_idx)
    c.value = f'=IF({col_rka_ltr}{row}="","",IF({col_rka_ltr}{row}=0,"",{col_pos_ltr}{row}/{col_rka_ltr}{row}))'
    c.number_format = "0.00%"
    c.fill = fill_obj
    c.font = font_obj
    c.alignment = _align(h="right", v="center")
    c.border = bdr

    # Growth (kalau ada)
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key, 0)
        c = ws.cell(row=row, column=col)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

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
    col_pos_ltr = get_column_letter(COL_POS_END)
    col_rka_ltr = get_column_letter(COL_RKA_START + rka_bulan_idx)
    c.value = f'=IF({col_rka_ltr}{row}="","",IF({col_rka_ltr}{row}=0,"",{col_pos_ltr}{row}/{col_rka_ltr}{row}))'
    c.number_format = "0.00%"
    c.fill = _fill(CLR_PENCAP_BG)
    c.font = font_obj
    c.alignment = _align(h="right", v="center")
    c.border = bdr

    # Growth
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key, 0)
        c = ws.cell(row=row, column=col)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

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

    # Pencapaian RKA (formula)
    c = ws.cell(row=row, column=COL_PENCAP)
    col_pos_ltr = get_column_letter(COL_POS_END)
    col_rka_ltr = get_column_letter(COL_RKA_START + rka_bulan_idx)
    c.value = f'=IF({col_rka_ltr}{row}="","",IF({col_rka_ltr}{row}=0,"",{col_pos_ltr}{row}/{col_rka_ltr}{row}))'
    c.number_format = "0.00%"
    c.fill = _fill(CLR_PENCAP_BG)
    c.font = font_obj
    c.alignment = _align(h="right", v="center")
    c.border = bdr

    # Growth
    for col, key in [(COL_MTD, "mtd"), (COL_DTD, "dtd"),
                     (COL_YOY, "yoy"), (COL_YTD, "ytd")]:
        val = row_data.get(key, 0)
        c = ws.cell(row=row, column=col)
        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = val if val == "-" else ""

        c.number_format = '0.00%' if is_pct else "#,##0;-#,##0;\"-\""
        c.fill = fill_obj
        c.font = font_obj
        c.alignment = _align(h="right", v="center")
        c.border = bdr

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

