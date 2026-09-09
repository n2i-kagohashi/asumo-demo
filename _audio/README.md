# ナレーション音声の作り方

`../narration.mp3`（213秒・通し1本）を作り直す手順です。

```bash
export ELEVENLABS_API_KEY=...        # ~/.zshrc に入っていれば不要（スクリプトが読みます）
python3 build_audio.py               # 1キューずつ生成 → 無音除去 → 窓に収まるか判定
python3 assemble.py ../narration.mp3 # タイムラインどおりに1本へ合成
```

- **声**: ElevenLabs `Shizuka - Natural`（`WQz3clzUdMqvBf0jswZQ`）/ `eleven_v3`・stability 0.0・`language_code: ja`
  （言語を明示しないと、カタカナ語を英語の抑揚で読むことがある）。抑揚は `narration.py` の `TAGS`（`[upbeat]` 基調・決め所 `[excited]`）
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

## BGM

`bgm.mp3`（ElevenLabs Music で生成・216秒）があれば、`assemble.py` が声の下に敷きます。
声が鳴っている間は `sidechaincompress` で自動的に沈む（ダッキング）ので、BGM の音量は
`assemble.py` の `BGM_GAIN`（既定 0.12 ≒ -18dB。声の無い区間で -30dB 前後）だけ触れば足ります。BGM を外すなら
`bgm.mp3` を消して `assemble.py` を流し直してください。

作り直し（生成のたびに曲は変わるので、気に入ったものは残しておくこと）:

```bash
curl -X POST "https://api.elevenlabs.io/v1/music" -H "xi-api-key: $ELEVENLABS_API_KEY" \
  -H "Content-Type: application/json" -o bgm.mp3 \
  -d '{"prompt":"Gentle, warm, unobtrusive background music ... instrumental only.","music_length_ms":216000,"model_id":"music_v1","force_instrumental":true}'
```
