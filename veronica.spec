# PyInstaller spec - build a double-clickable Veronica.
#   pip install pyinstaller
#   pyinstaller --noconfirm veronica.spec
# Windows -> dist/Veronica/Veronica.exe   macOS -> dist/Veronica.app
import sys
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

a = Analysis(
    ['veronica.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets')],
    hiddenimports=collect_submodules('Bio') + ['openpyxl', 'requests'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy.distutils', 'pytest', 'tkinter.test'],
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name='Veronica',
    debug=False,
    strip=False,
    upx=True,
    console=False,                      # no terminal window
    icon='assets/veronica.ico' if sys.platform == 'win32' else 'assets/veronica.icns',
)
coll = COLLECT(
    exe, a.binaries, a.zipfiles, a.datas,
    strip=False, upx=True, name='Veronica',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='Veronica.app',
        icon='assets/veronica.icns',
        bundle_identifier='local.veronica.review',
        info_plist={
            'CFBundleShortVersionString': '5.0',
            'NSHighResolutionCapable': True,
            'LSApplicationCategoryType': 'public.app-category.education',
        },
    )
