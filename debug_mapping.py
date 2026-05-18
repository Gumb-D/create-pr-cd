ref_file = 'Info/contract_info_reference.md'
mapping = {}
with open(ref_file, 'r') as f:
    lines = f.readlines()

in_section = False
for line_num, line in enumerate(lines):
    print(f'{line_num}: {repr(line[:80])}')
    if '## Region to Purchasing Area' in line:
        in_section = True
        print(f'  -> FOUND REGION SECTION')
        continue
    if in_section and line.startswith('## '):
        print(f'  -> END REGION SECTION')
        break
    if in_section and '|' in line and '-' not in line and 'Region' not in line:
        parts = [p.strip() for p in line.split('|')]
        print(f'  -> PARSING: {parts}')
        if len(parts) >= 3 and parts[1] and parts[2]:
            mapping[parts[1]] = parts[2]
            print(f'     ADDED: {parts[1]} -> {parts[2]}')

print('\nFinal mapping:')
for k, v in mapping.items():
    print(f'  {k} -> {v}')
