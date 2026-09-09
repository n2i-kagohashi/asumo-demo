# -*- coding: utf-8 -*-
"""cues.json の各音声を、タイムラインの秒数どおりに 213秒の1本へ並べる。
   窓に入らない行だけ atempo で詰める。bgm.mp3 があれば、声が鳴っている間だけ
   BGM を自動で下げて（ダッキング）混ぜる。最後に音量を揃える。"""
import json, os, pathlib, subprocess, sys
HERE = pathlib.Path(__file__).parent
TOTAL = float(os.environ.get("TOTAL", "213.0"))   # 台本の版で尺が変わる
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "narration.mp3"
BGM = HERE / "bgm.mp3"
BGM_GAIN = 0.12          # 声の下に敷く量（≒ -18dB）。声の無い区間で -30dB 前後、声の間はさらに沈む

import os
CUES = pathlib.Path(os.environ.get("CUES", str(HERE / "cues.json")))   # 台本の版を切り替えられるように
cues = json.loads(CUES.read_text(encoding="utf-8"))
inputs, filters, labels = [], [], []
for n, c in enumerate(cues):
    inputs += ["-i", c["path"]]
    chain = []
    if c["tempo"] > 1.0:                      # 窓に入らないぶんだけ速める
        chain.append(f"atempo={min(c['tempo'], 1.22):.4f}")
    chain.append(f"adelay={int(c['start']*1000)}")   # 開始秒に置く
    filters.append(f"[{n}:a]{','.join(chain)}[a{n}]")
    labels.append(f"[a{n}]")

# 1) 声だけを 213 秒の wav に（音量はここで揃える）
voice = HERE / "voice.wav"
fc = (";".join(filters) + ";" + "".join(labels) +
      f"amix=inputs={len(cues)}:normalize=0:dropout_transition=0[mix];"
      f"[mix]apad,atrim=0:{TOTAL},loudnorm=I=-16:TP=-1.5:LRA=11[out]")
subprocess.run(["ffmpeg","-v","error","-y",*inputs,"-filter_complex",fc,
                "-map","[out]","-ac","1","-ar","44100",str(voice)], check=True)

# 2) BGM があれば混ぜる。声が鳴っている間は sidechaincompress で BGM を沈める
if BGM.exists():
    # 生成曲は出だし30秒が極端に静か（-50dB）で終盤も落ちるので、dynaudnorm で曲全体の音量を
    # 均してから敷く。これで BGM_GAIN が曲の作りに左右されず「声の下にどれだけ敷くか」だけになる。
    fc2 = (f"[1:a]aformat=channel_layouts=mono,atrim=0:{TOTAL},apad,atrim=0:{TOTAL},"
           f"dynaudnorm=f=300:g=5:m=60:p=0.9:r=0.35:s=2,"
           f"afade=t=in:st=0:d=2,afade=t=out:st={TOTAL-4}:d=4,volume={BGM_GAIN}[bgm];"
           f"[bgm][0:a]sidechaincompress=threshold=0.02:ratio=8:attack=60:release=800[duck];"
           f"[0:a][duck]amix=inputs=2:normalize=0:dropout_transition=0[mix];"
           f"[mix]loudnorm=I=-16:TP=-1.5:LRA=11[out]")
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(voice),"-i",str(BGM),"-filter_complex",fc2,
                    "-map","[out]","-ac","1","-ar","44100","-b:a","128k",str(OUT)], check=True)
else:
    subprocess.run(["ffmpeg","-v","error","-y","-i",str(voice),"-ac","1","-ar","44100","-b:a","128k",str(OUT)], check=True)

d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(OUT)],
                         capture_output=True, text=True).stdout.strip())
print(f"完成: {OUT}")
print(f"  尺 {d:.2f}秒 (目標 {TOTAL}) / サイズ {OUT.stat().st_size/1024/1024:.2f}MB / {len(cues)}キュー / BGM {'あり' if BGM.exists() else 'なし'}")
sped = [c for c in cues if c["tempo"] > 1.0]
print(f"  速度を詰めた行: {len(sped)}件 (最大 {max((min(c['tempo'],1.22) for c in sped), default=1):.2f}x)")
