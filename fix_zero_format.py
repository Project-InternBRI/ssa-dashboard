import re

with open('core/exporter.py', 'r') as f:
    content = f.read()

# Replace "#,##0" with "#,##0;-#,##0;\"-\""
content = content.replace('"#,##0"', '"#,##0;-#,##0;\\"-\\""')
# There might be some with single quotes '#,##0'
content = content.replace("'#,##0'", '"#,##0;-#,##0;\\"-\\""')

with open('core/exporter.py', 'w') as f:
    f.write(content)
