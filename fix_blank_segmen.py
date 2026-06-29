import re

with open('core/processor.py', 'r') as f:
    content = f.read()

old_blank = "blank_segmen = (df_p['_segmen_2025'] == '') | (df_p['_segmen_2025'] == 'nan')"
new_blank = "blank_segmen = df_p['_segmen_2025'].str.lower().isin(['', 'nan', 'none', 'null', '#n/a', '-'])"

content = content.replace(old_blank, new_blank)

with open('core/processor.py', 'w') as f:
    f.write(content)
