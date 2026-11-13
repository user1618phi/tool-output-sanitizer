#!/usr/bin/env bash
# Start the local sanitizer server on http://127.0.0.1:8000 with every model found in models/
cd "$(dirname "$0")/.."
exec uv run python app/server.py "$@"
