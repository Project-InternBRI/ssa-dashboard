import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# 1. Add PRODUK constants and classify functions
logic_funcs = """
PRODUK_MIKRO = ['kupedes', 'kur mikro', 'briguna karya', 'briguna purna']
PRODUK_SMALL = ['kur kecil', 'kredit kemitraan', 'retel']
PRODUK_KONSUMER = ['briguna ritel', 'kpp', 'kpr', 'kkb', 'brguna umum', 'pangan', 'kredit pegawai']

def classify_produk(produk_str: str) -> str:
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

def classify_segmen_2025(value: str) -> str:
    if not isinstance(value, str):
        return None
    val = value.strip().lower()
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

def prepare_pinjaman(df: pd.DataFrame) -> pd.DataFrame:
"""

# Replace `def prepare_pinjaman` with the logic
content = re.sub(r'def prepare_pinjaman\(df: pd\.DataFrame\) -> pd\.DataFrame:', logic_funcs, content)

# 2. Inside prepare_pinjaman, apply the logic
prep_logic = """
    # 1. Bersihkan whitespace dan klasifikasikan segmen_dashboard
    for col in ['SEGMEN_2025', 'Produk', 'Nama Cabang']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    if 'Produk' in df.columns and 'SEGMEN_2025' in df.columns:
        df['segmen_dashboard_produk'] = df['Produk'].apply(classify_produk)
        df['segmen_dashboard_2025'] = df['SEGMEN_2025'].apply(classify_segmen_2025)
        df['segmen_dashboard'] = df['segmen_dashboard_produk'].combine_first(df['segmen_dashboard_2025'])
        df.loc[df['segmen_dashboard_2025'] == 'EXCLUDE', 'segmen_dashboard'] = None
        df.loc[df['segmen_dashboard_produk'] == 'EXCLUDE', 'segmen_dashboard'] = None

    # Parse Baki Debet
    def parse_num(val):
        if pd.isna(val): return 0.0
        s = str(val).strip()
        try: return float(s)
        except ValueError:
            s = s.replace('.','').replace(',','.')
            try: return float(s)
            except: return 0.0
    
    if 'Baki Debet' in df.columns:
        df['Baki Debet'] = df['Baki Debet'].apply(parse_num)
    
    # Konversi Kolektabilitas
    if 'Kolektabilitas One Obligor' in df.columns:
        df['Kolektabilitas One Obligor'] = pd.to_numeric(
            df['Kolektabilitas One Obligor'], errors='coerce'
        ).fillna(0).astype(int)
    
    # Exclude Kolektabilitas = 0 and Baki Debet = 0
    if 'Kolektabilitas One Obligor' in df.columns:
        df = df[df['Kolektabilitas One Obligor'] != 0].copy()
    if 'Baki Debet' in df.columns:
        df = df[df['Baki Debet'].notna() & (df['Baki Debet'] != 0)].copy()
        
    return df
"""

content = re.sub(r"def prepare_pinjaman\(df: pd\.DataFrame\) -> pd\.DataFrame:.*?return df", logic_funcs + prep_logic, content, flags=re.DOTALL)

# 3. Update hitung_pinjaman_kc to use segmen_dashboard
hitung_logic = """    # Mask dasar per segmen berdasarkan segmen_dashboard yang sudah diproses
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
    npl_total    = npl_small + npl_konsumer + npl_mikro"""

content = re.sub(r"    # Mask dasar per segmen.*?npl_total    = npl_small \+ npl_konsumer \+ npl_mikro", hitung_logic, content, flags=re.DOTALL)

with open('core/processor.py', 'w') as f:
    f.write(content)
print("SUCCESS")
