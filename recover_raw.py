import re

log_path = '/Users/naufalrasydan/.gemini/antigravity-ide/brain/d5f3c549-e4d2-43b3-80b5-0ec17f3fe3fd/.system_generated/logs/transcript_full.jsonl'
lines_dict = {}

with open(log_path, 'r') as f:
    for line in f:
        if 'File Path: `file:///Users/naufalrasydan/Documents/Workspace/Intern%20BRI/ssa-dashboard/core/processor.py`' in line:
            # We can use regex to extract everything that looks like "1090:     def ..."
            matches = re.findall(r'\\n(\d+):\s(.*?)(?=\\n|$)', line)
            for m in matches:
                line_num = int(m[0])
                lines_dict[line_num] = m[1].replace('\\n', '')

print(f"Recovered {len(lines_dict)} lines.")
if lines_dict:
    max_l = max(lines_dict.keys())
    with open('processor_recovered.py', 'w') as f:
        for i in range(1, max_l + 1):
            f.write(lines_dict.get(i, f"# MISSING {i}") + '\\n')
    print("Saved processor_recovered.py")
