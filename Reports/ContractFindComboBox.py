# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2017 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

import email.utils
from PyQt4                     import QtGui
from PyQt4.QtCore              import QModelIndex, SIGNAL

from Reports.ContractFindComboBoxPopup import CIndependentContractFindComboBoxPopup
from library.Utils             import forceString


from Accounting.Utils          import CContractFindTreeModel
from library.TreeComboBox      import CTreeComboBox

class CIndependentContractTreeFindComboBox(CTreeComboBox):
    def __init__(self, parent, filter={}):
        CTreeComboBox.__init__(self, parent)
        self.parent = parent
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self._model = CContractFindTreeModel(self)
        self.setModel(self._model)
        self.preferredWidth = 0
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self._prevValue = None
        self.contractId = None
        self.filter = filter
        self.mainDialog = None


    def showPopup(self):
        if not self._popup:
            self._popup = CIndependentContractFindComboBoxPopup(self, self.filter)
            self.connect(self._popup, SIGNAL('ContractFindCodeSelected(int)'), self.setValue)
        else:
            self._popup.on_buttonBox_apply()
        pos = self.rect().bottomLeft()
        pos2 = self.rect().topLeft()
        pos = self.mapToGlobal(pos)
        pos2 = self.mapToGlobal(pos2)
        size = self._popup.sizeHint()
        width = max(size.width(), self.width())

        size.setWidth(width)
        screen = QtGui.QApplication.desktop().availableGeometry(pos)
        pos.setX( max(min(pos.x(), screen.right()-size.width()), screen.left()) )
        pos.setY( max(min(pos.y(), screen.bottom()-size.height()), screen.top()) )
        self._popup.move(pos)
        self._popup.resize(size)
        self._popup.show()


    def setPreferredWidth(self, preferredWidth):
        self.preferredWidth = preferredWidth


    def getPath(self):
        index = self.currentModelIndex()
        if index and index.isValid():
            item = index.internalPointer()
            parts = []
            while item:
                parts.append(email.utils.quote(item.name))
                item = item.parent
            return '\\'.join(parts[::-1])


    def setPath(self, path):
        names = [u'Все договоры']
        names2 = [email.utils.unquote(part) for part in path.split('\\')][1:]
        for name in names2:
           names.append(name)
        item = self._model.getRootItem()
        for name in names:
            nextItem = item.mapNameToItem.get(name, None)
            if nextItem:
                item = nextItem
            else:
                break
        index = self._model.createIndex(item.row(), 0, item)
        self.setCurrentModelIndex(index)


    def getPathById(self, contractId):
        path = self._model.getPathById(contractId)
        return '\\'.join(path)


    def getIdByPath(self, path):
        return self._model.getIdByPath(path)


    def getIdList(self):
        index = self.currentModelIndex()
        item = index.internalPointer()
        return item.idList


    def setValue(self, value):
        self.contractId = value
        self.setPath(self.getPathById(value))


    def value(self):
        return self.contractId


    def setDate(self, date):
        self.filter['setDate'] = date
        self._model.reset()


    def setOrgId(self, orgId):
        self.filter['orgId'] = orgId
        self._model.reset()


    def setFilter(self, filter):
        self.filter = filter
