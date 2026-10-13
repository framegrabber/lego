"""Filesystem locations shared by the CLI commands."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LDRAW_DIR = ROOT / "ldraw"
WEB_DIR = ROOT / "web"
