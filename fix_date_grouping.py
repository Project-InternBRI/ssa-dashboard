import re
import sys

with open('core/processor.py', 'r') as f:
    content = f.read()

# 1. Update dates parsing loop to build tgl_set by label
old_date_set = """    # Kumpulkan semua tanggal unik
    tgl_set: dict[pd.Timestamp, str] = {}

    for tgl in df_s['_tanggal'].dropna().unique():
        tgl = pd.Timestamp(tgl)
        lbl = format_label(tgl)
        tgl_set[tgl] = lbl

    for tgl in df_p['_tanggal'].dropna().unique():
        tgl = pd.Timestamp(tgl)
        lbl = format_label(tgl)
        tgl_set[tgl] = lbl

    # Urutkan lama → baru
    periodes_sorted = sorted(tgl_set.items(), key=lambda x: x[0])"""

new_date_set = """    # Kumpulkan semua tanggal unik berdasarkan label
    tgl_set: dict[str, pd.Timestamp] = {}

    # Assign _label so we can match by it later
    df_s['_label'] = df_s['_tanggal'].apply(format_label)
    df_p['_label'] = df_p['_tanggal'].apply(format_label)

    for idx, row in df_s.dropna(subset=['_tanggal']).iterrows():
        lbl = row['_label']
        tgl = row['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl

    for idx, row in df_p.dropna(subset=['_tanggal']).iterrows():
        lbl = row['_label']
        tgl = row['_tanggal']
        if lbl not in tgl_set or tgl > tgl_set[lbl]:
            tgl_set[lbl] = tgl

    # Urutkan lama → baru berdasarkan max timestamp
    # periodes_sorted will be list of (label, timestamp)
    periodes_sorted = sorted([(lbl, tgl) for lbl, tgl in tgl_set.items()], key=lambda x: x[1])"""
content = content.replace(old_date_set, new_date_set)

# 2. Update _sum_saldo filtering
old_sum_saldo = """def _sum_saldo(df: pd.DataFrame, wilayah: str, tanggal: pd.Timestamp | None,
               jenis: str, segmentasi: str, saldo_col: str) -> float:
    \"\"\"
    SUM(Saldo) WHERE Jenis Produk=jenis AND Segmentasi BPR=segmentasi
    AND _wilayah=wilayah AND _tanggal=tanggal
    Hasil dalam JUTA RUPIAH.
    \"\"\"
    mask = df['_wilayah'] == wilayah
    if tanggal is not None and '_tanggal' in df.columns:
        mask &= df['_tanggal'] == tanggal"""

new_sum_saldo = """def _sum_saldo(df: pd.DataFrame, wilayah: str, label: str,
               jenis: str, segmentasi: str, saldo_col: str) -> float:
    \"\"\"
    SUM(Saldo) WHERE Jenis Produk=jenis AND Segmentasi BPR=segmentasi
    AND _wilayah=wilayah AND _label=label
    Hasil dalam JUTA RUPIAH.
    \"\"\"
    mask = df['_wilayah'] == wilayah
    if label is not None and '_label' in df.columns:
        mask &= df['_label'] == label"""
content = content.replace(old_sum_saldo, new_sum_saldo)

# 3. Update build_pinjaman_rows filtering
old_build_pinj = """def build_pinjaman_rows(df_pinj, wilayah, tanggal, baki_col):
    mask_kc = (df_pinj['_wilayah'] == wilayah)
    mask_tgl = (df_pinj['_tanggal'] == tanggal)"""
new_build_pinj = """def build_pinjaman_rows(df_pinj, wilayah, label, baki_col):
    mask_kc = (df_pinj['_wilayah'] == wilayah)
    mask_tgl = (df_pinj['_label'] == label) if '_label' in df_pinj.columns else (df_pinj['_tanggal'] == label)"""
content = content.replace(old_build_pinj, new_build_pinj)

# 4. Update row lambdas in _build_rows
old_build_rows = """    def row(row_type: str, label: str, get_fn):
        \"\"\"Buat satu baris dengan values per periode.\"\"\"
        vals = {}
        for lbl, tgl in periodes_sorted:
            vals[lbl] = get_fn(tgl)"""
new_build_rows = """    def row(row_type: str, label: str, get_fn):
        \"\"\"Buat satu baris dengan values per periode.\"\"\"
        vals = {}
        for lbl, tgl in periodes_sorted:
            vals[lbl] = get_fn(lbl)"""
content = content.replace(old_build_rows, new_build_rows)

old_pinjaman_call = """    # ── HITUNG SEMUA NILAI PINJAMAN DULU ──────────────────────────
    pinjaman_data = {}
    for lbl, tgl in periodes_sorted:
        pinjaman_data[lbl] = build_pinjaman_rows(df_p, wilayah, tgl, baki_col)"""
new_pinjaman_call = """    # ── HITUNG SEMUA NILAI PINJAMAN DULU ──────────────────────────
    pinjaman_data = {}
    for lbl, tgl in periodes_sorted:
        pinjaman_data[lbl] = build_pinjaman_rows(df_p, wilayah, lbl, baki_col)"""
content = content.replace(old_pinjaman_call, new_pinjaman_call)

# 5. Fix periodes_sorted fallback
old_fallback = """    # Fallback jika tidak ada tanggal
    if not periodes_sorted:
        now = pd.Timestamp.now().normalize()
        periodes_sorted = [(now, "Terbaru")]
        tgl_set = {now: "Terbaru"}
        df_s['_tanggal'] = now
        df_p['_tanggal'] = now"""
new_fallback = """    # Fallback jika tidak ada tanggal
    if not periodes_sorted:
        now = pd.Timestamp.now().normalize()
        periodes_sorted = [("Terbaru", now)]
        tgl_set = {"Terbaru": now}
        df_s['_tanggal'] = now
        df_p['_tanggal'] = now
        df_s['_label'] = "Terbaru"
        df_p['_label'] = "Terbaru\""""
content = content.replace(old_fallback, new_fallback)

# 6. Fix printing
old_print_periode = """    print(f"\\n[PERIODE] {len(periodes_sorted)} periode:")
    for tgl, lbl in periodes_sorted:
        n_s = len(df_s[df_s['_tanggal'] == tgl])
        n_p = len(df_p[df_p['_tanggal'] == tgl])
        print(f"  {lbl} ({tgl.date()}) → Simp={n_s}, Pinj={n_p}")"""
new_print_periode = """    print(f"\\n[PERIODE] {len(periodes_sorted)} periode:")
    for lbl, tgl in periodes_sorted:
        n_s = len(df_s[df_s['_label'] == lbl]) if '_label' in df_s.columns else 0
        n_p = len(df_p[df_p['_label'] == lbl]) if '_label' in df_p.columns else 0
        print(f"  {lbl} ({tgl.date()}) → Simp={n_s}, Pinj={n_p}")"""
content = content.replace(old_print_periode, new_print_periode)

old_tgl_terbaru = """    # Gunakan tanggal terbaru untuk verifikasi
    tgl_terbaru = periodes_sorted[-1][0] if periodes_sorted else None
    for wil in WILAYAH_ORDER:
        mask_s = (df_s['_wilayah'] == wil)
        mask_p = (df_p['_wilayah'] == wil)
        if tgl_terbaru is not None:
            mask_s = mask_s & (df_s['_tanggal'] == tgl_terbaru)
            mask_p = mask_p & (df_p['_tanggal'] == tgl_terbaru)"""
new_tgl_terbaru = """    # Gunakan label terbaru untuk verifikasi
    lbl_terbaru = periodes_sorted[-1][0] if periodes_sorted else None
    for wil in WILAYAH_ORDER:
        mask_s = (df_s['_wilayah'] == wil)
        mask_p = (df_p['_wilayah'] == wil)
        if lbl_terbaru is not None:
            mask_s = mask_s & (df_s['_label'] == lbl_terbaru)
            mask_p = mask_p & (df_p['_label'] == lbl_terbaru)"""
content = content.replace(old_tgl_terbaru, new_tgl_terbaru)

with open('core/processor.py', 'w') as f:
    f.write(content)
print("Updated processor successfully.")
