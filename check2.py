import sys; sys.stdout.reconfigure(encoding='utf-8')
f = open(r'C:\Users\compu\Desktop\UFC analysis\ufc\templates\index.html', encoding='utf-8')
lines = f.readlines()
f.close()
navlines = [l.rstrip() for l in lines if 'showSection' in l and 'onclick' in l]
print('Current nav items:')
for n in navlines: print(' ', n.strip())
sections = [l.rstrip() for l in lines if 'id="sec-' in l]
print('Current sections:')
for s in sections: print(' ', s.strip())
print('Total lines:', len(lines))
