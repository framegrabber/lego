import os
from pathlib import Path

from lego.paths import write_atomic
from lego.preview import newest_model


def _touch(path: Path, mtime_ns: int) -> None:
    path.write_text("0 x\n")
    os.utime(path, ns=(mtime_ns, mtime_ns))


def test_newest_model_picks_the_latest_mpd_or_ldr_and_ignores_other_files(tmp_path):
    _touch(tmp_path / "old.mpd", 1_000)
    _touch(tmp_path / "hand.ldr", 2_000)
    _touch(tmp_path / "new.mpd", 3_000)
    _touch(tmp_path / "new.json", 9_000)  # instruction data, not a model
    _touch(tmp_path / ".new.mpd.tmp", 9_000)  # half-written temp file
    (tmp_path / "renders").mkdir()
    assert newest_model(tmp_path) == tmp_path / "new.mpd"


def test_newest_model_is_none_in_an_empty_folder(tmp_path):
    assert newest_model(tmp_path) is None


def test_write_atomic_leaves_no_temp_file(tmp_path):
    target = tmp_path / "car.mpd"
    write_atomic(target, "first")
    write_atomic(target, "second")
    assert target.read_text() == "second"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["car.mpd"]
