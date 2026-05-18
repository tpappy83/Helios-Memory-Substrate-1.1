"""init_db.py — one-shot DB initializer. Called from setup scripts."""
from core.db import init_schema

if __name__ == "__main__":
    init_schema()
    print("Helios DB initialized.")
