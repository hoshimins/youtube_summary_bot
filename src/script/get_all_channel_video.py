#!/usr/bin/env python3
"""チャンネル全動画を取得する薄いラッパー。"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src")
    subprocess.check_call(
        [sys.executable, str(ROOT / "src" / "main.py"), "all"],
        cwd=ROOT,
        env=env,
    )
