"""Run LANrage code quality tools in a consistent order.

Usage:
  python tools/run_code_quality.py
  python tools/run_code_quality.py --check
  python tools/run_code_quality.py --ruff-fix
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(name: str, cmd: list[str], cwd: Path) -> int:
    print(f"\n==> {name}")
    print(" ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        print(f"\n{name} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Run check-only mode (no formatting changes).",
    )
    parser.add_argument(
        "--ruff-fix",
        action="store_true",
        help="Run ruff with --fix (ignored when --check is used).",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    py = sys.executable

    if args.check:
        steps = [
            ("isort (check)", [py, "-m", "isort", "--check-only", "--diff", "."]),
            ("black (check)", [py, "-m", "black", "--check", "--diff", "."]),
            ("ruff (check)", [py, "-m", "ruff", "check", "."]),
        ]
    else:
        ruff_cmd = [py, "-m", "ruff", "check", "."]
        if args.ruff_fix:
            ruff_cmd.append("--fix")

        steps = [
            ("isort", [py, "-m", "isort", "."]),
            ("black", [py, "-m", "black", "."]),
            ("ruff", ruff_cmd),
        ]

    for name, cmd in steps:
        code = run_step(name, cmd, repo_root)
        if code != 0:
            return code

    print("\nAll code quality steps passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
