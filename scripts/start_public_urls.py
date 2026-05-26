#!/usr/bin/env python3
"""掲示物をインターネット公開し、上司送付用URLを発行する（Cloudflare Tunnel）"""
from __future__ import annotations

import re
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLISH_DIR = ROOT / "publish"
SCRIPTS_DIR = Path(__file__).resolve().parent
CLOUDFLARED = SCRIPTS_DIR / "cloudflared.exe"
HOSTING_YAML = ROOT / "data" / "hosting.yaml"
SERVE_SCRIPT = SCRIPTS_DIR / "serve_publish.py"
PORT = 8080

CLINICS = [
    ("kohokudai", "湖北台診療所"),
    ("nogata", "のがたクリニック"),
    ("ikebukuro", "みんなの血管外科池袋"),
    ("yuzawa", "湯沢クリニック"),
]


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_boss_files(base: str) -> None:
    base = base.rstrip("/")
    lines = [
        "【上司送付用】施設基準・算定点数 掲示（令和8年度改定）",
        "",
        f"■ 4院まとめて見る（一覧）",
        f"{base}/",
        "",
    ]
    for cid, name in CLINICS:
        url = f"{base}/{cid}/"
        lines.extend([f"■ {name}", url, ""])

    lines.extend(
        [
            "【ご注意】",
            "・このURLは確認用の一時公開です（このPCの電源・通信が切れると開けなくなります）。",
            "・URLを再発行する場合は start_public_urls.py を再実行してください。",
            "・本番掲載は各クリニック公式サイト（/shisetsu-kijun/）へアップロードしてください。",
        ]
    )

    (ROOT / "上司送付用URL.txt").write_text("\n".join(lines), encoding="utf-8")

    cards = []
    for cid, name in CLINICS:
        url = f"{base}/{cid}/"
        cards.append(
            f"""    <section class="card">
      <h2>{esc(name)}</h2>
      <p><a class="btn" href="{esc(url)}">掲示を開く</a></p>
      <p class="url">{esc(url)}</p>
    </section>"""
        )

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>施設基準掲示｜上司送付用リンク</title>
  <style>
    body {{ font-family: "Yu Gothic", Meiryo, sans-serif; max-width: 40rem; margin: 2rem auto; padding: 0 1rem; }}
    h1 {{ font-size: 1.25rem; color: #1e5a8e; }}
    .note {{ background: #fff8e1; border: 1px solid #f0c040; padding: 0.75rem 1rem; font-size: 0.85rem; margin: 1rem 0; border-radius: 6px; }}
    .card {{ border: 1px solid #e5e7eb; border-radius: 8px; padding: 1rem; margin: 0.75rem 0; }}
    .card h2 {{ margin: 0 0 0.5rem; font-size: 1.05rem; }}
    .btn {{ display: inline-block; background: #1e5a8e; color: #fff !important; padding: 0.5rem 1rem; border-radius: 6px; text-decoration: none; font-weight: bold; }}
    .url {{ font-size: 0.8rem; color: #555; word-break: break-all; margin: 0.5rem 0 0; }}
    .all {{ margin: 1.25rem 0; }}
  </style>
</head>
<body>
  <h1>施設基準・算定点数 掲示（令和8年度改定）</h1>
  <p>下のボタンから各クリニックの掲示をご確認ください。</p>
  <p class="all"><a class="btn" href="{esc(base)}/">4院一覧ページを開く</a></p>
{chr(10).join(cards)}
  <div class="note">
    <p>確認用の一時URLです。PCの電源が切れると閲覧できなくなります。本番は各院ホームページへ掲載します。</p>
  </div>
</body>
</html>
"""
    (ROOT / "上司送付用URL.html").write_text(html, encoding="utf-8")
    HOSTING_YAML.write_text(
        f"# 上司送付・社内確認用（{time.strftime('%Y-%m-%d %H:%M')} 発行）\n"
        f"public_base: {base}\n",
        encoding="utf-8",
    )


def download_cloudflared() -> None:
    if CLOUDFLARED.exists():
        return
    import urllib.request

    url = (
        "https://github.com/cloudflare/cloudflared/releases/download/"
        "2025.4.0/cloudflared-windows-amd64.exe"
    )
    print("cloudflared をダウンロード中...")
    urllib.request.urlretrieve(url, CLOUDFLARED)


def port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> None:
    if not PUBLISH_DIR.is_dir():
        print("publish/ がありません。先に generate.py を実行してください。")
        raise SystemExit(1)

    download_cloudflared()

    if not port_in_use(PORT):
        subprocess.Popen(
            [sys.executable, str(SERVE_SCRIPT)],
            cwd=str(ROOT),
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )
        time.sleep(1.5)

    print("インターネット公開用トンネルを起動中（数十秒かかります）...")
    proc = subprocess.Popen(
        [str(CLOUDFLARED), "tunnel", "--url", f"http://127.0.0.1:{PORT}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    base = None
    assert proc.stdout is not None
    for _ in range(120):
        line = proc.stdout.readline()
        if not line and proc.poll() is not None:
            break
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
        if m:
            base = m.group(0)
            break

    if not base:
        print("公開URLの取得に失敗しました。cloudflared の出力を確認してください。")
        raise SystemExit(1)

    write_boss_files(base)
    print()
    print("=" * 60)
    print("上司に送るURLを作成しました（ファイルも保存済み）")
    print("=" * 60)
    print(f"一覧:     {base}/")
    for cid, name in CLINICS:
        print(f"{name}: {base}/{cid}/")
    print()
    print(f"送付用テキスト: {ROOT / '上司送付用URL.txt'}")
    print(f"送付用HTML:     {ROOT / '上司送付用URL.html'}")
    print()
    print("【重要】このウィンドウを閉じるとURLは使えなくなります。")
    print("       確認中はPCの電源を入れたままにしてください。")
    print("=" * 60)

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
