"""Local HTTP server for `lego preview` and `lego live`; also used by `lego render`."""

import json
import threading
import webbrowser
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from lego.paths import LDRAW_DIR, ROOT, WEB_DIR

DEFAULT_PORT = 8765


class PreviewError(Exception):
    pass


def newest_model(directory: Path) -> Path | None:
    """The most recently written .mpd/.ldr file directly in `directory`, if any."""
    models = [p for p in directory.glob("*") if p.suffix in (".mpd", ".ldr") and p.is_file()]
    return max(models, key=lambda p: p.stat().st_mtime_ns, default=None)


class _Handler(SimpleHTTPRequestHandler):
    """Serves /web/ → web/, /ldraw/ → parts library, /model/ → the model directory, and in live
    mode /live → {"model": "<newest file>", "version": <mtime>} for the page to poll."""

    def __init__(self, *args, mounts: dict[str, Path], live_dir: Path | None, **kwargs):
        self.mounts = mounts
        self.live_dir = live_dir
        super().__init__(*args, **kwargs)

    def do_GET(self) -> None:
        if self.live_dir is not None and urlsplit(self.path).path == "/live":
            newest = newest_model(self.live_dir)
            version = None
            if newest is not None:
                files = [newest, newest.with_suffix(".json")]
                version = max(p.stat().st_mtime_ns for p in files if p.is_file())
            body = json.dumps({"model": newest and newest.name, "version": version}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

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


@contextmanager
def _server(model_dir: Path, port: int, live: bool) -> Generator[str]:
    """Run the server in a background thread; yields its base URL."""
    if not (LDRAW_DIR / "LDConfig.ldr").is_file():
        raise PreviewError("LDraw library missing; run `lego setup`")
    mounts = {"/web/": WEB_DIR.resolve(), "/ldraw/": LDRAW_DIR.resolve(), "/model/": model_dir}
    handler = partial(_Handler, mounts=mounts, live_dir=model_dir if live else None)
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    except OSError as e:
        raise PreviewError(f"cannot listen on port {port}: {e}") from e
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, bound_port = server.server_address[:2]
        yield f"http://{host}:{bound_port}"
    finally:
        server.shutdown()
        server.server_close()


@contextmanager
def serve(model: Path, port: int = 0) -> Generator[str]:
    """Serve the preview for `model` in a background thread; yields the page URL."""
    model = model.resolve()
    if not model.is_file():
        raise PreviewError(f"model not found: {model}")
    with _server(model.parent, port, live=False) as base:
        yield f"{base}/web/index.html?model=/model/{quote(model.name)}"


def _wait_forever() -> None:
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


def run(model: Path, port: int = DEFAULT_PORT) -> None:
    with serve(model, port) as url:
        print(f"Preview: {url}")
        print("Press Ctrl+C to stop.", flush=True)
        _wait_forever()


def run_live(
    directory: Path | None = None, port: int = DEFAULT_PORT, open_browser: bool = True
) -> None:
    """Show whatever model was built last in `directory` (default out/); the page reloads after
    every build."""
    directory = (directory or ROOT / "out").resolve()
    directory.mkdir(parents=True, exist_ok=True)
    with _server(directory, port, live=True) as base:
        url = f"{base}/web/index.html?live=1"
        print(f"Live preview: {url}")
        print(f"Shows the newest model in {directory}; updates after every `lego build`.")
        print("Press Ctrl+C to stop.", flush=True)
        if open_browser:
            webbrowser.open(url)
        _wait_forever()
