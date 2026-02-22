#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
COMPOSE_FILE="${REPO_ROOT}/docker-compose.yaml"
SERVICES=(gpt-sovits-cu128 gpt-sovits-files-api gpt-sovits-training-api)

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: docker command not found" >&2
  exit 1
fi

compose() {
  docker compose -f "${COMPOSE_FILE}" "$@"
}

start() {
  compose up -d "${SERVICES[@]}"
}

stop() {
  compose stop "${SERVICES[@]}"
}

restart() {
  compose restart "${SERVICES[@]}"
}

status() {
  compose ps "${SERVICES[@]}"
}

logs() {
  compose logs -f "${SERVICES[@]}"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  logs) logs ;;
  *)
    echo "Usage: $0 {start|stop|restart|status|logs}" >&2
    exit 1
    ;;
esac
