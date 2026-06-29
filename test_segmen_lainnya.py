import pandas as pd
import glob
import os
from core.processor import classify_produk, classify_segmen_2025

p_files = sorted(glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv')))

df_p = pd.read_csv(p_files[-1], delimiter=';', encoding='utf-8')
df_p.columns = [str(c).strip() for c in df_p.columns]

produk_col = [c for c in df_p.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
segmen_col = [c for c in df_p.columns if 'SEGMEN_2025' in c.upper()][0]

df_p['segmen_dashboard_2025'] = df_p[segmen_col].astype(str).apply(classify_segmen_2025)
df_p['segmen_dashboard_produk'] = df_p[produk_col].astype(str).apply(classify_produk)

df_p['segmen_dashboard'] = df_p['segmen_dashboard_2025']
for idx, row in df_p.iterrows():
    seg = row['segmen_dashboard']
    if pd.isna(seg) or seg == 'None':
        seg = df_p.at[idx, 'segmen_dashboard_produk']
        if pd.notna(seg) and seg != 'None':
            df_p.at[idx, 'segmen_dashboard'] = seg

df_p.loc[df_p['segmen_dashboard_2025'] == 'EXCLUDE', 'segmen_dashboard'] = None
df_p.loc[df_p['segmen_dashboard_produk'] == 'EXCLUDE', 'segmen_dashboard'] = None
df_p['_segmen'] = df_p['segmen_dashboard']

df_lainnya = df_p[df_p[produk_col].astype(str).str.contains('Lainnya', case=False, na=False)]
print("--- LAINNYA SEGMEN ---")
print(df_lainnya[[produk_col, segmen_col, 'segmen_dashboard_2025', 'segmen_dashboard_produk', 'segmen_dashboard', '_segmen']].head())

