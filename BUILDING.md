# Building & releasing

## What you ship

- **macOS:** `type hype.app` (zipped via `ditto`) — drag-to-Applications install
- **Windows:** `type hype/` folder containing `type hype.exe` and supporting DLLs — unzip and run

Both bundles include Python and Tk, so end users don't install anything.

Runtime data (history CSV, source caches, config) lives in the per-user data dir, not inside the bundle:

- macOS: `~/Library/Application Support/TypeHype/`
- Windows: `%APPDATA%\TypeHype\`

## Recommended: GitHub Actions

The `.github/workflows/build.yml` workflow builds both platforms in parallel and (on tag pushes) creates a GitHub Release with the zipped artifacts attached.

To cut a release:

```sh
git tag v0.1.0
git push origin v0.1.0
```

The workflow will:

1. Run on macos-latest and windows-latest in parallel
2. Install build deps, generate icons, run PyInstaller
3. Zip the output per platform
4. Publish a GitHub Release with both zips

You can also trigger a manual build from the Actions tab (no tag, no release — just produces downloadable artifacts).

## Local builds

For testing builds without going through Actions:

```sh
pip install -r requirements-build.txt
python scripts/generate_icon.py
pyinstaller typehype.spec --clean --noconfirm
```

Output:

- macOS: `dist/type hype.app`
- Windows: `dist/type hype/type hype.exe`

You can only build for the OS you're running. PyInstaller does not cross-compile.

## Known caveats

- Bundles are **not code-signed**. First-launch users will see:
  - macOS: "type hype can't be opened because Apple cannot check it for malicious software" — right-click → Open → Open
  - Windows: "Windows protected your PC" → More info → Run anyway
- Code signing requires paid certificates (Apple Developer $99/yr; Windows code-signing cert $100-300/yr). See the workflow for where to hook signing steps in if you decide to spring for them.
