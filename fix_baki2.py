import re

with open('core/processor.py', 'r') as f:
    content = f.read()

new_parse = """def parse_baki_debet(val) -> float:
    if pd.isna(val) or val is None:
        return 0.0
    s = str(val).strip()
    if s in ('', '-', 'nan', 'None', '#N/A', 'null', 'N/A'):
        return 0.0
        
    if s.replace('-', '').isdigit():
        return float(s)
        
    dots = s.count('.')
    commas = s.count(',')
    last_dot = s.rfind('.')
    last_comma = s.rfind(',')
    
    try:
        if dots > 0 and commas > 0:
            if last_comma > last_dot:
                s = s.replace('.', '').replace(',', '.')
            else:
                s = s.replace(',', '')
        elif dots > 0:
            if dots == 1 and len(s) - last_dot != 4:
                pass 
            else:
                s = s.replace('.', '')
        elif commas > 0:
            if commas == 1 and len(s) - last_comma != 4:
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
                
        return float(s)
    except ValueError:
        return 0.0
"""

old_parse_regex = r"def parse_baki_debet\(val\) -> float:.*?(?=def parse_numeric)"

content = re.sub(old_parse_regex, new_parse, content, flags=re.DOTALL)

with open('core/processor.py', 'w') as f:
    f.write(content)

