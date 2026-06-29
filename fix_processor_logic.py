import sys

with open('core/processor.py', 'r') as f:
    content = f.read()

target_start_string = """    # Produk (pinjaman)
    produk_col = _find_col(df_p, "Produk", "PRODUK", "produk")
    if produk_col is None:
        raise RuntimeError("Kolom 'Produk' tidak ditemukan di SSA Pinjaman.")
        
    segmen_col_p = _find_col(df_p, "SEGMEN_2025", "Segmen_2025", "segmen_2025", "Segmen", "SEGMEN")
    if segmen_col_p is None:
        raise RuntimeError("Kolom 'SEGMEN_2025' tidak ditemukan di SSA Pinjaman.")"""

target_end_string = """    # Exclude Kol = 0 and NaN/0 Baki Debet as requested
    df_p = df_p[df_p['_kolekt'] != 0].copy()
    df_p = df_p[df_p[baki_col].notna() & (df_p[baki_col] != 0)].copy()

    # Verifikasi nilai unik
    print(f"\\n[JENIS PRODUK] {df_s['_jenis'].unique()[:10]}")
    print(f"[SEGMENTASI] {df_s['_segmentasi'].unique()[:10]}")
    print(f"[SEGMEN_DASHBOARD] {df_p['segmen_dashboard'].unique()[:10]}")
    print(f"[KOLEKT] {df_p['_kolekt'].unique()[:10]}")"""

new_content = """    # Produk (pinjaman)
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

start_idx = content.find(target_start_string)
end_idx = content.find(target_end_string)

if start_idx != -1 and end_idx != -1:
    end_idx += len(target_end_string)
    final_content = content[:start_idx] + new_content + content[end_idx:]
    with open('core/processor.py', 'w') as f:
        f.write(final_content)
    print("SUCCESS: REPLACED BLOCK!")
else:
    print(f"FAILED TO FIND STRINGS! Start: {start_idx}, End: {end_idx}")

