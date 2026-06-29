import re

with open('core/processor.py', 'r') as f:
    content = f.read()

new_logic = """def get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025=None, kolektabilitas=None, baki_col=None):
    mask = df_p['_wilayah'] == wilayah
    if tanggal is not None:
        mask &= (df_p['_tanggal'] == tanggal)
    
    # Selalu exclude Kolektabilitas=0 kecuali diminta explicitly
    if kolektabilitas is None:
        mask &= (df_p['_kolekt'] != 0)
    elif isinstance(kolektabilitas, list):
        mask &= df_p['_kolekt'].isin(kolektabilitas)
    else:
        mask &= (df_p['_kolekt'] == kolektabilitas)
    
    if segmen_2025 is not None:
        if isinstance(segmen_2025, list):
            mask &= df_p['_segmen_2025'].isin(segmen_2025)
        else:
            mask &= (df_p['_segmen_2025'] == segmen_2025)
            
    total = df_p.loc[mask, baki_col].sum()
    return float(total) / 1_000_000

def build_pinjaman_rows(df_p, wilayah, tanggal, baki_col):
    # -- PINJAMAN UTAMA (HANYA PERFORMING / KOL 1) --
    small      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Small',    kolektabilitas=1, baki_col=baki_col)
    konsumer   = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Consumer', kolektabilitas=1, baki_col=baki_col)
    mikro      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Micro',    kolektabilitas=1, baki_col=baki_col)
    
    # Hitung nilai total all kol untuk persentase SML dan NPL
    small_all      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Small',    kolektabilitas=None, baki_col=baki_col)
    konsumer_all   = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Consumer', kolektabilitas=None, baki_col=baki_col)
    mikro_all      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Micro',    kolektabilitas=None, baki_col=baki_col)
    total_pinj_all = small_all + konsumer_all + mikro_all
    
    total_pinj_perf = small + konsumer + mikro
    
    # -- SML (Kolektabilitas = 2) --
    sml_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small',    kolektabilitas=2, baki_col=baki_col)
    sml_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=2, baki_col=baki_col)
    sml_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro',    kolektabilitas=2, baki_col=baki_col)
    sml_total    = sml_small + sml_konsumer + sml_mikro
    
    # -- NPL (Kolektabilitas = 3, 4, 5) --
    npl_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small',    kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro',    kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_total    = npl_small + npl_konsumer + npl_mikro
    
    # -- PERSENTASE --
    def pct(num, den):
        return round(num / den, 6) if den != 0 else 0.0
    
    return {
        'Pinjaman'     : total_pinj_perf,
        'Mikro'        : mikro,
        'Small'        : small,
        'Konsumer'     : konsumer,
        
        'SML'          : sml_total,
        'SML %'        : pct(sml_total, total_pinj_all),
        'SML > Mikro'  : sml_mikro,
        'Mikro %'      : pct(sml_mikro, mikro_all),
        'SML > Small'  : sml_small,
        'Small %'      : pct(sml_small, small_all),
        'SML > Konsumer': sml_konsumer,
        'Konsumer %'   : pct(sml_konsumer, konsumer_all),
        
        'NPL'          : npl_total,
        'NPL %'        : pct(npl_total, total_pinj_all),
        'NPL > Mikro'  : npl_mikro,
        'Mikro % NPL'  : pct(npl_mikro, mikro_all),
        'NPL > Small'  : npl_small,
        'Small % NPL'  : pct(npl_small, small_all),
        'NPL > Konsumer': npl_konsumer,
        'Konsumer % NPL': pct(npl_konsumer, konsumer_all),
        
        'Recovery. EC' : "",
        'Mikro EC'     : "",
        'Small EC'     : "",
        'Konsumer EC'  : "",
    }
"""

content = re.sub(r"def get_pinjaman_value\(df_p, wilayah, tanggal.*?return \{.*?\n    \}", new_logic, content, flags=re.DOTALL)

with open('core/processor.py', 'w') as f:
    f.write(content)
