"""
history_manager.py — Manajemen riwayat generate.
Menyimpan log ke history/history.json.
Field baru: jumlah_kc, jumlah_periode, has_historis, list_kc.
"""
import json
from pathlib import Path
from datetime import datetime

# Lokasi direktori riwayat
HISTORY_DIR  = Path(__file__).parent.parent / "history"
HISTORY_FILE = HISTORY_DIR / "history.json"


def _ensure_dir() -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    """Baca seluruh riwayat. Return list dict, terbaru di depan."""
    if not HISTORY_FILE.exists():
        return []
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_history(entry: dict) -> None:
    """
    Tambahkan satu entri baru ke riwayat.

    entry harus berisi minimal:
        tanggal_proses, tanggal_data, nama_file_simpanan,
        nama_file_pinjaman, output_path, status,
        dan field opsional: jumlah_kc, jumlah_periode,
        has_historis, list_kc, ukuran_file, waktu_proses.
    """
    _ensure_dir()
    history = load_history()

    # Pastikan semua field standar ada
    entry.setdefault("tanggal_proses",    datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    entry.setdefault("tanggal_data",      "")
    entry.setdefault("nama_file_simpanan","")
    entry.setdefault("nama_file_pinjaman","")
    entry.setdefault("output_path",       "")
    entry.setdefault("ukuran_file",       "0 KB")
    entry.setdefault("waktu_proses",      "0s")
    entry.setdefault("status",            "sukses")
    entry.setdefault("jumlah_kc",         0)
    entry.setdefault("jumlah_periode",    0)
    entry.setdefault("has_historis",      False)
    entry.setdefault("list_kc",           [])

    history.insert(0, entry)

    # Batasi 100 entri
    history = history[:100]

    try:
        HISTORY_FILE.write_text(
            json.dumps(history, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass


def delete_history_entry(index: int) -> bool:
    """Hapus satu entri berdasarkan indeks. Return True jika berhasil."""
    history = load_history()
    if 0 <= index < len(history):
        # Juga hapus file Excel output jika masih ada
        path = history[index].get("output_path", "")
        if path:
            p = Path(path)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
        history.pop(index)
        try:
            HISTORY_FILE.write_text(
                json.dumps(history, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return False
        return True
    return False


def clear_history() -> None:
    """Hapus seluruh riwayat dan file-file Excel yang tercatat."""
    history = load_history()
    for entry in history:
        path = entry.get("output_path", "")
        if path:
            p = Path(path)
            if p.exists():
                try:
                    p.unlink()
                except OSError:
                    pass
    _ensure_dir()
    try:
        HISTORY_FILE.write_text(
            json.dumps([], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass
