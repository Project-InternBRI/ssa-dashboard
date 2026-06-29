import pandas as pd
import glob
import os
from core.processor import process_files

s_files = sorted(glob.glob(os.path.expanduser('~/Downloads/SSA Simpanan*.csv')))
p_files = sorted(glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv')))

df_s_curr = s_files[-1]
df_p_curr = p_files[-1]
df_s_hist = s_files[:-1]
df_p_hist = p_files[:-1]

def cb(x, y): pass
res = process_files(df_s_curr, df_p_curr, df_s_hist, df_p_hist, cb)
rows = res['tabel_data'].get('Tanah Abang', [])

print("--- TANAH ABANG SML & NPL (Jan-26 to Mei-26) ---")

sml_small = {}
sml_konsumer = {}
npl_konsumer = {}

mode = ""
for r in rows:
    if r['label'] == 'SML':
        mode = "SML"
    elif r['label'] == 'NPL':
        mode = "NPL"
    elif r.get('row_type') == 'header_value':
        mode = r['label']
    
    if mode == "SML":
        if r['label'] == 'Small' and 'Small %' not in r['label']:
            sml_small = r['values']
        elif r['label'] == 'Konsumer' and 'Konsumer %' not in r['label']:
            sml_konsumer = r['values']
    elif mode == "NPL":
        if r['label'] == 'Konsumer' and 'Konsumer %' not in r['label']:
            npl_konsumer = r['values']

periods = ['Jan-26', 'Feb-26', 'Mar-26', 'Apr-26', 'Mei-26']
for p in periods:
    print(f"[{p}] SML Small: {sml_small.get(p, 0)}, SML Konsumer: {sml_konsumer.get(p, 0)}, NPL Konsumer: {npl_konsumer.get(p, 0)}")

