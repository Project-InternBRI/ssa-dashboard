# -*- mode: python ; coding: utf-8 -*-
import platform

os_name = platform.system()
if os_name == 'Darwin':
    icon_path = 'assets/icons/icon_app.icns'
else:
    icon_path = 'assets/icons/icon_app.ico'

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets', 'assets'), ('data', 'data'), ('ui', 'ui'), ('core', 'core')],
    hiddenimports=['pandas', 'openpyxl', 'numpy', 'PySide6.QtCharts'],
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='BRIVIEW',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path
)

if os_name == 'Darwin':
    app = BUNDLE(
        exe,
        name='BRIVIEW.app',
        icon=icon_path,
        bundle_identifier='com.bri.briview',
    )

