# -*- coding: utf-8 -*-
"""timeline_v2.json から試聴ページを作る。行をクリックするとその秒へ頭出しする。
   注意: 静的サーバーが Range に対応していないと途中へシークできない（../serve.py を使う）。"""
import json, pathlib, sys, html
HERE = pathlib.Path(__file__).parent
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
CHANGED = set(int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 and sys.argv[2] else []))
tl = json.loads((HERE / "timeline_v2.json").read_text(encoding="utf-8"))

def row_html(r):
    chg = " chg" if r["no"] in CHANGED else ""
    say = html.escape(r["read"]) if r["read"] else '<span class="m">（音声なし・タイトルカード）</span>'
    dur = f'{r["end"]-r["start"]:.1f}'
    return (f'<tr class="{r["kind"]}{chg}" data-s="{r["start"]}" data-e="{r["end"]}" tabindex="0">'
            f'<td class="no">{r["no"]}{"<span class=dot>●</span>" if chg else ""}</td>'
            f'<td class="t">{r["start"]:.1f}<span class="d">{dur}s</span></td>'
            f'<td class="cap">{html.escape(r["cap"]).replace(chr(10), "<br>")}</td>'
            f'<td class="say">{say}</td></tr>')

body = "".join(row_html(r) for r in tl["rows"])
(OUT / "index.html").write_text(f'''<!doctype html><meta charset="utf-8"><title>ASUMO ナレーション v2 試聴</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
 body{{font-family:'Inter','Noto Sans JP',sans-serif;background:#f6f7f9;color:#1b2726;margin:0;padding:0 24px 40px}}
 .wrap{{max-width:1020px;margin:0 auto}}
 .sticky{{position:sticky;top:0;background:#f6f7f9;padding:18px 0 12px;z-index:3;box-shadow:0 8px 12px -8px rgba(0,0,0,.12)}}
 h1{{font-size:18px;margin:0 0 4px}} .lead{{font-size:12px;color:#667;margin:0 0 10px;line-height:1.7}}
 audio{{width:100%;height:38px;display:block}}
 .bar{{display:flex;gap:12px;align-items:center;font-size:12px;color:#667;margin-top:6px}}
 .cur{{font-family:ui-monospace,monospace;font-weight:700;color:#1b3a6b}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13px;margin-top:12px}}
 th,td{{padding:9px 11px;border-bottom:1px solid #eceef2;vertical-align:top;text-align:left}}
 th{{background:#1b3a6b;color:#fff;font-size:12px;position:sticky;top:118px;z-index:2}}
 tbody tr{{cursor:pointer}} tbody tr:hover td{{background:#f1f5fc}} tbody tr:focus{{outline:2px solid #1b3a6b;outline-offset:-2px}}
 tr.title td{{background:#e8f0fe;font-weight:600}} tr.title:hover td{{background:#dde8fb}}
 tr.now td{{background:#fff3cd !important}} tr.chg td{{box-shadow:inset 3px 0 0 #E8590C}}
 .dot{{color:#E8590C;font-size:9px;margin-left:3px;vertical-align:2px}}
 .no{{width:46px;color:#667}} .t{{width:74px;font-family:ui-monospace,monospace;color:#667}}
 .t .d{{display:block;font-size:10px;color:#aab}} .cap{{width:37%}} .m{{color:#aaa}}
</style>
<div class="wrap"><div class="sticky">
 <h1>ASUMO ナレーション v2（シート反映版）試聴</h1>
 <p class="lead">全体 {tl["total"]}秒。<b>行をクリック（またはキーボードの Enter）でその秒へ頭出し</b>。黄色＝再生中の行。<b style="color:#E8590C">●</b>＝直近で録り直した行。</p>
 <audio id="a" controls preload="auto" src="narration_v2.mp3"></audio>
 <div class="bar"><span>再生位置 <span class="cur" id="cur">0.0</span> / {tl["total"]}秒</span>
  <label><input type="checkbox" id="follow" checked> 再生に合わせてスクロール</label></div>
</div>
<table><thead><tr><th>No</th><th>秒 / 尺</th><th>テロップ（画面）</th><th>読み（音声）</th></tr></thead><tbody>{body}</tbody></table></div>
<script>
const a = document.getElementById('a'), cur = document.getElementById('cur'), follow = document.getElementById('follow');
const trs = [...document.querySelectorAll('tbody tr')];
let pending = null;
/* メタデータが来る前に currentTime を入れても捨てられるので、来るまで持っておく。 */
function seek(sec){{
  if (a.readyState < 1) {{ pending = sec; a.load(); return; }}
  try {{ a.currentTime = sec; }} catch(_) {{ pending = sec; return; }}
  a.play().catch(()=>{{}});
}}
a.addEventListener('loadedmetadata', ()=>{{ if (pending != null) {{ const s = pending; pending = null; seek(s); }} }});
trs.forEach(tr => {{
  const go = () => seek(+tr.dataset.s);
  tr.addEventListener('click', go);
  tr.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); go(); }} }});
}});
let last = null;
a.addEventListener('timeupdate', () => {{
  const t = a.currentTime; cur.textContent = t.toFixed(1);
  const hit = trs.find(tr => t >= +tr.dataset.s && t < +tr.dataset.e) || null;
  if (hit !== last) {{
    trs.forEach(tr => tr.classList.remove('now'));
    if (hit) {{ hit.classList.add('now'); if (follow.checked) hit.scrollIntoView({{block:'center', behavior:'smooth'}}); }}
    last = hit;
  }}
}});
</script>''', encoding='utf-8')
print(f"試聴ページ: {OUT/'index.html'}（{len(tl['rows'])}行 / {tl['total']}秒）")
