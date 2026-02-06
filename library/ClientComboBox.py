# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2015 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4 import QtGui, QtSql
from PyQt4.QtCore import QDate, Qt, pyqtSignature, QVariant, SIGNAL

from library.crbcombobox import CRBComboBox
from library.Utils import forceBool, forceRef, forceInt, forceString

from library.InDocTable import CInDocTableModel, CInDocTableCol
from library.crbcombobox import CRBComboBox, CAbstractRBModelData, CRBModelData, CRBModel, QAbstractTableModel, CRBSelectionModel
from library.TableModel import CTableModel, CCol
from library.Ui_ClientPopup import Ui_ClientPopup
from library.adjustPopup import adjustPopupToWidget
from Orgs.Utils import getOrgStructureDescendants
import re

class CClientPopup(QtGui.QFrame, Ui_ClientPopup):
    __pyqtSignals__ = ('itemSelected(int)',)
    def __init__(self, parent = None):
        QtGui.QFrame.__init__(self, parent, Qt.Popup)
        self.setFrameShape(QtGui.QFrame.StyledPanel)
        self.setAttribute(Qt.WA_WindowPropagation)
        self.setupUi(self)
        self.sizeGrip = QtGui.QSizeGrip(self)
        self.layout().addWidget(self.sizeGrip, 2, 0, 1, 3, Qt.AlignBottom | Qt.AlignRight)
        self.btnSearch.setShortcut(Qt.Key_Return)
        self.tableModel = CClientModel(self)
        self.tblClient.setModel(self.tableModel)
        self.clientId = None

    def getClientId(self):
        return self.clientId

    def selectClientId(self, clientId):
        self.clientId = clientId
        self.emit(SIGNAL('itemSelected(int)'), clientId if clientId else 0)
        self.close()

    def getCurrentClientId(self):
        return self.tblClient.currentItemId()

    @pyqtSignature('QModelIndex')
    def on_tblClient_doubleClicked(self, index):
        if index.isValid():
            if (Qt.ItemIsEnabled & self.tableModel.flags(index)):
                clientId = self.getCurrentClientId()
                self.selectClientId(clientId)

    @pyqtSignature('')
    def on_btnSearch_clicked(self):
        self.tblClient.model().update(self.edtQuery.text())

class CClientModel(QAbstractTableModel):
    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._idList = []
        self._noneText = u'все'
        self._items = [self.getEmptyRecord()]
        self._cols = [
            CCol(u'Код', ['id'], 10, 'l'),
            CCol(u'ФИО', ['fio'], 50, 'l'),
            CCol(u'Дата рождения', ['birthDate'], 10, 'l'),
            CCol(u'Пол', ['sex'], 10, 'l'),
            CCol(u'СНИЛС', ['SNILS'], 20, 'l'),

        ]
        self.filter = None

    def getFilter(self):
        filter = []
        if self.filter:
            filter.append(self.filter)
        filter.append('Client.deleted = 0')
        return ' and '.join(filter)

    def getEmptyRecord(self):
        record = QtSql.QSqlRecord()
        record.append(QtSql.QSqlField('id', QVariant.String))
        record.append(QtSql.QSqlField('fio', QVariant.String))
        record.setValue(1, self._noneText)
        return record

    def loadData(self):
        stmt = u'''
            select id, concat_ws(" ", lastName, firstName, patrName) as fio, sex, birthDate, SNILS from Client where %s order by lastName, firstName, patrName
        '''
        stmt %= self.getFilter()

        query = QtGui.qApp.db.query(stmt)
        items = [self.getEmptyRecord()]

        while query.next():
            items.append(query.record())
        self._idList = [forceInt(i.value('id')) if not i.value('id').isNull() else None for i in items]
        self._items = items
        self.reset()

    def rowCount(self, index = None):
        return len(self._items)

    def columnCount(self, index = None):
        return len(self._cols)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        column = index.column()
        row    = index.row()
        if role == Qt.DisplayRole:
            if row == 0 and column != 1:
                return u"-"
            return self._items[row].value(column)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal:
            if role == Qt.DisplayRole:
                if section < len(self._cols):
                    return self._cols[section].title()
            if role == Qt.ToolTipRole:
                return self._cols[section].toolTip()
            if role == Qt.WhatsThisRole:
                return self._cols[section].whatsThis()
                #        elif orientation == Qt.Vertical:
                #            if role == Qt.DisplayRole:
                #                return QVariant(self._idList[section])
        return QVariant()

    def idList(self):
        return self._idList

    def searchId(self, itemId):
        if not self._idList:
            self.update(str(itemId))
        index = self._idList.index(itemId) if itemId in self._idList else -1
        return index

    def update(self, query):
        if query:
            if re.search('\d+', query):
                self.filter = u'Client.id = %s' % re.search('\d+', query).group(0)
            else:
                self.filter = u'concat_ws(" ", Client.lastName, Client.firstName, Client.patrName) like "%%%s%%"' % query
        self.loadData()

    def getId(self, rowIndex):
        if self._idList:
            return self._idList[rowIndex]
        else:
            return  None

    def setNoneText(self, noneText):
        self._noneText = noneText
        self._items[0].setValue(1, noneText)


class CClientComboBox(CRBComboBox):
    def __init__(self, parent):
        CRBComboBox.__init__(self, parent)
        #self._tableName = 'Client'
        self._addNone = True
        self._popup = CClientPopup(self)
        self.setModel(self._popup.tblClient.model())
        self.setModelColumn(1)
        self.connect(self._popup, SIGNAL('itemSelected(int)'), self.on_popup_itemSelected)

    def showPopup(self):
        adjustPopupToWidget(self, self._popup)
        self._popup.show()
    
    def hasTable(self):
        return True
    
    def setNoneText(self, noneText):
        self._popup.tblClient.model().setNoneText(noneText)

    @pyqtSignature('int')
    def on_popup_itemSelected(self, clientId):
        self.setValue(clientId)