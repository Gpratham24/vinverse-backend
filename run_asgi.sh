#!/bin/bash
# Run Django with ASGI server (required for WebSocket support)
# Usage: ./run_asgi.sh

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || true

# Use daphne for ASGI (supports WebSockets)
daphne -b 0.0.0.0 -p 8000 vinverse.asgi:application

