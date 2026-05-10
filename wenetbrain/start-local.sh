#!/usr/bin/env bash
# WenetBrain — local startup script
# Runs main app on :8000 and admin panel on :8001

set -e

cd "$(dirname "$0")"
source .venv/bin/activate

echo "🧠 Starting WenetBrain local services..."

# Kill any existing instances
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:8001 | xargs kill -9 2>/dev/null || true
sleep 1

# Start main app
echo "  → Main app     http://localhost:8000"
python3 -m app.fast_api_app > /tmp/wenetbrain-main.log 2>&1 &
MAIN_PID=$!
echo $MAIN_PID > /tmp/wenetbrain-main.pid

# Start admin app
echo "  → Admin panel  http://localhost:8001"
PYTHONPATH="$(pwd)" python3 admin/admin_app.py > /tmp/wenetbrain-admin.log 2>&1 &
ADMIN_PID=$!
echo $ADMIN_PID > /tmp/wenetbrain-admin.pid

sleep 3

echo ""
echo "✅ Services running!"
echo ""
echo "  Main app:     http://localhost:8000"
echo "  Admin panel:  http://localhost:8001"
echo "  API docs:     http://localhost:8000/docs"
echo ""
echo "  Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping services..."; kill $MAIN_PID $ADMIN_PID 2>/dev/null; exit 0' INT
wait
