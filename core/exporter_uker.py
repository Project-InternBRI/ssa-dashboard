"""
exporter_uker.py — Export hasil proses KCP / Unit ke format Excel Dashboard.

Reuses semua fungsi styling, _write_sheet, dan _build_export_filename dari exporter.py.
TIDAK mengubah exporter.py sama sekali.
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime

from core.file_reader import BULAN_PANJANG, BULAN_SINGKAT
from core.exporter import (
    _write_sheet,       # tulis satu sheet — identik dengan KC
    get_unique_path,
)

from openpyxl import Workbook


# ────────────────────────────────────────────────────────────────────
# FILENAME HELPER
# ────────────────────────────────────────────────────────────────────
def get_filename_uker(data_dict: dict, uker_type: str) -> str:
    """
    Buat nama file berdasarkan periode terbaru pada data.
    Format: Dashboard KCP AH Gunsar [DD] [Bulan] [YYYY].xlsx
            Dashboard Unit AH Gunsar [DD] [Bulan] [YYYY].xlsx
    """
    date_str = ""
    try:
        # Cari Total KCP atau Total Unit
        total_key = 'Total KCP' if uker_type == 'KCP' else 'Total Unit'
        total_data = data_dict.get(total_key)
        if not total_data:
            # Fallback: ambil entitas pertama
            for k, v in data_dict.items():
                if k != '__stats__' and isinstance(v, dict) and 'rows' in v:
                    total_data = v
                    break

        if total_data:
            rows = total_data.get('rows', [])
            meta = next((r for r in rows if r.get('row_type') == '__metadata__'), None)
            if meta:
                terbaru_dt = meta['periode_refs']['terbaru']
                if terbaru_dt:
                    date_str = f" {terbaru_dt.day} {BULAN_PANJANG[terbaru_dt.month]} {terbaru_dt.year}"
    except Exception:
        pass

    label = uker_type  # 'KCP' or 'Unit'
    return f"Dashboard {label} AH Gunsar{date_str}.xlsx"


# ────────────────────────────────────────────────────────────────────
# EXPORT KCP atau UNIT ke Excel
# ────────────────────────────────────────────────────────────────────
def export_uker_to_excel(data_dict: dict, output_path: str,
                         uker_type: str) -> Path:
    """
    Export data KCP atau Unit ke file Excel.

    data_dict: hasil dari process_files_uker()
    uker_type : 'KCP' | 'Unit'
    """
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    first = True

    stats   = data_dict.get('__stats__', {})
    total_key = 'Total KCP' if uker_type == 'KCP' else 'Total Unit'

    # Entitas individual (diurutkan alphabetical)
    entity_keys = sorted([
        k for k, v in data_dict.items()
        if k not in ('__stats__', total_key)
        and isinstance(v, dict) and 'rows' in v
        and v.get('uker_type') == uker_type
    ])

    all_keys = entity_keys + ([total_key] if total_key in data_dict else [])

    for key in all_keys:
        kc_data = data_dict[key]
        sheet_name = key[:31]  # Excel max 31 chars

        if first:
            ws = wb.active
            ws.title = sheet_name
            first = False
        else:
            ws = wb.create_sheet(title=sheet_name)

        # Gunakan _write_sheet dari exporter.py — logika penulisan identik KC
        _write_sheet(ws, key, kc_data)

    try:
        wb.save(str(out))
    except Exception as e:
        raise RuntimeError(f"Gagal menyimpan file Excel ({uker_type}): {e}") from e

    return out
