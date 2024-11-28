# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['../gui.py'],
    pathex=['../'],
    binaries=[],
    datas=[('../assets/myicon.icns', 'assets')],
    hiddenimports=['zeroconf._utils.ipaddress', 'zeroconf._handlers.answers'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Include binaries
    a.zipfiles,
    a.datas,
    [],
    name='GoProStreamRelayHelper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Ensure this is set to False
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/myicon.icns'
)

app = BUNDLE(
    exe,
    name='GoProStreamRelay.app',
    icon='../assets/myicon.icns',
    bundle_identifier=None
)
