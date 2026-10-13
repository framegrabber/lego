"""Buildability checks (SPEC.md, B1–B7). Each check is a pure function `Model -> Report`."""

from collections.abc import Callable

from lego.check.basic import collisions, valid_parts
from lego.check.report import Issue, PartRef, Report, to_json, to_text
from lego.dsl import Model

CHECKS: list[Callable[[Model], Report]] = [valid_parts, collisions]


def run_all(model: Model) -> list[Report]:
    return [check(model) for check in CHECKS]


__all__ = ["CHECKS", "Issue", "PartRef", "Report", "run_all", "to_json", "to_text"]
