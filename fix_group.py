with open('c:/Users/User/dev/tutorial/curriculum_manager/pages/1_Excel_Upload.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'domain = str(row[1]).strip() if pd.notna(row[1]) else "nan"' in line:
        indent = line[:line.find('domain')]
        insert_code = indent + 'group_cands = [str(row[j]).strip() for j in [3, 2] if j < len(row) and pd.notna(row[j]) and str(row[j]).strip() not in ["nan", "None"]]\n'
        insert_code += indent + 'group = group_cands[0] if group_cands else ""\n'
        lines.insert(i + 1, insert_code)
        break

with open('c:/Users/User/dev/tutorial/curriculum_manager/pages/1_Excel_Upload.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
print('Done')
