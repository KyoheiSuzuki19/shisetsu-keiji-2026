#!/usr/bin/env python3
"""YAML定義から院内掲示・ホームページ用HTMLを生成する"""
from __future__ import annotations

import html
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML が必要です: pip install pyyaml")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PUBLISH_DIR = ROOT / "publish"
OSHIRASE_DIR = ROOT / "お知らせ"
WP_UPLOAD_DIR = ROOT / "wordpress-upload"

THEMES = {
    "blue": {"primary": "#1e5a8e", "light": "#e8f2fa", "accent": "#2d7ab8"},
    "green": {"primary": "#1a6b4a", "light": "#e8f5ef", "accent": "#2a8f63"},
}

FOLDERS = {
    "kohokudai": "01-湖北台診療所",
    "nogata": "02-のがたクリニック",
    "ikebukuro": "03-みんなの血管外科池袋",
    "yuzawa": "04-湯沢クリニック",
}


def esc(s: str) -> str:
    return html.escape(str(s), quote=True)


def nl2br(text: str) -> str:
    return esc(text.strip()).replace("\n", "<br>\n")


def render_points(points: list) -> str:
    rows = "".join(
        f'<tr><th scope="row">{esc(p["label"])}</th><td>{esc(p["value"])}</td></tr>'
        for p in points
    )
    return f'<table class="points-table"><tbody>{rows}</tbody></table>'


def render_item(item: dict, for_web: bool) -> str:
    body = nl2br(item.get("body", ""))
    parts = [f'<section class="item" id="{esc(item["id"])}">']
    parts.append(f'<h3>{esc(item["title"])}</h3>')
    parts.append(f'<div class="body">{body}</div>')

    if item.get("subsections"):
        for sub in item["subsections"]:
            parts.append(f'<h4>{esc(sub["heading"])}</h4>')
            parts.append(render_points(sub["points"]))
    elif item.get("points"):
        parts.append(render_points(item["points"]))

    if item.get("footnote"):
        parts.append(f'<p class="footnote">{esc(item["footnote"])}</p>')

    if item.get("patient_note"):
        cls = "patient-note web-only" if for_web else "patient-note"
        parts.append(
            f'<aside class="{cls}"><strong>患者さまへ</strong> {esc(item["patient_note"])}</aside>'
        )

    parts.append("</section>")
    return "\n".join(parts)


def build_items_html(clinic: dict, for_web: bool) -> str:
    return "\n".join(render_item(i, for_web) for i in clinic.get("items", []))


def build_notes(clinic: dict) -> str:
    notes = clinic.get("notes", [])
    if not notes:
        return ""
    lis = "".join(f"<li>{esc(n)}</li>" for n in notes)
    return f'<ul class="notes">{lis}</ul>'


def signage_url(clinic: dict) -> str:
    url = str(clinic.get("signage_url", "")).strip()
    if url:
        return url.rstrip("/") + "/"
    base = str(clinic.get("web_url", "")).rstrip("/")
    return f"{base}/shisetsu-kijun/"


def build_revision_banner(clinic: dict) -> str:
    rev = clinic.get("revision")
    eff = clinic.get("effective_date")
    if not rev and not eff:
        return ""
    parts = []
    if rev:
        parts.append(esc(rev))
    if eff:
        parts.append(f"（{esc(eff)}）")
    return f'<p class="revision-banner">{"".join(parts)}</p>'


def in_hospital_html(clinic: dict) -> str:
    theme = THEMES.get(clinic.get("theme", "blue"), THEMES["blue"])
    items = build_items_html(clinic, for_web=False)
    notes = build_notes(clinic)
    revision = build_revision_banner(clinic)
    specs = "・".join(clinic.get("specialties", []))
    rev_label = esc(clinic.get("revision", "令和8年度（2026年）診療報酬改定"))

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>施設基準・算定点数のお知らせ（院内掲示）｜{esc(clinic["name"])}</title>
  <style>
    @page {{ size: A4; margin: 15mm; }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", Meiryo, sans-serif;
      color: #1a1a1a;
      line-height: 1.7;
      max-width: 210mm;
      margin: 0 auto;
      padding: 12mm;
      background: #fff;
    }}
    header {{
      border-bottom: 3px solid {theme["primary"]};
      padding-bottom: 8px;
      margin-bottom: 16px;
    }}
    h1 {{
      font-size: 1.35rem;
      color: {theme["primary"]};
      margin: 0 0 4px;
    }}
    .meta {{ font-size: 0.85rem; color: #444; }}
    .subtitle {{ font-size: 0.95rem; margin: 8px 0 0; }}
    .revision-banner {{
      font-size: 0.82rem;
      color: {theme["primary"]};
      font-weight: bold;
      margin: 6px 0 0;
    }}
    .notes {{
      background: {theme["light"]};
      border-left: 4px solid {theme["accent"]};
      padding: 8px 12px;
      margin: 12px 0;
      font-size: 0.8rem;
    }}
    .item {{
      break-inside: avoid;
      margin-bottom: 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid #e0e0e0;
    }}
    .item h3 {{
      font-size: 1rem;
      color: {theme["primary"]};
      margin: 0 0 6px;
      padding: 4px 8px;
      background: {theme["light"]};
    }}
    .item h4 {{ font-size: 0.9rem; margin: 8px 0 4px; }}
    .body {{ font-size: 0.88rem; }}
    .points-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.85rem;
      margin: 6px 0;
    }}
    .points-table th, .points-table td {{
      border: 1px solid #ccc;
      padding: 6px 8px;
      text-align: left;
    }}
    .points-table th {{ background: #f5f5f5; width: 65%; }}
    .footnote {{ font-size: 0.8rem; color: #555; }}
    .patient-note {{
      font-size: 0.82rem;
      background: #fffde7;
      border: 1px solid #f0e68c;
      padding: 6px 10px;
      margin-top: 6px;
      border-radius: 4px;
    }}
    footer {{
      margin-top: 20px;
      font-size: 0.75rem;
      color: #666;
      text-align: center;
    }}
    @media print {{
      body {{ padding: 0; }}
      .no-print {{ display: none; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>施設基準・算定点数に関するお知らせ</h1>
    <p class="meta">{esc(clinic["name_full"])}</p>
    <p class="meta">{esc(clinic["address"])}　TEL {esc(clinic["phone"])}</p>
    <p class="subtitle">診療科目：{esc(specs)}</p>
    {revision}
  </header>
  {notes}
  <main>
    {items}
  </main>
  <footer>
    <p>保険医療機関における施設基準等の届出に基づく掲示（{rev_label}）</p>
    <p class="no-print">※ブラウザの「印刷」からA4で印刷できます。</p>
  </footer>
</body>
</html>
"""


def web_html(clinic: dict) -> str:
    theme = THEMES.get(clinic.get("theme", "blue"), THEMES["blue"])
    items = build_items_html(clinic, for_web=True)
    notes = build_notes(clinic)
    revision = build_revision_banner(clinic)
    specs = "・".join(clinic.get("specialties", []))
    rev_label = esc(clinic.get("revision", "令和8年度（2026年）診療報酬改定"))
    page_url = signage_url(clinic)
    jst = timezone(timedelta(hours=9))
    built_at = datetime.now(jst).strftime("%Y-%m-%d %H:%M")

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <title>医療機関としての掲示事項｜{esc(clinic["name"])}</title>
  <meta name="description" content="{esc(clinic["name"])}の施設基準・算定点数に関する掲示事項です。">
  <link rel="canonical" href="{esc(page_url)}">
  <meta property="og:url" content="{esc(page_url)}">
  <meta property="og:title" content="医療機関としての掲示事項｜{esc(clinic["name"])}">
  <meta property="og:type" content="article">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {{
      --color-primary: {theme["primary"]};
      --color-light: {theme["light"]};
      --color-accent: {theme["accent"]};
    }}
    body {{ font-family: "Hiragino Sans", "Hiragino Kaku Gothic ProN", "Yu Gothic", Meiryo, sans-serif; }}
    .item h3 {{
      color: var(--color-primary);
      background: var(--color-light);
      padding: 0.5rem 0.75rem;
      border-radius: 0.25rem;
      font-size: 1.05rem;
      font-weight: 700;
    }}
    .points-table {{ width: 100%; border-collapse: collapse; margin: 0.5rem 0; font-size: 0.95rem; }}
    .points-table th, .points-table td {{ border: 1px solid #d1d5db; padding: 0.5rem 0.75rem; }}
    .points-table th {{ background: #f9fafb; text-align: left; }}
    .patient-note {{
      background: #fffbeb;
      border: 1px solid #fcd34d;
      border-radius: 0.375rem;
      padding: 0.75rem 1rem;
      margin-top: 0.75rem;
      font-size: 0.9rem;
    }}
    .notes li {{ margin-bottom: 0.25rem; }}
    a:focus, button:focus {{ outline: 2px solid var(--color-accent); outline-offset: 2px; }}
  </style>
</head>
<body class="bg-gray-50 text-gray-900">
  <a href="#main" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-white px-3 py-2 shadow rounded">
    本文へスキップ
  </a>
  <header class="bg-white border-b-4" style="border-color: var(--color-primary)">
    <div class="max-w-3xl mx-auto px-4 py-6">
      <p class="text-sm text-gray-600 mb-1">医療機関としての掲示事項</p>
      <h1 class="text-2xl md:text-3xl font-bold" style="color: var(--color-primary)">
        施設基準・算定点数に関するお知らせ
      </h1>
      <p class="mt-2 font-medium">{esc(clinic["name_full"])}</p>
      <p class="text-sm text-gray-600 mt-1">{esc(clinic["address"])}</p>
      <p class="text-sm text-gray-600">TEL <a href="tel:{esc(clinic["phone"].replace("-", ""))}" class="underline" style="color: var(--color-accent)">{esc(clinic["phone"])}</a></p>
      <p class="text-sm mt-2">診療科目：{esc(specs)}</p>
      {revision.replace('class="revision-banner"', 'class="revision-banner text-sm font-semibold mt-2" style="color: var(--color-primary)"') if revision else ''}
    </div>
  </header>

  <main id="main" class="max-w-3xl mx-auto px-4 py-8">
    {notes.replace('class="notes"', 'class="notes text-sm bg-white border-l-4 rounded-r-lg p-4 mb-8 space-y-1" style="border-color: var(--color-accent)"') if notes else ''}

    <nav aria-label="掲示項目一覧" class="mb-8 p-4 bg-white rounded-lg shadow-sm">
      <h2 class="text-lg font-bold mb-3" style="color: var(--color-primary)">目次</h2>
      <ol class="list-decimal list-inside space-y-1 text-sm md:columns-2">
        {''.join(f'<li><a href="#{esc(i["id"])}" class="underline hover:no-underline" style="color: var(--color-accent)">{esc(i["title"])}</a></li>' for i in clinic.get("items", []))}
      </ol>
    </nav>

    <div class="space-y-8 bg-white rounded-lg shadow-sm p-4 md:p-6">
      {items.replace('class="item"', 'class="item pb-6 border-b border-gray-100 last:border-0"')}
    </div>
  </main>

  <footer class="max-w-3xl mx-auto px-4 py-8 text-center text-xs text-gray-500">
    <p>保険医療機関における施設基準等の届出に基づく掲示（{rev_label}）</p>
    <p class="mt-1 text-gray-400">掲示データ更新：{built_at}（JST）</p>
    <p class="mt-2"><a href="{esc(clinic["web_url"])}" class="underline" style="color: var(--color-accent)">クリニック公式サイトへ</a></p>
  </footer>
</body>
</html>
"""


def oshirase_post(clinic: dict) -> str:
    url = signage_url(clinic)
    eff = clinic.get("effective_date", "令和8年6月1日施行")
    rev = clinic.get("revision", "令和8年度（2026年）診療報酬改定")
    return f"""■ お知らせに貼るURL（この1行をリンクにしてください）
{url}

■ お知らせのタイトル（例）
{rev}に伴う施設基準の掲示について

■ お知らせの本文（例・コピー用）
平素より{clinic["name"]}をご利用いただき、ありがとうございます。

{eff}の{rev}に伴い、当院で届出・算定している施設基準および算定点数について、下記ページに掲示いたしました。

▼施設基準・算定点数に関するお知らせ（医療機関としての掲示事項）
{url}

ご不明な点は受付までお問い合わせください。

■ WordPressで掲示ページを作る場合
1. 管理画面 → 固定ページ → 新規追加
2. タイトル：施設基準・算定点数に関するお知らせ
3. パーマリンク（スラッグ）：shisetsu-kijun
4. カスタムHTMLブロックに「wordpress-upload/{clinic["id"]}/本文.html」の内容をすべて貼り付け
   または FTP で「wordpress-upload/{clinic["id"]}/index.html」をサイトの /shisetsu-kijun/ に配置
5. 公開後、上記URLで表示されることを確認してからお知らせを投稿
"""


def web_body_fragment(clinic: dict) -> str:
    """WordPressのカスタムHTMLブロック用（本文のみ）"""
    theme = THEMES.get(clinic.get("theme", "blue"), THEMES["blue"])
    items = build_items_html(clinic, for_web=True)
    notes = build_notes(clinic)
    revision = build_revision_banner(clinic)
    specs = "・".join(clinic.get("specialties", []))
    rev_label = esc(clinic.get("revision", "令和8年度（2026年）診療報酬改定"))
    page_url = signage_url(clinic)

    rev_html = (
        revision.replace(
            'class="revision-banner"',
            'class="revision-banner" style="font-size:0.9rem;font-weight:bold;color:'
            + theme["primary"]
            + ';margin-top:0.5rem"'
        )
        if revision
        else ""
    )
    notes_html = (
        notes.replace(
            'class="notes"',
            'class="notes" style="font-size:0.85rem;background:'
            + theme["light"]
            + ';border-left:4px solid '
            + theme["accent"]
            + ';padding:0.75rem 1rem;margin-bottom:1.5rem;border-radius:0 0.25rem 0.25rem 0"',
        )
        if notes
        else ""
    )

    toc = "".join(
        f'<li style="margin-bottom:0.25rem"><a href="#{esc(i["id"])}" style="color:{theme["accent"]}">{esc(i["title"])}</a></li>'
        for i in clinic.get("items", [])
    )

    return f"""<style>
.shisetsu-keiji .item h3 {{ color:{theme["primary"]}; background:{theme["light"]}; padding:0.5rem 0.75rem; border-radius:0.25rem; font-size:1.05rem; margin:0 0 0.5rem; }}
.shisetsu-keiji .body {{ font-size:0.95rem; }}
.shisetsu-keiji .points-table {{ width:100%; border-collapse:collapse; margin:0.5rem 0; font-size:0.9rem; }}
.shisetsu-keiji .points-table th, .shisetsu-keiji .points-table td {{ border:1px solid #d1d5db; padding:0.5rem 0.75rem; text-align:left; }}
.shisetsu-keiji .points-table th {{ background:#f9fafb; }}
.shisetsu-keiji .footnote {{ font-size:0.85rem; color:#555; }}
.shisetsu-keiji .patient-note {{ background:#fffbeb; border:1px solid #fcd34d; border-radius:0.375rem; padding:0.75rem 1rem; margin-top:0.75rem; font-size:0.9rem; }}
.shisetsu-keiji .item h4 {{ font-size:0.95rem; margin:0.75rem 0 0.35rem; }}
</style>
<div class="shisetsu-keiji" style="font-family:'Yu Gothic',Meiryo,sans-serif;color:#1a1a1a;line-height:1.7;max-width:48rem">
  <header style="border-bottom:4px solid {theme["primary"]};padding-bottom:1rem;margin-bottom:1.5rem">
    <p style="font-size:0.85rem;color:#666;margin:0 0 0.25rem">医療機関としての掲示事項</p>
    <h1 style="font-size:1.5rem;color:{theme["primary"]};margin:0 0 0.5rem">施設基準・算定点数に関するお知らせ</h1>
    <p style="font-weight:bold;margin:0.25rem 0">{esc(clinic["name_full"])}</p>
    <p style="font-size:0.85rem;color:#666;margin:0.15rem 0">{esc(clinic["address"])}</p>
    <p style="font-size:0.85rem;color:#666;margin:0.15rem 0">TEL <a href="tel:{esc(clinic["phone"].replace("-", ""))}" style="color:{theme["accent"]}">{esc(clinic["phone"])}</a></p>
    <p style="font-size:0.85rem;margin:0.25rem 0">診療科目：{esc(specs)}</p>
    {rev_html}
  </header>
  {notes_html}
  <nav aria-label="掲示項目一覧" style="background:#fff;border:1px solid #e5e7eb;border-radius:0.5rem;padding:1rem;margin-bottom:1.5rem">
    <h2 style="font-size:1.05rem;color:{theme["primary"]};margin:0 0 0.5rem">目次</h2>
    <ol style="margin:0;padding-left:1.25rem;font-size:0.9rem">{toc}</ol>
  </nav>
  <div>
    {items.replace('class="item"', 'class="item" style="margin-bottom:1.5rem;padding-bottom:1rem;border-bottom:1px solid #eee"')}
  </div>
  <footer style="margin-top:2rem;padding-top:1rem;border-top:1px solid #e5e7eb;font-size:0.75rem;color:#666;text-align:center">
    <p>保険医療機関における施設基準等の届出に基づく掲示（{rev_label}）</p>
    <p style="margin-top:0.5rem"><a href="{esc(clinic["web_url"])}" style="color:{theme["accent"]}">クリニック公式サイトへ</a></p>
  </footer>
</div>
"""


def wp_upload_readme(clinics: list[dict]) -> str:
    lines = [
        "【WordPress / サーバーへの掲示ページ設置手順】",
        "",
        "お知らせに貼るURLは、各固定ページ公開後に有効になります。",
        "",
        "■ 各クリニックの掲示ページURL",
    ]
    for c in clinics:
        lines.append(f"  {c['name']}：{signage_url(c)}")
    lines.extend(
        [
            "",
            "■ 設置方法（どちらか）",
            "A) WordPress 固定ページ",
            "   1. 固定ページ → 新規 → タイトル「施設基準・算定点数に関するお知らせ」",
            "   2. スラッグを shisetsu-kijun に設定",
            "   3. カスタムHTMLブロックに wordpress-upload/（院名フォルダ）/本文.html を貼付",
            "   4. 公開",
            "",
            "B) FTP・ファイルマネージャ",
            "   wordpress-upload/（院名フォルダ）/index.html を",
            "   サーバーの /shisetsu-kijun/index.html として配置",
            "",
            "■ お知らせ投稿用テキスト",
            "   各院フォルダの「お知らせ/」内テキストをコピーしてください。",
            "",
        ]
    )
    return "\n".join(lines)


def root_url_index_html(clinics: list[dict]) -> str:
    cards = []
    for c in clinics:
        url = signage_url(c)
        folder = FOLDERS[c["id"]]
        cards.append(
            f"""    <section class="card">
      <h2>{esc(c["name"])}</h2>
      <p class="url"><a href="{esc(url)}">{esc(url)}</a></p>
      <p class="meta">お知らせに上記URLをリンクとして掲載してください。</p>
      <ul>
        <li><a href="publish/{c["id"]}/">掲示ページ（アップロード用HTML）</a></li>
        <li><a href="お知らせ/{folder}-お知らせ.txt">お知らせ文面（コピー用）</a></li>
        <li><a href="wordpress-upload/{c["id"]}/本文.html">WordPress貼り付け用HTML</a></li>
      </ul>
    </section>"""
        )
    body = "\n".join(cards)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>各クリニック Web掲示 URL一覧</title>
  <style>
    body {{ font-family: "Yu Gothic", Meiryo, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; color: #1a1a1a; }}
    h1 {{ font-size: 1.4rem; color: #1e5a8e; border-bottom: 3px solid #1e5a8e; padding-bottom: 0.5rem; }}
    .lead {{ background: #eff6ff; border-left: 4px solid #2d7ab8; padding: 1rem; margin: 1rem 0; font-size: 0.95rem; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem 1.25rem; margin: 1rem 0; }}
    .card h2 {{ margin: 0 0 0.5rem; font-size: 1.1rem; color: #1e5a8e; }}
    .url {{ font-size: 1rem; word-break: break-all; }}
    .url a {{ color: #2d7ab8; font-weight: bold; }}
    .meta {{ font-size: 0.85rem; color: #555; }}
    ul {{ margin: 0.5rem 0 0; padding-left: 1.25rem; font-size: 0.9rem; }}
    ol.steps {{ margin-top: 1.5rem; }}
  </style>
</head>
<body>
  <h1>各クリニック Web掲示 URL（お知らせ掲載用）</h1>
  <div class="lead">
    <p><strong>手順：</strong>①下記URLの掲示ページをWordPress等に設置 → ②お知らせ欄に同じURLをリンクで投稿 → ③リンクを開いて掲示内容が表示されることを確認</p>
  </div>
{body}
  <ol class="steps">
    <li><code>wordpress-upload/掲載手順.txt</code> を参照して各院の掲示ページを公開</li>
    <li><code>お知らせ/</code> フォルダの文面をコピーしてお知らせを投稿</li>
    <li>公開URLをクリックし、令和8年度改定の掲示が表示されることを確認</li>
  </ol>
</body>
</html>
"""


def publish_index_html(clinics: list[dict]) -> str:
    rows = []
    for c in clinics:
        url = signage_url(c)
        preview = f"./{c['id']}/"
        rows.append(
            f"""      <tr>
        <td class="py-3 pr-4 font-medium">{esc(c["name"])}</td>
        <td class="py-3 pr-4 break-all"><a href="{esc(url)}" class="text-blue-700 underline">{esc(url)}</a></td>
        <td class="py-3"><a href="{esc(preview)}" class="text-blue-700 underline">アップロード前プレビュー</a></td>
      </tr>"""
        )
    body_rows = "\n".join(rows)
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>施設基準掲示｜公開URL一覧</title>
  <style>
    body {{ font-family: "Yu Gothic", Meiryo, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1 {{ font-size: 1.35rem; color: #1e5a8e; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.95rem; }}
    th, td {{ border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }}
    th {{ background: #f3f4f6; padding: 0.5rem 0.75rem; }}
    .note {{ margin-top: 1.5rem; padding: 1rem; background: #eff6ff; border-left: 4px solid #2d7ab8; font-size: 0.9rem; }}
    code {{ background: #f3f4f6; padding: 0.1rem 0.35rem; border-radius: 3px; }}
  </style>
</head>
<body>
  <h1>施設基準・算定点数 掲示（Web公開用）</h1>
  <p>各クリニックのホームページ掲載用URLです。<code>publish/</code> フォルダの HTML を各URLへアップロードしてください。</p>
  <table>
    <thead>
      <tr><th>クリニック</th><th>公開URL（掲載先）</th><th>確認</th></tr>
    </thead>
    <tbody>
{body_rows}
    </tbody>
  </table>
  <div class="note">
    <p><strong>同一オフィス内で他PCからすぐ確認する場合</strong></p>
    <p>PowerShell で <code>python scripts/serve_publish.py</code> を実行すると、<code>http://&lt;このPCのIP&gt;:8080/</code> から閲覧できます（アップロード前のプレビュー用）。</p>
  </div>
</body>
</html>
"""


def load_hosting() -> dict:
    path = DATA_DIR / "hosting.yaml"
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


def github_pages_base(hosting: dict) -> str | None:
    user = str(hosting.get("github_user", "")).strip()
    repo = str(hosting.get("github_repo", "")).strip()
    if not user or not repo:
        return None
    return f"https://{user}.github.io/{repo}/"


def github_pages_url_html(clinics: list[dict], base: str) -> str:
    base = base.rstrip("/") + "/"
    cards = []
    for c in clinics:
        url = f"{base}{c['id']}/"
        cards.append(
            f"""    <section class="card">
      <h2>{esc(c["name"])}</h2>
      <p><a class="btn" href="{esc(url)}">掲示を開く</a></p>
      <p class="url">{esc(url)}</p>
    </section>"""
        )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitHub Pages 公開URL（常設）</title>
  <style>
    body {{ font-family: "Yu Gothic", Meiryo, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }}
    h1 {{ font-size: 1.3rem; color: #1e5a8e; }}
    .ok {{ background: #ecfdf5; border: 1px solid #6ee7b7; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.9rem; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin: 0.75rem 0; }}
    .btn {{ display: inline-block; background: #1e5a8e; color: #fff !important; padding: 0.5rem 1rem; border-radius: 6px; text-decoration: none; font-weight: bold; }}
    .url {{ font-size: 0.8rem; color: #555; word-break: break-all; margin-top: 0.5rem; }}
  </style>
</head>
<body>
  <h1>施設基準掲示（GitHub Pages・常設URL）</h1>
  <p class="ok">PCの電源に依存せず、スマホ・どのPCからでも開けます。上司への送付はこのURLをご利用ください。</p>
  <p><a class="btn" href="{esc(base)}">4院一覧を開く</a></p>
{chr(10).join(cards)}
</body>
</html>
"""


def github_pages_url_txt(clinics: list[dict], base: str) -> str:
    base = base.rstrip("/") + "/"
    lines = [
        "【上司送付・プレビュー用】施設基準・算定点数 掲示（GitHub Pages）",
        "",
        f"■ 4院まとめて見る（一覧）",
        base,
        "",
    ]
    for c in clinics:
        lines.append(f"■ {c['name']}")
        lines.append(f"{base}{c['id']}/")
        lines.append("")
    lines.extend(
        [
            "【ご注意】",
            "・上記URLは GitHub Pages の常設プレビューです（push 後 1〜3分で反映）。",
            "・古い表示のときは Ctrl+F5 で強制再読み込みしてください。",
            "・フッターに「掲示データ更新」の日時が表示されます。NCDが無く8項目なら最新版です。",
            "・同一PC内の即時確認: python scripts/serve_publish.py → http://127.0.0.1:8080/ikebukuro/",
            "・本番掲載は各クリニック公式サイト（/shisetsu-kijun/）へアップロードしてください。",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    clinics: list[dict] = []
    for yaml_path in sorted(DATA_DIR.glob("*.yaml")):
        with open(yaml_path, encoding="utf-8") as f:
            clinic = yaml.safe_load(f)
        if not clinic or not clinic.get("id"):
            continue
        clinics.append(clinic)

    PUBLISH_DIR.mkdir(parents=True, exist_ok=True)
    OSHIRASE_DIR.mkdir(parents=True, exist_ok=True)
    WP_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    for clinic in clinics:
        cid = clinic["id"]
        folder_name = FOLDERS[cid]
        folder = ROOT / folder_name
        folder.mkdir(parents=True, exist_ok=True)

        web_content = web_html(clinic)
        body_fragment = web_body_fragment(clinic)
        in_path = folder / "院内掲示.html"
        web_path = folder / "ホームページ用.html"
        publish_path = PUBLISH_DIR / cid / "index.html"
        oshirase_path = OSHIRASE_DIR / f"{folder_name}-お知らせ.txt"
        wp_dir = WP_UPLOAD_DIR / cid
        wp_index = wp_dir / "index.html"
        wp_body = wp_dir / "本文.html"

        in_path.write_text(in_hospital_html(clinic), encoding="utf-8")
        web_path.write_text(web_content, encoding="utf-8")
        publish_path.parent.mkdir(parents=True, exist_ok=True)
        publish_path.write_text(web_content, encoding="utf-8")
        oshirase_path.write_text(oshirase_post(clinic), encoding="utf-8")
        wp_dir.mkdir(parents=True, exist_ok=True)
        wp_index.write_text(web_content, encoding="utf-8")
        wp_body.write_text(body_fragment, encoding="utf-8")

        print(f"Generated: {in_path.relative_to(ROOT)}")
        print(f"Generated: {web_path.relative_to(ROOT)}")
        print(f"Generated: {publish_path.relative_to(ROOT)}  -> {signage_url(clinic)}")
        print(f"Generated: {oshirase_path.relative_to(ROOT)}")
        print(f"Generated: {wp_body.relative_to(ROOT)}")

    index_path = PUBLISH_DIR / "index.html"
    index_path.write_text(publish_index_html(clinics), encoding="utf-8")
    print(f"Generated: {index_path.relative_to(ROOT)}")

    readme_path = WP_UPLOAD_DIR / "掲載手順.txt"
    readme_path.write_text(wp_upload_readme(clinics), encoding="utf-8")
    print(f"Generated: {readme_path.relative_to(ROOT)}")

    root_index = ROOT / "公開URL一覧.html"
    root_index.write_text(root_url_index_html(clinics), encoding="utf-8")
    print(f"Generated: {root_index.relative_to(ROOT)}")

    hosting = load_hosting()
    gh_base = github_pages_base(hosting)
    if gh_base:
        gh_html = ROOT / "GitHubPages-公開URL.html"
        gh_txt = ROOT / "GitHubPages-公開URL.txt"
        boss_txt = ROOT / "上司送付用URL.txt"
        boss_html = ROOT / "上司送付用URL.html"
        pages_txt = github_pages_url_txt(clinics, gh_base)
        gh_html.write_text(github_pages_url_html(clinics, gh_base), encoding="utf-8")
        gh_txt.write_text(pages_txt, encoding="utf-8")
        boss_txt.write_text(pages_txt, encoding="utf-8")
        boss_html.write_text(github_pages_url_html(clinics, gh_base), encoding="utf-8")
        print(f"Generated: {gh_html.relative_to(ROOT)}")
        print(f"Generated: {boss_txt.relative_to(ROOT)}")
        print(f"GitHub Pages base: {gh_base}")


if __name__ == "__main__":
    main()
