> # ⚠️ この版は「見本」です。使いません
>
> **実際に発表・配布に使うのは Codex が作る版です。** このブランチ（`feat/invoice-bulk-issue`）と
> 公開URL `https://n2i-kagohashi.github.io/asumo-demo/` に置いてあるのは、
> 台本 v2（スプレッドシート）から動画を組み直す **作り方の見本** として残したものです。
>
> - 作り方の指示書: [_docs/CODEX_VIDEO_INSTRUCTIONS.html](_docs/CODEX_VIDEO_INSTRUCTIONS.html)
> - 台本の正: [_audio/timeline_v2.json](_audio/timeline_v2.json)（元はスプレッドシート）
> - 組み直しの手順: `python3 _docs/build_v2.py && python3 _docs/finish_v2.py && python3 _docs/check_scenes.py`
>
> 福井 聖さん（@shofukui-neo）の `shofukui-neo/asumo-demo` は**この変更を取り込んでいません**。
> そちらの公開URL `https://shofukui-neo.github.io/asumo-demo/` は従来のままです。

# ASUMO 営業ジャーニー（発表用 疑似動画）

求人広告代理店の営業が触る画面を、リスト作成から請求・入金まで **11工程**ぶん通しでたどる、発表用の疑似動画です。
HTML 1 枚で完結しており、ブラウザで開いて開始カードをクリックすると再生が始まります（約3分52秒）。

- 公開URL: https://shofukui-neo.github.io/asumo-demo/
- 登場する企業名・担当者名・メールアドレス・URL・金額はすべて架空のサンプルです。実在の顧客データは含みません。

## 見るときの注意

- ブラウザの仕様上、自動再生はしません。開始カードをクリックしてください。
- **ナレーション付きで再生します**（🔇 ボタン、または `M` キーで消せます）。音声は ElevenLabs で収録した `narration.mp3` 1本で、映像と同じタイムラインに焼いてあります。作り直し方は [_audio/README.md](_audio/README.md) を参照してください。
- 全画面は `F` キー。`#t=120` のように付けると、その秒数に頭出しした状態で開始カードが出ます。
- キー操作: `Space` 再生/停止 ／ `←` `→` 5秒 ／ `[` `]` 章の移動 ／ `R` 最初から ／ `C` チャプター。
