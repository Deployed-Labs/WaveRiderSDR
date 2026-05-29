"""Simple Python build helper for WaveRider SDR."""

from __future__ import annotations

import subprocess
import sys


def main() -> int:
    return subprocess.call(
        [
            sys.executable,
            "-m",
            "py_compile",
            "run.py",
            "waverider_common.py",
            "waverider_web.py",
            "waverider_sdr.py",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())

