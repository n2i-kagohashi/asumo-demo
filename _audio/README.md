# ナレーション音声の作り方

`../narration.mp3`（213秒・通し1本）を作り直す手順です。

```bash
export ELEVENLABS_API_KEY=...        # ~/.zshrc に入っていれば不要（スクリプトが読みます）
python3 build_audio.py               # 1キューずつ生成 → 無音除去 → 窓に収まるか判定
python3 assemble.py ../narration.mp3 # タイムラインどおりに1本へ合成
```

- **声**: ElevenLabs `Shizuka - Natural`（`WQz3clzUdMqvBf0jswZQ`）/ `eleven_multilingual_v2`
- **台本**: `narration.py` の `NARR`。`(開始秒, 終了秒, 画面に出す字幕, 読み上げ文)` の並びです。
  読み上げ文が `None` のときは字幕をそのまま読みます。`ASUMO` → `アスモ`、`CSV` → `シーエスブイ`、
  `→` や `／` のような記号は、そのままだと誤読するので読み下しています。
- **`index.html` の `CAPS` と同じ内容**にしてください。字幕は `CAPS` が、音は `narration.mp3` が持っています。
  台本を直したら、両方を作り直す必要があります（`build_audio.py` が `CAPS` 形式も出力します）。
- 生成結果は `cache/` にテキストのハッシュで残るので、**直した行だけ**APIを叩きます。

## 窓に収まらないと言われたら

`build_audio.py` が「文を短くする必要がある行」と目標字数を出します。ElevenLabs は
**句読点ごとに 0.6〜1.3 秒の間**を置くので、読点を1つ減らすほうが字を削るより効きます。
実測はおおむね **4.2字/秒**（間を含む）。1.22倍までは `assemble.py` が自動で詰めます。
