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
from PyQt4.QtCore import QDate, SIGNAL, Qt

from Registry.ClientRelationComboBox            import CClientRelationComboBox
from Registry.ClientRelationSimpleComboBoxPopup import CClientRelationSimpleComboBoxPopup


__all__ = [ 'CClientRelationSimpleComboBox',
          ]


class CClientRelationSimpleComboBox(CClientRelationComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent = None, mainClientId = None, regAddressInfo = {}, logAddressInfo = {}):
        CClientRelationComboBox.__init__(self, parent, mainClientId, regAddressInfo, logAddressInfo)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup=None
        self.mainClientId = mainClientId
        self.clientId = None
        self.clientLowerId = None
        self.needSNILS = False
        self.regAddressInfo = regAddressInfo
        self.logAddressInfo = logAddressInfo
        self.date = QDate.currentDate()
        self.installEventFilter(self)


    def showPopup(self):
        if not self._popup:
            self._popup = CClientRelationSimpleComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('relatedClientIdSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos = self.mapToGlobal(pos)
        size = self._popup.sizeHint()
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        size.setWidth(screen.width())
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.setDate(self.date)
        self._popup.setClientLowerId(self.clientLowerId)
        self._popup.setClientRelationCode(self.clientId, self.mainClientId, self.regAddressInfo, self.logAddressInfo)
        self._popup.regAddressInfo = self.regAddressInfo
        self._popup.logAddressInfo = self.logAddressInfo
        self._popup.setClientRelationTable()
        self._popup.show()


    def setClientId(self, clientId):
        if not self.model().isReadOnly():
            self.mainClientId = clientId


    def setClientLowerId(self, clientLowerId):
        if not self.model().isReadOnly():
            self.clientLowerId = clientLowerId


    def setNeedSNILS(self, value=False):
        self.needSNILS = value


    def getNeedSNILS(self):
        return self.needSNILS


    def setValue(self, clientId):
        if not self.model().isReadOnly():
            self.clientId = clientId
            self.updateText(needSNILS=self.needSNILS)
            self.lineEdit().setCursorPosition(0)


    def keyPressEvent(self, event):
        if self.model().isReadOnly():
            event.accept()
        else:
            key = event.key()
            if key == Qt.Key_Escape:
                event.ignore()
            elif key == Qt.Key_Return or key == Qt.Key_Enter:
                event.ignore()
            if key == Qt.Key_Delete or key == Qt.Key_Backspace:
                self.setValue(None)
                event.accept()
            else:
                QtGui.QComboBox.keyPressEvent(self, event)

