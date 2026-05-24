"""
Per-user data directory — single source of truth for all writable
runtime files (history CSV, source caches, config).

A packaged app (PyInstaller .app on Mac, .exe folder on Windows) lives
in a read-only location. Writing alongside the bundle would either
fail outright or end up in surprising places, so we route everything
to a per-user dir:

  • macOS:   ~/Library/Application Support/TypeHype/
  • Windows: %APPDATA%\\TypeHype\\
  • Linux:   $XDG_DATA_HOME/TypeHype/  (falls back to ~/.local/share/TypeHype/)

`migrate_legacy_data()` copies anything from a legacy in-repo `data/`
folder over on first launch so dev-mode history isn't lost when you
switch to the packaged build.
"""

import os
import shutil
import sys
from pathlib import Path

APP_NAME = "TypeHype"


def user_data_dir() -> Path:
    """Per-user, writable data directory. Created on first access."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA") or str(Path.home())) / APP_NAME
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = (Path(xdg) if xdg else Path.home() / ".local" / "share") / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base


def data_file(name: str) -> str:
    """Absolute path to a single file under the user data dir."""
    return str(user_data_dir() / name)


def migrate_legacy_data():
    """Copy files from a legacy `<repo>/data/` folder into the user
    data dir on first launch. Idempotent — only fills in files that
    don't already exist in the user data dir.

    This is purely for the dev → packaged transition. In a bundled
    app `__file__` lives inside the read-only bundle, so the legacy
    folder won't exist there and this is a no-op."""
    udd = user_data_dir()
    legacy = Path(__file__).resolve().parent / "data"
    if not legacy.is_dir():
        return
    for f in legacy.iterdir():
        if not f.is_file():
            continue
        dest = udd / f.name
        if dest.exists():
            continue
        try:
            shutil.copy2(f, dest)
        except Exception:
            pass
