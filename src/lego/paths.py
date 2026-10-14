"""Filesystem locations shared by the CLI commands."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LDRAW_DIR = ROOT / "ldraw"
WEB_DIR = ROOT / "web"


def write_atomic(path: Path, text: str) -> None:
    """Write via a hidden temp file and rename, so readers (the live preview) never see a
    half-written file. The temp name doesn't end in .mpd, so it is never taken for a model."""
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text)
    tmp.replace(path)
