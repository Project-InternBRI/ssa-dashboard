import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# Replace the build_pinjaman_rows logic
old_logic = """def build_pinjaman_rows(df_p, wilayah, tanggal, baki_col):
    # -- PINJAMAN UTAMA --
    # Pinjaman Performing (Kol = 1)
    pinjaman_perf = get_pinjaman_value(df_p, wilayah, tanggal, 
                                       segmen_2025=['Small', 'Consumer', 'Micro', 'Corporate'],
                                       kolektabilitas=1, baki_col=baki_col)
    
    # Outstanding all kol (!=0)
    small      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Small', kolektabilitas=None, baki_col=baki_col)
    konsumer   = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Consumer', kolektabilitas=None, baki_col=baki_col)
    mikro      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Micro', kolektabilitas=None, baki_col=baki_col)
    total_all_kol = small + konsumer + mikro
    
    # -- SML (Kolektabilitas = 2) --
    sml_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small', kolektabilitas=2, baki_col=baki_col)
    sml_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=2, baki_col=baki_col)
    sml_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro', kolektabilitas=2, baki_col=baki_col)
    sml_total    = sml_small + sml_konsumer + sml_mikro
    
    # -- NPL (Kolektabilitas = 3, 4, 5) --
    npl_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_total    = npl_small + npl_konsumer + npl_mikro
    
    # -- PERSENTASE --
    def pct(num, den):
        return float(num / den) if den != 0 else 0.0
    
    return {
        'Pinjaman'     : pinjaman_perf,
        'Mikro'        : mikro,
        'Small'        : small,
        'Konsumer'     : konsumer,
        
        'SML'          : sml_total,
        'SML %'        : pct(sml_total, total_all_kol),
        'SML > Mikro'  : sml_mikro,
        'Mikro %'      : pct(sml_mikro, mikro),
        'SML > Small'  : sml_small,
        'Small %'      : pct(sml_small, small),
        'SML > Konsumer': sml_konsumer,
        'Konsumer %'   : pct(sml_konsumer, konsumer),
        
        'NPL'          : npl_total,
        'NPL %'        : pct(npl_total, total_all_kol),
        'NPL > Mikro'  : npl_mikro,
        'Mikro % NPL'  : pct(npl_mikro, mikro),
        'NPL > Small'  : npl_small,
        'Small % NPL'  : pct(npl_small, small),
        'NPL > Konsumer': npl_konsumer,
        'Konsumer % NPL': pct(npl_konsumer, konsumer),
        
        'Recovery. EC' : 0.0,
        'Mikro EC'     : 0.0,
        'Small EC'     : 0.0,
        'Konsumer EC'  : 0.0,
    }"""

new_logic = """def build_pinjaman_rows(df_p, wilayah, tanggal, baki_col):
    # Outstanding all kol (!=0)
    mikro      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Micro', kolektabilitas=None, baki_col=baki_col)
    small      = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Small', kolektabilitas=None, baki_col=baki_col)
    konsumer   = get_pinjaman_value(df_p, wilayah, tanggal, segmen_2025='Consumer', kolektabilitas=None, baki_col=baki_col)
    
    # Total Pinjaman = Mikro + Small + Konsumer (sesuai instruksi revisi)
    total_pinjaman = mikro + small + konsumer
    
    # -- SML (Kolektabilitas = 2) --
    sml_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro', kolektabilitas=2, baki_col=baki_col)
    sml_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small', kolektabilitas=2, baki_col=baki_col)
    sml_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=2, baki_col=baki_col)
    sml_total    = sml_mikro + sml_small + sml_konsumer
    
    # -- NPL (Kolektabilitas = 3, 4, 5) --
    npl_mikro    = get_pinjaman_value(df_p, wilayah, tanggal, 'Micro', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_small    = get_pinjaman_value(df_p, wilayah, tanggal, 'Small', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_konsumer = get_pinjaman_value(df_p, wilayah, tanggal, 'Consumer', kolektabilitas=[3,4,5], baki_col=baki_col)
    npl_total    = npl_mikro + npl_small + npl_konsumer
    
    # -- PERSENTASE --
    def pct(num, den):
        return float(num / den) if den != 0 else 0.0
    
    return {
        'Pinjaman'     : total_pinjaman,
        'Mikro'        : mikro,
        'Small'        : small,
        'Konsumer'     : konsumer,
        
        'SML'          : sml_total,
        'SML %'        : pct(sml_total, total_pinjaman),
        'SML > Mikro'  : sml_mikro,
        'Mikro %'      : pct(sml_mikro, mikro),
        'SML > Small'  : sml_small,
        'Small %'      : pct(sml_small, small),
        'SML > Konsumer': sml_konsumer,
        'Konsumer %'   : pct(sml_konsumer, konsumer),
        
        'NPL'          : npl_total,
        'NPL %'        : pct(npl_total, total_pinjaman),
        'NPL > Mikro'  : npl_mikro,
        'Mikro % NPL'  : pct(npl_mikro, mikro),
        'NPL > Small'  : npl_small,
        'Small % NPL'  : pct(npl_small, small),
        'NPL > Konsumer': npl_konsumer,
        'Konsumer % NPL': pct(npl_konsumer, konsumer),
        
        'Recovery. EC' : "",
        'Mikro EC'     : "",
        'Small EC'     : "",
        'Konsumer EC'  : "",
    }"""

content = content.replace(old_logic, new_logic)
with open('core/processor.py', 'w') as f:
    f.write(content)

