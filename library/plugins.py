# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2023 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui

def hook(func):
    def _wrapper(*args, **kwargs):
        if hasattr(QtGui.qApp, '_hookList'):
            name = '%s.%s'%(args[0].__class__.__name__, func.__name__)
            hook = QtGui.qApp._hookList.get(name)
            return hook(func, *args, **kwargs) if hook else func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    return _wrapper
