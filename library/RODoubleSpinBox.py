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


class CRODoubleSpinBox(QtGui.QDoubleSpinBox):
    u"""QDoubleSpinBox с ReadOnly, not MouseWheel"""

    def __init__(self, parent):
        QtGui.QDoubleSpinBox.__init__(self, parent)
        self.readOnly = False
        self.isWheel = False        
        self.installEventFilter(self)
        
        
    def setWheel(self, value=False):
        self.isWheel = value                


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
        elif event.type() == QEvent.Wheel: # QWheelEvent
            if not self.isWheel:
                event.ignore() 
                return False                
        return QtGui.QDoubleSpinBox.event(self, event)


    def keyPressEvent(self, event):
        if self.isReadOnly():
            event.accept()
        else:
            QtGui.QDoubleSpinBox.keyPressEvent(self, event)


    def eventFilter(self, watched, event):
        if self.isReadOnly():
            event.accept()
            return False
        return QtGui.QDoubleSpinBox.eventFilter(self, watched, event)
        
