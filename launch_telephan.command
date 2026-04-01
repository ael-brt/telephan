#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"
BACKEND_DIR="$ROOT_DIR/qlio_dash"
FRONTEND_DIR="$ROOT_DIR/visual-identical-twin-main"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"
BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

mkdir -p "$RUN_DIR"

cd "$ROOT_DIR"

if [ ! -f "$ROOT_DIR/.env" ] && [ -f "$ROOT_DIR/.env.example" ]; then
  cp "$ROOT_DIR/.env.example" "$ROOT_DIR/.env"
  echo "[INFO] .env cree depuis .env.example"
fi

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "[ERREUR] Commande manquante: $1"
    exit 1
  fi
}

process_running() {
  local pid_file="$1"
  if [ -f "$pid_file" ]; then
    local pid
    pid="$(cat "$pid_file" 2>/dev/null || true)"
    if [ -n "$pid" ] && kill -0 "$pid" >/dev/null 2>&1; then
      return 0
    fi
  fi
  return 1
}

require_cmd docker
require_cmd python3
require_cmd npm

echo "[1/5] Demarrage MariaDB + phpMyAdmin..."
docker compose up -d mariadb phpmyadmin >/dev/null

echo "[2/5] Verification backend Python..."
if [ ! -x "$BACKEND_DIR/.venv/bin/python" ]; then
  echo "  - Creation du venv backend..."
  python3 -m venv "$BACKEND_DIR/.venv"
fi

if ! "$BACKEND_DIR/.venv/bin/python" -c "import django, pandas, MySQLdb" >/dev/null 2>&1; then
  echo "  - Installation des dependances backend (premier lancement)..."
  "$BACKEND_DIR/.venv/bin/pip" install -r "$BACKEND_DIR/requirements.txt"
fi

echo "[3/5] Verification frontend Node..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "  - Installation des dependances frontend (premier lancement)..."
  (cd "$FRONTEND_DIR" && npm install)
fi

echo "[4/5] Lancement backend Django..."
if process_running "$BACKEND_PID_FILE"; then
  echo "  - Backend deja en cours (PID $(cat "$BACKEND_PID_FILE"))"
else
  nohup bash -lc "
    set -euo pipefail
    cd '$BACKEND_DIR'
    set -a
    [ -f '$ROOT_DIR/.env' ] && . '$ROOT_DIR/.env'
    set +a
    export USE_SQLITE_FALLBACK=\${USE_SQLITE_FALLBACK:-0}
    export DB_HOST=127.0.0.1
    export DB_PORT=3306
    export ENERGY_CSV_PATH='$ROOT_DIR/dataEnergy.csv'
    export FRONTEND_BASE_URL=\${FRONTEND_BASE_URL:-http://127.0.0.1:8080}
    . '.venv/bin/activate'
    python manage.py migrate
    python manage.py runserver 127.0.0.1:8000 --noreload
  " >>"$BACKEND_LOG" 2>&1 &
  echo $! > "$BACKEND_PID_FILE"
  sleep 2
  if process_running "$BACKEND_PID_FILE"; then
    echo "  - Backend lance (PID $(cat "$BACKEND_PID_FILE"))"
  else
    echo "  - Echec backend (voir log: $BACKEND_LOG)"
    exit 1
  fi
fi

echo "[5/5] Lancement frontend Vite..."
if process_running "$FRONTEND_PID_FILE"; then
  echo "  - Frontend deja en cours (PID $(cat "$FRONTEND_PID_FILE"))"
else
  nohup bash -lc "
    set -euo pipefail
    cd '$FRONTEND_DIR'
    npm run dev -- --host 127.0.0.1 --port 8080 --strictPort
  " >>"$FRONTEND_LOG" 2>&1 &
  echo $! > "$FRONTEND_PID_FILE"
  echo "  - Frontend lance (PID $(cat "$FRONTEND_PID_FILE"))"
fi

sleep 2

echo
echo "TELEPHAN Dashboard:"
echo "- Frontend : http://127.0.0.1:8080"
echo "- Backend  : http://127.0.0.1:8000"
echo "- phpMyAdmin : http://127.0.0.1:8081"
echo
echo "Logs:"
echo "- $BACKEND_LOG"
echo "- $FRONTEND_LOG"
echo
echo "Pour arreter: ./stop_telephan.command"

if command -v open >/dev/null 2>&1; then
  open "http://127.0.0.1:8080" >/dev/null 2>&1 || true
fi
