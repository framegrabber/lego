"""`lego build`: run a DSL program and write its model as LDraw."""

import runpy
import traceback
from pathlib import Path

from lego import ldraw
from lego.dsl import DesignError, Model
from lego.paths import ROOT


class BuildError(Exception):
    pass


def load_program(program: Path) -> Model:
    """Run `program`, which must create exactly one module-level `Model`, and return it."""
    if not program.is_file():
        raise BuildError(f"program not found: {program}")
    # DesignError gets the program's line number attached; other exceptions propagate with
    # their traceback, which already points at the offending line.
    try:
        namespace = runpy.run_path(str(program), run_name="__lego_build__")
    except DesignError as e:
        frames = traceback.extract_tb(e.__traceback__)
        line = next(
            (f.lineno for f in reversed(frames) if Path(f.filename).resolve() == program.resolve()),
            None,
        )
        raise BuildError(f"{program}:{line}: {e}") from e
    models = [v for v in namespace.values() if isinstance(v, Model)]
    if len(models) != 1:
        raise BuildError(
            f"{program}: expected exactly one module-level Model, found {len(models)}"
        )
    model = models[0]
    if model.num_steps == 0:
        raise BuildError(f"{program}: model has no steps")
    return model


def build(program: Path, out: Path | None = None) -> tuple[Model, Path]:
    """Run `program` and save its model to `out` (default: out/<program>.mpd)."""
    model = load_program(program)
    target = out or ROOT / "out" / f"{program.stem}.mpd"
    ldraw.save(model, target)
    return model, target


def run(program: Path, out: Path | None) -> None:
    model, target = build(program, out)
    print(f"{target}: {len(model.placements)} parts, {model.num_steps} steps")
