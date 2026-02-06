# -*- coding: utf-8 -*-
#############################################################################
##
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
from PyQt4.QtCore import SIGNAL


__all__ = ['CClientEventsComboBox']

from PyQt4.QtCore import Qt
from Registry.ClientEventsComboBoxPopup import CClientEventsComboBoxPopup
from Registry.Utils import eventIdToText
from library.ROComboBox import CROComboBox
from library.Utils import forceString


class CClientEventsComboBox(CROComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                       )

    def __init__(self, parent=None, clientId=None):
        CROComboBox.__init__(self, parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self.clientId = clientId
        self.eventId = None
        self.mkb = None
        self.begDate = None
        self.endDate = None

    def showPopup(self):
        if not self._popup:
            self._popup = CClientEventsComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('eventIdIdSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX(max(min(pos.x(), screen.right() - size.width()), screen.left()))
        pos.setY(max(min(pos.y(), screen.bottom() - size.height()), screen.top()))
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.setClientId(self.clientId)
        self._popup.setMKB(self.mkb)
        self._popup.setBegDate(self.begDate)
        self._popup.setEndDate(self.endDate)
        self._popup.setClientEventsTable()
        self._popup.show()

    def setClientId(self, clientId):
        if not self.model().isReadOnly():
            self.clientId = clientId

    def setMKB(self, mkb):
        if not self.model().isReadOnly():
            self.mkb = mkb

    def setBegDate(self, begDate):
        if not self.model().isReadOnly():
            self.begDate = begDate

    def setEndDate(self, endDate):
        if not self.model().isReadOnly():
            self.endDate = endDate

    def setValue(self, eventId):
        self.eventId = eventId
        self.updateText()

    def clearValue(self):
        self.eventId = None
        self.clearEditText()

    def value(self):
        return self.eventId

    def updateText(self):
        self.setEditText(eventIdToText(self.eventId))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Backspace, Qt.Key_Delete):
            self.clearValue()
        CROComboBox.keyPressEvent(self, event)
