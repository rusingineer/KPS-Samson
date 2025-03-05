# -*- coding: utf-8 -*-
#############################################################################
##
## Copyright (C) 2006-2012 Chuk&Gek and Vista Software. All rights reserved.
## Copyright (C) 2012-2022 SAMSON Group. All rights reserved.
##
#############################################################################
##
## Это программа является свободным программным обеспечением.
## Вы можете использовать, распространять и/или модифицировать её согласно
## условиям GNU GPL версии 3 или любой более поздней версии.
##
#############################################################################

from PyQt4              import QtGui, QtCore
from library.Utils      import forceString, forceInt, forceBool, toVariant
from library.TableView  import CTableView
from library.DialogBase import CDialogBase
from library.InDocTable import CRecordListModel, CInDocTableView, CInDocTableCol, CBoolInDocTableCol

from library.SortFilterProxyTableModel import CSortFilterProxyTableModel


class CMultivalueTableDialog(QtGui.QDialog):
    def __init__(self, parent=None, model=None):
        QtGui.QDialog.__init__(self, parent)
        self.tableView = CTableView(self)
        buttonBox = QtGui.QDialogButtonBox(self)

        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        if model is not None:
            self.tableView.setModel(model)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tableView.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.tableView)
        layout.addWidget(buttonBox)


    def setModel(self, model):
        self.tableView.setModel(model)


    def model(self):
        return self.tableView.model()


    def selectedItemIdList(self):
        return self.tableView.selectedItemIdList()


    def setSelectedItemIdList(self, idList):
        self.tableView.setSelectedItemIdList(idList)


class CRBRecordList(CRecordListModel):
    def __init__(self, parent=None):
        CRecordListModel.__init__(self, parent)
        self.addCol(CBoolInDocTableCol(u'', '_chk', 1).setSortable())
        self.addCol(CInDocTableCol(u'Код', 'code', 10).setReadOnly().setSortable())
        self.addCol(CInDocTableCol(u'Наименование', 'name', 45).setReadOnly().setSortable())

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.UserRole:
            col = self.cols()[index.column()]
            record = self.items()[index.row()]
            return col.toSortString(record.value(col.fieldName()), record)
        return CRecordListModel.data(self, index, role)


class CRBMultivalueTableDialog(CDialogBase):
    def __init__(self, parent=None, tableName='', filter=''):
        CDialogBase.__init__(self, parent)
        self.setObjectName('CRBMultivalueTableDialog')
        self.tableName = tableName
        self.filter = filter
        self.edtCode = QtGui.QLineEdit(self)
        self.edtName = QtGui.QLineEdit(self)
        self.btnReset = QtGui.QPushButton(u'Сбросить', self)
        self.btnSelectAll = QtGui.QPushButton(u'Выбрать всё', self)
        self.tableView = CInDocTableView(self)
        buttonBox = QtGui.QDialogButtonBox(self)
        layout = QtGui.QGridLayout(self)

        self.edtCode.textChanged.connect(self.setCodeFilter)
        self.edtName.textChanged.connect(self.setNameFilter)
        self.btnReset.clicked.connect(self.uncheckAll)
        self.btnSelectAll.clicked.connect(self.checkAll)
        self.tableView.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        self.sourceModel = CRBRecordList(self)
        self.model = CSortFilterProxyTableModel(self, self.sourceModel)
        self.model.setSortRole(QtCore.Qt.UserRole)
        self.tableView.setModel(self.model)
        self.select()
        self.model.sort(0, QtCore.Qt.DescendingOrder)

        layout.addWidget(QtGui.QLabel(u'Код'), 0, 0, 1, 1)
        layout.addWidget(self.edtCode, 0, 1, 1, 2)
        layout.addWidget(QtGui.QLabel(u'Наименование'), 1, 0, 1, 1)
        layout.addWidget(self.edtName, 1, 1, 1, 2)
        layout.addWidget(self.tableView, 2, 0, 1, 3)
        layout.addWidget(self.btnReset, 3, 0, 1, 1)
        layout.addWidget(self.btnSelectAll, 3, 1, 1, 1)
        layout.addWidget(buttonBox, 3, 2, 1, 1)


    def select(self):
        self.sourceModel.setItems(QtGui.qApp.db.getRecordList(
            self.tableName, 'id, code, name, 0 AS _chk', self.filter))


    def selectedItemIdList(self):
        idList = []
        for item in self.sourceModel.items():
            if forceBool(item.value('_chk')):
                idList.append(forceInt(item.value('id')))
        return idList


    def setSelectedItemIdList(self, idList):
        for item in self.sourceModel.items():
            if forceInt(item.value('id')) in idList:
                item.setValue('_chk', toVariant(True))
        self.sourceModel.emitColumnChanged(0)
        self.model.invalidate()


    def setCodeFilter(self, value):
        value = forceString(value)
        if value:
            self.model.setFilter('code', value, CSortFilterProxyTableModel.MatchContains)
        else:
            self.model.removeFilter('code')


    def setNameFilter(self, value):
        value = forceString(value)
        if value:
            self.model.setFilter('name', value, CSortFilterProxyTableModel.MatchContains)
        else:
            self.model.removeFilter('name')


    def uncheckAll(self):
        for item in self.sourceModel.items():
            item.setValue('_chk', toVariant(False))
        self.sourceModel.emitColumnChanged(0)
        self.model.invalidate()


    def checkAll(self):
        for item in self.sourceModel.items():
            item.setValue('_chk', toVariant(True))
        self.sourceModel.emitColumnChanged(0)
        self.model.invalidate()


    def formatSelectedItemIdList(self):
        return formatIdList(self.tableName, self.selectedItemIdList())


def formatIdList(table, idList, nameField='name'):
    items = []
    for id in idList:
        item = forceString(QtGui.qApp.db.translate(table, 'id', id, nameField))
        if item:
            items.append(item)
    return u', '.join(items) if items else u'Не задано'
