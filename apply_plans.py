import os
import glob

plans_dir = r'C:\Users\eckel\.gemini\tmp\invincible-inc\79389143-52bd-4c20-b0ac-5f433c1452e2\plans'
base_dir = r'C:\Users\eckel\OneDrive\Documents\Invincible.Inc'

for plan_file in glob.glob(os.path.join(plans_dir, '*.md')):
    with open(plan_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by '## ' to find the updates
    parts = content.split('\n## ')
    for part in parts[1:]:
        lines = part.split('\n')
        header = lines[0]
        if 'UPDATE:' in header:
            # Extract filepath, e.g., '1. SOVEREIGN TIER UPDATE: Sovereign_Plans/CCTV_GODVIEW_INTEL.md'
            try:
                filepath = header.split('')[1]
                target_path = os.path.join(base_dir, filepath.replace('/', '\\'))
                
                # The content to append is the rest of the part
                content_to_append = '\n\n## ' + '\n'.join(lines[1:])
                
                print(f'Appending to {target_path} from {os.path.basename(plan_file)}')
                
                if os.path.exists(target_path):
                    with open(target_path, 'a', encoding='utf-8') as tf:
                        tf.write('\n\n---' + content_to_append)
                else:
                    with open(target_path, 'w', encoding='utf-8') as tf:
                        tf.write('# ' + os.path.basename(filepath).replace('_', ' ').replace('.md', '') + content_to_append)
            except Exception as e:
                print(f'Error processing part: {e}')

