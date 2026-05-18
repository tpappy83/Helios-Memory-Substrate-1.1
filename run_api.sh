#!/usr/bin/env bash
# Helios FastAPI runner.
# Pass --dev for hot-reload.
set -e
EXTRA=""
if [ "$1" = "--dev" ]; then
    EXTRA="--reload"
fi
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000 $EXTRA
