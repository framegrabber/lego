"""`lego` command-line entry point."""

import argparse
import sys
from pathlib import Path

from lego import build, preview, render, setup
from lego.dsl import DesignError
from lego.ldraw import LDrawError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lego", description="Kids' LEGO designer pipeline")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("setup", help="download the LDraw library and headless Chromium")
    p_build = commands.add_parser("build", help="run a DSL program and write LDraw")
    p_build.add_argument("program", type=Path, help="Python file using lego.dsl")
    p_build.add_argument("-o", "--out", type=Path, help="output .mpd (default: out/<name>.mpd)")
    p_preview = commands.add_parser("preview", help="serve the web preview for a model")
    p_preview.add_argument("model", type=Path, help=".ldr or .mpd file")
    p_preview.add_argument("--port", type=int, default=preview.DEFAULT_PORT)
    p_render = commands.add_parser("render", help="render PNGs from fixed camera angles")
    p_render.add_argument("model", type=Path, help=".ldr or .mpd file")
    p_render.add_argument("-o", "--out", type=Path, required=True, help="output directory")
    p_render.add_argument("--step", type=int, help="render only up to this 1-based step")

    args = parser.parse_args(argv)
    try:
        if args.command == "setup":
            setup.run()
        elif args.command == "build":
            build.run(args.program, args.out)
        elif args.command == "preview":
            preview.run(args.model, args.port)
        elif args.command == "render":
            render.run(args.model, args.out, args.step)
    except (
        setup.SetupError,
        build.BuildError,
        DesignError,
        LDrawError,
        preview.PreviewError,
        render.RenderError,
    ) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1
    return 0
