"""
exporter.py — Generate file Excel berformat template Dashboard AH Gunsar.
"""
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


# ── Style constants ────────────────────────────────────────────
_FILL_HEADER   = PatternFill("solid", fgColor="1E3A5F")
_FILL_SUBTOTAL = PatternFill("solid", fgColor="DBEAFE")
_FILL_TOTAL    = PatternFill("solid", fgColor="1E3A5F")
_FILL_ROW_A    = PatternFill("solid", fgColor="FFFFFF")
_FILL_ROW_B    = PatternFill("solid", fgColor="F1F5F9")

_FONT_HEADER   = Font(name="Arial", bold=True,  size=11, color="FFFFFF")
_FONT_SUBTOTAL = Font(name="Arial", bold=True,  size=11, color="1E293B")
_FONT_TOTAL    = Font(name="Arial", bold=True,  size=11, color="FFFFFF")
_FONT_NORMAL   = Font(name="Arial", bold=False, size=10, color="1E293B")

_ALIGN_CTR     = Alignment(horizontal="center", vertical="center", wrap_text=True)
_ALIGN_LEFT    = Alignment(horizontal="left",   vertical="center")
_ALIGN_RIGHT   = Alignment(horizontal="right",  vertical="center")

_THIN          = Side(style="thin", color="D1D5DB")
_BORDER        = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)

_TOTAL_KW      = {"total keseluruhan", "grand total"}
_SUB_KW        = {"subtotal", "sub total"}


def export_to_excel(
    data_dict: dict,
    output_path: str,
    tanggal_data: str = "",
) -> Path:
    """
    Export data_dict ke file Excel berformat template Dashboard AH Gunsar.

    Args:
        data_dict  : dict {sheet_name: pd.DataFrame}
        output_path: path lengkap file output .xlsx
        tanggal_data: string tanggal data untuk header

    Returns:
        Path ke file yang disimpan.

    Raises:
        RuntimeError jika gagal menyimpan.
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    first = True

    for sheet_name, df in data_dict.items():
        if df is None or df.empty:
            continue

        if first:
            ws = wb.active
            ws.title = sheet_name[:31]   # Excel sheet name ≤ 31 karakter
            first = False
        else:
            ws = wb.create_sheet(title=sheet_name[:31])

        _write_sheet(ws, df)

    # Buang sheet kosong default
    if first and "Sheet" in wb.sheetnames:
        del wb["Sheet"]

    try:
        wb.save(str(out))
    except Exception as e:
        raise RuntimeError(f"Gagal menyimpan file Excel: {e}") from e

    return out


def _write_sheet(ws, df: pd.DataFrame) -> None:
    """Tulis satu sheet dengan formatting lengkap."""
    cols = list(df.columns)
    n    = len(cols)

    # ── Header row ─────────────────────────────────────
    for ci, col_name in enumerate(cols, 1):
        c = ws.cell(row=1, column=ci, value=col_name)
        c.fill      = _FILL_HEADER
        c.font      = _FONT_HEADER
        c.alignment = _ALIGN_CTR
        c.border    = _BORDER

    # ── Data rows ───────────────────────────────────────
    for ri, (_, row) in enumerate(df.iterrows(), 2):
        kc_val   = str(row.iloc[0]).strip()
        kc_lower = kc_val.lower()

        is_total    = any(k in kc_lower for k in _TOTAL_KW)
        is_subtotal = any(k in kc_lower for k in _SUB_KW)

        if is_total:
            fill, font = _FILL_TOTAL, _FONT_TOTAL
        elif is_subtotal:
            fill, font = _FILL_SUBTOTAL, _FONT_SUBTOTAL
        else:
            fill = _FILL_ROW_A if ri % 2 == 0 else _FILL_ROW_B
            font = _FONT_NORMAL

        for ci, col_name in enumerate(cols, 1):
            val = row[col_name]
            c   = ws.cell(row=ri, column=ci)

            if ci == 1:
                # Kolom KC — teks
                c.value     = val
                c.alignment = _ALIGN_LEFT
            else:
                try:
                    num = float(val)
                    c.value        = num
                    c.number_format = "#,##0"
                    c.alignment    = _ALIGN_RIGHT
                except (ValueError, TypeError):
                    c.value     = val
                    c.alignment = _ALIGN_RIGHT

            c.fill   = fill
            c.font   = font
            c.border = _BORDER

    # ── Column widths ───────────────────────────────────
    ws.column_dimensions["A"].width = 36
    for ci in range(2, n + 1):
        ws.column_dimensions[get_column_letter(ci)].width = 18

    # ── Freeze panes ────────────────────────────────────
    ws.freeze_panes = "B2"


def get_file_size_str(path: str) -> str:
    """Return ukuran file dalam format KB atau MB."""
    p = Path(path)
    if not p.exists():
        return "0 KB"
    sz = p.stat().st_size
    return f"{sz / 1024:.0f} KB" if sz < 1_048_576 else f"{sz / 1_048_576:.1f} MB"
