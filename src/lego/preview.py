"""Local HTTP server for the web preview (`lego preview`), also used by `lego render`."""

import threading
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from lego.paths import LDRAW_DIR, WEB_DIR

DEFAULT_PORT = 8765


class PreviewError(Exception):
    pass


class _Handler(SimpleHTTPRequestHandler):
    """Serves /web/ → web/, /ldraw/ → parts library, /model/ → the model's directory."""

    def __init__(self, *args, mounts: dict[str, Path], **kwargs):
        self.mounts = mounts
        super().__init__(*args, **kwargs)

    def translate_path(self, path: str) -> str:
        path = unquote(urlsplit(path).path)
        for prefix, root in self.mounts.items():
            if path.startswith(prefix):
                target = (root / path[len(prefix) :]).resolve()
                # Refuse anything that escapes the mount (e.g. "..").
                if target == root or root in target.parents:
                    return str(target)
        return str(WEB_DIR / "__not_found__")

    def end_headers(self) -> None:
        # The model file changes between builds; never let the browser cache it.
        if self.path.startswith("/model/"):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        # LDrawLoader probes several folders per part; the resulting 404s are expected noise.
        pass


def _check_inputs(model: Path) -> None:
    if not model.is_file():
        raise PreviewError(f"model not found: {model}")
    if not (LDRAW_DIR / "LDConfig.ldr").is_file():
        raise PreviewError("LDraw library missing; run `lego setup`")


@contextmanager
def serve(model: Path, port: int = 0) -> Generator[str]:
    """Serve the preview for `model` in a background thread; yields the page URL."""
    model = model.resolve()
    _check_inputs(model)
    mounts = {
        "/web/": WEB_DIR.resolve(),
        "/ldraw/": LDRAW_DIR.resolve(),
        "/model/": model.parent,
    }
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), partial(_Handler, mounts=mounts))
    except OSError as e:
        raise PreviewError(f"cannot listen on port {port}: {e}") from e
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, bound_port = server.server_address[:2]
        yield f"http://{host}:{bound_port}/web/index.html?model=/model/{quote(model.name)}"
    finally:
        server.shutdown()
        server.server_close()


def run(model: Path, port: int = DEFAULT_PORT) -> None:
    with serve(model, port) as url:
        print(f"Preview: {url}")
        print("Press Ctrl+C to stop.", flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
