import pandas as pd
import glob
import os

p_files = sorted(glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv')))
df_list = []
for f in p_files:
    df_temp = pd.read_csv(f, delimiter=';', encoding='utf-8')
    df_list.append(df_temp)
df_p = pd.concat(df_list, ignore_index=True)
df_p.columns = [str(c).strip() for c in df_p.columns]

kc_col = [c for c in df_p.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df_p.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
baki_col = [c for c in df_p.columns if 'Baki' in c or 'Outstanding' in c][0]
periode_col = [c for c in df_p.columns if 'Periode' in c or 'Tanggal' in c][0]
kol_col = [c for c in df_p.columns if 'Kolekt' in c or 'Kol' in c][0]

df = df_p[df_p[kc_col].str.contains('Tanah Abang', case=False, na=False)].copy()
df = df[df[periode_col].astype(str).str.contains('Januari 2026|Jan 2026|-01-2026|2026-01', case=False, na=False, regex=True)].copy()

def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df[baki_col] = df[baki_col].apply(parse_numeric)
df['_kol'] = pd.to_numeric(df[kol_col], errors='coerce').fillna(0).astype(int)

print("--- NPL KONSUMER JAN 2026 ---")
df_kons = df[df[produk_col].str.contains('Briguna|KPR|Lainnya', case=False, na=False)]
res = df_kons.groupby([produk_col, '_kol'])[baki_col].sum() / 1_000_000
for (prod, kol), val in res.items():
    if kol in [3, 4, 5]:
        print(f"[{prod}] Kol={kol} : {val:,.2f}")
print("--- SML KONSUMER JAN 2026 ---")
for (prod, kol), val in res.items():
    if kol == 2:
        print(f"[{prod}] Kol={kol} : {val:,.2f}")
