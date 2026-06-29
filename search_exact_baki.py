import pandas as pd
import glob
import os

p_files = glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv'))
df_list = []
for f in p_files:
    df = pd.read_csv(f, delimiter=';', encoding='utf-8')
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)
df.columns = [str(c).strip() for c in df.columns]

kc_col = [c for c in df.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
kolekt_col = [c for c in df.columns if 'Kolekt' in c or 'Kol' in c][0]
baki_col = [c for c in df.columns if 'Baki' in c or 'Outstanding' in c][0]
periode_col = [c for c in df.columns if 'Periode' in c or 'Tanggal' in c][0]

df = df[df[periode_col].astype(str).str.contains('Desember 2025|Dec 2025|-12-2025|2025-12', case=False, na=False)].copy()

def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df[baki_col] = df[baki_col].apply(parse_numeric)

print("--- SEARCHING FOR ~20,930 BAKI DEBET (Total Kol 1-5) ---")
res = df.groupby([kc_col, produk_col])[baki_col].sum() / 1_000_000
for (kc, prod), val in res.items():
    if 20800 < val < 21000:
        print(f"[{kc}] [{prod}] : {val:,.2f}")

print("\n--- SEARCHING FOR ~576 SML (Kol 2) ---")
df2 = df[df[kolekt_col].astype(str) == '2']
res2 = df2.groupby([kc_col, produk_col])[baki_col].sum() / 1_000_000
for (kc, prod), val in res2.items():
    if 550 < val < 600:
        print(f"[{kc}] [{prod}] : {val:,.2f}")

print("\n--- SEARCHING FOR ~1,286 NPL (Kol 3,4,5) ---")
df_npl = df[df[kolekt_col].astype(str).isin(['3', '4', '5'])]
res_npl = df_npl.groupby([kc_col, produk_col])[baki_col].sum() / 1_000_000
for (kc, prod), val in res_npl.items():
    if 1250 < val < 1350:
        print(f"[{kc}] [{prod}] : {val:,.2f}")

