# -*- mode: python ; coding: utf-8 -*-
# pyinstaller transcriber.spec
import customtkinter
import os

# 取得 CustomTkinter 的路徑
ctk_path = os.path.dirname(customtkinter.__file__)

block_cipher = None

a = Analysis(
    ['transcriber.py'],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(ctk_path, 'assets'), 'customtkinter/assets'),
    ],
    hiddenimports=[
        'faster_whisper',
        'opencc',
        'customtkinter',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.filedialog',
        'tkinter.messagebox',
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
    exclude_binaries=True,
    name='中文轉錄工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='中文轉錄工具',
)

app = BUNDLE(
    coll,
    name='中文轉錄工具.app',
    bundle_identifier='com.transcriber.app',
    info_plist={
        'CFBundleName': '中文轉錄工具',
        'CFBundleDisplayName': '中文轉錄工具',
        'CFBundleGetInfoString': 'MP3 語音轉繁體中文字幕',
        'CFBundleIdentifier': 'com.transcriber.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.13.0',
    },
)