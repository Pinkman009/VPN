# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('v2rayN/v2rayN-windows-64/bin/Xray/geosite.dat', '.'), ('v2rayN/v2rayN-windows-64/bin/Xray/geoip.dat', '.')]
binaries = [
    ('v2rayN/v2rayN-windows-64/bin/Xray/xray.exe', '.'),
    ('C:/Python314/vcruntime140.dll', '.'),
    ('C:/Python314/vcruntime140_1.dll', '.'),
    ('C:/Windows/System32/msvcp140.dll', '.')
]
hiddenimports = ['vpn_updater', 'vpn_core', 'vpn_speedtest']
tmp_ret = collect_all('customtkinter')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pystray')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('qrcode')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

a = Analysis(
    ['vpn_app.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='Unblocknet',
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
