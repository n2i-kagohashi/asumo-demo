# -*- coding: utf-8 -*-
"""スプレッドシート（構成・カット割 v2）から音声を作る。
   シートの秒は目安。声が長ければ後続を送る（音に映像を合わせる前提）。
   出力: cues_v2.json（合成用）/ timeline_v2.json（映像の切り直し用）"""
import json, re, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from build_audio import tts, dur, key, TOTAL
HERE = pathlib.Path(__file__).parent
GAP = 0.35                      # 声と声のあいだに必ず空ける
MAX_HOLE = 3.0                  # シート上の穴（消した行のぶん）はここまで詰める
# 音声にだけ当てる読み替え（テロップは触らない）
READ = [("ASUMO","アスモ"),("asumo","アスモ"),("ICP","アイシーピー"),("URL","ユーアールエル"),("Gmail","ジーメール"),
        ("CSV","シーエスブイ"),("PDF","ピーディーエフ"),("AI","エーアイ"),("1社","いっしゃ"),("2回目","二回目"),("「",""),("」","")]
def reading(t):
    for a,b in READ: t = t.replace(a,b)
    return t.strip()
TAGS = {2: "[excited]", 49: "[warm]", 50: "[excited]"}; TAG_DEFAULT = "[upbeat]"

sheet = json.loads((HERE/"sheet_v2.json").read_text(encoding="utf-8"))
rows = []
for r in sheet["rows"]:
    r = [str(c).strip() for c in list(r) + [""]*13]
    no, sec, kind, a, b, _, screen, cap, say = r[:9]
    if not no:                       # No の無い行は直前の行の続き（複数行のカード）
        if rows:
            if cap: rows[-1]["cap"] += "\n" + cap
            if say: rows[-1]["say"] += "。" + say if not rows[-1]["say"].endswith(("。","！","？")) else say
        continue
    if not cap and not say: continue  # 空欄＝削除
    rows.append({"no": int(float(no)), "sec": sec, "kind": "title" if "タイトル" in kind else "cut",
                 "sheet_start": float(a or 0), "sheet_end": float(b or 0), "screen": screen, "cap": cap, "say": say})

k = key(); t = 0.0; cues = []; timeline = []
for r in rows:
    start = max(r["sheet_start"], t + (GAP if t > 0 else 0))
    if t > 0 and start - t > MAX_HOLE: start = t + MAX_HOLE
    if r["say"]:
        text = reading(r["say"]); tag = TAGS.get(r["no"], TAG_DEFAULT)
        p = tts((tag + " " + text).strip(), k); d = dur(p)
        end = start + d
        cues.append({"i": len(cues), "start": round(start,2), "end": round(end,2), "win": round(end-start,2), "avail": 999, "dur": d, "tempo": 0.0, "text": text, "path": str(p)})
        r.update(start=round(start,2), end=round(end,2), audio=round(d,2), read=text)
    else:
        end = start + max(0.5, r["sheet_end"] - r["sheet_start"])   # タイトルカードは尺だけ確保
        r.update(start=round(start,2), end=round(end,2), audio=0, read="")
    t = end; timeline.append(r)
    shift = r["start"] - r["sheet_start"]
    print(f"{r['no']:3d} {'T' if r['kind']=='title' else ' '} {r['start']:6.1f}-{r['end']:6.1f} {'(+%4.1f)'%shift if shift>0.05 else '       '} {r['read'][:36] if r['read'] else '（'+r['cap'][:20]+'）'}")
total = round(t + 0.5, 1)
(HERE/"cues_v2.json").write_text(json.dumps(cues, ensure_ascii=False, indent=1), encoding="utf-8")
(HERE/"timeline_v2.json").write_text(json.dumps({"total": total, "rows": timeline}, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\n行 {len(rows)}（うち音声 {len(cues)}）/ 音声の終わり {t:.1f}秒 → 全体 {total}秒（シート想定 213秒）")
