"""
file_reader.py — Universal file reader untuk SSA Dashboard.
Mendukung CSV (auto-detect delimiter & encoding) dan semua format Excel.
"""
import io
import chardet
import pandas as pd
from pathlib import Path


# Ekstensi yang didukung
CSV_EXTS   = {".csv"}
EXCEL_EXTS = {".xlsx", ".xls", ".xlsb", ".xlsm"}
ALL_EXTS   = CSV_EXTS | EXCEL_EXTS


def detect_csv_params(path: str) -> dict:
    """
    Auto-detect delimiter dan encoding file CSV.
    Return dict berisi 'sep' dan 'encoding'.
    """
    raw = Path(path).read_bytes()

    # 1. Detect encoding
    detected = chardet.detect(raw[:8192])
    encoding = detected.get("encoding") or "utf-8"
    # Normalisasi nama encoding umum
    enc_map = {
        "ascii": "utf-8",
        "UTF-8-SIG": "utf-8-sig",
    }
    encoding = enc_map.get(encoding, encoding)

    # 2. Decode untuk analisis delimiter
    try:
        text = raw.decode(encoding, errors="replace")
    except (LookupError, UnicodeDecodeError):
        encoding = "latin-1"
        text = raw.decode(encoding, errors="replace")

    # Ambil baris pertama
    first_line = text.split("\n")[0] if "\n" in text else text[:500]

    # 3. Hitung kemunculan setiap kandidat delimiter
    delimiters = [";", ",", "\t", "|"]
    counts = {d: first_line.count(d) for d in delimiters}
    sep = max(counts, key=counts.get)

    # Fallback ke koma jika tidak ada delimiter yang jelas
    if counts[sep] == 0:
        sep = ","

    return {"sep": sep, "encoding": encoding}


def read_file(path: str, sheet_name: int | str = 0,
              nrows: int | None = None) -> pd.DataFrame:
    """
    Baca file CSV atau Excel ke DataFrame.

    Args:
        path     : path lengkap ke file
        sheet_name: untuk Excel, nama/index sheet (default 0 = sheet pertama)
        nrows    : batas jumlah baris yang dibaca (None = semua)

    Returns:
        pd.DataFrame dengan kolom di-strip whitespace-nya.

    Raises:
        ValueError jika format file tidak didukung.
        RuntimeError jika gagal membaca.
    """
    p = Path(path)
    ext = p.suffix.lower()

    if ext not in ALL_EXTS:
        raise ValueError(
            f"Format file '{ext}' tidak didukung. "
            f"Gunakan: {', '.join(sorted(ALL_EXTS))}"
        )

    try:
        if ext in CSV_EXTS:
            params = detect_csv_params(str(p))
            df = pd.read_csv(
                str(p),
                sep=params["sep"],
                encoding=params["encoding"],
                on_bad_lines="skip",
                low_memory=False,
                nrows=nrows,
            )
        elif ext == ".xlsx" or ext == ".xlsm":
            df = pd.read_excel(str(p), sheet_name=sheet_name,
                               engine="openpyxl", nrows=nrows)
        elif ext == ".xls":
            df = pd.read_excel(str(p), sheet_name=sheet_name,
                               engine="xlrd", nrows=nrows)
        elif ext == ".xlsb":
            df = pd.read_excel(str(p), sheet_name=sheet_name,
                               engine="pyxlsb", nrows=nrows)
        else:
            raise ValueError(f"Format tidak dikenali: {ext}")

        # Bersihkan nama kolom
        df.columns = df.columns.astype(str).str.strip()

        # Hapus baris yang sepenuhnya kosong
        df.dropna(how="all", inplace=True)
        df.reset_index(drop=True, inplace=True)

        return df

    except (ValueError, ImportError):
        raise
    except Exception as e:
        raise RuntimeError(f"Gagal membaca file '{p.name}': {e}") from e


def get_file_info(path: str) -> dict:
    """
    Ambil metadata dasar file: nama, ekstensi, ukuran.

    Returns:
        {name, ext, size_bytes, size_str, exists}
    """
    p = Path(path)
    exists = p.exists()
    size_bytes = p.stat().st_size if exists else 0

    if size_bytes < 1_048_576:
        size_str = f"{size_bytes / 1024:.0f} KB"
    else:
        size_str = f"{size_bytes / 1_048_576:.1f} MB"

    return {
        "name": p.name,
        "ext": p.suffix.lower(),
        "size_bytes": size_bytes,
        "size_str": size_str,
        "exists": exists,
    }


def validate_columns(df: pd.DataFrame, required: list[str]) -> tuple[bool, list[str]]:
    """
    Periksa apakah DataFrame memiliki semua kolom yang diharuskan.

    Returns:
        (True, []) jika valid
        (False, [kolom_tidak_ada, ...]) jika tidak valid
    """
    actual = set(df.columns.str.strip())
    missing = [c for c in required if c not in actual]
    return (len(missing) == 0), missing


# Filter string untuk QFileDialog
FILTER_SSA    = "CSV / Excel (*.csv *.xlsx *.xls *.xlsb *.xlsm);;All Files (*)"
FILTER_RKA    = "Excel (*.xlsx *.xls *.xlsb *.xlsm);;CSV (*.csv);;All Files (*)"
FILTER_EXCEL  = "Excel Files (*.xlsx)"
