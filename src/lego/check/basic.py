"""B1 valid parts and B2 collisions."""

from lego.check.report import Issue, PartRef, Report
from lego.dsl import Model
from lego.parts import colors
from lego.paths import LDRAW_DIR


def valid_parts(model: Model) -> Report:
    """B1: every part file exists in the LDraw library and every color is defined."""
    report = Report("B1", "valid parts")
    known_colors = set(colors().values())
    for i, p in enumerate(model.placements):
        if not (LDRAW_DIR / "parts" / p.part.filename).is_file():
            message = f"{p.part.filename} is missing from the LDraw library"
            report.issues.append(Issue(message, [PartRef.of(model, i)]))
        if p.color not in known_colors:
            report.issues.append(
                Issue(f"color {p.color} is not an LDraw color", [PartRef.of(model, i)])
            )
    return report


def collisions(model: Model) -> Report:
    """B2: no two parts occupy the same grid cell (1 stud × 1 stud × 1 plate)."""
    report = Report("B2", "no collisions")
    owner: dict[tuple[int, int, int], int] = {}
    first_overlap: dict[tuple[int, int], tuple[int, int, int]] = {}
    for i, p in enumerate(model.placements):
        for x, z in sorted(p.cells()):
            for y in p.levels():
                cell = (x, y, z)
                other = owner.setdefault(cell, i)
                if other != i:
                    first_overlap.setdefault((other, i), cell)
    for (a, b), cell in first_overlap.items():
        report.issues.append(
            Issue("parts overlap", [PartRef.of(model, a), PartRef.of(model, b)], cell)
        )
    return report
