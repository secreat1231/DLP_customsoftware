# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main_ui.py'],
    pathex=[],
    binaries=[('cheetah.dll', '.')],
    datas=[
        ('test (2).ui', '.'),
        ('EngineeringWindow (3).ui', '.'),
        ('ShortAxisFlip.png', '.'),
        ('LongAxisFlip.png', '.'),
        ('customers', 'customers'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DLP_Controller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
