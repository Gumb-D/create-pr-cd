def load_region_mapping(ref_file):
    """Load Region to Purchasing Area mapping from reference file."""
    mapping = {}
    with open(ref_file, 'r') as f:
        lines = f.readlines()
    in_section = False
    for line_num, line in enumerate(lines):
        if '## Region to Purchasing Area' in line:
            in_section = True
            print(f"Line {line_num}: Found Region section")
            continue
        if in_section and line.startswith('## '):
            print(f"Line {line_num}: Found next section, breaking")
            break
        if in_section and '|' in line:
            # Skip header and separator rows
            if 'Region' in line or '---' in line:
                print(f"Line {line_num}: SKIP (header/separator)")
                continue
            parts = [p.strip() for p in line.split('|')]
            # parts = ['', region, purchasing_area, '']
            print(f"Line {line_num}: parts={parts}")
            if len(parts) >= 3 and parts[1] and parts[2] and parts[1] != '':
                mapping[parts[1]] = parts[2]
                print(f"  -> ADDED: {parts[1]} -> {parts[2]}")
    return mapping

ref_file = 'Info/input/contract_info_reference.md'
result = load_region_mapping(ref_file)
print(f'\nFinal mapping ({len(result)} entries):')
for k, v in sorted(result.items()):
    print(f'  {k} -> {v}')
