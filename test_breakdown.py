import glob
import os
import sys
import pandas as pd
from core.processor import process_files, classify_produk, classify_segmen_2025

# Setup paths
s_files = glob.glob(os.path.expanduser('~/Downloads/SSA Simpanan*.csv'))
p_files = glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv'))

if not s_files or not p_files:
    print("No files found.")
    sys.exit(1)

# We want to trace exactly what is being assigned to Mikro, Small, Konsumer for Tanah Abang in Des-25.
# Let's read the pinjaman dataframe manually as done in processor.py
from core.processor import _read_ssa_csv, parse_tanggal_id, format_label

df_p = _read_ssa_csv(p_files[0], "Pinjaman-0")
if len(p_files) > 1:
    frames = [df_p]
    for p in p_files[1:]:
        frames.append(_read_ssa_csv(p, "Pinjaman"))
    df_p = pd.concat(frames, ignore_index=True)

df_p.columns = [str(c).strip() for c in df_p.columns]
kc_col = [c for c in df_p.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df_p.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
segmen_col = [c for c in df_p.columns if 'SEGMEN_2025' in c.upper()][0]
kolekt_col = [c for c in df_p.columns if 'Kolekt' in c or 'Kol' in c][0]
baki_col = [c for c in df_p.columns if 'Baki' in c or 'Outstanding' in c][0]
periode_col = [c for c in df_p.columns if 'Periode' in c or 'Tanggal' in c][0]

df_p['_wilayah'] = None
mask_ta = df_p[kc_col].str.contains('Tanah Abang', case=False, na=False)
df_p.loc[mask_ta, '_wilayah'] = 'Tanah Abang'
df_p = df_p[mask_ta].copy()

# Parse tanggal
df_p['_tanggal'] = df_p[periode_col].apply(parse_tanggal_id)
df_p['_label'] = df_p['_tanggal'].apply(format_label)

# Filter for Des-25
df_p = df_p[df_p['_label'] == 'Des-25'].copy()

# Numeric conversions
def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df_p[baki_col] = df_p[baki_col].apply(parse_numeric)
df_p['_kolekt'] = pd.to_numeric(df_p[kolekt_col], errors='coerce').fillna(0).astype(int)

df_p = df_p[df_p['_kolekt'] != 0].copy()
df_p = df_p[df_p[baki_col] != 0].copy()

# Apply classification logic from processor
df_p['segmen_dashboard_produk'] = df_p[produk_col].astype(str).apply(classify_produk)
df_p['segmen_dashboard_2025'] = df_p[segmen_col].astype(str).apply(classify_segmen_2025)
df_p['segmen_dashboard'] = df_p['segmen_dashboard_produk'].combine_first(df_p['segmen_dashboard_2025'])

print("--- TANAH ABANG, DES-25 BREAKDOWN ---")
res = df_p.groupby(['segmen_dashboard', produk_col, segmen_col])[baki_col].sum() / 1_000_000
for (seg, prod, s2025), val in res.items():
    print(f"[{seg}] {prod} (SEGMEN={s2025}) : {val:,.2f}")

unclassed = df_p[df_p['segmen_dashboard'].isna()]
if not unclassed.empty:
    print("\n--- UNCLASSIFIED ---")
    u_res = unclassed.groupby([produk_col, segmen_col])[baki_col].sum() / 1_000_000
    for (prod, s2025), val in u_res.items():
        print(f"None | {prod} (SEGMEN={s2025}) : {val:,.2f}")

