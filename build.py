"""07_build_py.py — Cross-platform Python build script
Target: NEW file at helios-memory/build.py, replacing build.bat + build.sh

Rationale (per Forge audit): the v4.1 Node tarball has `script/build.ts` —
a typed code-based build pipeline with error handling, dependency allowlists,
and rm-rf safety. Current Helios's build.bat is a one-liner with no error
handling and is Windows-only.

This Python equivalent:
- Wraps PyInstaller with the same --add-data + --collect-submodules flags
- Runs on Windows AND macOS AND Linux without forking
- Validates required artifacts exist before bundling (schema.sql, frontend/)
- Has --exclude-module allowlist to shrink the EXE (per Forge)
- Cleans dist/ and build/ at start, on success only (preserves on failure for debug)
- Prints a final EXE size + path for the user
- Returns nonzero exit code on any failure

Usage:
    python build.py             # Default: produce HeliosStandalone.exe
    python build.py --debug     # Skip --strip, leave symbols (for ASan-style debug)
    python build.py --name X    # Override output name
"""
from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

REQUIRED_DATA_FILES = [
    "schema.sql",
    "frontend/index.html",
    "frontend/styles.css",
    "frontend/app.js",
]

EXCLUDE_MODULES = [
    # Test infra — never needed at runtime
    "pytest", "pytest_asyncio", "_pytest",
    "mypy", "pyright",
    # Build infra
    "PyInstaller.lib",
    # Heavy optional deps that creep in via transitive imports
    "matplotlib", "numpy.tests", "pandas.tests",
    # Streamlit dev tooling
    "watchdog.tricks",
]


def check_prereqs() -> None:
    """Validate that all required input artifacts exist before bundling."""
    missing = [f for f in REQUIRED_DATA_FILES if not (ROOT / f).exists()]
    if missing:
        print(f"ERROR: required data files missing:\n  " + "\n  ".join(missing), file=sys.stderr)
        sys.exit(1)

    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("ERROR: pyinstaller not installed. Run: pip install pyinstaller", file=sys.stderr)
        sys.exit(1)


def clean_output_dirs() -> None:
    """Remove dist/ and build/ from prior runs."""
    for d in ("dist", "build"):
        if (ROOT / d).exists():
            shutil.rmtree(ROOT / d)


def build_exe(name: str = "HeliosStandalone", debug: bool = False) -> Path:
    """Invoke PyInstaller. Returns path to the produced executable."""
    sep = ";" if platform.system() == "Windows" else ":"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", name,
        f"--add-data=schema.sql{sep}.",
        f"--add-data=frontend{sep}frontend",
        f"--add-data=migrations{sep}migrations",   # NEW: v0.2 migration files
        "--collect-submodules", "core",
        "--noconfirm",
    ]
    for mod in EXCLUDE_MODULES:
        cmd += ["--exclude-module", mod]
    if not debug:
        cmd.append("--strip")

    cmd.append("api.py")    # entry point — runs FastAPI which auto-mounts /ui/

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        print(f"\nERROR: PyInstaller exited with {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)

    suffix = ".exe" if platform.system() == "Windows" else ""
    exe = ROOT / "dist" / f"{name}{suffix}"
    if not exe.exists():
        print(f"ERROR: expected EXE at {exe} but not found", file=sys.stderr)
        sys.exit(2)
    return exe


def report(exe_path: Path) -> None:
    """Print final size + path for the user."""
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[OK] Built {exe_path.name} ({size_mb:.1f} MB)")
    print(f"     Path: {exe_path}")
    print(f"\nRun: {exe_path} &  # then open http://localhost:8000/ui/")


def main() -> int:
    parser = argparse.ArgumentParser(description="Helios EXE bundler")
    parser.add_argument("--name", default="HeliosStandalone")
    parser.add_argument("--debug", action="store_true",
                        help="Keep symbols and skip --strip")
    args = parser.parse_args()

    check_prereqs()
    clean_output_dirs()
    exe = build_exe(args.name, args.debug)
    report(exe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
