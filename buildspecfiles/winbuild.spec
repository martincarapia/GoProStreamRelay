# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../gui.py'],  # Replace with your main script
    pathex=['../'],
    binaries=[],
    datas=[('../assets/myicon.icns', 'assets')],
    hiddenimports=['zeroconf._utils.ipaddress', 'zeroconf._handlers.answers'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GoProStreamRelay',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Ensure this is set to False for a windowed application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../assets/myicon.ico',  # Path to your icon file in .ico format
    onefile=True  # Create a single executable file
)