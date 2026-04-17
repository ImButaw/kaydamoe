# Read the file with UTF-8 encoding
with open('C:/Users/Admin/Desktop/ashlylegit/livestats.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Remove duplicate state line and fix HELPERS comment
fixed_lines = []
skip_next = False

for i, line in enumerate(lines):
    # Skip the duplicate state line
    if i == 292 and 'state = {' in line and 'team_id' in line:
        if i + 1 < len(lines) and 'state = {' in lines[i + 1] and 'team_id' in lines[i + 1]:
            fixed_lines.append(line)  # Keep the first one
            skip_next = True
            continue
    
    if skip_next and 'state = {' in line and 'team_id' in line:
        skip_next = False
        continue
    
    # Fix the undo_mode line with concatenated HELPERS comment
    if 'undo_mode = {' in line and 'HELPERS' in line:
        # Extract just the undo_mode part and put it on one line
        fixed_lines.append('    undo_mode = {"active": False}\n')
        # Add the HELPERS comment on its own line with proper formatting
        fixed_lines.append('    # ─── HELPERS ───────────────────────────────────────────────────────────\n')
        continue
    
    fixed_lines.append(line)

# Write the fixed file
with open('C:/Users/Admin/Desktop/ashlylegit/livestats.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print('File fixed successfully!')
