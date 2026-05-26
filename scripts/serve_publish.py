#!/usr/bin/env python3
"""publish/ フォルダを簡易Webサーバーで公開（同一LANの他PCから閲覧可能）"""
from __future__ import annotations

import http.server
import socket
from pathlib import Path

PORT = 8080
ROOT = Path(__file__).resolve().parent.parent / "publish"


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def main() -> None:
    if not ROOT.is_dir():
        print(f"publish/ がありません。先に generate.py を実行してください: {ROOT}")
        raise SystemExit(1)

    handler = lambda *args, **kwargs: http.server.SimpleHTTPRequestHandler(  # noqa: E731
        *args, directory=str(ROOT), **kwargs
    )
    server = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    ip = local_ip()
    print(f"掲示プレビュー公開中")
    print(f"  このPC:     http://127.0.0.1:{PORT}/")
    print(f"  同一LAN他PC: http://{ip}:{PORT}/")
    print("終了: Ctrl+C")
    server.serve_forever()


if __name__ == "__main__":
    main()
