# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['appendix\\regional\\r23\\importReestr\\importReestr.py'],
             pathex=['appendix\\regional\\r23\\importReestr', 'd:\\SVN\\SVN_SAMSON\\UP_s11\\client'],
             binaries=[],
             datas=[('i18n', 'i18n')],
             hiddenimports=[],
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
          name='importReestr23',
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
               name='importReestr23')
