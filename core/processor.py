"""
processor.py — Logika pemrosesan utama SSA Dashboard.

Mapping CSV SSA ke template baris FIXED sesuai mockup Dashboard AH Gunsar.
Nilai dalam JUTA RUPIAH (dibagi 1_000_000).
Periode: tanggal terbaru dari file CSV sebagai kolom aktif,
          plus semua tanggal historis sebagai kolom tambahan.

Output per wilayah:
{
    "Veteran": {
        "rows": [...],
        "periode_list": ["20 Jun-2026", "Des-25"],
        "mtd_label": "MTD (Des-25 vs 20 Jun-26)",
        ...
    },
    "Total AH Gunsar": { ... },
    "__stats__": { ... },
}
"""
import calendar
from datetime import datetime

import pandas as pd

# ─── Import dengan fallback graceful ─────────────────────────────────
try:
    from core.file_reader import (
        find_column, diagnose_file,
        BULAN_SINGKAT, BULAN_PANJANG,
    )
except ImportError:
    find_column = None
    diagnose_file = None
    BULAN_SINGKAT = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
                     'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    BULAN_PANJANG = ['', 'Januari', 'Februari', 'Maret', 'April', 'Mei',
                     'Juni', 'Juli', 'Agustus', 'September', 'Oktober',
                     'November', 'Desember']
# Produk yang dikecualikan dari Konsumer
EXCLUDE_KONSUMER = ['lainnya']

# Produk yang dikecualikan dari Mikro
EXCLUDE_MIKRO_PRODUK = ['kur ritel']


def validasi_silang(hasil_generate, kc_name, tanggal, expected_values=None):
    if kc_name not in hasil_generate:
        return
    # In processor, data is in hasil_generate[kc_name]['rows']
    # which is a list of dicts. We need to extract the 'tanggal' column.
    rows = hasil_generate.get(kc_name, {}).get('rows', [])
    data = {}
    for r in rows:
        val = r.get('values', {}).get(tanggal, 0)
        label = r.get('label', '')
        if label == 'Pinjaman': data['pinjaman_total'] = val
        elif label == 'Pinjaman - mikro': data['pinjaman_mikro'] = val
        elif label == 'Pinjaman - small': data['pinjaman_small'] = val
        elif label == 'Pinjaman - konsumer': data['pinjaman_konsumer'] = val
        elif label == 'SML': data['sml_total'] = val
        elif label == 'mikro' and r.get('row_type') == 'data': # Wait, multiple 'mikro', we need to track blocks
            pass # Too hard to map back from rows. I will print the validation inside _build_rows directly instead!

# We'll just define the validation data
EXPECTED_GUNUNG_SAHARI_DES25 = {
    'pinjaman_total'    : 1181726.410,
    'pinjaman_mikro'    : 0.000,
    'pinjaman_small'    : 453861.945,
    'pinjaman_konsumer' : 727864.465,
    'sml_total'         : 52962.208,
    'sml_mikro'         : 0.000,
    'sml_small'         : 18969.650,
    'sml_konsumer'      : 33992.558,
    'npl_total'         : 66259.102,
    'npl_mikro'         : 0.000,
    'npl_small'         : 29672.595,
    'npl_konsumer'      : 36586.507,
}



# ────────────────────────────────────────────────────────────────────
# KONSTANTA WILAYAH
# ────────────────────────────────────────────────────────────────────
WILAYAH_ORDER = [
    'Tanah Abang',
    'Krekot',
    'Veteran',
    'Roxi',
    'Gunung Sahari',
    'Mangga Dua',
    'Kemayoran',
]

# keyword → wilayah (single keyword per wilayah, case-insensitive)
WILAYAH_KEYWORD_MAP = {
    'tanah abang':  'Tanah Abang',
    'krekot':       'Krekot',
    'veteran':      'Veteran',
    'roxi':         'Roxi',
    'gunung sahari':'Gunung Sahari',
    'mangga dua':   'Mangga Dua',
    'kemayoran':    'Kemayoran',
}


# ────────────────────────────────────────────────────────────────────
# KONSTANTA NAMA KOLOM (persis dari header CSV)
# ────────────────────────────────────────────────────────────────────
# SSA Simpanan
COL_S_KC      = "Nama Cabang"
COL_S_JENIS   = "Jenis Produk"
COL_S_SEG     = "Segmentasi BPR"
COL_S_SALDO   = "Saldo"
COL_S_PERIODE = "Month, Day, Year of Posisi"

# SSA Pinjaman
COL_P_KC      = "Nama Cabang"
COL_P_SEGMEN  = "Segmen"
COL_P_KOLEKT  = "Kolektabilitas One Obligor"
COL_P_BAKI    = "Baki Debet"
COL_P_PERIODE = "Month, Day, Year of Periode"


# ────────────────────────────────────────────────────────────────────
# PARSING NUMERIK
# ────────────────────────────────────────────────────────────────────
BULAN_ID_MAP = {
    'januari': 1,  'jan': 1,
    'februari': 2, 'feb': 2,
    'maret': 3,    'mar': 3,
    'april': 4,    'apr': 4,
    'mei': 5,      'may': 5,
    'juni': 6,     'jun': 6,
    'juli': 7,     'jul': 7,
    'agustus': 8,  'agu': 8, 'aug': 8,
    'september': 9,'sep': 9,
    'oktober': 10, 'okt': 10, 'oct': 10,
    'november': 11,'nov': 11,
    'desember': 12,'des': 12, 'dec': 12,
}



def parse_baki_debet(val):
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    try:
        return float(s)
    except ValueError:
        # Format Indonesia: koma = desimal
        s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except:
            return 0.0
    s = str(val).strip()
    s = s.replace('Rp', '').replace('Rp.', '').replace(' ', '').strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null', 'N/A'):
        return 0.0
        
    if s.replace('-', '').isdigit():
        return float(s)
        
    dots = s.count('.')
    commas = s.count(',')
    last_dot = s.rfind('.')
    last_comma = s.rfind(',')
    
    try:
        if dots > 0 and commas > 0:
            if last_comma > last_dot:
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif dots > 0:
            if dots == 1 and len(s) - last_dot != 4:
                pass 
            else:
                s = s.replace('.', '')
        elif commas > 0:
            if commas == 1 and len(s) - last_comma != 4:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
                
        return float(s)
    except ValueError:
        return 0.0
def parse_numeric(val) -> float:
    """
    Parse nilai numerik dari format Indonesia atau internasional.
    Contoh input yang dihandle:
      "366343375,68"  → 366343375.68  (koma = desimal)
      "242592783"     → 242592783.0   (integer biasa)
      "20608201345,1" → 20608201345.1
      "1.234.567,89"  → 1234567.89   (titik = ribuan, koma = desimal)
      "nan", "", None → 0.0
    """
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null', 'N/A'):
        return 0.0

    # 1. Coba langsung (float/int, scientific notation)
    try:
        return float(s)
    except ValueError:
        pass

    # 2. Hapus prefix Rp dan spasi
    s = s.replace('Rp', '').replace('\xa0', '').strip()

    # 3. Deteksi format:
    #    a) titik = ribuan, koma = desimal: "1.234.567,89"
    #    b) koma saja = desimal: "366343375,68"
    #    c) titik saja = mungkin ribuan atau desimal
    dot_pos   = s.rfind('.')
    comma_pos = s.rfind(',')

    if dot_pos != -1 and comma_pos != -1:
        if comma_pos > dot_pos:
            # titik = ribuan, koma = desimal → "1.234.567,89"
            s = s.replace('.', '').replace(',', '.')
        else:
            # koma = ribuan, titik = desimal → "1,234,567.89"
            s = s.replace(',', '')
    elif comma_pos != -1:
        # Hanya koma → koma sebagai desimal
        s = s.replace(',', '.')
    elif dot_pos != -1:
        # Hanya titik → jika lebih dari satu kemungkinan ribuan
        if s.count('.') > 1:
            s = s.replace('.', '')
        # jika hanya satu titik → biarkan sebagai desimal

    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_tanggal_id(tgl_str) -> pd.Timestamp | None:
    """
    Parse tanggal format Indonesia: "20 Juni 2026", "20 Jun 2026"
    atau format standar: "2026-06-20", datetime object.
    """
    if pd.isna(tgl_str) or tgl_str is None:
        return None
    if isinstance(tgl_str, pd.Timestamp):
        return tgl_str
    if isinstance(tgl_str, datetime):
        return pd.Timestamp(tgl_str)

    s = str(tgl_str).strip()
    parts = s.split()
    if len(parts) >= 3:
        bulan_key = parts[1].lower().rstrip('.')
        bulan = BULAN_ID_MAP.get(bulan_key)
        if bulan:
            try:
                return pd.Timestamp(
                    year=int(parts[2]),
                    month=bulan,
                    day=int(parts[0])
                )
            except Exception:
                pass

    try:
        return pd.to_datetime(s, dayfirst=True)
    except Exception:
        return None


def format_label(ts: pd.Timestamp) -> str:
    """
    Timestamp → label periode:
    Akhir bulan: "Des-25", "Jun-26"
    Tengah bulan: "20 Jun-2026"
    """
    if ts is None:
        return "Unknown"
    akhir = calendar.monthrange(ts.year, ts.month)[1]
    bln = BULAN_SINGKAT[ts.month]
    thn2 = str(ts.year)[-2:]
    if ts.day >= akhir - 1:
        return f"{bln}-{thn2}"
    else:
        return f"{ts.day} {bln}-{ts.year}"


# ────────────────────────────────────────────────────────────────────
# MAPPING WILAYAH
# ────────────────────────────────────────────────────────────────────
def map_to_wilayah(nama_cabang) -> str | None:
    """
    Map nama cabang ke nama wilayah.
    Contoh: "00356 -- KC JAKARTA KEMAYORAN (Konsolidasi-MB)" → "Kemayoran"
    """
    if not isinstance(nama_cabang, str):
        return None
    s = nama_cabang.lower()
    for keyword, wilayah in WILAYAH_KEYWORD_MAP.items():
        if keyword in s:
            return wilayah
    return None


# ────────────────────────────────────────────────────────────────────
# BACA FILE CSV SSA
# ────────────────────────────────────────────────────────────────────
def _read_ssa_csv(path: str, label: str) -> pd.DataFrame:
    """
    Baca file CSV SSA dengan delimiter semicolon dan encoding utf-8-sig.
    Semua kolom dibaca sebagai string, lalu konversi di tahap berikutnya.
    """
    import os
    from pathlib import Path

    ext = Path(path).suffix.lower()

    if ext == '.csv':
        import io
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        df = None
        
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    lines = f.readlines()
                    
                if not lines:
                    continue
                    
                header = lines[0].strip().split(';')
                header_len = len(header)
                
                fixed_lines = [lines[0].strip()]
                for i in range(1, len(lines)):
                    line = lines[i].strip()
                    if not line:
                        continue
                    parts = line.split(';')
                    
                    if len(parts) > header_len:
                        for j in range(1, len(parts)-1):
                            if parts[j].strip() == '':
                                del parts[j]
                                if len(parts) == header_len:
                                    break
                        if len(parts) > header_len:
                            parts = parts[:header_len]
                            
                    elif len(parts) < header_len:
                        parts.extend([''] * (header_len - len(parts)))
                        
                    fixed_lines.append(';'.join(parts))
                    
                fixed_csv = '\n'.join(fixed_lines)
                
                df = pd.read_csv(
                    io.StringIO(fixed_csv),
                    sep=';',
                    dtype=str,
                    skipinitialspace=True,
                    low_memory=False,
                )
                
                if len(df.columns) >= 3:
                    break
                df = None
            except Exception as e:
                continue
                
        if df is None:
            raise ValueError(f"Tidak dapat membaca {label}: {Path(path).name}")

    elif ext in ('.xlsx', '.xlsm'):
        df = pd.read_excel(path, engine='openpyxl', dtype=str)
    elif ext == '.xls':
        df = pd.read_excel(path, engine='xlrd', dtype=str)
    elif ext == '.xlsb':
        df = pd.read_excel(path, engine='pyxlsb', dtype=str)
    else:
        raise ValueError(f"Format tidak didukung: {ext}")

    # Bersihkan nama kolom
    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(how='all').reset_index(drop=True)

    print(f"  [{label}] {Path(path).name}: {df.shape[0]} baris, {df.shape[1]} kolom")
    if len(df.columns) <= 5:
        print(f"  [{label}] Kolom: {list(df.columns)}")

    return df


def _find_col(df: pd.DataFrame, *candidates) -> str | None:
    """Cari kolom dari beberapa kandidat (exact match, lalu partial)."""
    cols = list(df.columns)
    for c in candidates:
        if c in cols:
            return c
    # Partial match case-insensitive
    for c in candidates:
        for col in cols:
            if c.lower() in col.lower():
                return col
    return None


# ────────────────────────────────────────────────────────────────────
# AGREGASI DATA
# ────────────────────────────────────────────────────────────────────
def _sum_saldo(df: pd.DataFrame, wilayah: str, label: str,
               jenis: str, segmentasi: str, saldo_col: str) -> float:
    """
    SUM(Saldo) WHERE Jenis Produk=jenis AND Segmentasi BPR=segmentasi
    AND _wilayah=wilayah AND _label=label
    Hasil dalam JUTA RUPIAH.
    """
    if wilayah == '__TOTAL__':
        mask = df['_wilayah'].isin(WILAYAH_ORDER)
    else:
        mask = df['_wilayah'] == wilayah
        
    if label is not None and '_label' in df.columns:
        mask &= df['_label'] == label
    if jenis:
        mask &= df['_jenis'].str.lower() == jenis.lower()
    if segmentasi:
        mask &= df['_segmentasi'].str.lower() == segmentasi.lower()

    total = df.loc[mask, saldo_col].sum()
    return float(total) / 1_000_000


def _sum_baki(df: pd.DataFrame, wilayah: str, tanggal: pd.Timestamp | None,
              segmen: str | None, kolekt_vals: list[int], baki_col: str) -> float:
    """
    SUM(Baki Debet) WHERE Kolektabilitas IN kolekt_vals
    AND Segmen=segmen (opsional) AND _wilayah=wilayah AND _tanggal=tanggal
    Hasil dalam JUTA RUPIAH.
    """
    mask = df['_wilayah'] == wilayah
    if tanggal is not None and '_tanggal' in df.columns:
        mask &= df['_tanggal'] == tanggal
    if kolekt_vals:
        mask &= df['_kolekt'].isin([str(k) for k in kolekt_vals])
    if segmen:
        mask &= df['_segmen'].str.lower() == segmen.lower()

    total = df.loc[mask, baki_col].sum()
    return float(total) / 1_000_000


# ────────────────────────────────────────────────────────────────────
# TEMPLATE BARIS FIXED
# ────────────────────────────────────────────────────────────────────

def build_pinjaman_rows(df_pinj, wilayah, label, baki_col):
    if wilayah == '__TOTAL__':
        mask_kc = df_pinj['_wilayah'].isin(WILAYAH_ORDER)
    else:
        mask_kc = (df_pinj['_wilayah'] == wilayah)
    mask_tgl = (df_pinj['_label'] == label) if '_label' in df_pinj.columns else (df_pinj['_tanggal'] == label)
    df = df_pinj[mask_kc & mask_tgl].copy()
    
    if df.empty:
        return {
            'pinjaman_mikro': 0.0, 'pinjaman_small': 0.0, 'pinjaman_konsumer': 0.0, 'pinjaman_total': 0.0,
            'sml_mikro': 0.0, 'sml_small': 0.0, 'sml_konsumer': 0.0, 'sml_total': 0.0,
            'sml_pct': 0.0, 'sml_pct_mikro': 0.0, 'sml_pct_small': 0.0, 'sml_pct_konsumer': 0.0,
            'npl_mikro': 0.0, 'npl_small': 0.0, 'npl_konsumer': 0.0, 'npl_total': 0.0,
            'npl_pct': 0.0, 'npl_pct_mikro': 0.0, 'npl_pct_small': 0.0, 'npl_pct_konsumer': 0.0,
        }
    
    import pandas as pd
    def safe_pct(num, den):
        if den == 0 or pd.isna(den):
            return "-"
        return round(num / den, 6)
    
    def sum_seg_kol(segmen, kolektabilitas):
        mask_seg = (df['segmen_dashboard'] == segmen)
        if isinstance(kolektabilitas, list):
            mask_kol = df['_kolekt'].isin(kolektabilitas)
        else:
            mask_kol = (df['_kolekt'] == kolektabilitas)
        return df[mask_seg & mask_kol][baki_col].sum() / 1_000_000
        
    p_mikro   = sum_seg_kol('Mikro',    [1, 2, 3, 4, 5])
    p_small   = sum_seg_kol('Small',    [1, 2, 3, 4, 5])
    p_konsumer= sum_seg_kol('Konsumer', [1, 2, 3, 4, 5])
    
    s_mikro   = sum_seg_kol('Mikro',    2)
    s_small   = sum_seg_kol('Small',    2)
    s_konsumer= sum_seg_kol('Konsumer', 2)
    
    n_mikro   = sum_seg_kol('Mikro',    [3, 4, 5])
    n_small   = sum_seg_kol('Small',    [3, 4, 5])
    n_konsumer= sum_seg_kol('Konsumer', [3, 4, 5])
    
    p_total   = p_mikro + p_small + p_konsumer
    s_total   = s_mikro + s_small + s_konsumer
    n_total   = n_mikro + n_small + n_konsumer
    
    s_pct       = safe_pct(s_total,   p_total)
    s_pct_mikro = safe_pct(s_mikro,   p_mikro)
    s_pct_small = safe_pct(s_small,   p_small)
    s_pct_kons  = safe_pct(s_konsumer, p_konsumer)
    
    n_pct       = safe_pct(n_total,   p_total)
    n_pct_mikro = safe_pct(n_mikro,   p_mikro)
    n_pct_small = safe_pct(n_small,   p_small)
    n_pct_kons  = safe_pct(n_konsumer, p_konsumer)
    
    res = {
        'pinjaman_mikro': p_mikro, 'pinjaman_small': p_small, 'pinjaman_konsumer': p_konsumer, 'pinjaman_total': p_total,
        'sml_mikro': s_mikro, 'sml_small': s_small, 'sml_konsumer': s_konsumer, 'sml_total': s_total,
        'sml_pct': s_pct, 'sml_pct_mikro': s_pct_mikro, 'sml_pct_small': s_pct_small, 'sml_pct_konsumer': s_pct_kons,
        'npl_mikro': n_mikro, 'npl_small': n_small, 'npl_konsumer': n_konsumer, 'npl_total': n_total,
        'npl_pct': n_pct, 'npl_pct_mikro': n_pct_mikro, 'npl_pct_small': n_pct_small, 'npl_pct_konsumer': n_pct_kons,
    }
    
    if wilayah == "Gunung Sahari" and label == "Des-25":
        print(f"\n=== VALIDASI SILANG: {wilayah} - 31 Desember 2025 ===")
        fields = [
            ('pinjaman_total',   'Pinjaman Total'),
            ('pinjaman_mikro',   'Pinjaman Mikro'),
            ('pinjaman_small',   'Pinjaman Small'),
            ('pinjaman_konsumer','Pinjaman Konsumer'),
            ('sml_total',        'SML Total'),
            ('sml_mikro',        'SML Mikro'),
            ('sml_small',        'SML Small'),
            ('sml_konsumer',     'SML Konsumer'),
            ('npl_total',        'NPL Total'),
            ('npl_mikro',        'NPL Mikro'),
            ('npl_small',        'NPL Small'),
            ('npl_konsumer',     'NPL Konsumer'),
        ]
        
        # Define expected values safely inside the function
        EXPECTED_GUNUNG_SAHARI_DES25 = {
            'pinjaman_total'    : 1181726.410,
            'pinjaman_mikro'    : 0.000,
            'pinjaman_small'    : 453861.945,
            'pinjaman_konsumer' : 727864.465,
            'sml_total'         : 52962.208,
            'sml_mikro'         : 0.000,
            'sml_small'         : 18969.650,
            'sml_konsumer'      : 33992.558,
            'npl_total'         : 66259.102,
            'npl_mikro'         : 0.000,
            'npl_small'         : 29672.595,
            'npl_konsumer'      : 36586.507,
        }
        
        for key, label in fields:
            val = res.get(key, 0)
            print(f'  {label}: {val:>15,.3f}')
            if key in EXPECTED_GUNUNG_SAHARI_DES25:
                exp = EXPECTED_GUNUNG_SAHARI_DES25[key]
                selisih = abs(val - exp)
                status = '✓' if selisih < 1.0 else f'✗ SELISIH {selisih:.3f}'
                print(f'    Expected: {exp:>12,.3f}  {status}')
                
        check = p_mikro + p_small + p_konsumer
        if abs(check - p_total) > 0.001:
            print(f'  ⚠ INKONSISTENSI: Mikro+Small+Konsumer={check:.3f} ≠ Total={p_total:.3f}')
            
    return res


def classify_pinjaman_exact(row) -> str | None:
    import re
    def norm(s):
        return re.sub(r'[\s\-]', '', str(s)).lower()
        
    produk = norm(row.get('Produk', ''))
    segmen = norm(row.get('SEGMEN_2025', ''))
    
    mikro_prods = ['brigunamikro', 'kupedes', 'kurmikro', 'kreditmikrokpp', 'mikrocashcollateral', 'kreditmikrokurritel2015']
    if produk in mikro_prods and segmen == 'micro':
        return 'Mikro'
        
    if produk == 'kecilkomersial' and segmen == 'small':
        return 'Small'
        
    konsumer_prods = ['brigunaritel', 'kpr']
    if produk in konsumer_prods and segmen == 'consumer':
        return 'Konsumer'
        
    return None

def prepare_pinjaman(df: pd.DataFrame) -> pd.DataFrame:
    '''
    Melakukan preprocessing data pinjaman, mencakup pembersihan dan parsing Baki Debet.
    Hanya membuang baris yang Kolektabilitas-nya = 0, atau Baki Debet-nya NaN/0.
    '''
    df = df.copy()
    
    # 1. Bersihkan whitespace dan klasifikasikan segmen_dashboard
    for col in ['SEGMEN_2025', 'Produk', 'Nama Cabang']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    if 'Produk' in df.columns and 'SEGMEN_2025' in df.columns:
        df['segmen_dashboard'] = df.apply(classify_pinjaman_exact, axis=1)
    
    # 2. Konversi Baki Debet ke float
    def parse_num(v):
        s = str(v).strip()
        try: return float(s)
        except:
            s = s.replace('.','').replace(',','.')
            try: return float(s)
            except: return 0.0
    
    if 'Baki Debet' in df.columns:
        df['Baki Debet'] = df['Baki Debet'].apply(parse_num)
    
    # 3. Konversi Kolektabilitas ke integer
    if 'Kolektabilitas One Obligor' in df.columns:
        df['Kolektabilitas One Obligor'] = pd.to_numeric(
            df['Kolektabilitas One Obligor'], errors='coerce'
        ).fillna(0).astype(int)
    
    # 4. Exclude Kolektabilitas = 0
    if 'Kolektabilitas One Obligor' in df.columns:
        df = df[df['Kolektabilitas One Obligor'] != 0].copy()
    
    # 5. Exclude Baki Debet NaN atau 0
    if 'Baki Debet' in df.columns:
        df = df[df['Baki Debet'].notna() & (df['Baki Debet'] != 0)].copy()
    
    return df

def _zero_result():
    keys = ['pinjaman','pinjaman_mikro','pinjaman_small','pinjaman_konsumer',
            'sml','sml_pct','sml_mikro','sml_mikro_pct',
            'sml_small','sml_small_pct','sml_konsumer','sml_konsumer_pct',
            'npl','npl_pct','npl_mikro','npl_mikro_pct',
            'npl_small','npl_small_pct','npl_konsumer','npl_konsumer_pct',
            'recovery_ec','recovery_ec_mikro','recovery_ec_small','recovery_ec_konsumer']
    return {k: 0.0 for k in keys}

def hitung_pinjaman_kc(df_pinj, kc_keyword, tanggal):
    '''
    Menghitung semua nilai pinjaman untuk satu KC dan satu periode.
    df_pinj sudah melalui prepare_pinjaman().
    '''
    if 'Nama Cabang' not in df_pinj.columns or 'Month, Day, Year of Periode' not in df_pinj.columns:
        return _zero_result()

    # Filter KC
    if kc_keyword == '__TOTAL__':
        mask_kc = df_pinj['_wilayah'].isin(WILAYAH_ORDER)
    else:
        mask_kc = df_pinj['_wilayah'] == kc_keyword
        
    # Filter tanggal
    mask_tgl = (df_pinj['_label'] == tanggal)
    df = df_pinj[mask_kc & mask_tgl].copy()
    
    if df.empty:
        return _zero_result()
    
    def s(m): return df[m]['Baki Debet'].sum() / 1_000_000
    def safe_pct(num, den):
        return round(num/den, 6) if den and den != 0 else None
    
    # Mask dasar per segmen dari klasifikasi yang sudah dihitung
    m_small    = df['segmen_dashboard'] == 'Small'
    m_consumer = df['segmen_dashboard'] == 'Konsumer'
    m_micro    = df['segmen_dashboard'] == 'Mikro'
    
    # Mask kolektabilitas
    m_kol2   = df['Kolektabilitas One Obligor'] == 2
    m_kol345 = df['Kolektabilitas One Obligor'].isin([3, 4, 5])
    
    # Hitung nilai
    small    = s(m_small)
    konsumer = s(m_consumer)
    mikro    = s(m_micro)
    total_p  = small + konsumer + mikro
    
    sml_small    = s(m_small    & m_kol2)
    sml_konsumer = s(m_consumer & m_kol2)
    sml_mikro    = s(m_micro    & m_kol2)
    sml_total    = sml_small + sml_konsumer + sml_mikro
    
    npl_small    = s(m_small    & m_kol345)
    npl_konsumer = s(m_consumer & m_kol345)
    npl_mikro    = s(m_micro    & m_kol345)
    npl_total    = npl_small + npl_konsumer + npl_mikro
    
    return {
        'pinjaman'         : total_p,
        'pinjaman_mikro'   : mikro,
        'pinjaman_small'   : small,
        'pinjaman_konsumer': konsumer,
        'sml'              : sml_total,
        'sml_pct'          : safe_pct(sml_total, total_p),
        'sml_mikro'        : sml_mikro,
        'sml_mikro_pct'    : safe_pct(sml_mikro, mikro),
        'sml_small'        : sml_small,
        'sml_small_pct'    : safe_pct(sml_small, small),
        'sml_konsumer'     : sml_konsumer,
        'sml_konsumer_pct' : safe_pct(sml_konsumer, konsumer),
        'npl'              : npl_total,
        'npl_pct'          : safe_pct(npl_total, total_p),
        'npl_mikro'        : npl_mikro,
        'npl_mikro_pct'    : safe_pct(npl_mikro, mikro),
        'npl_small'        : npl_small,
        'npl_small_pct'    : safe_pct(npl_small, small),
        'npl_konsumer'     : npl_konsumer,
        'npl_konsumer_pct' : safe_pct(npl_konsumer, konsumer),
        'recovery_ec'         : None,
        'recovery_ec_mikro'   : None,
        'recovery_ec_small'   : None,
        'recovery_ec_konsumer': None,
    }

def log_pinjaman_debug(df_pinj, kc_keyword, tanggal, hasil):
    if 'Nama Cabang' not in df_pinj.columns or '_label' not in df_pinj.columns:
        return
    df_kc = df_pinj[
        df_pinj['Nama Cabang'].str.lower().str.contains(kc_keyword.lower(), na=False) &
        (df_pinj['_label'] == tanggal)
    ]
    print(f'\n[DEBUG] {kc_keyword} - {tanggal}')
    print(f'  Total baris: {len(df_kc)}')
    print(f'  SEGMEN_2025 unik: {sorted(df_kc["SEGMEN_2025"].unique())}')
    print(f'  Produk unik: {sorted(df_kc["Produk"].unique())}')
    print(f'  Pinjaman: {hasil["pinjaman"]:,.1f}')
    print(f'  Small: {hasil["pinjaman_small"]:,.1f}')
    print(f'  Konsumer: {hasil["pinjaman_konsumer"]:,.1f}')
    print(f'  Mikro: {hasil["pinjaman_mikro"]:,.1f}')
    sml = hasil.get('sml', 0) or 0
    sml_pct = hasil.get('sml_pct', 0) or 0
    npl = hasil.get('npl', 0) or 0
    npl_pct = hasil.get('npl_pct', 0) or 0
    print(f'  SML: {sml:,.1f} ({sml_pct:.2%})')
    print(f'  NPL: {npl:,.1f} ({npl_pct:.2%})')


def _build_rows(wilayah: str, df_s: pd.DataFrame, df_p: pd.DataFrame,

                periodes_sorted: list[tuple], saldo_col: str,
                baki_col: str) -> list[dict]:
    """
    Bangun template baris FIXED untuk satu wilayah.
    periodes_sorted: list of (label, pd.Timestamp), diurutkan lama→baru
    Semua nilai dalam JUTA RUPIAH.
    """
    def row(row_type: str, label: str, get_fn):
        """Buat satu baris dengan values per periode."""
        vals = {}
        for lbl, tgl in periodes_sorted:
            vals[lbl] = get_fn(lbl)
        return {
            'row_type': row_type,
            'label': label,
            'values': vals,
        }

    rows = []
    periode_labels = [p[0] for p in periodes_sorted]

    # Helper khusus untuk menghitung DPK (memasukkan Micro khusus Krekot dan Roxi)
    def _get_dpk(wil, tgl, jenis):
        if wil == '__TOTAL__':
            total_val = 0
            for w in WILAYAH_ORDER:
                val = _sum_saldo(df_s, w, tgl, jenis, 'Ritel', saldo_col)
                if w.lower() in ['krekot', 'roxi', 'roxy']:
                    val += _sum_saldo(df_s, w, tgl, jenis, 'Micro', saldo_col)
                total_val += val
            return total_val
        else:
            val = _sum_saldo(df_s, wil, tgl, jenis, 'Ritel', saldo_col)
            if wil.lower() in ['krekot', 'roxi', 'roxy']:
                val += _sum_saldo(df_s, wil, tgl, jenis, 'Micro', saldo_col)
            return val

    # ── BLOK 1: Dana Pihak Ketiga (Ritel + Micro khusus cabang tertentu) ──
    rows.append(row('header_value', 'Dana Pihak Ketiga',
        lambda t: _get_dpk(wilayah, t, 'Tabungan') + _get_dpk(wilayah, t, 'Giro') + _get_dpk(wilayah, t, 'Deposito')
    ))

    rows.append(row('data', 'Tabungan', lambda t: _get_dpk(wilayah, t, 'Tabungan')))
    rows.append(row('data', 'Giro', lambda t: _get_dpk(wilayah, t, 'Giro')))
    rows.append(row('data', 'Deposito', lambda t: _get_dpk(wilayah, t, 'Deposito')))

    # CASA = Tabungan + Giro
    rows.append(row('bold', 'CASA',
        lambda t: _get_dpk(wilayah, t, 'Tabungan') + _get_dpk(wilayah, t, 'Giro')
    ))

    # DPK Korporasi (Wholesale)
    rows.append(row('header_value', 'DPK Korporasi',
        lambda t: (
            _sum_saldo(df_s, wilayah, t, 'Giro', 'Wholesale', saldo_col) +
            _sum_saldo(df_s, wilayah, t, 'Deposito', 'Wholesale', saldo_col)
        )))

    rows.append(row('data', 'Giro',
        lambda t: _sum_saldo(df_s, wilayah, t, 'Giro', 'Wholesale', saldo_col)))

    rows.append(row('data', 'Deposito',
        lambda t: _sum_saldo(df_s, wilayah, t, 'Deposito', 'Wholesale', saldo_col)))

    rows.append({'row_type': 'separator', 'label': '', 'values': {}})


    # ── HITUNG SEMUA NILAI PINJAMAN DULU ──────────────────────────
    pinjaman_data = {}
    for lbl, tgl in periodes_sorted:
        hasil = hitung_pinjaman_kc(df_p, wilayah, lbl)
        pinjaman_data[lbl] = hasil
        log_pinjaman_debug(df_p, wilayah, lbl, hasil)

    def p_row(row_type: str, label: str, key: str):
        vals = {}
        for lbl, tgl in periodes_sorted:
            vals[lbl] = pinjaman_data[lbl].get(key) # can be None
        return {'row_type': row_type, 'label': label, 'values': vals}

    # ── BLOK 2: Pinjaman ────────────────────────────────────────
    rows.append(p_row('header_value', 'Pinjaman', 'pinjaman'))
    rows.append(p_row('data', 'Mikro', 'pinjaman_mikro'))
    rows.append(p_row('data', 'Small', 'pinjaman_small'))
    rows.append(p_row('data', 'Konsumer', 'pinjaman_konsumer'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    # ── BLOK 3: SML ─────────────────────────────────────────────
    rows.append(p_row('bold', 'SML', 'sml'))
    rows.append(p_row('bold', 'SML %', 'sml_pct'))
    rows.append(p_row('data', 'Mikro', 'sml_mikro'))
    rows.append(p_row('data', 'Mikro %', 'sml_mikro_pct'))
    rows.append(p_row('data', 'Small', 'sml_small'))
    rows.append(p_row('data', 'Small %', 'sml_small_pct'))
    rows.append(p_row('data', 'Konsumer', 'sml_konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'sml_konsumer_pct'))

    # ── BLOK 4: NPL ─────────────────────────────────────────────
    rows.append(p_row('bold', 'NPL', 'npl'))
    rows.append(p_row('bold', 'NPL %', 'npl_pct'))
    rows.append(p_row('data', 'Mikro', 'npl_mikro'))
    rows.append(p_row('data', 'Mikro %', 'npl_mikro_pct'))
    rows.append(p_row('data', 'Small', 'npl_small'))
    rows.append(p_row('data', 'Small %', 'npl_small_pct'))
    rows.append(p_row('data', 'Konsumer', 'npl_konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'npl_konsumer_pct'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    # ── BLOK 5: Recovery EC ─────────────────────────────────────
    rows.append(p_row('header', 'Recovery. EC', 'recovery_ec'))
    rows.append(p_row('data', 'Mikro', 'recovery_ec_mikro'))
    rows.append(p_row('data', 'Small', 'recovery_ec_small'))
    rows.append(p_row('data', 'Konsumer', 'recovery_ec_konsumer'))

    # ── Hitung Growth per baris ──────────────────────────────────

    rows = _attach_growth(rows, periodes_sorted)

    return rows


TIPE_BARIS_TERBALIK = {
    'SML', 'SML %', 'SML > Mikro', 'Mikro %',
    'SML > Small', 'Small %', 'SML > Konsumer', 'Konsumer %',
    'NPL', 'NPL %', 'NPL > Mikro', 'NPL > Small',
    'NPL > Konsumer',
    'Mikro % NPL', 'Small % NPL', 'Konsumer % NPL'
}

TIPE_GROWTH_TERBALIK = TIPE_BARIS_TERBALIK

def tentukan_periode_referensi(periode_list, tanggal_terbaru):
    from dateutil.relativedelta import relativedelta

    hasil = {
        'terbaru'  : tanggal_terbaru,
        'mtd_ref'  : None,
        'dtd_ref'  : None,
        'yoy_ref'  : None,
        'ytd_ref'  : None,
    }

    if not periode_list or not tanggal_terbaru:
        return hasil

    sorted_list = sorted(periode_list)
    try:
        idx_terbaru = sorted_list.index(tanggal_terbaru)
    except ValueError:
        return hasil

    if idx_terbaru > 0:
        hasil['dtd_ref'] = sorted_list[idx_terbaru - 1]

    bulan_sebelumnya = tanggal_terbaru - relativedelta(months=1)
    target_bulan = bulan_sebelumnya.month
    target_tahun = bulan_sebelumnya.year
    kandidat_mtd = [
        t for t in sorted_list
        if t.month == target_bulan and t.year == target_tahun
    ]
    if kandidat_mtd:
        hasil['mtd_ref'] = max(kandidat_mtd)

    target_bulan_yoy = tanggal_terbaru.month
    target_tahun_yoy = tanggal_terbaru.year - 1
    kandidat_yoy = [
        t for t in sorted_list
        if t.month == target_bulan_yoy and t.year == target_tahun_yoy
    ]
    if kandidat_yoy:
        hasil['yoy_ref'] = max(kandidat_yoy)

    target_tahun_ytd = tanggal_terbaru.year - 1
    kandidat_ytd = [
        t for t in sorted_list
        if t.month == 12 and t.year == target_tahun_ytd
    ]
    if kandidat_ytd:
        hasil['ytd_ref'] = max(kandidat_ytd)

    return hasil

def hitung_pencapaian_rka(nama_baris, nilai_terbaru, rka):
    if not nilai_terbaru or not rka or rka == 0:
        return None
    if nama_baris in TIPE_BARIS_TERBALIK:
        return round(rka / nilai_terbaru, 6) if nilai_terbaru != 0 else None
    else:
        return round(nilai_terbaru / rka, 6)

def hitung_growth(nama_baris, nilai_terbaru, nilai_ref):
    if nilai_terbaru is None or nilai_ref is None:
        return None
    
    # Kondisi khusus Recovery EC: YOY = Terbaru
    if "Recovery" in nama_baris and nilai_ref == 'YOY_SPECIAL':
        return nilai_terbaru
    
    try:
        selisih = float(nilai_terbaru) - float(nilai_ref)
    except (ValueError, TypeError):
        return None
        
    if nama_baris in TIPE_GROWTH_TERBALIK:
        return -selisih
    return selisih

def hitung_semua_growth_dan_rka(data_per_periode, rka_values,
                                 periode_refs, nama_baris):
    if not periode_refs['terbaru']:
        return {'pencapaian_rka': None, 'mtd': None, 'dtd': None, 'yoy': None, 'ytd': None}

    terbaru_label  = format_label(periode_refs['terbaru'])
    dtd_label      = format_label(periode_refs['dtd_ref']) if periode_refs['dtd_ref'] else None
    mtd_label      = format_label(periode_refs['mtd_ref']) if periode_refs['mtd_ref'] else None
    yoy_label      = format_label(periode_refs['yoy_ref']) if periode_refs['yoy_ref'] else None
    ytd_label      = format_label(periode_refs['ytd_ref']) if periode_refs['ytd_ref'] else None

    val_terbaru = data_per_periode.get(terbaru_label)
    val_dtd_ref = data_per_periode.get(dtd_label) if dtd_label else None
    val_mtd_ref = data_per_periode.get(mtd_label) if mtd_label else None
    val_yoy_ref = data_per_periode.get(yoy_label) if yoy_label else None
    val_ytd_ref = data_per_periode.get(ytd_label) if ytd_label else None

    rka = None
    if rka_values:
        rka = rka_values.get(terbaru_label) or rka_values.get(f'Jun-{str(periode_refs["terbaru"].year)[2:]}')
        
    yoy_calc = val_yoy_ref
    if "Recovery" in nama_baris:
        yoy_calc = 'YOY_SPECIAL'
        
    if "%" in nama_baris:
        val_mtd_ref = None # Sesuai aturan: Baris % tidak memiliki MTD yang bermakna

    return {
        'pencapaian_rka' : hitung_pencapaian_rka(nama_baris, val_terbaru, rka),
        'mtd'            : hitung_growth(nama_baris, val_terbaru, val_mtd_ref),
        'dtd'            : hitung_growth(nama_baris, val_terbaru, val_dtd_ref),
        'yoy'            : hitung_growth(nama_baris, val_terbaru, yoy_calc),
        'ytd'            : hitung_growth(nama_baris, val_terbaru, val_ytd_ref),
    }

def _attach_growth(rows: list[dict], periodes_sorted: list[tuple]) -> list[dict]:
    if not periodes_sorted:
        return rows
        
    periode_list = [t for l, t in periodes_sorted if t is not None]
    if not periode_list:
        return rows
        
    tanggal_terbaru = max(periode_list)
    periode_refs = tentukan_periode_referensi(periode_list, tanggal_terbaru)
    
    # Save periode refs dynamically so exporter can use them if needed
    rows.append({'row_type': '__metadata__', 'periode_refs': periode_refs})
    
    for r in rows:
        if r.get('row_type') in ('separator', '__metadata__'):
            continue
            
        nama_baris = r.get('label', '')
        vals = r.get('values', {})
        
        # Calculate growth using the helper (RKA is passed as None here, handled in exporter)
        res = hitung_semua_growth_dan_rka(vals, None, periode_refs, nama_baris)
        r.update(res)
        
    return rows

def _growth_labels(periodes_sorted: list[tuple]) -> dict:
    labels = {
        'mtd_label': 'MTD',
        'dtd_label': 'DTD',
        'yoy_label': 'YOY',
        'ytd_label': 'YTD',
    }
    
    periode_list = [t for l, t in periodes_sorted if t is not None]
    if not periode_list:
        return labels
        
    tanggal_terbaru = max(periode_list)
    refs = tentukan_periode_referensi(periode_list, tanggal_terbaru)
    
    try:
        from core.file_reader import BULAN_SINGKAT
    except ImportError:
        BULAN_SINGKAT = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    
    terbaru_dt = refs['terbaru']
    if terbaru_dt:
        t_str = f"{terbaru_dt.day} {BULAN_SINGKAT[terbaru_dt.month]} {str(terbaru_dt.year)[-2:]}"
        t_str_dtd = f"{terbaru_dt.day} {BULAN_SINGKAT[terbaru_dt.month]}"
        
        mtd_ref = refs['mtd_ref']
        if mtd_ref:
            p_str = f"{BULAN_SINGKAT[mtd_ref.month]} {str(mtd_ref.year)[-2:]}"
            labels['mtd_label'] = f"MTD\n({p_str} vs {t_str})"
            
        dtd_ref = refs['dtd_ref']
        if dtd_ref:
            d_str = f"{dtd_ref.day} {BULAN_SINGKAT[dtd_ref.month]}"
            labels['dtd_label'] = f"DTD\n({d_str} vs {t_str_dtd})"
            
    return labels


# ────────────────────────────────────────────────────────────────────
# ENTRY POINT UTAMA
# ────────────────────────────────────────────────────────────────────
def process_files(
    path_simpanan_berjalan: str,
    path_pinjaman_berjalan: str,
    path_simpanan_historis: list[str] | None = None,
    path_pinjaman_historis: list[str] | None = None,
    callback=None,
) -> dict:
    """
    Proses file SSA Simpanan dan Pinjaman ke format dashboard.
    Returns: dict per wilayah + "Total AH Gunsar" + "__stats__"
    """
    if path_simpanan_historis is None:
        path_simpanan_historis = []
    if path_pinjaman_historis is None:
        path_pinjaman_historis = []

    def cb(pct: int, msg: str):
        if callback:
            callback(pct, msg)

    # ── 1. BACA FILE SIMPANAN ─────────────────────────────────────
    cb(5, "Membaca file SSA Simpanan...")
    all_s_paths = [path_simpanan_berjalan] + list(path_simpanan_historis)
    frames_s = []
    for i, p in enumerate(all_s_paths):
        try:
            df = _read_ssa_csv(p, f"Simpanan-{i}")
            frames_s.append(df)
        except Exception as e:
            raise RuntimeError(f"Gagal membaca SSA Simpanan: {e}") from e

    df_s_all = pd.concat(frames_s, ignore_index=True)
    df_s_all.dropna(how='all', inplace=True)
    n_rows_s = len(df_s_all)

    print(f"\n[SIMPANAN] Total baris: {n_rows_s}")
    print(f"[SIMPANAN] Kolom: {list(df_s_all.columns[:10])}")

    # ── 2. BACA FILE PINJAMAN ─────────────────────────────────────
    cb(15, "Membaca file SSA Pinjaman...")
    all_p_paths = [path_pinjaman_berjalan] + list(path_pinjaman_historis)
    frames_p = []
    for i, p in enumerate(all_p_paths):
        try:
            df = _read_ssa_csv(p, f"Pinjaman-{i}")
            frames_p.append(df)
        except Exception as e:
            raise RuntimeError(f"Gagal membaca SSA Pinjaman: {e}") from e

    df_p_all = pd.concat(frames_p, ignore_index=True)
    df_p_all.dropna(how='all', inplace=True)
    n_rows_p = len(df_p_all)

    print(f"\n[PINJAMAN] Total baris: {n_rows_p}")
    print(f"[PINJAMAN] Kolom: {list(df_p_all.columns[:10])}")

    # ── 3. TEMUKAN KOLOM ──────────────────────────────────────────
    cb(22, "Mencocokkan kolom...")

    kc_col_s   = _find_col(df_s_all, COL_S_KC, "Cabang", "KC")
    jenis_col  = _find_col(df_s_all, COL_S_JENIS, "Jenis", "Produk")
    seg_col    = _find_col(df_s_all, COL_S_SEG, "Segmentasi", "Segmen")
    saldo_col  = _find_col(df_s_all, COL_S_SALDO, "Outstanding", "Balance")
    periode_s  = _find_col(df_s_all, COL_S_PERIODE, "Posisi", "Tanggal")

    missing_s = [n for n, v in [
        (COL_S_KC, kc_col_s), (COL_S_JENIS, jenis_col),
        (COL_S_SEG, seg_col), (COL_S_SALDO, saldo_col),
    ] if v is None]

    if missing_s:
        raise RuntimeError(
            f"File SSA Simpanan tidak lengkap.\n"
            f"Kolom tidak ditemukan: {missing_s}\n"
            f"Kolom tersedia: {list(df_s_all.columns)}"
        )


    kc_col_p   = _find_col(df_p_all, COL_P_KC, "Cabang", "KC")
    
    segmen_col = _find_col(df_p_all, "SEGMEN_2025", "Segmen_2025", "segmen_2025", "Segmen", "SEGMEN")
    kolekt_col = _find_col(df_p_all, COL_P_KOLEKT, "Kolektabilitas", "Kol")
    baki_col   = _find_col(df_p_all, COL_P_BAKI, "Outstanding", "Baki")
    periode_p  = _find_col(df_p_all, COL_P_PERIODE, "Periode", "Tanggal")

    missing_p = [n for n, v in [
        (COL_P_KC, kc_col_p), ("SEGMEN_2025", segmen_col),
        (COL_P_KOLEKT, kolekt_col), (COL_P_BAKI, baki_col),
    ] if v is None]


    if missing_p:
        raise RuntimeError(
            f"File SSA Pinjaman tidak lengkap.\n"
            f"Kolom tidak ditemukan: {missing_p}\n"
            f"Kolom tersedia: {list(df_p_all.columns)}"
        )

    print(f"\n[KOLOM S] KC={kc_col_s}, Jenis={jenis_col}, Seg={seg_col}, "
          f"Saldo={saldo_col}, Periode={periode_s}")
    print(f"[KOLOM P] KC={kc_col_p}, Segmen={segmen_col}, "
          f"Kolekt={kolekt_col}, Baki={baki_col}, Periode={periode_p}")

    # ── 4. KONVERSI NUMERIK ───────────────────────────────────────
    cb(28, "Konversi nilai numerik...")

    df_s_all[saldo_col] = df_s_all[saldo_col].apply(parse_numeric)
    df_p_all[baki_col] = df_p_all[baki_col].apply(parse_baki_debet)

    # ── 5. MAP WILAYAH ────────────────────────────────────────────
    cb(32, "Mapping wilayah KC...")

    df_s_all['_wilayah'] = df_s_all[kc_col_s].apply(map_to_wilayah)
    df_p_all['_wilayah'] = df_p_all[kc_col_p].apply(map_to_wilayah)

    # Log KC tidak dikenal
    unk_s = df_s_all[df_s_all['_wilayah'].isna()][kc_col_s].unique()
    unk_p = df_p_all[df_p_all['_wilayah'].isna()][kc_col_p].unique()
    if len(unk_s) > 0:
        print(f"\n[WARN] KC Simpanan tidak dikenali ({len(unk_s)} unik):")
        for u in unk_s[:5]:
            print(f"  '{u}'")
    if len(unk_p) > 0:
        print(f"\n[WARN] KC Pinjaman tidak dikenali ({len(unk_p)} unik):")
        for u in unk_p[:5]:
            print(f"  '{u}'")


    # Hapus baris tanpa wilayah
    df_s = df_s_all[df_s_all['_wilayah'].notna()].copy()
    df_p = df_p_all[df_p_all['_wilayah'].notna()].copy()

    print(f"\n[AFTER MAPPING] Simpanan: {len(df_s)} baris valid")
    print(f"\n[AFTER MAPPING] Pinjaman: {len(df_p)} baris valid")

    # ── 6. NORMALISASI KOLOM PENTING ─────────────────────────────
    cb(36, "Normalisasi data...")

    # Jenis Produk (simpanan)
    df_s['_jenis'] = df_s[jenis_col].astype(str).str.strip()
    # Segmentasi BPR (simpanan)
    df_s['_segmentasi'] = df_s[seg_col].astype(str).str.strip()

    # Produk (pinjaman)
    produk_col = _find_col(df_p, "Produk", "PRODUK", "produk")
    if produk_col is None:
        raise RuntimeError("Kolom 'Produk' tidak ditemukan di SSA Pinjaman.")
        
    segmen_col_p = _find_col(df_p, "SEGMEN_2025", "Segmen_2025", "segmen_2025", "Segmen", "SEGMEN")
    if segmen_col_p is None:
        raise RuntimeError("Kolom 'SEGMEN_2025' tidak ditemukan di SSA Pinjaman.")

    # Rename dynamic columns to standard names for prepare_pinjaman
    df_p.rename(columns={
        produk_col: 'Produk',
        segmen_col_p: 'SEGMEN_2025',
        kolekt_col: 'Kolektabilitas One Obligor',
        baki_col: 'Baki Debet',
        kc_col_p: 'Nama Cabang',
        periode_p: 'Month, Day, Year of Periode'
    }, inplace=True)
    
    # Process Pinjaman completely using user's prepare_pinjaman
    df_p = prepare_pinjaman(df_p)

    # Update variable names after renaming so rest of code works
    kc_col_p = 'Nama Cabang'
    periode_p = 'Month, Day, Year of Periode'

    # Verifikasi nilai unik
    print(f"\n[JENIS PRODUK] {df_s['_jenis'].unique()[:10]}")
    print(f"[SEGMENTASI] {df_s['_segmentasi'].unique()[:10]}")

    # ── 7. PARSE TANGGAL & KUMPULKAN PERIODE ─────────────────────
    cb(40, "Parsing tanggal periode...")

    # Simpanan
    if periode_s and periode_s in df_s.columns:
        df_s['_tanggal'] = df_s[periode_s].apply(parse_tanggal_id)
    else:
        df_s['_tanggal'] = None

    # Pinjaman
    if periode_p and periode_p in df_p.columns:
        df_p['_tanggal'] = df_p[periode_p].apply(parse_tanggal_id)
    else:
        df_p['_tanggal'] = None

    # Kumpulkan semua tanggal unik berdasarkan label
    tgl_set: dict[str, pd.Timestamp] = {}

    # Assign _label so we can match by it later
    df_s['_label'] = df_s['_tanggal'].apply(format_label)
    df_p['_label'] = df_p['_tanggal'].apply(format_label)

    for idx, row in df_s.dropna(subset=['_tanggal']).iterrows():
        lbl = row['_label']
        tgl = row['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl

    for idx, row in df_p.dropna(subset=['_tanggal']).iterrows():
        lbl = row['_label']
        tgl = row['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl

    # Urutkan lama → baru berdasarkan max timestamp
    # periodes_sorted will be list of (label, timestamp)
    periodes_sorted = sorted([(lbl, tgl) for lbl, tgl in tgl_set.items()], key=lambda x: x[1])

    # Fallback jika tidak ada tanggal
    if not periodes_sorted:
        now = pd.Timestamp.now().normalize()
        periodes_sorted = [("Terbaru", now)]
        tgl_set = {"Terbaru": now}
        df_s['_tanggal'] = now
        df_p['_tanggal'] = now
        df_s['_label'] = "Terbaru"
        df_p['_label'] = "Terbaru"

    print(f"\n[PERIODE] {len(periodes_sorted)} periode:")
    for lbl, tgl in periodes_sorted:
        n_s = len(df_s[df_s['_label'] == lbl]) if '_label' in df_s.columns else 0
        n_p = len(df_p[df_p['_label'] == lbl]) if '_label' in df_p.columns else 0
        print(f"  {lbl} ({tgl.date()}) → Simp={n_s}, Pinj={n_p}")

    cb(44, "Verifikasi data per wilayah...")

    print(f"\n{'='*55}")
    print(f"  VERIFIKASI DATA PER WILAYAH")
    print(f"{'='*55}")
    # Gunakan label terbaru untuk verifikasi
    lbl_terbaru = periodes_sorted[-1][0] if periodes_sorted else None
    for wil in WILAYAH_ORDER:
        mask_s = (df_s['_wilayah'] == wil)
        mask_p = (df_p['_wilayah'] == wil)
        if lbl_terbaru is not None:
            mask_s = mask_s & (df_s['_label'] == lbl_terbaru)
            mask_p = mask_p & (df_p['_label'] == lbl_terbaru)
        n_s = mask_s.sum()
        n_p = mask_p.sum()
        sum_s = df_s.loc[mask_s, saldo_col].sum() / 1_000_000 if n_s > 0 else 0
        sum_p = df_p.loc[mask_p, baki_col].sum() / 1_000_000 if n_p > 0 else 0
        print(f"  {wil:15s}: Simp={n_s:5d} baris ({sum_s:>10,.1f} Jt), "
              f"Pinj={n_p:5d} baris ({sum_p:>10,.1f} Jt)")

    # ── 9. PROSES PER WILAYAH ─────────────────────────────────────
    result = {}
    wilayah_found = []

    for i, wilayah in enumerate(WILAYAH_ORDER):
        pct = int(48 + (i / len(WILAYAH_ORDER)) * 40)
        cb(pct, f"Memproses {wilayah}...")

        rows = _build_rows(wilayah, df_s, df_p,
                           periodes_sorted, saldo_col, baki_col)

        _attach_growth(rows, periodes_sorted)

        result[wilayah] = {
            'rows': rows,
            'periode_list': [lbl for lbl, _ in periodes_sorted],
            **_growth_labels(periodes_sorted),
            'kc_short': wilayah,
        }
        wilayah_found.append(wilayah)

    # ── 10. TOTAL AH GUNSAR ───────────────────────────────────────
    cb(90, "Menghitung Total AH Gunsar...")

    # Hitung total dari data asli tanpa menimpa _wilayah
    # karena kita butuh info wilayah (cabang) untuk filter spesifik per cabang (seperti Krekot/Roxi)
    total_rows = _build_rows('__TOTAL__', df_s, df_p,
                             periodes_sorted, saldo_col, baki_col)

    _attach_growth(total_rows, periodes_sorted)

    result['Total AH Gunsar'] = {
        'rows': total_rows,
        'periode_list': [lbl for lbl, _ in periodes_sorted],
        **_growth_labels(periodes_sorted),
        'kc_short': 'Total AH Gunsar',
    }

    # ── 11. STATS ─────────────────────────────────────────────────
    cb(96, "Finalisasi...")

    # Hitung baris per file (berjalan saja)
    n_s_berjalan = len(frames_s[0]) if frames_s else 0
    n_p_berjalan = len(frames_p[0]) if frames_p else 0

    stats = {
        'jumlah_kc':              len(wilayah_found),
        'jumlah_sheet':           len(wilayah_found) + 1,
        'jumlah_periode':         len(periodes_sorted),
        'jumlah_baris_simpanan':  n_s_berjalan,
        'jumlah_baris_pinjaman':  n_p_berjalan,
        'jumlah_baris_total':     n_rows_s + n_rows_p,
        'daftar_kc':              wilayah_found,
        # Info per file untuk popup
        'baris_simpanan_berjalan':  n_s_berjalan,
        'baris_pinjaman_berjalan':  n_p_berjalan,
        'baris_simpanan_historis':  sum(len(f) for f in frames_s[1:]),
        'baris_pinjaman_historis':  sum(len(f) for f in frames_p[1:]),
        'has_historis_simpanan':    len(frames_s) > 1,
        'has_historis_pinjaman':    len(frames_p) > 1,
        'jumlah_file_simpanan':     len(frames_s),
        'jumlah_file_pinjaman':     len(frames_p),
    }
    result['__stats__'] = stats

    print(f"\n[RESULT] {len(wilayah_found)} KC, {len(periodes_sorted)} periode")
    print(f"[STATS] {stats}")

    cb(100, "Selesai!")
    return result


# ────────────────────────────────────────────────────────────────────
# UTILITY
# ────────────────────────────────────────────────────────────────────
def count_kc(data_dict: dict) -> int:
    """Hitung jumlah KC (tanpa Total AH Gunsar dan __stats__)."""
    return sum(1 for k in data_dict
               if k not in ('Total AH Gunsar', '__stats__'))
