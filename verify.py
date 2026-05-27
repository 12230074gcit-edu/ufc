import sys
sys.stdout.reconfigure(encoding='utf-8')
f = open(r'C:\Users\compu\Desktop\UFC analysis\ufc\templates\index.html', encoding='utf-8')
content = f.read()
f.close()
checks = [
    ('Top15 nav item',     'Top 15 Rankings'),
    ('sec-top15 section',  'sec-top15'),
    ('initTop15 JS',       'initTop15'),
    ('loadDivision JS',    'loadDivision'),
    ('renderRankings JS',  'renderRankings'),
    ('weight grid fixed',  'margin-bottom:16px'),
    ('img support',        'static/fighters/'),
    ('Physical nav gone',  'Physical Attributes'),
    ('Stance nav gone',    'Stance Analysis'),
    ('Experience nav gone','showSection(\'experience\',this)'),
]
for name, term in checks:
    found = term in content
    print(('FOUND  ' if found else 'MISSING') + ' ' + name)
