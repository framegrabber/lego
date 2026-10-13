"""`lego check`: run all checks on an LDraw file or DSL program."""

import json
from pathlib import Path

from lego import ldraw
from lego.build import load_program
from lego.check import run_all, to_json, to_text
from lego.dsl import Model


def load_model(path: Path) -> Model:
    if path.suffix == ".py":
        return load_program(path)
    if not path.is_file():
        raise ldraw.LDrawError(f"model not found: {path}")
    return ldraw.load(path)


def run(path: Path, as_json: bool) -> bool:
    """Print the report; return True if every check passed."""
    reports = run_all(load_model(path))
    print(json.dumps(to_json(reports), indent=2) if as_json else to_text(reports))
    return all(r.ok for r in reports)
