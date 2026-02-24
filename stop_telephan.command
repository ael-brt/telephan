#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"

stop_pid_file() {
  local label="$1"
  local pid_file="$2"

  if [ ! -f "$pid_file" ]; then
    echo "- $label: aucun PID"
    return
  fi

  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    echo "- $label: arret (PID $pid)"
  else
    echo "- $label: deja arrete"
  fi
  rm -f "$pid_file"
}

echo "Arret TELEPHAN..."
stop_pid_file "Backend" "$RUN_DIR/backend.pid"
stop_pid_file "Frontend" "$RUN_DIR/frontend.pid"

if command -v docker >/dev/null 2>&1; then
  docker compose -f "$ROOT_DIR/docker-compose.yml" stop mariadb phpmyadmin >/dev/null 2>&1 || true
  echo "- Docker: mariadb + phpMyAdmin stoppes"
fi

echo "OK"

