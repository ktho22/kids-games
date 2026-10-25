# Rebuilds the badge app's pkdata.py and sprites/ from the web game, so the
# two versions share their Pokemon, moves and balance numbers.
# Needs node and Pillow:  python3 build.py
import json, os, glob, subprocess, tempfile
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
APP = os.path.join(HERE, '..', 'pocket_mini_adventure')
D = tempfile.mkdtemp()
subprocess.run(['node', os.path.join(HERE, 'extract.js'), D], check=True)
d = json.load(open(D + '/data.json'))
S = d['SPECIES']
ids = list(S.keys())

def py(v):
  return repr(v)

lines = ['"""Game data generated from the web version of Pocket Mini Adventure. Do not edit by hand."""', '']
# species: id -> (name, type, hp, atk, def, spd, evolveLv, evolveTo, moves, stage)
lines.append('ORDER = ' + py(tuple(ids)))
lines.append('SPECIES = {')
for k, s in S.items():
  to = s.get('evolveTo')
  to = tuple(to) if isinstance(to, list) else to
  lines.append('  %r: (%r, %r, %d, %d, %d, %d, %d, %r, %r, %d),' % (
    k, s['name'], s['type'], s['hp'], s['atk'], s['def'], s['spd'], s.get('evolveLv') or 0, to, tuple(s['mv']), s.get('stage', 0)))
lines.append('}')
# moves: name -> (type, pow, acc, pri, status, status chance)
lines.append('MOVES = {')
for k, m in d['MOVES'].items():
  lines.append('  %r: (%r, %r, %r, %d, %r, %r),' % (k, m['t'], m['pow'], m['acc'], m.get('pri', 0), m.get('st'), m.get('stc', 0)))
lines.append('}')
lines.append('TYPES = {')
for k, t in d['TYPES'].items():
  lines.append('  %r: (%r, %r, %r),' % (k, tuple(t['strong']), tuple(t['weak']), tuple(t.get('barely', []))))
lines.append('}')
lines.append('AREAS = (')
for a in d['AREAS']:
  lines.append('  (%r, %d, %d, %d, %r, %r),' % (a['name'], a['min'], a['max'], a['need'], tuple(a['pool']), tuple(a['rare'])))
lines.append(')')
lines.append('CAVES = (')
for c in d['CAVES']:
  lines.append('  (%r, %r, %r, %r),' % (c['name'], c['badge'], c['trainer'], tuple((i, l) for i, l in c['team'])))
lines.append(')')
L = d['LEGEND']
lines.append('LEGEND = (%r, %r, %r, %r)' % (L['name'], None, L['trainer'], tuple((i, l) for i, l in L['team'])))
lines.append('LEGENDS = ' + py(tuple(d['LEGENDS'])))
lines.append('MEGA = {' + ', '.join('%r: %r' % (k, v['name']) for k, v in d['MEGA'].items()) + '}')
lines.append('PLAZA = ' + py(tuple((p['trainer'], p['type']) for p in d['PLAZA'])))
lines.append('EVOLVED = ' + py(tuple(sorted(d['EVOLVED']))))
for k in ('MEWTWO_LV', 'LEGEND_RATE', 'BOX_MAX', 'GAUGE_MAX'):
  lines.append('%s = %r' % (k, d[k]))
open(APP + '/pkdata.py', 'w').write('\n'.join(lines) + '\n')
print('pkdata.py', os.path.getsize(APP + '/pkdata.py'), 'bytes')

# sprites: trimmed to their outline, shrunk only if bigger than the box,
# then sat on a 48x48 canvas feet-down so every Pokemon stands on the same line
BOX = 48
for f in glob.glob(D + '/raw/*.png'):
  im = Image.open(f).convert('RGBA')
  bb = im.getchannel('A').point(lambda a: 255 if a > 24 else 0).getbbox()
  im = im.crop(bb)
  w, h = im.size
  k = min(1.0, BOX / max(w, h))
  if k < 1:
    im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
  # crisp edges read better on the small screen than a soft fringe
  a = im.getchannel('A').point(lambda v: 255 if v >= 110 else 0)
  im.putalpha(a)
  can = Image.new('RGBA', (BOX, BOX), (0, 0, 0, 0))
  can.paste(im, ((BOX - im.width) // 2, BOX - im.height), im)
  can.save(APP + '/sprites/' + os.path.basename(f), optimize=True)
tot = sum(os.path.getsize(p) for p in glob.glob(APP + '/sprites/*.png'))
print(len(glob.glob(APP + '/sprites/*.png')), 'sprites', tot, 'bytes')
