import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# 1. Add _segmen_old extraction in _read_ssa_csv or wherever df_p is processed.
# Wait, let's just do it inside get_pinjaman_value dynamically by passing the original df_p and using the column name?
# Or I can just inject it where _segmen_2025 is assigned.

segmen_assign = "df_p['_segmen_2025'] = df_p[segmen_col].astype(str).str.strip()"
segmen_fallback = """df_p['_segmen_2025'] = df_p[segmen_col].astype(str).str.strip()
    
    # Extract old Segmen column for fallback
    seg_col_old = 'Segmen'
    if seg_col_old in df_p.columns:
        df_p['_segmen_old'] = df_p[seg_col_old].astype(str).str.strip().str.lower()
    else:
        df_p['_segmen_old'] = ''
"""
content = content.replace(segmen_assign, segmen_fallback)


# 2. Update get_pinjaman_value
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
        if segmen_2025 == 'Consumer':
            mask &= ((df_p['_segmen_2025'] == 'Consumer') | (df_p['_segmen_old'] == 'konsumer'))
        elif segmen_2025 == 'Small':
            mask &= ((df_p['_segmen_2025'] == 'Small') | (df_p['_segmen_old'] == 'small') | (df_p['_segmen_old'] == 'sme'))
        elif segmen_2025 == 'Micro':
            mask &= ((df_p['_segmen_2025'] == 'Micro') | (df_p['_segmen_old'] == 'micro') | (df_p['_segmen_old'] == 'mikro'))
        else:
            if isinstance(segmen_2025, list):
                mask &= df_p['_segmen_2025'].isin(segmen_2025)
            else:
                mask &= (df_p['_segmen_2025'] == segmen_2025)
            
    total = df_p.loc[mask, baki_col].sum()
    return float(total) / 1_000_000"""

content = re.sub(r"def get_pinjaman_value\(df_p, wilayah, tanggal.*?return float\(total\) / 1_000_000", new_logic, content, flags=re.DOTALL)

with open('core/processor.py', 'w') as f:
    f.write(content)
