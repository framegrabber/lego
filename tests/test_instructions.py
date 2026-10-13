import pytest

from lego import ldraw
from lego.dsl import Model
from lego.instructions import instruction_steps, instructions, object_paths

pytestmark = pytest.mark.ldraw


def _model() -> Model:
    m = Model("bot")
    leg = m.subassembly("leg")
    with leg.step():
        leg.brick("2x2", x=0, z=0, y=0, color="black")
    with leg.step():
        leg.brick("2x2", x=0, z=0, y=3, color="blue")
    arm = m.subassembly("arm")
    with arm.step():
        arm.brick("1x2", x=0, z=0, y=0, color="red")
    with m.step():
        m.plate("2x4", x=0, z=0, y=6, color="white")
        m.plate("2x4", x=0, z=2, y=6, color="white")
    with m.step():
        m.attach(leg, x=0, y=0, z=0)
        m.plate("1x1", x=3, z=0, y=7, color="white")  # own part between two attachments
        m.attach(leg, x=2, y=0, z=0)
    with m.step():
        m.attach(arm, x=4, y=6, z=0)
    return m


def test_object_paths_point_at_the_matching_ldraw_lines():
    """The preview finds parts by line position; paths must match what dumps() writes."""
    m = _model()
    sections = ldraw.dumps(m).split("0 NOFILE")
    main_lines = [line for line in sections[0].splitlines() if line.startswith("1 ")]
    sub_lines = {
        section.split()[2]: [line for line in section.splitlines() if line.startswith("1 ")]
        for section in sections[1:]
        if "0 FILE" in section
    }
    for i, path in object_paths(m).items():
        p = m.placements[i]
        line = main_lines[path[0]]
        if len(path) == 1:
            assert line == ldraw._line(p)
        else:
            sub_file = line.split()[-1]
            local = next(a.sub for a in m.attachments if a.label == p.sub).placements[path[1]]
            assert sub_lines[sub_file][path[1]] == ldraw._line(local)


def test_instruction_steps_count_each_sub_assembly_once_per_attaching_step():
    # 3 main steps + leg (2 steps, shown once for both copies) + arm (1 step)
    assert instruction_steps(_model()) == 6


def test_step_parts_and_attachments():
    data = instructions(_model())
    assert data["main"][1] == {
        "parts": [{"count": 1, "part": "1x1 plate", "color": "white"}],
        "attach": [{"count": 2, "name": "leg"}],
    }
    assert data["subs"]["bot__leg.ldr"][1]["parts"] == [
        {"count": 1, "part": "2x2 brick", "color": "blue"}
    ]
