# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2025 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui
from PyQt4.QtCore import QEvent


class CROCheckBox(QtGui.QCheckBox):
    u"""CheckBox с ReadOnly"""

    def __init__(self, parent):
        QtGui.QCheckBox.__init__(self, parent)
        self.readOnly = True
        self.installEventFilter(self)


    def setReadOnly(self, value=False):
        self.readOnly = value


    def isReadOnly(self):
        return self.readOnly


    def event(self, event):
        if event.type() in (QEvent.KeyPress, QEvent.MouseButtonPress,
                            QEvent.MouseButtonRelease, QEvent.MouseMove,
                            QEvent.MouseMove, QEvent.MouseTrackingChange,
                            QEvent.MouseButtonDblClick):
            if self.isReadOnly():
                event.accept()
                return False
        return QtGui.QCheckBox.event(self, event)


    def keyPressEvent(self, event):
        if self.isReadOnly():
            event.accept()
        else:
            QtGui.QCheckBox.keyPressEvent(self, event)


    def eventFilter(self, watched, event):
        if self.isReadOnly():
            event.accept()
            return False
        return QtGui.QCheckBox.eventFilter(self, watched, event)

