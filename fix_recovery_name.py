import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# Make sure _build_rows maps exactly to the keys in the user's snippet!
content = content.replace("p_row('header', 'recovery.EC', 'Recovery. EC')", "p_row('header', 'recovery.EC', 'Recovery.EC')")

with open('core/processor.py', 'w') as f:
    f.write(content)
