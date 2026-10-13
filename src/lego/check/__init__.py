"""Buildability checks (SPEC.md, B1–B7). Each check is a pure function `Model -> Report`."""

from collections.abc import Callable

from lego.check.basic import collisions, valid_parts
from lego.check.connectivity import connected
from lego.check.report import Issue, PartRef, Report, to_json, to_text
from lego.check.steps import insertable, step_size, steps_connected
from lego.dsl import Model

CHECKS: list[Callable[[Model], Report]] = [
    valid_parts,
    collisions,
    connected,
    steps_connected,
    insertable,
    step_size,
]


def run_all(model: Model) -> list[Report]:
    return [check(model) for check in CHECKS]


__all__ = ["CHECKS", "Issue", "PartRef", "Report", "run_all", "to_json", "to_text"]
