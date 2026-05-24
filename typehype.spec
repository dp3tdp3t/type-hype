# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller build spec for type hype.

Run from the repo root:
    pyinstaller typehype.spec

Outputs (per platform):
  macOS:   dist/type hype.app
  Windows: dist/type hype/type hype.exe (+ supporting files in folder)

The spec is cross-platform: same file works on both build machines.
GitHub Actions calls it as-is for the two-OS build matrix.

Runtime data (history CSV, source caches, config) writes to the
per-user data dir from paths.py, NOT inside the bundle. The bundle
itself only contains code + the two bundled data files
(python_snippets.py, wiki_titles.py) which are regular Python modules
auto-picked-up by PyInstaller's import graph.
"""

import sys
from pathlib import Path

APP_NAME = "type hype"
ICON_DIR = Path(SPECPATH) / "icon"


a = Analysis(
    ["main.py"],
    pathex=[SPECPATH],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)


# --- Windows: single-folder app with a launcher .exe ---
if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(ICON_DIR / "icon.ico"),
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

# --- macOS: .app bundle ---
elif sys.platform == "darwin":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=str(ICON_DIR / "icon.icns"),
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=str(ICON_DIR / "icon.icns"),
        bundle_identifier="com.davidpetty.typehype",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "NSHumanReadableCopyright": "© type hype",
            # We use AppleScript via osascript to bring the app to
            # the front on macOS (see _activate_self_on_macos in
            # app.py). Sandboxing is off, so no entitlement is
            # required for that call, but flagging this here so the
            # next person doesn't get confused.
            "LSApplicationCategoryType": "public.app-category.utilities",
        },
    )

# --- Linux fallback: just a folder ---
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        disable_windowed_traceback=False,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )
