import json
import re

log_path = "/Users/naufalrasydan/.gemini/antigravity-ide/brain/d5f3c549-e4d2-43b3-80b5-0ec17f3fe3fd/.system_generated/logs/transcript_full.jsonl"

def restore_file(target_path, view_file_content):
    # Parse the content
    lines = view_file_content.split('\n')
    restored_lines = []
    started = False
    for line in lines:
        if "The following code has been modified to include a line number before every line" in line:
            started = True
            continue
        if started:
            if "The above content shows the entire, complete file contents of the requested file" in line or "The above content does NOT show the entire file contents" in line:
                break
            
            # Match line number pattern: "123: original line"
            match = re.match(r'^\d+:\s(.*)$', line)
            if match:
                restored_lines.append(match.group(1))
            elif re.match(r'^\d+:$', line): # Empty line case
                restored_lines.append("")
                
    with open(target_path, "w") as f:
        f.write('\n'.join(restored_lines) + '\n')
    print(f"Restored {target_path}")

exporter_content = None
processor_part1 = None
processor_part2 = None

with open(log_path, 'r') as f:
    for line in f:
        data = json.loads(line)
        if "output" in data.get("content", "") and "File Path:" in data.get("content", ""):
            content = data["content"]
            if "core/exporter.py" in content and "Showing lines 1 to 616" in content:
                exporter_content = content
            if "core/processor.py" in content and "Showing lines 1 to 800" in content:
                processor_part1 = content
            if "core/processor.py" in content and "Showing lines 750 to 1007" in content:
                processor_part2 = content

if exporter_content:
    restore_file("core/exporter.py", exporter_content)
else:
    print("Exporter content not found!")

if processor_part1 and processor_part2:
    lines1 = []
    for line in processor_part1.split('\n'):
        if "The following code has been modified" in line:
            started = True
            continue
        if "The above content" in line:
            break
        match = re.match(r'^(\d+):\s(.*)$', line)
        if match:
            lines1.append((int(match.group(1)), match.group(2)))
        elif re.match(r'^(\d+):$', line):
            lines1.append((int(re.match(r'^(\d+):$', line).group(1)), ""))

    lines2 = []
    for line in processor_part2.split('\n'):
        if "The following code has been modified" in line:
            started = True
            continue
        if "The above content" in line:
            break
        match = re.match(r'^(\d+):\s(.*)$', line)
        if match:
            lines2.append((int(match.group(1)), match.group(2)))
        elif re.match(r'^(\d+):$', line):
            lines2.append((int(re.match(r'^(\d+):$', line).group(1)), ""))

    combined = {}
    for num, text in lines1:
        combined[num] = text
    for num, text in lines2:
        combined[num] = text
        
    sorted_lines = [combined[i] for i in sorted(combined.keys())]
    
    with open("core/processor.py", "w") as f:
        f.write('\n'.join(sorted_lines) + '\n')
    print("Restored core/processor.py")
else:
    print("Processor content not found!")
