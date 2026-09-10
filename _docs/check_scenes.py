# -*- coding: utf-8 -*-
"""index.html の検算。JS 構文 / シーンの並び・すき間 / 内部の相対秒 / CAPS の重なりと台本との一致。"""
import json, os, re, subprocess, sys, tempfile, pathlib
from html.parser import HTMLParser
H = pathlib.Path(__file__).parent.parent
s = (H/'index.html').read_text(encoding='utf-8')
tl = json.loads((H/'_audio/timeline_v2.json').read_text(encoding='utf-8')); TOTAL = tl["total"]
ok = True
def say(label, good, detail=""):
    global ok; ok &= good
    print(f"  {'✅' if good else '❌'} {label}" + (f" — {detail}" if detail else ""))

js = re.search(r'<script>\n(.*)\n</script>', s, re.S).group(1)
f = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8'); f.write(js); f.close()
r = subprocess.run(['node','--check',f.name], capture_output=True, text=True); os.unlink(f.name)
say("JS 構文", r.returncode == 0, r.stderr.strip()[:200])

VOID = {'br','img','input','meta','link','hr','rect','path','source'}
secs = []
for m in re.finditer(r'<section class="scene([^"]*)"([^>]*?)data-start="([\d.]+)" data-end="([\d.]+)"([^>]*)>(.*?)</section>', s, re.S):
    a, b = float(m.group(3)), float(m.group(4)); attrs = m.group(2) + m.group(5); body = m.group(6); d = b - a
    nav = (re.search(r'data-nav="([^"]+)"', attrs) or [None, '(全画面)'])[1]
    ts = [float(v) for at in ('data-in','data-out','data-click','data-sel','data-on') for v in re.findall(at+r'="([\d.]+)"', body)]
    ts += [float(y) for x, y, _ in re.findall(r'data-fx="([\d.]+):([\d.]+):([^"]+)"', body)]
    sc = re.search(r'data-scroll="([^"]+)"', attrs)
    if sc: ts += [float(p.split(':')[0]) for p in sc.group(1).split(',')]
    over = [t for t in ts if t > d + 0.05]
    class P(HTMLParser):
        def __init__(x): super().__init__(); x.st=[]; x.err=[]
        def handle_starttag(x,t,at):
            if t not in VOID: x.st.append(t)
        def handle_endtag(x,t):
            if not x.st or x.st[-1] != t: x.err.append(t)
            else: x.st.pop()
    pp = P(); pp.feed(body)
    if over or pp.err or pp.st:
        say(f"{nav} [{a}-{b}]", False, f"尺超え{len(over)}件(最大{max(over) if over else 0}s>{d}s) タグ{pp.err or pp.st}")
    secs.append((a, b, nav))
secs.sort()
say(f"シーン {len(secs)}本 の内部秒とタグ", ok)
gaps = [(secs[i][1], secs[i+1][0]) for i in range(len(secs)-1) if abs(secs[i][1]-secs[i+1][0]) > 0.01]
say("すき間・重なりなし", not gaps, str(gaps[:4]))
say(f"先頭 0.0 / 末尾 {TOTAL}", secs[0][0] == 0.0 and abs(secs[-1][1]-TOTAL) < 0.01, f"実際 {secs[0][0]} / {secs[-1][1]}")
say(f"TOTAL 定数 = {TOTAL}", f'const TOTAL = {TOTAL};' in s)

caps = re.search(r'const CAPS = \[(.*?)\n  \];', s, re.S).group(1)
cr = [(float(a), float(b)) for a, b in re.findall(r'\[\s*([\d.]+),\s*([\d.]+),', caps)]
ovl = [(cr[i], cr[i+1]) for i in range(len(cr)-1) if cr[i+1][0] < cr[i][1] - 0.01]
say(f"CAPS {len(cr)}行 の重なりなし", not ovl, str(ovl[:3]))
exp = [(r["start"], r["end"]) for r in tl["rows"] if r["kind"] != "title"]
say("CAPS が台本と一致", cr == exp, f"{len(cr)} vs {len(exp)}")
for f_ in re.findall(r'src="(deck/[^"]+|narration\.mp3)"', s):
    say(f"参照ファイル {f_}", (H/f_).exists())
print("\n" + ("すべて通過 ✅" if ok else "要修正 ❌")); sys.exit(0 if ok else 1)
