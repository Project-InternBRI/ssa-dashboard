import json
import re

log_path = '/Users/naufalrasydan/.gemini/antigravity-ide/brain/d5f3c549-e4d2-43b3-80b5-0ec17f3fe3fd/.system_generated/logs/transcript_full.jsonl'

lines_dict = {}

with open(log_path, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                output = data.get('content', '')
                if 'File Path: `file:///Users/naufalrasydan/Documents/Workspace/Intern%20BRI/ssa-dashboard/core/processor.py`' in output:
                    for l in output.split('\\n'):
                        match = re.match(r'^(\d+):\s(.*)', l)
                        if match:
                            line_num = int(match.group(1))
                            lines_dict[line_num] = match.group(2)
        except Exception:
            pass

print(f"Recovered {len(lines_dict)} lines.")
max_l = max(lines_dict.keys()) if lines_dict else 0
print(f"Max line: {max_l}")

# Let's save the lines from 1084 onwards to a file
if max_l > 1084:
    with open('processor_bottom.py', 'w') as f:
        for i in range(1085, max_l + 1):
            f.write(lines_dict.get(i, f"# MISSING {i}") + '\\n')
    print("Saved processor_bottom.py")
