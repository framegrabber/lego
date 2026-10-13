"""`lego setup`: fetch the LDraw parts library and the headless browser used for rendering."""

import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

from lego.paths import LDRAW_DIR

LDRAW_URL = "https://library.ldraw.org/library/updates/complete.zip"
# Files whose presence means the library is usable.
LDRAW_MARKERS = ("parts/3001.dat", "LDConfig.ldr")


class SetupError(Exception):
    pass


def ldraw_installed(ldraw_dir: Path = LDRAW_DIR) -> bool:
    return all((ldraw_dir / marker).is_file() for marker in LDRAW_MARKERS)


def ensure_ldraw(ldraw_dir: Path = LDRAW_DIR, url: str = LDRAW_URL) -> bool:
    """Download and unpack the library unless present. Returns True if it was installed now."""
    if ldraw_installed(ldraw_dir):
        return False
    if ldraw_dir.exists():
        raise SetupError(
            f"{ldraw_dir} exists but is incomplete (missing one of {LDRAW_MARKERS}); "
            "remove it and retry"
        )
    # Stage next to the target so the final rename stays on one filesystem.
    with tempfile.TemporaryDirectory(dir=ldraw_dir.parent, prefix=".ldraw-") as tmp:
        archive = Path(tmp) / "complete.zip"
        print(f"Downloading {url} …", flush=True)
        try:
            # The server rejects urllib's default User-Agent with 403.
            request = urllib.request.Request(url, headers={"User-Agent": "lego-designer/0.1"})
            with urllib.request.urlopen(request) as response, archive.open("wb") as out:
                shutil.copyfileobj(response, out)
        except OSError as e:
            raise SetupError(f"download failed: {e}") from e
        try:
            with zipfile.ZipFile(archive) as zf:
                names = zf.namelist()
                if not names or not all(n.startswith("ldraw/") for n in names):
                    raise SetupError("unexpected archive layout: expected top-level 'ldraw/'")
                zf.extractall(tmp)
        except zipfile.BadZipFile as e:
            raise SetupError(f"downloaded file is not a valid zip: {e}") from e
        staged = Path(tmp) / "ldraw"
        if not ldraw_installed(staged):
            raise SetupError(f"archive is missing one of {LDRAW_MARKERS}")
        staged.rename(ldraw_dir)
    return True


def chromium_installed() -> bool:
    with sync_playwright() as p:
        return Path(p.chromium.executable_path).is_file()


def ensure_chromium() -> bool:
    """Install Playwright's Chromium unless present. Returns True if it was installed now."""
    if chromium_installed():
        return False
    result = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    if result.returncode != 0:
        raise SetupError(f"playwright install chromium failed (exit {result.returncode})")
    return True


def run() -> None:
    if ensure_ldraw():
        print(f"LDraw library installed in {LDRAW_DIR}")
    else:
        print(f"LDraw library already present in {LDRAW_DIR}")
    if ensure_chromium():
        print("Chromium installed")
    else:
        print("Chromium already installed")
