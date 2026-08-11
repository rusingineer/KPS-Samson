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
from PyQt4 import QtCore, QtGui

class SafeCleanupMixin(object):
    def safeDelete(self):
        try:
            self.objectName()
        except (RuntimeError, AttributeError):
            return 
        
        if isinstance(self, QtGui.QWidget):
            try:
                self.clearFocus()
                self.hide()
            except Exception:
                pass
            
        try:
            self.blockSignals(True)
            self.disconnect()
        except Exception:
            pass
        
        QtCore.QObject.deleteLater(self)
    