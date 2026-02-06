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
from PyQt4.QtCore import QDate, SIGNAL

from Registry.ClientRelationComboBoxPopup import CClientRelationComboBoxPopup
from Registry.Utils import clientIdToText
from library.ROComboBox import CROComboBox


__all__ = [ 'CClientRelationComboBox',
          ]


class CClientRelationComboBox(CROComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )

    def __init__(self, parent = None, mainClientId = None, regAddressInfo = {}, logAddressInfo = {}, defaultAddressInfo = None):
        CROComboBox.__init__(self, parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup=None
        self.mainClientId = mainClientId
        self.clientId = None
        self.regAddressInfo = regAddressInfo
        self.logAddressInfo = logAddressInfo
        self.defaultAddressInfo = defaultAddressInfo
        self.date = QDate.currentDate()
        self.sex = None


    def showPopup(self, parent = None):
        if parent:
            self.sex = parent.sex
        if not self._popup:
            self._popup = CClientRelationComboBoxPopup(self)
            self.connect(self._popup, SIGNAL('relatedClientIdSelected(int)'), self.setValue)
        pos = self.rect().bottomLeft()
        pos2 = self.rect().topLeft()
        pos = self.mapToGlobal(pos)
        pos2 = self.mapToGlobal(pos2)
        size = self._popup.sizeHint()
        width= max(size.width(), self.width())
        size.setWidth(width)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()
        self._popup.setDate(self.date)
        self._popup.setClientRelationCode(self.clientId, self.mainClientId, self.regAddressInfo, self.logAddressInfo)
        self._popup.regAddressInfo = self.regAddressInfo
        self._popup.logAddressInfo = self.logAddressInfo
        self._popup.defaultAddressInfo = self.defaultAddressInfo


    def setDate(self, date):
        self.date = date


    def setValue(self, clientId):
        self.clientId = clientId
        self.updateText()


    def value(self):
        return self.clientId


    def updateText(self, needSNILS=False):
        self.setEditText(clientIdToText(self.clientId, needSNILS=needSNILS))
