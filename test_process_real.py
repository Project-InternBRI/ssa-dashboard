import glob
import os
import sys
import traceback

from core.processor import process_files

s_files = glob.glob(os.path.expanduser('~/Downloads/SSA Simpanan*.csv'))
p_files = glob.glob(os.path.expanduser('~/Downloads/SSA Pinjaman*.csv'))

if not s_files or not p_files:
    print("No files found.")
    sys.exit(0)

print(f"Found {len(s_files)} Simpanan, {len(p_files)} Pinjaman.")
try:
    # Pass arguments correctly:
    # process_files(simpanan_berjalan, pinjaman_berjalan, simpanan_historis, pinjaman_historis, callback)
    res = process_files(s_files[0], p_files[0], s_files[1:], p_files[1:], lambda x,y: None)
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
