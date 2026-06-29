import pandas as pd
import glob
import os
from core.processor import prepare_pinjaman, hitung_pinjaman_kc, _find_col, _parse_date

p_files = glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv'))
dfs = []
for p in p_files:
    d = pd.read_csv(p, delimiter=';')
    if len(d.columns) < 5:
        d = pd.read_csv(p, delimiter=',')
    dfs.append(d)
df = pd.concat(dfs, ignore_index=True)

df.rename(columns={
    'Nama Cabang': 'Nama Cabang',
    'SEGMEN_2025': 'SEGMEN_2025',
    'Produk': 'Produk',
    'Month, Day, Year of Periode': 'Month, Day, Year of Periode',
    'Kolektabilitas One Obligor': 'Kolektabilitas One Obligor',
    'Baki Debet': 'Baki Debet'
}, inplace=True)
df['_tanggal'] = df['Month, Day, Year of Periode'].apply(_parse_date)
df['_label'] = df['_tanggal'].apply(lambda d: f"{['','Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'][d.month]}-{str(d.year)[-2:]}" if pd.notnull(d) else "Unknown")
df = prepare_pinjaman(df)

df_k = df[(df['Nama Cabang'].str.contains('Kemayoran', case=False, na=False)) & (df['_label'] == 'Mar-26')]
df_m = df_k[df_k['SEGMEN_2025'] == 'Micro']
print("Micro rows:")
print(df_m[['Produk', 'Kolektabilitas One Obligor', 'Baki Debet']])
print("Sum:", df_m['Baki Debet'].sum())
