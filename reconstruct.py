import json
import re

transcript_path = '/Users/naufalrasydan/.gemini/antigravity-ide/brain/d5f3c549-e4d2-43b3-80b5-0ec17f3fe3fd/.system_generated/logs/transcript_full.jsonl'

lines_dict = {}

with open(transcript_path, 'r') as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
                output = data.get('content', '')
                if 'File Path: `file:///Users/naufalrasydan/Documents/Workspace/Intern%20BRI/ssa-dashboard/core/processor.py`' in output:
                    # Parse the lines
                    # Format: <line_number>: <original_line>
                    for out_line in output.split('\n'):
                        match = re.match(r'^(\d+):\s(.*)', out_line)
                        if match:
                            line_num = int(match.group(1))
                            content = match.group(2)
                            # Overwrite with the latest seen version of this line
                            lines_dict[line_num] = content
        except Exception:
            pass

print(f"Recovered {len(lines_dict)} unique lines.")
if lines_dict:
    max_line = max(lines_dict.keys())
    print(f"Max line number: {max_line}")
    with open('processor_recovered.py', 'w') as f:
        for i in range(1, max_line + 1):
            f.write(lines_dict.get(i, f"# MISSING LINE {i}\n") + '\n')
    print("Saved to processor_recovered.py")
