# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['bm-time.py'],
    pathex=[],
    binaries=[
        ('C:\\Python39\\DLLs\\libcrypto-1_1.dll', '.'),
        ('C:\\Python39\\DLLs\\libssl-1_1.dll', '.'),
    ],
    datas=[],
    hiddenimports=[
        'selenium.webdriver',
        'selenium.webdriver.chrome',
        'selenium.webdriver.common',
        'ssl',
    ],
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
    [],
    exclude_binaries=True,
    name='bm-time',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='bm-time',
)
