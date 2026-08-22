# Building Veronica

The app runs fine as `python3 veronica.py`. These steps produce a double-clickable build
with the icon and no terminal window.

## Both platforms

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm veronica.spec
```

| Platform | Output |
|---|---|
| Windows | `dist/Veronica/Veronica.exe` |
| macOS | `dist/Veronica.app` |
| Linux | `dist/Veronica/Veronica` |

Build on the platform you are targeting — PyInstaller does not cross-compile.

## Notes

- `assets/` is bundled by the spec, so the icon and window icons travel with the build.
- **macOS Gatekeeper**: an unsigned .app shows "cannot be opened because the developer
  cannot be verified". Right-click → Open once, or ship it signed:
  `codesign --deep --force --sign "Developer ID Application: NAME" dist/Veronica.app`.
- **Windows SmartScreen** warns on unsigned .exe the first few downloads. Expected for a
  free research tool; mention it in the release notes.
- Ollama is **not** bundled — it is a separate local service. The app degrades gracefully:
  searching, ranking, screening and Excel work without it; scoring and drafting need it.
- First launch is slow (PyInstaller unpacks); later launches are normal.
- Keep the build out of git: add `build/`, `dist/`, `*.spec.bak` to `.gitignore`.

## Release checklist

1. Bump `VERSION` in `veronica.py` and the version in `veronica.spec`.
2. Note the changes in `CHANGELOG.md`.
3. Build on Windows and macOS, launch each once, run one real search.
4. Attach both builds to the GitHub release, with `requirements.txt` and the README.
