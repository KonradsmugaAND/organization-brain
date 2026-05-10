#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[INFO] WenetBrain — stopping services..."

# Stop FastAPI server
if [ -f .server.pid ]; then
    kill "$(cat .server.pid)" 2>/dev/null || true
    rm .server.pid
    echo "  → FastAPI server stopped"
fi

# Stop Qdrant
docker compose down
echo "  → Qdrant stopped"

echo "[OK] All services stopped."
