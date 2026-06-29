import re

with open('core/processor.py', 'r') as f:
    content = f.read()

new_main = """if __name__ == '__main__':
    print("Menjalankan verifikasi numerik Kemayoran Des-25...")
    import os
    from core.processor import process_files
    import glob
    
    # Try to find some CSV files in data/ or history/
    files_s = glob.glob('data/*Simpanan*.csv') + glob.glob('history/*Simpanan*.csv') + glob.glob('data/uploads/*Simpanan*.csv')
    files_p = glob.glob('data/*Pinjaman*.csv') + glob.glob('history/*Pinjaman*.csv') + glob.glob('data/uploads/*Pinjaman*.csv')
    
    if files_s and files_p:
        print(f"Menggunakan file Simpanan: {files_s[0]}")
        print(f"Menggunakan file Pinjaman: {files_p[0]}")
        
        try:
            res = process_files(files_s[0], files_p[0])
            
            # Cari Kemayoran
            if 'Kemayoran' in res:
                print("\\nVerifikasi Kemayoran:")
                kem = res['Kemayoran']['rows']
                
                for r in kem:
                    label = r.get('label')
                    if label == 'Pinjaman - small':
                        print(f"Small all kol (Pinjaman - small) : {r['values']}")
                    elif label == 'small' and r['row_type'] == 'data':
                        # Bisa jadi SML > Small atau NPL > Small
                        # Kita print semuanya
                        print(f"Baris '{label}' (bisa SML/NPL > Small): {r['values']}")
        except Exception as e:
            print(f"Error saat verifikasi: {e}")
    else:
        print("File CSV tidak ditemukan untuk unit test.")"""

content = re.sub(r"if __name__ == '__main__':\n    print\(\"Menjalankan verifikasi numerik Kemayoran Des-25\.\.\.\"\).*?\n", new_main + "\n", content, flags=re.DOTALL)

with open('core/processor.py', 'w') as f:
    f.write(content)
