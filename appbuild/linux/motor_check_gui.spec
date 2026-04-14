# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec — Linux 실행파일/AppImage 빌드용.

실행 위치: appbuild/linux/ (프로젝트 루트에서 상대경로 ../../로 접근)
사용법: (appbuild/linux/ 디렉토리에서)
    pyinstaller motor_check_gui.spec
"""
import os

# 프로젝트 루트 경로 (appbuild/linux 기준 두 단계 위)
PROJECT_ROOT = os.path.abspath(os.path.join(os.getcwd(), '..', '..'))

block_cipher = None

a = Analysis(
    [os.path.join(PROJECT_ROOT, 'main.py')],
    pathex=[PROJECT_ROOT],
    binaries=[],
    datas=[
        # resource/ 안의 이미지를 번들 루트('.')로 복사
        (os.path.join(PROJECT_ROOT, 'resource', 'logo.png'), '.'),
        (os.path.join(PROJECT_ROOT, 'resource', 'icon.png'), '.'),
    ],
    hiddenimports=[
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'serial',
        'serial.tools',
        'serial.tools.list_ports',
        'st3215',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'cv2',
        'numpy',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='sts3215-motor-test',
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
