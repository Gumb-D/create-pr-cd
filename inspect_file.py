with open('Info/contract_info_reference.md', 'r') as f:
    lines = f.readlines()

for i in range(5, 14):
    line = lines[i]
    print(f"Line {i}: {repr(line)}")
    print(f"  Has 'Region': {'Region' in line}")
    print(f"  Has '---': {'---' in line}")
    print(f"  Has '|': {'|' in line}")
    parts = [p.strip() for p in line.split('|')]
    print(f"  Parts: {parts}")
    print()
