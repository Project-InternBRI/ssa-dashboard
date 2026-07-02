"""
processor_uker.py — Proses file SSA untuk Dashboard KCP dan Unit.

Perbedaan dari processor.py (Dashboard KC):
  - Identitas entitas dibaca dari kolom "Nama Uker" (bukan "Nama Cabang")
  - KCP  = Nama Uker yang mengandung kata "KCP"
  - Unit = Nama Uker yang mengandung kata "UNIT", "BRI UNIT", atau "TERAS"
  - Logika perhitungan segmen, produk, SML, NPL, Growth: IDENTIK dengan KC

DISCLAIMER: File processor.py (Dashboard KC) TIDAK DIUBAH SAMA SEKALI.
"""
from __future__ import annotations

import pandas as pd

from core.processor import (
    _find_col, _attach_growth, _growth_labels,
    hitung_pinjaman_kc,          # reuse sepenuhnya — filter oleh _wilayah, kita pakai _uker
    build_pinjaman_rows,
    prepare_pinjaman,
    classify_pinjaman_exact,
    format_label, parse_tanggal_id, parse_numeric,
    BULAN_ID_MAP,
)
from core.file_reader import BULAN_PANJANG, BULAN_SINGKAT


# ────────────────────────────────────────────────────────────────────
# KLASIFIKASI JENIS UKER
# ────────────────────────────────────────────────────────────────────
def classify_uker(nama_uker: str) -> str | None:
    """
    Kembalikan 'KCP' atau 'Unit' berdasarkan nama Uker.
    Kembalikan None jika bukan keduanya (mis. KC induk).
    """
    u = str(nama_uker).strip().upper()
    if not u or u in ('NAN', 'NONE', ''):
        return None
    if 'KCP' in u:
        return 'KCP'
    if 'BRI UNIT' in u or 'UNIT' in u or 'TERAS' in u:
        return 'Unit'
    return None


# ────────────────────────────────────────────────────────────────────
# SUM SALDO PER UKER (SIMPANAN)
# Identik _sum_saldo di processor.py namun filter by _uker bukan _wilayah
# ────────────────────────────────────────────────────────────────────
def _sum_saldo_uker(df: pd.DataFrame, uker: str, label: str,
                    jenis: str, segmentasi: str, saldo_col: str) -> float:
    """
    SUM(Saldo) WHERE Jenis=jenis AND Segmentasi=segmentasi
    AND _uker=uker AND _label=label.
    Hasil dalam JUTA RUPIAH.
    """
    if uker == '__TOTAL_KCP__':
        mask = df['_uker_type'] == 'KCP'
    elif uker == '__TOTAL_UNIT__':
        mask = df['_uker_type'] == 'Unit'
    else:
        mask = df['_uker'] == uker

    if label is not None and '_label' in df.columns:
        mask &= df['_label'] == label
    if jenis:
        mask &= df['_jenis'].str.lower() == jenis.lower()
    if segmentasi:
        mask &= df['_segmentasi'].str.lower() == segmentasi.lower()

    total = df.loc[mask, saldo_col].sum()
    return float(total) / 1_000_000


# ────────────────────────────────────────────────────────────────────
# HITUNG PINJAMAN PER UKER
# ────────────────────────────────────────────────────────────────────
def hitung_pinjaman_uker(df_pinj: pd.DataFrame, uker: str, label: str,
                          baki_col: str = 'Baki Debet') -> dict:
    """
    Menghitung semua nilai pinjaman untuk satu Uker dan satu periode.
    Logika identik dengan hitung_pinjaman_kc namun filter by _uker.
    """
    def _zero():
        keys = [
            'pinjaman', 'pinjaman_mikro', 'pinjaman_small',
            'pinjaman_konsumer', 'pinjaman_konsumer_kpr', 'pinjaman_konsumer_briguna',
            'sml', 'sml_pct', 'sml_mikro', 'sml_mikro_pct',
            'sml_small', 'sml_small_pct', 'sml_konsumer', 'sml_konsumer_pct',
            'sml_konsumer_kpr', 'sml_konsumer_kpr_pct',
            'sml_konsumer_briguna', 'sml_konsumer_briguna_pct',
            'npl', 'npl_pct', 'npl_mikro', 'npl_mikro_pct',
            'npl_small', 'npl_small_pct', 'npl_konsumer', 'npl_konsumer_pct',
            'npl_konsumer_kpr', 'npl_konsumer_kpr_pct',
            'npl_konsumer_briguna', 'npl_konsumer_briguna_pct',
            'recovery_ec', 'recovery_ec_mikro', 'recovery_ec_small', 'recovery_ec_konsumer',
        ]
        return {k: 0.0 for k in keys}

    if '_uker' not in df_pinj.columns:
        return _zero()

    if uker == '__TOTAL_KCP__':
        mask = df_pinj['_uker_type'] == 'KCP'
    elif uker == '__TOTAL_UNIT__':
        mask = df_pinj['_uker_type'] == 'Unit'
    else:
        mask = df_pinj['_uker'] == uker

    mask &= df_pinj['_label'] == label
    df = df_pinj[mask].copy()

    if df.empty:
        return _zero()

    def s(m): return df[m][baki_col].sum() / 1_000_000
    def safe_pct(num, den): return round(num / den, 6) if den and den != 0 else None

    m_small    = df['segmen_dashboard'] == 'Small'
    m_consumer = df['segmen_dashboard'] == 'Konsumer'
    m_micro    = df['segmen_dashboard'] == 'Mikro'

    norm_produk = df['Produk'].astype(str).str.lower().str.replace(r'[\s\-]', '', regex=True)
    m_kpr     = m_consumer & (norm_produk == 'kpr')
    m_briguna = m_consumer & (norm_produk == 'brigunaritel')

    m_kol2   = df['Kolektabilitas One Obligor'] == 2
    m_kol345 = df['Kolektabilitas One Obligor'].isin([3, 4, 5])

    small    = s(m_small)
    kpr      = s(m_kpr)
    briguna  = s(m_briguna)
    konsumer = kpr + briguna
    mikro    = s(m_micro)
    total_p  = small + konsumer + mikro

    sml_small    = s(m_small    & m_kol2)
    sml_kpr      = s(m_kpr      & m_kol2)
    sml_briguna  = s(m_briguna  & m_kol2)
    sml_konsumer = sml_kpr + sml_briguna
    sml_mikro    = s(m_micro    & m_kol2)
    sml_total    = sml_small + sml_konsumer + sml_mikro

    npl_small    = s(m_small    & m_kol345)
    npl_kpr      = s(m_kpr      & m_kol345)
    npl_briguna  = s(m_briguna  & m_kol345)
    npl_konsumer = npl_kpr + npl_briguna
    npl_mikro    = s(m_micro    & m_kol345)
    npl_total    = npl_small + npl_konsumer + npl_mikro

    return {
        'pinjaman'                     : total_p,
        'pinjaman_mikro'               : mikro,
        'pinjaman_small'               : small,
        'pinjaman_konsumer'            : konsumer,
        'pinjaman_konsumer_kpr'        : kpr,
        'pinjaman_konsumer_briguna'    : briguna,
        'sml'                          : sml_total,
        'sml_pct'                      : safe_pct(sml_total, total_p),
        'sml_mikro'                    : sml_mikro,
        'sml_mikro_pct'                : safe_pct(sml_mikro, mikro),
        'sml_small'                    : sml_small,
        'sml_small_pct'                : safe_pct(sml_small, small),
        'sml_konsumer'                 : sml_konsumer,
        'sml_konsumer_pct'             : safe_pct(sml_konsumer, konsumer),
        'sml_konsumer_kpr'             : sml_kpr,
        'sml_konsumer_kpr_pct'         : safe_pct(sml_kpr, konsumer),
        'sml_konsumer_briguna'         : sml_briguna,
        'sml_konsumer_briguna_pct'     : safe_pct(sml_briguna, konsumer),
        'npl'                          : npl_total,
        'npl_pct'                      : safe_pct(npl_total, total_p),
        'npl_mikro'                    : npl_mikro,
        'npl_mikro_pct'                : safe_pct(npl_mikro, mikro),
        'npl_small'                    : npl_small,
        'npl_small_pct'                : safe_pct(npl_small, small),
        'npl_konsumer'                 : npl_konsumer,
        'npl_konsumer_pct'             : safe_pct(npl_konsumer, konsumer),
        'npl_konsumer_kpr'             : npl_kpr,
        'npl_konsumer_kpr_pct'         : safe_pct(npl_kpr, konsumer),
        'npl_konsumer_briguna'         : npl_briguna,
        'npl_konsumer_briguna_pct'     : safe_pct(npl_briguna, konsumer),
        'recovery_ec'                  : None,
        'recovery_ec_mikro'            : None,
        'recovery_ec_small'            : None,
        'recovery_ec_konsumer'         : None,
    }


# ────────────────────────────────────────────────────────────────────
# BUILD ROWS PER UKER — template baris identik dengan KC
# ────────────────────────────────────────────────────────────────────
def _build_rows_uker(uker: str, df_s: pd.DataFrame, df_p: pd.DataFrame,
                     periodes_sorted: list[tuple], saldo_col: str,
                     baki_col: str) -> list[dict]:
    """
    Bangun template baris FIXED untuk satu Uker (KCP atau Unit).
    Pola identik dengan _build_rows() di processor.py.
    """
    def row(row_type: str, label: str, get_fn):
        vals = {}
        for lbl, _ in periodes_sorted:
            vals[lbl] = get_fn(lbl)
        return {'row_type': row_type, 'label': label, 'values': vals}

    rows = []

    # Helper DPK — hanya Ritel (tidak ada Micro khusus seperti Krekot/Roxi)
    def _get_dpk(tgl, jenis):
        return _sum_saldo_uker(df_s, uker, tgl, jenis, 'Ritel', saldo_col)

    # ── BLOK 1: Dana Pihak Ketiga ────────────────────────────────
    rows.append(row('header_value', 'Dana Pihak Ketiga',
        lambda t: _get_dpk(t, 'Tabungan') + _get_dpk(t, 'Giro') + _get_dpk(t, 'Deposito')))
    rows.append(row('data', 'Tabungan',  lambda t: _get_dpk(t, 'Tabungan')))
    rows.append(row('data', 'Giro',      lambda t: _get_dpk(t, 'Giro')))
    rows.append(row('data', 'Deposito',  lambda t: _get_dpk(t, 'Deposito')))
    rows.append(row('bold', 'CASA',
        lambda t: _get_dpk(t, 'Tabungan') + _get_dpk(t, 'Giro')))

    # DPK Korporasi (Wholesale)
    rows.append(row('header_value', 'DPK Korporasi',
        lambda t: (
            _sum_saldo_uker(df_s, uker, t, 'Giro',     'Wholesale', saldo_col) +
            _sum_saldo_uker(df_s, uker, t, 'Deposito', 'Wholesale', saldo_col)
        )))
    rows.append(row('data', 'Giro',
        lambda t: _sum_saldo_uker(df_s, uker, t, 'Giro',     'Wholesale', saldo_col)))
    rows.append(row('data', 'Deposito',
        lambda t: _sum_saldo_uker(df_s, uker, t, 'Deposito', 'Wholesale', saldo_col)))

    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    # ── BLOK 2-5: Pinjaman, SML, NPL, Recovery ──────────────────
    pinjaman_data = {}
    for lbl, _ in periodes_sorted:
        pinjaman_data[lbl] = hitung_pinjaman_uker(df_p, uker, lbl, baki_col)

    def p_row(row_type: str, label: str, key: str):
        vals = {}
        for lbl, _ in periodes_sorted:
            vals[lbl] = pinjaman_data[lbl].get(key)
        return {'row_type': row_type, 'label': label, 'values': vals}

    rows.append(p_row('header_value', 'Pinjaman',                   'pinjaman'))
    rows.append(p_row('data',         'Mikro',                       'pinjaman_mikro'))
    rows.append(p_row('data',         'Small',                       'pinjaman_small'))
    rows.append(p_row('data',         'Konsumer - KPR',              'pinjaman_konsumer_kpr'))
    rows.append(p_row('data',         'Konsumer - Briguna Ritel',    'pinjaman_konsumer_briguna'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    rows.append(p_row('bold',  'SML',                         'sml'))
    rows.append(p_row('bold',  'SML %',                       'sml_pct'))
    rows.append(p_row('data',  'Mikro',                       'sml_mikro'))
    rows.append(p_row('data',  'Mikro %',                     'sml_mikro_pct'))
    rows.append(p_row('data',  'Small',                       'sml_small'))
    rows.append(p_row('data',  'Small %',                     'sml_small_pct'))
    rows.append(p_row('data',  'Konsumer - KPR',              'sml_konsumer_kpr'))
    rows.append(p_row('data',  'Konsumer - KPR %',            'sml_konsumer_kpr_pct'))
    rows.append(p_row('data',  'Konsumer - Briguna Ritel',    'sml_konsumer_briguna'))
    rows.append(p_row('data',  'Konsumer - Briguna Ritel %',  'sml_konsumer_briguna_pct'))

    rows.append(p_row('bold',  'NPL',                         'npl'))
    rows.append(p_row('bold',  'NPL %',                       'npl_pct'))
    rows.append(p_row('data',  'Mikro',                       'npl_mikro'))
    rows.append(p_row('data',  'Mikro %',                     'npl_mikro_pct'))
    rows.append(p_row('data',  'Small',                       'npl_small'))
    rows.append(p_row('data',  'Small %',                     'npl_small_pct'))
    rows.append(p_row('data',  'Konsumer - KPR',              'npl_konsumer_kpr'))
    rows.append(p_row('data',  'Konsumer - KPR %',            'npl_konsumer_kpr_pct'))
    rows.append(p_row('data',  'Konsumer - Briguna Ritel',    'npl_konsumer_briguna'))
    rows.append(p_row('data',  'Konsumer - Briguna Ritel %',  'npl_konsumer_briguna_pct'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    rows.append(p_row('header', 'Recovery. EC',    'recovery_ec'))
    rows.append(p_row('data',   'Mikro',            'recovery_ec_mikro'))
    rows.append(p_row('data',   'Small',            'recovery_ec_small'))
    rows.append(p_row('data',   'Konsumer',         'recovery_ec_konsumer'))

    rows = _attach_growth(rows, periodes_sorted)
    return rows


def process_uker_from_df(
    df_s_all: pd.DataFrame,
    df_p_all: pd.DataFrame,
    callback=None,
    uker_type_filter: str | None = None,
) -> dict:
    """
    Proses DataFrame SSA yang sudah dimuat ke memori untuk Dashboard KCP / Unit.
    Tidak membaca file CSV/Excel lagi untuk menghemat waktu.
    """
    def cb(pct, msg):
        if callback:
            callback(pct, msg)

    # DataFrame harus dicopy agar tidak merusak proses KC utama
    df_s_all = df_s_all.copy()
    df_p_all = df_p_all.copy()

    # ── 1. TEMUKAN KOLOM ─────────────────────────────────────────
    cb(52, "(KCP/Unit) Mencocokkan kolom...")

    # Simpanan
    uker_col_s = _find_col(df_s_all, "Nama Uker", "NAMA UKER", "NamaUker", "nama_uker")
    if uker_col_s is None:
        raise RuntimeError(
            "Kolom 'Nama Uker' tidak ditemukan di SSA Simpanan.\n"
            f"Kolom tersedia: {list(df_s_all.columns[:20])}"
        )

    jenis_col  = _find_col(df_s_all, "Jenis Produk", "Jenis", "Produk")
    seg_col    = _find_col(df_s_all, "Segmentasi BPR", "Segmentasi", "Segmen")
    saldo_col  = _find_col(df_s_all, "Saldo", "Outstanding", "Balance")
    periode_s  = _find_col(df_s_all, "Month, Day, Year of Posisi", "Posisi", "Tanggal")

    for name, val in [("Jenis Produk", jenis_col), ("Segmentasi BPR", seg_col),
                       ("Saldo", saldo_col)]:
        if val is None:
            raise RuntimeError(f"Kolom '{name}' tidak ditemukan di SSA Simpanan.")

    # Pinjaman
    kc_col_p   = _find_col(df_p_all, "Nama Cabang", "Cabang", "KC")
    periode_p  = _find_col(df_p_all, "Month, Day, Year of Periode", "Periode", "Tanggal")
    baki_col   = _find_col(df_p_all, "Baki Debet", "Baki", "Outstanding")
    kolekt_col = _find_col(df_p_all, "Kolektabilitas One Obligor", "Kolektabilitas", "Kolekt")
    produk_col = _find_col(df_p_all, "Produk", "PRODUK")
    segmen_col = _find_col(df_p_all, "SEGMEN_2025", "Segmen_2025", "Segmen", "SEGMEN")

    uker_col_p = _find_col(df_p_all, "Nama Uker", "NAMA UKER", "NamaUker", "nama_uker")

    for name, val in [("Baki Debet", baki_col), ("Kolektabilitas", kolekt_col),
                       ("Produk", produk_col), ("SEGMEN_2025", segmen_col)]:
        if val is None:
            raise RuntimeError(f"Kolom '{name}' tidak ditemukan di SSA Pinjaman.")

    # ── 2. MAP UKER (SIMPANAN) ───────────────────────────────────
    cb(58, "(KCP/Unit) Mapping Nama Uker...")
    df_s_all['_uker']      = df_s_all[uker_col_s].astype(str).str.strip()
    df_s_all['_uker_type'] = df_s_all['_uker'].apply(classify_uker)

    df_s_all['_jenis']       = df_s_all[jenis_col].astype(str).str.strip()
    df_s_all['_segmentasi']  = df_s_all[seg_col].astype(str).str.strip()

    # MAP UKER (PINJAMAN)
    if uker_col_p:
        df_p_all['_uker']      = df_p_all[uker_col_p].astype(str).str.strip()
        df_p_all['_uker_type'] = df_p_all['_uker'].apply(classify_uker)
    else:
        df_p_all['_uker']      = 'Unknown'
        df_p_all['_uker_type'] = None

    # Rename kolom pinjaman agar cocok dengan prepare_pinjaman
    df_p_all.rename(columns={
        produk_col : 'Produk',
        segmen_col : 'SEGMEN_2025',
        kolekt_col : 'Kolektabilitas One Obligor',
        baki_col   : 'Baki Debet',
        kc_col_p   : 'Nama Cabang',
        **(({periode_p: 'Month, Day, Year of Periode'} if periode_p else {}))
    }, inplace=True)
    baki_col   = 'Baki Debet'
    periode_p  = 'Month, Day, Year of Periode'

    df_p_all = prepare_pinjaman(df_p_all)
    df_p_all['segmen_dashboard'] = df_p_all.apply(classify_pinjaman_exact, axis=1)

    # ── 6. PARSE TANGGAL ─────────────────────────────────────────
    cb(38, "Parsing tanggal periode (Uker)...")

    if periode_s and periode_s in df_s_all.columns:
        df_s_all['_tanggal'] = df_s_all[periode_s].apply(parse_tanggal_id)
    else:
        df_s_all['_tanggal'] = None

    if 'Month, Day, Year of Periode' in df_p_all.columns:
        df_p_all['_tanggal'] = df_p_all['Month, Day, Year of Periode'].apply(parse_tanggal_id)
    else:
        df_p_all['_tanggal'] = None

    df_s_all['_label'] = df_s_all['_tanggal'].apply(format_label)
    df_p_all['_label'] = df_p_all['_tanggal'].apply(format_label)

    # Kumpulkan semua periode unik
    tgl_set: dict[str, pd.Timestamp] = {}
    for _, r in df_s_all.dropna(subset=['_tanggal']).iterrows():
        lbl, tgl = r['_label'], r['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl
    for _, r in df_p_all.dropna(subset=['_tanggal']).iterrows():
        lbl, tgl = r['_label'], r['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl

    periodes_sorted = sorted(
        [(lbl, tgl) for lbl, tgl in tgl_set.items()], key=lambda x: x[1]
    )
    if not periodes_sorted:
        now = pd.Timestamp.now().normalize()
        periodes_sorted = [("Terbaru", now)]
        df_s_all['_tanggal'] = now
        df_p_all['_tanggal'] = now
        df_s_all['_label']   = "Terbaru"
        df_p_all['_label']   = "Terbaru"

    print(f"[UKER] {len(periodes_sorted)} periode ditemukan")

    # ── 7. FILTER BERDASARKAN JENIS UKER ────────────────────────
    if uker_type_filter:
        df_s = df_s_all[df_s_all['_uker_type'] == uker_type_filter].copy()
        df_p = df_p_all[df_p_all['_uker_type'] == uker_type_filter].copy() if '_uker_type' in df_p_all.columns else df_p_all.copy()
    else:
        df_s = df_s_all[df_s_all['_uker_type'].notna()].copy()
        df_p = df_p_all[df_p_all['_uker_type'].notna()].copy() if '_uker_type' in df_p_all.columns else df_p_all.copy()

    # ── 8. DAFTAR ENTITAS ────────────────────────────────────────
    cb(44, "Identifikasi entitas Uker...")

    lbl_terbaru = periodes_sorted[-1][0] if periodes_sorted else None

    if uker_type_filter:
        target_types = [uker_type_filter]
    else:
        target_types = ['KCP', 'Unit']

    uker_list: dict[str, list[str]] = {'KCP': [], 'Unit': []}
    # Ambil dari data terbaru saja untuk counting
    df_s_ref = df_s[df_s['_label'] == lbl_terbaru] if lbl_terbaru else df_s
    for utype in target_types:
        mask = df_s_ref['_uker_type'] == utype
        uker_list[utype] = sorted(df_s_ref.loc[mask, '_uker'].dropna().unique().tolist())

    print(f"[UKER] KCP ({len(uker_list['KCP'])}): {uker_list['KCP'][:5]}")
    print(f"[UKER] Unit ({len(uker_list['Unit'])}): {uker_list['Unit'][:5]}")

    # ── 9. PROSES PER ENTITAS ─────────────────────────────────────
    result = {}
    all_ukers = []
    for utype in target_types:
        all_ukers.extend([(u, utype) for u in uker_list[utype]])

    for i, (uker, utype) in enumerate(all_ukers):
        pct = int(48 + (i / max(len(all_ukers), 1)) * 40)
        cb(pct, f"Memproses {uker}...")

        rows = _build_rows_uker(uker, df_s, df_p, periodes_sorted, saldo_col, baki_col)

        result[uker] = {
            'rows'        : rows,
            'periode_list': [lbl for lbl, _ in periodes_sorted],
            **_growth_labels(periodes_sorted),
            'kc_short'    : uker,
            'uker_type'   : utype,
        }

    # ── 10. TOTAL PER JENIS ──────────────────────────────────────
    cb(90, "Menghitung total (Uker)...")
    for utype in target_types:
        total_key = '__TOTAL_KCP__' if utype == 'KCP' else '__TOTAL_UNIT__'
        display_key = 'Total KCP' if utype == 'KCP' else 'Total Unit'

        df_s_type = df_s[df_s['_uker_type'] == utype].copy()
        df_p_type = df_p[df_p['_uker_type'] == utype].copy() if '_uker_type' in df_p.columns else pd.DataFrame()

        # Pakai uker='__TOTAL_KCP__' / '__TOTAL_UNIT__' agar _sum_saldo_uker tahu
        total_rows = _build_rows_uker(total_key, df_s, df_p,
                                      periodes_sorted, saldo_col, baki_col)

        result[display_key] = {
            'rows'        : total_rows,
            'periode_list': [lbl for lbl, _ in periodes_sorted],
            **_growth_labels(periodes_sorted),
            'kc_short'    : display_key,
            'uker_type'   : utype,
        }

    # ── 11. STATS ────────────────────────────────────────────────
    cb(96, "Finalisasi (Uker)...")

    n_s = len(df_s_all)
    n_p = len(df_p_all)

    stats = {
        'jumlah_kcp'   : len(uker_list.get('KCP',  [])),
        'jumlah_unit'  : len(uker_list.get('Unit', [])),
        'daftar_kcp'   : uker_list.get('KCP',  []),
        'daftar_unit'  : uker_list.get('Unit', []),
        'jumlah_periode': len(periodes_sorted),
        'baris_simpanan': n_s,
        'baris_pinjaman': n_p,
    }
    result['__stats__'] = stats

    print(f"[UKER RESULT] KCP={stats['jumlah_kcp']}, Unit={stats['jumlah_unit']}")
    cb(100, "Selesai (Uker)!")
    return result
