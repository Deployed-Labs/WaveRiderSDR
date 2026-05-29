"""Universal Python launcher for WaveRider SDR."""

from __future__ import annotations

import argparse
import os
import platform

from waverider_web import run_web


def detect_mode(mode: str) -> str:
    if mode in {"web", "desktop"}:
        return mode

    system = platform.system().lower()
    if system in {"windows", "darwin"}:
        return "desktop"

    if os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY"):
        return "desktop"
    return "web"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WaveRider SDR Python launcher")
    parser.add_argument("--mode", choices=["auto", "web", "desktop"], default="auto")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    selected_mode = detect_mode(args.mode)
    open_browser = selected_mode == "desktop"

    print("\n============================================================")
    print("  WAVERIDER SDR (PYTHON)")
    print("  Universal Cross-Platform Launcher")
    print("============================================================\n")
    print(f"Selected mode: {selected_mode}")

    return run_web(host=args.host, port=args.port, open_browser=open_browser)


if __name__ == "__main__":
    raise SystemExit(main())

