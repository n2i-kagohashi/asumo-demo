# -*- coding: utf-8 -*-
"""cues.json の各音声を、タイムラインの秒数どおりに 213秒の1本へ並べる。
   窓に入らない行だけ atempo で詰める。最後に音量を揃える。"""
import json, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).parent
TOTAL = 213.0
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "narration.mp3"

cues = json.loads((HERE / "cues.json").read_text(encoding="utf-8"))
inputs, filters, labels = [], [], []
for n, c in enumerate(cues):
    inputs += ["-i", c["path"]]
    chain = []
    if c["tempo"] > 1.0:                      # 窓に入らないぶんだけ速める
        chain.append(f"atempo={min(c['tempo'], 1.22):.4f}")
    chain.append(f"adelay={int(c['start']*1000)}")   # 開始秒に置く
    filters.append(f"[{n}:a]{','.join(chain)}[a{n}]")
    labels.append(f"[a{n}]")

fc = (";".join(filters) + ";" + "".join(labels) +
      f"amix=inputs={len(cues)}:normalize=0:dropout_transition=0[mix];"
      f"[mix]apad,atrim=0:{TOTAL},loudnorm=I=-16:TP=-1.5:LRA=11[out]")
cmd = ["ffmpeg","-v","error","-y",*inputs,"-filter_complex",fc,
       "-map","[out]","-ac","1","-ar","44100","-b:a","128k",str(OUT)]
subprocess.run(cmd, check=True)
d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(OUT)],
                         capture_output=True, text=True).stdout.strip())
print(f"完成: {OUT}")
print(f"  尺 {d:.2f}秒 (目標 {TOTAL}) / サイズ {OUT.stat().st_size/1024/1024:.2f}MB / {len(cues)}キュー")
sped = [c for c in cues if c["tempo"] > 1.0]
print(f"  速度を詰めた行: {len(sped)}件 (最大 {max((c['tempo'] for c in sped), default=1):.2f}x)")
