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

from library.Utils             import forceString

from OrgComboBox               import CContractDbData, CContractDbModel

from Accounting.Utils          import CContractFindTreeModel
from library.TreeComboBox      import CTreeComboBox
from ContractFindComboBoxPopup import CContractFindComboBoxPopup
from Reports.ContractFindComboBox import CIndependentContractTreeFindComboBox

class CContractClientDbModel(CContractDbModel):

    def __init__(self, parent):
        CContractDbModel.__init__(self, parent)


    def initDbData(self):
        self.dbdata = CContractDbData()
        if self.orgId:
            self.dbdata.select(self)


class CContractFindComboBox(QtGui.QComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent):
        QtGui.QComboBox.__init__(self, parent)
        self.SizeAdjustPolicy(QtGui.QComboBox.AdjustToMinimumContentsLength)
        self.setModelColumn(0)
        self._model = CContractClientDbModel(self)
        self.setModel(self._model)
        self.preferredWidth = 0
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self._popup = None
        self._prevValue = None


    def showPopup(self):
        if not self._popup:
            self._popup = CContractFindComboBoxPopup(self)
            self.connect(self._popup,SIGNAL('ContractFindCodeSelected(int)'), self.setValue)
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


    def setPreferredWidth(self, preferredWidth):
        self.preferredWidth = preferredWidth


    def setCurrentIndex(self, index):
        if not index:
            index = QModelIndex()
        if index:
            QtGui.QComboBox.setCurrentIndex(self, index.row())


    def getWeakValue(self):
        if self._model.dbdata:
            return self.value()
        else:
            return None


    def setCurrentIfOnlyOne(self):
        n = self._model.rowCount()
        if n == 1:
            self.setCurrentIndex(0)
        elif n > 1 and self._model.onlyOneWithSameFinance(0):
            self.setCurrentIndex(0)
        else:
            self.setCurrentIndex(-1)


    def setOrgId(self, orgId):
        self._model.setOrgId(orgId)


    def setClientInfo(self, clientId, sex, age, orgId, policyInfoList):
        self._model.setClientInfo(clientId, sex, age, orgId, policyInfoList)


    def setFinanceId(self, financeId):
        self._model.setFinanceId(financeId)


    def setEventTypeId(self, eventTypeId):
        self._model.setEventTypeId(eventTypeId)


    def setActionTypeId(self, actionTypeId):
        self._model.setActionTypeId(actionTypeId)


    def setBegDate(self, begDate):
        self._model.setBegDate(begDate)
        self.setCurrentIfOnlyOne()
        self.conditionalEmitValueChanged()


    def setEndDate(self, endDate):
        self._model.setEndDate(endDate)
        self.setCurrentIfOnlyOne()
        self.conditionalEmitValueChanged()


    def setDate(self, date):
        self._model.setBegDate(date)
        self._model.setEndDate(date)
        if self._prevValue is not None:
            self.setValue(self._prevValue)
        if self.getWeakValue() is None:
            self.setCurrentIfOnlyOne()


    def conditionalEmitValueChanged(self):
        value = self.getWeakValue()
        if self._prevValue != value:
            self._prevValue = value
            self.emit(SIGNAL('valueChanged()'))


    def getContractIdByFinance(self, financeCode):
        return self._model.getContractIdByFinance(financeCode)


    def setValue(self, itemId):
        rowIndex = self._model.searchId(itemId)
        self.setCurrentIndex(rowIndex)


    def value(self):
        rowIndex = self.currentIndex()
        return self._model.getId(rowIndex)


    def setText(self, name):
        rowIndex = self._model.keyboardSearch(name)
        self.setCurrentIndex(rowIndex)


    def text(self):
        rowIndex = self.currentIndex()
        return forceString(self._model.getName(rowIndex))


    def addItem(self, item):
        pass


    def updateModel(self):
        itemId = self.value()
        self._model.update()
        self.setValue(itemId)


# ##########################################################################################################

class CContractTreeFindComboBox(CTreeComboBox):
    def __init__(self, parent, filter={}):
        CTreeComboBox.__init__(self, parent)
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


    def showPopup(self):
        if not self._popup:
            self._popup = CContractFindComboBoxPopup(self, self.filter)
            self.connect(self._popup, SIGNAL('ContractFindCodeSelected(int)'), self.setValue)
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


class CARMSIndependentContractTreeFindComboBox(CIndependentContractTreeFindComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent, filter={}):
        CIndependentContractTreeFindComboBox.__init__(self, parent, filter)
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
        
    
    def setMainDialog(self, parent):
        self.mainDialog = parent


    def setValue(self, value):
        self.contractId = value
        self.setPath(self.getPathById(value))
        self.updateText()


    def updateText(self):
        if self.contractId:
            names = ['number', 'date', 'resolution']
            record = QtGui.qApp.db.getRecord('Contract', ['number', 'date', 'resolution'], self.contractId)
            self.setEditText(' '.join([forceString(record.value(name)) for name in names]))
        else:
            self.setEditText('')


class CARMSContractTreeFindComboBox(CContractTreeFindComboBox):
    __pyqtSignals__ = ('textChanged(QString)',
                       'textEdited(QString)'
                      )
    def __init__(self, parent, filter={}):
        CContractTreeFindComboBox.__init__(self, parent, filter)
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


    def setValue(self, value):
        self.contractId = value
        self.setPath(self.getPathById(value))
        self.updateText()


    def updateText(self):
        if self.contractId:
            names = ['number', 'date', 'resolution']
            record = QtGui.qApp.db.getRecord('Contract', ['number', 'date', 'resolution'], self.contractId)
            self.setEditText(' '.join([forceString(record.value(name)) for name in names]))
        else:
            self.setEditText('')
