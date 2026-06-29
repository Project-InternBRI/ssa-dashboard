import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# 1. Fix the messed up block at line 888
# Find everything from `    # Produk (pinjaman)` up to `    kolekt_col = _find_col`
pattern1 = r'    # Produk \(pinjaman\)\n    produk_col = _find_col\(df_p_all, "Produk", "PRODUK", "produk"\)\n.*?    # Log audit\n    log_produk_mapping\(df_p_all\)\n        \n    kolekt_col = _find_col'
replacement1 = r'    segmen_col = _find_col(df_p_all, "SEGMEN_2025", "Segmen_2025", "segmen_2025", "Segmen", "SEGMEN")\n    kolekt_col = _find_col'

content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)

# 2. Fix the correct block at line 989
pattern2 = r'    # Produk \(pinjaman\)\n    produk_col = _find_col\(df_p, "Produk", "PRODUK", "produk"\)\n    if produk_col is None:\n        raise RuntimeError\("Kolom \'Produk\' tidak ditemukan di SSA Pinjaman\."\)\n        \n    df_p\[\'segmen_dashboard\'\] = df_p\[produk_col\]\.astype\(str\)\.apply\(classify_produk\)\n    \n    unclassified = df_p\[df_p\[\'segmen_dashboard\'\]\.isna\(\)\]\[produk_col\]\.unique\(\)\n    if len\(unclassified\) > 0:\n        print\(f\'\\\\nPERINGATAN: Produk tidak terklasifikasi \(\{len\(unclassified\)\} jenis\):\'\)\n        for p in sorted\(unclassified\):\n            print\(f\'  - \{repr\(p\)\}\'\)\n        print\(\'  Produk ini TIDAK masuk ke Mikro/Small/Konsumer manapun\.\'\)\n\n    # Log audit\n    log_produk_mapping\(df_p\)'

replacement2 = """    # Produk (pinjaman)
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
    
    # Kombinasi (Fallback)
    df_p['segmen_dashboard'] = df_p['segmen_dashboard_produk'].combine_first(df_p['segmen_dashboard_2025'])
    
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
    log_produk_mapping(df_p)"""

content = re.sub(pattern2, replacement2, content)

with open('core/processor.py', 'w') as f:
    f.write(content)

print("Replacement done.")
