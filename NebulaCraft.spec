# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['server/desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('index.html', '.'),
        ('js', 'js'),
        ('css', 'css'),
        ('locales', 'locales'),
        ('static', 'static'),
        ('server', 'server'),
        ('data', 'data'),
        ('manifest.json', '.'),
        ('sw.js', '.'),
        ('favicon.ico', '.'),
    ],
    hiddenimports=[
        'server',
        'server.handler',
        'server.config',
        'server.main',
        'server.routes',
        'server.routes.*',
        'server.services',
        'server.services.*',
        'server.services.watcher',
        'server.utils',
        'server.utils.*',
        'PIL',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'jupyter',
        'torch',
        'torchvision',
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='NebulaCraft',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico' if Path('favicon.ico').exists() else None,
)