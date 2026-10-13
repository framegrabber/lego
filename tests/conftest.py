import pytest

from lego.paths import LDRAW_DIR


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if (LDRAW_DIR / "LDConfig.ldr").is_file():
        return
    skip = pytest.mark.skip(reason="LDraw library missing; run `uv run lego setup`")
    for item in items:
        if "ldraw" in item.keywords:
            item.add_marker(skip)
