# -*- coding: utf-8 -*-
"""build_v2.py のあとに流す仕上げ。TOTAL・総尺表記・字幕(CAPS)・章(CH)・CSS・エンディングの文言。"""
import json, re, pathlib
H = pathlib.Path(__file__).parent.parent
p = H/'index.html'; s = p.read_text(encoding='utf-8')
tl = json.loads((H/'_audio/timeline_v2.json').read_text(encoding='utf-8')); TOTAL = tl["total"]
mm, ss = divmod(int(round(TOTAL)), 60)

# ---- 尺 ----
s = re.sub(r'const TOTAL = [\d.]+;', f'const TOTAL = {TOTAL};', s, count=1)
s = re.sub(r'(<span id="ttot">)[^<]*(</span>)', rf'\g<1>{mm}:{ss:02d}\g<2>', s, count=1)
s = s.replace('3分33秒', f'{mm}分{ss:02d}秒')

# ---- 字幕: 22字を超える行は、真ん中に近い句読点で2行に割る（単語の途中で折り返さないため）----
def wrap(t):
    if '\n' in t or len(t) <= 22: return t
    cands = [i for i, ch in enumerate(t) if ch in '、。' and 6 <= i <= len(t)-6]
    if not cands: return t
    i = min(cands, key=lambda i: abs(i - len(t)/2))
    return t[:i+1] + '\n' + t[i+1:]
def js(x): return "'" + x.replace("\\","\\\\").replace("'","\\'").replace("\n","\\n") + "'"
out = ["  /* 字幕。[開始, 終了, 画面に出す字幕, 読み上げ文]。台本は _audio/timeline_v2.json（スプレッドシート由来）。",
       "     タイトルカードの行はここに入れない——カードが画面センターに文字を出すため。長い行は句読点で2行に割る。 */",
       "  const CAPS = ["]
prev = None
for r in tl["rows"]:
    if r["kind"] == "title": continue
    if prev is not None and r["start"] - prev > 1.2: out.append("")
    row = f'    [{r["start"]:6.1f}, {r["end"]:6.1f}, {js(wrap(r["cap"]))}'
    if r["read"] and r["read"] != r["cap"].replace("\n",""): row += f', {js(r["read"])}'
    out.append(row + "],"); prev = r["end"]
out.append("  ];")
caps_js = "\n".join(out)
s = re.sub(r'  /\* 字幕。.*?\n  const CAPS = \[.*?\n  \];', lambda m: caps_js, s, count=1, flags=re.S)

# ---- 章（タイトルカードの位置）----
CH = [(0.0,'オープニング','ASUMO'),(12.7,'概要','11工程をひとつに'),(17.0,'工程1〜3','リード作成 〜 テレアポ準備'),
      (69.7,'工程4','テレアポ'),(112.0,'工程4','アポ獲得後の日程調整'),(129.1,'工程5〜7','提案資料はAIが作成'),
      (166.6,'工程8〜10','受注から掲載まで'),(200.2,'工程11','請求後の入金までフォロー'),(220.1,'エンディング','ASUMO')]
ch_js = "  const CH = [\n" + "".join(f"    [{a:6.1f}, '{b}', '{c}', ''],\n" for a,b,c in CH) + "  ];"
s = re.sub(r'  const CH = \[.*?\n  \];', lambda m: ch_js, s, count=1, flags=re.S)

# ---- CSS ----
CSS = '''
  /* ── タイトルカード（章の頭。機能名を画面センターに約2秒）────────────── */
  .scene.tcard{display:flex;align-items:center;justify-content:center;background:var(--theater);padding:0 80px}
  .tc{text-align:center;max-width:1120px}
  .tc-eyebrow{font-size:15px;letter-spacing:.22em;color:var(--em-400);font-weight:700;margin-bottom:18px;min-height:20px}
  .tc-title{font-size:52px;line-height:1.28;font-weight:800;color:#fff;margin:0;letter-spacing:.01em}
  .tc-sub{font-size:26px;line-height:1.5;color:var(--em-200);margin:18px 0 0;font-weight:500}
  .s11wrap{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;max-width:1040px;margin:6px auto 0}
  .s11{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.18);
       color:#fff;border-radius:999px;padding:10px 18px;font-size:18px;font-weight:600;white-space:nowrap}
  .s11 b{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
         background:var(--em-500);color:#08201d;font-size:13px;font-weight:800}
  /* 提案書の実物。下の帯は字幕に隠れないよう、下に余白を取る */
  .scene.deckshot{display:flex;align-items:flex-start;justify-content:center;background:var(--theater);padding:28px 60px 150px}
  .dk-wrap{width:100%;max-width:1000px}
  .dk-stage{position:relative;width:100%;aspect-ratio:16/9;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.35)}
  .dk{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;background:#fff}
  .dk-bar{display:flex;align-items:center;gap:14px;margin-top:12px;color:#fff;flex-wrap:wrap}
  .dk-title{font-size:15px;font-weight:700}
  .dk-cap{font-size:14px;color:var(--em-200);background:rgba(255,255,255,.10);border-radius:999px;padding:5px 14px}
'''
s = re.sub(r'\n  /\* ── タイトルカード.*?(?=\n  @media \(prefers-reduced-motion:reduce\))', '', s, count=1, flags=re.S)
s = s.replace('\n  @media (prefers-reduced-motion:reduce)', CSS + '\n  @media (prefers-reduced-motion:reduce)', 1)

# ---- エンディングの文言を台本 v2 に ----
s = s.replace('色が付いている <b>テレアポ</b> と <b>商談</b> 以外は、ASUMOが用意する。',
              '<b>テレアポ</b> と <b>商談</b> 以外の裏側は、すべて AI とシステムが。')
s = s.replace('<div class="et-sub">リスト作成・メール・フォーム・テレアポ・商談・見積・申込・掲載・請求——11工程</div>',
              '<div class="et-sub">求人広告の営業プロセスを、AIで変える。</div>')
p.write_text(s, encoding='utf-8')
print(f"finish_v2: TOTAL={TOTAL} ({mm}:{ss:02d}) / CAPS {sum(1 for r in tl['rows'] if r['kind']!='title')}行 / 章 {len(CH)} / 文言・CSS 更新")
