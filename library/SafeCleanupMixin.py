# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2026 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################
from PyQt4 import QtGui

class SafeCleanupMixin(object):
    def safeDelete(self):
        try:
            self.objectName()
        except RuntimeError:
            return 

        self._deepSilence(self)

        attrs = list(self.__dict__.keys())
        for attr in attrs:
            if not attr.startswith('__'):
                try:
                    setattr(self, attr, None)
                except:
                    pass

        QtGui.QDialog.deleteLater(self)

    def _deepSilence(self, obj):
        if obj is None:
            return

        if hasattr(obj, 'children'):
            for child in obj.children():
                self._deepSilence(child)

        try:
            obj.blockSignals(True)
            obj.disconnect()
        except (RuntimeError, TypeError):
            pass