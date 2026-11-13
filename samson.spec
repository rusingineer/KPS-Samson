# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['s11main.py'],
             pathex=['d:\\SVN\\SVN_SAMSON\\UP_s11\\client'],
             binaries=[('ru_RU.aff', '.'), ('ru_RU.dic', '.'), ('x64/libwinpthread-1.dll', '.'), ('x64/hunspell.dll', '.'), ('x64/hidapi.dll', '.')],
             datas=[('i18n', 'i18n'), ('icons', 'icons')],
             hiddenimports=['hunter'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='samson',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False , icon='icons\\s11.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='samson')
