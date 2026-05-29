"""Desktop launcher for the Python WaveRider SDR GUI."""

from __future__ import annotations

import argparse

from waverider_web import run_web


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WaveRider SDR Python desktop mode")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    return run_web(host=args.host, port=args.port, open_browser=True)


if __name__ == "__main__":
    raise SystemExit(main())

