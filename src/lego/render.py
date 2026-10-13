"""`lego render`: PNG screenshots of the web preview from fixed camera angles."""

from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import ViewportSize, sync_playwright

from lego import preview

VIEWS = ("front", "side", "top", "iso")
VIEWPORT: ViewportSize = {"width": 1024, "height": 768}
LOAD_TIMEOUT_MS = 60_000


class RenderError(Exception):
    pass


def render(model: Path, out_dir: Path, step: int | None = None) -> tuple[list[Path], str]:
    """Render all VIEWS of `model` (optionally at instruction `step`) into `out_dir`.

    Returns the written files and the step caption (e.g. "Step 3 / 12 · Build the leg (1/2)").
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"-step{step}" if step is not None else ""
    written: list[Path] = []
    caption = ""
    with preview.serve(model) as url, sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except PlaywrightError as e:
            raise RenderError(f"cannot start Chromium ({e}); run `lego setup`") from e
        try:
            page = browser.new_page(viewport=VIEWPORT)
            for view in VIEWS:
                query = f"&view={view}" + (f"&step={step}" if step is not None else "")
                page.goto(url + query)
                try:
                    page.wait_for_function(
                        "window.legoReady || window.legoError", timeout=LOAD_TIMEOUT_MS
                    )
                except PlaywrightError as e:
                    raise RenderError(f"{view}: page did not finish loading: {e}") from e
                error = page.evaluate("window.legoError")
                if error:
                    raise RenderError(f"{view}: {error}")
                caption = page.evaluate("window.legoStep")
                target = out_dir / f"{model.stem}-{view}{suffix}.png"
                page.screenshot(path=str(target))
                written.append(target)
        finally:
            browser.close()
    return written, caption


def run(model: Path, out_dir: Path, step: int | None) -> None:
    paths, caption = render(model, out_dir, step)
    for path in paths:
        print(path)
    print(caption)
