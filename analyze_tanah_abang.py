import pandas as pd
import os
import glob
from pathlib import Path

# Find the Pinjaman CSV file
files = glob.glob('*Pinjaman*.csv')
if not files:
    print("No Pinjaman files found in root, checking subdirs...")
    files = glob.glob('**/*Pinjaman*.csv', recursive=True)

target_file = None
for f in files:
    if 'data (11)' in f or 'Des' in f or 'Full Data' in f:
        target_file = f
        break

if not target_file and files:
    target_file = files[0]

if not target_file:
    print("Could not find any Pinjaman CSV.")
    exit(1)

print(f"Reading {target_file}...")

# Use the same robust reading logic
def read_csv_robust(path):
    import io
    encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                lines = f.readlines()
            if not lines: continue
            header = lines[0].strip().split(';')
            header_len = len(header)
            fixed_lines = [lines[0].strip()]
            for i in range(1, len(lines)):
                line = lines[i].strip()
                if not line: continue
                parts = line.split(';')
                if len(parts) > header_len:
                    for j in range(1, len(parts)-1):
                        if parts[j].strip() == '':
                            del parts[j]
                            if len(parts) == header_len: break
                    if len(parts) > header_len:
                        parts = parts[:header_len]
                elif len(parts) < header_len:
                    parts.extend([''] * (header_len - len(parts)))
                fixed_lines.append(';'.join(parts))
            fixed_csv = '\n'.join(fixed_lines)
            df = pd.read_csv(io.StringIO(fixed_csv), sep=';', dtype=str)
            return df
        except:
            pass
    return pd.DataFrame()

df = read_csv_robust(target_file)
if df.empty:
    print("Failed to read dataframe.")
    exit(1)

df.columns = [str(c).strip() for c in df.columns]

kc_col = [c for c in df.columns if 'Cabang' in c or 'KC' in c][0]
produk_col = [c for c in df.columns if 'Produk' in c.title() or 'PRODUK' in c.upper()][0]
segmen_col = [c for c in df.columns if 'SEGMEN_2025' in c.upper() or 'SEGMEN 2025' in c.upper()][0]
kolekt_col = [c for c in df.columns if 'Kolekt' in c or 'Kol' in c][0]
baki_col = [c for c in df.columns if 'Baki' in c or 'Outstanding' in c][0]

# Filter Tanah Abang
df = df[df[kc_col].str.contains('Tanah Abang', case=False, na=False)].copy()

# Parse numerics
def parse_numeric(val):
    s = str(val).strip().replace('Rp', '').replace(' ', '')
    s = s.replace('.', '').replace(',', '.')
    try: return float(s)
    except: return 0.0

df[baki_col] = df[baki_col].apply(parse_numeric)
df['_kolekt'] = pd.to_numeric(df[kolekt_col], errors='coerce').fillna(0).astype(int)

# Exclude Kol = 0 and baki = 0
df = df[df['_kolekt'] != 0]
df = df[df[baki_col] != 0]

# Sum by Produk and Segmen_2025
summary = df.groupby([segmen_col, produk_col])[baki_col].sum() / 1_000_000

print("\n--- BAKI DEBET BY SEGMEN_2025 & PRODUK (in Millions) ---")
for (s, p), val in summary.items():
    print(f"{s} | {p}: {val:,.3f}")

print("\n--- TOTALS BY SEGMEN_2025 ---")
print(df.groupby(segmen_col)[baki_col].sum() / 1_000_000)

