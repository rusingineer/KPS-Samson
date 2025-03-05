# -*- coding: utf-8 -*-
# {WARN}


from __future__ import division, absolute_import, print_function, unicode_literals
import ctypes
import datetime
import os
import os.path
import sys
import time


time_t = ctypes.c_long      # это но это не точно
context_p = ctypes.c_void_p # этого достаточно


def wrapString(s):
    if isinstance(s, bytes):
        return(s)
    else:
        return s.encode('utf-8')


def unwrapString(s):
    return s.decode('utf-8')


def wrapDateTime(dt):
    return int(time.mktime(dt.timetuple()))


def unwrapDateTime(ts):
    return datetime.datetime.fromtimestamp(ts)


class ClassicInterfaceWrap:
    @staticmethod
    def loadLibrary():
        fileDirName = os.path.dirname(__file__)
        if os.name == 'nt' or sys.platform == 'cygwin':
            baseNames = [ 'classic_fr_drv_ng.dll',    # для случая msvc
                          'libclassic_fr_drv_ng.dll', # для случая mingw
                        ]
            libDirs   = [ os.path.join(fileDirName, 'fr_drv_ng'),
                          fileDirName,
                          os.path.join(os.path.curdir, 'fr_drv_ng'),
                          os.path.curdir,
                          ''
                        ]
        elif os.name == 'posix':
            baseNames = [ 'libclassic_fr_drv_ng.so',
                        ]
#            bitness   = ctypes.sizeof(ctypes.c_void_p)*8
            libDirs   = [
#                          os.path.join('/', 'opt', 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join('/', 'opt', 'fr_drv_ng', 'lib'),
                          os.path.join('/', 'opt', 'fr_drv_ng'),
#                          os.path.join(fileDirName, 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join(fileDirName, 'fr_drv_ng', 'lib'),
                          os.path.join(fileDirName, 'fr_drv_ng'),
                          fileDirName,
#                          os.path.join(os.path.curdir, 'fr_drv_ng', 'lib%d' % bitness),
                          os.path.join(os.path.curdir, 'fr_drv_ng', 'lib'),
                          os.path.join(os.path.curdir, 'fr_drv_ng'),
                          os.path.curdir,
                        ]
        else:
            raise NotImplementedError('fr_drv_ng support is not implemented for this platform')

        for baseName in baseNames:
            for libDir in libDirs:
                try:
                    return ctypes.CDLL(os.path.join(libDir, baseName))
                except:
                    pass
        raise Exception('fr_drv_ng library not found in list %r'
                        % [
                            os.path.join(libDir, baseName)
                            for libDir in libDirs
                            for baseName in baseNames
                          ]
                       )


    def __init__(self):
        self.lib = lib = self.loadLibrary()
        c_classic_init_proto = ctypes.CFUNCTYPE(context_p, ctypes.c_char_p)
        c_classic_deinit_proto = ctypes.CFUNCTYPE(None, context_p)
        # {FUNC_TYPES}

        self.c_classic_init   = c_classic_init_proto(('c_classic_init', lib))
        self.c_classic_deinit = c_classic_deinit_proto(('c_classic_deinit', lib))
        # {FUNC_WRAPPERS}


classicInterfaceWrap = None


class ClassicInterface(object):

    # {ENUMS}

    def __init__(self, instance_prefix='fr_drv_ng'):
        global classicInterfaceWrap
        self.context = None
        if classicInterfaceWrap is None:
            classicInterfaceWrap = ClassicInterfaceWrap()
        self.context = classicInterfaceWrap.c_classic_init(wrapString(instance_prefix))

    def __del__(self):
        global classicInterfaceWrap
        if classicInterfaceWrap and self.context:
            classicInterfaceWrap.c_classic_deinit(self.context)
        self.context = None


    # {FUNC_IMPS}

    # {PROPS}
