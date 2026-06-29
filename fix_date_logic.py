import re
import sys

with open('core/processor.py', 'r') as f:
    content = f.read()

# 1. Restore parse_tanggal_id (remove to_end_of_month)
old_parse = """def parse_tanggal_id(tgl_str) -> pd.Timestamp | None:
    \"\"\"
    Parse tanggal format Indonesia: "20 Juni 2026", "20 Jun 2026"
    atau format standar: "2026-06-20", datetime object.
    Semua tanggal akan dinormalisasi ke akhir bulan agar dapat dicocokkan 
    secara presisi antara file Simpanan dan Pinjaman.
    \"\"\"
    import calendar
    def to_end_of_month(ts: pd.Timestamp) -> pd.Timestamp:
        akhir = calendar.monthrange(ts.year, ts.month)[1]
        return pd.Timestamp(year=ts.year, month=ts.month, day=akhir)

    if pd.isna(tgl_str) or tgl_str is None:
        return None
    if isinstance(tgl_str, pd.Timestamp):
        return to_end_of_month(tgl_str)
    if isinstance(tgl_str, datetime):
        return to_end_of_month(pd.Timestamp(tgl_str))

    s = str(tgl_str).strip()
    parts = s.split()
    if len(parts) >= 3:
        bulan_key = parts[1].lower().rstrip('.')
        bulan = BULAN_ID_MAP.get(bulan_key)
        if bulan:
            try:
                # Gunakan day=1 sementara untuk menghindari error "day is out of range", 
                # lalu normalisasi ke akhir bulan
                ts = pd.Timestamp(year=int(parts[2]), month=bulan, day=1)
                return to_end_of_month(ts)
            except Exception:
                pass

    # Fallback pandas
    try:
        ts = pd.to_datetime(s, dayfirst=True)
        return to_end_of_month(ts)
    except Exception:
        return None"""

new_parse = """def parse_tanggal_id(tgl_str) -> pd.Timestamp | None:
    \"\"\"
    Parse tanggal format Indonesia: "20 Juni 2026", "20 Jun 2026"
    atau format standar: "2026-06-20", datetime object.
    \"\"\"
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
        return None"""
content = content.replace(old_parse, new_parse)

# 2. Update format_label to be more forgiving for end of month
old_format = """def format_label(ts: pd.Timestamp) -> str:
    \"\"\"
    Timestamp → label periode:
    Akhir bulan: "Des-25", "Jun-26"
    \"\"\"
    if ts is None:
        return "Unknown"
    akhir = calendar.monthrange(ts.year, ts.month)[1]
    bln = BULAN_SINGKAT[ts.month]
    thn2 = str(ts.year)[-2:]
    if ts.day >= akhir - 1:
        return f"{bln}-{thn2}"
    else:
        return f"{ts.day} {bln}-{ts.year}\""""

new_format = """def format_label(ts: pd.Timestamp) -> str:
    \"\"\"
    Timestamp → label periode:
    Akhir bulan: "Des-25", "Jun-26"
    \"\"\"
    if ts is None or pd.isna(ts):
        return "Unknown"
    import calendar
    akhir = calendar.monthrange(ts.year, ts.month)[1]
    bln = BULAN_SINGKAT[ts.month]
    thn2 = str(ts.year)[-2:]
    # Snap dates within 4 days of month-end to end-of-month label
    if ts.day >= akhir - 4:
        return f"{bln}-{thn2}"
    else:
        return f"{ts.day} {bln}-{ts.year}\""""
content = content.replace(old_format, new_format)

# 3. Add EXCLUDE logic to classify_produk and classify_segmen_2025
old_class_p = """    for keyword in PRODUK_KONSUMER:
        if keyword in p:
            return 'Konsumer'
    return None"""
new_class_p = """    for keyword in PRODUK_KONSUMER:
        if keyword in p:
            if 'lainnya' in p:
                return 'EXCLUDE'
            return 'Konsumer'
    return None"""
content = content.replace(old_class_p, new_class_p)

old_class_s = """    elif val in ['small', 'sme', 'small business']:
        return 'Small'
    return None"""
new_class_s = """    elif val in ['small', 'sme', 'small business']:
        return 'Small'
    elif val in ['medium', 'commercial', 'commercial banking']:
        return 'EXCLUDE'
    return None"""
content = content.replace(old_class_s, new_class_s)

# 4. Fallback exclusion enforcement
old_fallback = """    # Kombinasi (Fallback) - Prioritaskan SEGMEN_2025
    df_p['segmen_dashboard'] = df_p['segmen_dashboard_produk'].combine_first(df_p['segmen_dashboard_2025'])"""
new_fallback = """    # Kombinasi (Fallback) - Prioritaskan Produk
    df_p['segmen_dashboard'] = df_p['segmen_dashboard_produk'].combine_first(df_p['segmen_dashboard_2025'])
    # Force exclude
    df_p.loc[df_p['segmen_dashboard_2025'] == 'EXCLUDE', 'segmen_dashboard'] = None
    df_p.loc[df_p['segmen_dashboard_produk'] == 'EXCLUDE', 'segmen_dashboard'] = None"""
content = content.replace(old_fallback, new_fallback)

with open('core/processor.py', 'w') as f:
    f.write(content)
print("Updated processor successfully.")
