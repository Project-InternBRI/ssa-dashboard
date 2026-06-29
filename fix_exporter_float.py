import re

with open('core/exporter.py', 'r') as f:
    content = f.read()

# Replace all occurrences of `c.value = float(val)` with a safe cast
def safe_cast(match):
    return """        try:
            c.value = float(val)
        except (ValueError, TypeError):
            c.value = \"\"
"""

content = re.sub(r'        c\.value = float\(val\)', safe_cast, content)

with open('core/exporter.py', 'w') as f:
    f.write(content)
