# Publishing Veronica

You cannot build a Windows `.exe` or a macOS `.app` from Linux — PyInstaller runs the app's
own interpreter, so each platform must be built on that platform. Two ways to get all
three:

- **GitHub Actions (recommended).** Push a tag; GitHub builds Windows, macOS and Linux on
  its own runners and attaches all three to the release. Nothing to install, no second
  machine.
- **By hand**, if you have access to a Mac and a Windows PC: run the build on each.

---

## 1 · Push the code

From the project folder:

```bash
git init                                  # skip if already a repo
git remote add origin https://github.com/paranjapepratik/Veronica.git
git add .
git commit -m "v5.0 — rewrite: five sources, local ranking, optional AI scoring, Word export"
git branch -M main
git push -u origin main --force           # --force only if overwriting the old v3 code
```

If the old repo has PyInstaller leftovers committed (a `build/` folder), drop them once:

```bash
git rm -r --cached build dist
git commit -m "Stop tracking build output"
git push
```

`.gitignore` keeps them out from now on.

## 2 · Cut a release — this is what builds all three

```bash
git tag v5.0
git push origin v5.0
```

That's it. Watch **Actions** on GitHub: three jobs (Linux, Windows, macOS) build in
parallel, take about 3–6 minutes, and a release appears under **Releases** with:

| Asset | For |
|---|---|
| `Veronica-windows.zip` | Windows 10/11 |
| `Veronica-macos.zip` | macOS |
| `Veronica-linux-x86_64.tar.gz` | Linux |

To test the workflow without releasing, use **Actions → Build → Run workflow**; it builds
and attaches the files as artifacts without creating a release.

## 3 · What users will hit

Both unsigned builds trigger an OS warning. Say so in the release notes rather than
letting people guess:

- **macOS**: "Veronica.app cannot be opened because the developer cannot be verified."
  Right-click → Open, once. Signing properly needs a paid Apple Developer account.
- **Windows**: SmartScreen "unrecognised app" → More info → Run anyway. Clears itself once
  enough people download it.
- **Ollama is not bundled** (it's a separate local service, several GB of models). The app
  works without it — searching, ranking, screening, Excel, Word, RIS all function; only AI
  scoring and Draft review need it. The release notes say this.

## Building by hand instead

On the target machine, with Python 3.10+ installed:

```bash
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm veronica.spec
```

| Platform | Output |
|---|---|
| Windows | `dist/Veronica/Veronica.exe` |
| macOS | `dist/Veronica.app` |
| Linux | `dist/Veronica/Veronica` |

## Release checklist

1. Bump `VERSION` in `veronica.py` and `CFBundleShortVersionString` in `veronica.spec`.
2. Add the changes to `CHANGELOG.md`.
3. Commit, push, tag, push the tag.
4. Download each built asset and launch it once — a build that starts is the only test that
   matters.
5. Add two screenshots (light and dark) to the README; it's the first thing visitors judge.
