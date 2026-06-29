import json

transcript_file = '/Users/naufalrasydan/.gemini/antigravity-ide/brain/d5f3c549-e4d2-43b3-80b5-0ec17f3fe3fd/.system_generated/logs/transcript_full.jsonl'

# We want to find the output of the multi_replace_file_content or view_file
# that has the content of processor.py just before the truncation.
with open(transcript_file, 'r') as f:
    lines = f.readlines()

for line in lines[-500:]:
    try:
        data = json.loads(line)
        if data.get('source') == 'MODEL' and 'tool_calls' in data:
            for tc in data['tool_calls']:
                if tc['name'] == 'default_api:multi_replace_file_content':
                    args = tc['args']
                    if 'ReplacementChunks' in args:
                        pass
        if data.get('source') == 'SYSTEM' and data.get('type') == 'TOOL_RESPONSE':
            content = data.get('content', '')
            if 'The following code has been modified' in content and 'core/processor.py' in content:
                pass
    except Exception as e:
        pass

