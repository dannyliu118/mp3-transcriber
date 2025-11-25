from setuptools import setup

APP = ['transcriber.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': True,
    'packages': ['customtkinter', 'faster_whisper', 'opencc'],
    'iconfile': 'icon.icns',
    'plist': {
        'CFBundleName': '中文轉錄工具',
        'CFBundleDisplayName': '中文轉錄工具',
        'CFBundleGetInfoString': "語音轉繁體中文字幕",
        'CFBundleIdentifier': "com.yourname.transcriber",
        'CFBundleVersion': "1.0.0",
        'CFBundleShortVersionString': "1.0.0",
        'NSHumanReadableCopyright': "Copyright © 2024",
        'NSHighResolutionCapable': True,
    }
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)