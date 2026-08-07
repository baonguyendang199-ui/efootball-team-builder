from pathlib import Path
p = Path('app.py')
text = p.read_text(encoding='utf-8')
lines = text.splitlines(True)
print(f'LINE COUNT: {len(lines)}')
for i, line in enumerate(lines, 1):
    if "elif key in ['height', 'weight', 'age']:" in line or "elif key == 'bmi':" in line or "num = float(re.sub" in line:
        print(i, repr(line))
        for j in range(max(0, i-3), min(len(lines), i+8)):
            print(f'  {j+1}: {repr(lines[j])}')
        print('---')
        break
