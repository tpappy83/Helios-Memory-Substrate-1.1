@echo off
REM Helios FastAPI runner. Pass --dev for hot-reload.
if "%1"=="--dev" (
    python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn api:app --host 0.0.0.0 --port 8000
)
