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
  /* ── オープニング: エンディングのロゴ演出 ＋ 2文 ── */
  .end-title.op .op-line{font-size:32px;font-weight:700;color:#fff;line-height:1.5;margin:6px 0 0;letter-spacing:.01em}
  .end-title.op .op-line2{font-size:26px;font-weight:500;color:var(--em-200);margin-top:10px}
  .end-title.op .et-rule{margin:26px 0 22px}
  /* ── 11工程のプロセス図（ガント型・画面全体）── */
  .gt{position:absolute;inset:0;padding:34px 70px 196px;display:flex;flex-direction:column;gap:12px;color:#fff}
  .gt-h{display:flex;align-items:center;justify-content:space-between}
  .gt-eyebrow{font-size:14px;letter-spacing:.24em;color:var(--em-300);font-weight:700}
  .gt-legend{font-size:14px;color:var(--theater-muted);display:flex;align-items:center;gap:6px}
  .gt-legend i{display:inline-block;width:14px;height:14px;border-radius:4px;margin-right:4px}
  .gt-legend i.ai{background:var(--em-500)} .gt-legend i.hu{background:#FF7A6B}
  .gt-lanes,.gt-row{display:grid;grid-template-columns:262px 1fr;align-items:center}
  .gt-lanegrid{display:grid;grid-template-columns:repeat(11,1fr);gap:0 6px}
  .gt-lane{font-size:12px;color:var(--theater-muted);border-top:1px solid var(--theater-line);padding-top:6px;white-space:nowrap;overflow:hidden;min-width:0;text-overflow:ellipsis}
  .gt-lane i{font-style:normal;font-weight:800;color:var(--em-300);margin-right:6px;letter-spacing:.08em}
  .gt-rows{display:flex;flex-direction:column;gap:7px}
  .gt-row{height:38px}
  .gt-label{display:flex;align-items:center;gap:10px;font-size:17px;font-weight:600;white-space:nowrap}
  .gt-label b{display:inline-flex;align-items:center;justify-content:center;width:24px;height:24px;border-radius:50%;
              background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);font-size:12px;font-weight:800}
  .gt-badge{font-size:11px;font-weight:800;color:#2b120e;background:#FF7A6B;border-radius:6px;padding:2px 7px;margin-left:2px}
  .gt-track{position:relative;height:30px;border-left:1px solid var(--theater-line)}
  .gt-track::before{content:"";position:absolute;left:0;right:0;top:50%;height:1px;background:rgba(255,255,255,.06)}
  .gt-bar{position:absolute;top:2px;bottom:2px;border-radius:7px;background:linear-gradient(90deg,var(--em-500),var(--em-400));
          box-shadow:0 4px 14px rgba(21,145,120,.35);transform:scaleX(0);transform-origin:left center;
          transition:transform .55s cubic-bezier(.2,.8,.2,1),opacity .3s}
  .gt-bar.cue{opacity:0;transform:scaleX(0)} .gt-bar.cue.in{opacity:1;transform:scaleX(1)}
  .gt-bar.human{background:linear-gradient(90deg,#FF7A6B,#FF9A8A);box-shadow:0 4px 16px rgba(255,111,97,.45);display:flex;align-items:center;justify-content:center}
  .gt-bar.human em{font-style:normal;font-size:12px;font-weight:800;color:#2b120e;white-space:nowrap}
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
