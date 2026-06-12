import os
import glob
import re

plans_dir = r'C:\Users\eckel\.gemini\tmp\invincible-inc\79389143-52bd-4c20-b0ac-5f433c1452e2\plans'
base_dir = r'C:\Users\eckel\OneDrive\Documents\Invincible.Inc'

for plan_file in glob.glob(os.path.join(plans_dir, '*plan_overhaul.md')):
    with open(plan_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find blocks using backticks
    matches = re.finditer(r'## \d+\..*?UPDATE:\s*`([^`]+)`\n(.*?)(?=\n## \d|\n---\n\s*\*\*Status|\Z)', content, re.DOTALL)
    for match in matches:
        filepath = match.group(1)
        updates = match.group(2).strip()
        # Remove the italics note if it exists
        updates = re.sub(r'^\*\([^)]+\)\*\n+', '', updates).strip()
        
        target_path = os.path.join(base_dir, filepath.replace('/', '\\'))
        print(f'Updating {target_path}')
        
        append_str = '\n\n---\n\n## UNIVERSAL ANALYSIS PROTOCOL: TACTICAL UPDATES\n\n' + updates + '\n'
        
        if os.path.exists(target_path):
            with open(target_path, 'a', encoding='utf-8') as tf:
                tf.write(append_str)
        else:
            with open(target_path, 'w', encoding='utf-8') as tf:
                tf.write('# ' + os.path.basename(filepath).replace('.md', '').replace('_', ' ') + '\n\n' + append_str)
