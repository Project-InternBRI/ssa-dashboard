import pandas as pd
import glob
import os

p_files = glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv'))
print(f"Found files: {p_files}")

df_list = []
for f in p_files:
    df = pd.read_csv(f, delimiter=';', encoding='utf-8')
    df_list.append(df)
df = pd.concat(df_list, ignore_index=True)
df.columns = [str(c).strip() for c in df.columns]

kc_col = [c for c in df.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
baki_col = [c for c in df.columns if 'Baki' in c or 'Outstanding' in c][0]
periode_col = [c for c in df.columns if 'Periode' in c or 'Tanggal' in c][0]
kolekt_col = [c for c in df.columns if 'Kolekt' in c or 'Kol' in c][0]

df = df[df[kc_col].str.contains('Tanah Abang', case=False, na=False)].copy()
df = df[df[periode_col].astype(str).str.contains('Desember 2025|Dec 2025|-12-2025|2025-12', case=False, na=False)].copy()

def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df[baki_col] = df[baki_col].apply(parse_numeric)

print("--- RAW BAKI DEBET BY PRODUK IN TANAH ABANG (DEC 2025) ---")
res = df.groupby([produk_col, kolekt_col])[baki_col].sum() / 1_000_000
for (prod, kol), val in res.items():
    print(f"[{prod}] (Kol={kol}) : {val:,.2f}")

print("\n--- TOTAL BAKI DEBET BY PRODUK ---")
res2 = df.groupby(produk_col)[baki_col].sum() / 1_000_000
for prod, val in res2.items():
    print(f"[{prod}] : {val:,.2f}")

