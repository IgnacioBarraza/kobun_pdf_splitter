#!/usr/bin/env python3
"""
Builds the Kobun executable for the system it runs on.

    ./.venv/bin/python scripts/build_app.py
    ./.venv/bin/python scripts/build_app.py --onedir

PyInstaller **does not cross-compile**: the Windows .exe has to be produced on
Windows and the Linux binary on Linux. This script is the same on both; what
changes is where it runs.

Requires the build extra:

    pip install -e .[build]
"""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "packaging" / "kobun.spec"
OUTPUT_DIR = ROOT / "dist"
WORK_DIR = ROOT / "build"

BINARY_NAME = "kobun.exe" if sys.platform.startswith("win") else "kobun"


def check_environment() -> None:
    if not SPEC.is_file():
        raise SystemExit(f"Recipe not found: {SPEC}")

    if shutil.which("pyinstaller") is None and not _pyinstaller_importable():
        raise SystemExit(
            "PyInstaller is not installed.\n"
            "Install it with:  pip install -e .[build]"
        )


def _pyinstaller_importable() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return False

    return True


def build(onedir: bool, clean: bool) -> Path:
    if clean:
        for directory in (OUTPUT_DIR, WORK_DIR):
            if directory.exists():
                shutil.rmtree(directory)
                print(f"  cleaned {directory.relative_to(ROOT)}/")

    command = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--distpath", str(OUTPUT_DIR),
        "--workpath", str(WORK_DIR),
        "--noconfirm",
        "--log-level", "WARN",
    ]

    # The --onedir flag never reaches a .spec file: the recipe reads the mode
    # from the environment. Passing it as a flag did nothing.
    environment = dict(os.environ, KOBUN_ONEFILE="0" if onedir else "1")

    print(f"\nBuilding for {sys.platform} ({'directory' if onedir else 'single file'})...")
    start = time.monotonic()
    result = subprocess.run(command, cwd=ROOT, env=environment)
    elapsed = time.monotonic() - start

    if result.returncode != 0:
        raise SystemExit(f"\nThe build failed (exit code {result.returncode}).")

    print(f"Finished in {elapsed:.0f}s")

    return OUTPUT_DIR / BINARY_NAME


def report(binary: Path) -> None:
    if binary.is_file():
        mb = binary.stat().st_size / 1024 / 1024
        print(f"\nExecutable: {binary}  ({mb:.0f} MB)")
    elif binary.parent.is_dir():
        total = sum(f.stat().st_size for f in binary.parent.rglob("*") if f.is_file())
        print(f"\nDirectory: {binary.parent}  ({total / 1024 / 1024:.0f} MB)")
    else:
        raise SystemExit(f"\nExpected output not found at {binary}")

    print(
        "\nRun it before distributing it: an executable can build without errors "
        "and still fail at startup because of a Qt module excluded too eagerly."
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--onedir", action="store_true",
        help="Produce a directory instead of a single file (starts faster)",
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="Do not delete dist/ and build/ before building",
    )
    args = parser.parse_args()

    check_environment()
    report(build(onedir=args.onedir, clean=not args.keep))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
