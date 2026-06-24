"""
validator.py — Validasi struktur DataFrame SSA.
Validator bersifat fleksibel: mencari kolom wajib dengan matching parsial.
"""
import pandas as pd


# Kolom wajib SSA Simpanan (minimal yang harus ada)
REQUIRED_SIMPANAN = [
    "Nama Cabang",
    "Jenis Produk",
    "Segmentasi BPR",
    "Saldo",
]

# Kolom wajib SSA Pinjaman
REQUIRED_PINJAMAN = [
    "Nama Cabang",
    "Kolektabilitas One Obligor",
    "Segmen",
    "Baki Debet",
]


class ValidationResult:
    """Hasil validasi satu DataFrame."""

    def __init__(self, valid: bool, message: str = "",
                 missing: list[str] | None = None):
        self.valid   = valid
        self.message = message
        self.missing = missing or []

    def __bool__(self) -> bool:
        return self.valid


def _find_column(df: pd.DataFrame, name: str) -> str | None:
    """
    Cari kolom dengan nama yang tepat atau yang mengandung substring.
    Return nama kolom asli jika ditemukan, None jika tidak.
    """
    cols = df.columns.str.strip()
    # Exact match dulu
    if name in cols.values:
        return name
    # Partial match (case-insensitive)
    for col in cols:
        if name.lower() in col.lower():
            return col
    return None


def validate_ssa_simpanan(df: pd.DataFrame) -> ValidationResult:
    """
    Validasi DataFrame SSA Simpanan.
    Return ValidationResult dengan detail kolom yang kurang.
    """
    if df.empty:
        return ValidationResult(False, "File kosong atau tidak bisa dibaca.")

    missing = []
    for req in REQUIRED_SIMPANAN:
        if _find_column(df, req) is None:
            missing.append(req)

    if missing:
        msg = (
            "File SSA Simpanan tidak memiliki kolom yang diharapkan:\n"
            + "\n".join(f"  • {c}" for c in missing)
            + "\n\nPastikan Anda memilih file SSA Simpanan yang benar."
        )
        return ValidationResult(False, msg, missing)

    return ValidationResult(True, "File SSA Simpanan valid.")


def validate_ssa_pinjaman(df: pd.DataFrame) -> ValidationResult:
    """
    Validasi DataFrame SSA Pinjaman.
    Return ValidationResult dengan detail kolom yang kurang.
    """
    if df.empty:
        return ValidationResult(False, "File kosong atau tidak bisa dibaca.")

    missing = []
    for req in REQUIRED_PINJAMAN:
        if _find_column(df, req) is None:
            missing.append(req)

    if missing:
        msg = (
            "File SSA Pinjaman tidak memiliki kolom yang diharapkan:\n"
            + "\n".join(f"  • {c}" for c in missing)
            + "\n\nPastikan Anda memilih file SSA Pinjaman yang benar."
        )
        return ValidationResult(False, msg, missing)

    return ValidationResult(True, "File SSA Pinjaman valid.")


def validate_rka(df: pd.DataFrame) -> ValidationResult:
    """
    Validasi DataFrame RKA (opsional — selalu return valid jika bisa dibaca).
    Hanya periksa apakah DataFrame tidak kosong.
    """
    if df.empty:
        return ValidationResult(False, "File RKA kosong.", [])
    return ValidationResult(True, "File RKA valid.")
