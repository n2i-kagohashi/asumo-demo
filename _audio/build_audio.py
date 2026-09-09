# -*- coding: utf-8 -*-
"""ASUMO デモ用ナレーション: ElevenLabs で生成 → 無音除去 → 213秒の通し1本に合成。
   テキストのハッシュでキャッシュするので、直した行だけ再生成される。"""
import os, re, json, hashlib, pathlib, subprocess, sys, urllib.request, importlib.util

HERE = pathlib.Path(__file__).parent
CACHE = HERE / "cache"; CACHE.mkdir(exist_ok=True)
VOICE = "WQz3clzUdMqvBf0jswZQ"          # Shizuka - Natural（ユーザー選定）
MODEL = "eleven_multilingual_v2"
SETTINGS = {"stability": 0.45, "similarity_boost": 0.75, "style": 0.0, "use_speaker_boost": True}
TOTAL = 213.0
MAX_TEMPO = 1.22                         # これ以上速めると聞いて分かるので、超えたら文を直す
GAP = 0.10                               # 次のキューとのあいだに必ず空ける間

def key():
    for l in open(os.path.expanduser("~/.zshrc"), encoding="utf-8", errors="ignore"):
        m = re.match(r'^export ELEVENLABS_API_KEY=[\'"]?([^\'"\s]+)', l)
        if m: return m.group(1)
    sys.exit("ELEVENLABS_API_KEY が見つかりません")

def load_narr():
    spec = importlib.util.spec_from_file_location("n", HERE / "narration.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.NARR

def dur(p):
    return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                                 "-of","csv=p=0",str(p)], capture_output=True, text=True).stdout.strip())

def tts(text, k):
    h = hashlib.sha1(f"{VOICE}|{MODEL}|{json.dumps(SETTINGS,sort_keys=True)}|{text}".encode()).hexdigest()[:16]
    raw, trimmed = CACHE/f"{h}.mp3", CACHE/f"{h}.trim.wav"
    if not trimmed.exists():
        if not raw.exists():
            body = json.dumps({"text": text, "model_id": MODEL, "voice_settings": SETTINGS}).encode()
            req = urllib.request.Request(
                f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE}?output_format=mp3_44100_128",
                data=body, headers={"xi-api-key": k, "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=180) as r: raw.write_bytes(r.read())
        # 前後の無音を落とす（先頭の立ち上がりぶんの尺を取り戻す）
        sr = "silenceremove=start_periods=1:start_silence=0:start_threshold=-45dB:detection=peak"
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(raw),"-af",
                        f"{sr},areverse,{sr},areverse","-ar","44100","-ac","1",str(trimmed)], check=True)
    return trimmed

def write_caps(narr):
    """index.html の CAPS にそのまま貼れる形を吐く。字幕と音声の台本がずれないように。"""
    def js(x): return "'" + x.replace("\\","\\\\").replace("'","\\'").replace("\n","\\n") + "'"
    out, prev = ["  const CAPS = ["], None
    for a,b,cap,say in narr:
        if prev is not None and a - prev > 0.5: out.append("")
        row = f"    [{a:6.1f}, {b:6.1f}, {js(cap)}"
        if say is not None: row += f", {js(say)}"
        out.append(row + "],")
        prev = b
    out.append("  ];")
    (HERE/"caps.js").write_text("\n".join(out), encoding="utf-8")
    print(f"caps.js を書き出しました（index.html の CAPS と差し替えて使います）")

def main():
    k = key(); narr = load_narr()
    rows, over = [], []
    for i,(a,b,cap,say) in enumerate(narr):
        text = say or cap.replace("\\n","").replace("\n","")
        p = tts(text, k); d = dur(p); win = b - a
        # 収める先は「字幕の窓」ではなく「次のキューが始まるまで」。字幕が一瞬早く消えるのは
        # 気づかれないが、次の声に被るのは事故なので、そこだけは必ず空ける。
        nxt = narr[i+1][0] if i+1 < len(narr) else TOTAL
        avail = max(0.5, nxt - GAP - a)
        tempo = d / avail
        rows.append({"i":i,"start":a,"end":b,"win":win,"avail":avail,"dur":d,"tempo":tempo,
                     "text":text,"path":str(p)})
        if tempo > MAX_TEMPO: over.append(rows[-1])
        print(f"{'超過' if tempo>MAX_TEMPO else 'OK  '} [{a:6.1f}-{b:6.1f}] 窓{win:4.1f}s 余地{avail:4.1f}s "
              f"音声{d:5.2f}s 倍速{tempo:4.2f}x {len(text):2d}字  {text[:30]}")
    (HERE/"cues.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    write_caps(narr)
    print(f"\n合計 {len(rows)}キュー / 収まらない行 {len(over)}件 (許容 {MAX_TEMPO}x まで)")
    if over:
        print("\n▼ 文を短くする必要がある行:")
        for r in over:
            need = int(r["avail"] * MAX_TEMPO * len(r["text"]) / r["dur"])
            print(f"  [{r['start']:6.1f}] {len(r['text'])}字 → {need}字以下に  「{r['text']}」")
    return over

if __name__ == "__main__":
    main()
