import re

with open('core/processor.py', 'r') as f:
    code = f.read()

# 1. Replace the classification variables and functions at the top with EXCLUDE
old_top = """PRODUK_MIKRO = ['kupedes', 'kur mikro', 'briguna karya', 'briguna purna']
PRODUK_SMALL = ['kur kecil', 'kredit kemitraan', 'retel']
PRODUK_KONSUMER = ['briguna ritel', 'kpp', 'kpr', 'kkb', 'brguna umum', 'pangan', 'kredit pegawai']

def classify_produk(produk_str: str) -> str | None:
    if not isinstance(produk_str, str):
        return None
    p = produk_str.strip().lower()
    for keyword in PRODUK_MIKRO:
        if keyword in p:
            return 'Mikro'
    for keyword in PRODUK_SMALL:
        if keyword in p:
            return 'Small'
    for keyword in PRODUK_KONSUMER:
        if keyword in p:
            if 'lainnya' in p:
                return 'EXCLUDE'
            return 'Konsumer'
    return None

def classify_segmen_2025(value: str) -> str | None:
    if not isinstance(value, str):
        return None
    val = value.strip().lower()
    # hapus spasi ganda
    import re
    val = re.sub(r'\\s+', ' ', val)
    
    if val in ['consumer', 'konsumer', 'retail consumer', 'consumer banking']:
        return 'Konsumer'
    elif val in ['micro', 'mikro', 'micro banking']:
        return 'Mikro'
    elif val in ['small', 'sme', 'small business']:
        return 'Small'
    elif val in ['medium', 'commercial', 'commercial banking']:
        return 'EXCLUDE'
    return None

def log_produk_mapping(df_p):
    import pandas as pd
    try:
        import os
        produk_counts = df_p.groupby(['Produk', 'segmen_dashboard'])['Baki Debet'].agg(['count', 'sum']).reset_index()
        produk_counts = produk_counts.sort_values(by=['segmen_dashboard', 'sum'], ascending=[True, False])
        
        with open('log_produk.txt', 'w') as f:
            f.write('=== HASIL MAPPING PRODUK KE SEGMEN ===\\n')
            for _, row in produk_counts.iterrows():
                f.write(
                    f'  Produk: {row["Produk"]:<30} | '
                    f'Segmen: {str(row["segmen_dashboard"]):<10} | '
                    f'Count: {row["count"]:>5} | '
                    f'Total: {row["sum"]/1e6:>15,.2f}\\n'
                )
    except Exception as e:
        print(f"Gagal log produk: {e}")"""

new_top = """# Produk yang dikecualikan dari Konsumer
EXCLUDE_KONSUMER = ['lainnya']

# Produk yang dikecualikan dari Mikro
EXCLUDE_MIKRO_PRODUK = ['kur ritel']"""

code = code.replace(old_top, new_top)

# 2. Replace pinjaman internal functions with new functions
old_pinj_funcs = """def _sum_seg_kol(df: pd.DataFrame, mask_seg, mask_kol, baki_col: str, 
                 segmen: str | None, kolekt_vals: list[int], baki_col_name: str) -> float:
    \"\"\"Helper untuk sum baki debet.\"\"\"
    if segmen:
        # Khusus untuk pinjaman, _segmen sudah diisi oleh segmen_dashboard
        mask_s = mask_seg & (df['_segmen'] == segmen)
    else:
        mask_s = mask_seg
        
    mask_k = mask_kol & df['_kolekt'].isin(kolekt_vals)
    return df.loc[mask_s & mask_k, baki_col].sum() / 1_000_000


def build_pinjaman_rows(df_pinj, wilayah, label, baki_col):
    \"\"\"Menghitung pinjaman, SML, NPL, dan persentasenya.\"\"\"
    mask_w = df_pinj['_wilayah'] == wilayah
    mask_l = df_pinj['_label'] == label
    df = df_pinj[mask_w & mask_l]

    if df.empty:
        return {}
        
    def s(m_seg, m_kol):
        return df[m_seg & m_kol][baki_col].sum() / 1_000_000

    def pct(num, den):
        return round(num / den, 6) if den and den != 0 else None

    # Base masks
    m_mikro = df['_segmen'] == 'Mikro'
    m_small = df['_segmen'] == 'Small'
    m_konsumer = df['_segmen'] == 'Konsumer'
    
    # Kol masks
    m_all_kol = df['_kolekt'] >= 1
    m_kol2 = df['_kolekt'] == 2
    m_kol345 = df['_kolekt'].isin([3, 4, 5])

    # Pinjaman (Kol 1-5)
    p_mikro = s(m_mikro, m_all_kol)
    p_small = s(m_small, m_all_kol)
    p_konsumer = s(m_konsumer, m_all_kol)
    
    # OVERRIDE SML & NPL KONSUMER BERDASARKAN EXCEL LAMA (Jan-Mei 26)
    # --- MANUAL ADJUSTMENTS BASED ON EXCEL ---
    tgl_str = str(label)
    
    sml_kons_override = None
    npl_kons_override = None
    npl_small_override = None
    
    if tgl_str == "Jan-26":
        npl_kons_override = 405.000
        sml_kons_override = 36981.821
        npl_small_override = 76835.474
    elif tgl_str == "Feb-26":
        npl_kons_override = 692.651
        sml_kons_override = 52518.291
    elif tgl_str == "Mar-26":
        npl_kons_override = 1354.218
        sml_kons_override = 52163.351
    elif tgl_str == "Apr-26":
        npl_kons_override = 1339.739
        sml_kons_override = 59164.223
    elif tgl_str == "Mei-26":
        npl_kons_override = 1435.031
        sml_kons_override = 62755.074

    p_total = p_mikro + p_small + p_konsumer

    # SML
    sml_mikro = s(m_mikro, m_kol2)
    sml_small = s(m_small, m_kol2)
    sml_konsumer = sml_kons_override if sml_kons_override is not None else s(m_konsumer, m_kol2)
    sml_total = sml_mikro + sml_small + sml_konsumer

    # NPL
    npl_mikro = s(m_mikro, m_kol345)
    npl_small = npl_small_override if npl_small_override is not None else s(m_small, m_kol345)
    npl_konsumer = npl_kons_override if npl_kons_override is not None else s(m_konsumer, m_kol345)
    npl_total = npl_mikro + npl_small + npl_konsumer

    return {
        'pinjaman_total': p_total,
        'pinjaman_mikro': p_mikro,
        'pinjaman_small': p_small,
        'pinjaman_konsumer': p_konsumer,

        'sml_total': sml_total,
        'sml_pct': pct(sml_total, p_total),
        'sml_mikro': sml_mikro,
        'sml_pct_mikro': pct(sml_mikro, p_mikro),
        'sml_small': sml_small,
        'sml_pct_small': pct(sml_small, p_small),
        'sml_konsumer': sml_konsumer,
        'sml_pct_konsumer': pct(sml_konsumer, p_konsumer),

        'npl_total': npl_total,
        'npl_pct': pct(npl_total, p_total),
        'npl_mikro': npl_mikro,
        'npl_pct_mikro': pct(npl_mikro, p_mikro),
        'npl_small': npl_small,
        'npl_pct_small': pct(npl_small, p_small),
        'npl_konsumer': npl_konsumer,
        'npl_pct_konsumer': pct(npl_konsumer, p_konsumer),
        
        'recovery_ec': None
    }"""

new_pinj_funcs = """def prepare_pinjaman(df):
    # 1. Konversi Baki Debet ke float
    def parse_num(v):
        s = str(v).strip()
        try: return float(s)
        except:
            s = s.replace('.','').replace(',','.')
            try: return float(s)
            except: return 0.0
    
    if 'Baki Debet' in df.columns:
        df['Baki Debet'] = df['Baki Debet'].apply(parse_num)
    
    # 2. Konversi Kolektabilitas ke integer
    if 'Kolektabilitas One Obligor' in df.columns:
        df['Kolektabilitas One Obligor'] = pd.to_numeric(
            df['Kolektabilitas One Obligor'], errors='coerce'
        ).fillna(0).astype(int)
    
    # 3. Bersihkan whitespace semua kolom string
    for col in ['SEGMEN_2025', 'Produk', 'Nama Cabang']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
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
    return {k: None for k in keys}

def hitung_pinjaman_kc(df_pinj, kc_keyword, tanggal):
    '''
    Menghitung semua nilai pinjaman untuk satu KC dan satu periode.
    df_pinj sudah melalui prepare_pinjaman().
    '''
    if 'Nama Cabang' not in df_pinj.columns or 'Month, Day, Year of Periode' not in df_pinj.columns:
        return _zero_result()

    # Filter KC (substring, case-insensitive)
    mask_kc = df_pinj['Nama Cabang'].str.lower().str.contains(
        kc_keyword.lower(), na=False
    )
    # Filter tanggal
    mask_tgl = (df_pinj['Month, Day, Year of Periode'] == tanggal)
    df = df_pinj[mask_kc & mask_tgl].copy()
    
    if df.empty:
        return _zero_result()
    
    def s(m): return df[m]['Baki Debet'].sum() / 1_000_000
    def safe_pct(num, den):
        return round(num/den, 6) if den and den != 0 else None
    
    # Mask dasar per segmen
    m_small    = df['SEGMEN_2025'] == 'Small'
    m_consumer = (df['SEGMEN_2025'] == 'Consumer') & \\
                 ~(df['Produk'].str.lower() == 'lainnya')
    m_micro    = (df['SEGMEN_2025'] == 'Micro') & \\
                 ~(df['Produk'].str.lower().str.contains('kur ritel', na=False))
    
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
    if 'Nama Cabang' not in df_pinj.columns or 'Month, Day, Year of Periode' not in df_pinj.columns:
        return
    df_kc = df_pinj[
        df_pinj['Nama Cabang'].str.lower().str.contains(kc_keyword.lower(), na=False) &
        (df_pinj['Month, Day, Year of Periode'] == tanggal)
    ]
    print(f'\\n[DEBUG] {kc_keyword} - {tanggal}')
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
    print(f'  NPL: {npl:,.1f} ({npl_pct:.2%})')"""

code = code.replace(old_pinj_funcs, new_pinj_funcs)

# 3. Fix _build_rows 
old_pinj_rows = """    # ── HITUNG SEMUA NILAI PINJAMAN DULU ──────────────────────────
    pinjaman_data = {}
    for lbl, tgl in periodes_sorted:
        pinjaman_data[lbl] = build_pinjaman_rows(df_p, wilayah, lbl, baki_col)

    def p_row(row_type: str, label: str, key: str):
        vals = {}
        for lbl, tgl in periodes_sorted:
            if key == 'recovery_ec':
                vals[lbl] = ""
            else:
                vals[lbl] = pinjaman_data[lbl].get(key, 0.0)
        return {'row_type': row_type, 'label': label, 'values': vals}

    # ── BLOK 2: Pinjaman ────────────────────────────────────────
    rows.append(p_row('header_value', 'Pinjaman', 'pinjaman_total'))
    rows.append(p_row('data', 'Mikro', 'pinjaman_mikro'))
    rows.append(p_row('data', 'Small', 'pinjaman_small'))
    rows.append(p_row('data', 'Konsumer', 'pinjaman_konsumer'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    # ── BLOK 3: SML ─────────────────────────────────────────────
    rows.append(p_row('bold', 'SML', 'sml_total'))
    rows.append(p_row('bold', 'SML %', 'sml_pct'))
    rows.append(p_row('data', 'Mikro', 'sml_mikro'))
    rows.append(p_row('data', 'Mikro %', 'sml_pct_mikro'))
    rows.append(p_row('data', 'Small', 'sml_small'))
    rows.append(p_row('data', 'Small %', 'sml_pct_small'))
    rows.append(p_row('data', 'Konsumer', 'sml_konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'sml_pct_konsumer'))

    # ── BLOK 4: NPL ─────────────────────────────────────────────
    rows.append(p_row('bold', 'NPL', 'npl_total'))
    rows.append(p_row('bold', 'NPL %', 'npl_pct'))
    rows.append(p_row('data', 'Mikro', 'npl_mikro'))
    rows.append(p_row('data', 'Mikro %', 'npl_pct_mikro'))
    rows.append(p_row('data', 'Small', 'npl_small'))
    rows.append(p_row('data', 'Small %', 'npl_pct_small'))
    rows.append(p_row('data', 'Konsumer', 'npl_konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'npl_pct_konsumer'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})

    # ── BLOK 5: Recovery EC ─────────────────────────────────────
    rows.append(p_row('header', 'Recovery. EC', 'recovery_ec'))
    rows.append(p_row('data', 'Mikro', 'recovery_ec'))
    rows.append(p_row('data', 'Small', 'recovery_ec'))
    rows.append(p_row('data', 'Konsumer', 'recovery_ec'))"""

new_pinj_rows = """    # ── HITUNG SEMUA NILAI PINJAMAN DULU ──────────────────────────
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
    rows.append(p_row('data', 'Konsumer', 'recovery_ec_konsumer'))"""

code = code.replace(old_pinj_rows, new_pinj_rows)

# 4. In process_files, apply prepare_pinjaman and rename columns
old_preprocessing = """    # Produk (pinjaman)
    produk_col = _find_col(df_p, "Produk", "PRODUK", "produk")
    if produk_col is None:
        raise RuntimeError("Kolom 'Produk' tidak ditemukan di SSA Pinjaman.")
        
    segmen_col_p = _find_col(df_p, "SEGMEN_2025", "Segmen_2025", "segmen_2025", "Segmen", "SEGMEN")
    if segmen_col_p is None:
        raise RuntimeError("Kolom 'SEGMEN_2025' tidak ditemukan di SSA Pinjaman.")
        
    # Klasifikasi lapis 1: Berdasarkan Produk
    df_p['segmen_dashboard_produk'] = df_p[produk_col].astype(str).apply(classify_produk)
    
    # Klasifikasi lapis 2: Berdasarkan SEGMEN_2025
    df_p['segmen_dashboard_2025'] = df_p[segmen_col_p].astype(str).apply(classify_segmen_2025)
    
    # Kombinasi (Fallback) - Prioritaskan Produk
    df_p['segmen_dashboard'] = df_p['segmen_dashboard_produk'].combine_first(df_p['segmen_dashboard_2025'])
    # Force exclude
    df_p.loc[df_p['segmen_dashboard_2025'] == 'EXCLUDE', 'segmen_dashboard'] = None
    df_p.loc[df_p['segmen_dashboard_produk'] == 'EXCLUDE', 'segmen_dashboard'] = None
    
    print("\\n[AUDIT] Distribusi SEGMEN_2025:")
    print(df_p[segmen_col_p].value_counts(dropna=False).to_string())
    
    print("\\n[AUDIT] Total Baris per Segmen Dashboard:")
    print(df_p['segmen_dashboard'].value_counts(dropna=False).to_string())

    unclassified = df_p[df_p['segmen_dashboard'].isna()][produk_col].unique()
    if len(unclassified) > 0:
        print(f'\\nPERINGATAN: Produk tidak terklasifikasi setelah fallback ({len(unclassified)} jenis):')
        for p in sorted(unclassified):
            print(f'  - {repr(p)}')
            
    # Tampilkan juga SEGMEN_2025 yang gagal terklasifikasi
    unclassified_segmen = df_p[df_p['segmen_dashboard'].isna()][segmen_col_p].unique()
    if len(unclassified_segmen) > 0:
        print(f'\\nPERINGATAN: Nilai SEGMEN_2025 tidak terklasifikasi ({len(unclassified_segmen)} jenis):')
        for s in sorted(unclassified_segmen):
            print(f'  - {repr(s)}')

    # Log audit
    log_produk_mapping(df_p)

    # Kolektabilitas (pinjaman) -> Integer (0 jika invalid)
    df_p['_kolekt'] = pd.to_numeric(
        df_p[kolekt_col], errors='coerce'
    ).fillna(0).astype(int)

    # Exclude Kol = 0 and NaN/0 Baki Debet as requested
    df_p = df_p[df_p['_kolekt'] != 0].copy()
    df_p = df_p[df_p[baki_col].notna() & (df_p[baki_col] != 0)].copy()

    # Verifikasi nilai unik
    print(f"\\n[JENIS PRODUK] {df_s['_jenis'].unique()[:10]}")
    print(f"[SEGMENTASI] {df_s['_segmentasi'].unique()[:10]}")
    print(f"[SEGMEN_DASHBOARD] {df_p['segmen_dashboard'].unique()[:10]}")
    print(f"[KOLEKT] {df_p['_kolekt'].unique()[:10]}")"""

new_preprocessing = """    # Produk (pinjaman)
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
    print(f"\\n[JENIS PRODUK] {df_s['_jenis'].unique()[:10]}")
    print(f"[SEGMENTASI] {df_s['_segmentasi'].unique()[:10]}")"""

code = code.replace(old_preprocessing, new_preprocessing)

with open('core/processor.py', 'w') as f:
    f.write(code)
print("PATCH APPLIED!")
