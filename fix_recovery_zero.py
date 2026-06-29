import re

with open('core/processor.py', 'r') as f:
    content = f.read()

# Replace empty strings for recovery with 0.0
content = content.replace("'Recovery. EC' : \"\"", "'Recovery. EC' : 0.0")
content = content.replace("'Mikro EC'     : \"\"", "'Mikro EC'     : 0.0")
content = content.replace("'Small EC'     : \"\"", "'Small EC'     : 0.0")
content = content.replace("'Konsumer EC'  : \"\"", "'Konsumer EC'  : 0.0")

with open('core/processor.py', 'w') as f:
    f.write(content)
