"""`lego` command-line entry point."""

import argparse
import sys

from lego import setup


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lego", description="Kids' LEGO designer pipeline")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="download the LDraw library and headless Chromium")

    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            setup.run()
    except setup.SetupError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
