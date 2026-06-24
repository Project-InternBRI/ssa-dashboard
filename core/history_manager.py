"""
history_manager.py — Kelola riwayat generate dashboard.
Menyimpan, membaca, menghapus entri dalam file JSON di folder history/.
"""
import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime

_ROOT        = Path(__file__).resolve().parent.parent
HISTORY_DIR  = _ROOT / "history"
HISTORY_FILE = HISTORY_DIR / "history.json"


def _ensure_dir() -> None:
    """Pastikan folder history/ ada."""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def load_history() -> list[dict]:
    """
    Baca seluruh riwayat dari JSON, diurutkan terbaru di atas.
    Return list kosong jika file tidak ada atau rusak.
    """
    _ensure_dir()
    if not HISTORY_FILE.exists():
        return []
    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        data.sort(key=lambda x: x.get("tanggal_proses", ""), reverse=True)
        return data
    except Exception:
        return []


def save_history(entry: dict) -> str:
    """
    Simpan satu entri riwayat baru.
    Otomatis menambahkan 'id' dan 'tanggal_proses' jika belum ada.
    Return id entri.
    """
    _ensure_dir()
    if "id" not in entry:
        entry["id"] = str(uuid.uuid4())[:8]
    if "tanggal_proses" not in entry:
        entry["tanggal_proses"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    data = load_history()
    # Hapus entri lama dengan id yang sama (jika ada update)
    data = [e for e in data if e.get("id") != entry["id"]]
    data.insert(0, entry)

    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return entry["id"]


def delete_history(entry_id: str) -> bool:
    """
    Hapus satu entri dan file Excel-nya.
    Return True jika berhasil ditemukan dan dihapus.
    """
    data = load_history()
    new_data = []
    deleted = False

    for item in data:
        if item.get("id") == entry_id:
            _delete_output_file(item)
            deleted = True
        else:
            new_data.append(item)

    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)

    return deleted


def delete_all_history() -> int:
    """
    Hapus semua entri riwayat dan file Excel-nya.
    Return jumlah entri yang dihapus.
    """
    data = load_history()
    count = len(data)
    for item in data:
        _delete_output_file(item)

    with HISTORY_FILE.open("w", encoding="utf-8") as f:
        json.dump([], f)

    return count


def get_history_file_path(entry_id: str) -> Path | None:
    """
    Return Path ke file Excel untuk satu entri.
    Return None jika entri tidak ditemukan atau file tidak ada.
    """
    for item in load_history():
        if item.get("id") == entry_id:
            output = item.get("output_path", "")
            if output:
                p = Path(output)
                if not p.is_absolute():
                    p = _ROOT / p
                if p.exists():
                    return p
    return None


def get_latest_entry() -> dict | None:
    """Return entri riwayat terbaru, atau None jika kosong."""
    data = load_history()
    return data[0] if data else None


def _delete_output_file(item: dict) -> None:
    """Hapus file Excel yang terkait dengan satu entri riwayat."""
    output = item.get("output_path", "")
    if output:
        p = Path(output)
        if not p.is_absolute():
            p = _ROOT / p
        p.unlink(missing_ok=True)
