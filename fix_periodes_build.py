import re

with open('core/processor.py', 'r') as f:
    content = f.read()

old_build = """    # Format untuk hasil: [(label, timestamp), ...]
    periodes_for_build = [(lbl, tgl) for tgl, lbl in periodes_sorted]"""

new_build = """    # Format untuk hasil: [(label, timestamp), ...]
    periodes_for_build = periodes_sorted"""
content = content.replace(old_build, new_build)

with open('core/processor.py', 'w') as f:
    f.write(content)
print("Fixed periodes_for_build.")
