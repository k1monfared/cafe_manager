# PyInstaller spec file for Cafe Manager
# -*- mode: python ; coding: utf-8 -*-
#
# Build:  pyinstaller cafe_manager.spec
# Output: dist\CafeManager\   (the entire folder is what you distribute)
#
# --onedir is used (not --onefile) because the app writes CSV files back
# to the data/ directory at runtime.  --onefile extracts to a read-only
# temp folder, which would silently break uploads and recalculations.

block_cipher = None

a = Analysis(
    ['simple_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('data', 'data'),
    ],
    hiddenimports=[
        'pandas',
        'pandas.io.parsers',
        'flask',
        'jinja2',
        'werkzeug',
        'webbrowser',
        'threading',
        'inventory_engine',
        'audit_inventory'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name='CafeManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CafeManager'
)