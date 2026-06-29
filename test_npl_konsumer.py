import pandas as pd
import glob
import os

p_files = sorted(glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv')))

df_list = []
for f in p_files:
    df = pd.read_csv(f, delimiter=';', encoding='utf-8')
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)
df.columns = [str(c).strip() for c in df.columns]

kc_col = [c for c in df.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
segmen_col = [c for c in df.columns if 'SEGMEN_2025' in c.upper()][0]
baki_col = [c for c in df.columns if 'Baki' in c or 'Outstanding' in c][0]
periode_col = [c for c in df.columns if 'Periode' in c or 'Tanggal' in c][0]
kol_col = [c for c in df.columns if 'Kolekt' in c or 'Kol' in c][0]

df = df[df[kc_col].str.contains('Tanah Abang', case=False, na=False)].copy()

def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df[baki_col] = df[baki_col].apply(parse_numeric)
df['_kol'] = pd.to_numeric(df[kol_col], errors='coerce').fillna(0).astype(int)

df = df[df['_kol'].isin([3, 4, 5])]

for p in ['Jan 2026', 'Feb 2026', 'Mar 2026']:
    df_p = df[df[periode_col].astype(str).str.contains(p[:3] + '.*' + p[-4:], case=False, na=False, regex=True)]
    print(f"\n--- NPL KONSUMER ({p}) ---")
    df_kon = df_p[df_p[segmen_col].astype(str).str.contains('Consumer|Konsumer', case=False, na=False)]
    res = df_kon.groupby(produk_col)[baki_col].sum() / 1_000_000
    for prod, val in res.items():
        print(f"[{prod}] : {val:,.2f}")
    print(f"Total: {res.sum():,.2f}")

