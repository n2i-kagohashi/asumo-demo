# -*- coding: utf-8 -*-
"""index.html を台本 v2（timeline_v2.json / scenes_v2.json）へ組み直す。
   旧シーンは捨てず、開始・終了を付け替えて内部の相対秒を掛け直す。
   大きく縮むシーンは「速める」のではなく data-fx の寄りを間引く（見せ場を残す方針）。"""
import json, re, pathlib, math

HERE = pathlib.Path(__file__).parent.parent
# 入力は必ず v1 のバックアップ（index.html は出力先。v2 を再度読むと旧シーンが取れない）
src = (HERE/'_docs/index_v1_backup.html').read_text(encoding='utf-8')
tl = json.loads((HERE/'_audio/timeline_v2.json').read_text(encoding='utf-8'))
rows = {r["no"]: r for r in tl["rows"]}
TOTAL = tl["total"]

# ---------- 旧シーンを取り出す ----------
old = {}
for m in re.finditer(r'(<!-- ===== [^\n]*? ===== -->\n\s*)?<section class="scene([^"]*)" data-start="([\d.]+)" data-end="([\d.]+)"([^>]*)>(.*?)</section>', src, re.S):
    a, b, attrs, body = float(m.group(3)), float(m.group(4)), m.group(5), m.group(6)
    nav = (re.search(r'data-nav="([^"]+)"', attrs) or [None, f'cinema{int(a)}'])[1]
    key = nav if nav not in old else f'{nav}#2'
    old[key] = {"cls": m.group(2), "a": a, "b": b, "attrs": attrs, "body": body, "raw": m.group(0)}
print("旧シーン:", list(old))

def rescale(o, new_dur, keep_fx=None):
    """内部の相対秒を new_dur に合わせて掛け直す。keep_fx を指定すると data-fx をその数まで間引く。"""
    k = new_dur / (o["b"] - o["a"])
    body, attrs = o["body"], o["attrs"]
    if keep_fx is not None:
        fxs = re.findall(r'\s*data-fx="[^"]+"', body)
        if len(fxs) > keep_fx:                      # 前後を残して中を落とす（寄りを減らして1つを長く）
            drop = fxs[1:-1][: len(fxs) - keep_fx]
            for d in drop: body = body.replace(d, "", 1)
    def t1(m): return f'{m.group(1)}="{round(float(m.group(2))*k, 1)}"'
    body = re.sub(r'\b(data-in|data-out|data-click|data-sel|data-on|data-dur)="([\d.]+)"', t1, body)
    def fx(m): return f'data-fx="{round(float(m.group(1))*k,1)}:{round(float(m.group(2))*k,1)}:{m.group(3)}"'
    body = re.sub(r'data-fx="([\d.]+):([\d.]+):([^"]+)"', fx, body)
    sc = re.search(r'data-scroll="([^"]+)"', attrs)
    if sc:
        pts = ",".join(f'{round(float(p.split(":")[0])*k,1)}:{p.split(":")[1]}' for p in sc.group(1).split(","))
        attrs = attrs.replace(sc.group(0), f'data-scroll="{pts}"')
    return attrs, body, k

def scene(o, start, end, keep_fx=None, note=""):
    attrs, body, k = rescale(o, end - start, keep_fx)
    attrs = re.sub(r'\s*data-scroll="[^"]*"', lambda m: m.group(0), attrs)
    return (f'\n            <!-- {note} -->\n'
            f'            <section class="scene{o["cls"]}" data-start="{start}" data-end="{end}"{attrs}>{body}</section>')

def title_card(no, start, end, eyebrow, step=None):
    r = rows[no]; lines = r["cap"].split("\n")
    if len(lines) == 1:
        inner = f'<h2 class="tc-title">{lines[0]}</h2>'
    else:   # 2行あるカードは、1行目 → 2行目の順に出す
        half = round(start + (end - start) * 0.42 - start, 1)
        inner = (f'<h2 class="tc-title">{lines[0]}</h2>'
                 f'<p class="tc-sub cue" data-in="{half}">{lines[1]}</p>')
    st = f' data-step="{step}"' if step is not None else ''
    return (f'\n            <!-- タイトルカード No.{no} -->\n'
            f'            <section class="scene full tcard" data-cinema="1" data-start="{start}" data-end="{end}"{st}>'
            f'<div class="tc"><div class="tc-eyebrow cue" data-in="0.15">{eyebrow}</div>'
            f'<div class="tc-body cue" data-in="0.3">{inner}</div></div></section>')

STEPS11 = ["リスト作成・取込","メール送信","フォーム送信","テレアポ","初回商談資料","商談・議事録",
           "2回目商談資料","見積","申し込み","掲載","請求"]
def overview_scene(start, end):
    chips = "".join(f'<span class="s11 cue" data-in="{round(0.5 + i*0.22, 2)}"><b>{i+1}</b>{t}</span>' for i, t in enumerate(STEPS11))
    return (f'\n            <!-- 11工程の俯瞰 No.3 -->\n'
            f'            <section class="scene full tcard" data-cinema="1" data-start="{start}" data-end="{end}" data-step="0">'
            f'<div class="tc"><div class="tc-eyebrow cue" data-in="0.1">営業工程 1 〜 11</div>'
            f'<div class="s11wrap">{chips}</div></div></section>')   # 一言は字幕（CAPS）が出すので重ねない

DECK = [("p01.jpg","表紙"),("p06.jpg","お客様の課題仮説"),("p08.jpg","課題と解決策の対応"),
        ("p12.jpg","ご提案プラン（松・竹・梅）"),("p13.jpg","お見積り")]
def deck_scene(start, end):
    dur = end - start; step = dur / len(DECK)
    imgs = "".join(
        f'<img class="dk cue" src="deck/{f}" alt="{cap}" data-in="{round(i*step,1)}"'
        + (f' data-out="{round((i+1)*step,1)}"' if i < len(DECK)-1 else '') + '>' for i,(f,cap) in enumerate(DECK))
    caps = "".join(
        f'<span class="dk-cap cue" data-in="{round(i*step,1)}"'
        + (f' data-out="{round((i+1)*step,1)}"' if i < len(DECK)-1 else '') + f'>{cap}</span>' for i,(f,cap) in enumerate(DECK))
    return (f'\n            <!-- 提案書の実物 No.30 -->\n'
            f'            <section class="scene full deckshot" data-cinema="1" data-start="{start}" data-end="{end}" data-step="5">'
            f'<div class="dk-wrap"><div class="dk-stage">{imgs}</div>'
            f'<div class="dk-bar"><span class="dk-title">初回商談資料 — ロジテック物流株式会社 御中</span>{caps}</div></div></section>')

def issuance_scene(start, end):
    """入金の登録・督促の記録（v1 に無い。実装の PaymentModal / DunningModal / issuance に合わせる）"""
    d = end - start
    return f'''
            <!-- 入金・督促 No.45,46 -->
            <section class="scene" data-start="{start}" data-end="{end}" data-nav="/issuance" data-step="11">
              <div class="page"><div class="container">
                <div class="page-head"><h1>🗂️ 発行状況</h1><div class="meta">いま止まっている書類を片付ける画面です。未入金の判定は期間に関わらず出します。</div></div>
                <div class="panel p0"><div style="padding:10px 14px;font-size:13px;font-weight:700">未入金（期限内を含む）</div>
                  <table class="tbl"><thead><tr><th style="width:150px">請求ID</th><th>会社</th><th class="r" style="width:120px">金額(税込)</th><th class="r" style="width:120px">残額</th><th style="width:140px">支払期限</th><th style="width:110px">状態</th><th style="width:250px"></th></tr></thead><tbody>
                    <tr data-fx="0.6:{round(d*0.30,1)}:残額と支払期限で追う"><td class="mono small">I20261031-002</td><td style="white-space:nowrap"><a>東和デリバリー株式会社</a></td><td class="r tnum">¥52,800</td><td class="r tnum"><b class="cue in" data-out="{round(d*0.44,1)}">¥52,800</b><b class="show" data-in="{round(d*0.44,1)}">¥12,800</b></td><td class="small mono">2026-11-30</td><td><span class="pill in_progress cue in" data-out="{round(d*0.44,1)}">発行済</span><span class="pill pending show" data-in="{round(d*0.44,1)}">一部入金</span></td><td><span class="btn sm" data-click="{round(d*0.17,1)}">💴 入金を登録</span> <span class="btn sm secondary">✕ 取消</span></td></tr>
                    <tr data-fx="{round(d*0.56,1)}:{round(d*0.86,1)}:督促は履歴に残る。二度掛けを防ぐ"><td class="mono small">I20260905-001</td><td style="white-space:nowrap"><a>ベイサイド倉庫サービス株式会社</a></td><td class="r tnum">¥64,300</td><td class="r tnum"><b>¥64,300</b></td><td class="small mono">2026-10-05<div class="tiny" style="color:var(--danger)">36日超過</div></td><td><span class="pill error">期限超過</span><div class="tiny muted cue in" data-out="{round(d*0.76,1)}">督促なし</div><div class="tiny show" data-in="{round(d*0.85,1)}">督促 1回（電話）</div></td><td><span class="btn sm">💴 入金を登録</span> <span class="btn sm secondary" data-click="{round(d*0.62,1)}">📣 督促を記録</span></td></tr>
                  </tbody></table></div>
              </div></div>
              <div class="show" data-in="{round(d*0.20,1)}" data-out="{round(d*0.43,1)}" style="position:absolute;inset:0;background:rgba(27,39,38,.45);display:flex;align-items:center;justify-content:center;z-index:10"><div class="panel" data-fx="{round(d*0.20,1)}:{round(d*0.43,1)}:日付と金額で入れる（一部入金も追える）" style="width:560px;margin:0"><h3 style="background:none;border:0;padding:0;margin:0 0 8px;font-size:15px;color:var(--n-900)">入金を登録</h3>
                <table class="tbl"><tbody><tr><td>請求額（税込）</td><td class="r tnum">¥52,800</td><td>支払期限</td><td class="mono small">2026-11-30</td></tr><tr><td>入金済</td><td class="r tnum">¥0</td><td>残額</td><td class="r tnum"><b>¥52,800</b></td></tr></tbody></table>
                <div class="row" style="align-items:flex-end;margin-top:10px"><div class="field" style="margin:0"><label>入金日</label><div class="inp">2026-11-28</div></div><div class="field" style="width:150px;margin:0"><label>入金額（円）</label><div class="inp"><span class="type" data-type="40000" data-in="{round(d*0.24,1)}" data-dur="0.8"></span></div></div><span class="small"><span class="chk on"></span>一部入金</span><span class="btn success" data-click="{round(d*0.38,1)}">💴 入金を登録</span></div>
                <p class="small muted" style="margin:8px 0 0">登録した入金は取り消せません。金額と日付を確かめてから押してください。</p></div></div>
              <div class="toast cue" data-in="{round(d*0.44,1)}" data-out="{round(d*0.56,1)}"><div class="banner ok">✅ I20261031-002 に ¥40,000 の一部入金を記録しました。残額 ¥12,800 は引き続きここで追います。</div></div>
              <div class="show" data-in="{round(d*0.64,1)}" data-out="{round(d*0.84,1)}" style="position:absolute;inset:0;background:rgba(27,39,38,.45);display:flex;align-items:center;justify-content:center;z-index:10"><div class="panel" style="width:600px;margin:0"><h3 style="background:none;border:0;padding:0;margin:0 0 8px;font-size:15px;color:var(--n-900)">督促を記録</h3>
                <div class="row" style="align-items:flex-end"><div class="field" style="width:130px;margin:0"><label>手段</label><div class="sel">電話</div></div><div class="field" style="margin:0"><label>督促日</label><div class="inp">2026-11-10</div></div><div class="field" style="flex:1;margin:0"><label>ひとこと（相手の反応・次の約束）</label><div class="inp"><span class="type" data-type="経理の田中様。今月末に振込予定とのこと" data-in="{round(d*0.68,1)}" data-dur="1.4"></span></div></div><span class="btn success" data-click="{round(d*0.79,1)}">記録する</span></div>
                <p class="small muted" style="margin:8px 0 0">記録は消せません（誰がいつ連絡したかの証跡）。</p></div></div>
              <div class="toast cue" data-in="{round(d*0.85,1)}" data-out="{round(d*0.99,1)}"><div class="banner ok">✅ I20260905-001 に督促を記録しました。次の督促は7日後から「今日の行動」に出ます。</div></div>
            </section>'''

# ---------- シーンを並べる ----------
S = []
S.append(title_card(1, 0.0, 9.7, "ASUMO", 0))
S.append(title_card(2, 9.7, 12.7, "", 0))
S.append(overview_scene(12.7, 17.0))
S.append(title_card(4, 17.0, 19.3, "工程1", 1))
S.append(scene(old['/list-build'], 19.3, 54.2, note="リスト作成 No.5-10"))
S.append(scene(old['/list-import'], 54.2, 57.9, keep_fx=2, note="リスト取込 No.11"))
S.append(scene(old['/outreach'], 57.9, 63.4, keep_fx=2, note="メール送信 No.12"))
S.append(scene(old['/form-outreach'], 63.4, 69.7, keep_fx=3, note="フォーム送信 No.13"))
S.append(title_card(14, 69.7, 72.1, "工程4", 4))
S.append(scene(old['/teleapo'], 72.1, 112.0, note="テレアポ No.15-22（見せ場・v1 と同じ尺）"))
S.append(title_card(23, 112.0, 114.3, "工程4", 4))
S.append(scene(old['/outreach#2'], 114.3, 129.1, note="日程調整・お客様のスマホ No.24-26"))
S.append(title_card(27, 129.1, 131.5, "工程5", 5))
S.append(scene(old['/proposal'], 131.5, 143.5, keep_fx=4, note="初回商談資料 No.28,29"))
S.append(deck_scene(143.5, 151.9))
S.append(scene(old['/minutes2'], 151.9, 162.7, keep_fx=4, note="商談議事録 No.31,32"))
S.append(scene(old['/proposal2'], 162.7, 166.6, note="2回目商談資料 No.33"))
S.append(title_card(34, 166.6, 169.0, "工程8〜10", 8))
S.append(scene(old['/estimate'], 169.0, 178.4, note="見積 No.35,36"))
S.append(scene(old['/contract'], 178.4, 185.7, keep_fx=3, note="申し込み No.37,38"))
S.append(scene(old['/publication'], 185.7, 200.2, note="掲載 No.39,40"))
S.append(title_card(44, 200.2, 205.2, "工程11", 11))
S.append(issuance_scene(205.2, 220.1))
S.append(scene(old['cinema205'], 220.1, TOTAL, note="エンディング No.49,50"))

# ---------- 差し替え ----------
# app-main の中身（画面つきシーン）を入れ替える
start_marker = src.index('>', src.index('<div class="app-main')) + 1
end_marker = src.index('</div><!-- /app-main -->')
head, tail = src[:start_marker], src[end_marker:]
# 全画面シーン（data-cinema）は app の外に置く。まず旧オープニング・エンディングを外す。
for k in ('cinema0', 'cinema205'):
    assert old[k]['raw'] in tail, k
    tail = tail.replace(old[k]['raw'], '', 1)
body_new = "\n" + "".join(x for x in S if 'data-cinema' not in x) + "\n            "
cine_new = "\n".join(x for x in S if 'data-cinema' in x)
anchor = '</div><!-- /app -->'
assert tail.count(anchor) == 1
out = head + body_new + tail.replace(anchor, anchor + "\n" + cine_new + "\n", 1)
(HERE/'index.html').write_text(out, encoding='utf-8')
print(f"シーン {len(S)} 本を書き込み（うち全画面 {sum(1 for s in S if 'data-cinema' in s)} 本）")
