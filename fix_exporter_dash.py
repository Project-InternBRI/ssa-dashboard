path = "core/exporter.py"
with open(path, "r") as f:
    content = f.read()
    
# We want to replace exactly:
#         except (ValueError, TypeError):
#             c.value = ""
# with:
#         except (ValueError, TypeError):
#             c.value = val if val == "-" else ""

import re
# Handle varying indentation
content = re.sub(
    r"(\s+except \(ValueError, TypeError\):\n\s+)c\.value = \"\"",
    r'\1c.value = val if val == "-" else ""',
    content
)

with open(path, "w") as f:
    f.write(content)
