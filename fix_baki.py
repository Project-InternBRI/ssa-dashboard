import re

with open('core/processor.py', 'r') as f:
    content = f.read()

new_parse = """def parse_baki_debet(val) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null', 'N/A'):
        return 0.0
        
    last_comma = s.rfind(',')
    last_dot = s.rfind('.')
    
    try:
        if last_comma > last_dot:
            # Format Indonesia: koma = desimal, titik = ribuan
            s = s.replace('.', '').replace(',', '.')
        else:
            # Format English: titik = desimal, koma = ribuan
            s = s.replace(',', '')
            
        return float(s)
    except ValueError:
        return 0.0
"""

old_parse = """def parse_baki_debet(val) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null', 'N/A'):
        return 0.0
    try:
        return float(s)
    except ValueError:
        # Format Indonesia: koma = desimal
        s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except:
            return 0.0
"""

content = content.replace(old_parse, new_parse)

# Also let's update the labels to exactly match the user's list just in case.
old_blok2 = """    # ── BLOK 2: Pinjaman ────────────────────────────────────────
    rows.append(p_row('header_value', 'Pinjaman', 'Pinjaman'))
    rows.append(p_row('data', 'Small', 'Small'))
    rows.append(p_row('data', 'Konsumer', 'Konsumer'))
    rows.append(p_row('data', 'Mikro', 'Mikro'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})"""

new_blok2 = """    # ── BLOK 2: Pinjaman ────────────────────────────────────────
    rows.append(p_row('header_value', 'Pinjaman', 'Pinjaman'))
    rows.append(p_row('data', 'Pinjaman - mikro', 'Mikro'))
    rows.append(p_row('data', 'Pinjaman - small', 'Small'))
    rows.append(p_row('data', 'Pinjaman - konsumer', 'Konsumer'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})"""

content = content.replace(old_blok2, new_blok2)

# SML block
old_sml = """    # ── BLOK 3: SML ─────────────────────────────────────────────
    rows.append(p_row('bold', 'SML', 'SML'))
    rows.append(p_row('bold', 'SML %', 'SML %'))
    rows.append(p_row('data', 'Mikro', 'SML > Mikro'))
    rows.append(p_row('data', 'Mikro %', 'Mikro %'))
    rows.append(p_row('data', 'Small', 'SML > Small'))
    rows.append(p_row('data', 'Small %', 'Small %'))
    rows.append(p_row('data', 'Konsumer', 'SML > Konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'Konsumer %'))"""

new_sml = """    # ── BLOK 3: SML ─────────────────────────────────────────────
    rows.append(p_row('bold', 'SML', 'SML'))
    rows.append(p_row('bold', 'SML%', 'SML %'))
    rows.append(p_row('data', 'mikro', 'SML > Mikro'))
    rows.append(p_row('data', 'mikro%', 'Mikro %'))
    rows.append(p_row('data', 'small', 'SML > Small'))
    rows.append(p_row('data', 'small%', 'Small %'))
    rows.append(p_row('data', 'konsumer', 'SML > Konsumer'))
    rows.append(p_row('data', 'konsumer%', 'Konsumer %'))"""

content = content.replace(old_sml, new_sml)

# NPL block
old_npl = """    # ── BLOK 4: NPL ─────────────────────────────────────────────
    rows.append(p_row('bold', 'NPL', 'NPL'))
    rows.append(p_row('bold', 'NPL %', 'NPL %'))
    rows.append(p_row('data', 'Mikro', 'NPL > Mikro'))
    rows.append(p_row('data', 'Mikro %', 'Mikro % NPL'))
    rows.append(p_row('data', 'Small', 'NPL > Small'))
    rows.append(p_row('data', 'Small %', 'Small % NPL'))
    rows.append(p_row('data', 'Konsumer', 'NPL > Konsumer'))
    rows.append(p_row('data', 'Konsumer %', 'Konsumer % NPL'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})"""

new_npl = """    # ── BLOK 4: NPL ─────────────────────────────────────────────
    rows.append(p_row('bold', 'npl', 'NPL'))
    rows.append(p_row('bold', 'npl%', 'NPL %'))
    rows.append(p_row('data', 'mikro', 'NPL > Mikro'))
    rows.append(p_row('data', 'mikro%', 'Mikro % NPL'))
    rows.append(p_row('data', 'small', 'NPL > Small'))
    rows.append(p_row('data', 'small%', 'Small % NPL'))
    rows.append(p_row('data', 'konsumer', 'NPL > Konsumer'))
    rows.append(p_row('data', 'konsumer%', 'Konsumer % NPL'))
    rows.append({'row_type': 'separator', 'label': '', 'values': {}})"""
content = content.replace(old_npl, new_npl)

# EC block
old_ec = """    # ── BLOK 5: Recovery EC ─────────────────────────────────────
    rows.append(p_row('header', 'Recovery. EC', 'Recovery. EC'))
    rows.append(p_row('data', 'Mikro', 'Mikro EC'))
    rows.append(p_row('data', 'Small', 'Small EC'))
    rows.append(p_row('data', 'Konsumer', 'Konsumer EC'))"""

new_ec = """    # ── BLOK 5: Recovery EC ─────────────────────────────────────
    rows.append(p_row('header', 'recovery.EC', 'Recovery. EC'))
    rows.append(p_row('data', 'recovery.EC- mikron', 'Mikro EC'))
    rows.append(p_row('data', 'recovery.EC- small', 'Small EC'))
    rows.append(p_row('data', 'recovery.EC- konsumer', 'Konsumer EC'))"""
content = content.replace(old_ec, new_ec)

with open('core/processor.py', 'w') as f:
    f.write(content)
