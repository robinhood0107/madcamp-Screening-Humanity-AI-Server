#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ollama pull 진행률을 터미널에 보기 좋게 출력하는 스크립트.
POST /api/pull 스트림을 읽어 status, completed/total(%) 를 한 줄씩 출력한다.

사용법:
  python ollama_pull_progress.py [모델이름] [--host 호스트:포트]
  python ollama_pull_progress.py glm-4.7-flash
  python ollama_pull_progress.py glm-4.7-flash:latest --host localhost:11434

Docker 컨테이너 밖에서 실행: 포트 11434가 호스트에 매핑되어 있으면 --host localhost:11434 (기본값).
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="Ollama pull 진행률 표시")
    parser.add_argument("model", nargs="?", default="glm-4.7-flash", help="모델 이름 (기본: glm-4.7-flash)")
    parser.add_argument(
        "--host",
        default=os.environ.get("OLLAMA_HOST", "localhost:11434"),
        help="Ollama 호스트 (기본: localhost:11434, env: OLLAMA_HOST)",
    )
    args = parser.parse_args()

    h = args.host.strip()
    url = f"{h}/api/pull" if h.startswith("http://") or h.startswith("https://") else f"http://{h}/api/pull"

    body = json.dumps({"model": args.model, "stream": True}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    print(f"모델: {args.model} | Ollama: {args.host}", flush=True)
    print("연결 중...", flush=True)
    print("-" * 50, flush=True)

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            print("연결됨. 다운로드 스트림 수신 중...", flush=True)
            buf = b""
            while True:
                try:
                    chunk = resp.read(8192)
                except Exception:
                    chunk = b""
                if not chunk:
                    if buf.strip():
                        try:
                            obj = json.loads(buf.decode(errors="replace").strip())
                            if obj.get("error"):
                                print(f"오류: {obj['error']}", flush=True)
                            else:
                                s = obj.get("status") or ""
                                c, t = obj.get("completed"), obj.get("total")
                                if s:
                                    pct = f" ({int(c) * 100 // int(t)}%)" if (t and c is not None and int(t) > 0) else ""
                                    print(s + pct, flush=True)
                                elif t and c is not None and int(t) > 0:
                                    print(f"진행: {int(c) * 100 // int(t)}%", flush=True)
                        except Exception:
                            pass
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line.decode("utf-8", errors="replace"))
                    except Exception:
                        continue
                    err = obj.get("error")
                    if err:
                        print(f"오류: {err}", flush=True)
                        continue
                    s = obj.get("status") or ""
                    c, t = obj.get("completed"), obj.get("total")
                    if s:
                        pct = ""
                        if t and c is not None and int(t) > 0:
                            pct = f" ({int(c) * 100 // int(t)}%)"
                        print(s + pct, flush=True)
                    elif t and c is not None and int(t) > 0:
                        print(f"진행: {int(c) * 100 // int(t)}%", flush=True)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} 오류: {body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"연결 실패: {e}", file=sys.stderr)
        print("  - Ollama 컨테이너: docker ps | grep ollama", file=sys.stderr)
        print("  - 포트 11434 매핑 확인. 원격 서버면: --host 서버IP:11434", file=sys.stderr)
        sys.exit(1)

    print("-" * 50)
    print("완료.")


if __name__ == "__main__":
    main()
