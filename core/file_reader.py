"""
file_reader.py — Universal file reader untuk SSA Dashboard.

Fitur:
- Auto-detect encoding & delimiter untuk CSV
- Konversi numerik robust (format Indonesia & internasional)
- Parsing tanggal Indonesia ("19 Juni 2026")
- Fungsi diagnosa file untuk debugging
"""
import os
import calendar

import chardet
import pandas as pd
from pathlib import Path


# ────────────────────────────────────────────────────────────────────
# KONSTANTA
# ────────────────────────────────────────────────────────────────────
CSV_EXTS   = {".csv"}
EXCEL_EXTS = {".xlsx", ".xls", ".xlsb", ".xlsm"}
ALL_EXTS   = CSV_EXTS | EXCEL_EXTS

FILTER_SSA   = "CSV / Excel (*.csv *.xlsx *.xls *.xlsb *.xlsm);;All Files (*)"
FILTER_EXCEL = "Excel Files (*.xlsx)"

BULAN_MAP = {
    'januari': 1, 'jan': 1,
    'februari': 2, 'feb': 2,
    'maret': 3, 'mar': 3,
    'april': 4, 'apr': 4,
    'mei': 5, 'may': 5,
    'juni': 6, 'jun': 6,
    'juli': 7, 'jul': 7,
    'agustus': 8, 'agu': 8, 'aug': 8,
    'september': 9, 'sep': 9,
    'oktober': 10, 'okt': 10, 'oct': 10,
    'november': 11, 'nov': 11,
    'desember': 12, 'des': 12, 'dec': 12,
}

BULAN_SINGKAT = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']

BULAN_PANJANG = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei',
                 'Juni', 'Juli', 'Agustus', 'September', 'Oktober',
                 'November', 'Desember']


# ────────────────────────────────────────────────────────────────────
# DIAGNOSA FILE (untuk debugging di console)
# ────────────────────────────────────────────────────────────────────
def diagnose_file(path: str, label: str) -> pd.DataFrame:
    """Diagnosa file CSV sebelum diproses. Print info ke console."""
    size_mb = os.path.getsize(path) / (1024 * 1024)
    print(f"\n{'=' * 60}")
    print(f"  DIAGNOSA {label}")
    print(f"{'=' * 60}")
    print(f"  Path  : {path}")
    print(f"  Size  : {size_mb:.2f} MB")

    # Deteksi encoding dengan chardet
    try:
        with open(path, 'rb') as f:
            raw = f.read(10000)
        detected = chardet.detect(raw)
        print(f"  Encoding terdeteksi: {detected}")
    except Exception as e:
        print(f"  chardet error: {e}")

    # Baca 3 baris pertama sebagai raw text
    for enc in ['utf-8-sig', 'utf-8', 'latin-1']:
        try:
            with open(path, 'r', encoding=enc) as f:
                lines = [f.readline() for _ in range(3)]
            print(f"\n  Raw lines (encoding={enc}):")
            for i, line in enumerate(lines):
                print(f"    Baris {i + 1}: {repr(line[:200])}")
            baris1 = lines[0]
            for delim in [';', ',', '\t', '|']:
                count = baris1.count(delim)
                print(f"    Jumlah '{delim}' di baris 1: {count}")
            break
        except Exception as e:
            print(f"  Gagal baca dengan {enc}: {e}")

    # Baca dengan pandas
    df = read_file(path)
    print(f"\n  Hasil baca pandas:")
    print(f"    Shape : {df.shape}")
    print(f"    Kolom : {list(df.columns)}")
    print(f"    Dtypes:\n{df.dtypes.to_string()}")
    print(f"    5 baris pertama:")
    print(df.head().to_string())
    print(f"{'=' * 60}\n")

    return df


# ────────────────────────────────────────────────────────────────────
# READ FILE — CSV & Excel
# ────────────────────────────────────────────────────────────────────
def read_file(path: str, sheet_name: int | str = 0,
              nrows: int | None = None) -> pd.DataFrame:
    """
    Baca file CSV atau Excel ke DataFrame.
    CSV: auto-detect encoding & delimiter, pilih kombinasi terbaik.
    Semua kolom dibaca sebagai string, lalu konversi numerik.
    """
    ext = Path(path).suffix.lower()

    if ext == '.csv':
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        delimiters = [';', ',', '\t', '|']

        best_df = None
        best_col_count = 0

        for enc in encodings:
            for delim in delimiters:
                try:
                    df = pd.read_csv(
                        path,
                        sep=delim,
                        encoding=enc,
                        dtype=str,
                        skipinitialspace=True,
                        on_bad_lines='skip',
                        low_memory=False,
                        nrows=nrows,
                    )
                    if len(df.columns) > best_col_count:
                        best_col_count = len(df.columns)
                        best_df = df.copy()
                        if best_col_count >= 8:
                            break
                except Exception:
                    continue
            if best_col_count >= 8:
                break

        if best_df is None or best_col_count < 3:
            raise ValueError(
                f"Tidak dapat membaca file: {Path(path).name}\n"
                f"Pastikan file CSV tidak rusak."
            )

        df = best_df
        df.columns = [str(c).strip() for c in df.columns]
        df = df.dropna(how='all').reset_index(drop=True)
        df = convert_numerics(df)
        return df

    elif ext in ['.xlsx', '.xlsm']:
        df = pd.read_excel(path, sheet_name=sheet_name,
                           engine='openpyxl', dtype=str, nrows=nrows)
    elif ext == '.xls':
        df = pd.read_excel(path, sheet_name=sheet_name,
                           engine='xlrd', dtype=str, nrows=nrows)
    elif ext == '.xlsb':
        df = pd.read_excel(path, sheet_name=sheet_name,
                           engine='pyxlsb', dtype=str, nrows=nrows)
    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how='all').reset_index(drop=True)
    df = convert_numerics(df)
    return df


# ────────────────────────────────────────────────────────────────────
# KONVERSI NUMERIK — Saldo & Baki Debet
# ────────────────────────────────────────────────────────────────────
def _parse_num(val) -> float:
    """Parse satu nilai numerik dari berbagai format."""
    if pd.isna(val):
        return 0.0
    s = str(val).strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null'):
        return 0.0

    # Coba langsung (sudah float/int atau notasi ilmiah)
    try:
        return float(s)
    except ValueError:
        pass

    # Hapus karakter non-numerik (Rp, spasi)
    s = s.replace('Rp', '').replace(' ', '')

    # Format Indonesia: titik=ribuan, koma=desimal
    if ',' in s and '.' in s:
        if s.rfind('.') < s.rfind(','):
            # 1.234.567,89 → titik=ribuan, koma=desimal
            s = s.replace('.', '').replace(',', '.')
        else:
            # 1,234,567.89 → koma=ribuan
            s = s.replace(',', '')
    elif ',' in s:
        # Hanya koma: mungkin desimal
        s = s.replace(',', '.')
    elif '.' in s:
        # Hanya titik: mungkin ribuan atau desimal
        if s.count('.') > 1:
            s = s.replace('.', '')

    try:
        return float(s)
    except ValueError:
        return 0.0


def convert_numerics(df: pd.DataFrame) -> pd.DataFrame:
    """Konversi kolom Saldo dan Baki Debet ke float."""
    for col in ['Saldo', 'Baki Debet']:
        if col not in df.columns:
            continue
        df[col] = df[col].apply(_parse_num)
    return df


# ────────────────────────────────────────────────────────────────────
# PARSING TANGGAL
# ────────────────────────────────────────────────────────────────────
def parse_tanggal(tgl_str) -> pd.Timestamp | None:
    """
    Parse string tanggal ke pd.Timestamp.
    Mendukung format:
      - "19 Juni 2026" atau "19 Jun 2026"
      - "2026-06-19"
      - datetime/Timestamp object
    """
    if pd.isna(tgl_str) or str(tgl_str).strip() == '':
        return None

    # Sudah Timestamp/datetime
    if isinstance(tgl_str, (pd.Timestamp,)):
        return tgl_str
    try:
        from datetime import datetime as dt_cls
        if isinstance(tgl_str, dt_cls):
            return pd.Timestamp(tgl_str)
    except Exception:
        pass

    s = str(tgl_str).strip()
    parts = s.split()

    # Format: "19 Juni 2026" atau "19 Jun 2026"
    if len(parts) >= 3:
        bulan_key = parts[1].lower().rstrip('.')
        bulan = BULAN_MAP.get(bulan_key)
        if bulan:
            try:
                return pd.Timestamp(
                    year=int(parts[2]),
                    month=bulan,
                    day=int(parts[0])
                )
            except Exception:
                pass

    # Fallback: pandas parse otomatis
    try:
        return pd.to_datetime(s, dayfirst=True)
    except Exception:
        return None


def format_periode_label(ts) -> str:
    """
    Timestamp → label periode untuk header kolom Excel.

    Akhir bulan (hari >= akhir_bulan - 1):
      "Des-25", "Jan-26", "Feb-26"

    Harian (bukan akhir bulan):
      "17 Jun-2026", "20 Jun-2026"
    """
    if ts is None:
        return "Unknown"
    if not isinstance(ts, pd.Timestamp):
        try:
            ts = pd.Timestamp(ts)
        except Exception:
            return "Unknown"

    tahun2 = str(ts.year)[-2:]
    bulan = BULAN_SINGKAT[ts.month]
    akhir_bulan = calendar.monthrange(ts.year, ts.month)[1]

    if ts.day >= akhir_bulan - 1:
        # Periode bulanan: "Des-25", "Jan-26"
        return f"{bulan}-{tahun2}"
    else:
        # Periode harian: "17 Jun-2026", "20 Jun-2026"
        return f"{ts.day} {bulan}-{ts.year}"


# ────────────────────────────────────────────────────────────────────
# UTILITIES KOLOM
# ────────────────────────────────────────────────────────────────────
def get_file_info(path: str) -> dict:
    """Ambil metadata dasar file."""
    p = Path(path)
    exists = p.exists()
    size = p.stat().st_size if exists else 0

    if size < 1_048_576:
        size_str = f"{size / 1024:.0f} KB"
    else:
        size_str = f"{size / 1_048_576:.1f} MB"

    return {
        "name": p.name,
        "ext": p.suffix.lower(),
        "size_bytes": size,
        "size_str": size_str,
        "exists": exists,
    }


def find_column(df: pd.DataFrame, name: str) -> str | None:
    """
    Cari kolom dengan nama yang tepat atau partial match (case-insensitive).
    Return nama kolom asli jika ditemukan, None jika tidak ada.
    """
    cols = df.columns.str.strip()
    if name in cols.values:
        return name
    for col in cols:
        if name.lower() in col.lower():
            return col
    return None


def require_column(df: pd.DataFrame, name: str) -> str:
    """Seperti find_column tapi raise KeyError jika tidak ditemukan."""
    col = find_column(df, name)
    if col is None:
        raise KeyError(
            f"Kolom '{name}' tidak ditemukan. "
            f"Kolom yang tersedia: {list(df.columns[:15])}"
        )
    return col


def validate_columns(df: pd.DataFrame,
                     required: list[str]) -> tuple[bool, list[str]]:
    """Periksa apakah DataFrame memiliki semua kolom yang diharuskan."""
    missing = [c for c in required if find_column(df, c) is None]
    return len(missing) == 0, missing
