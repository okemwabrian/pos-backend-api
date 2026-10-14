# PyInstaller one-file bundle; POS records are stored in the current user's
# LocalAppData folder, not inside the executable or its temporary extraction.

from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

ROOT = Path(SPECPATH)
apps = ("core", "users", "inventory", "crm", "sales", "purchases", "finance", "offline")
hiddenimports = []
datas = [
    (str(ROOT / "templates"), "templates"),
    (str(ROOT / "static"), "static"),
]

for app in apps:
    hiddenimports += collect_submodules(app)
    template_dir = ROOT / app / "templates"
    if template_dir.is_dir():
        datas.append((str(template_dir), f"{app}/templates"))

a = Analysis(
    [str(ROOT / "run_windows_pos.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="ChiwasLiquorPOS",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)
