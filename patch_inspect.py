from pathlib import Path
p = Path('app.py')
text = p.read_text(encoding='utf-8')
lines = text.splitlines()
print(f'LINECOUNT {len(lines)}')
for i in range(2440, min(len(lines), 2490)):
    print(f'{i+1}: {repr(lines[i])}')
