from pathlib import Path
p = Path('app.py')
text = p.read_text(encoding='utf-8')
old = '''                elif key in ['height', 'weight', 'age']:
                    raw = get_data_value(label)
                    try:
                        num = float(re.sub(r'[^\n\d.]', '', str(raw or '')))
                        if key == 'height':
                            value = f"{int(num)} cm"
                        elif key == 'weight':
                            value = f"{int(num)} kg"
                        else:
                            value = f"{int(num)} yrs"
                    except:
                        value = ''
                elif key == 'bmi':
                    try:
                        h = float(re.sub(r'[^\n\d.]', '', str(get_data_value('Height') or '0'))) / 100.0
                        w = float(re.sub(r'[^\n\d.]', '', str(get_data_value('Weight') or '0')))
                if value:
'''
new = '''                elif key in ['height', 'weight', 'age']:
                    raw = get_data_value(label)
                    try:
                        num = float(re.sub(r'[^
\\d.]', '', str(raw or '')))
                        if key == 'height':
                            value = f"{int(num)} cm"
                        elif key == 'weight':
                            value = f"{int(num)} kg"
                        else:
                            value = f"{int(num)} yrs"
                    except:
                        value = ''
                elif key == 'bmi':
                    try:
                        h = float(re.sub(r'[^
\\d.]', '', str(get_data_value('Height') or '0'))) / 100.0
                        w = float(re.sub(r'[^
\\d.]', '', str(get_data_value('Weight') or '0')))
                        if h > 0:
                            value = f"{(w/(h**2)):.1f}"
                    except:
                        value = ''
                if value:
'''
if old not in text:
    print('OLD block not found')
    # print some context to debug
    idx = text.find("num = float(re.sub(r'")
    print('idx', idx)
    if idx != -1:
        print(repr(text[idx:idx+200]))
else:
    p.write_text(text.replace(old, new, 1), encoding='utf-8')
    print('patched')
