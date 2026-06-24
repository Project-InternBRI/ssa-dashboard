"""
processor.py — Logika utama pemrosesan data SSA.
Menghasilkan dict DataFrame siap tampil per produk.
RKA bersifat opsional.
"""
import pandas as pd
from pathlib import Path

from core.file_reader import read_file


# ── Nama kolom wajib ───────────────────────────────────────────
COL_KC         = "Nama Cabang"
COL_JENIS      = "Jenis Produk"
COL_SEG_BPR    = "Segmentasi BPR"
COL_SALDO      = "Saldo"
COL_KOLEKT     = "Kolektabilitas One Obligor"
COL_SEGMEN     = "Segmen"
COL_BAKI       = "Baki Debet"

SEG_SIMPANAN   = ["Ritel", "Wholesale"]
SEG_PINJAMAN   = ["Konsumer", "Mikro", "SME", "Korporasi"]


def _find_col(df: pd.DataFrame, name: str) -> str:
    """
    Cari kolom paling cocok di DataFrame.
    Exact match → partial match. Raise KeyError jika tidak ketemu.
    """
    cols = df.columns.str.strip()
    if name in cols.values:
        return name
    for col in cols:
        if name.lower() in col.lower():
            return col
    raise KeyError(f"Kolom '{name}' tidak ditemukan. Kolom tersedia: {list(df.columns)}")


def _extract_kc(raw: str) -> str:
    """
    Ekstrak nama KC dari format BRI.
    "00329 -- KC Jakarta Veteran (Konsolidasi-MB)" → "KC Jakarta Veteran"
    """
    if not isinstance(raw, str):
        return str(raw).strip()
    s = raw
    if " -- " in s:
        s = s.split(" -- ", 1)[1]
    elif "--" in s:
        s = s.split("--", 1)[1].strip()
    if " (" in s:
        s = s.split(" (")[0]
    elif "(" in s:
        s = s.split("(")[0]
    return s.strip()


def _pivot_product(df: pd.DataFrame, value_col: str,
                   segment_col: str, segments: list[str]) -> pd.DataFrame:
    """
    Pivot: baris=KC, kolom=segmen, nilai=sum(value_col).
    Tambah kolom Total dan baris TOTAL KESELURUHAN.
    """
    df = df.copy()
    df[value_col]   = pd.to_numeric(df[value_col], errors="coerce").fillna(0)
    df["KC"]        = df[_find_col(df, "Nama Cabang")].apply(_extract_kc)
    seg_actual      = _find_col(df, segment_col)

    pivot = (
        df.pivot_table(
            index="KC",
            columns=seg_actual,
            values=value_col,
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    # Pastikan semua kolom segmen ada
    for seg in segments:
        if seg not in pivot.columns:
            pivot[seg] = 0

    seg_cols = [c for c in segments if c in pivot.columns]
    pivot["Total"] = pivot[seg_cols].sum(axis=1)

    # Urutkan kolom
    pivot = pivot.reindex(columns=["KC"] + seg_cols + ["Total"], fill_value=0)

    # Grand total row
    total = {"KC": "TOTAL KESELURUHAN"}
    for c in seg_cols + ["Total"]:
        total[c] = pivot[c].sum()
    pivot = pd.concat([pivot, pd.DataFrame([total])], ignore_index=True)

    return pivot


def _combine(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Jumlahkan dua pivot DataFrame per KC (union of KCs).
    """
    merged = pd.merge(df1, df2, on="KC", how="outer", suffixes=("_a", "_b"))
    result = pd.DataFrame({"KC": merged["KC"]})

    base_cols_a = [c for c in merged.columns if c.endswith("_a")]
    for ca in base_cols_a:
        base = ca[:-2]
        cb = f"{base}_b"
        xa = pd.to_numeric(merged.get(ca, 0), errors="coerce").fillna(0)
        xb = pd.to_numeric(merged.get(cb, 0), errors="coerce").fillna(0)
        result[base] = xa + xb

    # Recompute Total
    num_cols = [c for c in result.columns if c != "KC"]
    result["Total"] = result[num_cols].sum(axis=1)

    return result


def process_files(
    path_simpanan: str,
    path_pinjaman: str,
    path_rka: str | None = None,
    callback=None,
) -> dict[str, pd.DataFrame]:
    """
    Proses data SSA Simpanan, Pinjaman, dan (opsional) RKA.

    Args:
        path_simpanan : path CSV/Excel SSA Simpanan
        path_pinjaman : path CSV/Excel SSA Pinjaman
        path_rka      : path Excel RKA — boleh None
        callback      : callable(pct: int, msg: str) untuk progress

    Returns:
        dict {
            "Tabungan": df, "Giro": df, "Deposito": df,
            "CASA": df, "Total DPK": df, "Pinjaman": df
        }
    """

    def _cb(pct: int, msg: str):
        if callback:
            callback(pct, msg)

    result: dict[str, pd.DataFrame] = {}

    # ── 1. Baca SSA Simpanan ────────────────────────────────
    _cb(10, "📂 Membaca file SSA Simpanan...")
    df_s = read_file(path_simpanan)
    kc_col_s  = _find_col(df_s, COL_KC)
    jen_col   = _find_col(df_s, COL_JENIS)
    seg_col   = _find_col(df_s, COL_SEG_BPR)
    saldo_col = _find_col(df_s, COL_SALDO)

    # Normalise jenis produk
    df_s["_jenis"] = df_s[jen_col].astype(str).str.strip().str.lower()

    # ── 2. Baca SSA Pinjaman ────────────────────────────────
    _cb(25, "📂 Membaca file SSA Pinjaman...")
    df_p = read_file(path_pinjaman)
    kol_col  = _find_col(df_p, COL_KOLEKT)
    seg_p    = _find_col(df_p, COL_SEGMEN)
    baki_col = _find_col(df_p, COL_BAKI)

    # ── 3. Baca RKA (opsional) ──────────────────────────────
    df_rka = None
    if path_rka and Path(path_rka).exists():
        _cb(33, "📂 Membaca file Target RKA...")
        try:
            df_rka = read_file(path_rka)
        except Exception:
            df_rka = None  # RKA gagal dibaca — lanjut tanpa RKA

    # ── 4. Tabungan ─────────────────────────────────────────
    _cb(42, "⚙️ Memproses data Tabungan...")
    df_tab = df_s[df_s["_jenis"] == "tabungan"].copy()
    result["Tabungan"] = _pivot_product(df_tab, saldo_col, seg_col, SEG_SIMPANAN)

    # ── 5. Giro ─────────────────────────────────────────────
    _cb(52, "⚙️ Memproses data Giro...")
    df_giro = df_s[df_s["_jenis"] == "giro"].copy()
    result["Giro"] = _pivot_product(df_giro, saldo_col, seg_col, SEG_SIMPANAN)

    # ── 6. Deposito ─────────────────────────────────────────
    _cb(60, "⚙️ Memproses data Deposito...")
    df_dep = df_s[df_s["_jenis"] == "deposito"].copy()
    result["Deposito"] = _pivot_product(df_dep, saldo_col, seg_col, SEG_SIMPANAN)

    # ── 7. CASA = Tabungan + Giro ────────────────────────────
    _cb(68, "⚙️ Memproses data CASA...")
    result["CASA"] = _combine(result["Tabungan"], result["Giro"])

    # ── 8. Total DPK = CASA + Deposito ──────────────────────
    _cb(76, "⚙️ Memproses data Total DPK...")
    result["Total DPK"] = _combine(result["CASA"], result["Deposito"])

    # ── 9. Pinjaman ─────────────────────────────────────────
    _cb(85, "⚙️ Memproses data Pinjaman...")
    df_p[kol_col] = pd.to_numeric(df_p[kol_col], errors="coerce")
    df_pinj = df_p[df_p[kol_col] == 1].copy()
    result["Pinjaman"] = _pivot_product(df_pinj, baki_col, seg_p, SEG_PINJAMAN)

    # ── 10. Merge RKA ────────────────────────────────────────
    _cb(93, "💾 Menyimpan hasil...")
    if df_rka is not None and not df_rka.empty:
        result = _merge_rka(result, df_rka)

    _cb(100, "✅ Selesai!")
    return result


def _merge_rka(data_dict: dict, df_rka: pd.DataFrame) -> dict:
    """
    Coba gabungkan kolom target RKA ke setiap sheet.
    Jika format tidak cocok, kembalikan data apa adanya.
    """
    # Cari kolom KC di RKA
    kc_candidates = ["KC", "Nama Cabang", "Cabang", "NAMA CABANG"]
    kc_rka = None
    for c in kc_candidates:
        for col in df_rka.columns:
            if c.lower() in col.lower():
                kc_rka = col
                break
        if kc_rka:
            break

    if not kc_rka:
        return data_dict  # Tidak bisa match KC — skip RKA

    df_rka["_kc"] = df_rka[kc_rka].apply(_extract_kc)

    for sheet_name, df_sheet in data_dict.items():
        # Cari kolom target RKA yang relevan
        tgt_col = None
        for col in df_rka.columns:
            if sheet_name.lower() in col.lower() and (
                "target" in col.lower() or "rka" in col.lower()
            ):
                tgt_col = col
                break

        if tgt_col:
            rka_map = dict(
                zip(
                    df_rka["_kc"],
                    pd.to_numeric(df_rka[tgt_col], errors="coerce").fillna(0),
                )
            )
            df_sheet["Target RKA"] = (
                df_sheet["KC"].map(rka_map).fillna(0)
            )

    return data_dict


def count_kc(data_dict: dict) -> int:
    """Hitung jumlah KC unik (tidak termasuk baris total)."""
    for df in data_dict.values():
        if df is not None and not df.empty and "KC" in df.columns:
            return len(df[df["KC"] != "TOTAL KESELURUHAN"])
    return 0
