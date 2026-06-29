from core.processor import process_files
import glob

files_s = glob.glob('data/SSA Simpanan*.csv')
files_p = glob.glob('data/SSA Pinjaman*.csv')

if files_s and files_p:
    res = process_files(files_s, files_p, lambda x,y: None)
    kem_rows = res['Kemayoran']['rows']
    
    # We want Dec-25 (Des-25) column index.
    des_25_key = "Des-25" 
    
    print("Kemayoran Des-25:")
    for r in kem_rows:
        if r.get('row_type') == 'data':
            if r.get('label') == 'Pinjaman - small':
                print(f"  Small all kol  : {r.get('values', {}).get(des_25_key)}")
            elif r.get('label') == 'small': # SML > Small
                print(f"  SML Small Kol=2: {r.get('values', {}).get(des_25_key)}")
            # Wait, NPL > Small label is also "small"
            # How to distinguish? SML is before NPL.
    
