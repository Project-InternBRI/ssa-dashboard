import sys

with open('core/processor.py', 'r') as f:
    content = f.read()

old_block = """    if ext == '.csv':
        # Coba berbagai encoding (prioritas utf-8-sig karena BOM)
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(
                    path,
                    sep=';',
                    encoding=enc,
                    dtype=str,
                    skipinitialspace=True,
                    on_bad_lines='skip',
                    low_memory=False,
                )
                # Validasi: harus punya minimal 3 kolom
                if len(df.columns) >= 3:
                    break
                df = None
            except Exception:
                continue

        if df is None:
            raise ValueError(f"Tidak dapat membaca {label}: {Path(path).name}")"""

new_block = """    if ext == '.csv':
        import io
        encodings = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        df = None
        
        for enc in encodings:
            try:
                with open(path, 'r', encoding=enc) as f:
                    lines = f.readlines()
                    
                if not lines:
                    continue
                    
                header = lines[0].strip().split(';')
                header_len = len(header)
                
                fixed_lines = [lines[0].strip()]
                for i in range(1, len(lines)):
                    line = lines[i].strip()
                    if not line:
                        continue
                    parts = line.split(';')
                    
                    if len(parts) > header_len:
                        for j in range(1, len(parts)-1):
                            if parts[j].strip() == '':
                                del parts[j]
                                if len(parts) == header_len:
                                    break
                        if len(parts) > header_len:
                            parts = parts[:header_len]
                            
                    elif len(parts) < header_len:
                        parts.extend([''] * (header_len - len(parts)))
                        
                    fixed_lines.append(';'.join(parts))
                    
                fixed_csv = '\\n'.join(fixed_lines)
                
                df = pd.read_csv(
                    io.StringIO(fixed_csv),
                    sep=';',
                    dtype=str,
                    skipinitialspace=True,
                    low_memory=False,
                )
                
                if len(df.columns) >= 3:
                    break
                df = None
            except Exception as e:
                continue
                
        if df is None:
            raise ValueError(f"Tidak dapat membaca {label}: {Path(path).name}")"""

if old_block in content:
    content = content.replace(old_block, new_block)
    with open('core/processor.py', 'w') as f:
        f.write(content)
    print("Success")
else:
    print("Old block not found!")
    sys.exit(1)
