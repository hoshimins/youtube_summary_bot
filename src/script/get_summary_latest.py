#!/usr/bin/env python3
"""latest → summarize を連続実行する薄いラッパー。"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _run(mode: str) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.check_call(
        [sys.executable, str(ROOT / "src" / "main.py"), mode],
        cwd=ROOT,
        env=env,
    )


if __name__ == "__main__":
    _run("latest")
    _run("summarize")
