#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

echo "[INFO] WenetBrain — starting services..."

# Start Qdrant
echo "  → Starting Qdrant (Docker)..."
docker compose up -d

# Wait for Qdrant
sleep 2

# Initialize collections and DB if not exists
echo "  → Initializing Qdrant collections..."
uv run python scripts/init_qdrant.py

echo "  → Initializing SQLite database..."
uv run python scripts/init_db.py

# Start FastAPI + ADK server
echo "  → Starting ADK FastAPI server on http://localhost:8000"
uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!
echo $SERVER_PID > .server.pid

echo ""
echo "[OK] WenetBrain is running!"
echo "   API:       http://localhost:8000"
echo "   Docs:      http://localhost:8000/docs"
echo "   A2A RPC:   http://localhost:8000/a2a/wenetbrain"
echo "   Qdrant:    http://localhost:6333/dashboard"
echo ""
echo "   Stop with: ./scripts/stop.sh"
