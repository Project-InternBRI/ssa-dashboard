import re

with open('core/processor.py', 'r') as f:
    code = f.read()

# 1. Remove PRODUK_MIKRO, PRODUK_SMALL, PRODUK_KONSUMER, classify_produk, classify_segmen_2025, log_produk_mapping
# We can use regex to remove these blocks.
code = re.sub(r'PRODUK_MIKRO = \[.*?\]\s*', '', code, flags=re.DOTALL)
code = re.sub(r'PRODUK_SMALL = \[.*?\]\s*', '', code, flags=re.DOTALL)
code = re.sub(r'PRODUK_KONSUMER = \[.*?\]\s*', '', code, flags=re.DOTALL)
code = re.sub(r'def classify_produk.*?return None\s*', '', code, flags=re.DOTALL)
code = re.sub(r'def classify_segmen_2025.*?return None\s*', '', code, flags=re.DOTALL)
code = re.sub(r'def log_produk_mapping.*?f\.write.*?\)\s*', '', code, flags=re.DOTALL)

# Insert the new constants at the top right after imports
imports_end = code.find('except ImportError:\n    find_column = None\n    diagnose_file = None\n    BULAN_SINGKAT = [\'\', \'Jan\', \'Feb\', \'Mar\', \'Apr\', \'Mei\', \'Jun\',\n                     \'Jul\', \'Agu\', \'Sep\', \'Okt\', \'Nov\', \'Des\']\n    BULAN_PANJANG = [\'\', \'Januari\', \'Februari\', \'Maret\', \'April\', \'Mei\',\n                     \'Juni\', \'Juli\', \'Agustus\', \'September\', \'Oktober\',\n                     \'November\', \'Desember\']\n')
if imports_end != -1:
    imports_end = code.find('\n\n', imports_end)
    
new_consts = """
# Produk yang dikecualikan dari Konsumer
EXCLUDE_KONSUMER = ['lainnya']

# Produk yang dikecualikan dari Mikro
EXCLUDE_MIKRO_PRODUK = ['kur ritel']
"""
code = code[:imports_end] + new_consts + code[imports_end:]


# 2. Replace the pinjaman calculation functions (build_pinjaman_rows, _sum_seg_kol, etc.)
# Currently they are right before _build_rows
# Wait, let's just insert the new functions before _build_rows and delete the old ones.
old_pinj_funcs_regex = r'def _sum_seg_kol.*?def build_pinjaman_rows.*?\n\n\n'
code = re.sub(r'def _sum_seg_kol\(df:.*?def build_pinjaman_rows.*?return\s+\{.*?\}\n\n', '', code, flags=re.DOTALL)

# Let's find def _build_rows and insert the new pinjaman functions there
new_pinj_funcs = """
def prepare_pinjaman(df):
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
    m_consumer = (df['SEGMEN_2025'] == 'Consumer') & \
                 ~(df['Produk'].str.lower() == 'lainnya')
    m_micro    = (df['SEGMEN_2025'] == 'Micro') & \
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
    print(f'  NPL: {npl:,.1f} ({npl_pct:.2%})')

"""
code = code.replace("def _build_rows(wilayah: str", new_pinj_funcs + "\ndef _build_rows(wilayah: str")

# 3. Fix _build_rows pinjaman section
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
prep_start = code.find("df_p_all[baki_col] = df_p_all[baki_col].apply(parse_baki_debet)")
prep_end = code.find("df_p = df_p_all[mask_valid].copy()")

if prep_start != -1 and prep_end != -1:
    # Let's replace the whole block from prep_start to just before _build_rows is called?
    # Actually, let's just insert column renaming and prepare_pinjaman
    pass

with open('core/processor.py', 'w') as f:
    f.write(code)

