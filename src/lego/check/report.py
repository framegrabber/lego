"""Check results, shared by every check and serialized to JSON for Claude."""

from dataclasses import asdict, dataclass, field

from lego.dsl import Model, Placement
from lego.parts import colors


@dataclass(frozen=True)
class PartRef:
    """Identifies a part the way the DSL program placed it."""

    index: int  # 0-based position in model.placements (= order of DSL calls)
    step: int  # 1-based
    call: str  # e.g. "brick('2x4', x=0, y=1, z=2, color='red', rot=0)"

    @staticmethod
    def of(model: Model, index: int) -> PartRef:
        return PartRef(index, model.placements[index].step + 1, describe(model.placements[index]))


@dataclass(frozen=True)
class Issue:
    message: str
    parts: list[PartRef]
    at: tuple[int, int, int] | None = None  # grid cell (x, y, z) where the problem is


@dataclass
class Report:
    check: str  # "B1" … "B7"
    name: str
    issues: list[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def describe(p: Placement) -> str:
    names = {code: name for name, code in colors().items()}
    color = names.get(p.color, p.color)
    return (
        f"{p.part.kind}({p.part.size!r}, x={p.x}, y={p.y}, z={p.z}, color={color!r}, rot={p.rot})"
    )


def to_json(reports: list[Report]) -> dict:
    """Stable JSON shape:

    {"ok": bool,
     "checks": [{"check": "B2", "name": "no collisions", "ok": false,
                 "issues": [{"message": str,
                             "parts": [{"index": int, "step": int, "call": str}],
                             "at": [x, y, z] | null}]}]}
    """
    return {
        "ok": all(r.ok for r in reports),
        "checks": [
            {"check": r.check, "name": r.name, "ok": r.ok, "issues": [asdict(i) for i in r.issues]}
            for r in reports
        ],
    }


def to_text(reports: list[Report]) -> str:
    lines = []
    for r in reports:
        lines.append(f"{r.check} {r.name}: {'ok' if r.ok else 'FAIL'}")
        for issue in r.issues:
            at = f" at {issue.at}" if issue.at else ""
            lines.append(f"  - {issue.message}{at}")
            lines += [f"      #{p.index} (step {p.step}) {p.call}" for p in issue.parts]
    return "\n".join(lines)
