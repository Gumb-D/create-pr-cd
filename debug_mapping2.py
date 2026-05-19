ref_file = 'Info/input/contract_info_reference.md'
mapping = {}
with open(ref_file, 'r') as f:
    lines = f.readlines()

in_section = False
for line_num, line in enumerate(lines):
    if '## Region to Purchasing Area' in line:
        in_section = True
        continue
    if in_section and line.startswith('## '):
        break
    if in_section and '|' in line:
        # Skip header line and separator line
        if 'Region' in line or '---' in line:
            print(f'Line {line_num}: SKIP (header/separator) - {repr(line[:40])}')
            continue
        parts = [p.strip() for p in line.split('|')]
        print(f'Line {line_num}: PARSE {repr(line[:40])} -> {parts}')
        if len(parts) >= 3 and parts[1] and parts[2]:
            mapping[parts[1]] = parts[2]
            print(f'  ADDED: {parts[1]} -> {parts[2]}')

print('\nFinal mapping:')
for k, v in mapping.items():
    print(f'  {k} -> {v}')
