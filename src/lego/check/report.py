"""Check results, shared by every check and serialized to JSON for Claude."""

from dataclasses import asdict, dataclass, field

from lego.dsl import Model, Placement
from lego.parts import colors


@dataclass(frozen=True)
class PartRef:
    """Identifies a part the way the DSL program placed it.

    For a part defined inside a sub-assembly, `call` is the sub-assembly call as written in the
    program (local coordinates, e.g. "leg.brick(...)"), `sub` names the sub-assembly copy and
    `sub_step` is its step inside the sub-assembly.
    """

    index: int  # 0-based position in the checked model's placements
    step: int  # 1-based step of the checked model (main model, or the sub-assembly itself)
    call: str  # e.g. "brick('2x4', x=0, y=1, z=2, color='red', rot=0)"
    sub: str | None = None  # e.g. "leg", "leg#2"
    sub_step: int | None = None  # 1-based step inside the sub-assembly

    @staticmethod
    def of(model: Model, index: int) -> PartRef:
        p = model.placements[index]
        if model.parent is not None:  # checking a sub-assembly on its own
            call = f"{model.name}.{describe(p)}"
            return PartRef(index, p.step + 1, call, model.name, p.step + 1)
        if p.sub is not None and p.sub_index is not None and p.sub_step is not None:
            attachment = next(a for a in model.attachments if a.label == p.sub)
            local = attachment.sub.placements[p.sub_index]
            call = f"{attachment.sub.name}.{describe(local)}"
            return PartRef(index, p.step + 1, call, p.sub, p.sub_step + 1)
        return PartRef(index, p.step + 1, describe(p))


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
                             "parts": [{"index": int, "step": int, "call": str,
                                        "sub": str | null, "sub_step": int | null}],
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
            for p in issue.parts:
                where = f"step {p.step}"
                if p.sub is not None:
                    where += f", {p.sub} step {p.sub_step}"
                lines.append(f"      #{p.index} ({where}) {p.call}")
    return "\n".join(lines)
